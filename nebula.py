"""Nebula Launcher — launcher de los proyectos de Nebula's Studio's (solo Minecraft: Java Edition con cuenta Microsoft).

Uso: python nebula.py            (normal)
     python nebula.py --vista    (ver la pantalla principal sin iniciar sesión; Jugar sigue pidiendo una cuenta real)
"""
import json
import sys
import threading
import time
import traceback

import webview

from motor import ajustes, cuenta, estado, instalador


class Api:
    def __init__(self, vista=False):
        self._vista = vista
        self._ventana = None
        self._sesion = None
        self._ocupado = False

    # ---- ventana ----
    def minimizar(self):
        self._ventana.minimize()

    def cerrar(self):
        self._ventana.destroy()

    def _js(self, funcion, *args):
        self._ventana.evaluate_js(f"{funcion}({','.join(json.dumps(a) for a in args)})")

    # ---- datos ----
    def inicio(self):
        cfg = ajustes.config()
        listo = bool(cfg.get("client_id")) and not cfg["client_id"].startswith("PON_AQUI")
        if listo and self._sesion is None:
            self._sesion = cuenta.renovar()
        sesion = {"nombre": self._sesion["nombre"], "uuid": self._sesion["uuid"]} if self._sesion else None
        if sesion is None and self._vista:
            # solo para ver la interfaz: no hay token, así que no se puede jugar con esto
            sesion = {"nombre": "Vista previa", "uuid": "00000000000000000000000000000000"}
        return {
            "proyectos": ajustes.proyectos(),
            "sesion": sesion,
            "preferencias": ajustes.preferencias(),
            "microsoft_listo": listo,
        }

    def estado(self, direccion):
        return estado.consultar(direccion)

    def guardar_preferencias(self, p):
        actual = ajustes.preferencias()
        actual.update({"ram_gb": max(2, min(16, int(p.get("ram_gb", 6)))), "opcionales": bool(p.get("opcionales"))})
        ajustes.guardar_preferencias(actual)
        return actual

    # ---- cuenta de Microsoft ----
    def entrar(self):
        try:
            url, est, verif = cuenta.datos_login()
        except RuntimeError as e:
            return {"error": str(e)}
        ms = webview.create_window("Iniciar sesión con Microsoft", url, width=520, height=680)
        fin = time.time() + 600
        while time.time() < fin:
            time.sleep(0.4)
            try:
                actual = ms.get_current_url() or ""
            except Exception:
                return {"error": "Has cerrado la ventana de Microsoft."}
            if cuenta.es_redireccion(actual):
                ms.destroy()
                try:
                    self._sesion = cuenta.completar(actual, est, verif)
                except Exception as e:
                    return {"error": str(e)}
                return {"nombre": self._sesion["nombre"], "uuid": self._sesion["uuid"]}
        ms.destroy()
        return {"error": "Se acabó el tiempo para iniciar sesión."}

    def salir(self):
        cuenta.cerrar_sesion()
        self._sesion = None
        return True

    # ---- jugar ----
    def jugar(self, id_proyecto):
        if self._ocupado:
            return {"error": "Ya se está preparando el juego."}
        if not self._sesion:
            return {"error": "Inicia sesión con tu cuenta de Microsoft."}
        proyecto = next((p for p in ajustes.proyectos() if p["id"] == id_proyecto), None)
        if not proyecto:
            return {"error": "No tienes acceso a ese proyecto."}
        self._ocupado = True
        threading.Thread(target=self._jugar, args=(proyecto,), daemon=True).start()
        return {"ok": True}

    def _jugar(self, proyecto):
        texto = {"t": ""}

        def aviso(t, hecho, total):
            if t:
                texto["t"] = t
            self._js("progreso", texto["t"], hecho, total)

        try:
            version = instalador.preparar(proyecto, aviso)
            nueva = cuenta.renovar()  # token recién renovado para que no caduque a mitad de partida
            if nueva:
                self._sesion = nueva
            juego = instalador.lanzar(proyecto, version, self._sesion)
            self._js("juegoAbierto")
            self._ventana.minimize()
            juego.wait()
            self._js("juegoCerrado", juego.returncode)
        except Exception as e:
            traceback.print_exc()
            self._js("fallo", str(e))
        finally:
            self._ocupado = False


def main():
    api = Api(vista="--vista" in sys.argv)
    api._ventana = webview.create_window(
        "Nebula Launcher", str(ajustes.RAIZ / "ui" / "index.html"), js_api=api,
        width=1280, height=760, min_size=(1024, 640), frameless=True, easy_drag=False, background_color="#07060f")
    webview.start(debug=False)


if __name__ == "__main__":
    main()
