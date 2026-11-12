# Données du tableau de suivi

La page lit tout dans la base de l'artefact (capacité `db`). Elle ne contient aucune donnée.
Chaque section ci-dessous indique l'emplacement (`collection/document` pour un document unique,
`collection` pour une liste) et la forme exacte attendue. Un onglet sans données reste masqué
(Lecture, Modèle MERISE, Exigences & recette, Plan, Boucle de dev) ou vide (les autres).

Sommaire : fiche · demarrage · lectures · fonctionnalites · decisions · exigences · recette ·
plan · cycle · merise · dev · valeurs autorisées · ordre de remplissage.

Les champs « Markdown léger » acceptent `- ` en début de ligne pour une liste, `**gras**` et
`` `code` ``. Les dates sont au format `AAAA-MM-JJ`. L'identifiant d'un élément de liste est
l'identifiant du document (`doc_id`) : la page l'expose sous le nom `id`.

## fiche/main — Vue d'ensemble (document unique)

| Champ | Contenu |
|---|---|
| `nom` | Nom du module, affiché en titre (ex. « Gestion des congés ») |
| `code` | Code court en majuscules (ex. « CONGES ») |
| `accroche` | Une phrase : ce que fait le module |
| `definition` | Markdown léger : de quoi il s'agit, les notions clés |
| `but` | Markdown léger : à quoi il sert |
| `usage` | Markdown léger : le cycle d'utilisation, les écrans |
| `architecture` | Une couche par ligne, format `Couche :: contenu` (ex. `Base de données :: tables …`) |
| `liens` | Markdown léger : interactions avec les autres modules |
| `docs` | Un document de référence par ligne |
| `fichiers` | Un chemin de fichier clé par ligne |
| `perimetres` | Facultatif. Libellés des périmètres d'exigences, un par ligne : `DIL: Diligences` |
| `sourceExigences` | Facultatif. Origine des exigences, ex. « cahier d'exigences du 08/10/2026 » |

## demarrage — Démarrage (liste)

Parcours de prise en main, coché par l'utilisateur. `doc_id` : `s01`, `s02`…

```json
{"ordre": 1, "titre": "Lire `CLAUDE.md`", "detail": "Règles permanentes du projet.", "fait": false, "faitLe": ""}
```

## lectures — Lecture (liste)

Documents du projet recopiés en Markdown, lus dans l'ordre. `doc_id` : `l01`, `l02`…
`etape` (facultatif) relie le document à une étape de démarrage : le bouton « Lire » y apparaît.

```json
{"ordre": 1, "titre": "Constitution du projet", "chemin": "CLAUDE.md", "maj": "2026-10-08",
 "contenu": "# Texte Markdown complet…", "etape": "s01", "lu": false, "luLe": ""}
```

Un document fait au plus 256 ko : découper un document plus long en plusieurs lectures.

## fonctionnalites — Fonctionnalités (liste)

Regroupées par `palier` (lot, version, jalon), dans l'ordre de `ordre`. `doc_id` : `f01`…

```json
{"ordre": 1, "palier": "Socle (V1)", "titre": "Créer une demande", "description": "…",
 "statut": "a_faire", "ref": "SPEC-CONG-01 §3", "note": "", "termineLe": ""}
```

## decisions — Arbitrages & décisions (liste)

Questions ouvertes et choix faits. `doc_id` : `d01`…

```json
{"ordre": 1, "code": "A1", "sujet": "Question à trancher", "statut": "a_trancher",
 "contexte": "…", "recommandation": "…", "decision": "", "par": "", "date": "", "ref": "DECISIONS.md"}
```

## exigences — Exigences & recette, vue Exigences (liste)

`doc_id` = identifiant de l'exigence (ex. `CONG-001`). `perimetre` regroupe les exigences
(un onglet par valeur distincte) ; `section` les regroupe à l'intérieur du périmètre.

```json
{"ordre": 1, "perimetre": "CONG", "section": "1.1 Création", "exigence": "Le système doit…",
 "criteres": "Critères d'acceptation…", "criticite": "Critique", "couverture": "a_verifier", "note": ""}
```

## recette — Exigences & recette, vue Recette (liste)

`doc_id` = identifiant du cas (ex. `TC-01`). Même `perimetre` que les exigences testées.

```json
{"ordre": 1, "perimetre": "CONG", "scenario": "Création", "profil": "Agent", "exig": "CONG-001",
 "preconditions": "", "etapes": "1. … 2. …", "attendu": "…", "criticite": "Critique",
 "statut": "non_execute", "resultat": "", "anomalie": "", "testeLe": ""}
```

## plan/dev — Plan de développement (document unique)

```json
{"titre": "Plan de développement — …", "sousTitre": "…",
 "phases": [{"id": "p1", "code": "Phase 1", "court": "Autonome", "titre": "…", "desc": "…"}],
 "modules": [{"id": "ORG", "nom": "Organigramme", "court": "Organigramme", "desc": "…",
              "sens": "amont", "mien": false,
              "contacts": [{"f": "lib/org.ts", "fn": "getOrgUnitsLite", "usage": "…"}]}],
 "lots": [{"id": "L01", "code": "L1", "ordre": 1, "phase": "p1", "titre": "…", "objectif": "…",
           "statut": "a_faire", "exig": "CONG-001 · TC-01", "schema": "", "fichiers": ["…"],
           "deps": [{"m": "ORG", "t": "L", "quoi": "lib/org.ts · getOrgUnitsLite", "faire": "…"}],
           "bloque": ["A1"]}],
 "regles": [{"t": "Méthode", "d": "…"}]}
```

