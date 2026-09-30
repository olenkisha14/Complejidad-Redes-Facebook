# Redes sociales y comunidades: análisis de la red de Facebook (SNAP)

Trabajo Parcial (TB1) del curso **1ACC0184 – Complejidad Algorítmica** (UPC, 2026-20).

## Integrantes

| Código | Integrante | Ego-red asignada |
|---|---|---|
| U202411669 | Olenka Priscilla Del Aguila Del Aguila | Ego 1684 |
| U202415495 | Angela Milagros Espinoza Cruz | Ego 107 |
| U202417857 | Rose Almendra Vergaray Calderon | Ego 1912 |

## Datos

Se usa el conjunto **ego-Facebook** del Stanford Network Analysis Project (SNAP):
4,039 usuarios y 88,234 amistades, con datos anonimizados por sus autores.

> McAuley, J., & Leskovec, J. (2012). Learning to discover social circles in ego networks.
> *Advances in Neural Information Processing Systems*, 25, 539–547.
> Fuente: https://snap.stanford.edu/data/ego-Facebook.html

Los archivos originales no se incluyen en el repositorio: el script los descarga
automáticamente desde SNAP la primera vez que se ejecuta.

## Estructura

```
scripts/
  preparar_datos.py     # descarga, procesa y valida los datos; genera los CSV
  graficar_egos.py      # dibuja las tres ego-redes (Figura 2 del informe)
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
