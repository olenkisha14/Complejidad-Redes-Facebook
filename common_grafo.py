#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilidades compartidas para cargar una ego-red ya procesada.

Este módulo NO implementa ningún algoritmo de análisis (eso vive en
comunidades.py, influencers.py y propagacion.py). Solo lee los CSV que
genera scripts/preparar_datos.py y arma, a partir de ellos, un grafo de
NetworkX y un diccionario de probabilidades dirigidas, listos para que
cada algoritmo los use.

Uso típico desde otro script:
    from common_grafo import cargar_ego
    G, prob = cargar_ego(1684)
"""

import sys
from pathlib import Path

import networkx as nx
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

RAIZ = Path(__file__).resolve().parent.parent
DIR_PROCESSED = RAIZ / "data" / "processed"


def rutas(ego, dir_datos=None):
    """Encuentra los CSV de una ego-red, acepte la carpeta ego_<id>/ o
    archivos planos nodos_<id>.csv / aristas_<id>.csv (mismo criterio que
    usa scripts/graficar_egos.py, para que cualquiera de las dos
    convenciones funcione)."""
    dir_datos = Path(dir_datos) if dir_datos else DIR_PROCESSED
    carpeta = dir_datos / f"ego_{ego}"
    if carpeta.exists():
        return carpeta / "nodos.csv", carpeta / "aristas.csv"
    return dir_datos / f"nodos_{ego}.csv", dir_datos / f"aristas_{ego}.csv"


def cargar_ego(ego, dir_datos=None):
    """Carga una ego-red como un grafo no dirigido con sus atributos.

    Devuelve:
      G:    nx.Graph. Cada nodo tiene 'grado', 'es_ego', 'circulo_real'.
            Cada arista tiene 'dist_jaccard' (= peso_jaccard, la DISTANCIA
            1 - J, no la similitud) y 'vecinos_comunes'.
      prob: dict {(u, v): probabilidad de que u contagie a v}. Es asimétrico
            (prob[(u, v)] != prob[(v, u)] en general), por eso no se guarda
            como atributo de arista no dirigida.
    """
    f_nodos, f_aristas = rutas(ego, dir_datos)
    if not f_nodos.exists() or not f_aristas.exists():
        raise FileNotFoundError(
            f"No se encontraron los CSV de la ego-red {ego} en {f_nodos.parent}. "
            "Corre antes scripts/preparar_datos.py."
        )

    nodos = pd.read_csv(f_nodos)
    aristas = pd.read_csv(f_aristas)

    G = nx.Graph()
    for fila in nodos.itertuples():
        G.add_node(
            fila.id,
            grado=fila.grado,
            es_ego=bool(fila.es_ego),
            circulo_real=fila.circulo_real,
        )

    prob = {}
    for fila in aristas.itertuples():
        G.add_edge(
            fila.origen,
            fila.destino,
            dist_jaccard=fila.peso_jaccard,
            vecinos_comunes=fila.vecinos_comunes,
        )
        prob[(fila.origen, fila.destino)] = fila.prob_origen_a_destino
        prob[(fila.destino, fila.origen)] = fila.prob_destino_a_origen

    return G, prob


if __name__ == "__main__":
    # Prueba rápida manual: python common_grafo.py 1684
    ego = int(sys.argv[1]) if len(sys.argv) > 1 else 1684
    G, prob = cargar_ego(ego)
    print(f"Ego-red {ego}: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
    u, v = next(iter(G.edges()))
    print(f"Ejemplo de arista ({u}, {v}): dist_jaccard={G[u][v]['dist_jaccard']:.4f}, "
          f"p({u}->{v})={prob[(u, v)]:.4f}, p({v}->{u})={prob[(v, u)]:.4f}")
