"""Cifrado César extendido a un alfabeto de 74 caracteres."""
import math
import unicodedata

ALFABETO = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789_-.áéíóú?!¿¡")
N = len(ALFABETO)
_INDICE = {c: i for i, c in enumerate(ALFABETO)}


def _desplazar(mensaje: str, k: int) -> str:
    """Desplaza k posiciones cada carácter del alfabeto.
    Los caracteres fuera del alfabeto (espacios, comas, etc.) no cambian."""
    return "".join(
        ALFABETO[(_INDICE[c] + k) % N] if c in _INDICE else c for c in mensaje
    )


def cifrar(mensaje: str, k: int) -> str:
    return _desplazar(mensaje, k)


def descifrar_con_clave(mensaje: str, k: int) -> str:
    return _desplazar(mensaje, -k)


# Frecuencias aproximadas de letras en español (%).
_FREQ = dict(zip("eaosrnidlctumpbhqygvjfzxkwñ", [
    13.7, 12.5, 8.7, 8.0, 6.9, 6.7, 6.3, 5.9, 5.0, 4.7, 4.6, 3.9, 2.9, 2.5,
    1.4, 1.2, 0.9, 0.9, 0.9, 0.9, 0.5, 0.5, 0.5, 0.2, 0.1, 0.1, 0.3]))


def _sin_tilde(c: str) -> str:
    return unicodedata.normalize("NFD", c)[0]


def _puntaje(texto: str) -> float:
    """Log-verosimilitud aproximada de que 'texto' sea español."""
    total, previo_letra = 0.0, False
    for c in texto:
        base = _sin_tilde(c).lower()
        if base in _FREQ and c.isalpha():
            p = _FREQ[base] / 100
            if c.isupper() and previo_letra:      # mayúscula a mitad de palabra
                p *= 0.02
            if c in "áéíóú":
                p *= 0.5
            total += math.log(p)
            previo_letra = True
        else:
            if c in _INDICE:                      # dígito o símbolo
                total += math.log(0.01)
            previo_letra = False
    return total


def descifrar(mensaje: str, top: int = 3):
    """Prueba los N-1 desplazamientos posibles y devuelve los `top` más
    probables como lista de (desplazamiento, texto, puntaje)."""
    candidatos = []
    for k in range(1, N):
        t = descifrar_con_clave(mensaje, k)
        candidatos.append((k, t, _puntaje(t)))
    candidatos.sort(key=lambda x: x[2], reverse=True)
    return candidatos[:top]