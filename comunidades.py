#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detección de comunidades - Kruskal + UFDS (single-linkage clustering)
Curso: Complejidad Algorítmica (UPC) - Hito 2

Idea: las aristas ya tienen una DISTANCIA (dist_jaccard = 1 - Jaccard), no
una similitud. Cuanto más cerca de 0, más amigos en común tienen esos dos
usuarios. Si ordenamos todas las aristas de menor a mayor distancia y las
vamos "uniendo" como en el MST de Kruskal, los usuarios más parecidos
quedan en el mismo grupo desde el principio. En vez de construir el árbol
de expansión mínima completo, nos detenemos apenas quedan k componentes:
eso es exactamente clustering jerárquico de enlace simple (single-linkage),
formulado como un problema de grafos por Zahn (1971).

Complejidad: ordenar las E aristas cuesta O(E log E); cada unión con UFDS
(compresión de camino + unión por rango) cuesta O(α(V)) amortizado, así
que el costo total es O(E log E), dominado por el ordenamiento.

Uso:
    python scripts/comunidades.py --ego 1684 --k 10
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_grafo import cargar_ego  # noqa: E402


class UFDS:
    """Union-Find / Disjoint Set con compresión de camino y unión por rango.

    Cada operación (find o union) cuesta O(α(V)) amortizado, donde α es la
    inversa de Ackermann: en la práctica, prácticamente O(1).
    """

    def __init__(self, elementos):
        self.padre = {x: x for x in elementos}
        self.rango = {x: 0 for x in elementos}
        self.num_componentes = len(elementos)

    def find(self, x):
        # Compresión de camino: cada nodo visitado apunta directo a la raíz,
        # así las siguientes búsquedas por ese camino son casi O(1).
        raiz = x
        while self.padre[raiz] != raiz:
            raiz = self.padre[raiz]
        while self.padre[x] != raiz:
            self.padre[x], x = raiz, self.padre[x]
        return raiz

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False  # ya estaban en el mismo grupo
        # Unión por rango: el árbol más bajo cuelga del más alto, para que
        # el camino hacia la raíz no se alargue innecesariamente.
        if self.rango[ra] < self.rango[rb]:
            ra, rb = rb, ra
        self.padre[rb] = ra
        if self.rango[ra] == self.rango[rb]:
            self.rango[ra] += 1
        self.num_componentes -= 1
        return True


def detectar_comunidades(G, k):
    """Agrupa los nodos de G en k comunidades por enlace simple (Kruskal).

    Devuelve un dict {nodo: id_comunidad}, con id_comunidad en [0, k).
    Si el grafo tiene varias componentes conexas y k es menor que su
    número, no se puede llegar a exactamente k grupos uniendo aristas
    existentes; en ese caso se detiene al unir todas las aristas posibles
    y se devuelven más de k comunidades (una por componente conexa).
    """
    ufds = UFDS(G.nodes())
    # Ordenar las aristas de menor a mayor distancia: O(E log E).
    aristas_ordenadas = sorted(G.edges(data="dist_jaccard"), key=lambda e: e[2])

    for u, v, _dist in aristas_ordenadas:
        if ufds.num_componentes <= k:
            break
        ufds.union(u, v)

    # Reetiquetar las raíces como 0, 1, 2, ... para que el id de comunidad
    # sea fácil de leer.
    raices = {}
    comunidad = {}
    for nodo in G.nodes():
        raiz = ufds.find(nodo)
        if raiz not in raices:
            raices[raiz] = len(raices)
        comunidad[nodo] = raices[raiz]
    return comunidad


def resumen_por_comunidad(G, comunidad):
    """Arma, por comunidad, su tamaño y el círculo real más frecuente
    dentro de ella (para comparar, a simple vista, contra los círculos
    reales etiquetados por el usuario ego)."""
    grupos = {}
    for nodo, c in comunidad.items():
        grupos.setdefault(c, []).append(nodo)

    filas = []
    for c, nodos in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        circulos = [G.nodes[n]["circulo_real"] for n in nodos]
        circulo_top = max(set(circulos), key=circulos.count)
        coincidencia = circulos.count(circulo_top) / len(circulos)
        filas.append({
            "comunidad": c,
            "tamano": len(nodos),
            "circulo_real_mas_comun": circulo_top,
            "pureza": round(coincidencia, 3),
        })
    return filas


def main():
    ap = argparse.ArgumentParser(description="Detecta comunidades con Kruskal + UFDS.")
    ap.add_argument("--ego", type=int, required=True, help="id de la ego-red (107, 1684, 1912)")
    ap.add_argument("--k", type=int, default=10, help="número de comunidades a formar")
    args = ap.parse_args()

    G, _prob = cargar_ego(args.ego)
    comunidad = detectar_comunidades(G, args.k)
    filas = resumen_por_comunidad(G, comunidad)

    print(f"Ego-red {args.ego}: {G.number_of_nodes()} nodos -> {len(filas)} comunidades (k pedido: {args.k})\n")
    print(f"{'Comunidad':>9} {'Tamaño':>7} {'Círculo real más común':>26} {'Pureza':>7}")
    for f in filas:
        print(f"{f['comunidad']:>9} {f['tamano']:>7} {f['circulo_real_mas_comun']:>26} {f['pureza']:>7.1%}")


if __name__ == "__main__":
    main()
