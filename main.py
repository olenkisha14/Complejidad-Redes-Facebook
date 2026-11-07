#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - Integración de los tres algoritmos sobre una ego-red
Curso: Complejidad Algorítmica (UPC) - Hito 2

Sigue el flujo descrito en la Figura 3 del informe (Entrada -> Pesos ->
3 ramas -> Salida):

    1. Entrada:  CSV de nodos y aristas de una ego-red (generados por
                 preparar_datos.py).
    2. Pesos:    ya vienen calculados en los CSV (dist_jaccard y las
                 probabilidades direccionales); common_grafo.cargar_ego
                 los arma en un grafo de NetworkX + un diccionario de
                 probabilidades.
    3. Tres ramas, cada una con su propio algoritmo:
         a) Comunidades  (Kruskal + UFDS)       -> comunidades.py
         b) Influencers   (voraz por grado + BFS) -> influencers.py
         c) Propagación   (BFS + Dijkstra)       -> propagacion.py
    4. Salida:   un resumen impreso en consola con los resultados de las
                 tres ramas para la ego-red pedida.

Uso:
    python scripts/main.py --ego 1684
    python scripts/main.py --ego 1684 --k 17 --top-influencers 10
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_grafo import cargar_ego  # noqa: E402
from comunidades import detectar_comunidades, resumen_por_comunidad  # noqa: E402
from influencers import ranking_influencers  # noqa: E402
from propagacion import alcance_por_rondas, camino_mas_probable  # noqa: E402


def separador(titulo):
    print("\n" + "=" * 60)
    print(titulo)
    print("=" * 60)


def main():
    ap = argparse.ArgumentParser(
        description="Corre las tres ramas de análisis (comunidades, influencers, propagación) sobre una ego-red."
    )
    ap.add_argument("--ego", type=int, required=True, help="id de la ego-red (107, 1684, 1912)")
    ap.add_argument("--k", type=int, default=10, help="número de comunidades a formar")
    ap.add_argument("--top-influencers", type=int, default=5, help="cuántos influencers listar")
    ap.add_argument("--origen", type=int, default=None,
                     help="nodo origen para la propagación (por defecto, el nodo con mayor grado)")
    ap.add_argument("--destino", type=int, default=None,
                     help="nodo destino para el camino más probable (opcional)")
    args = ap.parse_args()

    # 1-2. Entrada + Pesos.
    G, prob = cargar_ego(args.ego)
    separador(f"ENTRADA: ego-red {args.ego}")
    print(f"{G.number_of_nodes()} nodos, {G.number_of_edges()} aristas (pesos ya calculados en los CSV)")

    origen = args.origen if args.origen is not None else max(G.nodes(data="grado"), key=lambda nv: nv[1])[0]

    # 3a. Rama Comunidades.
    separador("RAMA 1: Comunidades (Kruskal + UFDS)")
    comunidad = detectar_comunidades(G, args.k)
    filas_com = resumen_por_comunidad(G, comunidad)
    print(f"{len(filas_com)} comunidades formadas (k pedido: {args.k})")
    for f in filas_com[:5]:
        print(f"  comunidad {f['comunidad']}: {f['tamano']} nodos, "
              f"círculo más común = {f['circulo_real_mas_comun']} ({f['pureza']:.1%} pureza)")
    if len(filas_com) > 5:
        print(f"  ... ({len(filas_com) - 5} comunidad(es) más, muchas de tamaño 1 por el efecto cadena)")

    # 3b. Rama Influencers.
    separador("RAMA 2: Influencers (voraz por grado + BFS de alcance)")
    filas_inf = ranking_influencers(G, top=args.top_influencers)
    for f in filas_inf:
        print(f"  nodo {f['nodo']}: grado={f['grado']}, alcance a 2 saltos={f['alcance_total']}, "
              f"círculo={f['circulo_real']}")

    # 3c. Rama Propagación.
    separador(f"RAMA 3: Propagación (BFS + Dijkstra), origen = {origen}")
    orden, rondas = alcance_por_rondas(G, origen)
    print(f"Alcance total desde {origen}: {len(orden)}/{G.number_of_nodes()} nodos en {len(rondas) - 1} ronda(s)")
    if args.destino is not None:
        camino, probabilidad = camino_mas_probable(G, prob, origen, args.destino)
        if camino is None:
            print(f"No existe camino de {origen} a {args.destino}.")
        else:
            ruta = " -> ".join(str(n) for n in camino)
            print(f"Camino más probable {origen} -> {args.destino}: {ruta} "
                  f"(probabilidad total: {probabilidad:.6f})")

    # 4. Salida.
    separador(f"SALIDA: resumen ego-red {args.ego}")
    print(f"- Comunidades: {len(filas_com)} grupos (dominadas por 1 comunidad grande + singletons)")
    print(f"- Influencer principal: nodo {filas_inf[0]['nodo']} (grado {filas_inf[0]['grado']})")
    print(f"- Propagación desde {origen}: alcanza a toda la red en {len(rondas) - 1} rondas")


if __name__ == "__main__":
    main()
