---
name: suivi-module
description: "Crée, relit et met à jour le tableau de suivi d'un module ou de tous les modules d'un projet logiciel, en explorant le dépôt lui-même (code, documents, modèle de données, aide, git) sans rien demander au développeur, quelle que soit la technologie (JS/TS, Python, Java/Kotlin, C#, PHP, Ruby, Go…). Neuf onglets : vue d'ensemble, démarrage, lecture, MCD MERISE, exigences et recette, plan et dépendances, boucle de dev, fonctionnalités, arbitrages ; plus une page d'accueil de tous les modules. Pages HTML dans `suivi/` (Claude Code) ou artefacts privés (claude.ai). Utiliser dès que l'utilisateur dit « utilise le skill suivi-module », « crée le tableau de suivi du module X / de tous les modules », « où en est le module », « mets à jour / relis le tableau de suivi », veut prendre en main un module ou faire le point sur le livré et les arbitrages, même sans dire « tableau », ou si un dossier `suivi/` existe."
---

# Tableau de suivi de module

Ce skill donne à chaque module un poste de pilotage : ce qu'il fait, comment le prendre en main,
ce qui est livré, ce qui reste à faire, ce qui attend une décision. La page est fixe
(`assets/template.html`) ; on ne lui fournit que des données.

## Les deux règles qui comptent

**1. Ne pas fatiguer le développeur.** Il dit « crée le tableau de suivi du module X » ou
« … de tous les modules », et c'est tout. Quand le dépôt est accessible, ne poser aucune
question : explorer, lire, déduire, construire, puis rendre compte. Ce qui reste incertain va
dans une courte liste « À confirmer » à la fin, jamais dans une question préalable. Une seule
exception : le nom demandé ne correspond à aucun module, même après recherche dans les
documents (voir « Créer », étape 1).

**2. Ne rien affirmer sans preuve.** Chaque statut s'appuie sur un fichier, un test, un commit
ou un document, cité dans la note. Ce qu'on ne peut pas établir reste `a_verifier`, `a_faire`
ou `a_trancher`. Un onglet absent vaut mieux qu'un onglet rempli de suppositions. Les règles
de preuve sont dans `references/exploration.md`.

## Mode et portée

- **Mode local** (Claude Code, ou tout environnement avec le dépôt sur disque et sans outil
  `Artifact`) : chaque module a `suivi/<code>/remplissage.json` (versionné) et
  `suivi/<code>/index.html` (généré). En portée « tous », `suivi/index.html` récapitule.
- **Mode artefact** (outil `Artifact` présent, claude.ai) : chaque module est un artefact privé.
  Les sources sont les fichiers joints, les connecteurs disponibles ou un dépôt cloné dans le
  conteneur. Si rien n'est accessible, demander en une phrase les documents ou le dépôt.
- **Portée** : « le module X » → un module ; « tous les modules », « chaque module », « le
  projet » → tous les modules détectés.

Dans les commandes, `<skill>` est le dossier de ce skill ; `<code>` est le code du module en
minuscules (ex. `diligence`) ; `<dossier>` vaut `suivi/<code>` en mode local et
`/mnt/user-data/outputs/suivi-<code>` en mode artefact.

Si `suivi/<code>/remplissage.json` existe déjà, ou si l'utilisateur donne le lien d'un
artefact de suivi, c'est une **mise à jour** : aller à « Mettre à jour ». Ne jamais créer un
second tableau pour le même module.

## Créer

**1. Explorer.** Depuis la racine du dépôt :

```bash
python <skill>/scripts/explorer_projet.py . --sortie suivi/.inventaire.json                 # tous les modules
python <skill>/scripts/explorer_projet.py . --module "<nom>" --sortie suivi/.inventaire.json # un module
```

