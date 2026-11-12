# Déduire le tableau à partir du dépôt

Ce guide dit comment remplir chaque onglet avec ce que le dépôt contient, sans interroger le
développeur. Point de départ : l'inventaire de `scripts/explorer_projet.py`. Il dit où
chercher ; c'est la lecture des fichiers qui établit les faits.

Sommaire : budget de lecture · fiche · démarrage · lectures · fonctionnalités et statuts ·
décisions · exigences et recette · MERISE · plan et cycle · boucle de dev · à confirmer.

## Budget de lecture

Un module se documente en lisant, dans cet ordre, puis on s'arrête quand on a de quoi remplir :
1. Les documents du projet qui le concernent : `projet.documents_cles` (CLAUDE.md, AGENTS.md,
   DECISIONS.md, PROGRESS.md, README) en cherchant les passages sur le module, puis
   `module.documents` (les premiers sont les plus pertinents).
2. L'aide du module (`fichiers.aide`), surtout `workflows.md` et `champs.md`.
3. Les fichiers serveur et de logique : noms des fonctions exportées, statuts, règles.
4. Les écrans : quelles pages, vues ou routes existent.
5. Les tests : ce qui est vérifié.

Ne pas lire tous les fichiers du module ligne à ligne. Pour vérifier une fonctionnalité,
chercher (grep) le nom de la fonction, du statut ou de l'écran attendu. En mode « tous les
modules », viser une lecture comparable pour chaque module plutôt que tout lire pour le premier.

## fiche/main

- `nom` : nom métier du module (d'après l'aide ou les documents), pas le nom de dossier
  s'il est technique. `code` : `module.code`.
- `definition`, `but`, `usage` : d'après les documents et l'aide. `usage` liste les écrans
  réels (`fichiers.écrans`, chemins de route sans les groupes entre parenthèses).
- `architecture` : une ligne par couche présente, au format `Couche :: fichiers ou rôle`,
  à partir de `module.fichiers` et `modeles_donnees` (citer fichier et ligne de chaque entité).
  Nommer les couches avec le vocabulaire de la pile (contrôleurs, services, vues Django,
  composants React…), d'après `projet.pile`.
