# Redes sociales y comunidades: análisis de la red de Facebook (SNAP)

Trabajo del curso **1ACC0184 – Complejidad Algorítmica** (UPC, 2026-20).
Entregas: Trabajo Parcial (TB1), Hito 2 y Trabajo Final (Hito 3).

## Integrantes

| Código | Integrante | Ego-red asignada |
|---|---|---|
| U202411669 | Olenka Priscilla Del Aguila Del Aguila | Ego 1684 |
| U202415495 | Angela Milagros Espinoza Cruz | Ego 107 |
| U202417857 | Rose Almendra Vergaray Calderon | Ego 1912 |

## Datos

Se usa el conjunto **ego-Facebook** del Stanford Network Analysis Project (SNAP):
4,039 usuarios y 88,234 amistades, con datos anonimizados por sus autores.

Conjunto de datos:

> Stanford Network Analysis Project. (2012). *Social circles: Facebook* [Conjunto de datos].
> Stanford University. https://snap.stanford.edu/data/ego-Facebook.html

Artículo original de los autores del dataset:

> McAuley, J., & Leskovec, J. (2012). Learning to discover social circles in ego networks.
> En F. Pereira, C. J. C. Burges, L. Bottou, & K. Q. Weinberger (Eds.),
> *Advances in Neural Information Processing Systems* (Vol. 25, pp. 539–547). Curran Associates, Inc.
> https://proceedings.neurips.cc/paper_files/paper/2012/hash/7a614fd06c325499f1680b9896beedeb-Abstract.html
> 
Los archivos originales no se incluyen en el repositorio: el script los descarga
automáticamente desde SNAP la primera vez que se ejecuta.

## Estructura

```
scripts/
  preparar_datos.py     # descarga, procesa y valida los datos; genera los CSV
  graficar_egos.py      # dibuja las tres ego-redes (Figura 2 del informe)
  common_grafo.py        # carga los CSV de una ego-red en un grafo de NetworkX + probabilidades
  comunidades.py          # detección de comunidades: Kruskal + Union-Find (Hito 2, Angela)
  influencers.py          # ranking de influencers: voraz por grado + BFS de alcance (Hito 2, Olenka)
  propagacion.py          # simulación de contagio: BFS por rondas + Dijkstra (Hito 2, Rose)
  main.py                 # integra las tres ramas de análisis sobre una misma ego-red (Hito 2)
data/processed/
  nodos.csv             # un nodo por fila: grado, ego-red, círculo real
  aristas.csv           # una arista por fila: vecinos comunes, peso Jaccard, probabilidades
  membresias.csv        # pertenencia de cada nodo a ego-redes y círculos
  ego_107/  ego_1684/  ego_1912/   # nodos.csv y aristas.csv de cada ego-red
outputs/
  resumen_dataset.md    # métricas del grafo
  histograma_grados.png # Figura 1 del informe
  figura2_tres_egos.png # Figura 2 del informe
```

## Cómo ejecutarlo

Requiere Python 3.10 o superior.

```
pip install -r requirements.txt
python scripts/preparar_datos.py
python scripts/graficar_egos.py --combinada
```

## Atributos calculados

- **Peso Jaccard:** w(u, v) = 1 − |N(u) ∩ N(v)| / |N(u) ∪ N(v)| (distancia: 0 = muy cercanos, 1 = sin amigos en común).
- **Probabilidad de contagio:** p(u, v) = 1 / grado(v), modelo de cascada ponderada (Kempe et al., 2003).

### Hito 2: análisis algorítmico sobre las ego-redes

```
# las tres ramas integradas
python scripts/main.py --ego 1684 --k 17 --top-influencers 10 --destino 3363

# o cada rama por separado
python scripts/comunidades.py --ego 1684 --k 17
python scripts/influencers.py --ego 1684 --top 10
python scripts/propagacion.py --ego 1684 --origen 1684 --alcance
python scripts/propagacion.py --ego 1684 --origen 2782 --destino 3227 --camino
```

## Atributos calculados

- **Peso Jaccard:** w(u, v) = 1 − |N(u) ∩ N(v)| / |N(u) ∪ N(v)| (distancia: 0 = muy cercanos, 1 = sin amigos en común).
- **Probabilidad de contagio:** p(u, v) = 1 / grado(v), modelo de cascada ponderada (Kempe et al., 2003).

## Técnicas y algoritmos aplicados (Hito 2)

| Rama | Técnica | Complejidad |
|---|---|---|
| Comunidades | Kruskal + Union-Find (clustering de enlace simple) | O(E log E) |
| Influencers | Orden voraz por grado + BFS de alcance | O(V·(V+E)) |
| Propagación | BFS por niveles + Dijkstra sobre log(1/p(u,v)) | O(E log V) |

Las estructuras de bajo nivel (Union-Find, BFS, Dijkstra) están implementadas
desde cero, sin depender de las funciones equivalentes de NetworkX; la
librería se usa solo como contenedor del grafo.

## Estado del proyecto

- **Hito 1 (TB1):** modelado del grafo, cálculo de pesos y propuesta de técnicas - completado.
- **Hito 2:** diseño e implementación de los tres algoritmos sobre datos reales - completado; validación de resultados pendiente para la entrega final.
- **Trabajo Final (Hito 3):** validación, conclusiones y video de sustentación - pendiente.
