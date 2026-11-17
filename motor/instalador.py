"""Deja un proyecto listo para jugar: Minecraft + Fabric + Java, los mods del modpack (.mrpack) y la config del menú.

Cada proyecto tiene su carpeta en %APPDATA%/.nebula/instancias/<id>. En su carpeta mods solo quedan los mods del
proyecto: cualquier otro .jar que alguien meta a mano se quita antes de abrir el juego.
"""
import hashlib
import io
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import minecraft_launcher_lib as mll
import requests

from . import ajustes

S = requests.Session()
S.headers["User-Agent"] = "NebulaLauncher/" + ajustes.VERSION


def carpeta(proyecto: dict) -> Path:
    d = ajustes.INSTANCIAS / proyecto["id"]
    (d / "mods").mkdir(parents=True, exist_ok=True)
    (d / "config").mkdir(parents=True, exist_ok=True)
    return d


def _bytes(origen: str) -> bytes:
    """Descarga una URL o lee un archivo local (para probar antes de subir nada)."""
    if origen.startswith(("http://", "https://")):
        r = S.get(origen, timeout=60)
        r.raise_for_status()
        return r.content
    return Path(origen).read_bytes()


def _sha1(ruta: Path) -> str:
    h = hashlib.sha1()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(1 << 20), b""):
            h.update(trozo)
    return h.hexdigest()


def _bajar(destino: Path, urls: list, sha1: str) -> None:
    if destino.exists() and _sha1(destino) == sha1:
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    ultimo = None
    for u in urls:
        try:
            datos = _bytes(u)
            if hashlib.sha1(datos).hexdigest() != sha1:
                raise ValueError(f"{destino.name}: el archivo descargado no coincide")
            destino.write_bytes(datos)
            return
        except Exception as e:  # probar el siguiente enlace
            ultimo = e
    raise RuntimeError(f"No se pudo descargar {destino.name}: {ultimo}")


def preparar(proyecto: dict, aviso) -> str:
    """Instala o actualiza todo. `aviso(texto, hecho, total)` informa del progreso. Devuelve la versión a lanzar."""
    pref = ajustes.preferencias()
    juego = carpeta(proyecto)

    aviso("Leyendo el modpack", 0, 1)
    mrpack = zipfile.ZipFile(io.BytesIO(_bytes(proyecto["mrpack"])))
    indice = json.loads(mrpack.read("modrinth.index.json"))
    mc = indice["dependencies"]["minecraft"]
    fabric = indice["dependencies"]["fabric-loader"]
    version = f"fabric-loader-{fabric}-{mc}"

    if version not in {v["id"] for v in mll.utils.get_installed_versions(ajustes.MINECRAFT)}:
        estado = {"max": 1}
        cb = {
            "setStatus": lambda t: aviso(f"Instalando Minecraft {mc} · {t}", 0, 1),
            "setMax": lambda m: estado.update(max=max(1, m)),
            "setProgress": lambda p: aviso(None, p, estado["max"]),
        }
        mll.fabric.install_fabric(mc, ajustes.MINECRAFT, loader_version=fabric, callback=cb)

    # mods del modpack + extras del proyecto (por ejemplo el mod de CraftTerra)
    archivos = [f for f in indice["files"]
                if f.get("env", {}).get("client", "required") == "required"
                or (pref["opcionales"] and f["env"]["client"] == "optional")]
    archivos += [{"path": e["path"], "hashes": {"sha1": e["sha1"]}, "downloads": [e["url"]]} for e in proyecto.get("extras", [])]
    permitidos = set()
    for i, f in enumerate(archivos):
        aviso(f"Descargando {Path(f['path']).name}", i, len(archivos))
        destino = (juego / f["path"]).resolve()
        if juego.resolve() not in destino.parents:
            raise RuntimeError(f"Ruta no válida en el modpack: {f['path']}")
        _bajar(destino, f["downloads"], f["hashes"]["sha1"])
        permitidos.add(destino)

    # overrides del modpack (servers.dat, opciones...) solo la primera vez, para no pisar lo que el jugador cambie
    for nombre in mrpack.namelist():
        if nombre.startswith("overrides/") and not nombre.endswith("/"):
            destino = juego / nombre[len("overrides/"):]
            if destino.suffix == ".jar" or not destino.exists():
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_bytes(mrpack.read(nombre))
            if destino.parent.name == "mods":
                permitidos.add(destino.resolve())

    # en mods solo se quedan los del proyecto
    for jar in (juego / "mods").glob("*"):
        if jar.is_file() and jar.resolve() not in permitidos:
            jar.unlink()

    # el menú de título sabe a qué servidor entrar
    (juego / "config" / "craftterra_menu.properties").write_text(
        f"servidor={proyecto['servidor']}\nnombre={proyecto['nombre_servidor']}\n", encoding="utf-8")
    aviso("Todo listo", 1, 1)
    return version


def lanzar(proyecto: dict, version: str, sesion: dict) -> subprocess.Popen:
    pref = ajustes.preferencias()
    opciones = {
        "username": sesion["nombre"],
        "uuid": sesion["uuid"],
        "token": sesion["token"],
        "gameDirectory": str(carpeta(proyecto)),
        "jvmArguments": [f"-Xmx{pref['ram_gb']}G", f"-Xms{min(2, pref['ram_gb'])}G"],
        "launcherName": "NebulaLauncher",
        "launcherVersion": ajustes.VERSION,
    }
    orden = mll.command.get_minecraft_command(version, ajustes.MINECRAFT, opciones)
    if orden[0] == "java" and shutil.which("java") is None:
        raise RuntimeError("No se encontró Java. Vuelve a darle a Jugar para instalarlo.")
    flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    return subprocess.Popen(orden, cwd=carpeta(proyecto), creationflags=flags)
