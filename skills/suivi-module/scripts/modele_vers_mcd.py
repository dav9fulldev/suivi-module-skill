#!/usr/bin/env python3
"""Produit un premier modèle MERISE (document merise/mcd du tableau) à partir du modèle de
données du projet, quelle que soit la technologie.

Source du modèle, au choix :
  --racine .              lecture automatique (Prisma, SQL, Django, SQLAlchemy, TypeORM, JPA,
                          Entity Framework, Rails, Laravel, Mongoose, Drizzle) ; --source pour
                          forcer un lecteur ;
  --neutre modele.json    un modèle au format neutre (voir modeles_donnees.py), écrit à la main
                          pour une technologie non reconnue ou pour compléter une lecture.

Les entités retenues (--entites) sont complètes ; celles qu'elles référencent sont ajoutées
en entités compactes (identifiant seul). Une relation devient une association avec ses
cardinalités et sa clé étrangère ; la mise en page est automatique.

Usage :
  python modele_vers_mcd.py --racine . --entites Diligence,DiligenceSource --sortie mcd.json
  python modele_vers_mcd.py --neutre modele.json --entites Commande,Client --sortie mcd.json
"""
import argparse, datetime, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modeles_donnees import lire_modeles, LECTEURS  # noqa: E402

EW, LH, HEAD = 212, 15, 26


def ident(n):
    n = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", n)
    return re.sub(r"[^A-Za-z0-9]+", "_", n).strip("_").upper()


