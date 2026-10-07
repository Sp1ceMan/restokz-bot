import base64
from PIL import Image, ImageDraw

def create_guest_image(target_size):
    S = 256
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    
    pad = 8
    r = 58
    # Dark squircle
    draw.rounded_rectangle([pad, pad, S - pad, S - pad], radius=r, fill=(24, 20, 17, 255), outline=(196, 156, 109, 180), width=9)
    
    # Book
    cx = S // 2
    gold = (223, 200, 167, 255)
    lw = 16
    
    top_spine = 68
    bot_spine = 188
    left_x = cx - 62
    
    # Center spine line
    draw.line([(cx, top_spine + 14), (cx, bot_spine)], fill=gold, width=lw)
    
    # Left page outline
    draw.line([(left_x, top_spine + 8), (left_x, bot_spine)], fill=gold, width=lw)
    # Left page top curve
    draw.line([(left_x, top_spine + 8), (cx - 28, top_spine - 4)], fill=gold, width=lw)
    draw.line([(cx - 28, top_spine - 4), (cx, top_spine + 14)], fill=gold, width=lw)
    # Left page bot curve
    draw.line([(left_x, bot_spine), (cx - 28, bot_spine - 12)], fill=gold, width=lw)
    draw.line([(cx - 28, bot_spine - 12), (cx, bot_spine)], fill=gold, width=lw)
    
    # Right page
    right_x = cx + 62
    draw.line([(right_x, top_spine + 8), (right_x, bot_spine)], fill=gold, width=lw)
    # Right page top curve
    draw.line([(cx, top_spine + 14), (cx + 28, top_spine - 4)], fill=gold, width=lw)
    draw.line([(cx + 28, top_spine - 4), (right_x, top_spine + 8)], fill=gold, width=lw)
    # Right page bot curve
    draw.line([(cx, bot_spine), (cx + 28, bot_spine - 12)], fill=gold, width=lw)
    draw.line([(cx + 28, bot_spine - 12), (right_x, bot_spine)], fill=gold, width=lw)
    
    return im.resize((target_size, target_size), Image.Resampling.LANCZOS)

def create_admin_image(target_size):
    S = 256
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    
    pad = 8
    r = 58
    # Gold squircle
    draw.rounded_rectangle([pad, pad, S - pad, S - pad], radius=r, fill=(196, 156, 109, 255), outline=(142, 103, 55, 255), width=9)
    
    dark = (17, 14, 12, 255)
    cx = S // 2
    lw = 18
    
    # Top plate
    draw.line([(cx - 36, 56), (cx + 36, 56)], fill=dark, width=lw)
    # Top stem
    draw.line([(cx, 56), (cx, 96)], fill=dark, width=lw)
    
    # Dome arc
    base_y = 196
    dome_r = 74
    draw.arc([cx - dome_r, base_y - dome_r * 2, cx + dome_r, base_y], start=180, end=0, fill=dark, width=lw)
    
    # Base bar
    bw = 92
    draw.line([(cx - bw, base_y), (cx + bw, base_y)], fill=dark, width=lw)
    
    return im.resize((target_size, target_size), Image.Resampling.LANCZOS)

# 1. Save PNG files
g16 = create_guest_image(16)
g32 = create_guest_image(32)
g48 = create_guest_image(48)
g64 = create_guest_image(64)
g180 = create_guest_image(180)
g512 = create_guest_image(512)

a16 = create_admin_image(16)
a32 = create_admin_image(32)
a48 = create_admin_image(48)
a64 = create_admin_image(64)
a180 = create_admin_image(180)
a512 = create_admin_image(512)

g32.save("favicon-guest-32.png")
g64.save("favicon-guest.png")
g180.save("apple-touch-icon-guest.png")
g512.save("icon-guest-512.png")

a32.save("favicon-admin-32.png")
a64.save("favicon-admin.png")
a180.save("apple-touch-icon-admin.png")
a512.save("icon-admin-512.png")

# Save multi-size favicon.ico
g32.save("favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
a32.save("favicon-admin.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])

# 2. Save SVG files
svg_guest = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="gBg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#241d18"/>
      <stop offset="100%" stop-color="#120e0c"/>
    </linearGradient>
    <linearGradient id="gGold" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#dfc8a7"/>
      <stop offset="100%" stop-color="#c49c6d"/>
    </linearGradient>
  </defs>
  <rect x="2" y="2" width="60" height="60" rx="16" fill="url(#gBg)" stroke="#c49c6d" stroke-width="2.5" stroke-opacity="0.6"/>
  <path d="M32 17v28M32 17C28.5 14.5 23.5 14 16 14c-3 0-5 .5-7 1v28c2-.5 4-1 7-1 7.5 0 12.5 1.5 16 3m0-31c3.5-2.5 8.5-3 16-3 3 0 5 .5 7 1v28c-2-.5-4-1-7-1-7.5 0-12.5 1.5-16 3" fill="none" stroke="url(#gGold)" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""

svg_admin = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="aGold" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#dfc8a7"/>
      <stop offset="50%" stop-color="#c49c6d"/>
      <stop offset="100%" stop-color="#9e733e"/>
    </linearGradient>
  </defs>
  <rect x="2" y="2" width="60" height="60" rx="16" fill="url(#aGold)" stroke="#785322" stroke-width="2"/>
  <path d="M25 15h14" stroke="#110e0c" stroke-width="4.5" stroke-linecap="round"/>
  <path d="M32 15v8" stroke="#110e0c" stroke-width="4.5" stroke-linecap="round"/>
  <path d="M15 47a17 17 0 0134 0" fill="none" stroke="#110e0c" stroke-width="5" stroke-linecap="round"/>
  <path d="M10 47h44" stroke="#110e0c" stroke-width="5" stroke-linecap="round"/>
</svg>"""

with open("favicon-guest.svg", "w", encoding="utf-8") as f:
    f.write(svg_guest)

with open("favicon-admin.svg", "w", encoding="utf-8") as f:
    f.write(svg_admin)

print("All favicon assets generated successfully!")
