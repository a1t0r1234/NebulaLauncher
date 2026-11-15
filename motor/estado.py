"""Consulta si un servidor de Minecraft está abierto (el mismo "ping" que la lista de servidores del juego)."""
import json
import socket
import struct
import time


def _varint(n: int) -> bytes:
    out = b""
    while True:
        b = n & 0x7F
        n >>= 7
        out += struct.pack("B", b | (0x80 if n else 0))
        if not n:
            return out


def _leer_varint(s: socket.socket) -> int:
    n = 0
    for i in range(5):
        b = s.recv(1)
        if not b:
            raise ConnectionError("cerrado")
        n |= (b[0] & 0x7F) << (7 * i)
        if not b[0] & 0x80:
            return n
    raise ValueError("varint")


def _resolver(direccion: str):
    host, _, puerto = direccion.partition(":")
    if puerto:
        return host, int(puerto)
    try:  # registro SRV (_minecraft._tcp), como hace el juego
        import dns.resolver  # opcional
        r = dns.resolver.resolve(f"_minecraft._tcp.{host}", "SRV")[0]
        return str(r.target).rstrip("."), r.port
    except Exception:
        return host, 25565


def consultar(direccion: str, espera: float = 4.0) -> dict:
    host, puerto = _resolver(direccion)
    inicio = time.time()
    try:
        with socket.create_connection((host, puerto), timeout=espera) as s:
            s.settimeout(espera)
            hs = _varint(0) + _varint(774) + _varint(len(host)) + host.encode() + struct.pack(">H", puerto) + _varint(1)
            s.sendall(_varint(len(hs)) + hs)
            s.sendall(_varint(1) + _varint(0))
            _leer_varint(s)
            _leer_varint(s)
            largo = _leer_varint(s)
            datos = b""
            while len(datos) < largo:
                trozo = s.recv(largo - len(datos))
                if not trozo:
                    break
                datos += trozo
        info = json.loads(datos)
        jug = info.get("players", {})
        return {"abierto": True, "online": jug.get("online", 0), "max": jug.get("max", 0),
                "ping": int((time.time() - inicio) * 1000)}
    except Exception:
        return {"abierto": False}
