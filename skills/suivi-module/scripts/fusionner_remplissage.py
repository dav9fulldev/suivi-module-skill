#!/usr/bin/env python3
"""Fusionne un remplissage régénéré (déduit à nouveau du dépôt) avec le remplissage existant,
sans perdre ce que les personnes ont saisi.

Gardé de l'existant :
- démarrage : fait, faitLe ;   lectures : lu, luLe ;
- recette : statut, resultat, anomalie, testeLe ;
- décisions déjà tranchées, appliquées ou écartées : le document entier ;
- fonctionnalités et lots marqués « termine » : le statut et la date, sauf si le nouveau
  remplissage les marque eux aussi terminés (alors le nouveau l'emporte, date comprise) ;
- éléments ajoutés à la main dans la page (absents du nouveau remplissage) : conservés ;
- modèle MERISE : positions des entités et associations déplacées à la souris ;
- fiche : champs que le nouveau remplissage laisse vides.
Tout le reste vient du nouveau remplissage. Les désaccords sont listés sur la sortie standard.

Usage : python fusionner_remplissage.py ancien.json nouveau.json --sortie remplissage.json
"""
import argparse, copy, json

GARDER = {
    "demarrage": ("fait", "faitLe"),
    "lectures": ("lu", "luLe"),
    "recette": ("statut", "resultat", "anomalie", "testeLe"),
}
DECISIONS_FIGEES = {"tranche", "applique", "abandonne"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ancien")
    ap.add_argument("nouveau")
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()
    ancien = json.load(open(a.ancien, encoding="utf-8"))
    nouveau = json.load(open(a.nouveau, encoding="utf-8"))
    res = copy.deepcopy(nouveau)
    notes = []

    for cle, vieux in ancien.items():
        if cle not in res:
            res[cle] = copy.deepcopy(vieux)
            notes.append(f"conservé : {cle} (absent du nouveau remplissage)")
            continue
        neuf = res[cle]
        if "/" in cle:
            if cle == "fiche/main":
                for k, v in vieux.items():
                    if v and not neuf.get(k):
                        neuf[k] = v
            elif cle == "merise/mcd":
                anciennes_vues = {v.get("id"): v for v in vieux.get("vues", [])}
                for v in neuf.get("vues", []):
                    av = anciennes_vues.get(v.get("id"))
                    if av:
                        for e, p in av.get("ent", {}).items():
                            if e in v.get("ent", {}):
                                v["ent"][e].update({"x": p.get("x"), "y": p.get("y")})
                anc_assoc = {x.get("id"): x for x in vieux.get("assocs", [])}
                for x in neuf.get("assocs", []):
                    if x.get("id") in anc_assoc:
                        x["x"], x["y"] = anc_assoc[x["id"]].get("x", x["x"]), anc_assoc[x["id"]].get("y", x["y"])
            elif cle == "plan/dev":
                anc_lots = {l.get("id"): l for l in vieux.get("lots", [])}
                for l in neuf.get("lots", []):
                    al = anc_lots.get(l.get("id"))
                    if al and al.get("statut") == "termine" and l.get("statut") != "termine":
                        notes.append(f"désaccord : lot {l['id']} terminé dans l'existant, « {l.get('statut')} » d'après le dépôt ; gardé terminé")
                        l["statut"] = "termine"
            continue
        for doc_id, vdoc in vieux.items():
            if doc_id not in neuf:
                neuf[doc_id] = copy.deepcopy(vdoc)
                notes.append(f"conservé : {cle}/{doc_id} (ajouté à la main)")
                continue
            ndoc = neuf[doc_id]
            for champ in GARDER.get(cle, ()):
                if champ in vdoc:
                    ndoc[champ] = vdoc[champ]
            if cle == "decisions" and vdoc.get("statut") in DECISIONS_FIGEES:
                if any(vdoc.get(k) != ndoc.get(k) for k in ("statut", "decision")):
                    notes.append(f"décision gardée : {cle}/{doc_id} ({vdoc.get('code', '')}) est « {vdoc['statut']} » dans l'existant")
                neuf[doc_id] = copy.deepcopy(vdoc)
            if cle == "fonctionnalites" and vdoc.get("statut") == "termine" and ndoc.get("statut") != "termine":
                notes.append(f"désaccord : {cle}/{doc_id} « {ndoc.get('titre', '')} » terminée dans l'existant, "
                             f"« {ndoc.get('statut')} » d'après le dépôt ; gardée terminée")
                ndoc["statut"], ndoc["termineLe"] = "termine", vdoc.get("termineLe", "")

    json.dump(res, open(a.sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for n in notes:
        print(n)
    print(f"Fusion écrite : {a.sortie}")


if __name__ == "__main__":
    main()
