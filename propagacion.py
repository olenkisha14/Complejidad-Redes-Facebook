#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulación de propagación - BFS por niveles + Dijkstra de camino más probable
Curso: Complejidad Algorítmica (UPC) - Hito 2

Idea: se modela la difusión de un mensaje como un proceso de contagio
dirigido. Cada arista (u, v) tiene una probabilidad p(u, v) = 1/grado(v) de
que u contagie a v (cascada ponderada, Kempe, Kleinberg & Tardos, 2003).

Dos preguntas distintas se responden con dos algoritmos distintos:

1) "¿A quién llega el mensaje y en cuántos pasos?" -> BFS por niveles desde
   el nodo origen, siguiendo solo aristas con p(u, v) > 0 (todas las
   existentes lo cumplen). Cada nivel del BFS es una "ronda" de contagio.
   Complejidad: O(V + E).

2) "¿Cuál es el camino más probable de contagio entre dos nodos?" -> como
   las probabilidades se MULTIPLICAN a lo largo de un camino (no se suman),
   no se puede usar Dijkstra directamente sobre p(u, v): hay que convertir
   el producto en una suma con logaritmos. Se usa el peso
   peso(u, v) = log(1/p(u, v)), que es siempre >= 0 (porque 0 < p <= 1) y
   que, al sumarlo a lo largo de un camino, equivale a log(1 / producto de
   probabilidades). Minimizar esa suma con Dijkstra es lo mismo que
   maximizar el producto de probabilidades del camino, es decir, encontrar
   el camino "más fácil" de contagio, sin usar el signo "-" en la fórmula.
   Complejidad: O(E log V) con heap binario.

Uso:
    python scripts/propagacion.py --ego 1684 --origen 1684 --alcance
    python scripts/propagacion.py --ego 1684 --origen 1684 --destino 3363 --camino
"""

import argparse
import math
import sys
from collections import deque
from heapq import heappush, heappop
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_grafo import cargar_ego  # noqa: E402


def alcance_por_rondas(G, origen):
    """BFS por niveles desde `origen`: cada nivel es una ronda de contagio.

    Devuelve (orden_de_contagio, rondas), donde orden_de_contagio es una
    lista [(nodo, ronda), ...] en el orden en que se "contagian", y rondas
    es un dict {ronda: [nodos]} para un resumen por ronda.
    """
    visitado = {origen}
    ronda_de = {origen: 0}
    cola = deque([origen])
    orden = [(origen, 0)]

    while cola:
        u = cola.popleft()
        for v in G.neighbors(u):
            if v not in visitado:
                visitado.add(v)
                ronda_de[v] = ronda_de[u] + 1
                orden.append((v, ronda_de[v]))
                cola.append(v)

    rondas = {}
    for nodo, r in orden:
        rondas.setdefault(r, []).append(nodo)
    return orden, rondas


def camino_mas_probable(G, prob, origen, destino):
    """Dijkstra sobre peso(u, v) = log(1/p(u, v)) para hallar el camino de
    mayor probabilidad de contagio entre `origen` y `destino`.

    Devuelve (camino, probabilidad_total) o (None, 0.0) si no hay camino.
    """
    dist = {origen: 0.0}
    previo = {}
    visto = set()
    heap = [(0.0, origen)]

    while heap:
        d_u, u = heappop(heap)
        if u in visto:
            continue
        visto.add(u)
        if u == destino:
            break

        for v in G.neighbors(u):
            if v in visto:
                continue
            p = prob[(u, v)]
            peso = math.log(1.0 / p)  # siempre >= 0, sin usar "-log(p)"
            nueva_dist = d_u + peso
            if v not in dist or nueva_dist < dist[v]:
                dist[v] = nueva_dist
                previo[v] = u
                heappush(heap, (nueva_dist, v))

    if destino not in dist:
        return None, 0.0

    # Reconstruir camino desde destino hacia origen.
    camino = [destino]
    while camino[-1] != origen:
        camino.append(previo[camino[-1]])
    camino.reverse()

    probabilidad_total = math.exp(-dist[destino])  # producto de las p(u,v)
    return camino, probabilidad_total


def main():
    ap = argparse.ArgumentParser(description="Simula propagación: alcance por rondas o camino más probable.")
    ap.add_argument("--ego", type=int, required=True, help="id de la ego-red (107, 1684, 1912)")
    ap.add_argument("--origen", type=int, required=True, help="nodo desde el que inicia el contagio")
    ap.add_argument("--destino", type=int, default=None, help="nodo destino (requerido con --camino)")
    ap.add_argument("--alcance", action="store_true", help="mostrar el alcance por rondas (BFS)")
    ap.add_argument("--camino", action="store_true", help="mostrar el camino más probable (Dijkstra)")
    ap.add_argument("--max-rondas", type=int, default=5, help="cuántas rondas mostrar en --alcance")
    args = ap.parse_args()

    G, prob = cargar_ego(args.ego)

    if not args.alcance and not args.camino:
        args.alcance = True  # por defecto, mostrar alcance

    if args.alcance:
        orden, rondas = alcance_por_rondas(G, args.origen)
        total = len(orden)
        print(f"Ego-red {args.ego}: contagio desde {args.origen} alcanza {total}/{G.number_of_nodes()} nodos\n")
        for r in sorted(rondas)[:args.max_rondas]:
            nodos_r = rondas[r]
            print(f"Ronda {r}: {len(nodos_r)} nodo(s) nuevos" + (f" (ej: {nodos_r[:5]})" if r > 0 else " (origen)"))
        if len(rondas) > args.max_rondas:
            print(f"... ({len(rondas) - args.max_rondas} ronda(s) más)")
        print()

    if args.camino:
        if args.destino is None:
            print("Error: --camino requiere --destino", file=sys.stderr)
            sys.exit(1)
        camino, probabilidad = camino_mas_probable(G, prob, args.origen, args.destino)
        if camino is None:
            print(f"No existe camino de {args.origen} a {args.destino}.")
        else:
            ruta = " -> ".join(str(n) for n in camino)
            print(f"Camino más probable {args.origen} -> {args.destino} ({len(camino) - 1} saltos):")
            print(f"  {ruta}")
            print(f"  probabilidad total de contagio: {probabilidad:.6f} ({probabilidad * 100:.4f}%)")


if __name__ == "__main__":
    main()
