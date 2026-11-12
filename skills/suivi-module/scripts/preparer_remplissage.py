#!/usr/bin/env python3
"""Vérifie un fichier de remplissage et le découpe en lots prêts pour l'action write_db « batch ».

Entrée : un fichier JSON dont les clés sont
  - "collection/doc_id" pour un document unique (ex. "fiche/main", "plan/dev") ;
  - "collection" pour une liste, associée à un objet {doc_id: document}.

Sortie (dans --sortie) :
  - un fichier JSON par document : <collection>/<doc_id>.json ;
  - lots/lot_01.json, lot_02.json… : chacun une liste d'au plus 50 écritures
    {"op": "set", "collection", "doc_id", "file_path"} à passer telle quelle dans `writes`.

Le script refuse (code de sortie 1) un statut inconnu, un document trop gros ou un secret
probable, et avertit pour le reste.

Usage : python preparer_remplissage.py remplissage.json --sortie /mnt/user-data/outputs/remplissage
"""
import argparse, json, os, re, sys

UNIQUES = {"fiche/main", "plan/dev", "cycle/vie", "merise/mcd", "dev/boucle"}
LISTES = {"demarrage", "lectures", "fonctionnalites", "decisions", "exigences", "recette"}

VALEURS = {
    ("fonctionnalites", "statut"): {"a_faire", "en_cours", "a_verifier", "bloque", "termine"},
    ("decisions", "statut"): {"a_trancher", "tranche", "applique", "abandonne"},
    ("exigences", "couverture"): {"couvert", "partiel", "non_couvert", "a_verifier"},
    ("exigences", "criticite"): {"Bloquant", "Critique", "Majeur", "Mineur"},
    ("recette", "statut"): {"non_execute", "ok", "ko", "bloque"},
    ("recette", "criticite"): {"Bloquant", "Critique", "Majeur", "Mineur"},
}
OBLIGATOIRES = {
    "demarrage": ["titre", "ordre"],
    "lectures": ["titre", "chemin", "contenu", "ordre"],
    "fonctionnalites": ["titre", "statut", "ordre"],
    "decisions": ["sujet", "statut", "ordre"],
    "exigences": ["perimetre", "section", "exigence", "couverture", "ordre"],
    "recette": ["perimetre", "scenario", "statut", "ordre"],
}
# Motifs de secrets ou de données qu'on ne met jamais dans une base partagée.
SECRETS = [
    (r"(?i)(mot de passe|password|passwd|pwd)\s*(?:[:=]|est\b|`)\s*`?[^\s`]{6,}", "mot de passe"),
    (r"[\w.+-]+@[\w.-]+`?\s*/\s*`[^`\s]{6,}`", "identifiant et mot de passe"),
    (r"(?i)\b(secret|token|api[_-]?key|auth_secret)\b\s*[:=]\s*\S{8,}", "secret ou clé"),
    (r"\bsk-[A-Za-z0-9_-]{16,}", "clé d'API"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "clé privée"),
    (r"\b(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)(?:\.\d{1,3}){2,3}\b", "adresse IP interne"),
    (r"(?i)\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@", "identifiants dans une URL"),
    (r"(?i)[A-Z]:\\Users\\[^\\\s\"]+", "chemin personnel Windows"),
    (r"/(?:home|Users)/[a-z][a-z0-9._-]+/", "chemin personnel"),
]
MAX_DOC = 250_000
LOT = 50


