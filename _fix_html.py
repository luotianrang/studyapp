import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the first loginOverlay div
# It looks like:
# <div id="loginOverlay" style="display:none">
#     <div class="login-wrapper">
#         <div class="login-card">
#             ...
#             <div id="loginFormContainer"></div>
#             [script tags]
#
# <!-- LOGIN OVERLAY -->
# <div id="loginOverlay" style="display:none">
#     ...
# </div>

# Strategy: Find the second <!-- LOGIN OVERLAY --> comment and everything after it up to </body>
# Remove that second overlay (it's a duplicate)

lines = content.split('\n')

# Find key markers
login_overlay_comment_idx = None
second_overlay_start_idx = None
body_close_idx = None

for i, line in enumerate(lines):
    if 'LOGIN OVERLAY' in line and '<!--' in line:
        if login_overlay_comment_idx is None:
            login_overlay_comment_idx = i
        else:
            second_overlay_start_idx = login_overlay_comment_idx
            login_overlay_comment_idx = i
    if '</body>' in line:
        body_close_idx = i

print(f"Login overlay comment at line: {login_overlay_comment_idx}")
print(f"Second overlay start at line: {second_overlay_start_idx}")
print(f"</body> at line: {body_close_idx}")

if second_overlay_start_idx is not None and body_close_idx is not None:
    # Remove the duplicate overlay (from comment to before </body>)
    # But keep the script tags - they need to be moved outside the first overlay
    
    # Extract the second overlay content (to remove it)
    # And also extract script tags from inside the first overlay (to keep them)
    
    # Let me find where script tags are and where the first overlay should close
    
    # First: close the first overlay properly
    # Find the line with <div id="loginFormContainer"></div>
    # After that line, we need to add closing divs: </div></div></div>
    # Then the script tags should come after
    
    overlay_close_needed = False
    fixed_lines = []
    in_first_overlay = False
    
    for i, line in enumerate(lines):
        if '<div id="loginOverlay"' in line and not in_first_overlay:
            in_first_overlay = True
            fixed_lines.append(line)
            continue
        
        if '<div id="loginFormContainer"></div>' in line and in_first_overlay:
            fixed_lines.append(line)
            # Close the first overlay: card, wrapper, overlay
            fixed_lines.append('        </div>')
            fixed_lines.append('    </div>')
            fixed_lines.append('</div>')
            overlay_close_needed = True
            continue
        
        # Skip lines in the second overlay section (from comment to </body>)
        if i == login_overlay_comment_idx:
            # This is the second overlay start, skip everything until </body>
            # Actually, let me just keep the script tags and skip everything else
            continue
        
        if second_overlay_start_idx is not None and login_overlay_comment_idx is not None:
            if login_overlay_comment_idx <= i < body_close_idx:
                # Skip the entire second overlay region
                continue
        
        fixed_lines.append(line)
    
    content_new = '\n'.join(fixed_lines)
    
    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(content_new)
    
    print("HTML fixed successfully")
else:
    print("Could not find overlay structure")
