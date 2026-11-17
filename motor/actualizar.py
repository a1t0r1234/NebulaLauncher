"""Actualizaciones del launcher desde las Releases de GitHub.

Cada versión se publica como una Release con la etiqueta vX.Y.Z y dos archivos:
  - NebulaLauncher.exe
  - NebulaLauncher.exe.sha256   (la huella SHA-256 del .exe, en hexadecimal)
El launcher compara su versión (ajustes.VERSION) con la de la última Release; si hay una más nueva, el jugador
pulsa "Actualizar": se descarga el .exe, se comprueba la huella (si no coincide, no se instala), y un pequeño
.bat espera a que el launcher se cierre, cambia el archivo y lo vuelve a abrir.
Solo funciona en el .exe (desde el código no hay nada que sustituir).
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

from . import ajustes
from .instalador import S

REPO = "a1t0r1234/NebulaLauncher"
API = f"https://api.github.com/repos/{REPO}/releases/latest"
NOMBRE_EXE = "NebulaLauncher.exe"


def _tupla(v: str) -> tuple:
    try:
        return tuple(int(x) for x in v.strip().lstrip("vV").split("."))
    except ValueError:
        return (0,)


def en_exe() -> bool:
    return bool(getattr(sys, "frozen", False))


def comprobar() -> dict | None:
    """Datos de la versión nueva si la hay; None si estamos al día o no se puede mirar (sin internet, etc.)."""
    try:
        r = S.get(API, timeout=8, headers={"Accept": "application/vnd.github+json"})
        if r.status_code != 200:
            return None
        rel = r.json()
    except Exception:
        return None
    nueva = rel.get("tag_name", "")
    if _tupla(nueva) <= _tupla(ajustes.VERSION):
        return None
    archivos = {a["name"]: a["browser_download_url"] for a in rel.get("assets", [])}
    if NOMBRE_EXE not in archivos or NOMBRE_EXE + ".sha256" not in archivos:
        return None                                         # Release a medias: mejor no ofrecerla
    return {
        "version": nueva.lstrip("vV"),
        "notas": (rel.get("body") or "").strip()[:600],
        "exe": archivos[NOMBRE_EXE],
        "sha256": archivos[NOMBRE_EXE + ".sha256"],
        "puede_instalar": en_exe(),
    }


def instalar(datos: dict, aviso) -> None:
    """Descarga y comprueba el .exe nuevo y deja preparado el cambio. Después hay que cerrar el launcher."""
    if not en_exe():
        raise RuntimeError("Las actualizaciones solo se instalan en el .exe.")
    carpeta = ajustes.DATOS / "actualizacion"
    carpeta.mkdir(parents=True, exist_ok=True)
    nuevo = carpeta / NOMBRE_EXE
    esperada = S.get(datos["sha256"], timeout=20).text.split()[0].strip().lower()
    aviso("Descargando la nueva versión", 0, 1)
    h = hashlib.sha256()
    with S.get(datos["exe"], timeout=60, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
        hecho = 0
        with open(nuevo, "wb") as f:
            for trozo in r.iter_content(1 << 16):
                f.write(trozo)
                h.update(trozo)
                hecho += len(trozo)
                if total:
                    aviso("", hecho, total)
    if h.hexdigest().lower() != esperada:
        nuevo.unlink(missing_ok=True)
        raise RuntimeError("La descarga no coincide con la huella publicada. No se ha instalado nada.")
    actual = Path(sys.executable)
    bat = carpeta / "cambiar.bat"
    # espera a que el launcher se cierre (el .exe está bloqueado mientras corre), lo cambia y lo abre de nuevo
    bat.write_text(
        "@echo off\r\n"
        "set /a n=0\r\n"
        ":espera\r\n"
        "timeout /t 1 /nobreak >nul\r\n"
        f'move /y "{nuevo}" "{actual}" >nul 2>&1 && goto listo\r\n'
        "set /a n+=1\r\n"
        "if %n% lss 60 goto espera\r\n"
        "exit /b 1\r\n"
        ":listo\r\n"
        f'start "" "{actual}"\r\n'
        'del "%~f0"\r\n',
        encoding="utf-8")
    flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS if os.name == "nt" else 0
    subprocess.Popen(["cmd", "/c", str(bat)], creationflags=flags, close_fds=True)
    aviso("Reiniciando el launcher", 1, 1)
