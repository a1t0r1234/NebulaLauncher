"""Inicio de sesión con Microsoft (solo cuentas con Minecraft: Java Edition comprado).

El token de renovación se guarda cifrado con DPAPI de Windows: solo lo puede abrir el mismo usuario en el mismo PC.
"""
import ctypes
import ctypes.wintypes as wt
import json

import minecraft_launcher_lib as mll

from . import ajustes


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wt.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _dpapi(datos: bytes, cifrar: bool) -> bytes:
    entrada = _Blob(len(datos), ctypes.cast(ctypes.create_string_buffer(datos, len(datos)), ctypes.POINTER(ctypes.c_char)))
    salida = _Blob()
    f = ctypes.windll.crypt32.CryptProtectData if cifrar else ctypes.windll.crypt32.CryptUnprotectData
    if not f(ctypes.byref(entrada), None, None, None, None, 0, ctypes.byref(salida)):
        raise OSError("DPAPI falló")
    try:
        return ctypes.string_at(salida.pbData, salida.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(salida.pbData)


def _cliente():
    c = ajustes.config()
    cid = c.get("client_id", "")
    if not cid or cid.startswith("PON_AQUI"):
        raise RuntimeError("Falta el client_id de Azure en config.json. Hay que registrar la app de Microsoft primero.")
    return cid, c.get("redirect_uri", "https://login.microsoftonline.com/common/oauth2/nativeclient")


def datos_login():
    """URL para abrir en la ventana de Microsoft, más el estado y el verificador PKCE."""
    cid, redirect = _cliente()
    url, estado, verificador = mll.microsoft_account.get_secure_login_data(cid, redirect)
    return url, estado, verificador


def es_redireccion(url: str) -> bool:
    _, redirect = _cliente()
    return url.startswith(redirect) and mll.microsoft_account.url_contains_auth_code(url)


def completar(url: str, estado: str, verificador: str) -> dict:
    cid, redirect = _cliente()
    codigo = mll.microsoft_account.parse_auth_code_url(url, estado)
    ms = mll.microsoft_account.get_authorization_token(cid, None, redirect, codigo, verificador)
    return _minecraft(ms)


def _minecraft(ms: dict) -> dict:
    """Microsoft → Xbox Live → XSTS → Minecraft, comprobando cada paso para dar el motivo real si algo falla."""
    if "access_token" not in ms:
        raise RuntimeError("Microsoft no ha dado acceso: " + str(ms.get("error_description", ms))[:200])
    xbl = mll.microsoft_account.authenticate_with_xbl(ms["access_token"])
    xsts = mll.microsoft_account.authenticate_with_xsts(xbl["Token"])
    if "XErr" in xsts:
        motivos = {2148916233: "Esta cuenta de Microsoft no tiene perfil de Xbox. Entra una vez en minecraft.net o xbox.com para crearlo.",
                   2148916238: "La cuenta es de menor de edad y tiene que estar en una familia de Microsoft."}
        raise RuntimeError(motivos.get(xsts["XErr"], f"Xbox Live ha rechazado la cuenta (código {xsts['XErr']})."))
    uhs = xbl["DisplayClaims"]["xui"][0]["uhs"]
    mc = mll.microsoft_account.authenticate_with_minecraft(uhs, xsts["Token"])
    _registro("minecraft", {k: v for k, v in mc.items() if k != "access_token"})
    if "access_token" not in mc:
        texto = json.dumps(mc)
        if "Invalid app registration" in texto or "AppRegInfo" in texto:
            raise RuntimeError("Microsoft ha aceptado la sesión, pero Mojang aún no ha aprobado el launcher. Hay que esperar a que acepten el formulario.")
        raise RuntimeError("Minecraft ha rechazado el inicio de sesión: " + texto[:200])
    perfil = mll.microsoft_account.get_profile(mc["access_token"])
    _registro("perfil", {k: v for k, v in perfil.items() if k in ("id", "name", "error", "errorMessage")})
    if "name" not in perfil:
        raise RuntimeError("Esta cuenta de Microsoft no tiene Minecraft: Java Edition.")
    _guardar(ms)
    return {"nombre": perfil["name"], "uuid": perfil["id"], "token": mc["access_token"]}


def _registro(paso: str, datos) -> None:
    """Deja en %APPDATA%/.nebula/login.log la respuesta de cada paso (sin tokens) para poder ver qué falla."""
    with open(ajustes.DATOS / "login.log", "a", encoding="utf-8") as f:
        f.write(f"{paso}: {json.dumps(datos, ensure_ascii=False)[:500]}" + "\n")


def renovar() -> dict | None:
    """Sesión guardada → sesión nueva. None si no hay cuenta o el token ya no vale."""
    if not ajustes.CUENTA.exists():
        return None
    try:
        guardado = json.loads(_dpapi(ajustes.CUENTA.read_bytes(), False))
        cid, redirect = _cliente()
        ms = mll.microsoft_account.refresh_authorization_token(cid, None, redirect, guardado["refresh_token"])
        return _minecraft(ms)
    except Exception:
        return None


def cerrar_sesion() -> None:
    ajustes.CUENTA.unlink(missing_ok=True)


def _guardar(r) -> None:
    ajustes.CUENTA.write_bytes(_dpapi(json.dumps({"refresh_token": r["refresh_token"]}).encode(), True))
