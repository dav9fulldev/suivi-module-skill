#!/usr/bin/env node
// suivi-module — installe le skill de tableau de suivi de module dans les assistants IA de code.
// Aucune dépendance : Node.js 18 ou plus suffit.

import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, rmdirSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, relative, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ICI = dirname(fileURLToPath(import.meta.url));
const RACINE_PAQUET = resolve(ICI, "..");
const SOURCE = join(RACINE_PAQUET, "skills", "suivi-module");
const VERSION = JSON.parse(readFileSync(join(RACINE_PAQUET, "package.json"), "utf8")).version;
const NOM = "suivi-module";
const MARQUE = ".suivi-module-version";

// Dossier d'installation de chaque assistant : <racine>/<dossier>/suivi-module.
// `globale` remplace la racine pour une installation dans le dossier personnel.
const ASSISTANTS = {
  claude:      { nom: "Claude Code",                racine: ".claude",    dossier: "skills",   detecte: [".claude", ".claude-plugin", "CLAUDE.md"] },
  cursor:      { nom: "Cursor",                     racine: ".cursor",    dossier: "skills",   detecte: [".cursor", ".cursorrules"] },
  windsurf:    { nom: "Windsurf",                   racine: ".windsurf",  dossier: "skills",   detecte: [".windsurf", ".windsurfrules"] },
  copilot:     { nom: "GitHub Copilot",             racine: ".github",    dossier: "skills",   globale: ".copilot",
                 detecte: [".github/copilot-instructions.md", ".github/instructions", ".github/prompts", ".github/agents", ".github/skills"] },
  codex:       { nom: "Codex",                      racine: ".agents",    dossier: "skills",   detecte: [".codex", "AGENTS.md"] },
  gemini:      { nom: "Gemini CLI",                 racine: ".gemini",    dossier: "skills",   detecte: [".gemini", "GEMINI.md"] },
  universal:   { nom: "Standard Agent Skills",      racine: ".agents",    dossier: "skills",   detecte: [".agents"] },
  antigravity: { nom: "Antigravity",                racine: ".agents",    dossier: "skills",   detecte: [".agent"] },
  kiro:        { nom: "Kiro",                       racine: ".kiro",      dossier: "steering", detecte: [".kiro"] },
  roocode:     { nom: "Roo Code",                   racine: ".roo",       dossier: "skills",   detecte: [".roo"] },
  opencode:    { nom: "OpenCode",                   racine: ".opencode",  dossier: "skills",   detecte: [".opencode"] },
  continue:    { nom: "Continue",                   racine: ".continue",  dossier: "skills",   detecte: [".continue"] },
  trae:        { nom: "Trae",                       racine: ".trae",      dossier: "skills",   detecte: [".trae"] },
  qoder:       { nom: "Qoder",                      racine: ".qoder",     dossier: "skills",   detecte: [".qoder"] },
  codebuddy:   { nom: "CodeBuddy",                  racine: ".codebuddy", dossier: "skills",   detecte: [".codebuddy"] },
  droid:       { nom: "Droid (Factory)",            racine: ".factory",   dossier: "skills",   detecte: [".factory"] },
  kilocode:    { nom: "KiloCode",                   racine: ".kilocode",  dossier: "skills",   detecte: [".kilocode"] },
  warp:        { nom: "Warp",                       racine: ".warp",      dossier: "skills",   detecte: [".warp"] },
  augment:     { nom: "Augment",                    racine: ".augment",   dossier: "skills",   detecte: [".augment"] },
  zcode:       { nom: "ZCode",                      racine: ".zcode",     dossier: "skills",   detecte: [".zcode"] },
  kimi:        { nom: "Kimi Code",                  racine: ".kimi-code", dossier: "skills",   detecte: [".kimi-code"] },
  codewhale:   { nom: "CodeWhale",                  racine: ".codewhale", dossier: "skills",   detecte: [".codewhale"] },
  amazonq:     { nom: "Amazon Q Developer",         racine: ".amazonq",   dossier: "rules",    detecte: [".amazonq"] },
  openclaw:    { nom: "OpenClaw",                   racine: ".agents",    dossier: "skills",   detecte: [] },
};

const AIDE = `suivi-module ${VERSION} — tableau de suivi de module pour les assistants IA de code

Usage :
  npx suivi-module init                 installe pour l'assistant détecté dans le projet (Claude Code par défaut)
  npx suivi-module init --ai cursor     installe pour un assistant précis (plusieurs : --ai claude,cursor)
  npx suivi-module init --ai all        installe pour tous les assistants
  npx suivi-module init --global        installe dans le dossier personnel (tous vos projets)
  npx suivi-module update               met à jour toutes les installations trouvées
  npx suivi-module uninstall            retire le skill (assistants détectés, ou --ai …)
  npx suivi-module list                 assistants pris en charge et installations présentes

Options :
  --ai <id[,id…]|all>   assistants visés (voir « list »)
  --global              dossier personnel au lieu du projet courant
  --dry-run             affiche ce qui serait fait, sans rien écrire
  --version, --help

Ensuite, dans votre assistant :
  « Utilise le skill suivi-module pour créer le tableau de suivi de tous les modules »`;

