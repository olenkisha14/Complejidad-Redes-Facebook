#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visualización de las tres ego-redes (Sección 3 del informe).

Lee data/processed/ego_<id>/nodos.csv y aristas.csv (generados por
preparar_datos.py) y dibuja cada subgrafo con un layout de fuerzas
(Fruchterman-Reingold, nx.spring_layout) aplicando tres reglas:

  1. Tamaño del nodo  -> proporcional a la raíz del grado global (k).
  2. Color del nodo   -> círculo social real (circulo_real). Se colorean los
                         8 círculos más grandes; el resto va en gris.
  3. Arista           -> grosor y opacidad según la SIMILITUD de Jaccard,
                         que es 1 - peso_jaccard (peso_jaccard es una distancia).

Uso:  python scripts/graficar_egos.py              (una figura por ego-red)
      python scripts/graficar_egos.py --combinada  (las tres en una sola figura)
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

# Carpeta con los CSV; se puede pasar como argumento.
_ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
DIR_DATOS = Path(_ARGS[0]) if len(_ARGS) > 0 else Path("data/processed")
DIR_SALIDA = Path(_ARGS[1]) if len(_ARGS) > 1 else Path("outputs")

EGOS = [107, 1684, 1912]
SEMILLA = 42            # misma semilla que preparar_datos.py -> layout reproducible
MAX_CIRCULOS_COLOR = 8  # más de 8 colores ya no se distinguen a simple vista

PALETA = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
          "#9467bd", "#8c564b", "#e377c2", "#17becf"]
GRIS_OTROS = "#9a9a9a"
GRIS_SIN = "#d9d9d9"
FONDO = "#ffffff"


def rutas(ego):
    """Acepta la estructura del script (ego_<id>/nodos.csv) o archivos planos (nodos_<id>.csv)."""
    carpeta = DIR_DATOS / f"ego_{ego}"
    if carpeta.exists():
        return carpeta / "nodos.csv", carpeta / "aristas.csv"
    return DIR_DATOS / f"nodos_{ego}.csv", DIR_DATOS / f"aristas_{ego}.csv"


def construir_subgrafo(ego):
    f_nodos, f_aristas = rutas(ego)
    nodos = pd.read_csv(f_nodos)
    aristas = pd.read_csv(f_aristas)
    G = nx.Graph()
    for fila in nodos.itertuples():
        G.add_node(fila.id, grado=fila.grado, es_ego=fila.es_ego, circulo=fila.circulo_real)
    for fila in aristas.itertuples():
        G.add_edge(fila.origen, fila.destino, similitud=1 - fila.peso_jaccard)
    return G


def colores_por_circulo(G):
    """Asigna un color a cada uno de los círculos más grandes."""
    conteo = pd.Series(nx.get_node_attributes(G, "circulo")).value_counts()
    principales = [c for c in conteo.index if c != "sin_circulo"][:MAX_CIRCULOS_COLOR]
    mapa = {c: PALETA[i] for i, c in enumerate(principales)}

    def color(c):
        if c == "sin_circulo":
            return GRIS_SIN
        return mapa.get(c, GRIS_OTROS)

    return color, principales, conteo


def dibujar(ego, numero_figura):
    G = construir_subgrafo(ego)
    # k más grande separa mejor los grupos; iterations suficientes para estabilizar.
    pos = nx.spring_layout(G, seed=SEMILLA, k=0.35, iterations=100)
    color, principales, conteo = colores_por_circulo(G)

    fig, ax = plt.subplots(figsize=(10, 10), dpi=200)
    fig.patch.set_facecolor(FONDO)
    ax.set_facecolor(FONDO)

    # Aristas: se dibujan de menor a mayor similitud para que las fuertes queden encima.
    aristas = sorted(G.edges(data="similitud"), key=lambda e: e[2])
    sims = [s for _, _, s in aristas]
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edgelist=[(u, v) for u, v, _ in aristas],
        width=[0.05 + 0.9 * s for s in sims],
        alpha=0.12,
        edge_color=[(0.25, 0.25, 0.25, 0.05 + 0.5 * s) for s in sims],
    )

    # Nodos: primero los que no son ego, luego los egos con borde negro.
    no_egos = [n for n, d in G.nodes(data=True) if not d["es_ego"]]
    egos = [n for n, d in G.nodes(data=True) if d["es_ego"]]
    for lista, borde, ancho in ((no_egos, "white", 0.3), (egos, "black", 1.2)):
        nx.draw_networkx_nodes(
            G, pos, ax=ax, nodelist=lista,
            node_size=[4 + 3.5 * G.nodes[n]["grado"] ** 0.5 for n in lista],
            node_color=[color(G.nodes[n]["circulo"]) for n in lista],
            edgecolors=borde, linewidths=ancho,
        )
    # Etiqueta solo el ego principal.
    x, y = pos[ego]
    ax.annotate(f"ego {ego}", (x, y), xytext=(12, 12), textcoords="offset points",
                fontsize=11, fontweight="bold",
                bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "black", "lw": 0.6})

    # Leyenda de círculos.
    handles = [Line2D([], [], marker="o", ls="", color=PALETA[i], markersize=8,
                      label=f"{c.split('_', 1)[1]} ({conteo[c]} nodos)")
               for i, c in enumerate(principales)]
    # "Otros" incluye círculos pequeños y círculos de otra ego-red (nodos compartidos).
    nodos_otros = int(conteo[[c for c in conteo.index
                              if c != "sin_circulo" and c not in principales]].sum())
    if nodos_otros > 0:
        handles.append(Line2D([], [], marker="o", ls="", color=GRIS_OTROS, markersize=8,
                              label=f"otros círculos ({nodos_otros} nodos)"))
    if "sin_circulo" in conteo:
        handles.append(Line2D([], [], marker="o", ls="", color=GRIS_SIN, markersize=8,
                              label=f"sin círculo ({conteo['sin_circulo']} nodos)"))
    handles.append(Line2D([], [], marker="o", ls="", mfc="white", mec="black", mew=1.2,
                          markersize=8, label="nodo ego"))
    ax.legend(handles=handles, loc="lower left", fontsize=8.5, frameon=True,
              framealpha=0.92, title="Círculo real", title_fontsize=9)

    ax.set_title(f"Ego-red {ego}: {G.number_of_nodes():,} nodos, {G.number_of_edges():,} aristas",
                 fontsize=14, loc="left")
    ax.text(0.0, -0.02,
            "Tamaño del nodo ∝ √grado · color = círculo real · "
            "grosor/opacidad de arista ∝ similitud de Jaccard (1 − peso_jaccard) · "
            f"layout Fruchterman-Reingold (semilla {SEMILLA})",
            transform=ax.transAxes, fontsize=7.5, color="#555555")
    ax.axis("off")
    fig.tight_layout()
    salida = DIR_SALIDA / f"figura{numero_figura}_ego_{ego}.png"
    fig.savefig(salida, facecolor=FONDO)
    plt.close(fig)
    print(f"  [ok] {salida}")


