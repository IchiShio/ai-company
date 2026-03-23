from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1280, 670
OUT = os.path.join(os.path.dirname(__file__), "thumbnail.png")

img = Image.new("RGB", (W, H))
draw = ImageDraw.Draw(img)

# Dark gradient background
for y in range(H):
    ratio = y / H
    r = int(15 + 15 * ratio * 0.3)
    g = int(23 + 18 * ratio * 0.3)
    b = int(42 + 17 * ratio * 0.3)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# Decorative circles
overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ov_draw = ImageDraw.Draw(overlay)
ov_draw.ellipse([W-300, -150, W+100, 250], fill=(59, 130, 246, 25))
ov_draw.ellipse([-150, H-250, 250, H+50], fill=(139, 92, 246, 25))
ov_draw.ellipse([350, 100, 600, 350], fill=(6, 182, 212, 18))
bg_rgba = img.convert("RGBA")
composite = Image.alpha_composite(bg_rgba, overlay)
img = composite.convert("RGB")
draw = ImageDraw.Draw(img)

# Font loading
def load_font(size):
    paths = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for fp in paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except:
                continue
    return ImageFont.load_default()

def load_font_bold(size):
    paths = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    ]
    for fp in paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except:
                continue
    return load_font(size)

def center_text(draw, y, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    draw.text((x, y), text, fill=fill, font=font)
    return tw

# Badge
badge_font = load_font(20)
badge_text = "1,099 QUESTIONS DESIGNED"
bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
tw = bbox[2] - bbox[0]
bw = tw + 52
bh = 42
bx = (W - bw) // 2
by = 75
draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=21, fill=(59, 130, 246))
draw.text(((W - tw) // 2, by + 9), badge_text, fill="white", font=badge_font)

# Title
title_font = load_font_bold(54)
accent_font = load_font_bold(62)

center_text(draw, 155, "リスニング教材を設計してわかった", title_font, (241, 245, 249))
center_text(draw, 230, "英語が聞き取れる人の", title_font, (241, 245, 249))
center_text(draw, 315, "5つの共通点", accent_font, (251, 191, 36))

# Axis tags
axes = ["Speed", "Reduction", "Vocab", "Context", "Distractor"]
axis_font = load_font(20)
tag_w = 140
tag_h = 48
gap = 18
total_w = len(axes) * tag_w + (len(axes) - 1) * gap
start_x = (W - total_w) // 2
tag_y = 420

for i, axis in enumerate(axes):
    tx = start_x + i * (tag_w + gap)
    # Tag background
    draw.rounded_rectangle([tx, tag_y, tx + tag_w, tag_y + tag_h], radius=12,
                           fill=(30, 58, 108))
    # Border
    draw.rounded_rectangle([tx, tag_y, tx + tag_w, tag_y + tag_h], radius=12,
                           outline=(59, 130, 246), width=1)
    # Text centered
    bbox = draw.textbbox((0, 0), axis, font=axis_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((tx + (tag_w - tw) // 2, tag_y + (tag_h - th) // 2 - 2), axis,
              fill=(147, 197, 253), font=axis_font)

# Footer
footer_font = load_font(20)
center_text(draw, 510, "@ichi_eigo  |  native-real.com", footer_font, (148, 163, 184))

# Subtle bottom accent line
draw.rectangle([0, H-4, W, H], fill=(59, 130, 246))

img.save(OUT, "PNG", quality=95)
print(f"Saved: {OUT}")
print(f"Size: {os.path.getsize(OUT)} bytes")
