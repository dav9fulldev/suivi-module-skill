#!/usr/bin/env python3
"""Compare deux lectures de la base d'un tableau de suivi et résume ce qui a changé.

Chaque lecture est un dossier produit par l'action read_db avec out_dir :
  <dossier>/<collection>/<doc_id>.json

Usage : python comparer_lectures.py <ancienne_lecture> <nouvelle_lecture>
Sans ancienne lecture (premier passage), utiliser : --resume <lecture> pour un état chiffré.
"""
import glob, json, os, sys
from collections import Counter

STATUTS = {"fonctionnalites": "statut", "decisions": "statut", "exigences": "couverture",
           "recette": "statut", "demarrage": "fait", "lectures": "lu"}
TITRES = ("titre", "sujet", "exigence", "scenario")
LONG = {"contenu"}


def charger(d):
    out = {}
    for p in glob.glob(os.path.join(d, "**", "*.json"), recursive=True):
        rel = os.path.relpath(p, d)[:-5].replace(os.sep, "/")
        out[rel] = json.load(open(p, encoding="utf-8"))
    return out


def court(v, n=160):
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    return s if len(s) <= n else s[:n] + "…"


def nom(doc):
    for t in TITRES:
        if doc.get(t):
            return court(doc[t], 90)
    return ""


def resume(docs):
    lignes = []
    for col, champ in STATUTS.items():
        vals = [d.get(champ) for k, d in docs.items() if k.split("/")[0] == col]
        if vals:
            c = Counter("oui" if v is True else "non" if v is False else (v or "—") for v in vals)
            lignes.append(f"{col} ({len(vals)}) : " + ", ".join(f"{k} {n}" for k, n in c.most_common()))
    plan = docs.get("plan/dev")
    if plan:
        c = Counter(l.get("statut") for l in plan.get("lots", []))
        lignes.append(f"plan, lots ({len(plan.get('lots', []))}) : " + ", ".join(f"{k} {n}" for k, n in c.most_common()))
    return lignes


def comparer_listes(cle, a, b, sortie):
    ia = {x.get("id") or x.get("code"): x for x in a if isinstance(x, dict)}
    ib = {x.get("id") or x.get("code"): x for x in b if isinstance(x, dict)}
    for k in ib.keys() - ia.keys():
        sortie.append(f"  + {cle} {k} ajouté : {nom(ib[k])}")
    for k in ia.keys() - ib.keys():
        sortie.append(f"  - {cle} {k} retiré")
    for k in ia.keys() & ib.keys():
        for f in sorted(set(ia[k]) | set(ib[k])):
            if ia[k].get(f) != ib[k].get(f):
                sortie.append(f"  ~ {cle} {k} · {f} : {court(ia[k].get(f), 80)} → {court(ib[k].get(f), 80)}")


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--resume":
        print("\n".join(resume(charger(sys.argv[2]))))
        return
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    old, new = charger(sys.argv[1]), charger(sys.argv[2])
    out = []
    for k in sorted(new.keys() - old.keys()):
        out.append(f"NOUVEAU {k} : {nom(new[k]) or court(new[k])}")
    for k in sorted(old.keys() - new.keys()):
        out.append(f"SUPPRIMÉ {k} : {nom(old[k])}")
    for k in sorted(old.keys() & new.keys()):
        a, b = old[k], new[k]
        if a == b:
            continue
        out.append(f"MODIFIÉ {k} {('(' + nom(b) + ')') if nom(b) else ''}")
        for f in sorted(set(a) | set(b)):
            va, vb = a.get(f), b.get(f)
            if va == vb:
                continue
            if f in LONG:
                out.append(f"  ~ {f} : contenu modifié")
            elif isinstance(va, list) and isinstance(vb, list) and all(isinstance(x, dict) for x in va + vb):
                comparer_listes(f, va, vb, out)
            else:
                out.append(f"  ~ {f} : {court(va)} → {court(vb)}")
    print("\n".join(out) if out else "Aucun changement.")
    print("\nÉtat actuel :")
    print("\n".join(resume(new)))


if __name__ == "__main__":
    main()
