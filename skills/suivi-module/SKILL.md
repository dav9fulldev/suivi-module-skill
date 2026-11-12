---
name: suivi-module
description: Crée, relit et met à jour un tableau de suivi de module ou de projet logiciel à 9 onglets (vue d'ensemble, démarrage, lecture des documents, modèle MERISE, exigences et recette, plan de développement avec carte des dépendances, boucle de dev, fonctionnalités, arbitrages). Sur claude.ai, le tableau est un artefact privé ; dans Claude Code ou ailleurs, une page HTML générée dans le projet à partir d'un JSON versionné. Utiliser ce skill dès que l'utilisateur veut suivre l'avancement d'un module, d'un lot ou d'un projet, prendre en main un module existant, faire le point sur ce qui est livré et ce qui reste à arbitrer, ou demande « crée mon tableau de suivi », « fais le suivi de mon module », « relis / mets à jour mon tableau de suivi », « où en est le module », même sans prononcer le mot « tableau ». L'utiliser aussi quand il donne le lien d'un artefact « Suivi modul… » ou « Suivi de module », ou qu'un dossier `suivi/` existe dans le projet.
---

# Tableau de suivi de module

Ce skill produit un tableau de bord qui sert de poste de pilotage à un développeur
sur un module : ce que fait le module, comment le prendre en main, ce qui est livré, ce qui
reste à faire et ce qui attend une décision. La page est fixe (`assets/template.html`) et
toutes les données sont à part. On ne réécrit jamais la page pour un projet : on lui fournit
des données.

## Choisir le mode

- **Mode artefact** : l'outil `Artifact` (actions `publish`, `write_db`, `read_db`) est
  disponible, ce qui est le cas sur claude.ai. Le tableau est un artefact privé, ses données
  sont dans la base de l'artefact.
- **Mode local** : partout ailleurs, par exemple dans Claude Code. Le tableau est un fichier
  `suivi/<code>/index.html` dans le projet, généré à partir de `suivi/<code>/remplissage.json`.
  Ce JSON est versionné avec le code : il suit les branches et les revues.

Le choix ne dépend que des outils présents. Ne pas demander à l'utilisateur de choisir, sauf
s'il exprime une préférence. Les étapes 1 à 4 de « Créer » sont communes aux deux modes.
Dans les commandes ci-dessous, `<skill>` désigne le dossier de ce skill et `<dossier>` vaut
`/mnt/user-data/outputs/suivi-<code>` en mode artefact, `suivi/<code>` en mode local.

Le tableau ne vaut que par sa fiabilité. Chaque statut doit pouvoir se justifier par un
document ou par le code. Ce qu'on ne peut pas établir reste `a_verifier` ou `a_trancher`, ou
n'est pas créé. Un onglet absent vaut mieux qu'un onglet rempli de suppositions.

## Trois situations

1. **Créer** un tableau pour un module (rien n'existe encore) : section « Créer ».
2. **Relire** un tableau existant (« relis », « mets-toi à jour », un lien d'artefact) :
   section « Relire ».
3. **Mettre à jour** des éléments précis (« passe L3 en terminé », « ajoute l'arbitrage… ») :
   section « Mettre à jour ».

Si l'utilisateur donne un lien d'artefact ou parle d'un tableau qu'il a déjà, ne jamais en
créer un second : le relire (Artifact, action `list` si le lien manque).

## Créer

**1. Rassembler les sources.** Il faut au minimum le nom du module et un ou deux documents :
CLAUDE.md ou équivalent, spécification, cahier d'exigences, notes de cadrage, journal des
décisions, extrait du schéma de données. Les prendre dans les fichiers joints ou les
connecteurs disponibles. S'il n'y a rien, demander en une question les documents à utiliser.
Ne pas inventer un module à partir de son seul nom.

**2. Écrire le fichier de remplissage.** Lire `references/donnees.md` : il donne la forme
exacte de chaque document, les valeurs autorisées et l'ordre conseillé. Écrire
`<dossier>/remplissage.json` :

```json
{"fiche/main": {...}, "demarrage": {"s01": {...}}, "lectures": {"l01": {...}},
 "fonctionnalites": {"f01": {...}}, "decisions": {"d01": {...}}}
```

Règles de contenu :
- `fiche/main` : écrite à partir des documents, dans la langue de l'utilisateur.
- `demarrage` : le parcours réel de prise en main (lire tel document, lancer l'application,
  dérouler le cycle principal, lancer les tests), tout décoché.
- `lectures` : le texte des documents de référence en Markdown, chacun relié à son étape.
- `fonctionnalites` : une ligne par fonctionnalité citée dans les documents, groupées par
  `palier`. `termine` seulement si un document ou le code l'atteste ; sinon `a_verifier`
  ou `a_faire`.
- `decisions` : les choix déjà actés (`applique` ou `tranche`, avec `ref`) et les questions
  ouvertes (`a_trancher`, avec `contexte` et `recommandation`). Les contradictions entre
  documents sont des arbitrages à trancher : les signaler, ne pas les résoudre en silence.
- `exigences` / `recette` : seulement si un cahier d'exigences existe ; reprendre ses
  identifiants. `couverture` reste `a_verifier` tant que le code n'a pas été examiné.
- `plan/dev`, `cycle/vie`, `merise/mcd`, `dev/boucle` : seulement si les sources le permettent.

**3. Retirer les secrets.** La base est lisible par toute personne avec qui l'artefact est
partagé, et en mode local le JSON est commité dans le dépôt. On n'y met jamais de mot de passe, même de démonstration, ni de secret, de clé,
d'adresse IP interne, d'identifiant de connexion ou de chemin personnel (`C:\Users\…`).
Les remplacer par une indication neutre (« voir le gestionnaire de mots de passe de
l'équipe », « adresse de la base de test : voir `.env` »). Si un document de référence en
contient, le signaler aussi à l'utilisateur, car c'est un problème dans son dépôt.

**4. Vérifier et préparer les lots.**

```bash
python <skill>/scripts/preparer_remplissage.py <dossier>/remplissage.json \
  --sortie <dossier>/remplissage
```

Corriger chaque ERREUR et relancer jusqu'au code de sortie 0. Traiter les AVERTISSEMENTS
(champ vide, référence croisée cassée) ou les accepter en connaissance de cause.
`--autoriser-secrets` ne s'utilise que si l'utilisateur confirme qu'un motif signalé n'est
pas un secret.

En mode local, ajouter `suivi/*/remplissage/` au `.gitignore` : ce dossier de lots ne sert
qu'au mode artefact.

**5 (mode local). Générer la page.**

```bash
python <skill>/scripts/construire_page_locale.py suivi/<code>/remplissage.json --sortie suivi/<code>/index.html
```

Dire à l'utilisateur d'ouvrir `suivi/<code>/index.html` dans son navigateur, puis passer à
l'étape 7. Les coches qu'il fait dans la page restent dans son navigateur ; le bouton
« Exporter » télécharge un `remplissage.json` qu'il remet à la place de celui du projet.

**5 (mode artefact). Publier la page.** Copier `assets/template.html` vers
`/mnt/user-data/outputs/suivi-<code>/index.html` et remplacer seulement le contenu de
`<title>` par `Suivi de module — <Nom>`. Puis publier avec l'outil Artifact :
`action: "publish"`, `file_path` de cette copie, `capabilities: {"db": {}}`, `favicon: "📋"`,
`title: "Suivi de module — <Nom>"`. Sans `capabilities`, la page s'affiche « Hors ligne » et
la base ne peut pas être remplie.

**6 (mode artefact). Remplir la base.** Pour chaque fichier `remplissage/lots/lot_NN.json`, appeler Artifact
avec `action: "write_db"`, `url` de l'artefact publié, `db_op: "batch"` et `writes` = le
contenu du fichier. Chaque écriture pointe vers un `file_path` : ne pas recopier les documents.

**7. Contrôler et rendre compte.** En mode artefact, relire la base (voir « Relire »,
étape 1) dans `<dossier>/lecture-1` puis lancer
`python <skill>/scripts/comparer_lectures.py --resume <dossier>/lecture-1`. En mode local,
lancer le même résumé sur `<dossier>/remplissage` (le dossier produit à l'étape 4).

Répondre en quelques phrases : ce que contient le tableau, les onglets non créés faute de
source, les arbitrages ouverts, les secrets retirés. En mode artefact, rappeler que
l'artefact est privé ; en mode local, que le JSON sera commité avec le projet.

## Relire

**Mode local.** Lire `suivi/<code>/remplissage.json`. Si l'utilisateur a exporté ses
modifications depuis la page, il remplace d'abord ce fichier par l'export. Pour voir ce qui
a changé, comparer avec la version commitée : `git diff suivi/<code>/remplissage.json`, ou
préparer les deux versions avec `preparer_remplissage.py` et les passer à
`comparer_lectures.py`. Puis rendre compte comme à l'étape 3 ci-dessous.

**1 (mode artefact). Lire la base.** Lire d'abord la page (`action: "read"`) pour voir quelles collections
elle charge : chercher les appels `db.collection("…")` et `db.doc("…")` dans le script.
Un tableau plus récent peut en avoir de nouvelles. Puis, pour chaque collection, appeler
Artifact `action: "read_db"`, `db_op: "list"`, `query: {"limit": 1000}`,
`out_dir: /mnt/user-data/outputs/suivi-<code>/lecture-N`. Pour les documents uniques
(`fiche`, `plan`, `cycle`, `merise`, `dev`), lister la collection du même nom.

**2. Comparer.** Si une lecture précédente existe dans le conteneur :

```bash
python <skill>/scripts/comparer_lectures.py <lecture-précédente> <lecture-N>
```

Sinon, utiliser `--resume <lecture-N>` et lire les documents utiles.

**3. Rendre compte.** Ce qui a changé (statuts, nouveaux éléments, notes d'audit), l'état
chiffré, puis ce qui demande de l'attention : travail codé mais non commité, lot avancé
alors qu'un arbitrage le bloque, incohérence entre onglets, secret présent dans les données.
Ne rien modifier pendant une relecture sans que l'utilisateur le demande.

## Mettre à jour

**Mode local.** Modifier `suivi/<code>/remplissage.json`, relancer `preparer_remplissage.py`
pour le vérifier, puis `construire_page_locale.py` pour régénérer la page. Prévenir
l'utilisateur que les coches non exportées de son navigateur seront remplacées par le
contenu du fichier, car la page repart du fichier dès qu'il change.

**Mode artefact.** Lire le document concerné (`read_db`, `db_op: "get"`) pour connaître sa `version`, puis
écrire avec `write_db` (`update` pour quelques champs, `set` pour le document entier) en
passant `if_version`. Si l'écriture échoue parce que quelqu'un a modifié le document entre
temps, relire et refaire la modification. Pour plusieurs documents, utiliser `batch`.
Quand un statut passe à `termine` ou `ok`, renseigner aussi la date (`termineLe`, `testeLe`).

## Partager

En mode local, le tableau se partage avec le dépôt : toute personne qui a accès au code
ouvre `suivi/<code>/index.html`. En mode artefact, l'artefact est privé tant que l'utilisateur ne le partage pas. Partager son lien donne accès
aux mêmes données : c'est le bon choix pour des collègues qui travaillent sur le même module,
pas pour quelqu'un qui veut suivre son propre projet. Celui-ci installe ce skill et demande à
son Claude de créer son propre tableau. Pour le détail des options de partage, renvoyer vers
https://support.claude.com.

## Fichiers du skill

- `assets/template.html` : la page, à publier telle quelle (seul le `<title>` change).
  Sans base claude.ai, elle lit les données embarquées par `construire_page_locale.py`.
- `references/donnees.md` : forme de chaque document de la base, valeurs autorisées.
- `scripts/preparer_remplissage.py` : vérifie le remplissage (statuts, tailles, références
  croisées, secrets) et le découpe en lots de 50 écritures.
- `scripts/comparer_lectures.py` : compare deux lectures de la base ou résume l'état.
- `scripts/construire_page_locale.py` : génère la page du mode local, données embarquées.