def hauteur(nb):
    return HEAD + 10 + max(nb, 1) * LH


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--racine")
    ap.add_argument("--source", default="auto", choices=["auto"] + list(LECTEURS))
    ap.add_argument("--neutre")
    ap.add_argument("--entites", required=True, help="Noms d'entités du module, séparés par des virgules")
    ap.add_argument("--titre", default="")
    ap.add_argument("--sortie")
    a = ap.parse_args()
    if bool(a.racine) == bool(a.neutre):
        sys.exit("Donner --racine ou --neutre (un seul).")
    modele = json.load(open(a.neutre, encoding="utf-8")) if a.neutre else lire_modeles(os.path.abspath(a.racine), source=a.source)
    par_nom = {e["nom"]: e for e in modele["entites"]}
    retenus = [n.strip() for n in a.entites.split(",") if n.strip()]
    manquants = [n for n in retenus if n not in par_nom]
    if manquants:
        sys.exit("Entités introuvables : " + ", ".join(manquants) + "\nDisponibles : " + ", ".join(sorted(par_nom)))

    rels = [r for r in modele["relations"] if r["de"] in par_nom and r["vers"] in par_nom
            and (r["de"] in retenus or r["vers"] in retenus)]
    lies = []
    for r in rels:
        for n in (r["de"], r["vers"]):
            if n not in retenus and n not in lies:
                lies.append(n)

    entites = []
    for n in retenus + lies:
        e = par_nom[n]
        complet = n in retenus
        fks = {c for r in modele["relations"] if r["de"] == n for c in r.get("fk", [])}
        attrs = []
        for c in e["champs"]:
            if not complet and not c.get("id"):
                continue
            d = (c.get("type") or "") + ("?" if c.get("optionnel") and not c.get("id") else "") + ("[]" if c.get("liste") else "")
            if c.get("unique"):
                d += ", unique"
            if c["nom"] in fks:
                d += ", clé étrangère"
            x = {"n": c["nom"], "d": d.strip(", ")}
            if c.get("id"):
                x["id"] = True
            attrs.append(x)
        src = modele.get("source") or "modèle neutre"
        desc = f"{src} : {e['nom']}" + (f" ({e['fichier']}, ligne {e['ligne']})" if e.get("fichier") else "")
        entites.append({"id": ident(n), "nom": ident(n), "desc": desc + ("" if complet else " — hors module, montrée pour ses liens."),
                        "attrs": attrs or [{"n": "id", "id": True}]})

    assocs = []
    for r in rels:
        de, vers = ident(r["de"]), ident(r["vers"])
        if r.get("plusieurs_a_plusieurs"):
            liens = [{"e": de, "c": "0,n"}, {"e": vers, "c": "0,n"}]
            lecture = f"Un(e) {de.lower()} est lié(e) à zéro à plusieurs {vers.lower()}, et réciproquement."
        else:
            c_de = "0,1" if r.get("optionnel") else "1,1"
            c_vers = "0,1" if r.get("un_a_un") else "0,n"
            liens = [{"e": de, "c": c_de}, {"e": vers, "c": c_vers}]
            if r.get("fk"):
                liens[0]["fk"] = ", ".join(r["fk"])
            lecture = (f"Un(e) {de.lower()} est relié(e) à {'zéro ou un' if c_de == '0,1' else 'un et un seul'} {vers.lower()} "
                       f"({r['champ']}) ; un(e) {vers.lower()} l'est à {'zéro ou un' if c_vers == '0,1' else 'zéro à plusieurs'} {de.lower()}.")
        if de == vers:
            liens[0]["role"], liens[1]["role"] = "enfant", "parent"
        assocs.append({"id": f"{de}_{ident(r['champ'])}", "nom": ident(r["champ"]), "vue": "v1", "x": 0, "y": 0,
                       "attrs": [], "liens": liens, "lecture": lecture, "exig": ""})

    # Mise en page : entités du module en grille au centre, entités liées sur les côtés.
    colonnes = 3 if len(retenus) > 4 else 2 if len(retenus) > 1 else 1
    pas_x, marge = 330, 40
    y_col = [marge] * colonnes
    pos, h_de = {}, {e["id"]: hauteur(len(e["attrs"])) for e in entites}
    for i, n in enumerate(retenus):
        col = i % colonnes
        pos[ident(n)] = (marge + 250 + col * pas_x, y_col[col])
        y_col[col] += h_de[ident(n)] + 120
    x_droite = marge + 250 + colonnes * pas_x + 40
    y_g = y_d = marge
    for i, n in enumerate(lies):
        if i % 2 == 0:
            pos[ident(n)] = (marge, y_g); y_g += h_de[ident(n)] + 90
        else:
            pos[ident(n)] = (x_droite, y_d); y_d += h_de[ident(n)] + 90
    centre = lambda i: (pos[i][0] + EW / 2, pos[i][1] + h_de[i] / 2)
    deja = {}
    for x in assocs:
        a_, b_ = x["liens"][0]["e"], x["liens"][1]["e"]
        (x1, y1), (x2, y2) = centre(a_), centre(b_)
        k = deja.get((a_, b_), 0); deja[(a_, b_)] = k + 1
        if a_ == b_:
            x["x"], x["y"] = int(x1 + EW / 2 + 80), int(y1 - 30 + k * 46)
        else:
            x["x"], x["y"] = int((x1 + x2) / 2), int((y1 + y2) / 2 + k * 46)
    vue_ent = {i: ({"x": p[0], "y": p[1], "compact": True} if i in {ident(n) for n in lies} else {"x": p[0], "y": p[1]})
               for i, p in pos.items()}

    mcd = {
        "titre": a.titre or "Modèle conceptuel des données — " + ", ".join(retenus),
        "sousTitre": f"Premier modèle déduit du code ({modele.get('source') or 'modèle neutre'}) : à relire. "
                     "Les entités compactes sont hors du module.",
        "version": datetime.date.today().isoformat(),
        "vues": [{"id": "v1", "titre": "Vue 1 · Modèle déduit du code", "court": "Vue 1",
                  "desc": "Entités du module et leurs liens directs.",
                  "w": int(max(p[0] for p in pos.values()) + EW + marge + 60),
                  "h": int(max(p[1] + h_de[i] for i, p in pos.items()) + marge), "ent": vue_ent}],
        "entites": entites, "assocs": assocs, "regles": [],
        "ecarts": [{"entite": ident(n), "existant": n, "statut": "couvert", "note": f"Présent dans le code ({modele.get('source') or 'modèle neutre'})."}
                   for n in retenus],
    }
    texte = json.dumps(mcd, ensure_ascii=False, indent=1)
    if a.sortie:
        open(a.sortie, "w", encoding="utf-8").write(texte)
        print(f"MCD écrit : {a.sortie} ({len(entites)} entités, {len(assocs)} associations, source {modele.get('source') or 'neutre'})")
    else:
        print(texte)


if __name__ == "__main__":
    main()