function lireArgs(argv) {
  const out = { commande: null, ai: null, global: false, dryRun: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--ai") out.ai = argv[++i];
    else if (a.startsWith("--ai=")) out.ai = a.slice(5);
    else if (a === "--global" || a === "-g") out.global = true;
    else if (a === "--dry-run") out.dryRun = true;
    else if (a === "--version" || a === "-v") out.commande = "version";
    else if (a === "--help" || a === "-h") out.commande = "aide";
    else if (!a.startsWith("-") && !out.commande) out.commande = a;
    else throw new Error(`Option inconnue : ${a}`);
  }
  return out;
}

function base(global) {
  return global ? homedir() : process.cwd();
}

function cible(id, global) {
  const a = ASSISTANTS[id];
  const racine = global && a.globale ? a.globale : a.racine;
  return join(base(global), racine, a.dossier, NOM);
}

function choisir(ai, global, pourRetrait = false) {
  if (ai) {
    const ids = ai === "all" ? Object.keys(ASSISTANTS) : ai.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean);
    const inconnus = ids.filter((id) => !ASSISTANTS[id]);
    if (inconnus.length) throw new Error(`Assistant inconnu : ${inconnus.join(", ")}. Voir « npx suivi-module list ».`);
    return ids;
  }
  if (pourRetrait) return Object.keys(ASSISTANTS).filter((id) => existsSync(join(cible(id, global), "SKILL.md")));
  if (global) return ["claude"];
  const vus = Object.keys(ASSISTANTS).filter((id) => ASSISTANTS[id].detecte.some((m) => existsSync(join(process.cwd(), m))));
  return vus.length ? vus : ["claude"];
}

// Plusieurs assistants partagent un dossier (.agents/skills) : n'écrire qu'une fois.
function grouper(ids, global) {
  const parChemin = new Map();
  for (const id of ids) {
    const c = cible(id, global);
    if (!parChemin.has(c)) parChemin.set(c, []);
    parChemin.get(c).push(ASSISTANTS[id].nom);
  }
  return parChemin;
}

function copier(chemin, dryRun) {
  if (dryRun) return;
  if (existsSync(chemin)) rmSync(chemin, { recursive: true, force: true });
  mkdirSync(dirname(chemin), { recursive: true });
  cpSync(SOURCE, chemin, {
    recursive: true,
    filter: (src) => !src.includes("__pycache__") && !src.endsWith(".pyc") && !src.endsWith(".DS_Store"),
  });
  writeFileSync(join(chemin, MARQUE), VERSION + "\n");
}

// Après un retrait : supprimer les dossiers parents devenus vides (skills/, puis .cursor/…),
// sans jamais remonter au-delà du projet ou du dossier personnel, ni toucher un dossier non vide.
function nettoyerParents(chemin, global) {
  const limite = base(global);
  let d = dirname(chemin);
  for (let i = 0; i < 2 && d !== limite && d.startsWith(limite); i++) {
    try {
      if (readdirSync(d).length) break;
      rmdirSync(d);
    } catch { break; }
    d = dirname(d);
  }
}

function versionInstallee(chemin) {
  try { return readFileSync(join(chemin, MARQUE), "utf8").trim(); } catch { return null; }
}

function affiche(chemin) {
  const r = relative(process.cwd(), chemin);
  return r && !r.startsWith("..") ? r : chemin.replace(homedir(), "~");
}

function verifierPython() {
  for (const exe of ["python3", "python", "py"]) {
    const r = spawnSync(exe, ["--version"], { encoding: "utf8" });
    if (r.status === 0 && /Python 3/.test((r.stdout || "") + (r.stderr || ""))) return true;
  }
  console.log("\n⚠️  Python 3 est introuvable. Le skill en a besoin pour ses scripts (bibliothèque standard uniquement).");
  console.log("   Installez-le depuis https://www.python.org/downloads/ ou avec votre gestionnaire de paquets.");
  return false;
}

