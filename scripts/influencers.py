#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Identificación de influencers - orden voraz por grado + BFS de alcance
Curso: Complejidad Algorítmica (UPC) - Hito 2

Idea: el grado (número de amigos) ya da un primer candidato inmediato de
difusión, pero dos usuarios con el mismo grado no necesariamente llegan
igual de lejos: uno puede estar conectado a un grupo muy cerrado y otro a
puentes entre comunidades. Para refinar el ranking se calcula, con un BFS
de dos saltos, cuántos usuarios distintos alcanza cada candidato (amigos +
amigos de sus amigos), que es una medida barata de alcance real sin tener
que recorrer todo el grafo (que, al ser conexo, daría el mismo número para
casi todos).

Complejidad: ordenar por grado es O(V log V). El BFS de alcance, limitado a
2 saltos, cuesta O(V+E) en el peor caso por cada nodo; sobre los V nodos
(o sobre los top-N candidatos, si se usa --top-grado), el costo total es
O(V·(V+E)) en el peor caso.

Uso:
    python scripts/influencers.py --ego 1684 --top 10
    python scripts/influencers.py --ego 1684 --top 10 --top-grado 50
"""

import argparse
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_grafo import cargar_ego  # noqa: E402


def alcance_bfs(G, nodo, saltos=2):
    """BFS por niveles desde `nodo`, limitado a `saltos` niveles.

    Devuelve (alcance_total, alcance_por_nivel), donde alcance_por_nivel es
    una lista como [amigos_directos, amigos_de_amigos, ...].
    """
    visitado = {nodo}
    nivel_actual = [nodo]
    alcance_por_nivel = []

    for _ in range(saltos):
        siguiente_nivel = []
        for u in nivel_actual:
            for v in G.neighbors(u):
                if v not in visitado:
                    visitado.add(v)
                    siguiente_nivel.append(v)
        alcance_por_nivel.append(len(siguiente_nivel))
        if not siguiente_nivel:
            break
        nivel_actual = siguiente_nivel

    return len(visitado) - 1, alcance_por_nivel  # -1: no contar al propio nodo


def ranking_influencers(G, top=10, candidatos_por_grado=None, saltos=2):
    """Ordena los nodos de forma voraz por grado y refina los `candidatos_por_grado`
    primeros (o todos, si no se indica) con su alcance real por BFS.

    Devuelve una lista de dicts, ordenada por alcance descendente (y por
    grado como desempate), con los `top` mejores.
    """
    por_grado = sorted(G.nodes(data="grado"), key=lambda nv: -nv[1])
    if candidatos_por_grado is not None:
        por_grado = por_grado[:candidatos_por_grado]

    filas = []
    for nodo, grado in por_grado:
        total, por_nivel = alcance_bfs(G, nodo, saltos=saltos)
        filas.append({
            "nodo": nodo,
            "grado": grado,
            "alcance_total": total,
            "alcance_por_nivel": por_nivel,
            "circulo_real": G.nodes[nodo]["circulo_real"],
        })

    filas.sort(key=lambda f: (-f["alcance_total"], -f["grado"]))
    return filas[:top]


def main():
    ap = argparse.ArgumentParser(description="Rankea influencers por grado + alcance BFS.")
    ap.add_argument("--ego", type=int, required=True, help="id de la ego-red (107, 1684, 1912)")
    ap.add_argument("--top", type=int, default=10, help="cuántos influencers listar")
    ap.add_argument("--top-grado", type=int, default=None,
                     help="refinar solo entre los N de mayor grado (si se omite, se refinan todos)")
    ap.add_argument("--saltos", type=int, default=2, help="profundidad del BFS de alcance")
    args = ap.parse_args()

    G, _prob = cargar_ego(args.ego)
    filas = ranking_influencers(G, top=args.top, candidatos_por_grado=args.top_grado, saltos=args.saltos)

    print(f"Ego-red {args.ego}: top {len(filas)} influencers (BFS a {args.saltos} saltos)\n")
    print(f"{'Nodo':>8} {'Grado':>7} {'Alcance':>9}  Alcance por nivel   Círculo real")
    for f in filas:
        niveles = " -> ".join(str(n) for n in f["alcance_por_nivel"])
        print(f"{f['nodo']:>8} {f['grado']:>7} {f['alcance_total']:>9}  [{niveles}]   {f['circulo_real']}")


if __name__ == "__main__":
    main()
