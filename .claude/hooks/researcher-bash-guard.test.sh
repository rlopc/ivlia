#!/usr/bin/env bash
# shellcheck disable=SC2016  # Los comandos de prueba son literales: no deben expandirse.
# Pruebas de researcher-bash-guard.py.
# Uso: .claude/hooks/researcher-bash-guard.test.sh
# Cada caso: resultado esperado, agente y comando. Resultados: 0 permite y sigue el
# flujo normal de permisos, A aprueba sin preguntar, 2 bloquea.

set -uo pipefail

guard="$(dirname "$0")/researcher-bash-guard.py"
# The hook runs the guard with ~/.local/bin/python3.14 (.claude/settings.json); the
# test uses the root .venv's Python, the same version, which CI also has.
project="$(cd "$(dirname "$0")/../.." && pwd)"
python="$project/.venv/bin/python"
failures=0

check() {
  local expected=$1 agent=$2 cmd=$3 actual out
  out=$("$python" -I -c 'import json, sys
print(json.dumps({"agent_type": sys.argv[1], "tool_input": {"command": sys.argv[2]}}))' "$agent" "$cmd" |
    CLAUDE_PROJECT_DIR="$project" "$python" -I "$guard" 2>/dev/null)
  actual=$?
  [[ $actual == 0 && $out == *'"allow"'* ]] && actual=A
  if [[ $actual != "$expected" ]]; then
    echo "FALLA: esperado $expected, obtenido $actual [$agent] $cmd"
    failures=$((failures + 1))
  fi
}

# Otros agentes y la conversación principal: el hook no opina.
check 0 "" 'rm -rf /tmp/x'
check 0 general-purpose 'rm -rf /tmp/x'

# Lectura permitida.
check 0 researcher 'ls -la /some/dir'
check 0 researcher 'cat "/path with spaces/file.md" | head -50'
check 0 researcher 'grep -rn "a|b>c" /dir 2>/dev/null | wc -l'
check 0 researcher 'find . -name "*.md" -type f'
check 0 researcher 'cd /dir && grep -c foo bar.txt'
check 0 researcher 'curl -sSL https://example.com | grep -i token'

# Lectura de documentos: se aprueba sin preguntar.
check A researcher 'unzip -l book.epub'
check A researcher 'unzip -p book.epub OEBPS/ch1.xhtml | head -100'
check A researcher 'pdftotext -layout book.pdf - | grep -n "chapter"'
check A researcher 'pdftotext -f 2 -l 2 book.pdf - 2>/dev/null | grep -A 3 "code" | head -n 20'
check A researcher 'pdfinfo book.pdf'
check A researcher 'pdfinfo -meta book.pdf | wc -l'

# Lectura de documentos combinada con algo que puede leer otros ficheros: se pregunta.
check 0 researcher 'pdftotext a.pdf - ; cat ~/.ssh/id_rsa'
check 0 researcher 'pdftotext a.pdf - && ls ~'
check 0 researcher 'pdftotext a.pdf - | grep x ~/.ssh/id_rsa'
check 0 researcher 'pdftotext a.pdf - | grep -f ~/.ssh/id_rsa'
check 0 researcher 'pdftotext a.pdf - | grep -rn x'
check 0 researcher 'pdftotext a.pdf - | wc --files0-from=list'
check 0 researcher 'pdftotext a.pdf - | head ~/.ssh/id_rsa'
check 0 researcher 'pdftotext a.pdf - | cat - ~/.ssh/id_rsa'
check 0 researcher 'curl -sSL https://example.com/page'
check 0 researcher 'curl -sSL -A "Mozilla/5.0" https://example.com 2>&1 | head'
check 0 researcher 'curl -fsSL --compressed -m 30 https://example.com'
check 0 researcher 'find . -maxdepth 2 -type f -not -name "*.pyc"'
check 0 plugin:researcher 'ls'
# Entre comillas simples, $ \ { } y los operadores son literales (falsos positivos de la prueba real).
check 0 researcher "curl -sSL https://example.com | tr '<>' '  ' | grep -i token"
check 0 researcher "tr '<>' '\\n\\n' < page.html"
check 0 researcher "grep -n 'foo\$' f"
check 0 researcher "find . -name 'a{b}.md'"

# Escritura o ejecución arbitraria: bloqueadas.
check 2 plugin:researcher 'rm x'
check 2 researcher 'rm -rf /tmp/x'
check 2 researcher 'cat a > b'
check 2 researcher 'echo hi >> notes.md'
check 2 researcher 'ls; rm x'
check 2 researcher 'ls && python3 -c "print(1)"'
check 2 researcher 'cat $(which rm)'
check 2 researcher 'cat `ls`'
check 2 researcher 'cat <(rm x)'
check 2 researcher 'find . -name "*.tmp" -delete'
check 2 researcher 'find . -exec rm {} \;'
check 2 researcher 'unzip book.epub'
check 2 researcher 'unzip -o book.epub -d out'
check 2 researcher 'pdftotext book.pdf'
check 2 researcher 'curl -sSLo page.html https://example.com'
check 2 researcher 'curl --output=page.html https://example.com'
check 2 researcher 'curl -X POST https://example.com'
check 2 researcher 'curl -d "a=1" https://example.com'
check 2 researcher 'sort -o out.txt list.txt'
check 2 researcher 'sort -u list.txt'
check 2 researcher 'cat x | tee y'
check 2 researcher 'FOO=1 cat x'
check 2 researcher 'cat x &>/tmp/y'
check 2 researcher '/bin/rm x'
check 2 researcher 'file -C -m mymagic'
check 2 researcher 'cat x &'
check 2 researcher '(rm x)'
check 2 researcher '; rm x'

# Disfraces con comillas, escapes y expansiones (hallados en la revisión).
check 2 researcher "'rm' '-rf' '/tmp/x'"
check 2 researcher '"rm" cat'
check 2 researcher 'cat x; "python3" "-c" "print(1)"'
check 2 researcher "cat \\' ; rm -rf x ; cat \\'"
check 2 researcher $'cat "a\nb"; rm x'
check 2 researcher "cat 'unterminated"
check 2 researcher "find . -de'l'ete"
check 2 researcher 'find . -dele\te'
check 2 researcher 'find . -{delete,true}'
check 2 researcher 'find . -de${EMPTY}lete'
check 2 researcher 'find . -*elete'
check 2 researcher 'grep -n "foo$" f'
check 2 researcher 'cat "a\nb"'
check 2 researcher 'cat "$(rm x)"'
check 2 researcher 'cat <> x'
check 2 researcher 'git log --oneline'

# Opciones de escritura pegadas a su valor o fuera de la lista.
check 2 researcher 'curl -o/tmp/x https://example.com'
check 2 researcher 'curl -sSo/tmp/x https://example.com'
check 2 researcher 'curl --etag-save x https://example.com'
check 2 researcher 'curl --hsts x https://example.com'
check 2 researcher "curl -w '%output' https://example.com"
check 2 researcher 'curl gopher://example.com/x'
check 2 researcher 'curl -Q "DELE f" ftp://example.com/'
check 2 researcher 'curl https://a.com https://b.com'
check 2 researcher 'unzip -p book.epub -d out'
check 2 researcher 'pdftotext book.pdf out.txt -'

if ((failures)); then
  echo "$failures caso(s) fallido(s)"
  exit 1
fi
echo "Todos los casos pasan"
