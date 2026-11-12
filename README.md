# suivi-module

**Le tableau de suivi de vos modules, construit par Claude à partir de votre dépôt.**

Installez le skill, puis dites une phrase à Claude :

```
Utilise le skill suivi-module pour créer le tableau de suivi de tous les modules
```

Claude explore le dépôt seul, sans poser de questions, et produit pour chaque module un
tableau de bord : ce qu'il fait, comment le prendre en main, ce qui est livré, ce qui reste à
faire et ce qui attend une décision. Une page d'accueil récapitule l'avancement de tous les
modules.

**Les tableaux sont des artefacts Claude** : privés, interactifs, partageables par lien.
Là où l'outil d'artefacts n'existe pas (Claude Code sans cet outil, autre assistant), le skill
produit à la place des pages HTML dans le projet, avec le même contenu.

## Démarrage rapide

```bash
cd mon-projet
npx suivi-module init
```

Puis, dans votre assistant :

```
Utilise le skill suivi-module pour créer le tableau de suivi de tous les modules
```

`init` détecte l'assistant utilisé dans le projet (Claude Code, Cursor, Copilot, Codex, Gemini
CLI, Windsurf…) et y installe le skill. Seuls Node.js 18+ et Python 3 sont nécessaires.

**Sur claude.ai** : ajoutez [`suivi-module.skill`](./suivi-module.skill) à vos skills
([mode d'emploi](https://support.claude.com/en/articles/12512180-using-skills-in-claude)),
joignez une archive `.zip` de votre dépôt (ou donnez le lien d'un dépôt GitHub public), puis
dites la même phrase. Les tableaux produits localement peuvent aussi être publiés en artefacts :
joignez le dossier `suivi/` et dites « publie mes tableaux de suivi en artefacts ».

## Ce que vous obtenez

| | Artefacts (format principal) | Pages locales (repli) |
|---|---|---|
| Un tableau par module | Artefact « Suivi de module — <Nom> » | `suivi/<module>/index.html` |
| Accueil de tous les modules | Artefact « Suivi des modules — <Projet> » | `suivi/index.html` |
| Données | Base de l'artefact, partagée avec qui reçoit le lien | `suivi/<module>/remplissage.json`, versionné avec le code |
| Saisies (coches, décisions, recette) | Enregistrées pour tous les lecteurs | Gardées dans le navigateur, bouton « Exporter » |

Chaque tableau compte jusqu'à 9 onglets :

| Onglet | Contenu |
|---|---|
| Vue d'ensemble | Définition, but, usage, architecture en couches, liens avec les autres modules |
| Démarrage | Le parcours de prise en main, à cocher |
| Lecture | Les documents de référence mis en forme, à lire dans l'ordre |
| Modèle MERISE | MCD interactif déduit du code, dictionnaire, règles de gestion, écarts |
| Exigences & recette | Couverture des exigences, cas de recette, par périmètre |
| Plan de développement | Lots par phase, carte des dépendances entre modules, cycle de vie |
| Boucle de dev | Les commandes du quotidien, à copier |
| Fonctionnalités | Par palier, avec statut, avancement et preuve |
| Arbitrages & décisions | Questions ouvertes et choix actés |

Un onglet n'apparaît que si le dépôt permet de le remplir : le skill préfère un onglet absent
à un onglet rempli de suppositions.

## Installation

### Avec la commande `suivi-module` (recommandé)

Sans rien installer d'autre, depuis la racine du projet :

```bash
npx suivi-module init                      # assistant détecté dans le projet (Claude Code par défaut)
npx suivi-module init --ai cursor          # un assistant précis
npx suivi-module init --ai claude,copilot  # plusieurs
npx suivi-module init --ai all             # tous les assistants
npx suivi-module init --global             # dans le dossier personnel : tous vos projets
```

Ou en l'installant une fois pour toutes : `npm install -g suivi-module`, puis `suivi-module init`.

| `--ai` | Assistant | Dossier d'installation |
|---|---|---|
| `claude` | Claude Code | `.claude/skills/suivi-module` |
| `cursor` | Cursor | `.cursor/skills/suivi-module` |
| `copilot` | GitHub Copilot | `.github/skills/suivi-module` (global : `~/.copilot/skills`) |
| `codex` | Codex | `.agents/skills/suivi-module` |
| `gemini` | Gemini CLI | `.gemini/skills/suivi-module` |
| `windsurf` | Windsurf | `.windsurf/skills/suivi-module` |
| `universal` | Standard Agent Skills | `.agents/skills/suivi-module` |
| `kiro` | Kiro | `.kiro/steering/suivi-module` |
| `roocode` | Roo Code | `.roo/skills/suivi-module` |
| `opencode`, `continue`, `trae`, `qoder`, `codebuddy`, `droid`, `kilocode`, `warp`, `augment`, `zcode`, `kimi`, `codewhale`, `amazonq`, `antigravity`, `openclaw` | | `npx suivi-module list` |

Autres commandes :

```bash
npx suivi-module update        # met à jour toutes les installations trouvées (projet et dossier personnel)
npx suivi-module uninstall     # retire le skill (assistants détectés, ou --ai …)
npx suivi-module list          # assistants pris en charge et installations présentes
npx suivi-module init --dry-run   # montre ce qui serait fait, sans rien écrire
```

Vos tableaux de suivi ne sont jamais touchés par `update` ni `uninstall`.

### Claude Code, comme plugin

```
/plugin marketplace add dav9fulldev/suivi-module-skill
/plugin install suivi-module@suivi-module
```

### Sans Node.js (Claude Code uniquement)

```bash
curl -fsSL https://raw.githubusercontent.com/dav9fulldev/suivi-module-skill/main/install.sh | bash          # macOS, Linux, WSL
```

```powershell
irm https://raw.githubusercontent.com/dav9fulldev/suivi-module-skill/main/install.ps1 | iex                # Windows
```

### claude.ai

Téléchargez [`suivi-module.skill`](./suivi-module.skill) puis ajoutez-le à vos skills en
suivant [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude).

### Prérequis

Python 3 pour les scripts du skill (bibliothèque standard uniquement : rien n'est installé et
aucun appel réseau n'est fait), git pour l'historique, Node.js 18+ pour la commande `suivi-module`.

### Avec les autres assistants

Le skill est écrit pour Claude, mais suit le format standard des skills (`SKILL.md`). Dans un
assistant sans artefacts, il produit les tableaux en pages HTML dans `suivi/`, avec le même
contenu.

## Utilisation

| Vous dites | Claude fait |
|---|---|
| « Utilise le skill suivi-module pour créer le tableau de suivi du module diligences » | Explore le dépôt et crée `suivi/diligence/` |
| « … de tous les modules » | Crée un tableau par module détecté, plus `suivi/index.html` |
| « … pour mettre à jour le tableau de suivi de tous les modules » | Relit le dépôt et met à jour sans perdre vos saisies |
| « Relis le tableau de suivi du module diligences : qu'est-ce qui a changé ? » | Compare avec la version commitée et résume |
| « Passe la fonctionnalité f03 en terminé » | Modifie le tableau |
| « Publie mes tableaux de suivi en artefacts » (dossier `suivi/` joint) | Publie chaque module et l'accueil en artefacts, sans réexplorer |

Le nom du module peut être celui du code (`diligences`) ou un nom métier (« le module RH ») :
Claude cherche la correspondance dans les documents.

**Vos saisies sont conservées.** Les étapes cochées, les décisions prises, les résultats de
recette et les éléments ajoutés à la main survivent aux mises à jour. Dans un artefact, elles
sont enregistrées directement. Dans une page locale, elles restent dans votre navigateur : le
bouton « Exporter » télécharge un `remplissage.json` à remettre dans `suivi/<module>/`.

## Comment ça marche

1. **Exploration.** Un script dresse l'inventaire du dépôt : pile technique, modules, fichiers
   par couche, documents qui parlent de chaque module, modèle de données, dépendances entre
   modules, historique git, fichiers non commités, tests, TODO.
2. **Lecture ciblée.** Claude lit les documents du projet (CLAUDE.md, spécifications,
   décisions, aide) puis vérifie dans le code ce qu'ils décrivent.
3. **Preuves.** Chaque statut cite sa preuve (fichier, fonction, test, commit). Du code
   modifié mais non commité reste « à vérifier ». En cas de doute, le statut le moins avancé
   l'emporte.
4. **Compte rendu.** Ce qui a été créé, ce qui demande votre attention (travail non commité,
   arbitrages ouverts, secrets trouvés) et une courte liste « À confirmer ». Aucune question
   n'est posée en cours de route.

## Technologies

| | Reconnu automatiquement |
|---|---|
| Modèle de données | Prisma, SQL et migrations SQL, Django, SQLAlchemy, TypeORM, JPA/Hibernate, Entity Framework Core, Rails, Laravel, Mongoose, Drizzle |
| Structure des modules | Next.js, React, Vue, Angular, Svelte, NestJS, Express, Django, Flask, FastAPI, Rails, Laravel, Symfony, Spring Boot, ASP.NET Core, Go, architecture par couches |
| Dépendances entre modules | Imports JS/TS, Python, Java/Kotlin, PHP ; relations entre entités pour toutes les piles |
| Commandes de la boucle de dev | `package.json`, `Makefile`, `composer.json`, Docker Compose, conventions des frameworks |

Pour une technologie absente du tableau (GORM, Sequelize, Doctrine, Ecto…), Claude lit
lui-même les fichiers de modèle et les écrit dans un format neutre, d'où le même modèle MERISE
est généré. Les commandes déduites des conventions d'un framework sont signalées « à
confirmer ».

## Mettre à jour le skill

```bash
npx suivi-module@latest update
```

Installé comme plugin : mettez à jour le marketplace `suivi-module` depuis le menu `/plugin`.
Installé avec `curl` ou PowerShell : relancez la même commande. Vos tableaux (`suivi/` ou
artefacts) ne sont pas touchés par une mise à jour du skill.

## Confidentialité

Avant tout remplissage, un script bloque ce qui ressemble à un secret : mot de passe, clé
d'API, clé privée, adresse IP interne, identifiants dans une URL, chemin personnel. Le JSON
est commité avec le code et un artefact claude.ai est lisible par qui le reçoit : ces données
ne doivent jamais contenir de secrets. Si votre dépôt lui-même en contient, le compte rendu
vous le signale.

## Dépannage

| Symptôme | Solution |
|---|---|
| `npx: command not found` | Installer Node.js 18+ depuis https://nodejs.org, ou utiliser l'installation sans Node.js |
| `npm ERR! 404` sur `npx suivi-module` | Le paquet n'est pas encore sur npm : utiliser `npx github:dav9fulldev/suivi-module-skill init` |
| `python: command not found` | Installer Python 3 ; sur macOS, accepter l'installation des outils de ligne de commande proposée au premier `git` ou `python3` |
| Un module attendu n'est pas détecté | Le nommer explicitement : « crée le tableau de suivi du module X ». Claude complète par sa propre lecture de l'arborescence |
| Le modèle MERISE est vide ou incomplet | Demander : « complète le modèle MERISE du module X à partir des fichiers de modèle ». Claude passe par le format neutre |
| Mes coches ont disparu après une mise à jour | Elles étaient restées dans le navigateur : cliquer d'abord « Exporter », remplacer `suivi/<module>/remplissage.json`, puis relancer la mise à jour |
| Sur claude.ai, la page affiche « Hors ligne » | Demander à Claude de republier l'artefact avec la capacité `db` |
| `install.ps1` échoue | Utiliser `npx suivi-module init`, qui fonctionne sur tous les systèmes |

## Contenu du dépôt

```
bin/suivi-module.js                  la commande suivi-module (init, update, uninstall, list)
package.json                         paquet npm « suivi-module »
.claude-plugin/marketplace.json      déclaration du plugin pour Claude Code
skills/suivi-module/
  SKILL.md                           instructions suivies par Claude
  assets/template.html               la page d'un tableau (aucune donnée)
  references/exploration.md          comment déduire chaque onglet du dépôt, règles de preuve
  references/donnees.md              forme des données de chaque onglet
  scripts/explorer_projet.py         inventaire : pile, modules, couches, documents, entités, dépendances, git
  scripts/modeles_donnees.py         lecture du modèle de données de 11 technologies, format neutre
  scripts/modele_vers_mcd.py         modèle MERISE déduit du modèle de données
  scripts/preparer_remplissage.py    vérification (statuts, références, secrets) et lots
  scripts/construire_page_locale.py  page d'un module, données embarquées
  scripts/construire_index.py        page d'accueil de tous les modules (liens locaux ou artefacts)
  scripts/lecture_vers_remplissage.py   base d'un artefact → remplissage.json (mises à jour)
  scripts/fusionner_remplissage.py   mise à jour sans perte des saisies
  scripts/comparer_lectures.py       ce qui a changé entre deux lectures
suivi-module.skill                   archive pour claude.ai
install.sh, install.ps1              installation en une commande
```

## Versions

| Version | Nouveautés |
|---|---|
| 1.4.0 | Commande `npx suivi-module init` : installation en une commande dans Claude Code et 23 autres assistants (Cursor, Copilot, Codex, Gemini CLI, Windsurf…), détection de l'assistant du projet, `update`, `uninstall`, `list`, `--global`, `--dry-run` |
| 1.3.0 | Artefacts comme format principal : un artefact par module et un artefact d'accueil, mise à jour des artefacts sans perte des saisies, publication en artefacts de tableaux produits localement, dépôt joint en archive ou cloné depuis GitHub sur claude.ai |
| 1.2.0 | Toutes technologies : modèle de données de 11 piles, détection des modules selon les conventions de chaque framework, dépendances par les imports et les relations entre entités, commandes de la boucle de dev selon la pile |
| 1.1.0 | Exploration automatique du dépôt sans question, mode « tous les modules » et page d'accueil, statuts justifiés par des preuves, détection du travail non commité, mise à jour sans perte des saisies |
| 1.0.0 | Tableau de suivi à 9 onglets, en artefact claude.ai ou en page locale, vérification des secrets |

## Auteur et licence

Créé par Brou David Yao ([@dav9fulldev](https://github.com/dav9fulldev)). Licence MIT, voir
[LICENSE](./LICENSE). Les suggestions et corrections sont bienvenues dans les issues du dépôt.
