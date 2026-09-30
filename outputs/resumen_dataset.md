# Resumen del dataset - Facebook (SNAP, ego-Facebook)

Generado automáticamente por `scripts/preparar_datos.py`.

## Grafo completo

| Métrica | Valor |
|---|---|
| Nodos | 4,039 |
| Aristas (no dirigidas) | 88,234 |
| Grado promedio | 43.69 |
| Grado máximo | 1,045 (nodo 107) |
| Densidad | 0.010820 |
| Componentes conexas | 1 |
| Coeficiente de clustering promedio | 0.6055 |

## Las 10 ego-redes (ordenadas por tamaño)

Ego-red = ego ∪ nodos de `.edges` ∪ nodos de `.feat`. La columna *Nodos (.edges + ego)* muestra el tamaño si solo se usara `.edges`; la diferencia son amigos del ego sin amistades con otros amigos del ego.

| # | Ego | Nodos | Nodos (.edges + ego) | Aristas del subgrafo | Círculos | Elegida |
|---|---|---|---|---|---|---|
| 1 | 107 | 1,046 | 1,035 | 27,795 | 9 | ✔ |
| 2 | 1684 | 793 | 787 | 14,817 | 17 | ✔ |
| 3 | 1912 | 756 | 748 | 30,780 | 46 | ✔ |
| 4 | 3437 | 548 | 535 | 5,360 | 32 |  |
| 5 | 0 | 348 | 334 | 2,866 | 24 |  |
| 6 | 348 | 228 | 225 | 3,419 | 14 |  |
| 7 | 686 | 171 | 169 | 1,831 | 14 |  |
| 8 | 414 | 160 | 151 | 1,857 | 7 |  |
| 9 | 698 | 67 | 62 | 336 | 13 |  |
| 10 | 3980 | 60 | 53 | 205 | 17 |  |

Criterio: las 3 ego-redes más grandes con al menos 500 nodos.

## Solapamiento entre las ego-redes elegidas

| Conjunto | Nodos |
|---|---|
| 107 ∩ 1684 | 16 |
| 107 ∩ 1912 | 6 |
| 1684 ∩ 1912 | 1 |
| las 3 a la vez | 1 |
| en al menos 2 | 21 |
| unión de las 3 | 2,573 |
