"""shfmt.py <in> <out>: one-line shader code -> one statement per line, tab indent. Only adds line breaks/indent after ';' '{' '}' (outside parentheses), so the token stream is unchanged.
shfmt.py --check <a> <b>: 1 when both files hold the same tokens (whitespace-insensitive at statement borders)."""
import sys, re
def pieces(s):
    """Split into (text, kind) at ';' '{' '}' outside parentheses and at newlines; kind = the break char."""
    cur = ''; par = 0
    for ch in s:
        par += (ch == '(') - (ch == ')')
        if ch == '\n' or (par == 0 and ch in ';{}'):
            yield cur, ch; cur = ''
        else: cur += ch
    yield cur, '\n'
def fmt(s):
    out = []; ind = 0
    for text, k in pieces(s):
        text = text.strip()
        if k == '}':
            if text: out.append('\t' * ind + text)
            ind -= 1; out.append('\t' * ind + '}')
        else:
            line = text + (k if k != '\n' else '')
            if line: out.append('\t' * ind + line)
            ind += k == '{'
    return '\n'.join(out) + '\n'
norm = lambda s: re.sub(r'\s*([;{}])\s*', r'\1', re.sub(r'\s+', ' ', s)).strip()
if __name__ == '__main__':
    if sys.argv[1] == '--check': print(int(norm(open(sys.argv[2], encoding='utf-8').read()) == norm(open(sys.argv[3], encoding='utf-8').read())))
    else:
        src = open(sys.argv[1], encoding='utf-8').read(); dst = fmt(src); assert norm(src) == norm(dst), 'token stream changed'
        open(sys.argv[2], 'w', encoding='utf-8', newline='\n').write(dst); print(sys.argv[2], dst.count('\n'), 'lines')
