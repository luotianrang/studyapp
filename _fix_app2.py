import sys

with open('frontend/js/app.v5.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Global replace of \" with " (these were in places like document.querySelector(\"...\"))
old_count = content.count('\\"')

# But we need to preserve \" INSIDE JavaScript strings
# Approach: Use a smarter parser
lines = content.split('\n')
result = []

for line in lines:
    chars = []
    i = 0
    in_sq = False  # Inside single-quoted string
    in_dq = False  # Inside double-quoted string
    prev_was_backslash = False
    
    while i < len(line):
        ch = line[i]
        
        if ch == '\\':
            if in_dq and i + 1 < len(line) and line[i+1] == '"':
                # Keep escaped quote inside double-quoted string
                chars.append(ch)
                chars.append(line[i+1])
                i += 2
                continue
            elif in_sq and i + 1 < len(line) and line[i+1] == "'":
                # Keep escaped single quote inside single-quoted string
                chars.append(ch)
                chars.append(line[i+1])
                i += 2
                continue
            else:
                chars.append(ch)
                i += 1
                continue
        
        if ch == '"' and not in_sq:
            in_dq = not in_dq
            chars.append(ch)
            i += 1
            continue
        
        if ch == "'" and not in_dq:
            in_sq = not in_sq
            chars.append(ch)
            i += 1
            continue
        
        chars.append(ch)
        i += 1
    
    result.append(''.join(chars))

fixed = '\n'.join(result)
new_count = fixed.count('\\"')
replaced = old_count - new_count

# Step 2: Fix the specific broken line with id=loginBtn inside class
# Current: class='btn btn-primary btn-login id="loginBtn" id="loginBtn"'
# Fixed:   class='btn btn-primary btn-login' id='loginBtn'
fixed = fixed.replace(
    "class='btn btn-primary btn-login id=\"loginBtn\" id=\"loginBtn\"'",
    "class='btn btn-primary btn-login' id='loginBtn'"
)

# Also handle case where my first fixer already corrupted the quotes
fixed = fixed.replace(
    "class='btn btn-primary btn-login id=\"loginBtn\" id=\"loginBtn\"'",
    "class='btn btn-primary btn-login' id='loginBtn'"
)

with open('frontend/js/app.v5.js', 'w', encoding='utf-8') as f:
    f.write(fixed)

print(f'Replaced {replaced} occurrences of \\" (keeping {new_count} inside strings)')
print('Also fixed the id=loginBtn class attribute issue')
