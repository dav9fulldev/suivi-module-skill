#!/usr/bin/env python3
"""Génère la page du tableau de suivi en mode local (hors claude.ai) : un seul fichier HTML
qui embarque les données de remplissage.json et s'ouvre dans n'importe quel navigateur.

Usage : python construire_page_locale.py <remplissage.json> --sortie <dossier>/index.html

Les coches et modifications faites dans le navigateur sont gardées dans ce navigateur ;
le bouton « Exporter » télécharge un remplissage.json à remettre dans le projet, puis
relancer ce script. Dès que remplissage.json change, la page repart de son contenu.
"""
import argparse, html, json, os, re

ICI = os.path.dirname(os.path.abspath(__file__))
MODELE = os.path.join(ICI, "..", "assets", "template.html")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("remplissage")
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()

    data = json.load(open(a.remplissage, encoding="utf-8"))
    page = open(MODELE, encoding="utf-8").read()

    nom = (data.get("fiche/main") or {}).get("nom") or "module"
    page = page.replace("<title>Suivi de module</title>",
                        f"<title>Suivi de module — {html.escape(nom)}</title>", 1)

    # JSON sûr dans une balise script : neutraliser toute fermeture de balise.
    brut = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    bloc = f'<script type="application/json" id="suivi-donnees">{brut}</script>\n'
    i = page.rfind("<script>")
    if i < 0:
        raise SystemExit("Modèle inattendu : script principal introuvable.")
    page = page[:i] + bloc + page[i:]

    os.makedirs(os.path.dirname(os.path.abspath(a.sortie)), exist_ok=True)
    open(a.sortie, "w", encoding="utf-8").write(page)
    n = sum(len(v) if isinstance(v, dict) and "/" not in k else 1 for k, v in data.items())
    print(f"Page locale écrite : {a.sortie} ({n} document(s) embarqué(s))")


if __name__ == "__main__":
    main()
