import sys, json, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1350
LORA = "/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf"
POP = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
POPL = "/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf"

PALETTES = [
    ((28, 36, 52), (74, 58, 48), (232, 196, 140)),   # noite -> terra, dourado
    ((22, 48, 46), (60, 84, 62), (226, 210, 160)),   # verde profundo
    ((44, 30, 46), (98, 60, 58), (240, 190, 150)),   # vinho, pessego
    ((18, 32, 58), (46, 72, 104), (210, 222, 240)),  # azul, prata
]

def gradient(c1, c2):
    img = Image.new("RGB", (W, H), c1)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    # soft light glow
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((W*0.15, -H*0.25, W*1.1, H*0.45), fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    light = Image.new("RGB", (W, H), (255, 236, 200))
    return Image.composite(light, img, glow)

def fit_lines(draw, text, font_path, max_w, start, min_size):
    size = start
    while size >= min_size:
        f = ImageFont.truetype(font_path, size)
        try:
            f.set_variation_by_axes([600])
        except Exception:
            pass
        words, lines, cur = text.split(), [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if draw.textlength(test, font=f) <= max_w:
                cur = test
            else:
                lines.append(cur); cur = w
        lines.append(cur)
        lh = int(size * 1.32)
        if lh * len(lines) <= H * 0.48:
            return f, lines, lh
        size -= 4
    return f, lines, lh

def make(n, theme, phrase, ref, out):
    c1, c2, acc = PALETTES[n % len(PALETTES)]
    img = gradient(c1, c2)
    d = ImageDraw.Draw(img)
    pad = 110
    # theme label
    tf = ImageFont.truetype(POP, 34)
    label = theme.upper()
    spaced = " ".join(label)
    d.text((W/2, 250), spaced, font=tf, fill=acc, anchor="mm")
    d.line([(W/2-60, 300), (W/2+60, 300)], fill=acc, width=3)
    # phrase
    f, lines, lh = fit_lines(d, phrase, LORA, W - 2*pad, 76, 44)
    total = lh * len(lines)
    y = H/2 - total/2 + 40
    for ln in lines:
        d.text((W/2, y), ln, font=f, fill=(250, 246, 238), anchor="mm")
        y += lh
    # reference
    rf = ImageFont.truetype(POPL, 38)
    d.text((W/2, y + 50), ref, font=rf, fill=acc, anchor="mm")
    # handle
    hf = ImageFont.truetype(POPL, 30)
    d.text((W/2, H - 90), "@focoefenoprocesso", font=hf, fill=(235, 228, 215), anchor="mm")
    img.save(out, "JPEG", quality=92)

if __name__ == "__main__":
    data = json.load(open(sys.argv[1]))
    outdir = sys.argv[2]
    for i, p in enumerate(data):
        make(i, p["tema"], p["frase"], p["ref"], f"{outdir}/post{i+1:02d}.jpg")
    print("ok", len(data))
