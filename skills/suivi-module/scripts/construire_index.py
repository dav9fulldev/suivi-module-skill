#!/usr/bin/env python3
"""Génère suivi/index.html : la page d'accueil qui récapitule tous les tableaux de suivi
du projet (un par sous-dossier contenant un remplissage.json).

Usage : python construire_index.py suivi [--projet "Nom du projet"]
"""
import argparse, datetime, html, json, os

E = html.escape


def stats(d):
    f = list((d.get("fonctionnalites") or {}).values())
    dec = list((d.get("decisions") or {}).values())
    ex = list((d.get("exigences") or {}).values())
    rec = list((d.get("recette") or {}).values())
    dem = list((d.get("demarrage") or {}).values())
    lots = (d.get("plan/dev") or {}).get("lots", [])
    c = lambda xs, k, v: sum(1 for x in xs if x.get(k) == v)
    return {
        "f": len(f), "f_ok": c(f, "statut", "termine"), "f_verif": c(f, "statut", "a_verifier"),
        "f_cours": c(f, "statut", "en_cours"), "f_bloque": c(f, "statut", "bloque"),
        "dec_ouvertes": c(dec, "statut", "a_trancher"),
        "ex": len(ex), "ex_ok": c(ex, "couverture", "couvert"),
        "rec": len(rec), "rec_ok": c(rec, "statut", "ok"), "rec_ko": c(rec, "statut", "ko"),
        "dem": len(dem), "dem_ok": sum(1 for x in dem if x.get("fait")),
        "lots": len(lots), "lots_ok": c(lots, "statut", "termine"),
    }


