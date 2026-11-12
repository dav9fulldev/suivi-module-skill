---
name: suivi-module
description: "Crée, relit et met à jour le tableau de suivi d'un module ou de tous les modules d'un projet logiciel, en explorant le dépôt lui-même (code, documents, modèle de données, aide, git) sans rien demander au développeur, quelle que soit la technologie (JS/TS, Python, Java/Kotlin, C#, PHP, Ruby, Go…). Neuf onglets : vue d'ensemble, démarrage, lecture, MCD MERISE, exigences et recette, plan et dépendances, boucle de dev, fonctionnalités, arbitrages ; plus une page d'accueil de tous les modules. Livrés en artefacts Claude privés quand l'outil d'artefacts est disponible, sinon en pages HTML dans `suivi/`. Utiliser dès que l'utilisateur dit « utilise le skill suivi-module », « crée le tableau de suivi du module X / de tous les modules », « où en est le module », « mets à jour / relis le tableau de suivi », veut prendre en main un module ou faire le point sur le livré et les arbitrages, même sans dire « tableau », ou si un dossier `suivi/` existe."
---

# Tableau de suivi de module

Ce skill donne à chaque module un poste de pilotage : ce qu'il fait, comment le prendre en main,
ce qui est livré, ce qui reste à faire, ce qui attend une décision. La page est fixe
(`assets/template.html`) ; on ne lui fournit que des données.

## Les trois règles qui comptent

**1. Les tableaux sont des artefacts.** C'est le format voulu : un artefact Claude privé par
module, plus un artefact d'accueil qui les récapitule. Les pages HTML locales ne sont qu'un
repli, pour un environnement sans outil `Artifact` (Claude Code sans cet outil, autre agent).

**2. Ne pas fatiguer le développeur.** Il dit « crée le tableau de suivi du module X » ou
« … de tous les modules », et c'est tout. Quand les sources sont accessibles, ne poser aucune
question : explorer, lire, déduire, construire, puis rendre compte. Ce qui reste incertain va
dans une courte liste « À confirmer » à la fin. Deux exceptions seulement : aucune source n'est
accessible (voir « Sources »), ou le nom demandé ne correspond à aucun module même après
recherche dans les documents.

**3. Ne rien affirmer sans preuve.** Chaque statut s'appuie sur un fichier, un test, un commit
ou un document, cité dans la note. Ce qu'on ne peut pas établir reste `a_verifier`, `a_faire`
ou `a_trancher`. Un onglet absent vaut mieux qu'un onglet rempli de suppositions. Les règles de
preuve sont dans `references/exploration.md`.

## Mode, sources et portée

**Mode.** L'outil `Artifact` (actions `publish`, `write_db`, `read_db`) est disponible → mode
**artefact**, toujours. Sinon → mode **local** : `suivi/<code>/remplissage.json` (versionné) et
`suivi/<code>/index.html` (généré), plus `suivi/index.html` pour l'accueil. Le choix ne dépend
que des outils présents ; ne pas le demander, sauf préférence exprimée par l'utilisateur.

**Sources**, dans l'ordre de préférence :
1. Le dépôt sur disque (Claude Code) : explorer depuis sa racine.
2. Un dépôt joint ou récupérable : une archive (`.zip`, `.tar.gz`) jointe, à décompresser dans
   `/home/claude/projet` ; un dépôt GitHub public à cloner (`git clone --depth 1`) si le réseau
   du conteneur le permet ; ou les fichiers d'un connecteur disponible (GitHub, Drive…).
3. Un dossier `suivi/` produit en mode local (joint en archive ou fichier par fichier) :
   le publier en artefacts tel quel, voir « Publier des tableaux existants ».
4. Des documents joints seuls (spec, CLAUDE.md…) : tableau partiel, sans preuve tirée du code ;
   le dire dans le compte rendu.
Si rien de tout cela n'est disponible, demander en une phrase : « Joignez une archive du dépôt,
donnez le lien d'un dépôt GitHub public, ou joignez le dossier `suivi/` produit par Claude Code. »

