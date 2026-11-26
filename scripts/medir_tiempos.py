#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mide el tiempo de ejecucion de cada rama (comunidades, influencers, propagacion)
sobre las tres ego-redes (107, 1684, 1912). Genera una tabla lista para el Anexo C.

Uso:
    python scripts/medir_tiempos.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common_grafo import cargar_ego
from comunidades import detectar_comunidades
from influencers import ranking_influencers
from propagacion import alcance_por_rondas, camino_mas_probable

EGOS = [107, 1684, 1912]

def medir(funcion, *args, repeticiones=3):
    """Ejecuta la funcion N veces y devuelve el tiempo promedio en milisegundos."""
    tiempos = []
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        funcion(*args)
        fin = time.perf_counter()
        tiempos.append((fin - inicio) * 1000)
    return sum(tiempos) / len(tiempos)

def main():
    print("=" * 70)
    print("MEDICION DE TIEMPOS DE EJECUCION (promedio de 3 corridas, en ms)")
    print("=" * 70)
    print()
    print(f"{'Ego-red':<10} {'V':<6} {'E':<8} {'Comunidades':<14} {'Influencers':<14} {'Propagacion':<14}")
    print("-" * 70)

    for ego in EGOS:
        G, prob = cargar_ego(ego)
        V = G.number_of_nodes()
        E = G.number_of_edges()

        t_com = medir(detectar_comunidades, G, 10)
        t_inf = medir(ranking_influencers, G, 10)
        t_pro = medir(alcance_por_rondas, G, ego)

        print(f"{ego:<10} {V:<6} {E:<8} {t_com:>10.2f} ms  {t_inf:>10.2f} ms  {t_pro:>10.2f} ms")

    print()
    print("=" * 70)
    print("VERIFICACION EMPIRICA DE LA COMPLEJIDAD")
    print("=" * 70)
    print()
    print("Comunidades es O(E log E):")
    for ego in EGOS:
        G, _ = cargar_ego(ego)
        E = G.number_of_edges()
        import math
        print(f"  ego {ego}: E = {E:>6}, E*log(E) = {E * math.log(E):>12.0f}")

    print()
    print("Propagacion (BFS) es O(V + E):")
    for ego in EGOS:
        G, _ = cargar_ego(ego)
        V = G.number_of_nodes()
        E = G.number_of_edges()
        print(f"  ego {ego}: V+E = {V+E:>6}")

if __name__ == "__main__":
    main()
