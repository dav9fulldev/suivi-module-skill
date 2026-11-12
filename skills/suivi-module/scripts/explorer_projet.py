#!/usr/bin/env python3
"""Explore un dépôt et produit l'inventaire dont le skill a besoin, sans rien demander au
développeur : modules détectés, fichiers par couche, documents qui en parlent, modèles
Prisma, dépendances entre modules (d'après les imports), historique git, travail non
commité, tests, TODO, commandes du projet.

Usage :
  python explorer_projet.py [racine] [--module NOM] [--sortie inventaire.json] [--min-signaux 2]

Sans --module : tous les modules détectés. Avec --module : ce module seul (recherche souple
sur le nom) ; s'il est introuvable, la liste des modules détectés est affichée (code 3).
Python 3 standard uniquement.
"""
import argparse, json, os, re, subprocess, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modeles_donnees import lire_modeles  # noqa: E402

IGNORES = {"node_modules", ".git", ".next", "dist", "build", "out", "coverage", "vendor", ".venv",
           "venv", "__pycache__", ".turbo", ".cache", "suivi", ".idea", ".vscode", "public", "tmp"}
CODE = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".java", ".kt", ".cs", ".php", ".rb", ".vue", ".svelte")
GENERIQUES = {"index", "page", "layout", "route", "routes", "util", "utils", "type", "types", "api", "ui", "lib",
              "component", "components", "app", "server", "hook", "hooks", "style", "styles", "common", "shared",
              "test", "tests", "spec", "config", "constant", "constants", "helper", "helpers", "main", "m", "module",
              "modules", "src", "loading", "error", "not", "global", "globals", "middleware", "provider", "providers",
              "client", "action", "actions", "service", "services", "model", "models", "schema", "schemas", "store",
              "context", "new", "edit", "id", "slug", "default", "template", "base", "core", "data", "db", "prisma",
              "help", "content", "doc", "docs", "asset", "assets", "script", "scripts", "public", "feature", "features",
              "e2e", "mock", "mocks", "controller", "repository", "repositories", "entity", "entities", "dto", "dtos",
              "handler", "handlers", "router", "routers", "view", "views", "usecase", "usecases", "domain", "infra",
              "infrastructure", "application", "presentation", "migrations", "urls", "apps", "admin", "serializers",
              "serializer", "forms", "tasks", "signals", "java", "kotlin", "main",
              "resources", "rb", "php", "http", "requests", "policies", "jobs", "mail", "mailers", "concerns", "helpers", "fixture", "fixtures", "seed", "migration", "migrations", "readme", "claude",
              "agents", "changelog", "license", "package", "dockerfile", "next", "env", "the", "and", "for", "with"}
SOCLE = {"tenant", "auth", "rbac", "db", "prisma", "audit", "mail", "ai", "notification", "notifications",
         "historique", "permission", "permissions", "session", "logger", "log", "cache", "env", "fichier", "fichiers"}
MAX_FICHIERS = 80
COUCHES = {"controller", "controllers", "service", "services", "repository", "repositories", "entity", "entities",
           "model", "models", "dto", "dtos", "handler", "handlers", "router", "routers", "view", "views",
           "usecase", "usecases", "domain", "api", "web", "rest", "graphql", "resolvers", "infrastructure", "adapter", "adapters"}


def git(args, cwd):
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=30)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def norm(n):
    n = re.sub(r"\.[a-z0-9]+$", "", n.lower())
    return re.sub(r"[^a-z0-9]+", "-", n).strip("-")


def jetons(n):
    """Jetons d'un nom de fichier ou de dossier : kebab, snake et camelCase."""
    n = re.sub(r"\.[A-Za-z0-9]+$", "", n)
    n = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", n)
    return [t for t in re.split(r"[^a-z0-9]+", n.lower()) if t]


def racine_mot(t):
    if len(t) > 4 and t.endswith("ies"):
        return t[:-3] + "y"
    if len(t) > 3 and t[-1] in "sx" and not t.endswith("ss"):
        return t[:-1]
    return t


def souche(n):
    js = [t for t in jetons(n) if t not in GENERIQUES and not t.isdigit()]
    return racine_mot(js[0]) if js else ""


