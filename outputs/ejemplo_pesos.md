# Ejemplos de cálculo de pesos

Fórmulas (todo calculado sobre el grafo completo):

- N(x) = conjunto de vecinos de x, sin incluir a x.
- vecinos_comunes = |N(u) ∩ N(v)|
- |N(u) ∪ N(v)| = grado(u) + grado(v) − |N(u) ∩ N(v)|  (inclusión-exclusión)
- peso_jaccard = 1 − |N(u) ∩ N(v)| / |N(u) ∪ N(v)|  (0 = muy cercanos, 1 = sin amigos en común)
- prob_origen_a_destino = 1 / grado(destino);  prob_destino_a_origen = 1 / grado(origen)  (weighted cascade, Kempe, Kleinberg y Tardos, 2003)

Nota: como u y v son vecinos, v ∈ N(u) y u ∈ N(v); por eso ambos cuentan en la unión pero nunca en la intersección (no hay lazos).

| # | Arista (u, v) | grado(u) | grado(v) | comunes | unión | peso_jaccard | P(u→v) | P(v→u) |
|---|---|---|---|---|---|---|---|---|
| 1 | (1912, 2543) | 755 | 294 | 293 | 756 | 0.612434 | 0.003401 | 0.001325 |
| 2 | (58, 1912) | 12 | 755 | 0 | 767 | 1.000000 | 0.001325 | 0.083333 |
| 3 | (2078, 2206) | 204 | 210 | 199 | 215 | 0.074419 | 0.004762 | 0.004902 |
| 4 | (107, 911) | 1045 | 1 | 0 | 1046 | 1.000000 | 1.000000 | 0.000957 |
| 5 | (0, 107) | 347 | 1045 | 2 | 1390 | 0.998561 | 0.000957 | 0.002882 |

## Cálculo paso a paso

### Ejemplo 1: arista (1912, 2543)

*La arista con MÁS vecinos comunes (amistad muy 'incrustada' en su grupo).*

1. grado(1912) (ego) = 755;  grado(2543) = 294
2. |N(1912) ∩ N(2543)| = **293** amigos en común
3. |N(1912) ∪ N(2543)| = 755 + 294 − 293 = **756**
4. Jaccard = 293 / 756 = 0.387566
5. peso_jaccard = 1 − 0.387566 = **0.612434**
6. P(1912→2543) = 1 / grado(2543) = 1 / 294 = **0.003401**
7. P(2543→1912) = 1 / grado(1912) = 1 / 755 = **0.001325**

### Ejemplo 2: arista (58, 1912)

*Una arista con CERO vecinos comunes entre nodos con varios amigos (puente: peso máximo = 1).*

1. grado(58) = 12;  grado(1912) (ego) = 755
2. |N(58) ∩ N(1912)| = **0** amigos en común
3. |N(58) ∪ N(1912)| = 12 + 755 − 0 = **767**
4. Jaccard = 0 / 767 = 0.000000
5. peso_jaccard = 1 − 0.000000 = **1.000000**
6. P(58→1912) = 1 / grado(1912) = 1 / 755 = **0.001325**
7. P(1912→58) = 1 / grado(58) = 1 / 12 = **0.083333**

### Ejemplo 3: arista (2078, 2206)

*La arista de MENOR peso Jaccard sin egos (los dos amigos casi idénticos en su círculo).*

1. grado(2078) = 204;  grado(2206) = 210
2. |N(2078) ∩ N(2206)| = **199** amigos en común
3. |N(2078) ∪ N(2206)| = 204 + 210 − 199 = **215**
4. Jaccard = 199 / 215 = 0.925581
5. peso_jaccard = 1 − 0.925581 = **0.074419**
6. P(2078→2206) = 1 / grado(2206) = 1 / 210 = **0.004762**
7. P(2206→2078) = 1 / grado(2078) = 1 / 204 = **0.004902**

### Ejemplo 4: arista (107, 911)

*Una arista que toca a un EGO con un amigo de grado 1 (probabilidades muy asimétricas).*

1. grado(107) (ego) = 1045;  grado(911) = 1
2. |N(107) ∩ N(911)| = **0** amigos en común
3. |N(107) ∪ N(911)| = 1045 + 1 − 0 = **1046**
4. Jaccard = 0 / 1046 = 0.000000
5. peso_jaccard = 1 − 0.000000 = **1.000000**
6. P(107→911) = 1 / grado(911) = 1 / 1 = **1.000000**
7. P(911→107) = 1 / grado(107) = 1 / 1045 = **0.000957**

### Ejemplo 5: arista (0, 107)

*Una arista entre DOS EGOS (conecta dos ego-redes distintas).*

1. grado(0) (ego) = 347;  grado(107) (ego) = 1045
2. |N(0) ∩ N(107)| = **2** amigos en común
3. |N(0) ∪ N(107)| = 347 + 1045 − 2 = **1390**
4. Jaccard = 2 / 1390 = 0.001439
5. peso_jaccard = 1 − 0.001439 = **0.998561**
6. P(0→107) = 1 / grado(107) = 1 / 1045 = **0.000957**
7. P(107→0) = 1 / grado(0) = 1 / 347 = **0.002882**
