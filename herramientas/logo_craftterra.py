"""Logo e icono de CraftTerra para el launcher, estilo Minecraft.

- Logo: título estilo Minecraft (letras propias): degradado vivo de arriba abajo, borde de luz, contorno grueso y relieve.
  "CRAFT" dorado y "TERRA" verde césped con churretes de hierba.
- Icono: bloque de césped en perspectiva (pixel art) para la barra de proyectos.

Uso: python herramientas/logo_craftterra.py   -> ui/img/proyectos/craftterra_logo.png y craftterra_icono.png
"""
import random
from pathlib import Path

from PIL import Image

SALIDA = Path(__file__).resolve().parents[1] / "ui" / "img" / "proyectos"
SALIDA.mkdir(parents=True, exist_ok=True)

# letras propias de 5 x 7 (gruesas, de bloques)
F = {
    "C": ["01111", "11111", "11000", "11000", "11000", "11111", "01111"],
    "R": ["11110", "11111", "11011", "11110", "11011", "11011", "11011"],
    "A": ["01110", "11111", "11011", "11111", "11111", "11011", "11011"],
    "F": ["11111", "11111", "11000", "11110", "11000", "11000", "11000"],
    "T": ["11111", "11111", "00110", "00110", "00110", "00110", "00110"],
    "E": ["11111", "11111", "11000", "11110", "11000", "11111", "11111"],
}
B = 6            # píxeles por bloque de letra
HUECO = 1        # bloques entre letras
FONDO = 5        # extrusión hacia abajo (px)

PIEDRA = [(112, 112, 112), (122, 122, 122), (131, 131, 131), (140, 140, 140), (150, 150, 150)]
TIERRA = [(108, 74, 48), (121, 85, 58), (134, 96, 67), (150, 108, 74)]
HIERBA = [(76, 128, 42), (92, 148, 50), (108, 166, 58), (128, 186, 70)]
CONTORNO = (18, 16, 22)


def oscurecer(c, k):
    return tuple(int(v * k) for v in c)


DORADO = [(255, 246, 170), (255, 224, 90), (255, 196, 50), (246, 160, 34), (226, 124, 22), (196, 92, 14)]
VERDE = [(214, 255, 130), (164, 236, 74), (118, 210, 46), (80, 176, 34), (56, 140, 28), (40, 108, 22)]
CHURRETE = (226, 255, 150)


def logo():
    """Título estilo Minecraft: degradado de arriba abajo, borde de luz arriba, contorno grueso y relieve abajo."""
    rnd = random.Random(3)
    palabra = "CRAFTTERRA"
    celdas = {}                                   # (cx, cy) -> palabra (0 = CRAFT, 1 = TERRA)
    for li, ch in enumerate(palabra):
        for r, fila in enumerate(F[ch]):
            for c, v in enumerate(fila):
                if v == "1":
                    celdas[(li * (5 + HUECO) + c + (1 if li >= 5 else 0), r)] = 0 if li < 5 else 1
    ancho = max(x for x, _ in celdas) + 1
    W, H = ancho * B + 12, 7 * B + FONDO + 12
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    ox, oy = 6, 5
    cara = {}                                     # píxel -> palabra
    for (cx, cy), p in celdas.items():
        for x in range(B):
            for y in range(B):
                cara[(ox + cx * B + x, oy + cy * B + y)] = p
    alto = 7 * B

    def put(x, y, col):
        if 0 <= x < W and 0 <= y < H:
            px[x, y] = col + (255,)

    # relieve: cada columna de la letra se alarga hacia abajo con el color de abajo, oscurecido
    for (x, y), p in cara.items():
        if (x, y + 1) not in cara:
            base = (DORADO if p == 0 else VERDE)[-1]
            for d in range(1, FONDO + 1):
                put(x, y + d, oscurecer(base, 0.62 - d * 0.05))
    # contorno grueso (2 px)
    ocupado = {(x, y) for y in range(H) for x in range(W) if px[x, y][3]}
    for (x, y) in list(ocupado):
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if abs(dx) + abs(dy) <= 3 and (x + dx, y + dy) not in ocupado:
                    put(x + dx, y + dy, (16, 10, 14))
    # caras con degradado vertical por bandas (pixel art) y luz en el borde de arriba
    for (x, y), p in cara.items():
        rampa = DORADO if p == 0 else VERDE
        t = (y - oy) / alto
        c = rampa[min(len(rampa) - 1, int(t * len(rampa)))]
        if (x, y - 1) not in cara or (x, y - 2) not in cara:
            c = tuple(min(255, v + 40) for v in rampa[0])        # borde de luz arriba
        elif (x, y + 1) not in cara:
            c = oscurecer(c, 0.85)                               # sombra fina abajo
        if (x - 1, y) not in cara:
            c = tuple(min(255, v + 14) for v in c)               # luz en el lado izquierdo
        if (x * 7 + y * 13) % 23 == 0:
            c = oscurecer(c, 0.92)                               # textura suave de píxeles
        put(x, y, c)
    # churretes de hierba en TERRA: bajan desde el borde de arriba de cada trazo
    for (x, y), p in cara.items():
        if p == 1 and (x, y - 1) not in cara and rnd.random() < 0.35:
            largo = rnd.choice((2, 3, 3, 4, 5))
            for d in range(2, 2 + largo):
                if (x, y + d) in cara:
                    put(x, y + d, CHURRETE if d < 1 + largo else VERDE[1])
    return img


