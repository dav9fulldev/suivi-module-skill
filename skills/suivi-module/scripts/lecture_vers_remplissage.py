#!/usr/bin/env python3
"""Convertit une lecture de la base d'un artefact (dossier produit par read_db avec out_dir :
<dossier>/<collection>/<doc_id>.json) en un fichier remplissage.json, pour pouvoir le
fusionner avec un remplissage régénéré (fusionner_remplissage.py) ou le versionner.

Usage : python lecture_vers_remplissage.py <dossier_lecture> --sortie remplissage.json
"""
import argparse, glob, json, os

UNIQUES = {"fiche", "plan", "cycle", "merise", "dev"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lecture")
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()
    res = {}
    for p in sorted(glob.glob(os.path.join(a.lecture, "*", "*.json"))):
        col = os.path.basename(os.path.dirname(p))
        doc_id = os.path.splitext(os.path.basename(p))[0]
        doc = json.load(open(p, encoding="utf-8"))
        doc.pop("id", None)
        if col in UNIQUES:
            res[f"{col}/{doc_id}"] = doc
        else:
            res.setdefault(col, {})[doc_id] = doc
    json.dump(res, open(a.sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(len(v) if "/" not in k else 1 for k, v in res.items())
    print(f"Remplissage écrit : {a.sortie} ({n} document(s))")


if __name__ == "__main__":
    main()
