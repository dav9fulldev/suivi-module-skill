# suivi-module — un tableau de suivi de module pour Claude

Un skill qui fabrique et tient à jour le **tableau de suivi** d'un module, ou de tous les
modules d'un projet logiciel, en explorant le dépôt lui-même : le développeur n'a qu'une
phrase à dire.

Le tableau compte 9 onglets :

| Onglet | Contenu |
|---|---|
| Vue d'ensemble | Définition, but, usage, architecture en couches, liens avec les autres modules |
| Démarrage | Le parcours de prise en main, à cocher |
| Lecture | Les documents de référence mis en forme, à lire dans l'ordre |
| Modèle MERISE | MCD interactif, dictionnaire, règles de gestion, écarts avec l'existant |
| Exigences & recette | Couverture des exigences, cas de recette à exécuter, par périmètre |
| Plan de développement | Lots par phase, carte des dépendances, cycle de vie |
| Boucle de dev | Les commandes du quotidien, à copier |
| Fonctionnalités | Par palier, avec statut et avancement |
| Arbitrages & décisions | Questions ouvertes et choix actés |

Un onglet n'apparaît que si les documents du projet permettent de le remplir : le skill
préfère un onglet absent à un onglet rempli de suppositions.

## Installation

### Claude Code : comme plugin (recommandé)

Dans Claude Code :

```
/plugin marketplace add dav9fulldev/suivi-module-skill
/plugin install suivi-module@suivi-module
```

### Claude Code : dans un seul projet, en une commande

Depuis la racine du projet, le skill est copié dans `.claude/skills/suivi-module`.

Linux, macOS, WSL :

```bash
curl -fsSL https://raw.githubusercontent.com/dav9fulldev/suivi-module-skill/main/install.sh | bash
```

Windows PowerShell :

```powershell
irm https://raw.githubusercontent.com/dav9fulldev/suivi-module-skill/main/install.ps1 | iex
```

Pour l'installer pour tous vos projets plutôt que pour un seul : ajouter `-s -- --global`
après `bash` (Linux, macOS), ou lancer `$env:SUIVI_MODULE_GLOBAL = "1"` avant la commande
PowerShell.

### claude.ai

Télécharger [`suivi-module.skill`](./suivi-module.skill) puis l'ajouter à vos skills en
suivant [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude).

## Utilisation

Une phrase suffit, depuis la racine du projet dans Claude Code :

```
Utilise le skill suivi-module pour créer le tableau de suivi du module diligences
Utilise le skill suivi-module pour créer le tableau de suivi de tous les modules
```

Claude explore alors le dépôt lui-même, sans poser de questions : pile technique, modules,
écrans, fichiers serveur, aide, documents qui en parlent, modèle de données, dépendances entre
modules, historique git, travail non commité. Il produit :

- `suivi/<module>/index.html` : le tableau du module, à ouvrir dans le navigateur ;
- `suivi/<module>/remplissage.json` : ses données, versionnées avec le code ;
- `suivi/index.html` : la page d'accueil qui récapitule tous les modules.

Chaque statut est justifié par une preuve (fichier, test, commit) ; ce qui reste incertain
est listé « à confirmer » dans le compte rendu. Le modèle MERISE est déduit du modèle de
données et la carte des dépendances des imports et des relations entre entités.

## Technologies

Le skill s'adapte à la pile du projet :

| | Reconnu automatiquement |
|---|---|
| Modèle de données | Prisma, SQL et migrations SQL, Django, SQLAlchemy, TypeORM, JPA/Hibernate, Entity Framework Core, Rails, Laravel, Mongoose, Drizzle |
| Structure des modules | Next.js, React, Vue, Angular, Svelte, NestJS, Express, Django, Flask, FastAPI, Rails, Laravel, Symfony, Spring Boot, ASP.NET Core, Go, architecture par couches |
| Dépendances entre modules | Imports JS/TS, Python, Java/Kotlin, PHP ; relations entre entités pour toutes les piles |
| Commandes de la boucle de dev | `package.json`, `Makefile`, `composer.json`, Docker Compose, et conventions des frameworks ci-dessus |

Pour une technologie absente du tableau (GORM, Sequelize, Doctrine, Ecto…), Claude lit
lui-même les fichiers de modèle et les écrit dans un format neutre, d'où le même modèle MERISE
est généré.

Ensuite :

```
Utilise le skill suivi-module pour mettre à jour le tableau de suivi de tous les modules
Relis le tableau de suivi du module diligences : qu'est-ce qui a changé ?
```

La mise à jour garde ce que l'équipe a saisi : étapes cochées, décisions prises, résultats de
recette, éléments ajoutés à la main. Les coches faites dans la page restent dans le
navigateur ; le bouton « Exporter » télécharge un `remplissage.json` à remettre dans le projet.

Sur claude.ai, le même skill crée des artefacts privés à partir des fichiers joints.

Prérequis : Python 3 (scripts sans dépendance externe), et git pour l'historique.

## Confidentialité

Avant tout remplissage, `preparer_remplissage.py` bloque ce qui ressemble à un secret :
mot de passe, clé d'API, clé privée, adresse IP interne, identifiants dans une URL, chemin
personnel. Le JSON du mode local est commité avec le code, et la base d'un artefact est
lisible par toute personne avec qui il est partagé : ces données ne doivent jamais contenir
de secrets.

## Contenu

```
.claude-plugin/marketplace.json   déclaration du plugin pour Claude Code
skills/suivi-module/
  SKILL.md                        instructions suivies par Claude
  assets/template.html            la page du tableau (aucune donnée)
  references/donnees.md           forme des données de chaque onglet
  references/exploration.md       comment déduire chaque onglet du dépôt, règles de preuve
  scripts/explorer_projet.py      inventaire du dépôt : pile, modules, couches, documents, entités, dépendances, git
  scripts/modeles_donnees.py      lecture du modèle de données de 11 technologies, format neutre
  scripts/modele_vers_mcd.py      modèle MERISE déduit du modèle de données
  scripts/preparer_remplissage.py vérification (statuts, références, secrets) et lots
  scripts/construire_page_locale.py  page d'un module, données embarquées
  scripts/construire_index.py     page d'accueil de tous les modules
  scripts/fusionner_remplissage.py   mise à jour sans perte des saisies
  scripts/comparer_lectures.py    ce qui a changé entre deux lectures
suivi-module.skill                archive pour claude.ai
install.sh, install.ps1           installation en une commande
```

## Licence

MIT, voir [LICENSE](./LICENSE).
