#!/usr/bin/env python3
"""Hook PreToolUse (Bash): el subagente researcher solo puede ejecutar comandos de lectura.

Lista de permitidos por programa y por opción: lo que no se reconoce, se bloquea.
El comando se separa en palabras y operadores como haría el shell, así que las
comillas no sirven para disfrazar un programa ni una opción. Aun así es una
heurística sobre el texto del comando, no un sandbox.

Salida 0: permite (o no es researcher). Salida 2: bloquea; stderr llega al subagente.
Cualquier otro fallo también bloquea, por `onFailure: "block"` en settings.json.

Además aprueba sin preguntar la lectura de documentos (`unzip`, `pdftotext`, `pdfinfo`,
filtrados solo por tuberías que no leen otros ficheros). El resto, y en especial `curl`,
que es la salida a la red, sigue el flujo normal de permisos.
Solo usa la biblioteca estándar.
"""

import json
import re
import sys

AGENT = "researcher"

# Activan expansiones del shell (variables, sustitución de comandos, llaves,
# escapes). Solo son literales entre comillas simples.
FORBIDDEN_CHARS = set("$`\\{}")
SEPARATORS = {"|", "||", "&&", ";"}
PUNCTUATION = set("();<>|&")

ANY_OPTIONS = {"cat", "head", "tail", "ls", "grep", "wc", "cut", "tr", "cd", "pdfinfo"}
DOCUMENT_READERS = {"unzip", "pdftotext", "pdfinfo"}
FIND_OPTIONS = {
    "-name", "-iname", "-path", "-ipath", "-regex", "-iregex", "-type", "-maxdepth",
    "-mindepth", "-size", "-mtime", "-newer", "-empty", "-not", "!", "-a", "-and",
    "-o", "-or", "-print", "-print0", "-prune", "-ls", "-L", "-H",
}
UNZIP_MODES = {"-l", "-v", "-t", "-p", "-Z", "-Z1"}
PDFTOTEXT_FLAGS = {"-layout", "-raw", "-nopgbrk", "-q"}
PDFTOTEXT_WITH_VALUE = {"-f", "-l", "-enc"}
CURL_SHORT_FLAGS = re.compile(r"-[sSLfI]+")
CURL_LONG_FLAGS = {"--silent", "--show-error", "--location", "--fail", "--head", "--compressed"}
CURL_WITH_VALUE = {"-A", "-H", "-m", "--user-agent", "--header", "--max-time"}

ALLOWED_HELP = (
    "Permitido: cat, head, tail, ls, grep, wc, cut, tr, cd y pdfinfo con cualquier opción; "
    "find sin acciones (-name, -type, -maxdepth...); unzip -l|-v|-t|-p|-Z|-Z1 FICHERO [MIEMBRO]; "
    "pdftotext [-layout|-raw|-nopgbrk|-q|-f N|-l N|-enc X] FICHERO.pdf -; "
    "curl [-sSLfI|--compressed|-A V|-H V|-m N] URL_http(s). "
    "Se pueden encadenar con |, ;, && y ||; solo se redirige a /dev/null o con 2>&1. "
    "Fuera de comillas simples se prohíben $ ` \\ { }; los saltos de línea, siempre. "
    "Git no está permitido: lee .git con Read si hace falta."
)


class Blocked(Exception):
    pass


def tokenize(cmd):
    """Devuelve (es_operador, texto) por palabra u operador, como los separaría el shell.

    Basta un analizador mínimo porque se prohíbe todo lo que complica la sintaxis:
    sin barra invertida no hay escapes, así que una comilla siempre se cierra con
    la siguiente igual.
    """
    if "\n" in cmd:
        raise Blocked("salto de línea")
    forbidden = f"caracteres prohibidos fuera de comillas simples ({' '.join(sorted(FORBIDDEN_CHARS))})"
    tokens, word, in_word, i = [], [], False, 0

    def flush():
        nonlocal word, in_word
        if in_word:
            tokens.append((False, "".join(word)))
        word, in_word = [], False

    while i < len(cmd):
        c = cmd[i]
        if c in "'\"":
            end = cmd.find(c, i + 1)
            if end < 0:
                raise Blocked("comilla sin cerrar")
            inner = cmd[i + 1 : end]
            if c == '"' and FORBIDDEN_CHARS & set(inner):
                raise Blocked(forbidden)
            word.append(inner)
            in_word, i = True, end + 1
        elif c in FORBIDDEN_CHARS:
            raise Blocked(forbidden)
        elif c.isspace():
            flush()
            i += 1
        elif c in PUNCTUATION:
            flush()
            j = i
            while j < len(cmd) and cmd[j] in PUNCTUATION:
                j += 1
            tokens.append((True, cmd[i:j]))
            i = j
        else:
            word.append(c)
            in_word, i = True, i + 1
    flush()
    return tokens


