#!/usr/bin/env python3
"""Lit les modèles de données d'un dépôt, quelle que soit la technologie, et les ramène à un
format neutre commun :

{"source": "django",
 "entites":   [{"nom", "fichier", "ligne", "champs": [{"nom", "type", "optionnel", "liste", "id", "unique"}]}],
 "relations": [{"de", "champ", "vers", "fk": [...], "optionnel", "un_a_un", "plusieurs_a_plusieurs"}]}

Une relation va de l'entité qui porte la clé étrangère vers l'entité référencée (plusieurs à
un), sauf `un_a_un` (un à un) et `plusieurs_a_plusieurs` (table de liaison implicite).

Lecteurs : prisma, sql, django, sqlalchemy, typeorm, jpa, efcore, rails, laravel, mongoose,
drizzle. Ce sont des lectures par motifs, sans exécuter le projet : elles couvrent les
écritures usuelles. Pour une autre technologie, ou si la lecture est incomplète, écrire le
format neutre à la main et le passer à modele_vers_mcd.py avec --neutre.

Usage : python modeles_donnees.py [racine] [--source auto|prisma|sql|…] [--sortie modele.json]
"""
import argparse, json, os, re, sys

IGNORES = {"node_modules", ".git", ".next", "dist", "build", "out", "coverage", "vendor", ".venv",
           "venv", "__pycache__", "target", "bin", "obj", "suivi", ".gradle", ".idea"}
PRIORITE = ["prisma", "typeorm", "jpa", "efcore", "django", "sqlalchemy", "rails", "laravel",
            "drizzle", "mongoose", "sql"]


def lister(racine):
    for d, sous, fichiers in os.walk(racine):
        sous[:] = [s for s in sous if s not in IGNORES and not s.startswith(".")]
        for f in fichiers:
            yield os.path.relpath(os.path.join(d, f), racine).replace(os.sep, "/")


