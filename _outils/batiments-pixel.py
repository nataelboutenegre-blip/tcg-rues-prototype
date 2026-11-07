"""Bâtiments TerraFront en pixel art (24 x 24) : dessin par formes simples, contour automatique.
Export : batiments/<type>-<style>.svg (patch366). Aperçu : python3 batiments-pixel.py apercu."""
import json, sys
from PIL import Image

N = 24
PAL = {
    'k': '#1C1B2B',
    'S': '#9AA3B2', 's': '#6E7787', 'l': '#C9D0DA',
    'R': '#B5473A', 'r': '#86302A',
    'T': '#4A5568', 't': '#2F3846',
    'W': '#9C6B3E', 'w': '#6E4726', 'h': '#C08A55',
    'O': '#FFB020', 'o': '#FF6A1A', 'y': '#FFE27A',
    'g': '#D5DAE2', 'G': '#A3AAB6',
    'b': '#6EC3F0', 'B': '#2E78B8',
    'v': '#5DAF5A', 'V': '#3A7A3C',
    'Y': '#F0B429', 'u': '#C98A12',
    'M': '#EEE7D8', 'n': '#C3B89F',
    'e': '#D4BD8E', 'E': '#A88E5E',
    'c': '#45D6CF', 'C': '#1F8F8A',
    'p': '#C2413B', 'P': '#8E2A26',
    'x': '#FFFFFF',
}
SANS_CONTOUR = set('gG')


