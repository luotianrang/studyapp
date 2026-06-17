import re

# Fix backslash-doublequote issue in app.v5.js
with open('frontend/js/app.v5.js', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
fixed_lines = []

for line in lines:
    result = []
    i = 0
    in_string = False
    string_char = None
    
    while i < len(line):
        ch = line[i]
        
        # Handle escape sequences inside strings
        if in_string and ch == '\\' and i + 1 < len(line):
            next_ch = line[i + 1]
            if next_ch == string_char or next_ch == '\\':
                # Keep the escape sequence as-is
                result.append(ch)
                result.append(next_ch)
                i += 2
                continue
        
        # Toggle string state for unescaped quotes
        if ch == '"' or ch == "'":
            if not in_string:
                in_string = True
                string_char = ch
            elif ch == string_char:
                in_string = False
                string_char = None
            result.append(ch)
            i += 1
            continue
        
        # Replace backslash-doublequote when NOT inside a string
        if ch == '\\' and i + 1 < len(line) and line[i + 1] == '"' and not in_string:
            result.append('"')
            i += 2
            continue
        
        result.append(ch)
        i += 1
    
    fixed_lines.append(''.join(result))

fixed_content = '\n'.join(fixed_lines)

# Write back
with open('frontend/js/app.v5.js', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print('Fixed successfully')
print(f'Replaced {content.count(chr(92)+chr(34)) - fixed_content.count(chr(92)+chr(34))} occurrences')