def lister(racine):
    for d, sous, fichiers in os.walk(racine):
        sous[:] = [s for s in sous if s not in IGNORES and not (s.startswith(".") and s not in {".claude-plugin"})]
        for f in fichiers:
            yield os.path.relpath(os.path.join(d, f), racine).replace(os.sep, "/")


def lire(chemin, limite=None):
    try:
        with open(chemin, encoding="utf-8", errors="replace") as fh:
            return fh.read(limite) if limite else fh.read()
    except Exception:
        return ""


def titre_md(texte, defaut):
    m = re.search(r"^#\s+(.+)$", texte, re.M)
    return m.group(1).strip() if m else defaut


# --------------------------------------------------------------------------- imports
RE_IMPORT = re.compile(r"""import\s+(?:type\s+)?(?:\{([^}]*)\}|(\w+)(?:\s*,\s*\{([^}]*)\})?|\*\s+as\s+(\w+))\s+from\s+['"]([^'"]+)['"]""")


def resoudre(source, cible, existants, alias):
    if cible.startswith("."):
        base = os.path.normpath(os.path.join(os.path.dirname(source), cible)).replace(os.sep, "/")
    else:
        base = None
        for prefixe, dossier in alias:
            if cible.startswith(prefixe):
                base = (dossier + cible[len(prefixe):]).lstrip("/")
                break
        if base is None:
            return None
    for suffixe in ("", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.tsx", "/index.js"):
        if base + suffixe in existants:
            return base + suffixe
    return None


def lire_alias(racine):
    alias = []
    for cfg in ("tsconfig.json", "jsconfig.json"):
        t = lire(os.path.join(racine, cfg))
        t = re.sub(r"//.*", "", t)
        for m in re.finditer(r'"([^"]+)/\*"\s*:\s*\[\s*"([^"]*)/\*"', t):
            alias.append((m.group(1) + "/", m.group(2).lstrip("./") + "/"))
    if not alias:
        alias = [("@/", "src/" if os.path.isdir(os.path.join(racine, "src")) else "")]
    return alias


# --------------------------------------------------------------------------- pile technique
def detecter_pile(racine, fichiers, pkg):
    noms = {f.split("/")[-1] for f in fichiers}
    racine_f = set(fichiers)
    deps = json.dumps({**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}).lower()
    py = " ".join(lire(os.path.join(racine, f)).lower() for f in fichiers
                  if f.split("/")[-1] in ("requirements.txt", "pyproject.toml", "Pipfile", "setup.cfg") or re.match(r"requirements[^/]*\.txt$", f))
    gem = lire(os.path.join(racine, "Gemfile")).lower()
    composer = lire(os.path.join(racine, "composer.json")).lower()
    jvm = " ".join(lire(os.path.join(racine, f)).lower() for f in fichiers if f.split("/")[-1] in ("pom.xml", "build.gradle", "build.gradle.kts"))
    dotnet = " ".join(lire(os.path.join(racine, f)).lower() for f in fichiers if f.endswith(".csproj"))
    gomod = lire(os.path.join(racine, "go.mod")).lower()
    fw = []
    for cle, nom in (('"next"', "Next.js"), ('"react"', "React"), ('"vue"', "Vue"), ('"nuxt"', "Nuxt"), ('"@angular/core"', "Angular"),
                     ('"@sveltejs/kit"', "SvelteKit"), ('"svelte"', "Svelte"), ('"@nestjs/core"', "NestJS"), ('"express"', "Express"),
                     ('"fastify"', "Fastify"), ('"@remix-run', "Remix"), ('"prisma"', "Prisma"), ('"typeorm"', "TypeORM"),
                     ('"mongoose"', "Mongoose"), ('"drizzle-orm"', "Drizzle"), ('"sequelize"', "Sequelize")):
        if cle in deps:
            fw.append(nom)
    for cle, nom in (("django", "Django"), ("flask", "Flask"), ("fastapi", "FastAPI"), ("sqlalchemy", "SQLAlchemy")):
        if cle in py:
            fw.append(nom)
    if "manage.py" in noms and "Django" not in fw:
        fw.append("Django")
    if "rails" in gem:
        fw.append("Rails")
    if "laravel/framework" in composer:
        fw.append("Laravel")
    if "symfony/" in composer:
        fw.append("Symfony")
    if "spring-boot" in jvm:
        fw.append("Spring Boot")
    if "microsoft.aspnetcore" in dotnet or "microsoft.net.sdk.web" in dotnet:
        fw.append("ASP.NET Core")
    if "entityframeworkcore" in dotnet:
        fw.append("Entity Framework Core")
    for cle, nom in (("gin-gonic", "Gin"), ("labstack/echo", "Echo"), ("gofiber", "Fiber"), ("gorm.io", "GORM")):
        if cle in gomod:
            fw.append(nom)
    langages = Counter()
    ext = {".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript", ".jsx": "JavaScript", ".py": "Python", ".rb": "Ruby",
           ".php": "PHP", ".java": "Java", ".kt": "Kotlin", ".cs": "C#", ".go": "Go", ".vue": "Vue", ".svelte": "Svelte"}
    for f in fichiers:
        e = os.path.splitext(f)[1]
        if e in ext:
            langages[ext[e]] += 1

    cmd = []
    gest = "pnpm" if "pnpm-lock.yaml" in noms else "yarn" if "yarn.lock" in noms else "bun" if "bun.lockb" in noms else "npm"
    for k in pkg.get("scripts", {}):
        cmd.append({"cmd": f"{gest} run {k}" if gest != "yarn" else f"yarn {k}", "role": k, "origine": "package.json"})
    for k in re.findall(r"^([A-Za-z0-9_.-]+):", lire(os.path.join(racine, "Makefile")), re.M)[:30]:
        cmd.append({"cmd": f"make {k}", "role": k, "origine": "Makefile"})
    try:
        for k in json.loads(composer or "{}").get("scripts", {}):
            cmd.append({"cmd": f"composer {k}", "role": k, "origine": "composer.json"})
    except Exception:
        pass
    conv = {
        "Django": [("python manage.py runserver", "dev"), ("python manage.py test", "test"), ("python manage.py migrate", "migrations")],
        "Flask": [("flask run", "dev")], "FastAPI": [("uvicorn <module>:app --reload", "dev")],
        "Rails": [("bin/rails server", "dev"), ("bin/rails test", "test"), ("bin/rails db:migrate", "migrations")],
        "Laravel": [("php artisan serve", "dev"), ("php artisan test", "test"), ("php artisan migrate", "migrations")],
        "Spring Boot": [("./mvnw spring-boot:run" if "mvnw" in noms else "./gradlew bootRun" if "gradlew" in noms else "mvn spring-boot:run", "dev"),
                        ("./mvnw test" if "mvnw" in noms else "./gradlew test" if "gradlew" in noms else "mvn test", "test")],
        "ASP.NET Core": [("dotnet run", "dev"), ("dotnet test", "test")],
        "Entity Framework Core": [("dotnet ef database update", "migrations")],
    }
    for f_ in fw:
        for c, role in conv.get(f_, []):
            cmd.append({"cmd": c, "role": role, "origine": f"convention {f_}"})
    if "go.mod" in noms:
        cmd += [{"cmd": "go run .", "role": "dev", "origine": "convention Go"}, {"cmd": "go test ./...", "role": "test", "origine": "convention Go"}]
    if "pytest" in py and not any(c["role"] == "test" for c in cmd):
        cmd.append({"cmd": "pytest", "role": "test", "origine": "convention pytest"})
    for f in fichiers:
        if re.search(r"(^|/)(docker-)?compose[^/]*\.ya?ml$", f) and "/" not in f:
            cmd.append({"cmd": f"docker compose -f {f} up -d", "role": "services", "origine": f})
    tests = [t for t, ok in (("Vitest", '"vitest"' in deps), ("Jest", '"jest"' in deps), ("Cucumber", "cucumber" in deps or "cucumber" in gem),
                             ("Playwright", "playwright" in deps or "playwright" in py), ("Cypress", '"cypress"' in deps),
                             ("pytest", "pytest" in py), ("RSpec", "rspec" in gem), ("PHPUnit", "phpunit" in composer or "pestphp" in composer),
                             ("JUnit", "junit" in jvm), ("xUnit/NUnit", "xunit" in dotnet or "nunit" in dotnet), ("go test", "go.mod" in noms)) if ok]
    return {"langages": [l for l, _ in langages.most_common(5)], "frameworks": fw, "tests": tests, "commandes": cmd}


# --------------------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("racine", nargs="?", default=".")
    ap.add_argument("--module")
    ap.add_argument("--sortie")
    ap.add_argument("--min-signaux", type=int, default=2)
    a = ap.parse_args()
    racine = os.path.abspath(a.racine)
    fichiers = sorted(lister(racine))
    existants = set(fichiers)

    # 1. Signaux de modules
    signaux = defaultdict(Counter)
    noms = defaultdict(Counter)

    def signal(nom, poids, origine):
        s = souche(nom)
        if s and len(s) > 1 and s not in SOCLE:
            signaux[s][origine] += poids
            propre = re.sub(r"\.[A-Za-z0-9.]+$", "", nom)
            propre = re.sub(r"(?i)[._-]?(controller|service|repository|resolver|module|router|handler|serializer|views?|entity)$", "", propre) or propre
            noms[s][propre] += poids * (0.1 if origine in ("fichier de couche", "modèle") else 1)

    for f in fichiers:
        parts = f.split("/")
        base = parts[-1]
        if re.match(r"(src/)?content/help/[^/]+/", f):
            signal(parts[parts.index("help") + 1], 3, "aide")
        if "app" in parts[:3] and f.endswith((".tsx", ".ts", ".jsx", ".js")):
            i = parts.index("app")
            for p in parts[i + 1:-1]:
                if not (p.startswith("(") or p.startswith("[") or p in ("api",)):
                    signal(p, 2, "écran")
                    break
        for couche, poids in (("server", 2), ("components", 2), ("lib", 1), ("schemas", 1), ("services", 2),
                              ("modules", 3), ("features", 2), ("apps", 2), ("packages", 2), ("controllers", 2),
                              ("models", 1), ("views", 1), ("routers", 2), ("routes", 1), ("handlers", 2),
                              ("entities", 1), ("domain", 2), ("internal", 2), ("Controllers", 2), ("Models", 1),
                              ("Http", 1), ("pages", 2), ("screens", 2)):
            if couche in parts[:-1]:
                i = parts.index(couche)
                nom = parts[i + 1] if i + 1 < len(parts) - 1 else base
                if base.endswith(CODE) or i + 1 < len(parts) - 1:
                    signal(nom, poids, couche)
        # Django et apps Python : un dossier qui contient models.py, views.py ou apps.py est un module.
        if base in ("models.py", "views.py", "apps.py", "urls.py") and len(parts) >= 2:
            signal(parts[-2], 2 if base == "models.py" else 1, "app")
        # Paquets organisés par couche (Spring, NestJS, Go, architecture hexagonale…) :
        # le dossier parent d'une couche est le module (…/diligence/controller/X.java).
        if base.endswith(CODE):
            for i, p in enumerate(parts[:-1]):
                if i > 0 and p.lower() in COUCHES:
                    signal(parts[i - 1], 2, "paquet")
                    break
            # Fichiers nommés par couche : diligences_controller.rb, diligence.service.ts, DiligenceController.java
            if re.search(r"(controller|service|repository|resolver|module|router|handler|serializer|views?)\b", norm(base).replace("-", " ")):
                signal(base, 1, "fichier de couche")
    modele = lire_modeles(racine, fichiers)
    modeles = modele["entites"]
    for m in modeles:
        signal(m["nom"], 1, "modèle")

    FORTS = {"aide", "app", "paquet", "modules"}
    candidats = {s: c for s, c in signaux.items()
                 if (sum(c.values()) >= a.min_signaux and len(c) >= 2) or sum(v for k, v in c.items() if k in FORTS) >= 3}

    # Abréviations : une souche courte qui préfixe une souche plus longue en devient l'alias
    # (org → organigramme). La souche la plus longue garde le nom du module.
    alias_de = {}
    for court in sorted(candidats, key=len):
        if len(court) < 3:
            continue
        longs = [l for l in candidats if l != court and l.startswith(court) and l not in alias_de]
        if len(longs) == 1:
            alias_de[court] = longs[0]
    for court, long_ in alias_de.items():
        candidats[long_] = candidats[long_] + candidats.pop(court)
        noms[long_].update({k: 0 for k in noms[court]})
    principal = lambda x: alias_de.get(x, x)

    # 2. Rattacher les fichiers aux modules
    def souches_chemin(f):
        out = set()
        for p in f.split("/"):
            for t in jetons(p):
                out.add(racine_mot(t))
        return out

    par_module = defaultdict(list)
    proprietaire = {}
    for f in fichiers:
        if not f.endswith(CODE + (".md", ".prisma", ".feature", ".html", ".erb", ".haml", ".cshtml", ".razor", ".hbs", ".ejs", ".twig", ".sql")):
            continue
        ss = {principal(x) for x in souches_chemin(f)}
        trouves = [s for s in candidats if s in ss]
        for s in trouves:
            par_module[s].append(f)
        if trouves:
            base_s = principal(souche(f.split("/")[-1]))
            proprietaire[f] = base_s if base_s in trouves else trouves[0]

    # 3. Documents
    docs = []
    for f in fichiers:
        if f.endswith(".md") and "/help/" not in f:
            t = lire(os.path.join(racine, f))
            docs.append({"chemin": f, "titre": titre_md(t, f.split("/")[-1]), "octets": len(t.encode()), "texte": t})

    # 4. Imports
    alias = lire_alias(racine)
    contacts = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    utilise_par = defaultdict(lambda: defaultdict(set))
    par_suffixe = {}
    for x in fichiers:
        base_x = os.path.splitext(x)[0]
        for k in range(1, 5):
            par_suffixe.setdefault("/".join(base_x.split("/")[-k:]).lower(), x)

    def cibles_autres(f, texte):
        """Imports Python, Java/Kotlin et PHP ramenés à des fichiers du dépôt."""
        out = []
        if f.endswith(".py"):
            for m in re.finditer(r"^\s*from\s+([\w.]+)\s+import\s+([\w, ()]+)|^\s*import\s+([\w.]+)", texte, re.M):
                mod = (m.group(1) or m.group(3) or "").lstrip(".")
                noms_ = [x.strip(" ()") for x in (m.group(2) or "").split(",") if x.strip(" ()")]
                c = par_suffixe.get(mod.replace(".", "/").lower()) or par_suffixe.get((mod.replace(".", "/") + "/__init__").lower())
                if c:
                    out.append((c, noms_))
        elif f.endswith((".java", ".kt")):
            for m in re.finditer(r"^\s*import\s+(?:static\s+)?([\w.]+)\s*;?", texte, re.M):
                parts_ = m.group(1).split(".")
                c = par_suffixe.get("/".join(parts_[-4:]).lower()) or par_suffixe.get("/".join(parts_[-3:]).lower())
                if c:
                    out.append((c, [parts_[-1]]))
        elif f.endswith(".php"):
            for m in re.finditer(r"^\s*use\s+([\w\\]+)\s*;", texte, re.M):
                parts_ = m.group(1).split("\\")
                c = par_suffixe.get("/".join(parts_[-3:]).lower()) or par_suffixe.get("/".join(parts_[-2:]).lower())
                if c:
                    out.append((c, [parts_[-1]]))
        return out

    for f in fichiers:
        if f.endswith((".py", ".java", ".kt", ".php")):
            src = proprietaire.get(f)
            if src:
                for cible, fns in cibles_autres(f, lire(os.path.join(racine, f), 60000)):
                    dst = proprietaire.get(cible)
                    if dst and dst != src:
                        contacts[src][dst][cible].update(fns)
                        utilise_par[dst][src].add(f)
            continue
        if not f.endswith((".ts", ".tsx", ".js", ".jsx", ".mjs")):
            continue
        src = proprietaire.get(f)
        texte = lire(os.path.join(racine, f), 60000)
        for m in RE_IMPORT.finditer(texte):
            cible = resoudre(f, m.group(5), existants, alias)
            if not cible:
                continue
            fns = [x.strip().split(" as ")[0].replace("type ", "") for x in ((m.group(1) or "") + "," + (m.group(3) or "")).split(",") if x.strip()]
            fns += [x for x in (m.group(2), m.group(4)) if x]
            dst = proprietaire.get(cible)
            if src and dst and dst != src:
                contacts[src][dst][cible].update(fns)
                utilise_par[dst][src].add(f)
            elif src and not dst and "/lib/" in "/" + cible or (src and not dst and cible.startswith(("lib/", "src/lib/", "server/", "src/server/"))):
                contacts[src]["socle"][cible].update(fns)

    # Dépendances par le modèle de données : une entité d'un module qui référence l'entité
    # d'un autre module (clé étrangère, référence) crée un lien, quelle que soit la technologie.
    module_entite = {}
    for e in modeles:
        f_e = e.get("fichier")
        cand = proprietaire.get(f_e) if f_e else None
        js_ = jetons(e["nom"])
        par_nom_ = principal(racine_mot(js_[0])) if js_ else None
        module_entite[e["nom"]] = par_nom_ if par_nom_ in candidats else cand
    for r in modele["relations"]:
        a_, b_ = module_entite.get(r["de"]), module_entite.get(r["vers"])
        if a_ and b_ and a_ != b_:
            fe = next((e.get("fichier") for e in modeles if e["nom"] == r["vers"]), None) or "modèle de données"
            contacts[a_][b_][fe].add(r["vers"] + " (référencée par " + r["de"] + "." + r["champ"] + ")")
            utilise_par[b_][a_].add(next((e.get("fichier") for e in modeles if e["nom"] == r["de"]), "modèle de données"))

    # 5. Git
    est_git = bool(git(["rev-parse", "--is-inside-work-tree"], racine).strip())
    statut_git = {}
    if est_git:
        for l in git(["status", "--porcelain"], racine).splitlines():
            if len(l) > 3:
                statut_git[l[3:].strip().strip('"')] = l[:2].strip()

    # 6. Projet
    pkg = {}
    try:
        pkg = json.loads(lire(os.path.join(racine, "package.json")) or "{}")
    except Exception:
        pass
    makefile = re.findall(r"^([A-Za-z0-9_.-]+):", lire(os.path.join(racine, "Makefile")), re.M)
    projet = {
        "racine": racine,
        "nom": pkg.get("name") or os.path.basename(racine),
        "scripts": pkg.get("scripts", {}),
        "makefile": makefile[:30],
        "compose": [f for f in fichiers if re.search(r"(^|/)(docker-)?compose[^/]*\.ya?ml$", f)],
        "dockerfile": [f for f in fichiers if f.split("/")[-1].startswith("Dockerfile")],
        "documents_cles": [f for f in fichiers if f.split("/")[-1].upper() in
                           {"CLAUDE.MD", "AGENTS.MD", "README.MD", "DECISIONS.MD", "SCHEMA-REQUESTS.MD",
                            "PROGRESS.MD", "ROADMAP.MD", "CHANGELOG.MD", "CONTRIBUTING.MD"}],
        "modele_donnees": {"source": modele["source"], "autres_sources": modele.get("autres_sources", []),
                           "entites": len(modeles), "fichiers": sorted({m["fichier"] for m in modeles if m.get("fichier")})[:20]},
        "pile": detecter_pile(racine, fichiers, pkg),
        "git": {"depot": est_git,
                "branche": git(["branch", "--show-current"], racine).strip() if est_git else "",
                "dernier_commit": git(["log", "-1", "--date=short", "--format=%h|%ad|%s"], racine).strip() if est_git else "",
                "non_commites": len(statut_git)},
        "modules_detectes": sorted(candidats, key=lambda s: -sum(candidats[s].values())),
        "alias": alias_de,
    }

    # 7. Fiches modules
    def fiche_module(s):
        fs = par_module.get(s, [])
        nom = noms[s].most_common(1)[0][0] if noms[s] else s
        couches = defaultdict(list)
        for f in fs:
            p = f.split("/")
            if "/help/" in f:
                c = "aide"
            elif re.search(r"(\.test\.|\.spec\.|/tests?/|/e2e/|/features/.*\.feature$)", f):
                c = "tests"
            elif f.endswith(".md"):
                c = "documents"
            elif ("app" in p[:3] and f.endswith((".tsx", ".jsx", ".vue", ".svelte"))) or "pages" in p[:3] or "views" in p or "templates" in p or "screens" in p:
                c = "écrans"
            elif "components" in p:
                c = "composants"
            elif any(x in p for x in ("server", "controllers", "controller", "api", "routers", "handlers", "Controllers", "Http")) \
                    or re.search(r"(controller|service|router|handler|resolver)", f.split("/")[-1], re.I):
                c = "serveur"
            elif any(x in p for x in ("models", "entities", "entity", "Models", "migrations")) or f.split("/")[-1] == "models.py":
                c = "données"
            elif "schemas" in p:
                c = "validation"
            elif f.endswith(".prisma"):
                continue
            else:
                c = "logique"
            couches[c].append(f)
        mes_souches = {s} | {c for c, l in alias_de.items() if l == s}
        mes_fichiers = set(fs)
        mods = [m for m in modeles if (m.get("fichier") in mes_fichiers and len({proprietaire.get(m.get("fichier"))} | {s}) == 1)
                or (jetons(m["nom"]) and racine_mot(jetons(m["nom"])[0]) in mes_souches)]
        alias_s = {s, nom.lower()} | {n.lower() for n in noms[s]}
        docs_mod = []
        for d in docs:
            nb = sum(len(re.findall(r"\b" + re.escape(x) + r"s?\b", d["texte"], re.I)) for x in alias_s if len(x) > 2)
            if s in {principal(x) for x in souches_chemin(d["chemin"])} or nb >= 5:
                docs_mod.append({"chemin": d["chemin"], "titre": d["titre"], "octets": d["octets"], "mentions": nb})
        docs_mod.sort(key=lambda d: (-(s in {principal(x) for x in souches_chemin(d["chemin"])}), -d["mentions"]))
        todo = 0
        for f in fs:
            if f.endswith(CODE):
                todo += len(re.findall(r"\b(TODO|FIXME|XXX)\b", lire(os.path.join(racine, f), 200000)))
        hist = []
        if est_git and fs:
            hist = [dict(zip(("commit", "date", "message"), l.split("|", 2)))
                    for l in git(["log", "-n", "15", "--date=short", "--format=%h|%ad|%s", "--", *fs[:300]], racine).splitlines() if l]
        non_commites = sorted({f: statut_git[f] for f in fs if f in statut_git}.items())
        aide = couches.get("aide", [])
        return {
            "code": s.upper(), "souche": s, "nom": nom, "alias": sorted(mes_souches - {s}),
            "signaux": dict(candidats.get(s, signaux.get(s, {}))),
            "fichiers": {c: v[:MAX_FICHIERS] for c, v in sorted(couches.items())},
            "nb_fichiers": len(fs),
            "aide": {"present": bool(aide), "champs_md": any(x.endswith("champs.md") for x in aide),
                     "workflows_md": any(x.endswith("workflows.md") for x in aide)},
            "documents": docs_mod[:25],
            "modeles_donnees": [{"nom": m["nom"], "fichier": m.get("fichier"), "ligne": m.get("ligne"),
                                 "champs": [c["nom"] for c in m["champs"]]} for m in mods],
            "depend_de": {d: [{"f": f, "fn": sorted(v)} for f, v in sorted(cs.items())] for d, cs in contacts[s].items()},
            "utilise_par": {d: sorted(v)[:10] for d, v in utilise_par[s].items()},
            "historique": hist,
            "non_commites": [{"fichier": f, "etat": e} for f, e in non_commites],
            "todo": todo,
        }

    if a.module:
        cible = principal(racine_mot(norm(a.module).split("-")[0]))
        choix = [s for s in signaux if s == cible] or [s for s in candidats if s.startswith(cible) or cible.startswith(s)]
        choix = choix or [s for s in signaux if cible in s]
        if not choix:
            print(json.dumps({"erreur": f"Module « {a.module} » introuvable.", "modules_detectes": projet["modules_detectes"]},
                             ensure_ascii=False, indent=1))
            sys.exit(3)
        s = choix[0]
        if s not in candidats:
            candidats[s] = signaux[s]
        modules = [fiche_module(s)]
    else:
        modules = [fiche_module(s) for s in projet["modules_detectes"]]

    sortie = {"projet": projet, "modules": modules}
    texte = json.dumps(sortie, ensure_ascii=False, indent=1)
    if a.sortie:
        os.makedirs(os.path.dirname(os.path.abspath(a.sortie)), exist_ok=True)
        open(a.sortie, "w", encoding="utf-8").write(texte)
        print(f"Inventaire écrit : {a.sortie}")
        print("Modules : " + ", ".join(f"{m['nom']} ({m['nb_fichiers']} fichiers)" for m in modules))
    else:
        print(texte)


if __name__ == "__main__":
    main()
