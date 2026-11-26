#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz grafica web del aplicativo (Streamlit).
Curso: Complejidad Algoritmica (UPC) - Trabajo Final

Uso:
    streamlit run app.py
"""

import sys
import time
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))

from common_grafo import cargar_ego
from comunidades import detectar_comunidades, resumen_por_comunidad
from influencers import ranking_influencers
from propagacion import alcance_por_rondas, camino_mas_probable

st.set_page_config(
    page_title="Analisis de Redes Facebook (SNAP)",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Estilos de la interfaz
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Encabezado: sobrio, con una linea de acento a la izquierda */
    .hero {
        padding: 0.4rem 0 0.4rem 1.1rem;
        border-left: 4px solid #2BA89A;
        margin: 0.4rem 0 1.4rem 0;
    }
    .hero h1 {
        margin: 0 0 0.35rem 0;
        padding: 0;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.01em;
    }
    .hero p {
        color: #5F6368;
        margin: 0;
        max-width: 60rem;
    }

    /* Barra lateral */
    section[data-testid="stSidebar"] {
        border-right: 1px solid #E1E4E8;
    }

    /* Tarjetas de metricas */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E1E4E8;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        transition: border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover { border-color: #2BA89A; }

    /* Botones principales */
    .stButton > button[kind="primary"] {
        border-radius: 6px;
        font-weight: 600;
        transition: background-color 0.15s ease;
    }

    /* Etiquetas de algoritmo y complejidad */
    .chip {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        margin: 0 0.4rem 0.8rem 0;
        border-radius: 4px;
        font-size: 0.85rem;
        border: 1px solid #E1E4E8;
        background: #FFFFFF;
        color: #3C4043;
    }
    .chip.cian {
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        color: #1F8577;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

COLOR_PRIMARIO = "#2BA89A"
COLOR_SECUNDARIO = "#D9A441"


def chips(algoritmo, complejidad):
    st.markdown(
        f'<span class="chip">Algoritmo: {algoritmo}</span>'
        f'<span class="chip cian">Complejidad: {complejidad}</span>',
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner="Cargando ego-red...")
def cargar_grafo(ego):
    G, prob = cargar_ego(ego)
    return G, prob


# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------
st.sidebar.title("Configuracion")

ego_seleccionado = st.sidebar.selectbox(
    "Ego-red a analizar",
    options=[107, 1684, 1912],
    format_func=lambda x: f"Ego-red {x}",
    help="Selecciona una de las tres ego-redes del dataset SNAP ego-Facebook.",
)

G, prob = cargar_grafo(ego_seleccionado)

st.sidebar.markdown("---")
st.sidebar.metric("Nodos (V)", f"{G.number_of_nodes():,}")
st.sidebar.metric("Aristas (E)", f"{G.number_of_edges():,}")

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>Analisis Algoritmico de la Red ego-Facebook</h1>
        <p>Aplicativo del curso de Complejidad Algoritmica. Permite explorar las tres
        ramas de analisis implementadas sobre las ego-redes del dataset SNAP.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs(["Comunidades", "Influencers", "Propagacion"])

with tab1:
    st.header("Deteccion de comunidades")
    chips("Kruskal + Union-Find (clustering de enlace simple)", "O(E log E)")

    col1, col2 = st.columns([1, 3])
    with col1:
        k = st.number_input("Numero de comunidades (k)", min_value=2, max_value=50, value=10, step=1)
        ejecutar_com = st.button("Detectar comunidades", type="primary", width="stretch")

    with col2:
        if ejecutar_com:
            inicio = time.perf_counter()
            comunidad = detectar_comunidades(G, k)
            filas = resumen_por_comunidad(G, comunidad)
            tiempo = (time.perf_counter() - inicio) * 1000

            st.success(f"{len(filas)} comunidades formadas en {tiempo:.2f} ms")

            df = pd.DataFrame(filas)
            df.columns = ["Comunidad", "Tamanio", "Circulo real mas comun", "Pureza"]
            df["Pureza"] = df["Pureza"] * 100

            st.bar_chart(
                df.set_index("Comunidad")["Tamanio"],
                color=COLOR_PRIMARIO,
                height=260,
            )
            st.dataframe(
                df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Pureza": st.column_config.ProgressColumn(
                        "Pureza", format="%.1f %%", min_value=0, max_value=100
                    ),
                },
            )

with tab2:
    st.header("Ranking de influencers")
    chips("orden voraz por grado + BFS de alcance a 2 saltos", "O(V . (V+E))")

    col1, col2 = st.columns([1, 3])
    with col1:
        top = st.number_input("Top influencers a mostrar", min_value=3, max_value=20, value=10, step=1)
        ejecutar_inf = st.button("Calcular ranking", type="primary", width="stretch")

    with col2:
        if ejecutar_inf:
            inicio = time.perf_counter()
            filas = ranking_influencers(G, top=top)
            tiempo = (time.perf_counter() - inicio) * 1000

            st.success(f"Top {len(filas)} influencers calculado en {tiempo:.2f} ms")

            df = pd.DataFrame([
                {
                    "Nodo": f["nodo"],
                    "Grado": f["grado"],
                    "Alcance (2 saltos)": f["alcance_total"],
                    "Circulo real": f["circulo_real"],
                }
                for f in filas
            ])

            st.bar_chart(
                df.assign(Nodo=df["Nodo"].astype(str)).set_index("Nodo")["Alcance (2 saltos)"],
                color=COLOR_SECUNDARIO,
                height=260,
            )
            st.dataframe(
                df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Alcance (2 saltos)": st.column_config.ProgressColumn(
                        "Alcance (2 saltos)",
                        format="%d",
                        min_value=0,
                        max_value=G.number_of_nodes(),
                    ),
                },
            )

with tab3:
    st.header("Simulacion de propagacion")
    chips("BFS por niveles (alcance) + Dijkstra sobre log(1/p) (camino mas probable)", "O(E log V)")

    nodos_disponibles = sorted(G.nodes())
    col1, col2 = st.columns(2)
    with col1:
        origen = st.selectbox("Nodo origen (semilla del contagio)", options=nodos_disponibles, index=0)
    with col2:
        destino = st.selectbox(
            "Nodo destino (opcional, para camino mas probable)",
            options=["(ninguno)"] + [n for n in nodos_disponibles if n != origen],
            index=0,
        )

    ejecutar_pro = st.button("Simular propagacion", type="primary")

    if ejecutar_pro:
        inicio = time.perf_counter()
        orden, rondas = alcance_por_rondas(G, origen)
        tiempo = (time.perf_counter() - inicio) * 1000

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Nodos alcanzados", f"{len(orden)} / {G.number_of_nodes()}")
        with col_b:
            st.metric("Numero de rondas", len(rondas) - 1)
        with col_c:
            st.metric("Cobertura", f"{len(orden) / G.number_of_nodes() * 100:.1f} %")

        st.caption(f"Alcance calculado en {tiempo:.2f} ms")
        rondas_df = pd.DataFrame([
            {"Ronda": r, "Nodos nuevos": len(rondas[r])}
            for r in sorted(rondas)
        ])
        rondas_df["Acumulado"] = rondas_df["Nodos nuevos"].cumsum()

        st.markdown("**Alcance por ronda:**")
        st.area_chart(
            rondas_df.set_index("Ronda")[["Acumulado", "Nodos nuevos"]],
            color=[COLOR_PRIMARIO, COLOR_SECUNDARIO],
            height=260,
        )
        st.dataframe(rondas_df, width="stretch", hide_index=True)

        if destino != "(ninguno)":
            st.markdown("---")
            st.markdown("**Camino mas probable (Dijkstra sobre log(1/p)):**")
            camino, probabilidad = camino_mas_probable(G, prob, origen, int(destino))
            if camino is None:
                st.warning(f"No existe camino entre {origen} y {destino}.")
            else:
                ruta = " -> ".join(str(n) for n in camino)
                st.code(ruta, language=None)
                st.metric(
                    "Probabilidad total de contagio",
                    f"{probabilidad:.6f}",
                    delta=f"{probabilidad * 100:.4f} %",
                    delta_color="off",
                )

st.markdown("---")
st.caption(
    "Universidad Peruana de Ciencias Aplicadas - Ciencias de la Computacion - "
    "1ACC0184 Complejidad Algoritmica - 2026-20"
)
