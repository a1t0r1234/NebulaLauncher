"""Estado de Discord ("Jugando a CraftTerra") mientras el juego está abierto.

Habla con la app de Discord del propio PC por su tubería local (\\\\.\\pipe\\discord-ipc-N), sin librerías extra.
Si Discord no está abierto, o algo falla, no pasa nada: el juego se abre igual.
"""
import json
import os
import struct
import time
import uuid


ID_APLICACION = "1574191035918061758"   # aplicación "CraftTerra" del Developer Portal (no es secreto)
LOGO_GRANDE = "minecraft_title_3_"        # imagen subida en Rich Presence → Art Assets


class Presencia:
    def __init__(self):
        self._tubo = None

    def _enviar(self, op: int, datos: dict) -> dict:
        cuerpo = json.dumps(datos).encode("utf-8")
        self._tubo.write(struct.pack("<II", op, len(cuerpo)) + cuerpo)
        self._tubo.flush()
        cabecera = self._tubo.read(8)
        if len(cabecera) < 8:
            raise OSError("Discord cerró la conexión")
        _, largo = struct.unpack("<II", cabecera)
        return json.loads(self._tubo.read(largo).decode("utf-8"))

    def _conectar(self) -> bool:
        if os.name != "nt":
            return False
        for n in range(10):
            try:
                self._tubo = open(rf"\\.\pipe\discord-ipc-{n}", "r+b", buffering=0)
            except OSError:
                continue
            try:
                r = self._enviar(0, {"v": 1, "client_id": ID_APLICACION})
                if r.get("evt") == "READY":
                    return True
            except (OSError, ValueError):
                pass
            self.cerrar()
        return False

    def jugando(self, proyecto: dict) -> bool:
        """Pone "Jugando a CraftTerra" con el logo y el tiempo desde ahora. Devuelve si se pudo."""
        try:
            if not self._tubo and not self._conectar():
                return False
            actividad = {
                "details": "La era del Rey Oscuro",
                "state": "En el servidor",
                "timestamps": {"start": int(time.time())},
                "assets": {"large_image": LOGO_GRANDE, "large_text": "CraftTerra · Nebula Studios"},
            }
            r = self._enviar(1, {"cmd": "SET_ACTIVITY", "nonce": str(uuid.uuid4()),
                                 "args": {"pid": os.getpid(), "activity": actividad}})
            return r.get("evt") != "ERROR"
        except (OSError, ValueError):
            self.cerrar()
            return False

    def cerrar(self):
        """Al cerrar la conexión, Discord quita el estado solo."""
        if self._tubo:
            try:
                self._tubo.close()
            except OSError:
                pass
        self._tubo = None