`modules` = les modules voisins (carte des dépendances) ; `mien: true` pour un module dont
l'utilisateur est aussi responsable. `sens` : `amont` (le module suivi l'utilise), `aval`
(il utilise le module suivi) ou `both`. Dans `deps`, `t` vaut `L` (lecture du module d'une
autre équipe, sans le modifier) ou `M` (modification à demander à cette équipe) : la page en
déduit le niveau du lot (🟢 autonome, 🟡 lecture, 🔴 coordination). `bloque` liste les codes
d'arbitrages qui bloquent le lot. Facultatif : `majLe`.

## cycle/vie — Cycle de vie (document unique, affiché dans l'onglet Plan)

```json
{"titre": "Cycle de vie d'une demande", "desc": "…",
 "etapes": [{"id": "e1", "titre": "Création", "acteur": "Agent", "statut": "BROUILLON",
             "etat": "existe", "exig": "CONG-001", "regle": "Règle complète (au survol)"}],
 "retours": [{"de": "e3", "vers": "e1", "label": "Renvoyée (motif)"}]}
```

Le cycle n'apparaît que si `plan/dev` existe.

## merise/mcd — Modèle MERISE (document unique)

```json
{"titre": "Modèle conceptuel des données — …", "sousTitre": "…", "version": "2026-10-08",
 "vues": [{"id": "v1", "titre": "Vue 1 · Noyau", "court": "Vue 1", "desc": "…", "w": 1600, "h": 860,
           "ent": {"DEMANDE": {"x": 640, "y": 300}, "AGENT": {"x": 60, "y": 50, "compact": true}}}],
 "entites": [{"id": "DEMANDE", "nom": "DEMANDE", "desc": "…",
              "attrs": [{"n": "numero", "id": true, "d": "identifiant"}, {"n": "statut", "d": "Brouillon, …"}]}],
 "assocs": [{"id": "DEPOSER", "nom": "DÉPOSER", "vue": "v1", "x": 400, "y": 200, "attrs": [],
             "liens": [{"e": "DEMANDE", "c": "1,1", "fk": "matricule"}, {"e": "AGENT", "c": "0,n"}],
             "lecture": "Une demande est déposée par **un et un seul** agent…", "exig": "CONG-001"}],
 "regles": [{"code": "RG-01", "texte": "…", "exig": "CONG-001"}],
 "ecarts": [{"entite": "DEMANDE", "existant": "LeaveRequest", "statut": "partiel", "note": "…"}]}
```

Placement : une entité mesure 212 px de large ; laisser au moins 250 px entre colonnes et
tenir compte de la hauteur (26 + 10 + 15 par attribut). Une association sans `vue` n'apparaît
que dans le tableau. `fk` sur un lien 1,1 indique la clé étrangère (sert au modèle logique).
`c` vaut `0,1`, `1,1`, `0,n` ou `1,n`. L'utilisateur peut ensuite déplacer les blocs à la souris.

## dev/boucle — Boucle de dev (document unique)

```json
{"titre": "Boucle de développement", "sousTitre": "Commandes du quotidien.",
 "sections": [{"titre": "Démarrer", "cmds": [{"cmd": "npm run dev", "desc": "Lancer en local"}]}],
 "reperes": [{"t": "En codant", "d": "http://localhost:3000"}],
 "notes": ["Ne jamais supprimer le volume de la base."]}
```

## Valeurs autorisées

| Champ | Valeurs |
|---|---|
| fonctionnalites.statut | `a_faire`, `en_cours`, `a_verifier`, `bloque`, `termine` |
| decisions.statut | `a_trancher`, `tranche`, `applique`, `abandonne` |
| exigences.couverture | `couvert`, `partiel`, `non_couvert`, `a_verifier` |
| recette.statut | `non_execute`, `ok`, `ko`, `bloque` |
| criticite (exigences, recette) | `Bloquant`, `Critique`, `Majeur`, `Mineur` |
| plan.lots.statut | `a_faire`, `en_cours`, `termine`, `bloque` |
| plan.modules.sens | `amont`, `aval`, `both` |
| plan.lots.deps.t | `L`, `M` |
| cycle.etapes.etat | `existe`, `partiel`, `a_dev` |
| merise.ecarts.statut | `couvert`, `partiel`, `non_couvert` |

## Ordre de remplissage conseillé

1. `fiche/main`, `demarrage`, `lectures` : la prise en main.
2. `fonctionnalites`, `decisions` : l'état du travail.
3. Si un cahier d'exigences existe : `exigences`, `recette`.
4. Si le code ou une spec le permet : `merise/mcd`, `plan/dev`, `cycle/vie`.
5. Si l'utilisateur a une routine de travail : `dev/boucle`.

Mieux vaut un onglet absent qu'un onglet rempli de suppositions : ne créer que ce que les
documents du projet permettent d'établir.
