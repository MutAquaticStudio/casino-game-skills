#!/usr/bin/env python3
"""Consistency checks for this skills repo. Run from the repo root: python3 scripts/check_repo.py [--strict]

1. frontmatter   each skills/<name>/SKILL.md has name == folder name and a description (<= 1024 chars)
2. paths         every `references/...`, `scripts/...`, `assets/...` path written in backticks in a SKILL.md,
                 a reference doc or the README exists (relative to the skill, to the file, or to the repo)
3. syntax        every script in skills/*/scripts compiles (python: compile, node: --check)
4. orphans       every script and every non-vendor reference file is mentioned somewhere in docs
5. sections      "`file.md` §N" points at a heading that exists in that file
6. tree          every file named in the README structure tree exists, and every script and top-level reference is mentioned in the README
Exit code 1 on any ERROR; WARNs (orphans, size) only fail with --strict.
"""
import glob, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
errors, warns = [], []
skills = sorted(glob.glob("skills/*/SKILL.md"))
docs = [f for f in glob.glob("**/*.md", recursive=True) if "/vendor/" not in f]
doc_text = {f: open(f, encoding="utf-8").read() for f in docs}
all_docs_blob = "\n".join(doc_text.values())


def frontmatter(path):
    t = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n", t, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip().strip('"')
    return fm


# 1. frontmatter
for p in skills:
    d = os.path.basename(os.path.dirname(p))
    fm = frontmatter(p)
    if fm is None:
        errors.append(f"{p}: no frontmatter")
        continue
    if fm.get("name") != d:
        errors.append(f"{p}: name '{fm.get('name')}' != folder '{d}'")
    desc = fm.get("description", "")
    if not desc:
        errors.append(f"{p}: empty description")
    elif len(desc) > 1024:
        errors.append(f"{p}: description is {len(desc)} chars (max 1024)")
    n = len(doc_text[p].splitlines())
    if n > 500:
        warns.append(f"{p}: {n} lines (keep under 500; move detail to references/)")

# 2. paths in backticks
PATH = re.compile(r"`((?:references|scripts|assets)/[A-Za-z0-9_./*\-]+)`")
def exists(ref, doc):
    if "*" in ref or ref.endswith("/"):
        return True
    skill_dir = os.path.join("skills", doc.split("/")[1]) if doc.startswith("skills/") else None
    cands = [ref, os.path.join(os.path.dirname(doc), ref)]
    cands += [os.path.join(s, ref) for s in glob.glob("skills/*")]
    if skill_dir:
        cands.insert(0, os.path.join(skill_dir, ref))
    return any(os.path.exists(c) for c in cands) or bool(glob.glob("skills/**/" + ref, recursive=True))   # vendored files live deeper
for doc, t in doc_text.items():
    for ref in sorted(set(PATH.findall(t))):
        if ref.endswith(("/", ".")):
            continue
        if not exists(ref, doc):
            errors.append(f"{doc}: `{ref}` does not exist")

# 3. syntax
for f in sorted(glob.glob("skills/*/scripts/*") + glob.glob("scripts/*")):
    if f.endswith(".py"):
        try:
            compile(open(f, encoding="utf-8").read(), f, "exec")
        except SyntaxError as e:
            errors.append(f"{f}: syntax error line {e.lineno}: {e.msg}")
    elif f.endswith(".mjs") and shutil.which("node"):
        r = subprocess.run(["node", "--check", f], capture_output=True, text=True)
        if r.returncode:
            errors.append(f"{f}: {r.stderr.strip().splitlines()[-1] if r.stderr else 'node --check failed'}")

# 4. orphans
cands = [f for f in glob.glob("skills/*/scripts/*") if not f.endswith(("__pycache__",))]
cands += [f for f in glob.glob("skills/*/references/**/*.*", recursive=True)
          if "/vendor/" not in f and "/examples/" not in f and not f.endswith(".png")]
for f in sorted(cands):
    if os.path.isdir(f):
        continue
    parent_glob = os.path.basename(os.path.dirname(f)) + "/*"
    if os.path.basename(f) not in all_docs_blob and parent_glob not in all_docs_blob:
        warns.append(f"{f}: not mentioned in any doc")

# 5. section references: `file.md` §N
def headings(path):
    nums = set()
    for line in open(path, encoding="utf-8"):
        m = re.match(r"#{1,4}\s+(\d+(?:\.\d+)*)[.\s]", line)
        if m:
            nums.add(m.group(1))
    return nums
by_base = {}
for f in docs:
    by_base.setdefault(os.path.basename(f), []).append(f)
SEC = re.compile(r"`([A-Za-z0-9_\-]+\.md)`\s*(?:\([^)]*\)\s*)?§\s*(\d+(?:\.\d+)?)")
for doc, t in doc_text.items():
    for fn, sec in sorted(set(SEC.findall(t))):
        targets = by_base.get(fn, [])
        if len(targets) != 1:
            continue
        top = sec.split(".")[0]
        hs = headings(targets[0])
        if sec not in hs and top not in hs:
            errors.append(f"{doc}: `{fn}` §{sec} has no such heading in {targets[0]}")

# 6. README tree
if os.path.exists("README.md"):
    tree = [l for l in doc_text["README.md"].splitlines() if re.match(r"^[│├└ ]+", l)]
    names = set()
    for l in tree:
        found = re.findall(r"([A-Za-z0-9_\-]+\.(?:py|mjs|json|md|ts))", l)
        names.update(found[:1] if re.search(r"[├└]──", l) else found)   # on entry lines only the first name is a file; the rest is description
    have = {os.path.basename(f) for f in glob.glob("**/*", recursive=True) if os.path.isfile(f)}
    for n in sorted(names - have):
        errors.append(f"README.md tree names {n}, which does not exist")

    readme = doc_text["README.md"]
    for f in sorted(glob.glob("skills/*/scripts/*") + glob.glob("skills/*/assets/*") + glob.glob("scripts/*")
                    + [x for x in glob.glob("skills/*/references/*.md")]):
        if os.path.isfile(f) and os.path.basename(f) not in readme:
            warns.append(f"README.md does not mention {f}")

for w in warns:
    print("WARN ", w)
for e in errors:
    print("ERROR", e)
print(f"\n{len(skills)} skills, {len(errors)} errors, {len(warns)} warnings")
sys.exit(1 if errors or (warns and "--strict" in sys.argv) else 0)
