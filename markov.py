"""Modelo de Markov de orden K sobre caracteres."""
import random
from collections import Counter, defaultdict


def limpiar(texto: str) -> str:
    return " ".join(texto.split())


def construir_modelo(texto: str, k: int) -> dict:
    """llave (K caracteres) -> Counter({siguiente_caracter: veces})."""
    modelo = defaultdict(Counter)
    for i in range(len(texto) - k):
        modelo[texto[i:i + k]][texto[i + k]] += 1
    return modelo


def generar(texto: str, k: int, n: int) -> str:
    """Genera n caracteres; los primeros K son los K primeros del texto."""
    modelo = construir_modelo(texto, k)
    salida = texto[:k]
    llaves = list(modelo)
    while len(salida) < n:
        llave = salida[len(salida) - k:] if k else ""
        opciones = modelo.get(llave)
        if not opciones:                 # callejón sin salida: llave nueva
            llave = random.choice(llaves)
            opciones = modelo[llave]
        chars, pesos = zip(*opciones.items())
        salida += random.choices(chars, weights=pesos)[0]
    return salida[:n]


def frecuencias_ktuplas(texto: str, k: int) -> Counter:
    """Frecuencia de cada K-tupla. Para K=0 se cuentan caracteres individuales."""
    m = max(k, 1)
    return Counter(texto[i:i + m] for i in range(len(texto) - m + 1))