import math, random, sys, json
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card import fit_lines, LORA, POP, POPL

W, H = 1080, 1350
def lerp(a, b, t):
    t = max(0, min(1, t)); return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))

def sky(stops):
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        for i in range(len(stops)-1):
            p0, c0 = stops[i]; p1, c1 = stops[i+1]
            if p0 <= t <= p1:
                d.line([(0, y), (W, y)], fill=lerp(c0, c1, (t-p0)/(p1-p0))); break
    return img

def glow(img, cx, cy, r, color, strength=120):
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).ellipse((cx-r*4, cy-r*4, cx+r*4, cy+r*4), fill=strength)
    g = g.filter(ImageFilter.GaussianBlur(r*1.6))
    return Image.composite(Image.new("RGB", (W, H), color), img, g)

def disc(img, cx, cy, r, color):
    ImageDraw.Draw(img).ellipse((cx-r, cy-r, cx+r, cy+r), fill=color); return img

def ridge_pts(base, amp, seed, rough=5, step=8, scale=180):
    rnd = random.Random(seed); ph = [rnd.random()*6.28 for _ in range(rough)]
    pts = [(0, H)]
    for x in range(0, W+step, step):
        y = base - sum(amp/(k+1)*math.sin(x/(scale/(k+1))+ph[k]) for k in range(rough))
        pts.append((x, y))
    pts.append((W, H)); return pts

def ridge(img, base, amp, color, seed, mist=0, mist_col=(255, 240, 225), **kw):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).polygon(ridge_pts(base, amp, seed, **kw), fill=color+(255,))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    if mist:
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).rectangle((0, base-amp*0.3, W, base+amp*1.2), fill=mist)
        m = m.filter(ImageFilter.GaussianBlur(60))
        img = Image.composite(Image.new("RGB", (W, H), mist_col), img, m)
    return img

def stars(img, n, seed, ymax):
    rnd = random.Random(seed); d = ImageDraw.Draw(img)
    for _ in range(n):
        x, y = rnd.random()*W, rnd.random()*ymax
        r = rnd.choice([1, 1, 1, 2, 2, 3]); b = rnd.randint(170, 255)
        d.ellipse((x-r, y-r, x+r, y+r), fill=(b, b, min(255, b+10)))
    return img

def pine(d, x, base, h, color):
    w = h*0.32
    for k in range(4):
        top = base - h + k*h*0.18; bw = w*(0.45+k*0.2)
        d.polygon([(x, top), (x-bw, top+h*0.38), (x+bw, top+h*0.38)], fill=color)
    d.rectangle((x-w*0.06, base-h*0.08, x+w*0.06, base), fill=color)

# ---------- scenes ----------
def s_mountains(seed, pal):
    a, b, c, m1, m2, m3 = pal
    img = sky([(0, a), (0.6, b), (1, c)])
    img = glow(img, W*0.68, H*0.56, 46, c); img = disc(img, W*0.68, H*0.56, 44, lerp(c, (255, 252, 240), .7))
    img = ridge(img, H*0.62, 110, m1, seed, mist=70)
    img = ridge(img, H*0.73, 90, m2, seed+1, mist=45)
    return ridge(img, H*0.85, 70, m3, seed+2)

def s_sea(seed, pal):
    a, b, c, sea, sea2, _ = pal
    img = sky([(0, a), (0.55, b), (0.66, c), (1, c)])
    hor = int(H*0.66)
    img = glow(img, W*0.5, hor-30, 50, c, 140); img = disc(img, W*0.5, hor-20, 52, lerp(c, (255, 250, 235), .7))
    d = ImageDraw.Draw(img)
    for y in range(hor, H):
        t = (y-hor)/(H-hor); d.line([(0, y), (W, y)], fill=lerp(sea, sea2, t))
    rnd = random.Random(seed)
    for k in range(70):
        y = hor + 6 + (k**1.6)*1.4
        if y > H: break
        wdt = 30 + rnd.random()*120*(1-(y-hor)/(H-hor)*0.3)
        x = W*0.5 + rnd.uniform(-1, 1)*(40+(y-hor)*0.5)
        d.line([(x-wdt/2, y), (x+wdt/2, y)], fill=lerp(c, (255, 250, 235), .5), width=2)
    return img

def s_night(seed, pal):
    a, b, c, h1, h2, _ = pal
    img = sky([(0, a), (0.7, b), (1, c)])
    img = stars(img, 420, seed, H*0.75)
    img = glow(img, W*0.76, H*0.64, 30, (240, 236, 220), 60); img = disc(img, W*0.76, H*0.64, 34, (244, 240, 226))
    img = ridge(img, H*0.80, 60, h1, seed, scale=320)
    return ridge(img, H*0.90, 45, h2, seed+3, scale=260)