def lire(racine, f):
    try:
        with open(os.path.join(racine, f), encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except Exception:
        return ""


def ligne_de(texte, pos):
    return texte.count("\n", 0, pos) + 1


def bloc(texte, debut, ouvre="{", ferme="}"):
    """Contenu entre l'accolade ouvrante trouvée à partir de `debut` et sa fermante."""
    i = texte.find(ouvre, debut)
    if i < 0:
        return "", -1
    n = 0
    for j in range(i, len(texte)):
        if texte[j] == ouvre:
            n += 1
        elif texte[j] == ferme:
            n -= 1
            if n == 0:
                return texte[i + 1:j], j
    return texte[i + 1:], len(texte)


def champ(nom, type_="", optionnel=False, liste=False, id_=False, unique=False):
    return {"nom": nom, "type": type_, "optionnel": optionnel, "liste": liste, "id": id_, "unique": unique}


def rel(de, champ_, vers, fk=None, optionnel=False, un_a_un=False, pap=False):
    return {"de": de, "champ": champ_, "vers": vers, "fk": fk or [], "optionnel": optionnel,
            "un_a_un": un_a_un, "plusieurs_a_plusieurs": pap}


def singulier_table(table):
    """org_units → org_unit (convention Rails et Laravel des clés étrangères)."""
    if table.endswith("ies"):
        return table[:-3] + "y"
    return table[:-1] if table.endswith("s") and not table.endswith("ss") else table


def singulier_classe(table):
    """diligence_sources → DiligenceSource (pour les sources qui ne connaissent que des tables)."""
    parts = re.split(r"[_\-]+", table)
    if parts and len(parts[-1]) > 3:
        p = parts[-1]
        parts[-1] = p[:-3] + "y" if p.endswith("ies") else p[:-1] if p.endswith("s") and not p.endswith("ss") else p
    return "".join(x[:1].upper() + x[1:] for x in parts if x)


# --------------------------------------------------------------------------- Prisma
def lire_prisma(racine, fichiers):
    ents, rels = [], []
    for f in [x for x in fichiers if x.endswith(".prisma")]:
        t = lire(racine, f)
        for m in re.finditer(r"^\s*model\s+(\w+)\s*\{", t, re.M):
            corps, _ = bloc(t, m.end() - 1)
            e = {"nom": m.group(1), "fichier": f, "ligne": ligne_de(t, m.start()), "champs": []}
            for l in corps.splitlines():
                c = re.match(r"\s*(\w+)\s+(\w+)(\[\])?(\?)?(.*)$", l)
                if not c or l.strip().startswith(("@@", "//")):
                    continue
                reste = c.group(5) or ""
                e["champs"].append(dict(champ(c.group(1), c.group(2), bool(c.group(4)), bool(c.group(3)),
                                              "@id" in reste, "@unique" in reste), _rel=reste))
            ents.append(e)
    noms = {e["nom"] for e in ents}
    for e in ents:
        garde = []
        for c in e["champs"]:
            reste = c.pop("_rel")
            if c["type"] in noms:
                fk = re.search(r"fields:\s*\[([^\]]+)\]", reste)
                if fk and not c["liste"]:
                    cols = [x.strip() for x in fk.group(1).split(",")]
                    unique = any(x["nom"] in cols and x["unique"] for x in e["champs"])
                    rels.append(rel(e["nom"], c["nom"], c["type"], cols, c["optionnel"], unique))
                elif c["liste"]:
                    autre = next((x for x in ents if x["nom"] == c["type"]), None)
                    if autre and any(x.get("type") == e["nom"] and x.get("liste") for x in autre["champs"]) and e["nom"] < c["type"]:
                        rels.append(rel(e["nom"], c["nom"], c["type"], pap=True))
                continue
            garde.append(c)
        e["champs"] = garde
    return ents, rels


# --------------------------------------------------------------------------- SQL
def lire_sql(racine, fichiers):
    ents, rels, par_nom = [], [], {}
    for f in sorted(x for x in fichiers if x.endswith(".sql")):
        t = re.sub(r"--[^\n]*", "", lire(racine, f))
        for m in re.finditer(r"create\s+table\s+(?:if\s+not\s+exists\s+)?[`\"\[]?(?:\w+[`\"\]]?\.)?[`\"\[]?(\w+)[`\"\]]?\s*\(", t, re.I):
            corps, _ = bloc(t, m.end() - 1, "(", ")")
            nom = m.group(1)
            e = {"nom": nom, "fichier": f, "ligne": ligne_de(t, m.start()), "champs": []}
            pk, fks = set(), []
            for part in re.split(r",(?![^()]*\))", corps):
                p = part.strip()
                if not p:
                    continue
                low = p.lower()
                if low.startswith(("primary key", "constraint", "foreign key", "unique", "key ", "index", "check")):
                    k = re.search(r"primary\s+key\s*\(([^)]+)\)", p, re.I)
                    if k:
                        pk |= {x.strip(" `\"[]") for x in k.group(1).split(",")}
                    fk = re.search(r"foreign\s+key\s*\(([^)]+)\)\s*references\s+[`\"\[]?(?:\w+[`\"\]]?\.)?[`\"\[]?(\w+)", p, re.I)
                    if fk:
                        fks.append(([x.strip(" `\"[]") for x in fk.group(1).split(",")], fk.group(2)))
                    continue
                c = re.match(r"[`\"\[]?(\w+)[`\"\]]?\s+([\w ]+?(?:\([^)]*\))?)(\s|$)", p)
                if not c:
                    continue
                col = c.group(1)
                e["champs"].append(champ(col, c.group(2).strip(), "not null" not in low and "primary key" not in low,
                                         False, "primary key" in low, "unique" in low))
                r = re.search(r"references\s+[`\"\[]?(?:\w+[`\"\]]?\.)?[`\"\[]?(\w+)", p, re.I)
                if r:
                    fks.append(([col], r.group(1)))
            for c in e["champs"]:
                if c["nom"] in pk:
                    c["id"] = True
            if nom in par_nom:
                ents.remove(par_nom[nom])
                rels = [r for r in rels if r["de"] != nom]
            par_nom[nom] = e
            ents.append(e)
            for cols, vers in fks:
                opt = all(next((c["optionnel"] for c in e["champs"] if c["nom"] == x), False) for x in cols)
                uni = len(cols) == 1 and any(c["nom"] == cols[0] and c["unique"] for c in e["champs"])
                rels.append(rel(nom, cols[0], vers, cols, opt, uni))
        for m in re.finditer(r"alter\s+table\s+[`\"\[]?(?:\w+[`\"\]]?\.)?[`\"\[]?(\w+)[^;]*?foreign\s+key\s*\(([^)]+)\)\s*references\s+[`\"\[]?(?:\w+[`\"\]]?\.)?[`\"\[]?(\w+)", t, re.I | re.S):
            cols = [x.strip(" `\"[]") for x in m.group(2).split(",")]
            if not any(r["de"] == m.group(1) and r["fk"] == cols for r in rels):
                e = par_nom.get(m.group(1), {"champs": []})
                opt = all(next((c["optionnel"] for c in e["champs"] if c["nom"] == x), True) for x in cols)
                rels.append(rel(m.group(1), cols[0], m.group(3), cols, opt))
        for m in re.finditer(r"alter\s+table\s+[`\"\[]?(?:\w+[`\"\]]?\.)?[`\"\[]?(\w+)[`\"\]]?\s+add\s+(?:column\s+)?[`\"\[]?(\w+)[`\"\]]?\s+([\w ]+?(?:\([^)]*\))?)\s*(?:;|not|null|default|references|$)", t, re.I):
            e = par_nom.get(m.group(1))
            if e and m.group(2).lower() not in ("constraint", "foreign", "primary", "unique", "index") and not any(c["nom"] == m.group(2) for c in e["champs"]):
                e["champs"].append(champ(m.group(2), m.group(3).strip(), True))
    noms = {e["nom"] for e in ents}
    return ents, [r for r in rels if r["vers"] in noms]


# --------------------------------------------------------------------------- Django
def lire_django(racine, fichiers):
    ents, rels = [], []
    cands = [f for f in fichiers if f.endswith(".py") and (f.endswith("models.py") or "/models/" in f)]
    for f in cands:
        t = lire(racine, f)
        if "models.Model" not in t and "Model)" not in t:
            continue
        classes = list(re.finditer(r"^class\s+(\w+)\s*\(([^)]*)\)\s*:", t, re.M))
        for i, m in enumerate(classes):
            if "Model" not in m.group(2) or "Meta" == m.group(1):
                continue
            fin = classes[i + 1].start() if i + 1 < len(classes) else len(t)
            corps = t[m.end():fin]
            if re.search(r"^\s+abstract\s*=\s*True", corps, re.M):
                continue
            e = {"nom": m.group(1), "fichier": f, "ligne": ligne_de(t, m.start()), "champs": []}
            a_pk = False
            for c in re.finditer(r"^\s{4}(\w+)\s*=\s*(?:models\.)?(\w+Field|ForeignKey|OneToOneField|ManyToManyField)\((.*)$", corps, re.M):
                nom, typ, args = c.group(1), c.group(2), c.group(3)
                opt = "null=True" in args.replace(" ", "")
                if typ in ("ForeignKey", "OneToOneField", "ManyToManyField"):
                    cible = re.match(r"\s*['\"]?(?:\w+\.)?(\w+)['\"]?", args)
                    vers = cible.group(1) if cible else "?"
                    if vers == "self":
                        vers = e["nom"]
                    if typ == "ManyToManyField":
                        rels.append(rel(e["nom"], nom, vers, pap=True))
                    else:
                        rels.append(rel(e["nom"], nom, vers, [nom + "_id"], opt, typ == "OneToOneField"))
                        e["champs"].append(champ(nom + "_id", "FK", opt))
                    continue
                pk = "primary_key=True" in args.replace(" ", "")
                a_pk |= pk
                e["champs"].append(champ(nom, typ, opt, False, pk, "unique=True" in args.replace(" ", "")))
            if not a_pk:
                e["champs"].insert(0, champ("id", "AutoField", id_=True))
            ents.append(e)
    noms = {e["nom"] for e in ents}
    return ents, [r for r in rels if r["vers"] in noms]


# --------------------------------------------------------------------------- SQLAlchemy
def lire_sqlalchemy(racine, fichiers):
    ents, rels, tables = [], [], {}
    for f in [x for x in fichiers if x.endswith(".py")]:
        t = lire(racine, f)
        if "sqlalchemy" not in t and "db.Model" not in t and "mapped_column" not in t:
            continue
        classes = list(re.finditer(r"^class\s+(\w+)\s*\(([^)]*)\)\s*:", t, re.M))
        for i, m in enumerate(classes):
            fin = classes[i + 1].start() if i + 1 < len(classes) else len(t)
            corps = t[m.end():fin]
            if "Column(" not in corps and "mapped_column(" not in corps:
                continue
            e = {"nom": m.group(1), "fichier": f, "ligne": ligne_de(t, m.start()), "champs": []}
            tn = re.search(r"__tablename__\s*=\s*['\"](\w+)['\"]", corps)
            tables[tn.group(1) if tn else m.group(1).lower()] = m.group(1)
            for c in re.finditer(r"^\s{4}(\w+)\s*(?::\s*Mapped\[([^\]]+(?:\])?)\])?\s*=\s*(?:db\.|sa\.)?(Column|mapped_column|relationship)\((.*)$", corps, re.M):
                nom, annot, quoi, args = c.group(1), c.group(2) or "", c.group(3), c.group(4)
                if quoi == "relationship":
                    continue
                typ = re.match(r"\s*(?:db\.|sa\.)?(\w+)", args)
                typ = typ.group(1) if typ and typ.group(1) not in ("ForeignKey",) else (annot or "")
                opt = "nullable=True" in args.replace(" ", "") or "Optional[" in annot or "| None" in annot
                fk = re.search(r"ForeignKey\(\s*['\"](\w+)\.\w+['\"]", args)
                e["champs"].append(champ(nom, typ, opt, False, "primary_key=True" in args.replace(" ", ""),
                                         "unique=True" in args.replace(" ", "")))
                if fk:
                    rels.append(rel(e["nom"], nom, "table:" + fk.group(1), [nom], opt))
            ents.append(e)
    for r in rels:
        if r["vers"].startswith("table:"):
            r["vers"] = tables.get(r["vers"][6:], r["vers"][6:])
    noms = {e["nom"] for e in ents}
    return ents, [r for r in rels if r["vers"] in noms]


# --------------------------------------------------------------------------- TypeORM / JPA / EF Core
def _decorateurs_classe(t, motif_entite, fichier, motif_champ, analyser):
    ents, rels = [], []
    for m in re.finditer(motif_entite, t, re.S):
        corps, _ = bloc(t, m.end() - 1)
        e = {"nom": m.group(1), "fichier": fichier, "ligne": ligne_de(t, m.start()), "champs": []}
        for c in re.finditer(motif_champ, corps, re.S):
            analyser(e, c, rels)
        ents.append(e)
    return ents, rels


def lire_typeorm(racine, fichiers):
    ents, rels = [], []

    def analyser(e, c, rels_):
        deco, nom, typ = c.group(1), c.group(2), (c.group(3) or "").strip()
        opt = "nullable: true" in deco or "?" in c.group(0).split(":")[0][-3:]
        cible = re.search(r"\(\)\s*=>\s*(\w+)", deco)
        if "@ManyToOne" in deco or "@OneToOne" in deco:
            jc = re.search(r"@JoinColumn\(\s*\{\s*name:\s*['\"](\w+)['\"]", deco)
            if cible and ("@ManyToOne" in deco or "@JoinColumn" in deco):
                rels_.append(rel(e["nom"], nom, cible.group(1), [jc.group(1) if jc else nom + "Id"], opt, "@OneToOne" in deco))
            return
        if "@ManyToMany" in deco:
            if cible and "@JoinTable" in deco:
                rels_.append(rel(e["nom"], nom, cible.group(1), pap=True))
            return
        if "@OneToMany" in deco:
            return
        if "Column" in deco:
            e["champs"].append(champ(nom, typ, opt, typ.endswith("[]"), "Primary" in deco, "unique: true" in deco))

    for f in [x for x in fichiers if x.endswith(".ts")]:
        t = lire(racine, f)
        if "@Entity" not in t:
            continue
        a, b = _decorateurs_classe(t, r"@Entity\([^)]*\)\s*(?:export\s+)?(?:default\s+)?class\s+(\w+)[^{]*\{", f,
                                   r"((?:@\w+\((?:[^()]|\([^()]*\))*\)\s*)+)(\w+)[!?]?\s*:\s*([^;=\n]+)", analyser)
        ents += a; rels += b
    return ents, rels


def lire_jpa(racine, fichiers):
    ents, rels = [], []

    def analyser(e, c, rels_):
        deco, typ, nom = c.group(1) or "", c.group(2).strip(), c.group(3)
        if "@Transient" in deco:
            return
        cible = re.search(r"(?:List|Set|Collection)<(\w+)>", typ)
        if "@ManyToOne" in deco or ("@OneToOne" in deco and "mappedBy" not in deco):
            jc = re.search(r"@JoinColumn\([^)]*name\s*=\s*\"(\w+)\"", deco)
            opt = "optional = false" not in deco and "nullable = false" not in deco
            rels_.append(rel(e["nom"], nom, typ, [jc.group(1) if jc else nom + "_id"], opt, "@OneToOne" in deco))
            return
        if "@ManyToMany" in deco:
            if cible and "mappedBy" not in deco:
                rels_.append(rel(e["nom"], nom, cible.group(1), pap=True))
            return
        if "@OneToMany" in deco or "@OneToOne" in deco:
            return
        e["champs"].append(champ(nom, typ, "nullable = false" not in deco and "@Id" not in deco, False, "@Id" in deco,
                                 "unique = true" in deco))

    for f in [x for x in fichiers if x.endswith((".java", ".kt"))]:
        t = lire(racine, f)
        if "@Entity" not in t:
            continue
        a, b = _decorateurs_classe(t, r"@Entity\b.*?(?:public\s+)?(?:data\s+)?class\s+(\w+)[^{]*\{", f,
                                   r"((?:@\w+(?:\((?:[^()]|\([^()]*\))*\))?\s*)*)(?:private|protected|public)\s+(?:final\s+)?([\w<>, ?]+?)\s+(\w+)\s*(?:=[^;]*)?;", analyser)
        ents += a; rels += b
    noms = {e["nom"] for e in ents}
    return ents, [r for r in rels if r["vers"] in noms]


def lire_efcore(racine, fichiers):
    cs = [f for f in fichiers if f.endswith(".cs")]
    textes = {f: lire(racine, f) for f in cs}
    dbsets = set()
    for t in textes.values():
        dbsets |= set(re.findall(r"DbSet<(\w+)>", t))
    if not dbsets:
        return [], []
    ents, rels = [], []
    for f, t in textes.items():
        for m in re.finditer(r"(?:public\s+)?(?:partial\s+)?class\s+(\w+)[^{]*\{", t):
            if m.group(1) not in dbsets:
                continue
            corps, _ = bloc(t, m.end() - 1)
            e = {"nom": m.group(1), "fichier": f, "ligne": ligne_de(t, m.start()), "champs": []}
            for c in re.finditer(r"((?:\[[^\]]+\]\s*)*)public\s+(?:virtual\s+)?([\w<>?,\. ]+?)\s+(\w+)\s*\{\s*get;", corps):
                attrs, typ, nom = c.group(1), c.group(2).strip(), c.group(3)
                base = typ.rstrip("?")
                if re.search(r"(?:ICollection|List|IList|IEnumerable|HashSet)<\w+>", typ):
                    continue  # côté « plusieurs » d'une relation : porté par l'autre entité
                if base in dbsets:
                    fk = nom + "Id"
                    rels.append(rel(e["nom"], nom, base, [fk], typ.endswith("?")))
                    continue
                e["champs"].append(champ(nom, typ, typ.endswith("?"), False, nom in ("Id", e["nom"] + "Id") or "[Key]" in attrs, False))
            ents.append(e)
    return ents, rels


# --------------------------------------------------------------------------- Rails / Laravel
def lire_rails(racine, fichiers):
    f = next((x for x in fichiers if x.endswith("db/schema.rb")), None)
    if not f:
        return [], []
    t = lire(racine, f)
    ents, rels = [], []
    for m in re.finditer(r'create_table\s+"(\w+)"(.*?)\bdo\s*\|t\|(.*?)^\s*end', t, re.S | re.M):
        nom = singulier_classe(m.group(1))
        e = {"nom": nom, "fichier": f, "ligne": ligne_de(t, m.start()), "champs": []}
        if "id: false" not in m.group(2):
            e["champs"].append(champ("id", "bigint", id_=True))
        for c in re.finditer(r't\.(\w+)\s+"(\w+)"(.*)', m.group(3)):
            typ, col, reste = c.groups()
            e["champs"].append(champ(col, typ, "null: false" not in reste))
        ents.append(e)
    tables = {e["nom"] for e in ents}
    for m in re.finditer(r'add_foreign_key\s+"(\w+)",\s*"(\w+)"(?:,\s*column:\s*"(\w+)")?', t):
        de, vers = singulier_classe(m.group(1)), singulier_classe(m.group(2))
        col = m.group(3) or singulier_table(m.group(2)) + "_id"
        ent = next((e for e in ents if e["nom"] == de), None)
        opt = next((c["optionnel"] for c in ent["champs"] if c["nom"] == col), True) if ent else True
        if de in tables and vers in tables:
            rels.append(rel(de, col.replace("_id", ""), vers, [col], opt))
    return ents, rels


def lire_laravel(racine, fichiers):
    ents, rels, par_nom = [], [], {}
    for f in sorted(x for x in fichiers if "/migrations/" in x and x.endswith(".php")):
        t = lire(racine, f)
        for m in re.finditer(r"Schema::(create|table)\(\s*['\"](\w+)['\"]\s*,\s*function", t):
            corps, _ = bloc(t, m.end())
            nom = singulier_classe(m.group(2))
            e = par_nom.get(nom)
            if not e:
                if m.group(1) == "table":
                    continue
                e = {"nom": nom, "fichier": f, "ligne": ligne_de(t, m.start()), "champs": []}
                par_nom[nom] = e; ents.append(e)
            for c in re.finditer(r"\$table->(\w+)\(\s*(?:['\"](\w+)['\"])?[^;]*;", corps):
                typ, col, instr = c.group(1), c.group(2), c.group(0)
                opt = "->nullable()" in instr
                if typ in ("id", "bigIncrements", "increments", "uuid") and (typ != "uuid" or "primary" in instr or col in (None, "id")):
                    e["champs"].append(champ(col or "id", typ, id_=True)); continue
                if typ in ("timestamps", "softDeletes", "rememberToken", "index", "unique", "dropColumn", "primary"):
                    continue
                if typ in ("foreignId", "foreignUuid", "foreignIdFor"):
                    e["champs"].append(champ(col or "?", typ, opt))
                    on = re.search(r"constrained\(\s*['\"](\w+)['\"]", instr)
                    vers = singulier_classe(on.group(1)) if on else singulier_classe(re.sub(r"_id$", "", col or "")) if "constrained" in instr else None
                    if vers:
                        rels.append(rel(nom, re.sub(r"_id$", "", col or ""), vers, [col], opt))
                    continue
                if typ == "foreign":
                    on = re.search(r"->on\(\s*['\"](\w+)['\"]", instr)
                    if on:
                        rels.append(rel(nom, re.sub(r"_id$", "", col or ""), singulier_classe(on.group(1)), [col], True))
                    continue
                if col:
                    e["champs"].append(champ(col, typ, opt, False, False, "->unique()" in instr))
    noms = {e["nom"] for e in ents}
    return ents, [r for r in rels if r["vers"] in noms]


# --------------------------------------------------------------------------- Mongoose / Drizzle
def lire_mongoose(racine, fichiers):
    ents, rels = [], []
    for f in [x for x in fichiers if x.endswith((".js", ".ts", ".mjs"))]:
        t = lire(racine, f)
        if "Schema(" not in t or "mongoose" not in t:
            continue
        schemas = {}
        for m in re.finditer(r"(?:const|let|var)\s+(\w+)\s*=\s*new\s+(?:mongoose\.)?Schema(?:<[^>]*>)?\(\s*\{", t):
            corps, _ = bloc(t, m.end() - 1)
            schemas[m.group(1)] = (corps, m.start())
        for m in re.finditer(r"model(?:<[^>]*>)?\(\s*['\"](\w+)['\"]\s*,\s*(\w+)", t):
            if m.group(2) not in schemas:
                continue
            corps, pos = schemas[m.group(2)]
            e = {"nom": m.group(1), "fichier": f, "ligne": ligne_de(t, pos), "champs": [champ("_id", "ObjectId", id_=True)]}
            niveau, i, cle = 0, 0, None
            for c in re.finditer(r"(\w+)\s*:\s*(\[?\s*\{[^{}]*\}\s*\]?|\[?\s*\w+(?:\.\w+)*\s*\]?)\s*,?", corps):
                if corps[:c.start()].count("{") - corps[:c.start()].count("}") != 0:
                    continue
                nom, val = c.group(1), c.group(2)
                liste = val.strip().startswith("[")
                ref = re.search(r"ref\s*:\s*['\"](\w+)['\"]", val)
                req = "required: true" in val or "required:true" in val
                typ = re.search(r"type\s*:\s*([\w.]+)", val)
                if ref:
                    rels.append(rel(e["nom"], nom, ref.group(1), [nom], not req, False, liste))
                    continue
                e["champs"].append(champ(nom, typ.group(1) if typ else val.strip(" []"), not req, liste, False, "unique: true" in val))
            ents.append(e)
    noms = {e["nom"] for e in ents}
    return ents, [r for r in rels if r["vers"] in noms]


def lire_drizzle(racine, fichiers):
    ents, rels, var2 = [], [], {}
    textes = {f: lire(racine, f) for f in fichiers if f.endswith(".ts")}
    for f, t in textes.items():
        if "drizzle-orm" not in t:
            continue
        for m in re.finditer(r"export\s+const\s+(\w+)\s*=\s*(?:pg|mysql|sqlite)Table\(\s*['\"](\w+)['\"]\s*,\s*\{", t):
            corps, _ = bloc(t, m.end() - 1)
            nom = singulier_classe(m.group(2))
            var2[m.group(1)] = nom
            e = {"nom": nom, "fichier": f, "ligne": ligne_de(t, m.start()), "champs": []}
            for c in re.finditer(r"(\w+)\s*:\s*(\w+)\(\s*['\"]?(\w*)['\"]?[^)]*\)([^,\n]*)", corps):
                nom_c, typ, reste = c.group(1), c.group(2), c.group(4)
                e["champs"].append(champ(nom_c, typ, ".notNull()" not in reste and ".primaryKey()" not in reste, False,
                                         ".primaryKey()" in reste, ".unique()" in reste))
                r = re.search(r"\.references\(\s*\(\)\s*=>\s*(\w+)\.", reste)
                if r:
                    rels.append(rel(nom, nom_c, "var:" + r.group(1), [nom_c], ".notNull()" not in reste))
            ents.append(e)
    for r in rels:
        r["vers"] = var2.get(r["vers"][4:], r["vers"][4:])
    return ents, rels


LECTEURS = {"prisma": lire_prisma, "sql": lire_sql, "django": lire_django, "sqlalchemy": lire_sqlalchemy,
            "typeorm": lire_typeorm, "jpa": lire_jpa, "efcore": lire_efcore, "rails": lire_rails,
            "laravel": lire_laravel, "mongoose": lire_mongoose, "drizzle": lire_drizzle}


def lire_modeles(racine, fichiers=None, source="auto"):
    """Renvoie {"source", "entites", "relations", "autres_sources"}."""
    fichiers = fichiers if fichiers is not None else sorted(lister(racine))
    resultats = {}
    for nom in (PRIORITE if source == "auto" else [source]):
        try:
            ents, rels = LECTEURS[nom](racine, fichiers)
        except Exception as ex:  # une lecture par motifs ne doit jamais bloquer l'exploration
            print(f"Lecture {nom} interrompue : {ex}", file=sys.stderr)
            ents, rels = [], []
        if ents:
            resultats[nom] = {"source": nom, "entites": ents, "relations": rels}
    if not resultats:
        return {"source": None, "entites": [], "relations": [], "autres_sources": []}
    # SQL généré par un ORM (migrations Prisma, etc.) : ne le garder que s'il est seul.
    choix = next(n for n in PRIORITE if n in resultats) if source == "auto" else source
    out = dict(resultats[choix])
    out["autres_sources"] = sorted(n for n in resultats if n != choix)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("racine", nargs="?", default=".")
    ap.add_argument("--source", default="auto", choices=["auto"] + list(LECTEURS))
    ap.add_argument("--sortie")
    a = ap.parse_args()
    res = lire_modeles(os.path.abspath(a.racine), source=a.source)
    texte = json.dumps(res, ensure_ascii=False, indent=1)
    if a.sortie:
        open(a.sortie, "w", encoding="utf-8").write(texte)
        print(f"Modèle neutre écrit : {a.sortie} (source {res['source']}, {len(res['entites'])} entités, "
              f"{len(res['relations'])} relations ; autres sources : {', '.join(res['autres_sources']) or 'aucune'})")
    else:
        print(texte)


if __name__ == "__main__":
    main()