class Grille:
    def __init__(self):
        self.g = [[None] * N for _ in range(N)]

    def px(self, x, y, c):
        if 0 <= x < N and 0 <= y < N:
            self.g[y][x] = c

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px(xx, yy, c)

    def ligne(self, x0, y0, x1, y1, c):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n + 1):
            self.px(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < N and 0 <= y < N else None

    def contour(self):
        a_mettre = []
        for y in range(N):
            for x in range(N):
                if self.g[y][x] is not None:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    v = self.get(x + dx, y + dy)
                    if v is not None and v not in SANS_CONTOUR and v != 'k':
                        a_mettre.append((x, y))
                        break
        for x, y in a_mettre:
            self.g[y][x] = 'k'

    def herbe(self):
        for x in range(N):
            self.px(x, 22, 'V')
            self.px(x, 21, 'v' if x % 5 else 'V')
        for x in (2, 9, 15, 20):
            self.px(x, 20, 'v') if self.get(x, 20) is None else None


def pierre(G, x0, y0, w, h, base='S', joint='s', clair='l'):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            ry = y - y0
            if ry % 3 == 2:
                c = joint
            elif (x - x0 + (2 if (ry // 3) % 2 else 0)) % 4 == 3:
                c = joint
            else:
                c = base
            G.px(x, y, c)
    for y in range(y0, y0 + h):
        if G.get(x0, y) == base:
            G.px(x0, y, clair)


def briques(G, x0, y0, w, h):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            G.px(x, y, 'r' if (x + (2 if y % 2 else 0)) % 4 == 0 else 'R')


def triangle(G, cx_g, cx_d, y_bas, hauteur, pas, c, ombre=None):
    """Triangle posé sur la ligne y_bas, de cx_g à cx_d, qui rétrécit de `pas` de chaque côté par rang."""
    for i in range(hauteur):
        g, d = cx_g + i * pas, cx_d - i * pas
        if g > d:
            break
        for x in range(g, d + 1):
            G.px(x, y_bas - i, ombre if ombre and x > (cx_g + cx_d) / 2 else c)


def forteresse_chateau():
    G = Grille()
    pierre(G, 1, 6, 6, 15)
    pierre(G, 17, 6, 6, 15)
    pierre(G, 7, 10, 10, 11)
    for x in (1, 5, 17, 21):
        G.rect(x, 4, 2, 2, 'S')
    for x in (7, 11, 15):
        G.rect(x, 8, 2, 2, 'S')
    for x in (3, 19):
        G.rect(x, 9, 2, 3, 'k')
        G.rect(x, 15, 2, 2, 'k')
    # porte en arc
    G.rect(9, 14, 6, 7, 'k')
    G.rect(10, 15, 4, 6, 'W')
    G.px(9, 14, 'S'); G.px(14, 14, 'S')
    G.rect(11, 13, 2, 1, 'k')
    G.rect(11, 14, 2, 1, 'W')
    for y in range(15, 21):
        G.px(12, y, 'w')
    G.px(10, 16, 'k'); G.px(10, 19, 'k')
    # drapeau
    for y in range(1, 8):
        G.px(12, y, 'k')
    G.rect(13, 1, 3, 2, 'Y')
    G.px(13, 3, 'u'); G.px(14, 3, 'u')
    G.herbe()
    G.contour()
    return G


def forteresse_bastion():
    G = Grille()
    for y in range(13, 21):
        xl = 3 - (y - 13) * 3 // 7
        xr = N - 1 - xl
        for x in range(xl, xr + 1):
            joint = (y % 2 == 0) or ((x + (3 if y % 4 == 1 else 0)) % 6 == 0)
            G.px(x, y, 'E' if joint else 'e')
    for x in range(3, 21):
        G.px(x, 12, 'v')
    for x in (4, 7, 16, 19):
        G.px(x, 11, 'V')
    # poste de garde
    G.rect(8, 6, 8, 7, 'M')
    for y in range(6, 13):
        G.px(15, y, 'n')
    for x0 in (9, 13):
        G.rect(x0, 8, 2, 1, 'b')
        G.rect(x0, 9, 2, 1, 'B')
    triangle(G, 7, 16, 5, 4, 1, 'p', 'P')
    # fanion
    G.px(11, 1, 'k'); G.px(11, 0, 'k')
    G.px(12, 0, 'Y'); G.px(13, 0, 'Y'); G.px(12, 1, 'u')
    # porte et meurtrières
    G.rect(9, 15, 6, 6, 'k')
    G.rect(10, 16, 4, 5, 'w')
    G.rect(11, 16, 2, 5, 'W')
    G.rect(4, 16, 2, 1, 'k'); G.rect(18, 16, 2, 1, 'k')
    G.herbe()
    G.contour()
    return G


def forteresse_tour():
    G = Grille()
    triangle(G, 4, 19, 5, 5, 2, 'p', 'P')
    G.rect(6, 6, 12, 5, 'W')
    for x in (8, 11, 14):
        for y in range(6, 11):
            G.px(x, y, 'w')
    G.rect(8, 7, 8, 2, 'k')
    G.rect(9, 7, 6, 2, 'O')
    G.px(11, 7, 'y'); G.px(12, 7, 'y')
    for x in range(4, 20):
        G.px(x, 11, 'h')
    for x in (4, 9, 14, 19):
        G.px(x, 10, 'h')
    for x0 in (7, 15):
        G.rect(x0, 12, 2, 9, 'w')
    G.ligne(9, 12, 14, 17, 'W')
    G.ligne(14, 12, 9, 17, 'W')
    G.ligne(9, 16, 14, 20, 'W')
    G.ligne(14, 16, 9, 20, 'W')
    G.herbe()
    G.contour()
    return G


def fonderie_brique():
    G = Grille()
    briques(G, 1, 13, 22, 8)
    triangle(G, 1, 14, 12, 4, 1, 'T', 't')
    briques(G, 16, 3, 3, 10)
    G.rect(15, 2, 5, 1, 's')
    # fumée
    for x, y, c in ((15, 0, 'g'), (16, 0, 'g'), (17, 1, 'G'), (18, 0, 'g'), (19, 0, 'G'), (14, 1, 'g'), (20, 1, 'g')):
        G.px(x, y, c)
    # four
    G.rect(3, 14, 7, 7, 'k')
    G.rect(4, 15, 5, 6, 'O')
    G.rect(5, 14, 3, 1, 'O')
    G.rect(5, 16, 3, 3, 'y')
    G.rect(4, 19, 5, 2, 'o')
    # fenêtres
    for x0 in (11, 17):
        G.rect(x0 - 1, 14, 5, 4, 'k')
        G.rect(x0, 15, 3, 1, 'b')
        G.rect(x0, 16, 3, 1, 'B')
    G.herbe()
    G.contour()
    return G


def fonderie_acier():
    G = Grille()
    for x in range(1, 23):
        for y in range(12, 21):
            G.px(x, y, 'l' if x % 2 else 'S')
    for y, (g, d) in ((9, (5, 18)), (10, (3, 20)), (11, (1, 22))):
        for x in range(g, d + 1):
            G.px(x, y, 'T' if x < 14 else 't')
    for x0, y0 in ((4, 3), (8, 5)):
        G.rect(x0, y0, 2, 9 - y0, 's')
        G.rect(x0, y0, 2, 1, 'O')
    for x, y, c in ((4, 1, 'g'), (5, 0, 'g'), (5, 2, 'G'), (8, 3, 'g'), (9, 2, 'g'), (10, 3, 'G')):
        G.px(x, y, c)
    # porte roulante
    G.rect(8, 13, 8, 1, 'k')
    for x in range(8, 16):
        G.px(x, 13, 'Y' if x % 2 else 'k')
    G.rect(8, 14, 8, 7, 't')
    for y in (15, 17, 19):
        for x in range(9, 15):
            G.px(x, y, 's')
    for x in range(8, 16):
        G.px(x, 20, 'o' if x in (11, 12) else 't')
    for x0 in (2, 17):
        G.rect(x0, 14, 5, 3, 'k')
        G.rect(x0 + 1, 15, 3, 1, 'b')
    G.herbe()
    G.contour()
    return G


def banque_classique():
    G = Grille()
    for x in range(1, 23):
        G.px(x, 20, 'n')
    for x in range(2, 22):
        G.px(x, 19, 'M')
    for x in range(3, 21):
        G.px(x, 18, 'n')
    G.rect(3, 11, 18, 7, 't')
    for x0 in (4, 8, 14, 18):
        G.rect(x0, 11, 2, 7, 'M')
        for y in range(11, 18):
            G.px(x0 + 1, y, 'n')
    G.rect(10, 13, 4, 5, 'Y')
    G.rect(11, 14, 2, 2, 'u')
    G.px(12, 16, 'u')
    for x in range(2, 22):
        G.px(x, 9, 'M'); G.px(x, 10, 'n')
    triangle(G, 2, 21, 8, 5, 2, 'M')
    for x in range(2, 22):
        if G.get(x, 8) == 'M':
            G.px(x, 8, 'n')
    G.rect(11, 6, 2, 2, 'Y')
    G.px(12, 7, 'u')
    G.herbe()
    G.contour()
    return G


def centre_labo():
    G = Grille()
    G.rect(2, 13, 20, 8, 'l')
    for x in range(2, 22):
        G.px(x, 20, 'S')
    for x0 in (4, 17):
        G.rect(x0 - 1, 14, 5, 3, 'k')
        G.rect(x0, 15, 3, 1, 'c')
    G.rect(9, 15, 6, 6, 'k')
    G.rect(10, 16, 4, 5, 'C')
    G.rect(10, 16, 2, 5, 'c')
    rangs = {12: (5, 18), 11: (5, 18), 10: (6, 17), 9: (6, 17), 8: (7, 16), 7: (8, 15), 6: (10, 13)}
    for y, (g, d) in rangs.items():
        for x in range(g, d + 1):
            G.px(x, y, 'l' if x < g + 2 else 'S')
    for y in range(6, 12):
        G.px(11, y, 't'); G.px(12, y, 't')
    G.px(11, 8, 'c'); G.px(12, 8, 'c')
    for y in range(3, 13):
        G.px(20, y, 'k')
    G.px(20, 2, 'o'); G.px(19, 3, 'k'); G.px(21, 3, 'k')
    G.herbe()
    G.contour()
    return G


def banque_coffre():
    G = Grille()
    G.rect(2, 9, 20, 12, 'T')
    for y in range(9, 21):
        G.px(2, y, 'S'); G.px(21, y, 't')
    for x in range(1, 23):
        G.px(x, 8, 'S')
    for x, y in ((3, 10), (20, 10), (3, 19), (20, 19)):
        G.px(x, y, 'l')
    cx, cy = 11.5, 14.5
    for y in range(9, 21):
        for x in range(4, 20):
            d2 = (x + .5 - 12) ** 2 + (y + .5 - 15) ** 2
            if d2 <= 25:
                G.px(x, y, 'S' if d2 > 16 else 'l')
    for x in range(8, 16):
        G.px(x, 14, 'u')
    for y in range(11, 19):
        G.px(11, y, 'u')
    G.rect(10, 13, 3, 3, 'Y')
    G.px(11, 14, 'u')
    # lingots sur le toit
    G.rect(6, 6, 12, 2, 'Y')
    for x in range(6, 18):
        G.px(x, 7, 'u')
    G.px(11, 6, 'u'); G.px(12, 6, 'u')
    G.rect(9, 4, 6, 2, 'Y')
    for x in range(9, 15):
        G.px(x, 5, 'u')
    G.herbe()
    G.contour()
    return G


def centre_bunker():
    G = Grille()
    rangs = {11: (8, 15), 12: (7, 16), 13: (6, 17)}
    for y in range(14, 20):
        rangs[y] = (5, 18)
    for y, (g, d) in rangs.items():
        for x in range(g, d + 1):
            G.px(x, y, 'l' if y <= 12 else ('s' if x >= d - 1 else 'S'))
    for x in range(8, 16):
        G.px(x, 14, 'k')
    for x in range(9, 15):
        G.px(x, 14, 'c')
    G.px(11, 14, 'C'); G.px(12, 14, 'C')
    G.rect(10, 16, 4, 4, 't')
    G.px(10, 16, 's'); G.px(13, 16, 's')
    for y in range(17, 21):
        for x in list(range(1, 6)) + list(range(18, 23)):
            if y >= 17 + (abs(x - 11.5) > 9):
                G.px(x, y, 'v' if y < 19 else 'V')
    for y in range(4, 11):
        G.px(19, y, 'k')
    for x, y in ((16, 3), (17, 4), (18, 5), (19, 5), (20, 4), (21, 3)):
        G.px(x, y, 'l')
    G.px(18, 4, 'S'); G.px(20, 3, 'S')
    G.px(19, 2, 'o')
    G.herbe()
    G.contour()
    return G


def radar_parabole():
    G = Grille()
    # local technique en béton
    G.rect(4, 15, 16, 6, 'S')
    for y in range(15, 21):
        G.px(4, y, 'l'); G.px(19, y, 's')
    for x in range(3, 21):
        G.px(x, 14, 'l')
    G.rect(7, 17, 3, 4, 'k'); G.rect(8, 18, 1, 3, 't')
    G.rect(13, 16, 4, 2, 'k'); G.rect(14, 16, 2, 1, 'c')
    G.px(17, 19, 'o')
    # mât
    for y in range(9, 14):
        G.px(11, y, 's'); G.px(12, y, 'S')
    # la parabole, penchée vers le ciel à droite
    bol = {2: (13, 17), 3: (11, 19), 4: (9, 20), 5: (8, 20), 6: (7, 20), 7: (7, 19), 8: (7, 17), 9: (8, 14)}
    for y, (g, d) in bol.items():
        for x in range(g, d + 1):
            G.px(x, y, 'g' if (x - g) < 2 else 'M')
    for y, (g, d) in bol.items():
        G.px(d, y, 'n')
    # bras et source
    G.ligne(12, 6, 17, 1, 'T')
    G.px(18, 0, 'o'); G.px(17, 0, 'o'); G.px(18, 1, 'y')
    G.herbe()
    G.contour()
    return G


def radar_dome():
    G = Grille()
    # tour
    G.rect(8, 13, 8, 8, 'S')
    for y in range(13, 21):
        G.px(8, y, 'l'); G.px(15, y, 's')
    for y in (15, 18):
        for x in range(9, 15):
            G.px(x, y, 's')
    G.rect(10, 19, 4, 2, 'k'); G.rect(11, 19, 2, 2, 't')
    G.rect(6, 12, 12, 1, 'T')
    # le radôme : une boule blanche, des joints de panneaux, l'ombre à droite
    cx, cy, r = 12, 6.6, 6.3
    for y in range(0, 13):
        for x in range(4, 21):
            dx, dy = x + .5 - cx, y + .5 - cy
            if dx * dx + dy * dy <= r * r:
                ombre = dx * .7 + dy * .7 > 2.6
                horiz = y in (3, 7, 10)
                joint = horiz or abs(dx - dy * .25) < .5 or abs(dx + 3.6 - dy * .15) < .5 or abs(dx - 3.8 + dy * .15) < .5
                G.px(x, y, ('G' if horiz else 'n') if ombre else ('n' if joint else 'M'))
    G.px(8, 2, 'x'); G.px(9, 2, 'x'); G.px(8, 3, 'x')
    G.px(12, 0, 'o')
    G.herbe()
    G.contour()
    return G


def radar_pylone():
    G = Grille()
    # le pylône en treillis : deux montants qui s'écartent, des croisillons
    for y in range(8, 21):
        demi = 2 + (y - 8) * 5 // 12
        G.px(12 - demi, y, 'S'); G.px(11 + demi, y, 's')
    for y0 in (9, 13, 17):
        d0 = 2 + (y0 - 8) * 5 // 12
        d1 = 2 + (y0 + 3 - 8) * 5 // 12
        G.ligne(12 - d0 + 1, y0, 11 + d1 - 1, y0 + 3, 'T')
        G.ligne(11 + d0 - 1, y0, 12 - d1 + 1, y0 + 3, 'T')
    for x in range(5, 19):
        G.px(x, 20, 'T')
    # plateforme et antenne tournante
    G.rect(8, 7, 8, 1, 'T')
    G.rect(10, 5, 4, 2, 'S')
    G.rect(2, 3, 20, 2, 'l')
    for x in range(2, 22):
        G.px(x, 4, 'S')
    for x in range(3, 21, 3):
        G.px(x, 3, 'g')
    # les ondes
    for x, y in ((0, 1), (1, 0), (1, 2)):
        G.px(x, y, 'c')
    for x, y in ((23, 1), (22, 0), (22, 2)):
        G.px(x, y, 'c')
    G.px(12, 2, 'o')
    G.herbe()
    G.contour()
    return G


SPRITES = {
    'forteresse_chateau': forteresse_chateau,
    'forteresse_bastion': forteresse_bastion,
    'forteresse_tour': forteresse_tour,
    'fonderie_brique': fonderie_brique,
    'fonderie_acier': fonderie_acier,
    'banque_classique': banque_classique,
    'banque_coffre': banque_coffre,
    'centre_labo': centre_labo,
    'centre_bunker': centre_bunker,
    'radar_parabole': radar_parabole,
    'radar_dome': radar_dome,
    'radar_pylone': radar_pylone,
}


def en_svg(G, taille=None, label=None):
    parties = []
    par_couleur = {}
    for y in range(N):
        x = 0
        while x < N:
            c = G.g[y][x]
            if c is None:
                x += 1
                continue
            d = x
            while d < N and G.g[y][d] == c:
                d += 1
            par_couleur.setdefault(c, []).append(f'M{x} {y}h{d - x}v1h-{d - x}z')
            x = d
    for c, segs in par_couleur.items():
        parties.append(f'<path fill="{PAL[c]}" d="{"".join(segs)}"/>')
    attr = f' width="{taille}" height="{taille}"' if taille else ''
    role = f' role="img" aria-label="{label}"' if label else ' aria-hidden="true"'
    return f'<svg{role}{attr} viewBox="0 0 24 24" shape-rendering="crispEdges">{"".join(parties)}</svg>'


def apercu(chemin, echelle=10):
    noms = list(SPRITES)
    img = Image.new('RGB', (len(noms) * (N * echelle + 20) + 20, N * echelle + 40), '#0F1F38')
    for i, nom in enumerate(noms):
        G = SPRITES[nom]()
        ox = 20 + i * (N * echelle + 20)
        for y in range(N):
            for x in range(N):
                c = G.g[y][x]
                if c:
                    col = PAL[c]
                    for yy in range(echelle):
                        for xx in range(echelle):
                            img.putpixel((ox + x * echelle + xx, 20 + y * echelle + yy), tuple(int(col[j:j + 2], 16) for j in (1, 3, 5)))
    img.save(chemin)


if __name__ == '__main__':
    if sys.argv[1:] == ['apercu']:
        apercu('/home/claude/pixel/planche.png')
    else:
        out = {nom: en_svg(f()) for nom, f in SPRITES.items()}
        json.dump(out, open('/home/claude/pixel/sprites.json', 'w'), ensure_ascii=False)
        print({k: len(v) for k, v in out.items()})
