"""Ilustraciones de producto dibujadas con Pillow (sin fotos ni servicios externos).

`render(category, model, index)` devuelve un JPEG de 600x600: fondo de estudio, sombra en el
piso y un mueble de estilo plano con volumen suave. Cada modelo cambia forma y color.
"""
import io

from PIL import Image, ImageDraw, ImageFilter

S = 2  # supersampling: se dibuja a 1200px y se reduce a 600px
SIZE = 600
FLOOR = 470

FABRICS = ['#7C8B6F', '#C27A5A', '#3E5468', '#CBB89D', '#55565A', '#D4A437', '#D9A5A0', '#3F5E4E']
WOODS = ['#C9A27A', '#7A5638', '#D8C3A5', '#3A3430', '#A9794F', '#B88E5C', '#8C6A48', '#E0CBA8']
BACKGROUNDS = [('#F5F2EC', '#E4DED3'), ('#F1F3F2', '#DFE3E1'), ('#F6F0E8', '#E8DCCB')]


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(color, target, amount):
    """Acerca `color` (hex o tupla) a `target` (0 = negro, 255 = blanco) en la proporción `amount`."""
    base = rgb(color) if isinstance(color, str) else color
    return tuple(round(c + (target - c) * amount) for c in base)


class Scene:
    def __init__(self, index):
        top, bottom = (rgb(h) for h in BACKGROUNDS[index % len(BACKGROUNDS)])
        n = SIZE * S
        self.img = Image.new('RGB', (n, n))
        d = ImageDraw.Draw(self.img)
        for y in range(n):
            t = y / n
            d.line([(0, y), (n, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))
        self.d = ImageDraw.Draw(self.img)

    def _s(self, v):
        return [x * S for x in v] if isinstance(v, (list, tuple)) else v * S

    def shadow(self, cx, cy, rx, ry, alpha=95, blur=14):
        layer = Image.new('L', self.img.size, 0)
        ImageDraw.Draw(layer).ellipse(self._s([cx - rx, cy - ry, cx + rx, cy + ry]), fill=alpha)
        layer = layer.filter(ImageFilter.GaussianBlur(blur * S))
        self.img.paste(Image.new('RGB', self.img.size, (60, 50, 40)), mask=layer)
        self.d = ImageDraw.Draw(self.img)

    def glow(self, cx, cy, r, color=(255, 214, 140), alpha=150):
        layer = Image.new('L', self.img.size, 0)
        ImageDraw.Draw(layer).ellipse(self._s([cx - r, cy - r, cx + r, cy + r]), fill=alpha)
        layer = layer.filter(ImageFilter.GaussianBlur(r * S / 2.2))
        self.img.paste(Image.new('RGB', self.img.size, color), mask=layer)
        self.d = ImageDraw.Draw(self.img)

    def rr(self, box, r, fill, outline=None):
        self.d.rounded_rectangle(self._s(box), radius=r * S, fill=fill, outline=outline, width=S)

    def ell(self, box, fill, outline=None):
        self.d.ellipse(self._s(box), fill=fill, outline=outline, width=S)

    def poly(self, pts, fill):
        self.d.polygon([(x * S, y * S) for x, y in pts], fill=fill)

    def line(self, pts, fill, width=4):
        self.d.line([(x * S, y * S) for x, y in pts], fill=fill, width=int(width * S), joint='curve')

    def arc(self, box, start, end, fill, width=4):
        self.d.arc(self._s(box), start, end, fill=fill, width=int(width * S))

    def jpeg(self):
        out = io.BytesIO()
        self.img.crop((20 * S, 30 * S, 580 * S, 590 * S)).resize((SIZE, SIZE), Image.LANCZOS).save(out, 'JPEG', quality=90)
        return out.getvalue()


def legs(sc, xs, top, bottom, wood, w=9, taper=3):
    for x in xs:
        sc.poly([(x - w / 2, top), (x + w / 2, top), (x + taper, bottom), (x - taper, bottom)], wood)


def sofa(sc, model, i):
    fab, wood = FABRICS[i % 8], WOODS[(i + 3) % 8]
    seats = 3 if model in ('Cloud', 'Milano', 'Chesterfield', 'Oslo') else 2
    arms = model != 'Lounge'
    w = 130 * seats + (110 if arms else 60)
    l, r = 300 - w / 2, 300 + w / 2
    dark, light = mix(fab, 0, .22), mix(fab, 255, .14)
    sc.shadow(300, FLOOR + 6, w / 2 + 10, 16)
    legs(sc, [l + 22, r - 22], 440, FLOOR, wood, 12, 5)
    sc.rr([l + (40 if arms else 10), 240, r - (40 if arms else 10), 380], 34, fab)
    sc.rr([l + (40 if arms else 10), 240, r - (40 if arms else 10), 262], 20, light)
    cw = (w - (110 if arms else 40)) / seats
    for k in range(seats):
        x0 = l + (55 if arms else 20) + k * cw
        sc.rr([x0, 340, x0 + cw - 6, 420], 18, light if k % 2 == 0 else mix(fab, 255, .08))
    sc.rr([l + (8 if arms else 0), 410, r - (8 if arms else 0), 442], 10, dark)
    if arms:
        round_arm = model in ('Chesterfield', 'Velvet')
        for x0 in (l, r - 62):
            sc.rr([x0, 285 if not round_arm else 270, x0 + 62, 430], 28 if round_arm else 22, dark)
            sc.rr([x0 + 6, 285 if not round_arm else 270, x0 + 56, 300], 14, mix(fab, 0, .1))
    if model == 'Chesterfield':
        for row in range(2):
            for col in range(6):
                sc.ell([l + 70 + col * ((w - 140) / 5) - 3, 285 + row * 32 - 3, l + 70 + col * ((w - 140) / 5) + 3, 285 + row * 32 + 3], dark)
    if model == 'Modular':
        sc.rr([r - 10, 395, r + 85, 450], 14, light)
        sc.rr([r - 10, 440, r + 85, 452], 5, dark)


def chair(sc, model, i):
    fab, wood = FABRICS[i % 8], WOODS[i % 8]
    wood_dark = mix(wood, 0, .25)
    if model == 'Barstool':
        sc.shadow(300, FLOOR + 14, 90, 12)
        legs(sc, [250, 350], 300, FLOOR + 10, wood_dark, 8, 4)
        sc.line([(256, 400), (344, 400)], wood_dark, 6)
        sc.rr([225, 270, 375, 304], 16, fab)
        sc.rr([225, 270, 375, 282], 10, mix(fab, 255, .16))
        return
    if model == 'Rocking':
        sc.shadow(300, FLOOR + 6, 150, 12)
        sc.arc([140, 358, 460, 478], 15, 165, wood_dark, 12)
        legs(sc, [235, 365], 350, 468, wood_dark, 9, 6)
    else:
        sc.shadow(300, FLOOR + 6, 105, 13)
        legs(sc, [240, 360], 355, FLOOR, wood_dark, 10, 5)
        sc.poly([(226, 358), (234, 358), (212, FLOOR - 6), (204, FLOOR - 6)], mix(wood, 0, .35))
        sc.poly([(366, 358), (374, 358), (396, FLOOR - 6), (388, FLOOR - 6)], mix(wood, 0, .35))
    if model in ('Windsor', 'Oak'):
        sc.rr([232, 170, 368, 184], 6, wood)
        for x in range(246, 360, 22):
            sc.rr([x, 184, x + 8, 340], 4, wood)
        sc.rr([226, 170, 236, 340], 5, wood_dark)
        sc.rr([364, 170, 374, 340], 5, wood_dark)
    elif model in ('Bistro', 'Lounge'):
        sc.ell([226, 160, 374, 330], fab)
        sc.ell([240, 174, 360, 316], mix(fab, 255, .13))
    else:
        sc.rr([226, 160, 374, 340], 30, fab if model != 'Eames' else wood)
        sc.rr([238, 174, 362, 330], 24, mix(fab if model != 'Eames' else wood, 255, .12))
    sc.rr([214, 338, 386, 366], 14, fab if model not in ('Eames', 'Rocking') else wood)
    sc.rr([214, 338, 386, 350], 10, mix(fab if model not in ('Eames', 'Rocking') else wood, 255, .16))


def table(sc, model, i):
    wood = WOODS[(i + 1) % 8]
    dark, light = mix(wood, 0, .28), mix(wood, 255, .18)
    if model == 'Centro':
        sc.shadow(300, FLOOR - 40, 190, 18)
        sc.ell([110, 320, 490, 400], dark)
        sc.ell([110, 305, 490, 385], wood)
        sc.ell([130, 313, 470, 372], light)
        legs(sc, [185, 415], 380, FLOOR - 40, dark, 12, 6)
        legs(sc, [250, 350], 392, FLOOR - 30, mix(wood, 0, .4), 12, 6)
        return
    if model == 'Auxiliar':
        sc.shadow(300, FLOOR + 6, 110, 14)
        sc.rr([285, 310, 315, 460], 6, dark)
        sc.ell([200, 270, 400, 320], dark)
        sc.ell([200, 258, 400, 308], wood)
        sc.ell([215, 266, 385, 298], light)
        sc.ell([220, 452, 380, 478], dark)
        return
    narrow = model in ('Consola', 'Escritorio')
    top_y = 290 if model != 'Escritorio' else 270
    w = 340 if model != 'Comedor' else 420
    l, r = 300 - w / 2, 300 + w / 2
    sc.shadow(300, FLOOR + 6, w / 2 + 10, 14)
    if model == 'Plegable':
        sc.line([(l + 40, top_y + 20), (r - 70, FLOOR)], dark, 9)
        sc.line([(r - 40, top_y + 20), (l + 70, FLOOR)], dark, 9)
        sc.line([(l + 30, FLOOR), (r - 30, FLOOR)], dark, 6)
    else:
        legs(sc, [l + 26, r - 26], top_y + 22, FLOOR, dark if model != 'Nogal' else mix(wood, 0, .4), 14, 6)
    sc.rr([l + 14, top_y + 22, r - 14, top_y + 46], 4, dark)
    if model == 'Escritorio':
        sc.rr([r - 140, top_y + 22, r - 20, top_y + 150], 6, dark)
        for k in range(2):
            sc.rr([r - 132, top_y + 30 + k * 58, r - 28, top_y + 82 + k * 58], 5, wood)
            sc.rr([r - 94, top_y + 52 + k * 58, r - 66, top_y + 58 + k * 58], 3, dark)
    sc.rr([l, top_y, r, top_y + 26], 7, wood)
    sc.rr([l + 4, top_y, r - 4, top_y + 8], 5, light)
    if narrow and model == 'Consola':
        sc.rr([l + 30, top_y + 120, r - 30, top_y + 134], 4, wood)


def bed(sc, model, i):
    fab, wood = FABRICS[i % 8], WOODS[(i + 2) % 8]
    wide = {'King': 440, 'Queen': 390, 'Individual': 270, 'Litera': 290}.get(model, 350)
    l, r = 300 - wide / 2, 300 + wide / 2
    sc.shadow(300, FLOOR + 6, wide / 2 + 14, 15)
    duvet = FABRICS[(i + 4) % 8]
    if model == 'Litera':
        for x in (l - 8, r - 6):
            sc.rr([x, 150, x + 14, FLOOR], 5, wood)
        for y in (190, 330):
            sc.rr([l, y + 28, r, y + 56], 8, '#F2EEE8')
            sc.rr([l, y + 44, r, y + 70], 10, duvet)
            sc.rr([l + 8, y + 18, l + 80, y + 40], 10, '#FFFFFF')
        for k in range(4):
            sc.rr([r + 8, 220 + k * 62, r + 52, 230 + k * 62], 3, wood)
        sc.rr([r + 8, 210, r + 14, 440], 3, wood)
        sc.rr([r + 46, 210, r + 52, 440], 3, wood)
        return
    head_top = 160 if model != 'Nordic' else 190
    sc.rr([l - 6, head_top, r + 6, 340], 30 if model != 'Plataforma' else 8, fab)
    sc.rr([l + 6, head_top + 12, r - 6, head_top + 28], 12, mix(fab, 255, .16))
    if model in ('Canapé', 'King'):
        for row in range(2):
            for col in range(6):
                x = l + 40 + col * ((wide - 80) / 5)
                sc.ell([x - 4, head_top + 52 + row * 40 - 4, x + 4, head_top + 52 + row * 40 + 4], mix(fab, 0, .22))
    sc.rr([l, 328, r, 398], 14, '#F4F0EA')
    for x0, x1 in ((l + 16, l + 16 + wide * 0.38), (r - 16 - wide * 0.38, r - 16)):
        sc.rr([x0, 316, x1, 358], 16, '#FFFFFF', outline=mix('#FFFFFF', 0, .12))
    sc.rr([l, 352, r, 414], 14, duvet)
    sc.rr([l + 8, 352, r - 8, 366], 8, mix(duvet, 255, .2))
    sc.rr([l - 4, 408, r + 4, 452], 8, wood if model != 'Baúl' else mix(wood, 0, .15))
    if model == 'Baúl':
        sc.rr([l + 20, 418, r - 20, 444], 5, wood)
        sc.rr([300 - 18, 428, 300 + 18, 434], 3, mix(wood, 0, .4))
    legs(sc, [l + 8, r - 8], 450, FLOOR, mix(wood, 0, .3), 14, 8)


def storage(sc, model, i):
    wood, fab = WOODS[i % 8], FABRICS[(i + 1) % 8]
    dark, light = mix(wood, 0, .3), mix(wood, 255, .15)
    if model in ('Estantería', 'Biblioteca'):
        w, top = (260, 120) if model == 'Biblioteca' else (300, 160)
        l, r = 300 - w / 2, 300 + w / 2
        sc.shadow(300, FLOOR + 6, w / 2 + 12, 14)
        sc.rr([l, top, r, FLOOR], 6, dark)
        sc.rr([l + 10, top + 10, r - 10, FLOOR - 10], 4, light)
        shelves = 4 if model == 'Biblioteca' else 3
        gap = (FLOOR - top - 20) / shelves
        for s_ in range(shelves):
            y = top + 10 + (s_ + 1) * gap
            sc.rr([l + 8, y - 8, r - 8, y], 2, wood)
            x = l + 20
            k = 0
            while x < r - 40:
                bw = 14 + (k * 7) % 12
                bh = gap - 24 - (k * 11) % 26
                sc.rr([x, y - 8 - bh, x + bw, y - 8], 2, FABRICS[(k + s_ + i) % 8])
                x += bw + 3
                k += 1
        return
    if model in ('Cómoda', 'Cajonera'):
        w, top = (360, 260) if model == 'Cómoda' else (230, 170)
        rows = 3 if model == 'Cómoda' else 5
        l, r = 300 - w / 2, 300 + w / 2
        sc.shadow(300, FLOOR + 6, w / 2 + 10, 14)
        legs(sc, [l + 24, r - 24], FLOOR - 24, FLOOR, dark, 14, 8)
        sc.rr([l, top, r, FLOOR - 20], 8, wood)
        sc.rr([l + 4, top, r - 4, top + 12], 6, light)
        dh = (FLOOR - 20 - top - 22) / rows
        for k in range(rows):
            y = top + 14 + k * dh
            sc.rr([l + 14, y, r - 14, y + dh - 6], 5, light if k % 2 == 0 else mix(wood, 255, .08), outline=dark)
            sc.rr([300 - 22, y + dh / 2 - 6, 300 + 22, y + dh / 2], 3, dark)
        return
    if model in ('Armario', 'Vitrina'):
        glass = model == 'Vitrina'
        w, top = (230, 130) if glass else (320, 140)
        l, r = 300 - w / 2, 300 + w / 2
        sc.shadow(300, FLOOR + 6, w / 2 + 12, 14)
        sc.rr([l, top, r, FLOOR - 18], 8, wood)
        legs(sc, [l + 20, r - 20], FLOOR - 24, FLOOR, dark, 14, 8)
        for k, x0 in enumerate((l + 12, 300 + 3)):
            sc.rr([x0, top + 12, x0 + w / 2 - 15, FLOOR - 30], 5, '#DCE8EA' if glass else light, outline=dark)
        if glass:
            for y in (230, 310, 390):
                sc.rr([l + 14, y, r - 14, y + 6], 2, dark)
            for k in range(4):
                sc.rr([l + 28 + k * 42, 190, l + 48 + k * 42, 230], 4, FABRICS[(k + i) % 8])
        else:
            sc.rr([300 - 10, 280, 300 - 4, 340], 3, dark)
            sc.rr([300 + 4, 280, 300 + 10, 340], 3, dark)
        return
    if model == 'Zapatero':
        sc.shadow(300, FLOOR + 6, 150, 12)
        sc.rr([150, 300, 450, FLOOR - 14], 6, wood)
        for k in range(3):
            y = 312 + k * 48
            sc.rr([160, y, 440, y + 34], 3, light)
            for s_ in range(5):
                sc.rr([170 + s_ * 52, y + 14, 214 + s_ * 52, y + 30], 8, FABRICS[(s_ + k + i) % 8])
        legs(sc, [170, 430], FLOOR - 22, FLOOR, dark, 12, 7)
        return
    # Aparador
    sc.shadow(300, FLOOR + 6, 210, 14)
    legs(sc, [120, 480], FLOOR - 40, FLOOR, dark, 14, 6)
    sc.rr([90, 290, 510, FLOOR - 36], 10, wood)
    sc.rr([94, 290, 506, 304], 7, light)
    for k in range(3):
        x0 = 106 + k * 134
        sc.rr([x0, 314, x0 + 124, FLOOR - 48], 6, light, outline=dark)
        sc.ell([x0 + 56, 378, x0 + 68, 390], dark)


def lighting(sc, model, i):
    fab, wood = FABRICS[i % 8], WOODS[(i + 5) % 8]
    metal = '#3A3A3C'
    shade = '#F3E7D1'
    if model == 'Lámpara Pie':
        sc.glow(300, 210, 150)
        sc.shadow(300, FLOOR + 6, 70, 10)
        sc.ell([240, FLOOR - 14, 360, FLOOR + 6], metal)
        sc.rr([294, 250, 306, FLOOR - 8], 4, metal)
        sc.poly([(235, 250), (365, 250), (335, 140), (265, 140)], shade)
        sc.poly([(235, 250), (365, 250), (355, 232), (245, 232)], mix(shade, 0, .08))
    elif model == 'Lámpara Mesa':
        sc.glow(300, 280, 150)
        sc.shadow(300, FLOOR + 6, 90, 11)
        sc.rr([220, 400, 380, 440], 6, wood)
        sc.rr([225, 400, 375, 412], 5, mix(wood, 255, .2))
        sc.ell([262, 300, 338, 410], fab)
        sc.ell([272, 312, 318, 380], mix(fab, 255, .2))
        sc.rr([296, 268, 304, 304], 3, metal)
        sc.poly([(250, 270), (350, 270), (330, 190), (270, 190)], shade)
    elif model == 'Colgante':
        sc.glow(300, 300, 140)
        sc.line([(300, 0), (300, 200)], metal, 3)
        sc.rr([284, 190, 316, 212], 5, metal)
        sc.d.pieslice(sc._s([220, 200, 380, 360]), 180, 360, fill=fab)
        sc.ell([226, 270, 374, 296], '#FFF3D6')
    elif model == 'Aplique':
        sc.rr([0, 0, 64, 600], 0, '#E2D9C9')
        sc.rr([60, 0, 66, 600], 0, '#D2C8B6')
        sc.glow(300, 300, 130)
        sc.rr([44, 292, 70, 330], 5, metal)
        sc.line([(70, 310), (180, 310), (230, 290)], metal, 8)
        sc.poly([(205, 296), (295, 296), (320, 215), (240, 215)], shade)
        sc.ell([205, 288, 295, 304], '#FFF3D6')
    elif model == 'Arco':
        sc.glow(440, 300, 150)
        sc.shadow(300, FLOOR + 6, 130, 11)
        sc.rr([160, FLOOR - 22, 300, FLOOR + 4], 10, '#CFC8BC', outline='#B5AEA2')
        p0, p1, p2, p3 = (230, FLOOR - 20), (230, 70), (440, 40), (440, 222)
        pts = []
        for k in range(41):
            t = k / 40
            u = 1 - t
            pts.append((u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0],
                        u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]))
        sc.line(pts, metal, 7)
        sc.d.pieslice(sc._s([392, 214, 488, 316]), 180, 360, fill=fab)
        sc.ell([392, 262, 488, 280], '#FFF3D6')
    elif model == 'Industrial':
        sc.glow(300, 330, 150)
        sc.line([(300, 0), (300, 190)], metal, 3)
        sc.poly([(200, 330), (400, 330), (350, 200), (250, 200)], metal)
        sc.ell([200, 318, 400, 346], '#FFE9B5')
        sc.ell([278, 330, 322, 372], '#FFF6DC')
    elif model == 'Rattan':
        sc.glow(300, 310, 150)
        sc.line([(300, 0), (300, 170)], wood, 4)
        sc.d.pieslice(sc._s([200, 160, 400, 360]), 180, 360, fill=WOODS[7])
        for k in range(1, 6):
            sc.arc([200 + k * 14, 160 + k * 2, 400 - k * 14, 360 - k * 6], 180, 360, WOODS[4], 2)
        for k in range(1, 7):
            x = 200 + k * 29
            sc.line([(x, 260 - (50 - abs(x - 300) / 2.2)), (x, 260)], WOODS[4], 2)
    else:  # Globo
        sc.glow(300, 330, 170, alpha=190)
        sc.line([(300, 0), (300, 220)], metal, 3)
        sc.rr([288, 214, 312, 236], 5, metal)
        sc.ell([210, 232, 390, 412], '#FFF7E6', outline='#EADFC8')
        sc.ell([240, 262, 300, 322], '#FFFFFF')


DRAW = {'Sofas': sofa, 'Chairs': chair, 'Tables': table, 'Beds': bed, 'Storage': storage, 'Lighting': lighting}


def render(category, model, index):
    scene = Scene(index)
    DRAW[category](scene, model, index)
    return scene.jpeg()
