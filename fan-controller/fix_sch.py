#!/usr/bin/env python3
"""Fix kicad-mcp-server output defects in a .kicad_sch file:
1. Strip invalid per-property (uuid ...) sub-fields on placed symbol instances.
2. Add missing (instances (project ...)) blocks to placed symbol instances.
3. Move (sheet_instances ...) and (embedded_fonts ...) to the true end of the file.
Idempotent - safe to run repeatedly after each batch of MCP tool calls.
"""
import re
import sys

path = sys.argv[1]
project_name = sys.argv[2]
sheet_uuid = sys.argv[3]

content = open(path).read()

before = content.count('(uuid "')
content = re.sub(
    r'(\(effects \(font \(size 1\.27 1\.27\)\)(?: \(hide yes\))?\))\n\s*\(uuid "[0-9a-f-]+"\)\n(\s*)\)',
    r'\1\n\2)',
    content
)
after = content.count('(uuid "')
print(f"stripped {before-after} property uuids")

content = re.sub(r'\n?\t\(sheet_instances\n\t\t\(path "/"\n\t\t\t\(page "1"\)\n\t\t\)\n\t\)\n?', '\n', content)
content = re.sub(r'\n?\t\(embedded_fonts no\)\n?', '\n', content)

def add_instances_to_all(text):
    result = []
    i = 0
    n = len(text)
    marker = '  (symbol (lib_id "'
    count = 0
    while True:
        idx = text.find(marker, i)
        if idx == -1:
            result.append(text[i:])
            break
        result.append(text[i:idx])
        depth = 0
        j = idx
        while j < n:
            if text[j] == '(':
                depth += 1
            elif text[j] == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        block = text[idx:j+1]
        ref_m = re.search(r'\(property "Reference" "([^"]+)"', block)
        ref = ref_m.group(1)
        if '(instances' not in block:
            count += 1
            instances_block = (
                f'\n  (instances\n'
                f'    (project "{project_name}"\n'
                f'      (path "/{sheet_uuid}"\n'
                f'        (reference "{ref}") (unit 1)\n'
                f'      )\n'
                f'    )\n'
                f'  )\n)'
            )
            block = block[:-1] + instances_block
        result.append(block)
        i = j + 1
    print(f"added instances block to {count} symbols")
    return ''.join(result)

content = add_instances_to_all(content)

content = content.rstrip()
assert content.endswith(')')
content = content[:-1].rstrip()
content += '\n\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)\n'

open(path, 'w').write(content)
print("done")
