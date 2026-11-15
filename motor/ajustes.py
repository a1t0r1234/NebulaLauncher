"""Rutas y ajustes de Nebula Launcher (Nebula Studios)."""
import json
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATOS = Path(os.environ.get("APPDATA", Path.home())) / ".nebula"
MINECRAFT = DATOS / "minecraft"          # versiones, librerías, assets y Java (compartido entre proyectos)
INSTANCIAS = DATOS / "instancias"        # una carpeta de juego por proyecto (mods, config, capturas...)
CUENTA = DATOS / "cuenta.bin"            # token de Microsoft cifrado con DPAPI (solo lo abre tu usuario de Windows)
PREFERENCIAS = DATOS / "preferencias.json"

for d in (DATOS, MINECRAFT, INSTANCIAS):
    d.mkdir(parents=True, exist_ok=True)


def leer_json(ruta: Path, defecto):
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defecto


def config() -> dict:
    """config.json junto al launcher: client_id de Azure, redirect y (más adelante) el panel de cuentas."""
    return leer_json(RAIZ / "config.json", {})


def preferencias() -> dict:
    p = {"ram_gb": 6, "opcionales": False}
    p.update(leer_json(PREFERENCIAS, {}))
    return p


def guardar_preferencias(p: dict) -> None:
    PREFERENCIAS.write_text(json.dumps(p, indent=2), encoding="utf-8")


def proyectos() -> list:
    """Proyectos que ve este jugador. Hasta que exista el panel de cuentas, salen de proyectos.json."""
    if (RAIZ / "proyectos.json").exists():
        return leer_json(RAIZ / "proyectos.json", [])
    return leer_json(RAIZ / "proyectos.ejemplo.json", [])   # el que viene en el repositorio
