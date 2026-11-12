# suivi-module — un tableau de suivi de module pour Claude

Un skill qui fabrique et tient à jour le **tableau de suivi** d'un module ou d'un projet
logiciel, à partir des documents du projet (CLAUDE.md, spécifications, cahier d'exigences,
journal des décisions).

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

Il suffit de le demander, en joignant ou en désignant les documents du module :

- « Crée le tableau de suivi du module Congés à partir de CLAUDE.md et de docs/SPEC-CONG-01.md »
- « Relis mon tableau de suivi et dis-moi ce qui a changé »
- « Passe le lot L3 en terminé et ajoute l'arbitrage sur la durée de réouverture »

Le skill choisit son mode selon l'endroit où il tourne :

- **Dans Claude Code (mode local)** : il écrit `suivi/<code>/remplissage.json` et génère
  `suivi/<code>/index.html`, à ouvrir dans un navigateur. Le JSON est versionné avec le code.
  Les coches faites dans la page restent dans le navigateur ; le bouton « Exporter » télécharge
  un `remplissage.json` à remettre dans le projet.
- **Sur claude.ai (mode artefact)** : il publie un artefact privé et range les données dans sa
  base. Rien n'est visible des autres tant que vous ne le partagez pas.

Prérequis du mode local : Python 3 (scripts sans dépendance externe).

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
  scripts/preparer_remplissage.py vérification (statuts, références, secrets) et lots
  scripts/construire_page_locale.py  page locale avec données embarquées
  scripts/comparer_lectures.py    ce qui a changé entre deux lectures
suivi-module.skill                archive pour claude.ai
install.sh, install.ps1           installation en une commande
```

## Licence

MIT, voir [LICENSE](./LICENSE).