**Portée.** « le module X » → un module ; « tous les modules », « chaque module », « le projet »
→ tous les modules détectés, plus l'accueil.

Dans les commandes, `<skill>` est le dossier de ce skill ; `<code>` est le code du module en
minuscules (ex. `diligence`) ; `<dossier>` vaut `/mnt/user-data/outputs/suivi-<code>` en mode
artefact et `suivi/<code>` en mode local.

**Un seul tableau par module.** En mode artefact, chercher d'abord les tableaux existants :
`Artifact` `action: "list"`, titres « Suivi de module — <Nom> » et « Suivi des modules — <Projet> ».
En mode local, regarder si `suivi/<code>/remplissage.json` existe. S'il existe, c'est une
**mise à jour**.

## Créer

**1. Explorer.** Depuis la racine du dépôt (ou de `/home/claude/projet`) :

```bash
python <skill>/scripts/explorer_projet.py . --sortie <racine-suivi>/.inventaire.json                  # tous les modules
python <skill>/scripts/explorer_projet.py . --module "<nom>" --sortie <racine-suivi>/.inventaire.json # un module
```

`<racine-suivi>` vaut `suivi` en mode local et `/mnt/user-data/outputs` en mode artefact.

L'inventaire donne la pile du projet (`projet.pile` : langages, frameworks, outils de test,
commandes trouvées dans la configuration ou déduites des conventions du framework), le modèle
de données (`projet.modele_donnees`), et par module : fichiers par couche, documents qui en
parlent, entités (`modeles_donnees`), dépendances d'après les imports et le modèle de données
(`depend_de`, `utilise_par`), historique git, fichiers **non commités**, tests, TODO.

La détection suit les conventions courantes : écrans et routes, fichiers serveur, apps Django,
paquets par couche (Spring, NestJS, Go, architecture hexagonale), contrôleurs et modèles Rails
ou Laravel, aide par module. Si l'inventaire est pauvre, compléter par une lecture de
l'arborescence (`find . -maxdepth 3 -type d`), sans demander au développeur.

Si `--module` renvoie « introuvable » (code 3), le nom demandé est souvent un nom métier :
chercher ce nom dans les documents (`grep -ril "<nom>" --include=*.md .`) pour trouver le module
du code correspondant, et noter la correspondance dans « À confirmer ». Si rien ne ressort,
poser une seule question en proposant les modules détectés.

En portée « tous », regrouper les candidats qui sont le même module sous deux noms, écarter les
simples utilitaires (un ou deux fichiers, ni écran ni aide ni document) et le signaler.

**2. Lire et déduire.** Suivre `references/exploration.md`. Pour le modèle MERISE, quand le
module a des entités :

```bash
python <skill>/scripts/modele_vers_mcd.py --racine . --entites <Entité1,Entité2> --sortie <dossier>/mcd.json
```

Lecture automatique pour Prisma, SQL et migrations SQL, Django, SQLAlchemy, TypeORM,
JPA/Hibernate, Entity Framework, Rails, Laravel, Mongoose et Drizzle. Pour une autre technologie,
ou si `projet.modele_donnees.source` est vide alors que le projet a des modèles : lire les
fichiers de modèle, écrire le format neutre décrit en tête de `scripts/modeles_donnees.py` dans
`<dossier>/modele.json`, puis `modele_vers_mcd.py --neutre <dossier>/modele.json --entites …`.

**3. Écrire `<dossier>/remplissage.json`** au format de `references/donnees.md`. La boucle de
dev est commune au projet : la construire une fois et la reprendre dans chaque module.

**4. Retirer les secrets.** Le contenu est lisible par qui reçoit l'artefact, ou commité en mode
local. Jamais de mot de passe, même de démonstration, de secret, de clé, d'adresse IP interne,
d'identifiant de connexion ni de chemin personnel : renvoyer vers le fichier qui les contient
(« voir `.env.example` »). Si le dépôt lui-même contient un secret, le signaler dans les
arbitrages et dans le compte rendu.

**5. Vérifier.**