L'inventaire donne la pile du projet (`projet.pile` : langages, frameworks, outils de test,
commandes trouvées dans la configuration ou déduites des conventions du framework), le modèle
de données (`projet.modele_donnees` : technologie lue, nombre d'entités), et par module :
fichiers par couche, documents qui en parlent, entités (`modeles_donnees`), dépendances
d'après les imports et le modèle de données (`depend_de`, `utilise_par`), historique git,
fichiers **non commités**, tests, TODO.

La détection des modules suit les conventions courantes : dossiers d'écrans et de routes,
fichiers serveur, apps Django, paquets organisés par couche (Spring, NestJS, Go, architecture
hexagonale), contrôleurs et modèles Rails ou Laravel, aide par module. Si la structure du
projet est inhabituelle et que l'inventaire est pauvre, compléter par une lecture de
l'arborescence (`find . -maxdepth 3 -type d`), sans demander au développeur.

Si `--module` renvoie « introuvable » (code 3), le nom demandé est souvent un nom métier :
chercher ce nom dans les documents (`grep -ril "<nom>" --include=*.md .`) pour trouver le
module du code qui lui correspond, et retenir la correspondance la plus nette en la mettant
dans « À confirmer ». Si rien ne ressort, poser une seule question en proposant les modules
détectés.

En portée « tous », relire la liste : regrouper les candidats qui sont le même module sous
deux noms, écarter ceux qui ne sont que des utilitaires (un ou deux fichiers, ni écran ni aide
ni document) et le signaler dans le compte rendu.

**2. Lire et déduire.** Suivre `references/exploration.md` : budget de lecture, puis règles
de remplissage de chaque onglet, dont la règle de preuve des statuts. Pour le modèle MERISE,
quand le module a des entités :

```bash
python <skill>/scripts/modele_vers_mcd.py --racine . --entites <Entité1,Entité2> --sortie <dossier>/mcd.json
```

Le modèle est lu automatiquement pour Prisma, SQL et migrations SQL, Django, SQLAlchemy,
TypeORM, JPA/Hibernate, Entity Framework, Rails, Laravel, Mongoose et Drizzle. Pour une autre
technologie (GORM, Sequelize, Doctrine, Ecto…), ou si `projet.modele_donnees.source` est vide
alors que le projet a des modèles : lire les fichiers de modèle, écrire le format neutre décrit
en tête de `scripts/modeles_donnees.py` dans `<dossier>/modele.json`, puis lancer
`modele_vers_mcd.py --neutre <dossier>/modele.json --entites …`.

**3. Écrire `<dossier>/remplissage.json`** au format de `references/donnees.md` (formes
exactes, valeurs autorisées). La boucle de dev est commune au projet : la construire une
fois et la reprendre dans chaque module.

**4. Retirer les secrets.** Le JSON est commité (mode local) ou lisible par qui reçoit
l'artefact. Jamais de mot de passe, même de démonstration, de secret, de clé, d'adresse IP
interne, d'identifiant de connexion ni de chemin personnel : renvoyer vers le fichier qui les
contient (« voir `.env.example` »). Si le dépôt lui-même contient un secret, le signaler dans
les arbitrages et dans le compte rendu.

**5. Vérifier.**

```bash
python <skill>/scripts/preparer_remplissage.py <dossier>/remplissage.json --sortie <dossier>/remplissage
```

Corriger chaque ERREUR jusqu'au code 0. `--autoriser-secrets` seulement si l'utilisateur
confirme qu'un motif signalé n'en est pas un.

**6 (mode local). Générer les pages.**

```bash
python <skill>/scripts/construire_page_locale.py suivi/<code>/remplissage.json --sortie suivi/<code>/index.html
python <skill>/scripts/construire_index.py suivi --projet "<nom du projet>"   # portée « tous », ou dès qu'il y a 2 modules
```

Ajouter au `.gitignore` du projet, s'ils n'y sont pas : `suivi/*/remplissage/`,
`suivi/*/mcd.json`, `suivi/.inventaire.json`. Garder `remplissage.json` et `index.html`
versionnés.

**6 (mode artefact). Publier et remplir.** Copier `assets/template.html` vers
`<dossier>/index.html`, remplacer le contenu de `<title>` par `Suivi de module — <Nom>`, puis
appeler `Artifact` avec `action: "publish"`, ce `file_path`, `capabilities: {"db": {}}`,
`favicon: "📋"`, `title: "Suivi de module — <Nom>"`. Sans `capabilities`, la page reste
« Hors ligne ». Ensuite, pour chaque `<dossier>/remplissage/lots/lot_NN.json`, appeler
`Artifact` avec `action: "write_db"`, l'`url` publiée, `db_op: "batch"` et `writes` = le
contenu du fichier. En portée « tous », un artefact par module.

En portée « tous », enchaîner les modules sans s'arrêter entre deux pour demander
confirmation.

**7. Rendre compte**, brièvement :
- ce qui a été créé (chemins ou liens) et, par module, l'état en une ligne
  (`python <skill>/scripts/comparer_lectures.py --resume <dossier>/remplissage`) ;
- ce qui demande l'attention : travail non commité, arbitrages ouverts, secrets trouvés ;
- les onglets non créés faute de source ;
- la liste « À confirmer » ;
- en mode local : « ouvrez `suivi/index.html` (ou `suivi/<code>/index.html`) dans le navigateur ».

## Mettre à jour

**Mode local.** Refaire « Créer », étapes 1 à 4, en écrivant `<dossier>/remplissage.nouveau.json`,
puis fusionner pour garder ce que les personnes ont saisi (coches, décisions prises, résultats
de recette, éléments ajoutés à la main, positions du MCD) :

```bash
python <skill>/scripts/fusionner_remplissage.py <dossier>/remplissage.json <dossier>/remplissage.nouveau.json --sortie <dossier>/remplissage.json
```

Supprimer `remplissage.nouveau.json`, puis reprendre aux étapes 5 et 6. Rendre compte des
désaccords que la fusion affiche. Si l'utilisateur a coché des éléments dans la page sans les
exporter, lui dire d'utiliser d'abord le bouton « Exporter » et de remplacer le
`remplissage.json` du projet par le fichier téléchargé, car la page repart du fichier dès qu'il
change.

Pour une modification ponctuelle (« passe L3 en terminé »), modifier directement le JSON,
puis étapes 5 et 6.

**Mode artefact.** Lire le document (`read_db`, `db_op: "get"`) pour avoir sa `version`, puis
`write_db` (`update` ou `set`) avec `if_version`. Plusieurs documents : `batch`. Quand un
statut passe à `termine` ou `ok`, renseigner `termineLe` ou `testeLe`.

## Relire

« Relis le tableau », « qu'est-ce qui a changé », « où en est le module » :

- **Mode local** : comparer avec la version commitée (`git diff -- suivi/`), relancer
  l'explorateur pour repérer ce qui a bougé dans le code depuis (commits, non commités), et
  résumer avec `comparer_lectures.py --resume`.
- **Mode artefact** : lire la page (`action: "read"`) pour connaître ses collections, puis
  chaque collection avec `read_db` (`db_op: "list"`, `query: {"limit": 1000}`, `out_dir`
  `<dossier>/lecture-N`) ; comparer avec la lecture précédente si elle existe :
  `python <skill>/scripts/comparer_lectures.py <lecture-précédente> <lecture-N>`.

Rendre compte de ce qui a changé et de ce qui demande l'attention : travail codé mais non
commité, lot avancé alors qu'un arbitrage le bloque, incohérence entre onglets. Ne rien
modifier sans que l'utilisateur le demande.

## Partager

Mode local : le tableau voyage avec le dépôt. Mode artefact : l'artefact est privé ; partager
son lien donne accès aux mêmes données, ce qui convient à l'équipe du module. Une autre
personne installe le skill et crée son propre tableau. Options de partage :
https://support.claude.com.

## Fichiers du skill

- `assets/template.html` : la page d'un module ; données embarquées (mode local) ou base de l'artefact.
- `references/exploration.md` : comment déduire chaque onglet du dépôt, règles de preuve.
- `references/donnees.md` : forme exacte des données de chaque onglet.
- `scripts/explorer_projet.py` : inventaire du dépôt (pile, modules, couches, documents, entités, dépendances, git).
- `scripts/modeles_donnees.py` : lecture du modèle de données de 11 technologies vers un format neutre.
- `scripts/modele_vers_mcd.py` : modèle MERISE déduit du modèle de données (automatique ou neutre).
- `scripts/preparer_remplissage.py` : vérification (statuts, références, secrets) et lots d'écriture.
- `scripts/construire_page_locale.py` : page d'un module en mode local.
- `scripts/construire_index.py` : page d'accueil de tous les modules.
- `scripts/fusionner_remplissage.py` : mise à jour sans perte des saisies.
- `scripts/comparer_lectures.py` : ce qui a changé entre deux lectures, ou état chiffré.
