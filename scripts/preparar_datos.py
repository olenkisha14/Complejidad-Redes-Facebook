#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Preparación del dataset base - Proyecto "Redes sociales y comunidades"
Curso: Complejidad Algorítmica (UPC)

Este script hace TODO el pipeline de datos de principio a fin:
  1. Descarga (si no existen) los archivos de SNAP a data/raw/ y los descomprime.
  2. Carga el grafo completo de Facebook y valida sus propiedades conocidas.
  3. Lee las 10 ego-redes, calcula sus tamaños y elige las 3 más grandes (>= 500 nodos).
  4. Genera nodos.csv, membresias.csv y aristas.csv (con pesos Jaccard y
     probabilidades del modelo "weighted cascade").
  5. Genera los subconjuntos ego_<id>/ para cada integrante.
  6. Ejecuta validaciones finales con assert.
  7. Genera las salidas para el informe (resumen, histograma, ejemplos de pesos).

NO implementa algoritmos de análisis (Kruskal, BFS, etc.): solo prepara los datos.

Uso:  python scripts/preparar_datos.py
"""

import gzip
import random
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path

import matplotlib

# Backend sin ventana: así el script funciona igual en cualquier PC o servidor
# (no necesita pantalla para guardar el PNG).
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
import pandas as pd  # noqa: E402

# En Windows la consola a veces no usa UTF-8; forzamos UTF-8 para que las
# tildes y la ñ se impriman bien.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

# ---------------------------------------------------------------------------
# Constantes y rutas
# ---------------------------------------------------------------------------

# Las rutas se calculan a partir de la ubicación del script, no del directorio
# desde donde se ejecuta; así funciona igual si se llama desde otra carpeta.
RAIZ = Path(__file__).resolve().parent.parent
DIR_RAW = RAIZ / "data" / "raw"
DIR_EGOS_RAW = DIR_RAW / "facebook"
DIR_PROCESSED = RAIZ / "data" / "processed"
DIR_OUTPUTS = RAIZ / "outputs"

URL_COMBINADO = "https://snap.stanford.edu/data/facebook_combined.txt.gz"
URL_EGOS = "https://snap.stanford.edu/data/facebook.tar.gz"

# Valores publicados por SNAP para este dataset. Si no coinciden, algo salió mal
# en la descarga o en la carga, y preferimos detenernos antes que seguir con
# datos incorrectos.
NODOS_ESPERADOS = 4039
ARISTAS_ESPERADAS = 88234

TAM_MINIMO_EGO_RED = 500  # requisito del curso: cada integrante analiza >= 500 nodos
NUM_EGO_REDES_ELEGIDAS = 3  # una ego-red por integrante
SIN_CIRCULO = "sin_circulo"

# Semilla fija: la muestra para verificar Jaccard debe ser la misma en cada
# ejecución, para que los resultados sean reproducibles.
SEMILLA = 42
TAM_MUESTRA_JACCARD = 1000
DECIMALES = 6

# Colores del gráfico: una sola serie -> un solo tono; texto y rejilla neutros.
COLOR_SERIE = "#2a78d6"
COLOR_FONDO = "#fcfcfb"
COLOR_TEXTO = "#0b0b0b"
COLOR_TEXTO_SEC = "#52514e"
COLOR_REJILLA = "#e4e3df"


# ---------------------------------------------------------------------------
# 1. Descarga y descompresión
# ---------------------------------------------------------------------------

def descargar_si_falta(url, destino):
    """Descarga un archivo solo si no existe, para no volver a bajarlo en cada ejecución
    y para que data/raw/ conserve los originales intactos."""
    if destino.exists():
        print(f"  [ok] ya existe: {destino.name}")
        return
    print(f"  descargando {url} ...")
    try:
        urllib.request.urlretrieve(url, destino)
    except Exception as error:  # noqa: BLE001 - queremos un mensaje claro para cualquier fallo de red
        sys.exit(
            f"\nERROR: no se pudo descargar {url}\n  motivo: {error}\n"
            f"  Descárgalo manualmente y colócalo en: {destino}\n"
        )


def descomprimir_datos():
    """Descomprime los .gz/.tar.gz. Los comprimidos originales se conservan en data/raw/
    como evidencia de la fuente exacta usada."""
    txt = DIR_RAW / "facebook_combined.txt"
    if not txt.exists():
        with gzip.open(DIR_RAW / "facebook_combined.txt.gz", "rb") as f_in, open(txt, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    if not DIR_EGOS_RAW.exists():
        with tarfile.open(DIR_RAW / "facebook.tar.gz") as tar:
            # filter="data" evita que un tar malicioso escriba fuera de la carpeta destino.
            tar.extractall(DIR_RAW, filter="data")


def preparar_raw():
    DIR_RAW.mkdir(parents=True, exist_ok=True)
    descargar_si_falta(URL_COMBINADO, DIR_RAW / "facebook_combined.txt.gz")
    descargar_si_falta(URL_EGOS, DIR_RAW / "facebook.tar.gz")
    descomprimir_datos()


# ---------------------------------------------------------------------------
# 2. Grafo completo
# ---------------------------------------------------------------------------

def cargar_grafo_completo():
    """Carga facebook_combined.txt como grafo NO dirigido: la amistad en Facebook es
    mutua, así que (u, v) y (v, u) representan la misma relación."""
    G = nx.read_edgelist(DIR_RAW / "facebook_combined.txt", nodetype=int, create_using=nx.Graph)
    return G


def validar_grafo_completo(G):
    """Comprueba que el grafo cargado es exactamente el publicado por SNAP."""
    n, m = G.number_of_nodes(), G.number_of_edges()
    assert n == NODOS_ESPERADOS, f"Se esperaban {NODOS_ESPERADOS} nodos y hay {n}"
    assert m == ARISTAS_ESPERADAS, f"Se esperaban {ARISTAS_ESPERADAS} aristas y hay {m}"
    lazos = nx.number_of_selfloops(G)
    assert lazos == 0, f"El grafo tiene {lazos} lazos (self-loops); no deberían existir"
    comps = nx.number_connected_components(G)
    assert comps == 1, f"Se esperaba 1 componente conexa y hay {comps}"
    print(f"  [ok] {n} nodos, {m} aristas, 0 lazos, 1 componente conexa")


# ---------------------------------------------------------------------------
# 3. Ego-redes
# ---------------------------------------------------------------------------

def listar_egos():
    """Los egos son los nombres de archivo <ego>.edges dentro de facebook/."""
    return sorted(int(p.stem) for p in DIR_EGOS_RAW.glob("*.edges"))


def leer_nodos_edges(ego):
    """Nodos que aparecen en <ego>.edges. Este archivo contiene las amistades ENTRE
    los amigos del ego; el ego no aparece porque está conectado a todos."""
    nodos = set()
    with open(DIR_EGOS_RAW / f"{ego}.edges") as f:
        for linea in f:
            u, v = map(int, linea.split())
            nodos.update((u, v))
    return nodos


def leer_nodos_feat(ego):
    """Nodos listados en <ego>.feat (la primera columna es el id). Este archivo sí
    lista a TODOS los amigos del ego, incluidos los que no tienen ninguna amistad
    con otros amigos y por eso no aparecen en .edges."""
    with open(DIR_EGOS_RAW / f"{ego}.feat") as f:
        return {int(linea.split()[0]) for linea in f}


def leer_circulos(ego):
    """Lee <ego>.circles respetando el orden del archivo. El orden importa porque
    'circulo_real' se define como el PRIMER círculo al que pertenece un nodo.
    El nombre se vuelve único anteponiendo el ego (circle0 existe en varios egos)."""
    circulos = []
    with open(DIR_EGOS_RAW / f"{ego}.circles") as f:
        for linea in f:
            partes = linea.split()
            if not partes:
                continue
            nombre = f"{ego}_{partes[0]}"
            circulos.append((nombre, [int(x) for x in partes[1:]]))
    return circulos


def cargar_ego_redes(G):
    """Construye la información de cada ego-red.

    DECISIÓN: la ego-red se define como {ego} ∪ nodos de .edges ∪ nodos de .feat.
    Si usáramos solo .edges + ego perderíamos a los amigos del ego que no tienen
    otros amigos dentro de la red (p. ej. 11 nodos en la red de 107), y algunos
    miembros de círculos quedarían fuera de su propia ego-red. Guardamos también
    el tamaño 'solo .edges + ego' para mostrar que la selección no cambia."""
    ego_redes = {}
    for ego in listar_egos():
        nodos_edges = leer_nodos_edges(ego)
        nodos_feat = leer_nodos_feat(ego)
        circulos = leer_circulos(ego)
        nodos = {ego} | nodos_edges | nodos_feat
        miembros_circulos = {x for _, ms in circulos for x in ms}
        assert miembros_circulos <= nodos, f"Ego {ego}: hay miembros de círculos fuera de la ego-red"
        assert nodos <= set(G.nodes), f"Ego {ego}: hay nodos que no existen en el grafo completo"
        ego_redes[ego] = {
            "nodos": nodos,
            "tam_edges_mas_ego": len(nodos_edges | {ego}),
            "circulos": circulos,
        }
    return ego_redes


def tabla_ego_redes(G, ego_redes):
    """Tabla resumen de las ego-redes, ordenada de mayor a menor tamaño."""
    filas = []
    for ego, info in ego_redes.items():
        sub = G.subgraph(info["nodos"])
        filas.append({
            "ego": ego,
            "tam_edges_mas_ego": info["tam_edges_mas_ego"],
            "nodos": len(info["nodos"]),
            "aristas": sub.number_of_edges(),
            "circulos": len(info["circulos"]),
            "grado_ego": G.degree(ego),
        })
    return pd.DataFrame(filas).sort_values("nodos", ascending=False).reset_index(drop=True)


def elegir_ego_redes(tabla):
    """Elige automáticamente las 3 ego-redes más grandes con >= 500 nodos, para que
    cada integrante trabaje con una red de tamaño comparable y suficiente."""
    candidatas = tabla[tabla["nodos"] >= TAM_MINIMO_EGO_RED]
    if len(candidatas) < NUM_EGO_REDES_ELEGIDAS:
        sys.exit(
            f"\nERROR: solo hay {len(candidatas)} ego-redes con >= {TAM_MINIMO_EGO_RED} nodos; "
            f"se necesitan {NUM_EGO_REDES_ELEGIDAS}. Revisar el criterio de selección.\n"
        )
    return candidatas["ego"].head(NUM_EGO_REDES_ELEGIDAS).tolist()


def calcular_solapamiento(ego_redes, elegidas):
    """Cuenta nodos compartidos entre las ego-redes elegidas. Es importante saberlo
    porque un nodo compartido hace de 'puente' y puede aparecer en el análisis de
    más de un integrante."""
    a, b, c = (ego_redes[e]["nodos"] for e in elegidas)
    ea, eb, ec = elegidas
    return {
        f"{ea} ∩ {eb}": len(a & b),
        f"{ea} ∩ {ec}": len(a & c),
        f"{eb} ∩ {ec}": len(b & c),
        "las 3 a la vez": len(a & b & c),
        "en al menos 2": len((a & b) | (a & c) | (b & c)),
        "unión de las 3": len(a | b | c),
    }


# ---------------------------------------------------------------------------
# 4. nodos.csv y membresias.csv
# ---------------------------------------------------------------------------

def construir_membresias(ego_redes):
    """Formato largo: una fila por (nodo, ego-red, círculo). Se usa formato largo
    porque un nodo puede estar en varias ego-redes y en varios círculos; meter
    listas dentro de una celda haría el CSV difícil de filtrar."""
    filas = []
    for ego, info in ego_redes.items():
        circulos_de = {}
        for nombre, miembros in info["circulos"]:
            for x in miembros:
                circulos_de.setdefault(x, []).append(nombre)
        for nodo in info["nodos"]:
            for circulo in circulos_de.get(nodo, [SIN_CIRCULO]):
                filas.append({"id": nodo, "ego_red": ego, "circulo": circulo})
    df = pd.DataFrame(filas).sort_values(["id", "ego_red"], kind="stable").reset_index(drop=True)
    return df


def construir_nodos(G, ego_redes):
    """Una fila por nodo del grafo completo."""
    egos = set(ego_redes)
    # Ordenamos las ego-redes de mayor a menor: la primera que contenga al nodo
    # es su ego-red principal (la más grande que lo contiene).
    por_tamano = sorted(ego_redes, key=lambda e: len(ego_redes[e]["nodos"]), reverse=True)

    filas = []
    for nodo in sorted(G.nodes):
        contenedoras = [e for e in por_tamano if nodo in ego_redes[e]["nodos"]]
        assert contenedoras, f"El nodo {nodo} no pertenece a ninguna ego-red"
        # Para un ego, su ego-red principal es la propia (así lo pide la definición),
        # aunque esté contenido también en una ego-red más grande (p. ej. 0 está en la de 107).
        principal = nodo if nodo in egos else contenedoras[0]
        # Primer círculo (en orden de archivo) dentro de la ego-red principal.
        circulo = SIN_CIRCULO
        for nombre, miembros in ego_redes[principal]["circulos"]:
            if nodo in miembros:
                circulo = nombre
                break
        filas.append({
            "id": nodo,
            "grado": G.degree(nodo),
            "es_ego": nodo in egos,
            "ego_red": principal,
            "num_ego_redes": len(contenedoras),
            "circulo_real": circulo,
        })
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# 5. aristas.csv (pesos)
# ---------------------------------------------------------------------------

def vecinos(G):
    """Precalcula N(x) como conjunto de Python para cada nodo. N(x) NO incluye a x
    (el grafo no tiene lazos, ya validado). Precalcular evita reconstruir los
    conjuntos 88 234 veces."""
    return {x: set(G[x]) for x in G.nodes}


def jaccard_manual(N, u, v):
    """Coeficiente de Jaccard implementado a mano:
        J(u, v) = |N(u) ∩ N(v)| / |N(u) ∪ N(v)|
    Devuelve también los tamaños de la intersección y la unión para poder
    explicarlo paso a paso. La unión nunca es vacía porque u ∈ N(v) al ser vecinos."""
    comunes = N[u] & N[v]
    union = N[u] | N[v]
    return len(comunes), len(union), len(comunes) / len(union)


def construir_aristas(G, N):
    """Una fila por arista no dirigida, con origen < destino para que cada amistad
    aparezca exactamente una vez y sea fácil detectar duplicados.

    - peso_jaccard = 1 - J(u, v): lo convertimos en DISTANCIA social porque los
      algoritmos de árbol de expansión mínima / caminos mínimos minimizan pesos;
      así, amigos con muchos amigos en común quedan 'cerca' (peso ~ 0).
    - prob_origen_a_destino = 1 / grado(destino): modelo 'weighted cascade'
      (Kempe, Kleinberg y Tardos, 2003). Un nodo con muchos amigos recibe
      influencia de muchos lados, así que cada amigo individual pesa menos.
      Por eso la probabilidad NO es simétrica aunque la amistad sí lo sea."""
    filas = []
    for a, b in G.edges:
        u, v = (a, b) if a < b else (b, a)
        comunes, _, jac = jaccard_manual(N, u, v)
        filas.append({
            "origen": u,
            "destino": v,
            "vecinos_comunes": comunes,
            "peso_jaccard": round(1 - jac, DECIMALES),
            "prob_origen_a_destino": round(1 / len(N[v]), DECIMALES),
            "prob_destino_a_origen": round(1 / len(N[u]), DECIMALES),
        })
    return pd.DataFrame(filas).sort_values(["origen", "destino"]).reset_index(drop=True)


def verificar_jaccard_con_networkx(G, N):
    """Comparamos nuestra implementación con la de networkx en una muestra aleatoria
    de aristas. Si coinciden, podemos defender que nuestra fórmula es correcta."""
    rng = random.Random(SEMILLA)
    muestra = rng.sample(sorted(G.edges), TAM_MUESTRA_JACCARD)
    for u, v, j_nx in nx.jaccard_coefficient(G, muestra):
        _, _, j_manual = jaccard_manual(N, u, v)
        assert abs(j_manual - j_nx) < 1e-12, f"Jaccard distinto en ({u},{v}): manual={j_manual}, nx={j_nx}"
    print(f"  [ok] Jaccard manual = nx.jaccard_coefficient en {TAM_MUESTRA_JACCARD} aristas (semilla {SEMILLA})")


# ---------------------------------------------------------------------------
# 6. Subconjuntos por ego-red
# ---------------------------------------------------------------------------

def exportar_ego_redes(G, ego_redes, elegidas, df_nodos, df_aristas):
    """Filtra los CSV globales en vez de recalcular: así los pesos son idénticos a los
    del grafo completo y los 3 integrantes trabajan con los mismos valores."""
    for ego in elegidas:
        nodos = ego_redes[ego]["nodos"]
        carpeta = DIR_PROCESSED / f"ego_{ego}"
        carpeta.mkdir(parents=True, exist_ok=True)
        sub_nodos = df_nodos[df_nodos["id"].isin(nodos)]
        # Subgrafo inducido: se conservan las aristas cuyos DOS extremos están en la ego-red.
        sub_aristas = df_aristas[df_aristas["origen"].isin(nodos) & df_aristas["destino"].isin(nodos)]

        assert len(sub_nodos) >= TAM_MINIMO_EGO_RED, f"ego_{ego}: solo {len(sub_nodos)} nodos (< {TAM_MINIMO_EGO_RED})"
        assert len(sub_nodos) == len(nodos), f"ego_{ego}: faltan nodos al filtrar"
        m_esperadas = G.subgraph(nodos).number_of_edges()
        assert len(sub_aristas) == m_esperadas, f"ego_{ego}: {len(sub_aristas)} aristas, se esperaban {m_esperadas}"
        # El ego debe estar conectado a todos los demás nodos de su red.
        grado_ego_local = ((sub_aristas["origen"] == ego) | (sub_aristas["destino"] == ego)).sum()
        assert grado_ego_local == len(nodos) - 1, f"ego_{ego}: el ego no está conectado a todos sus nodos"

        sub_nodos.to_csv(carpeta / "nodos.csv", index=False)
        sub_aristas.to_csv(carpeta / "aristas.csv", index=False)
        print(f"  [ok] ego_{ego}: {len(sub_nodos)} nodos, {len(sub_aristas)} aristas")


# ---------------------------------------------------------------------------
# 7. Validaciones finales
# ---------------------------------------------------------------------------

def validaciones_finales(df_nodos, df_aristas, df_membresias):
    j = df_aristas["peso_jaccard"]
    assert ((j >= 0) & (j <= 1)).all(), "Hay peso_jaccard fuera de [0, 1]"
    for col in ("prob_origen_a_destino", "prob_destino_a_origen"):
        p = df_aristas[col]
        assert ((p > 0) & (p <= 1)).all(), f"Hay valores de {col} fuera de (0, 1]"

    assert len(df_aristas) == ARISTAS_ESPERADAS, f"aristas.csv tiene {len(df_aristas)} filas, se esperaban {ARISTAS_ESPERADAS}"
    assert len(df_nodos) == NODOS_ESPERADOS, f"nodos.csv tiene {len(df_nodos)} filas, se esperaban {NODOS_ESPERADOS}"

    assert (df_aristas["origen"] < df_aristas["destino"]).all(), "Hay aristas invertidas (origen >= destino) o lazos"
    assert not df_aristas.duplicated(["origen", "destino"]).any(), "Hay aristas duplicadas"
    assert df_nodos["id"].is_unique, "Hay ids repetidos en nodos.csv"

    ids = set(df_nodos["id"])
    extremos = set(df_aristas["origen"]) | set(df_aristas["destino"])
    faltantes = extremos - ids
    assert not faltantes, f"Hay {len(faltantes)} ids en aristas.csv que no están en nodos.csv"

    # Coherencia entre archivos: num_ego_redes debe coincidir con membresias.csv.
    conteo = df_membresias.groupby("id")["ego_red"].nunique()
    assert (df_nodos.set_index("id")["num_ego_redes"] == conteo).all(), "num_ego_redes no coincide con membresias.csv"
    print("  [ok] todas las validaciones finales pasaron")


# ---------------------------------------------------------------------------
# 8. Salidas para el informe
# ---------------------------------------------------------------------------

def estadisticas_generales(G):
    grados = dict(G.degree)
    nodo_max = max(grados, key=grados.get)
    return {
        "nodos": G.number_of_nodes(),
        "aristas": G.number_of_edges(),
        "grado_promedio": 2 * G.number_of_edges() / G.number_of_nodes(),
        "grado_max": grados[nodo_max],
        "nodo_grado_max": nodo_max,
        "densidad": nx.density(G),
        "componentes": nx.number_connected_components(G),
        "clustering_promedio": nx.average_clustering(G),
    }


def escribir_resumen(stats, tabla, elegidas, solapamiento):
    lineas = [
        "# Resumen del dataset - Facebook (SNAP, ego-Facebook)",
        "",
        "Generado automáticamente por `scripts/preparar_datos.py`.",
        "",
        "## Grafo completo",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Nodos | {stats['nodos']:,} |",
        f"| Aristas (no dirigidas) | {stats['aristas']:,} |",
        f"| Grado promedio | {stats['grado_promedio']:.2f} |",
        f"| Grado máximo | {stats['grado_max']:,} (nodo {stats['nodo_grado_max']}) |",
        f"| Densidad | {stats['densidad']:.6f} |",
        f"| Componentes conexas | {stats['componentes']} |",
        f"| Coeficiente de clustering promedio | {stats['clustering_promedio']:.4f} |",
        "",
        "## Las 10 ego-redes (ordenadas por tamaño)",
        "",
        "Ego-red = ego ∪ nodos de `.edges` ∪ nodos de `.feat`. La columna "
        "*Nodos (.edges + ego)* muestra el tamaño si solo se usara `.edges`; "
        "la diferencia son amigos del ego sin amistades con otros amigos del ego.",
        "",
        "| # | Ego | Nodos | Nodos (.edges + ego) | Aristas del subgrafo | Círculos | Elegida |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, fila in tabla.iterrows():
        marca = "✔" if fila["ego"] in elegidas else ""
        lineas.append(
            f"| {i + 1} | {fila['ego']} | {fila['nodos']:,} | {fila['tam_edges_mas_ego']:,} | "
            f"{fila['aristas']:,} | {fila['circulos']} | {marca} |"
        )
    lineas += [
        "",
        f"Criterio: las {NUM_EGO_REDES_ELEGIDAS} ego-redes más grandes con al menos {TAM_MINIMO_EGO_RED} nodos.",
        "",
        "## Solapamiento entre las ego-redes elegidas",
        "",
        "| Conjunto | Nodos |",
        "|---|---|",
    ]
    lineas += [f"| {k} | {v:,} |" for k, v in solapamiento.items()]
    (DIR_OUTPUTS / "resumen_dataset.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")


def graficar_histograma_grados(G, stats):
    """Distribución de grados en escala log-log. En redes sociales la mayoría de
    nodos tiene pocos amigos y unos pocos tienen muchísimos (cola pesada); en escala
    lineal esa cola sería invisible, por eso se usa log-log."""
    conteo = pd.Series(dict(G.degree)).value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=150)
    fig.patch.set_facecolor(COLOR_FONDO)
    ax.set_facecolor(COLOR_FONDO)
    ax.scatter(conteo.index, conteo.values, s=14, color=COLOR_SERIE, alpha=0.85, linewidths=0)
    ax.set_xscale("log")
    ax.set_yscale("log")

    ax.set_title("Distribución de grados - red de Facebook (SNAP)", color=COLOR_TEXTO, fontsize=13, loc="left", pad=12)
    ax.set_xlabel("Grado k (número de amigos)", color=COLOR_TEXTO_SEC)
    ax.set_ylabel("Número de nodos con grado k", color=COLOR_TEXTO_SEC)
    ax.grid(True, which="major", color=COLOR_REJILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(COLOR_REJILLA)
    ax.tick_params(colors=COLOR_TEXTO_SEC)

    # Etiqueta solo el punto más llamativo (el nodo de mayor grado), no todos.
    ax.annotate(
        f"nodo {stats['nodo_grado_max']}: grado {stats['grado_max']}",
        xy=(stats["grado_max"], 1), xytext=(-10, 28), textcoords="offset points",
        ha="right", color=COLOR_TEXTO_SEC, fontsize=9,
        arrowprops={"arrowstyle": "-", "color": COLOR_TEXTO_SEC, "linewidth": 0.8},
    )
    fig.text(
        0.01, 0.01,
        f"{stats['nodos']:,} nodos · {stats['aristas']:,} aristas · grado promedio {stats['grado_promedio']:.2f}",
        color=COLOR_TEXTO_SEC, fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(DIR_OUTPUTS / "histograma_grados.png", facecolor=COLOR_FONDO)
    plt.close(fig)


def elegir_aristas_ejemplo(df_aristas, egos):
    """Elige 5 aristas de tipos distintos para explicar las fórmulas en la exposición.
    Los empates se rompen por (origen, destino) para que la elección sea determinista."""
    df = df_aristas.sort_values(["origen", "destino"])
    toca_ego = df["origen"].isin(egos) | df["destino"].isin(egos)
    ambos_ego = df["origen"].isin(egos) & df["destino"].isin(egos)

    ejemplos = []

    def agregar(descripcion, fila):
        ejemplos.append((descripcion, int(fila["origen"]), int(fila["destino"])))

    agregar("La arista con MÁS vecinos comunes (amistad muy 'incrustada' en su grupo)",
            df.sort_values("vecinos_comunes", ascending=False, kind="stable").iloc[0])
    # Toda arista entre dos NO-egos tiene al menos 1 vecino común (el ego de la red
    # que la contiene), así que las aristas con 0 comunes siempre tocan a un ego.
    # Elegimos la de 0 comunes cuyos extremos tienen más amigos (prob. más pequeña):
    # así no es una simple 'hoja' de grado 1, sino un puente entre grupos.
    cero = df[df["vecinos_comunes"] == 0].copy()
    cero["prob_max"] = cero[["prob_origen_a_destino", "prob_destino_a_origen"]].max(axis=1)
    agregar("Una arista con CERO vecinos comunes entre nodos con varios amigos (puente: peso máximo = 1)",
            cero.sort_values("prob_max", kind="stable").iloc[0])
    agregar("La arista de MENOR peso Jaccard sin egos (los dos amigos casi idénticos en su círculo)",
            df[~toca_ego].sort_values("peso_jaccard", kind="stable").iloc[0])
    # Ego de mayor grado con un amigo de grado 1 (una 'hoja'): la probabilidad más
    # alta posible es 1/1 = 1, lo que muestra la asimetría más extrema.
    cand = df[toca_ego & ~ambos_ego].copy()
    cand["prob_max"] = cand[["prob_origen_a_destino", "prob_destino_a_origen"]].max(axis=1)
    cand["prob_min"] = cand[["prob_origen_a_destino", "prob_destino_a_origen"]].min(axis=1)
    agregar("Una arista que toca a un EGO con un amigo de grado 1 (probabilidades muy asimétricas)",
            cand.sort_values(["prob_max", "prob_min"], ascending=[False, True], kind="stable").iloc[0])
    agregar("Una arista entre DOS EGOS (conecta dos ego-redes distintas)", df[ambos_ego].iloc[0])
    return ejemplos


def escribir_ejemplo_pesos(G, N, df_aristas, egos):
    lineas = [
        "# Ejemplos de cálculo de pesos",
        "",
        "Fórmulas (todo calculado sobre el grafo completo):",
        "",
        "- N(x) = conjunto de vecinos de x, sin incluir a x.",
        "- vecinos_comunes = |N(u) ∩ N(v)|",
        "- |N(u) ∪ N(v)| = grado(u) + grado(v) − |N(u) ∩ N(v)|  (inclusión-exclusión)",
        "- peso_jaccard = 1 − |N(u) ∩ N(v)| / |N(u) ∪ N(v)|  (0 = muy cercanos, 1 = sin amigos en común)",
        "- prob_origen_a_destino = 1 / grado(destino);  prob_destino_a_origen = 1 / grado(origen)"
        "  (weighted cascade, Kempe, Kleinberg y Tardos, 2003)",
        "",
        "Nota: como u y v son vecinos, v ∈ N(u) y u ∈ N(v); por eso ambos cuentan en la unión "
        "pero nunca en la intersección (no hay lazos).",
        "",
        "| # | Arista (u, v) | grado(u) | grado(v) | comunes | unión | peso_jaccard | P(u→v) | P(v→u) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    ejemplos = elegir_aristas_ejemplo(df_aristas, egos)
    indice = df_aristas.set_index(["origen", "destino"])
    detalle = []
    for i, (desc, u, v) in enumerate(ejemplos, start=1):
        fila = indice.loc[(u, v)]
        du, dv = G.degree(u), G.degree(v)
        comunes, union, jac = jaccard_manual(N, u, v)
        assert union == du + dv - comunes  # comprobación de inclusión-exclusión
        lineas.append(
            f"| {i} | ({u}, {v}) | {du} | {dv} | {comunes} | {union} | {fila['peso_jaccard']:.6f} | "
            f"{fila['prob_origen_a_destino']:.6f} | {fila['prob_destino_a_origen']:.6f} |"
        )
        u_ego = " (ego)" if u in egos else ""
        v_ego = " (ego)" if v in egos else ""
        detalle += [
            f"### Ejemplo {i}: arista ({u}, {v})",
            "",
            f"*{desc}.*",
            "",
            f"1. grado({u}){u_ego} = {du};  grado({v}){v_ego} = {dv}",
            f"2. |N({u}) ∩ N({v})| = **{comunes}** amigos en común",
            f"3. |N({u}) ∪ N({v})| = {du} + {dv} − {comunes} = **{union}**",
            f"4. Jaccard = {comunes} / {union} = {jac:.6f}",
            f"5. peso_jaccard = 1 − {jac:.6f} = **{1 - jac:.6f}**",
            f"6. P({u}→{v}) = 1 / grado({v}) = 1 / {dv} = **{1 / dv:.6f}**",
            f"7. P({v}→{u}) = 1 / grado({u}) = 1 / {du} = **{1 / du:.6f}**",
            "",
        ]
    lineas += ["", "## Cálculo paso a paso", ""] + detalle
    (DIR_OUTPUTS / "ejemplo_pesos.md").write_text("\n".join(lineas), encoding="utf-8")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    print("1) Datos crudos")
    preparar_raw()

    print("2) Grafo completo")
    G = cargar_grafo_completo()
    validar_grafo_completo(G)

    print("3) Ego-redes")
    ego_redes = cargar_ego_redes(G)
    tabla = tabla_ego_redes(G, ego_redes)
    print(tabla.to_string(index=False))
    elegidas = elegir_ego_redes(tabla)
    print(f"  Ego-redes elegidas: {elegidas}")
    solapamiento = calcular_solapamiento(ego_redes, elegidas)
    for k, v in solapamiento.items():
        print(f"    {k}: {v} nodos")

    print("4) nodos.csv y membresias.csv")
    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    df_membresias = construir_membresias(ego_redes)
    df_nodos = construir_nodos(G, ego_redes)
    df_nodos.to_csv(DIR_PROCESSED / "nodos.csv", index=False)
    df_membresias.to_csv(DIR_PROCESSED / "membresias.csv", index=False)
    print(f"  [ok] nodos.csv: {len(df_nodos)} filas; membresias.csv: {len(df_membresias)} filas")

    print("5) aristas.csv")
    N = vecinos(G)
    verificar_jaccard_con_networkx(G, N)
    df_aristas = construir_aristas(G, N)
    df_aristas.to_csv(DIR_PROCESSED / "aristas.csv", index=False)
    print(f"  [ok] aristas.csv: {len(df_aristas)} filas")

    print("6) Validaciones finales")
    validaciones_finales(df_nodos, df_aristas, df_membresias)

    print("7) Subconjuntos por ego-red")
    exportar_ego_redes(G, ego_redes, elegidas, df_nodos, df_aristas)

    print("8) Salidas para el informe")
    DIR_OUTPUTS.mkdir(parents=True, exist_ok=True)
    stats = estadisticas_generales(G)
    escribir_resumen(stats, tabla, elegidas, solapamiento)
    graficar_histograma_grados(G, stats)
    escribir_ejemplo_pesos(G, N, df_aristas, set(ego_redes))
    for k, v in stats.items():
        print(f"    {k}: {v}")
    print("  [ok] outputs/resumen_dataset.md, outputs/histograma_grados.png, outputs/ejemplo_pesos.md")

    print("\nListo: todas las validaciones pasaron.")


if __name__ == "__main__":
    main()