```bash
python <skill>/scripts/preparer_remplissage.py <dossier>/remplissage.json --sortie <dossier>/remplissage
```

Corriger chaque ERREUR jusqu'au code 0. `--autoriser-secrets` seulement si l'utilisateur
confirme qu'un motif signalé n'en est pas un.

**6. Livrer** : « Publier en artefacts » (mode artefact) ou « Générer les pages locales ».
En portée « tous », enchaîner les modules sans s'arrêter pour demander confirmation.

**7. Rendre compte**, brièvement :
- ce qui a été créé (liens des artefacts, ou chemins) et, par module, l'état en une ligne
  (`python <skill>/scripts/comparer_lectures.py --resume <dossier>/remplissage`) ;
- ce qui demande l'attention : travail non commité, arbitrages ouverts, secrets trouvés ;
- les onglets non créés faute de source ;
- la liste « À confirmer » ;
- en mode artefact, que les artefacts sont privés jusqu'à ce que l'utilisateur les partage.

## Publier en artefacts

Pour chaque module :
1. Copier `assets/template.html` vers `<dossier>/index.html` ; remplacer seulement le contenu de
   `<title>` par `Suivi de module — <Nom>`.
2. `Artifact` `action: "publish"`, `file_path` de cette copie, `capabilities: {"db": {}}`,
   `favicon: "📋"`, `title: "Suivi de module — <Nom>"`. Sans `capabilities`, la page reste
   « Hors ligne » et sa base ne peut pas être remplie.
3. Pour chaque `<dossier>/remplissage/lots/lot_NN.json` : `Artifact` `action: "write_db"`,
   `url` publiée, `db_op: "batch"`, `writes` = le contenu du fichier.
4. Noter le lien dans `/mnt/user-data/outputs/liens.json` (`{"<code>": "<url>"}`).

Puis, dès que deux modules au moins sont publiés (et toujours en portée « tous »), l'accueil :

```bash
python <skill>/scripts/construire_index.py /mnt/user-data/outputs --projet "<Projet>" \
  --liens /mnt/user-data/outputs/liens.json --sortie /mnt/user-data/outputs/suivi-accueil/index.html
```

Publier `suivi-accueil/index.html` avec `title: "Suivi des modules — <Projet>"`, `favicon: "🗂️"`
(page statique : pas de `capabilities`). L'accueil est un instantané : le republier (avec son
`url`) après chaque création ou mise à jour d'un module.

## Publier des tableaux existants

Quand l'utilisateur fournit un dossier `suivi/` produit en mode local (« publie mes tableaux de
suivi en artefacts ») : pour chaque `suivi/<code>/remplissage.json`, reprendre « Créer » à
l'étape 5 (vérifier), puis « Publier en artefacts ». Pas de nouvelle exploration : les données
sont déjà établies.

## Générer les pages locales

```bash
python <skill>/scripts/construire_page_locale.py suivi/<code>/remplissage.json --sortie suivi/<code>/index.html
python <skill>/scripts/construire_index.py suivi --projet "<nom du projet>"   # dès qu'il y a 2 modules
```

Ajouter au `.gitignore` du projet, s'ils n'y sont pas : `suivi/*/remplissage/`, `suivi/*/mcd.json`,
`suivi/*/modele.json`, `suivi/.inventaire.json`. Garder `remplissage.json` et `index.html` versionnés.
Dire à l'utilisateur d'ouvrir `suivi/index.html` (ou `suivi/<code>/index.html`), et qu'il peut
publier ce dossier en artefacts depuis claude.ai en le joignant et en le demandant.

## Mettre à jour

Le principe : régénérer à partir des sources, puis fusionner avec l'existant pour garder ce que
les personnes ont saisi (coches, décisions prises, résultats de recette, ajouts manuels,
positions du MCD).

**Mode artefact.**
1. Lire la base de l'artefact du module : `read_db` `db_op: "list"`, `query: {"limit": 1000}`,
   `out_dir: <dossier>/lecture-N`, pour chaque collection (`fiche`, `demarrage`, `lectures`,
   `fonctionnalites`, `decisions`, `exigences`, `recette`, `plan`, `cycle`, `merise`, `dev`).