- `liens` : à partir de `depend_de` (le module utilise) et `utilise_par` (l'utilisent),
  avec les fonctions concernées.
- `docs` : les documents effectivement lus. `fichiers` : 5 à 12 fichiers clés.
- Si le module a un cahier d'exigences avec plusieurs périmètres, renseigner `perimetres`.

## demarrage

Un parcours de 4 à 8 étapes, construit d'après le dépôt :
1. Lire la constitution du projet (CLAUDE.md, AGENTS.md) si elle existe.
2. Lire le ou les documents de cadrage et de spécification du module.
3. Lire l'aide du module.
4. Parcourir les fichiers clés en nommant les fonctions principales.
5. Lancer l'application : la commande vient de `projet.scripts` (`dev`, `start`) ou du README.
   Indiquer l'écran du module à ouvrir. Ne jamais recopier de mot de passe : renvoyer vers le
   fichier ou le README qui les donne.
6. Lancer les tests (`projet.scripts.test`, ou la commande du framework détecté) et, s'il
   existe, l'audit d'aide.
Tout décoché. Relier chaque lecture à son étape (`etape`).

## lectures

Recopier en Markdown, dans l'ordre de lecture : les sections de CLAUDE.md utiles au module
(pas tout le fichier s'il est long), les documents du module, l'aide (`workflows.md`,
`champs.md`). `maj` : date du dernier commit du fichier (`git log -1 --format=%ad --date=short -- <fichier>`)
ou la date du jour. Couper au-delà de 250 ko. Retirer les secrets avant de recopier.

## fonctionnalités et statuts

La liste vient des documents (spec, cadrage, aide, roadmap) et, à défaut, des fonctions
serveur et des écrans existants. Grouper par `palier` : le lot ou la version cités par les
documents, sinon par thème (Modèle, Paramétrage, Saisie, Validation, Suivi, Reporting…).

Chaque statut s'appuie sur une preuve, citée dans `note` (chemin de fichier, fonction, test) :

| Statut | Preuve attendue |
|---|---|
| `termine` | Implémenté de bout en bout (serveur ou logique **et** écran ou appel), couvert par un test **ou** décrit dans l'aide, et aucun fichier concerné dans `non_commites` |
| `a_verifier` | Code présent mais ni test ni aide ; **ou** fichiers concernés modifiés et non commités (le noter : « codé, non commité ») ; **ou** la preuve est indirecte |
| `en_cours` | Une partie seulement des couches existe, ou des `TODO`/`FIXME` portent sur la fonctionnalité, ou des commits récents la travaillent sans qu'elle soit complète |
| `bloque` | Un document dit qu'elle attend une décision ou une autre équipe ; renseigner l'arbitrage correspondant |
| `a_faire` | Décrite dans les documents, aucune trace dans le code |

En cas de doute entre deux statuts, prendre le moins avancé et l'expliquer dans `note`.
`termineLe` : la date du commit qui l'a livrée si on la trouve, sinon vide.

## decisions

- Choix actés : entrées de DECISIONS.md (ou équivalent) qui concernent le module, statut
  `applique` si le code les reflète, `tranche` sinon. Citer la source dans `ref`.
- Questions ouvertes (`a_trancher`), avec `contexte` et `recommandation` :
  - formulations « à confirmer », « à définir », « TBD », « question ouverte » dans les documents ;
  - contradictions entre deux documents, ou entre un document et le code (le dire précisément) ;
  - `TODO` qui posent une question (« ? ») ;
  - règles du projet non respectées par le code (secret dans le dépôt, filtrage manquant…).
- Ne jamais trancher à la place de l'équipe : la recommandation est une proposition.

## exigences et recette

Seulement si un document liste des exigences identifiées (motif du type `ABC-001`) ou des cas
de test. Reprendre identifiants, sections et critères tels quels. `couverture` : même règle de
preuve que les fonctionnalités (`couvert` ≈ `termine`, `partiel` ≈ `en_cours`, `non_couvert`
≈ `a_faire`), `note` cite la preuve. Recette : statut `non_execute` partout, sauf résultat
documenté.

## merise/mcd

Si `module.modeles_donnees` n'est pas vide :

```bash
python <skill>/scripts/modele_vers_mcd.py --racine . --entites <Entité1,Entité2> --sortie <dossier>/mcd.json
```

Si la pile n'est pas lue automatiquement (`projet.modele_donnees.source` vide ou d'une autre
couche que celle du projet), lire les fichiers de modèle du module et écrire le format neutre
(en tête de `scripts/modeles_donnees.py`), puis passer `--neutre <fichier>` au lieu de
`--racine`. Si plusieurs sources existent (`autres_sources`, par exemple un ORM et des
migrations SQL), garder celle que le code utilise réellement ; `--source` force un lecteur.

Puis lire le résultat et l'enrichir : nommer les associations avec un verbe métier
(`PROVENIR`, `PILOTER`…) quand les documents le permettent, compléter `lecture`, ajouter des
`regles` de gestion tirées des documents, et des `ecarts` si les documents décrivent des
entités absentes du code (`non_couvert`). Insérer le document sous la clé `merise/mcd` du
remplissage. Sans modèle de données dans le code, ne créer le MCD que si un document le décrit.

## plan/dev et cycle/vie

- `modules` : un par clé de `depend_de` et de `utilise_par` (hors `socle`, sauf si utile),
  avec ses `contacts` (fichier, fonctions, usage). `sens` : `amont` si le module suivi
  l'utilise, `aval` s'il est utilisé par lui, `both` si les deux. `mien` : vrai pour les
  modules que le même développeur maintient, faux sinon (faux par défaut).
- `lots` : seulement si une roadmap, un plan ou les documents découpent le travail restant.
  Sinon, ne pas inventer de lots : laisser le plan sans lots et ne créer que la carte des
  dépendances, avec `phases` vide et `lots` vide. La page reste utile.
- `cycle/vie` : seulement si les documents ou le code décrivent un cycle de statuts (enum de
  statuts, workflow). `etat` de chaque étape selon la règle de preuve.

## dev/boucle

Commun à tous les modules d'un projet : le construire une fois et le copier. Partir de
`projet.pile.commandes` : chaque commande indique son `origine`. Celles qui viennent de la
configuration (`package.json`, `Makefile`, `composer.json`, fichier compose) sont sûres ;
celles marquées « convention » sont déduites du framework et vont dans « À confirmer », sauf
si le README les confirme. Sections : démarrer les services, coder, vérifier avant de
commiter (tests, lint, audits), migrations, commiter, arrêter. `reperes` : adresses locales
lues dans la configuration ou le README. Jamais de mot de passe ni de chemin personnel.

## À confirmer

Garder une liste courte de ce qui a été déduit avec une confiance moyenne (nom métier du
module, regroupement d'alias, statut ambigu, correspondance entre un nom demandé et un module
du code). Elle va dans le compte rendu final, pas dans une question au développeur.