def chaines(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from chaines(x)
    elif isinstance(v, list):
        for x in v:
            yield from chaines(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entree")
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--autoriser-secrets", action="store_true",
                    help="Ne pas bloquer sur les secrets probables (à n'utiliser qu'après vérification humaine).")
    a = ap.parse_args()

    data = json.load(open(a.entree, encoding="utf-8"))
    erreurs, avertissements, ecritures = [], [], []

    def ajouter(collection, doc_id, doc):
        lieu = f"{collection}/{doc_id}"
        if not isinstance(doc, dict):
            erreurs.append(f"{lieu} : un document doit être un objet JSON.")
            return
        if not re.fullmatch(r"[A-Za-z0-9_.~:@+-]{1,200}", doc_id):
            erreurs.append(f"{lieu} : identifiant de document invalide.")
        for champ in OBLIGATOIRES.get(collection, []):
            if doc.get(champ) in (None, ""):
                avertissements.append(f"{lieu} : champ « {champ} » vide.")
        for (col, champ), ok in VALEURS.items():
            if col == collection and champ in doc and doc[champ] not in ok:
                erreurs.append(f"{lieu} : {champ} = « {doc[champ]} » (attendu : {', '.join(sorted(ok))}).")
        taille = len(json.dumps(doc, ensure_ascii=False).encode("utf-8"))
        if taille > MAX_DOC:
            erreurs.append(f"{lieu} : {taille} octets, au-delà de 250 ko ; découper le document.")
        for s in chaines(doc):
            for motif, nature in SECRETS:
                m = re.search(motif, s)
                if m:
                    extrait = m.group(0)[:40]
                    msg = f"{lieu} : {nature} probable (« {extrait}… »)."
                    (avertissements if a.autoriser_secrets else erreurs).append(msg)
        chemin = os.path.join(a.sortie, collection, f"{doc_id}.json")
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        json.dump(doc, open(chemin, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        ecritures.append({"op": "set", "collection": collection, "doc_id": doc_id, "file_path": os.path.abspath(chemin)})

    for cle, valeur in data.items():
        if "/" in cle:
            if cle not in UNIQUES:
                avertissements.append(f"{cle} : document unique inconnu de la page (ignoré par l'affichage).")
            col, doc_id = cle.split("/", 1)
            ajouter(col, doc_id, valeur)
        else:
            if cle not in LISTES:
                avertissements.append(f"{cle} : liste inconnue de la page (ignorée par l'affichage).")
            if not isinstance(valeur, dict):
                erreurs.append(f"{cle} : une liste doit être un objet {{doc_id: document}}.")
                continue
            for doc_id, doc in valeur.items():
                ajouter(cle, doc_id, doc)

    # Cohérences entre collections.
    etapes = set((data.get("demarrage") or {}).keys())
    for doc_id, d in (data.get("lectures") or {}).items():
        if d.get("etape") and d["etape"] not in etapes:
            avertissements.append(f"lectures/{doc_id} : étape « {d['etape']} » absente de demarrage.")
    plan = data.get("plan/dev")
    if isinstance(plan, dict):
        mods = {m.get("id") for m in plan.get("modules", [])}
        phases = {p.get("id") for p in plan.get("phases", [])}
        decs = {d.get("code") for d in (data.get("decisions") or {}).values()}
        for l in plan.get("lots", []):
            if l.get("phase") not in phases:
                avertissements.append(f"plan/dev lot {l.get('id')} : phase « {l.get('phase')} » inconnue.")
            for dep in l.get("deps", []):
                if dep.get("m") not in mods:
                    avertissements.append(f"plan/dev lot {l.get('id')} : module « {dep.get('m')} » absent de modules.")
            for b in l.get("bloque", []) or []:
                if b not in decs:
                    avertissements.append(f"plan/dev lot {l.get('id')} : arbitrage « {b} » absent de decisions.")
    mcd = data.get("merise/mcd")
    if isinstance(mcd, dict):
        ents = {e.get("id") for e in mcd.get("entites", [])}
        for a_ in mcd.get("assocs", []):
            for li in a_.get("liens", []):
                if li.get("e") not in ents:
                    erreurs.append(f"merise/mcd association {a_.get('id')} : entité « {li.get('e')} » inconnue.")

    os.makedirs(os.path.join(a.sortie, "lots"), exist_ok=True)
    lots = [ecritures[i:i + LOT] for i in range(0, len(ecritures), LOT)]
    for i, lot in enumerate(lots, 1):
        json.dump(lot, open(os.path.join(a.sortie, "lots", f"lot_{i:02d}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    for m in avertissements:
        print("AVERTISSEMENT", m)
    for m in erreurs:
        print("ERREUR", m)
    print(f"{len(ecritures)} document(s), {len(lots)} lot(s) dans {os.path.join(a.sortie, 'lots')}")
    sys.exit(1 if erreurs else 0)


if __name__ == "__main__":
    main()
