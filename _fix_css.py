# Fix CSS: Move login styles outside :root block
with open('frontend/css/style.css', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the first :root block
# Current structure:
# :root {
# /* ===== LOGIN ===== */
# .login-wrapper { ... }
# ...
#     --primary: #2563eb;
#     ...
# }
#
# We need to restructure to:
# :root {
#     --primary: #2563eb;
#     ...
# }
#
# /* ===== LOGIN ===== */
# .login-wrapper { ... }
# ...

idx_root_open = content.find(':root {')
if idx_root_open >= 0:
    # Find the closing brace - it's before "*, *::before"
    idx_universal = content.find('*, *::before')
    if idx_universal > 0:
        # Find the last '}' before universal selector
        idx_root_close = content.rfind('}', 0, idx_universal)
        
        # Extract the :root block content
        root_content = content[idx_root_open + 7:idx_root_close].strip()
        
        # Extract CSS variable definitions (lines starting with --)
        var_lines = []
        other_lines = []
        for line in root_content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('--') or stripped == '':
                var_lines.append(line)
            else:
                other_lines.append(line)
        
        # Rebuild: :root with only variables, then rest as regular CSS
        new_root = ':root {\n' + '\n'.join(var_lines).strip() + '\n}\n'
        rest_content = '\n'.join(other_lines).strip()
        
        # Put it together
        new_content = new_root + '\n\n' + rest_content + '\n\n' + content[idx_universal:]
        
        with open('frontend/css/style.css', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print('CSS fixed successfully')
        print(f'Variables in :root: {len([l for l in var_lines if l.strip().startswith("--")])}')
        print(f'Styles moved outside :root: {len([l for l in other_lines if l.strip() and not l.strip().startswith("/*") and not l.strip().startswith("*")])} blocks')
    else:
        print("Could not find universal selector marker")
else:
    print("Could not find :root block")