def icono():
    """Bloque de césped en perspectiva, 32 x 32."""
    rnd = random.Random(9)
    N = 32
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    px = img.load()
    cara = 8                                       # textura de 8 x 8 por cara
    top = [[rnd.choice(HIERBA) for _ in range(cara)] for _ in range(cara)]
    lado = [[(rnd.choice(HIERBA) if (y < 2 or (y == 2 and rnd.random() < 0.5)) else rnd.choice(TIERRA))
             for _ in range(cara)] for y in range(cara)]
    cx = N // 2
    for y in range(N):
        for x in range(N):
            # proyección isométrica: arriba un rombo, abajo dos caras
            u = (x - cx) / 14.0
            v = (y - 9) / 7.0
            a, b = v + u, v - u                    # coordenadas de la cara de arriba
            if 0 <= a < 1 * 2 and 0 <= b < 2 and y < 16:
                i, j = int(a / 2 * cara), int(b / 2 * cara)
                if 0 <= i < cara and 0 <= j < cara and a + b <= 2.0 + 0.001 and a + b >= 0:
                    px[x, y] = top[j][i] + (255,)
                    continue
            if y >= 9:
                if x < cx:                         # cara izquierda
                    t = (cx - x) / 14.0
                    yy = y - 16 + t * 7
                    if 0 <= t <= 1 and 0 <= yy < 15:
                        px[x, y] = oscurecer(lado[int(yy / 15 * cara)][int(t * cara) % cara], 0.82) + (255,)
                else:                              # cara derecha
                    t = (x - cx) / 14.0
                    yy = y - 16 + t * 7
                    if 0 <= t <= 1 and 0 <= yy < 15:
                        px[x, y] = oscurecer(lado[int(yy / 15 * cara)][int(t * cara) % cara], 0.62) + (255,)
    # contorno
    borde = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    bp = borde.load()
    for y in range(N):
        for x in range(N):
            if px[x, y][3] == 0 and any(0 <= x + dx < N and 0 <= y + dy < N and px[x + dx, y + dy][3]
                                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                bp[x, y] = CONTORNO + (255,)
    borde.alpha_composite(img)
    return borde


if __name__ == "__main__":
    l = logo()
    l.save(SALIDA / "craftterra_logo.png")
    i = icono()
    i.save(SALIDA / "craftterra_icono.png")
    vista = Image.new("RGBA", (l.width * 3 + 40, l.height * 3 + 160), (7, 6, 15, 255))
    vista.alpha_composite(l.resize((l.width * 3, l.height * 3), Image.NEAREST), (20, 20))
    vista.alpha_composite(i.resize((128, 128), Image.NEAREST), (20, l.height * 3 + 26))
    vista.save(SALIDA / "_vista.png")
    print("logo", l.size, "icono", i.size)