def s_field(seed, pal):
    a, b, c, g1, g2, fl = pal
    img = sky([(0, a), (0.55, b), (1, c)])
    img = glow(img, W*0.3, H*0.58, 50, c, 130)
    img = ridge(img, H*0.68, 50, g1, seed, scale=420, mist=60)
    img = ridge(img, H*0.78, 40, g2, seed+1, scale=380)
    d = ImageDraw.Draw(img); rnd = random.Random(seed)
    for _ in range(900):
        y = rnd.uniform(H*0.80, H); depth = (y-H*0.8)/(H*0.2)
        x = rnd.random()*W; r = 2 + depth*7
        col = rnd.choice(fl)
        d.ellipse((x-r, y-r, x+r, y+r), fill=col)
    return img

def s_road(seed, pal):
    a, b, c, g1, g2, rd = pal
    img = sky([(0, a), (0.6, b), (1, c)])
    hor = H*0.66
    img = glow(img, W*0.5, hor-10, 46, c, 150); img = disc(img, W*0.5, hor-8, 40, lerp(c, (255, 252, 240), .7))
    img = ridge(img, hor+10, 40, g1, seed, scale=360, mist=60)
    d = ImageDraw.Draw(img)
    d.rectangle((0, hor+20, W, H), fill=g2)
    d.polygon([(W*0.49, hor+20), (W*0.51, hor+20), (W*0.86, H), (W*0.14, H)], fill=rd)
    for k in range(10):
        t0 = (k/10)**1.8; t1 = ((k+0.5)/10)**1.8
        y0 = hor+20 + (H-hor-20)*t0; y1 = hor+20 + (H-hor-20)*t1
        w0 = 2 + 10*t0; w1 = 2 + 10*t1
        d.polygon([(W/2-w0, y0), (W/2+w0, y0), (W/2+w1, y1), (W/2-w1, y1)], fill=lerp(c, (255, 250, 230), .5))
    return img

def s_forest(seed, pal):
    a, b, c, t1, t2, t3 = pal
    img = sky([(0, a), (0.6, b), (1, c)])
    img = glow(img, W*0.6, H*0.5, 60, c, 120)
    rnd = random.Random(seed)
    for layer, (col, base, hmin, hmax, n, mist) in enumerate([(t1, H*0.70, 160, 230, 26, 90), (t2, H*0.82, 220, 320, 18, 60), (t3, H*0.98, 320, 460, 10, 0)]):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        d.rectangle((0, base-10, W, H), fill=col+(255,))
        for i in range(n):
            x = (i+rnd.random()*0.6)/n*W*1.08 - 30
            pine(d, x, base, rnd.uniform(hmin, hmax), col+(255,))
        img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
        if mist:
            m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rectangle((0, base-60, W, base+80), fill=mist)
            img = Image.composite(Image.new("RGB", (W, H), lerp(c, (255, 255, 255), .4)), img, m.filter(ImageFilter.GaussianBlur(50)))
    return img

def s_lake(seed, pal):
    a, b, c, m1, m2, water = pal
    hor = int(H*0.70)
    top = sky([(0, a), (0.6, b), (1, c)])
    top = glow(top, W*0.62, H*0.52, 40, c, 120); top = disc(top, W*0.62, H*0.52, 36, lerp(c, (255, 252, 240), .7))
    top = ridge(top, hor-60, 120, m1, seed, mist=50)
    top = ridge(top, hor, 60, m2, seed+1, scale=300)
    upper = top.crop((0, 0, W, hor))
    refl = upper.transpose(Image.FLIP_TOP_BOTTOM).resize((W, H-hor))
    refl = Image.blend(refl, Image.new("RGB", refl.size, water), 0.45).filter(ImageFilter.GaussianBlur(3))
    img = top.copy(); img.paste(refl, (0, hor))
    d = ImageDraw.Draw(img); rnd = random.Random(seed)
    for _ in range(60):
        y = rnd.uniform(hor+8, H); x = rnd.random()*W; w = rnd.uniform(20, 90)
        d.line([(x, y), (x+w, y)], fill=lerp(water, (255, 255, 255), .35), width=1)
    return img

SCENES = {"mountains": s_mountains, "sea": s_sea, "night": s_night, "field": s_field,
          "road": s_road, "forest": s_forest, "lake": s_lake}

