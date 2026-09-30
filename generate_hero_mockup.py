import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_hero_dual_mockup():
    assets_dir = r'd:\bot\presentation_assets'
    admin_path = os.path.join(assets_dir, 'admin_terminal_mobile.png')
    guest_path = os.path.join(assets_dir, 'guest_catalog_mobile.png')
    
    if not os.path.exists(admin_path) or not os.path.exists(guest_path):
        print("Missing source assets!")
        return
        
    img_admin = Image.open(admin_path).convert("RGBA")
    img_guest = Image.open(guest_path).convert("RGBA")
    
    # Target dimensions
    screen_w, screen_h = 412, 892
    bezel = 10
    phone_w = screen_w + bezel * 2   # 432
    phone_h = screen_h + bezel * 2   # 912
    
    gap = 44
    margin_x = 40
    margin_top = 70
    margin_bottom = 38
    
    total_w = margin_x * 2 + phone_w * 2 + gap  # 40*2 + 432*2 + 44 = 988
    total_h = margin_top + phone_h + margin_bottom # 70 + 912 + 38 = 1020
    
    # Background color matches presentation card: #14171E
    canvas = Image.new("RGBA", (total_w, total_h), (20, 23, 30, 255))
    
    try:
        font_pill = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 13)
    except:
        try:
            font_pill = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 13)
        except:
            font_pill = ImageFont.load_default()

    def render_phone(screen_img, origin_x, origin_y, title_text):
        # 1. Subtle drop shadow
        shadow_layer = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_draw.rounded_rectangle(
            [origin_x - 6, origin_y - 2, origin_x + phone_w + 6, origin_y + phone_h + 16],
            radius=40,
            fill=(0, 0, 0, 180)
        )
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(16))
        canvas.alpha_composite(shadow_layer)
        
        # 2. Outer phone frame (Sleek dark titanium + luxury gold rim)
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle(
            [origin_x, origin_y, origin_x + phone_w, origin_y + phone_h],
            radius=38,
            fill=(17, 19, 24, 255),
            outline=(197, 168, 128, 220), # Luxury gold border
            width=2
        )
        
        # Inner titanium chamfer line
        draw.rounded_rectangle(
            [origin_x + 2, origin_y + 2, origin_x + phone_w - 2, origin_y + phone_h - 2],
            radius=36,
            outline=(45, 52, 65, 255),
            width=1
        )
        
        # 3. Screen mask (rounded corners fitting perfectly inside the bezel)
        mask = Image.new("L", (screen_w, screen_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, screen_w, screen_h], radius=28, fill=255)
        
        screen_x = origin_x + bezel
        screen_y = origin_y + bezel
        
        canvas.paste(screen_img, (screen_x, screen_y), mask)
        
        # 4. Subtle inner screen shadow / border
        draw.rounded_rectangle(
            [screen_x - 1, screen_y - 1, screen_x + screen_w + 1, screen_y + screen_h + 1],
            radius=29,
            outline=(10, 12, 16, 255),
            width=1
        )
        
        # 5. Title pill above the phone
        pill_w = 270
        pill_h = 34
        pill_x = origin_x + (phone_w - pill_w) // 2
        pill_y = origin_y - 48
        
        # Pill body
        draw.rounded_rectangle(
            [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
            radius=17,
            fill=(26, 30, 39, 255),
            outline=(197, 168, 128, 180),
            width=1
        )
        
        # Pill text
        bbox = draw.textbbox((0, 0), title_text, font=font_pill)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = pill_x + (pill_w - text_w) // 2
        text_y = pill_y + (pill_h - text_h) // 2 - 1
        draw.text((text_x, text_y), title_text, fill=(229, 213, 192, 255), font=font_pill)

    # Render Left Phone: Terminal Hostess PRO
    x_left = margin_x
    y_common = margin_top
    render_phone(img_admin, x_left, y_common, "ТЕРМИНАЛ ХОСТЕС RESTOKZ PRO")
    
    # Render Right Phone: Guest Mini App
    x_right = margin_x + phone_w + gap
    render_phone(img_guest, x_right, y_common, "ГОСТЕВОЙ TELEGRAM MINI APP")
    
    out_file = os.path.join(assets_dir, 'hero_dual_mockup.png')
    canvas.save(out_file, "PNG", quality=95)
    print(f"Generated clean straight hero mockup at: {out_file} ({canvas.size})")

if __name__ == '__main__':
    create_hero_dual_mockup()
