# Análisis Algorítmico de la Red ego-Facebook (SNAP)

Trabajo del curso **1ACC0184 Complejidad Algorítmica** (UPC, 2026-20). Aplicativo que analiza la red ego-Facebook de SNAP aplicando tres técnicas de grafos para responder:

1. ¿Qué comunidades de usuarios se forman? (Kruskal + Union-Find)
2. ¿Quiénes son los usuarios más influyentes? (voraz por grado + BFS)
3. ¿Cómo se propagaría un mensaje? (BFS + Dijkstra)

El aplicativo tiene dos interfaces: línea de comandos (`main.py`) e interfaz gráfica web (`app.py` con Streamlit).

## Integrantes

| Código     | Integrante                             | Ego-red |
|------------|----------------------------------------|---------|
| U202411669 | Olenka Priscilla Del Aguila Del Aguila | 1684    |
| U202415495 | Angela Milagros Espinoza Cruz          | 107     |
| U202417857 | Rose Almendra Vergaray Calderon        | 1912    |

## Dataset

Conjunto **ego-Facebook** del Stanford Network Analysis Project: 4,039 usuarios y 88,234 amistades, anonimizados en origen.

> McAuley, J., & Leskovec, J. (2012). Learning to discover social circles in ego networks. *Advances in Neural Information Processing Systems*, 25, 539-547. Fuente: <https://snap.stanford.edu/data/ego-Facebook.html>

Los archivos originales no se incluyen en el repositorio: el script `preparar_datos.py` los descarga automáticamente la primera vez.

## Estructura

```
scripts/
  preparar_datos.py    descarga y procesa los datos
  graficar_egos.py     dibuja las tres ego-redes
  common_grafo.py      carga los CSV en un grafo de NetworkX
  comunidades.py       Kruskal + Union-Find
  influencers.py       voraz por grado + BFS
  propagacion.py       BFS + Dijkstra
  main.py              integra las tres ramas (CLI)
  medir_tiempos.py     mide tiempos de ejecución
data/processed/        CSV por ego-red
outputs/               figuras del informe
app.py                 interfaz gráfica web (Streamlit)
requirements.txt
```

## Instalación

Requiere Python 3.10 o superior.

```bash
git clone https://github.com/olenkisha14/Complejidad-Redes-Facebook.git
cd Complejidad-Redes-Facebook
pip install -r requirements.txt
pip install streamlit
```

## Uso

### Línea de comandos

```bash
python scripts/preparar_datos.py              # solo la primera vez
python scripts/main.py --ego 1684 --k 17 --top-influencers 10 --destino 3363
python scripts/medir_tiempos.py               # mide tiempos reales
```

Cada rama también se puede correr por separado:

```bash
python scripts/comunidades.py --ego 1684 --k 17
python scripts/influencers.py --ego 1684 --top 10
python scripts/propagacion.py --ego 1684 --origen 1684 --alcance
```

### Interfaz gráfica web (recomendada para demostración)

```bash
python -m streamlit run app.py
```

Streamlit abre automáticamente el navegador en <http://localhost:8501>. La barra lateral permite elegir la ego-red (107, 1684 o 1912), y las tres pestañas ejecutan cada rama con parámetros configurables. Para detener la app, presiona `Ctrl + C` en la terminal.

## Atributos del grafo

- **Peso Jaccard:** `w(u, v) = 1 - |N(u) ∩ N(v)| / |N(u) ∪ N(v)|` (distancia entre vecindarios).
- **Probabilidad de contagio:** `p(u, v) = 1 / grado(v)` (cascada ponderada, Kempe et al., 2003). No simétrica.

## Técnicas y complejidades

| Rama        | Técnica                                    | Complejidad |
|-------------|--------------------------------------------|-------------|
| Comunidades | Kruskal + Union-Find (clustering)          | O(E log E)  |
| Influencers | Voraz por grado + BFS de alcance (2 saltos)| O(V·(V+E))  |
| Propagación | BFS por niveles + Dijkstra sobre log(1/p)  | O(E log V)  |

Las estructuras (Union-Find, BFS, Dijkstra) están implementadas desde cero. NetworkX se usa solo como contenedor del grafo.