PALS = {
 "dawn":   [(34, 44, 80), (214, 140, 120), (250, 205, 150), (126, 98, 120), (82, 66, 92), (44, 38, 56)],
 "golden": [(60, 80, 120), (236, 170, 110), (255, 220, 160), (150, 110, 90), (96, 70, 64), (52, 40, 40)],
 "sea":    [(26, 50, 90), (150, 170, 200), (250, 196, 150), (54, 92, 130), (20, 40, 70), None],
 "seadusk":[(40, 30, 70), (200, 110, 130), (255, 170, 120), (70, 60, 110), (24, 22, 48), None],
 "night":  [(8, 12, 32), (24, 40, 80), (60, 70, 110), (18, 24, 44), (8, 10, 22), None],
 "nightb": [(14, 10, 40), (44, 30, 90), (96, 70, 130), (26, 20, 50), (10, 8, 24), None],
 "field":  [(110, 160, 210), (210, 220, 210), (250, 230, 190), (120, 150, 90), (70, 110, 60), [(240, 200, 80), (250, 250, 240), (230, 120, 140), (200, 160, 230)]],
 "fieldw": [(90, 110, 170), (240, 180, 150), (255, 220, 170), (150, 140, 90), (96, 110, 60), [(250, 210, 90), (255, 240, 220), (240, 140, 110)]],
 "road":   [(50, 70, 120), (230, 160, 120), (255, 214, 160), (110, 90, 100), (70, 66, 60), (46, 44, 50)],
 "forest": [(40, 70, 90), (150, 190, 180), (230, 230, 200), (90, 120, 110), (52, 80, 70), (22, 40, 34)],
 "lake":   [(60, 90, 140), (180, 190, 210), (250, 220, 180), (90, 100, 130), (50, 60, 80), (60, 90, 120)],
 "lakep":  [(70, 60, 110), (220, 160, 170), (255, 210, 180), (120, 100, 130), (70, 60, 90), (90, 80, 120)],
}

def overlay(img, theme, phrase, ref, out, dark_text=False):
    shade = Image.new("L", (W, H), 0); sd = ImageDraw.Draw(shade)
    for y in range(H):
        sd.line([(0, y), (W, y)], fill=int(165*max(0, 1-y/(H*0.72))))
    img = Image.composite(Image.new("RGB", (W, H), (12, 14, 28)), img, shade)
    bot = Image.new("L", (W, H), 0); bd = ImageDraw.Draw(bot)
    for y in range(int(H*0.88), H):
        bd.line([(0, y), (W, y)], fill=int(120*(y-H*0.88)/(H*0.12)))
    img = Image.composite(Image.new("RGB", (W, H), (10, 10, 18)), img, bot)
    d = ImageDraw.Draw(img); acc = (246, 214, 160)
    d.text((W/2, 170), " ".join(theme.upper()), font=ImageFont.truetype(POP, 34), fill=acc, anchor="mm")
    d.line([(W/2-60, 215), (W/2+60, 215)], fill=acc, width=3)
    f, lines, lh = fit_lines(d, phrase, LORA, W-220, 72, 44)
    y = 300
    for ln in lines:
        d.text((W/2+2, y+3), ln, font=f, fill=(0, 0, 0), anchor="mm")
        d.text((W/2, y), ln, font=f, fill=(252, 248, 240), anchor="mm"); y += lh
    d.text((W/2, y+40), ref, font=ImageFont.truetype(POPL, 38), fill=acc, anchor="mm")
    d.text((W/2, H-70), "@focoefenoprocesso", font=ImageFont.truetype(POPL, 30), fill=(240, 236, 228), anchor="mm")
    img.save(out, "JPEG", quality=90)

# theme -> list of (scene, palette) options, rotated so neighbours differ
PLAN = {
 "Fé": [("road", "road"), ("night", "night"), ("lake", "lake")],
 "Perseverança": [("field", "field"), ("mountains", "golden"), ("forest", "forest")],
 "Resiliência": [("mountains", "dawn"), ("forest", "forest")],
 "Foco": [("road", "road"), ("mountains", "golden")],
 "Amor": [("field", "fieldw"), ("lake", "lakep")],
 "Paz": [("sea", "sea"), ("lake", "lake")],
 "Riquezas": [("night", "nightb"), ("sea", "seadusk"), ("field", "field")],
 "Bênçãos": [("mountains", "dawn"), ("lake", "lakep"), ("sea", "seadusk")],
}

if __name__ == "__main__":
    data = json.load(open(sys.argv[1])); outdir = sys.argv[2]
    used = {}; prev = None; log = []
    for i, p in enumerate(data):
        opts = PLAN[p["tema"]]; k = used.get(p["tema"], 0)
        choice = opts[k % len(opts)]
        if choice[0] == prev and len(opts) > 1:
            k += 1; choice = opts[k % len(opts)]
        used[p["tema"]] = k + 1; prev = choice[0]
        img = SCENES[choice[0]](i*7+3, PALS[choice[1]])
        overlay(img, p["tema"], p["frase"], p["ref"], f"{outdir}/n{i+1:02d}.jpg")
        log.append(f"n{i+1:02d} {p['tema']} {choice}")
    print("\n".join(log))