function init(o) {
  if (!existsSync(join(SOURCE, "SKILL.md"))) throw new Error(`Fichiers du skill introuvables dans ${SOURCE}.`);
  const ids = choisir(o.ai, o.global);
  const detecte = !o.ai && !o.global;
  const rienDetecte = detecte && !Object.values(ASSISTANTS).some((a) => a.detecte.some((m) => existsSync(join(process.cwd(), m))));
  console.log(`suivi-module ${VERSION}${o.dryRun ? " — simulation, rien n'est écrit" : ""}`);
  if (detecte) console.log(`Assistant${ids.length > 1 ? "s" : ""} ${ids.length === 1 && ids[0] === "claude" ? "retenu" : "détecté" + (ids.length > 1 ? "s" : "")} : ${ids.map((i) => ASSISTANTS[i].nom).join(", ")}`);
  for (const [chemin, noms] of grouper(ids, o.global)) {
    const avant = versionInstallee(chemin);
    copier(chemin, o.dryRun);
    let etat = avant ? (avant === VERSION ? "réinstallé" : `mis à jour (${avant} → ${VERSION})`) : "installé";
    if (o.dryRun) etat = avant ? `serait ${etat}` : "serait installé";
    console.log(`  ✓ ${noms.join(", ")} : ${etat} dans ${affiche(chemin)}`);
  }
  verifierPython();
  console.log(`\nDans votre assistant, dites par exemple :
  « Utilise le skill suivi-module pour créer le tableau de suivi de tous les modules »
  « Utilise le skill suivi-module pour créer le tableau de suivi du module <nom> »`);
  if (rienDetecte) {
    console.log(`\nAucun assistant détecté dans ce dossier : installé pour Claude Code.
Pour un autre assistant : npx suivi-module init --ai cursor (voir « npx suivi-module list »).`);
  }
}

function trouverInstallations() {
  const out = [];
  for (const global of [false, true]) {
    for (const [chemin, noms] of grouper(Object.keys(ASSISTANTS), global)) {
      if (existsSync(join(chemin, "SKILL.md"))) out.push({ chemin, noms, global });
    }
  }
  return out;
}

function update(o) {
  const trouvees = trouverInstallations().filter((x) => !o.global || x.global);
  if (!trouvees.length) {
    console.log("Aucune installation trouvée ici ni dans le dossier personnel. Lancez : npx suivi-module init");
    return;
  }
  console.log(`suivi-module ${VERSION}${o.dryRun ? " — simulation" : ""}`);
  for (const { chemin, noms } of trouvees) {
    const avant = versionInstallee(chemin) || "inconnue";
    copier(chemin, o.dryRun);
    console.log(`  ✓ ${noms.join(", ")} : ${avant === VERSION ? "déjà à jour, réinstallé" : `${avant} → ${VERSION}`} (${affiche(chemin)})${o.dryRun ? " — simulation" : ""}`);
  }
  console.log("\nVos tableaux de suivi (dossier suivi/ ou artefacts) ne sont pas modifiés.");
}

function uninstall(o) {
  const ids = choisir(o.ai, o.global, true);
  const chemins = [...grouper(ids, o.global)].filter(([c]) => existsSync(join(c, "SKILL.md")));
  if (!chemins.length) {
    console.log(`Aucune installation à retirer ${o.global ? "dans le dossier personnel" : "dans ce projet"}.${o.global ? "" : " Pour le dossier personnel : --global"}`);
    return;
  }
  for (const [chemin, noms] of chemins) {
    if (!o.dryRun) {
      rmSync(chemin, { recursive: true, force: true });
      nettoyerParents(chemin, o.global);
    }
    console.log(`  ✓ ${noms.join(", ")} : retiré de ${affiche(chemin)}${o.dryRun ? " (simulation)" : ""}`);
  }
  console.log("Vos tableaux de suivi (dossier suivi/ ou artefacts) sont conservés.");
}

function list() {
  console.log(`Assistants pris en charge (--ai <id>) :\n`);
  const installes = new Set(trouverInstallations().map((x) => x.chemin));
  for (const [id, a] of Object.entries(ASSISTANTS)) {
    const local = cible(id, false), glob = cible(id, true);
    const etat = [installes.has(local) ? "installé ici" : null, installes.has(glob) ? "installé globalement" : null].filter(Boolean).join(", ");
    console.log(`  ${id.padEnd(12)} ${a.nom.padEnd(24)} ${join(a.racine, a.dossier, NOM).padEnd(30)}${etat ? "  ← " + etat : ""}`);
  }
}

function main() {
  let o;
  try { o = lireArgs(process.argv.slice(2)); } catch (e) { console.error(e.message + "\n\n" + AIDE); process.exit(2); }
  try {
    switch (o.commande) {
      case "init": case "install": init(o); break;
      case "update": case "upgrade": update(o); break;
      case "uninstall": case "remove": uninstall(o); break;
      case "list": case "ls": list(); break;
      case "version": console.log(VERSION); break;
      case null: case "aide": case "help": console.log(AIDE); break;
      default: console.error(`Commande inconnue : ${o.commande}\n\n${AIDE}`); process.exit(2);
    }
  } catch (e) {
    console.error(`Erreur : ${e.message}`);
    process.exit(1);
  }
}

main();
