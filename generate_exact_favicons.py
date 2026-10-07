import subprocess
import os
import base64
from PIL import Image

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# 1. Exact SVGs matching the header elements
GUEST_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="8" fill="#181411" stroke="#3d3024" stroke-width="1.5"/>
  <svg x="4" y="4" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#c49c6d" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
  </svg>
</svg>"""

ADMIN_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <defs>
    <linearGradient id="adminGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#c49c6d"/>
      <stop offset="100%" stop-color="#8c673d"/>
    </linearGradient>
  </defs>
  <rect width="32" height="32" rx="8" fill="url(#adminGrad)"/>
  <svg x="4" y="4" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#110e0c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M3 17h18M5 17a7 7 0 0114 0M12 4v3m-2-3h4"/>
  </svg>
</svg>"""

# Save SVG files
with open("favicon-guest.svg", "w", encoding="utf-8") as f:
    f.write(GUEST_SVG)

with open("favicon-admin.svg", "w", encoding="utf-8") as f:
    f.write(ADMIN_SVG)

print("Saved SVG files.")

# Helper to render SVG via Edge headless to high-res PNG
def render_svg_to_png(svg_content, out_png, size=512):
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {size}px; height: {size}px; background: transparent; overflow: hidden; }}
svg {{ width: 100%; height: 100%; display: block; }}
</style>
</head>
<body>
{svg_content}
</body>
</html>"""
    temp_html = f"temp_render_{os.path.basename(out_png)}.html"
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    abs_html = os.path.abspath(temp_html)
    abs_png = os.path.abspath(out_png)
    
    cmd = [
        EDGE_PATH,
        "--headless=new",
        f"--screenshot={abs_png}",
        f"--window-size={size},{size}",
        "--default-background-color=00000000",
        f"file:///{abs_html.replace(os.sep, '/')}"
    ]
    subprocess.run(cmd, check=True)
    if os.path.exists(temp_html):
        os.remove(temp_html)
    print(f"Rendered {out_png} via Chromium engine.")

# Render 512x512 master images
render_svg_to_png(GUEST_SVG, "master_guest.png", 512)
render_svg_to_png(ADMIN_SVG, "master_admin.png", 512)

# Generate multi-res PNGs and ICOs with Lanczos resampling
def generate_derivatives(master_png, prefix):
    master = Image.open(master_png).convert("RGBA")
    
    p32 = master.resize((32, 32), Image.Resampling.LANCZOS)
    p64 = master.resize((64, 64), Image.Resampling.LANCZOS)
    p180 = master.resize((180, 180), Image.Resampling.LANCZOS)
    p512 = master.resize((512, 512), Image.Resampling.LANCZOS)
    
    p32.save(f"favicon-{prefix}-32.png")
    p64.save(f"favicon-{prefix}.png")
    p180.save(f"apple-touch-icon-{prefix}.png")
    p512.save(f"icon-{prefix}-512.png")
    
    # ICO file
    ico_name = "favicon.ico" if prefix == "guest" else f"favicon-{prefix}.ico"
    master.save(ico_name, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print(f"Generated derivatives for {prefix}.")

generate_derivatives("master_guest.png", "guest")
generate_derivatives("master_admin.png", "admin")

# Cleanup master PNGs
if os.path.exists("master_guest.png"): os.remove("master_guest.png")
if os.path.exists("master_admin.png"): os.remove("master_admin.png")

# Compute base64
b64_guest = base64.b64encode(GUEST_SVG.encode("utf-8")).decode("ascii")
b64_admin = base64.b64encode(ADMIN_SVG.encode("utf-8")).decode("ascii")

with open("favicons_b64.txt", "w", encoding="utf-8") as f:
    f.write(f"GUEST:\n{b64_guest}\n\nADMIN:\n{b64_admin}\n")

print("DONE! All exact favicons generated.")