2. `python <skill>/scripts/lecture_vers_remplissage.py <dossier>/lecture-N --sortie <dossier>/remplissage.actuel.json`
3. Refaire « Créer », étapes 1 à 4, dans `<dossier>/remplissage.nouveau.json`.
4. `python <skill>/scripts/fusionner_remplissage.py <dossier>/remplissage.actuel.json <dossier>/remplissage.nouveau.json --sortie <dossier>/remplissage.json`
5. Étape 5 de « Créer », puis réécrire la base de l'artefact existant (`write_db` `batch` avec les
   lots, sur son `url`) ; ne pas republier une nouvelle page. Republier l'accueil.

Pour une modification ponctuelle (« passe L3 en terminé ») : `read_db` `db_op: "get"` pour la
`version`, puis `write_db` `update` avec `if_version`. Quand un statut passe à `termine` ou
`ok`, renseigner `termineLe` ou `testeLe`.

**Mode local.** Refaire « Créer », étapes 1 à 4, dans `<dossier>/remplissage.nouveau.json`, puis
`fusionner_remplissage.py <dossier>/remplissage.json <dossier>/remplissage.nouveau.json --sortie <dossier>/remplissage.json`,
supprimer le fichier `.nouveau`, et reprendre aux étapes 5 et « Générer les pages locales ». Si
l'utilisateur a coché des éléments dans la page sans les exporter, lui dire d'abord d'utiliser le
bouton « Exporter » et de remplacer `remplissage.json` par le fichier téléchargé.

Dans les deux modes, rendre compte des désaccords que la fusion affiche.

## Relire

« Relis le tableau », « qu'est-ce qui a changé », « où en est le module » :
- **Mode artefact** : lire la page (`action: "read"`) pour connaître ses collections, lire chacune
  avec `read_db` dans `<dossier>/lecture-N`, puis comparer avec la lecture précédente si elle
  existe : `python <skill>/scripts/comparer_lectures.py <lecture-précédente> <lecture-N>`.
- **Mode local** : `git diff -- suivi/`, puis l'explorateur pour repérer ce qui a bougé dans le
  code (commits, non commités), et `comparer_lectures.py --resume`.

Rendre compte de ce qui a changé et de ce qui demande l'attention : travail codé mais non
commité, lot avancé alors qu'un arbitrage le bloque, incohérence entre onglets. Ne rien modifier
sans que l'utilisateur le demande.

## Partager

Un artefact est privé tant que l'utilisateur ne le partage pas. Partager son lien donne accès
aux mêmes données : c'est le bon choix pour l'équipe du module. Une autre personne qui veut
suivre son propre projet installe le skill et crée ses propres tableaux. Options de partage :
https://support.claude.com. En mode local, le tableau voyage avec le dépôt.

## Fichiers du skill

- `assets/template.html` : la page d'un module ; base de l'artefact, ou données embarquées en local.
- `references/exploration.md` : comment déduire chaque onglet du dépôt, règles de preuve.
- `references/donnees.md` : forme exacte des données de chaque onglet.
- `scripts/explorer_projet.py` : inventaire du dépôt (pile, modules, couches, documents, entités, dépendances, git).
- `scripts/modeles_donnees.py` : lecture du modèle de données de 11 technologies vers un format neutre.
- `scripts/modele_vers_mcd.py` : modèle MERISE déduit du modèle de données (automatique ou neutre).
- `scripts/preparer_remplissage.py` : vérification (statuts, références, secrets) et lots d'écriture.
- `scripts/construire_page_locale.py` : page d'un module en mode local.
- `scripts/construire_index.py` : page d'accueil de tous les modules (liens locaux ou artefacts).
- `scripts/lecture_vers_remplissage.py` : base d'un artefact → remplissage.json.
- `scripts/fusionner_remplissage.py` : mise à jour sans perte des saisies.
- `scripts/comparer_lectures.py` : ce qui a changé entre deux lectures, ou état chiffré.