def segments(cmd):
    """Separa el comando en segmentos de palabras, quitando las redirecciones inocuas.

    Devuelve también los operadores usados, para decidir si se aprueba sin preguntar.
    """
    tokens = tokenize(cmd)
    current, result, ops, i = [], [], set(), 0
    while i < len(tokens):
        is_op, tok = tokens[i]
        if not is_op:
            current.append(tok)
            i += 1
            continue
        ops.add(tok)
        if tok in SEPARATORS:
            result.append(current)
            current = []
        else:
            target = tokens[i + 1][1] if i + 1 < len(tokens) and not tokens[i + 1][0] else None
            if tok in {">", ">>"} and target == "/dev/null" or tok == ">&" and target in {"1", "2"}:
                if current and current[-1].isdigit():
                    current.pop()  # El descriptor de 2>/dev/null o 2>&1.
                i += 1
            elif tok == "<" and target is not None:
                i += 1  # Leer de un fichero no escribe nada.
            else:
                raise Blocked(f"operador no permitido: {tok}")
        i += 1
    result.append(current)
    return result, ops


def reads_only_stdin(words):
    """Filtro de tubería que no puede leer otros ficheros: los números no cuentan como ruta.

    Sin opciones largas (p. ej., `wc --files0-from`), y grep sin -f, -r, -R ni -d,
    que leen patrones o directorios.
    """
    prog, args = words[0], words[1:]
    if any(a.startswith("--") for a in args):
        return False
    positional = [a for a in args if not a.startswith("-") and not a.lstrip("+").isdigit()]
    if prog == "grep":
        if any(a.startswith("-") and set(a) & set("frRd") for a in args):
            return False
        return len(positional) <= 1  # Solo el patrón.
    if prog in {"head", "tail", "wc"}:
        return not positional
    return prog == "tr"


def auto_approved(segs, ops):
    """Un lector de documentos, encadenado solo por tuberías a filtros que no leen ficheros."""
    return (
        ops <= {"|", ">", ">&"}  # Las redirecciones que quedan aquí van a /dev/null o 2>&1.
        and segs[0][0] in DOCUMENT_READERS
        and all(reads_only_stdin(words) for words in segs[1:])
    )


def check_segment(words):
    if not words:
        raise Blocked("segmento vacío")
    prog, args = words[0], words[1:]
    for a in args:
        if a.startswith("-") and set(a) & set("*?["):
            raise Blocked(f"comodín en una opción: {a}")

    if prog in ANY_OPTIONS:
        return
    if prog == "find":
        for a in args:
            if a.startswith("-") and a not in FIND_OPTIONS:
                raise Blocked(f"opción de find no permitida: {a}")
    elif prog == "unzip":
        if not args or args[0] not in UNZIP_MODES or any(a.startswith("-") for a in args[1:]):
            raise Blocked("unzip solo lista o vuelca a la salida estándar")
    elif prog == "pdftotext":
        positional, rest = [], iter(args)
        for a in rest:
            if a in PDFTOTEXT_WITH_VALUE:
                next(rest, None)
            elif a == "-" or not a.startswith("-"):
                positional.append(a)
            elif a not in PDFTOTEXT_FLAGS:
                raise Blocked(f"opción de pdftotext no permitida: {a}")
        if len(positional) != 2 or positional[1] != "-":
            raise Blocked("pdftotext debe escribir en la salida estándar (último argumento: -)")
    elif prog == "curl":
        urls, rest = [], iter(args)
        for a in rest:
            if a in CURL_WITH_VALUE:
                next(rest, None)
            elif a in CURL_LONG_FLAGS or CURL_SHORT_FLAGS.fullmatch(a):
                pass
            elif a.startswith("-"):
                raise Blocked(f"opción de curl no permitida: {a}")
            else:
                urls.append(a)
        if len(urls) != 1 or not re.match(r"https?://", urls[0]):
            raise Blocked("curl necesita exactamente una URL http(s)")
    else:
        raise Blocked(f"programa no permitido: {prog}")


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        print("researcher-bash-guard: entrada no válida", file=sys.stderr)
        return 2
    agent = data.get("agent_type") or ""
    if agent != AGENT and not agent.endswith(":" + AGENT):  # Con plugin: "plugin:researcher".
        return 0
    try:
        segs, ops = segments(data.get("tool_input", {}).get("command", ""))
        for words in segs:
            check_segment(words)
    except Blocked as e:
        print(f"Bloqueado por researcher-bash-guard: {e}. {ALLOWED_HELP}", file=sys.stderr)
        return 2
    if auto_approved(segs, ops):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "researcher-bash-guard: lectura de documento validada",
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