def carte(dossier, d, s, maj):
    fiche = d.get("fiche/main") or {}
    pct = round(100 * s["f_ok"] / s["f"]) if s["f"] else 0
    seg = lambda n, cls: f'<span class="{cls}" style="width:{100 * n / s["f"]:.1f}%"></span>' if s["f"] and n else ""
    lignes = []
    if s["dec_ouvertes"]:
        lignes.append(f'<li class="alerte">{s["dec_ouvertes"]} arbitrage{"s" if s["dec_ouvertes"] > 1 else ""} à trancher</li>')
    if s["f_bloque"]:
        lignes.append(f'<li class="alerte">{s["f_bloque"]} fonctionnalité{"s" if s["f_bloque"] > 1 else ""} bloquée{"s" if s["f_bloque"] > 1 else ""}</li>')
    if s["f_verif"]:
        lignes.append(f'<li>{s["f_verif"]} à vérifier</li>')
    if s["ex"]:
        lignes.append(f'<li>Exigences couvertes : {s["ex_ok"]} / {s["ex"]}</li>')
    if s["rec"]:
        ko = f', {s["rec_ko"]} KO' if s["rec_ko"] else ""
        lignes.append(f'<li>Recette : {s["rec_ok"]} OK{ko} / {s["rec"]}</li>')
    if s["lots"]:
        lignes.append(f'<li>Lots terminés : {s["lots_ok"]} / {s["lots"]}</li>')
    if s["dem"]:
        lignes.append(f'<li>Prise en main : {s["dem_ok"]} / {s["dem"]} étapes</li>')
    return f'''<a class="carte" href="./{E(dossier)}/index.html">
  <div class="tete"><h2>{E(fiche.get("nom") or dossier)}</h2><span class="code">{E(fiche.get("code") or dossier.upper())}</span></div>
  <p class="accroche">{E(fiche.get("accroche") or "")}</p>
  <div class="pct"><b>{pct} %</b><span>{s["f_ok"]} / {s["f"]} fonctionnalités terminées</span></div>
  <div class="barre">{seg(s["f_ok"], "ok")}{seg(s["f_verif"], "verif")}{seg(s["f_cours"], "cours")}{seg(s["f_bloque"], "bloque")}</div>
  <ul>{"".join(lignes)}</ul>
  <p class="maj">Données du {maj}</p>
</a>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dossier", nargs="?", default="suivi")
    ap.add_argument("--projet", default="")
    a = ap.parse_args()
    cartes, total = [], {"f": 0, "f_ok": 0, "dec": 0, "n": 0}
    for nom in sorted(os.listdir(a.dossier)):
        chemin = os.path.join(a.dossier, nom, "remplissage.json")
        if not os.path.isfile(chemin):
            continue
        d = json.load(open(chemin, encoding="utf-8"))
        s = stats(d)
        maj = datetime.date.fromtimestamp(os.path.getmtime(chemin)).strftime("%d/%m/%Y")
        cartes.append((-(s["dec_ouvertes"] + s["f_bloque"]), (d.get("fiche/main") or {}).get("nom", nom).lower(), carte(nom, d, s, maj)))
        total["f"] += s["f"]; total["f_ok"] += s["f_ok"]; total["dec"] += s["dec_ouvertes"]; total["n"] += 1
    cartes.sort()
    pct = round(100 * total["f_ok"] / total["f"]) if total["f"] else 0
    projet = a.projet or os.path.basename(os.path.abspath(os.path.join(a.dossier, "..")))
    page = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Suivi des modules — {E(projet)}</title>
<style>
:root{{--fond:#F2F4F7;--carte:#FFFFFF;--encre:#172033;--doux:#5A6477;--ligne:#DCE1E8;--accent:#96560F;
--ok:#1C7548;--verif:#2A5CB3;--cours:#A86400;--bloque:#B42318;--vide:#EEF0F3;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root{{--fond:#12161F;--carte:#1B2130;--encre:#E7EAF0;--doux:#A3ABBA;--ligne:#2E3647;
--accent:#E0A35B;--ok:#4CC08A;--verif:#7FA6F0;--cours:#E0A35B;--bloque:#F07A6E;--vide:#2A3142;color-scheme:dark}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--fond);color:var(--encre);
font:15px/1.5 "Public Sans",system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:32px 20px 48px}}
.sur{{text-transform:uppercase;letter-spacing:.08em;font-size:12px;color:var(--doux);font-weight:600}}
h1{{font:800 32px/1.15 "Archivo","Arial Narrow",system-ui,sans-serif;margin:4px 0 6px}}
.resume{{color:var(--doux);margin:0 0 24px}}.resume b{{color:var(--encre)}}
.grille{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}}
.carte{{display:block;background:var(--carte);border:1px solid var(--ligne);border-radius:10px;padding:18px;
color:inherit;text-decoration:none;transition:border-color .15s}}
.carte:hover,.carte:focus-visible{{border-color:var(--accent);outline:none}}
.tete{{display:flex;justify-content:space-between;gap:8px;align-items:baseline}}
h2{{font:700 19px/1.25 "Archivo","Arial Narrow",system-ui,sans-serif;margin:0}}
.code{{font:500 11px ui-monospace,"JetBrains Mono",monospace;color:var(--accent)}}
.accroche{{color:var(--doux);font-size:13.5px;margin:6px 0 12px;min-height:2.6em}}
.pct{{display:flex;align-items:baseline;gap:8px}}.pct b{{font-size:24px}}.pct span{{color:var(--doux);font-size:13px}}
.barre{{display:flex;height:8px;border-radius:4px;overflow:hidden;background:var(--vide);margin:8px 0 12px}}
.barre .ok{{background:var(--ok)}}.barre .verif{{background:var(--verif)}}.barre .cours{{background:var(--cours)}}.barre .bloque{{background:var(--bloque)}}
ul{{list-style:none;margin:0;padding:0;font-size:13.5px}}li{{padding:2px 0}}li.alerte{{color:var(--bloque);font-weight:600}}
.maj{{color:var(--doux);font-size:12px;margin:10px 0 0}}
.legende{{display:flex;gap:16px;flex-wrap:wrap;color:var(--doux);font-size:12.5px;margin:-12px 0 20px}}
.legende i{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px}}
</style></head><body><main>
<div class="sur">Tableau de suivi des modules</div>
<h1>{E(projet)}</h1>
<p class="resume"><b>{total["n"]}</b> module{"s" if total["n"] > 1 else ""} · <b>{pct} %</b> des fonctionnalités terminées ({total["f_ok"]} / {total["f"]}) · <b>{total["dec"]}</b> arbitrage{"s" if total["dec"] > 1 else ""} à trancher</p>
<div class="legende"><span><i style="background:var(--ok)"></i>Terminé</span><span><i style="background:var(--verif)"></i>À vérifier</span><span><i style="background:var(--cours)"></i>En cours</span><span><i style="background:var(--bloque)"></i>Bloqué</span></div>
<div class="grille">{"".join(c for _, _, c in cartes) or "<p>Aucun tableau de suivi pour l’instant.</p>"}</div>
</main></body></html>'''
    sortie = os.path.join(a.dossier, "index.html")
    open(sortie, "w", encoding="utf-8").write(page)
    print(f"Page d'accueil écrite : {sortie} ({total['n']} module(s))")


if __name__ == "__main__":
    main()