def dibujar_panel(ax, ego, letra):
    """Dibuja una ego-red en un panel de la figura combinada (versión compacta)."""
    G = construir_subgrafo(ego)
    pos = nx.spring_layout(G, seed=SEMILLA, k=0.35, iterations=100)
    color, principales, conteo = colores_por_circulo(G)
    principales = principales[:5]  # en un panel pequeño, 5 colores es el máximo legible

    def color5(c):
        return PALETA[principales.index(c)] if c in principales else (GRIS_SIN if c == "sin_circulo" else GRIS_OTROS)

    aristas = sorted(G.edges(data="similitud"), key=lambda e: e[2])
    sims = [s for _, _, s in aristas]
    nx.draw_networkx_edges(G, pos, ax=ax, edgelist=[(u, v) for u, v, _ in aristas],
                           width=[0.02 + 0.3 * s for s in sims],
                           edge_color=[(0.25, 0.25, 0.25, 0.04 + 0.4 * s) for s in sims])
    no_egos = [n for n, d in G.nodes(data=True) if not d["es_ego"]]
    egos = [n for n, d in G.nodes(data=True) if d["es_ego"]]
    for lista, borde, ancho in ((no_egos, "white", 0.1), (egos, "black", 0.6)):
        nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=lista,
                               node_size=[0.6 + 0.9 * G.nodes[n]["grado"] ** 0.5 for n in lista],
                               node_color=[color5(G.nodes[n]["circulo"]) for n in lista],
                               edgecolors=borde, linewidths=ancho)

    handles = [Line2D([], [], marker="o", ls="", color=PALETA[i], markersize=4,
                      label=f"{c.split('_', 1)[1]} ({conteo[c]})") for i, c in enumerate(principales)]
    nodos_otros = int(conteo[[c for c in conteo.index if c != "sin_circulo" and c not in principales]].sum())
    if nodos_otros:
        handles.append(Line2D([], [], marker="o", ls="", color=GRIS_OTROS, markersize=4,
                              label=f"otros ({nodos_otros})"))
    if "sin_circulo" in conteo:
        handles.append(Line2D([], [], marker="o", ls="", color=GRIS_SIN, markersize=4,
                              label=f"sin círculo ({conteo['sin_circulo']})"))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2,
              fontsize=5.5, frameon=False, handletextpad=0.2, columnspacing=0.8)
    ax.set_title(f"({letra}) Ego {ego}: {G.number_of_nodes():,} nodos, {G.number_of_edges():,} aristas",
                 fontsize=7, loc="left")
    ax.axis("off")


def dibujar_combinada():
    """Las tres ego-redes en una sola figura (para ahorrar espacio en el informe)."""
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.3), dpi=400)
    fig.patch.set_facecolor(FONDO)
    for ax, ego, letra in zip(axes, EGOS, "abc"):
        dibujar_panel(ax, ego, letra)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.2, wspace=0.05)
    salida = DIR_SALIDA / "figura2_tres_egos.png"
    fig.savefig(salida, facecolor=FONDO)
    plt.close(fig)
    print(f"  [ok] {salida}")


def main():
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    if "--combinada" in sys.argv:
        dibujar_combinada()
        return
    for i, ego in enumerate(EGOS, start=2):  # la Figura 1 ya es el histograma
        dibujar(ego, i)


if __name__ == "__main__":
    main()
