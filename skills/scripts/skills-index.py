#!/usr/bin/env python3
"""skills-index.py - gera skills/SKILLS.txt a partir do frontmatter de cada skills/<nome>/SKILL.md.

Uso:
  python3 skills/scripts/skills-index.py          regenera SKILLS.txt
  python3 skills/scripts/skills-index.py --check  sai 1 se SKILLS.txt está desatualizado; não escreve

Colunas: nome (versão) | objetivo | contexto para ser utilizada (resumido).
Objetivo = primeira frase da description. Contexto = trecho a partir de "Use quando" /
"Use when" / "Triggers" da description, cortado em palavra. Só biblioteca padrão.
"""
import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # skills/
OUT = ROOT / "SKILLS.txt"
W_NAME, W_OBJ, W_CTX = 24, 56, 60
MAX_OBJ, MAX_CTX = 240, 320
CTX_START = re.compile(
    r"(?<!n't )(?<!not )(?<!não )"  # "Don't use for ..." é exclusão, não gatilho
    r"\b(Use (when|whenever|on|after|for|by default|before|this skill|quando|ao|em|no|na|nos|nas|se|sempre que|antes|após)"
    r"|Triggers?\b|Gatilhos?\b|Acione\b|Invoque\b)",
    re.I,
)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-Ú`\"(])")


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm = m.group(1)
    def field(key, indented=False):
        pat = (r"^\s+" if indented else r"^") + re.escape(key) + r":[ \t]*(.*?)[ \t]*$"
        f = re.search(pat, fm, re.M)
        if not f:
            return ""
        v = f.group(1)
        if v in ("", ">", ">-", "|", "|-", ">+", "|+"):
            # escalar YAML em bloco (`>-`, `|`): junta as linhas indentadas que seguem
            block = []
            for line in fm[f.end():].split("\n")[1:]:
                if line.strip() == "" or line[0] in " \t":
                    block.append(line.strip())
                else:
                    break
            v = " ".join(x for x in block if x)
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        return v
    return {"name": field("name"), "description": field("description"), "version": field("version", True)}


def cut(s: str, limit: int) -> str:
    s = " ".join(s.split())
    if len(s) <= limit:
        return s
    s = s[:limit].rsplit(" ", 1)[0]
    return s.rstrip(",;:-") + " ..."


def objective(desc: str) -> str:
    parts = SENTENCE_SPLIT.split(desc.strip(), maxsplit=1)
    return cut(parts[0], MAX_OBJ)


def context(desc: str) -> str:
    m = CTX_START.search(desc)
    if m:
        return cut(desc[m.start():], MAX_CTX)
    parts = SENTENCE_SPLIT.split(desc.strip(), maxsplit=1)
    return cut(parts[1] if len(parts) > 1 else parts[0], MAX_CTX)


def rows():
    for skill in sorted(p for p in ROOT.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()):
        fm = frontmatter((skill / "SKILL.md").read_text(encoding="utf-8"))
        name = fm.get("name") or skill.name
        if name != skill.name:
            name = f"{skill.name} (name: {name})"
        label = f"{name} ({fm['version']})" if fm.get("version") else name
        desc = fm.get("description", "")
        yield label, objective(desc), context(desc)


def render(items) -> str:
    sep = "+" + "-" * (W_NAME + 2) + "+" + "-" * (W_OBJ + 2) + "+" + "-" * (W_CTX + 2) + "+"
    lines = [
        "SKILLS.txt - índice das skills desta pasta (GERADO; não edite à mão)",
        "Regenerar: python3 skills/scripts/skills-index.py   Conferir: python3 skills/scripts/skills-index.py --check",
        "Fonte: frontmatter (name, description, metadata.version) de cada skills/<nome>/SKILL.md.",
        "Objetivo = primeira frase da description. Contexto = trecho \"Use quando / Use when / Triggers\" resumido.",
        f"Skills: {len(items)}",
        "",
        sep,
    ]
    head = (
        "| " + "nome skill (versão)".ljust(W_NAME) + " | "
        + "objetivo".ljust(W_OBJ) + " | "
        + "contexto para ser utilizada (resumido)".ljust(W_CTX) + " |"
    )
    lines += [head, sep.replace("-", "=")]
    for label, obj, ctx in items:
        c1 = textwrap.wrap(label, W_NAME) or [""]
        c2 = textwrap.wrap(obj, W_OBJ) or [""]
        c3 = textwrap.wrap(ctx, W_CTX) or [""]
        for i in range(max(len(c1), len(c2), len(c3))):
            a = c1[i] if i < len(c1) else ""
            b = c2[i] if i < len(c2) else ""
            c = c3[i] if i < len(c3) else ""
            lines.append("| " + a.ljust(W_NAME) + " | " + b.ljust(W_OBJ) + " | " + c.ljust(W_CTX) + " |")
        lines.append(sep)
    return "\n".join(lines) + "\n"


def main() -> int:
    content = render(list(rows()))
    if "--check" in sys.argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current == content:
            print("SKILLS.txt: atualizado")
            return 0
        print("SKILLS.txt: desatualizado; rode python3 skills/scripts/skills-index.py", file=sys.stderr)
        return 1
    OUT.write_text(content, encoding="utf-8")
    print(f"SKILLS.txt: {content.count(chr(10))} linhas, {len(list(rows()))} skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
