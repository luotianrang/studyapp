import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# Find all relevant lines
overlay_open_idx = None
form_container_idx = None
second_overlay_idx = None
body_close_idx = None

for i, line in enumerate(lines):
    if '<div id="loginOverlay"' in line and overlay_open_idx is None:
        overlay_open_idx = i
    elif '<div id="loginOverlay"' in line:
        second_overlay_idx = i
    if '<div id="loginFormContainer"></div>' in line and form_container_idx is None:
        form_container_idx = i
    if '</body>' in line:
        body_close_idx = i

print(f"First overlay: line {overlay_open_idx}")
print(f"Form container: line {form_container_idx}")
print(f"Second overlay: line {second_overlay_idx}")  
print(f"</body>: line {body_close_idx}")

if all(x is not None for x in [overlay_open_idx, form_container_idx, second_overlay_idx, body_close_idx]):
    # Build new file:
    # 1. Lines before first overlay
    # 2. First overlay properly closed
    # 3. Script tags (moved from inside overlay)
    # 4. Lines between second overlay and </body> (should be just the second overlay)
    # 5. </body>
    
    new_lines = []
    
    # Lines before first overlay
    new_lines.extend(lines[:overlay_open_idx])
    
    # First overlay - properly closed
    new_lines.extend(lines[overlay_open_idx:form_container_idx+1])
    new_lines.append('            </div>')  # close login-card
    new_lines.append('        </div>')      # close login-wrapper
    new_lines.append('    </div>')          # close loginOverlay
    new_lines.append('')                 # blank line
   
    # Script tags from inside the first overlay
    for i in range(form_container_idx+1, second_overlay_idx):
        line = lines[i]
        if '<script' in line:
            new_lines.append(line)
    
    new_lines.append('')
    new_lines.append(lines[body_close_idx])
    
    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("HTML fixed successfully")
else:
    print("Missing markers")
