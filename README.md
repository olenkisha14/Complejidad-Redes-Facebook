# Análisis Algorítmico de la Red ego-Facebook (SNAP)

Trabajo del curso **1ACC0184 Complejidad Algorítmica** (UPC, ciclo 2026-20).
Entregas: Trabajo Parcial (TB1), Hito 2 y Trabajo Final (Hito 3).

Aplicativo que analiza automáticamente la red social ego-Facebook del Stanford
Network Analysis Project (SNAP) aplicando tres técnicas de teoría de grafos para
responder tres preguntas distintas sobre la red:

1. **¿Qué comunidades de usuarios se forman?** (Kruskal + Union-Find, O(E log E))
2. **¿Quiénes son los usuarios más influyentes?** (voraz por grado + BFS a 2 saltos, O(V·(V+E)))
3. **¿Cómo se propagaría un mensaje desde un usuario?** (BFS por niveles + Dijkstra sobre log(1/p), O(E log V))

El aplicativo expone dos interfaces: una por línea de comandos (`main.py`) y
una interfaz gráfica web construida con Streamlit (`app.py`).

## Integrantes

| Código     | Integrante                             | Ego-red asignada |
|------------|----------------------------------------|------------------|
| U202411669 | Olenka Priscilla Del Aguila Del Aguila | Ego 1684         |
| U202415495 | Angela Milagros Espinoza Cruz          | Ego 107          |
| U202417857 | Rose Almendra Vergaray Calderon        | Ego 1912         |

## Dataset

Se usa el conjunto **ego-Facebook** del Stanford Network Analysis Project (SNAP):
4,039 usuarios y 88,234 amistades, con datos anonimizados por sus autores.

> McAuley, J., & Leskovec, J. (2012). Learning to discover social circles in ego networks.
> *Advances in Neural Information Processing Systems*, 25, 539-547.
> Fuente: <https://snap.stanford.edu/data/ego-Facebook.html>

Los archivos originales no se incluyen en el repositorio: el script
`preparar_datos.py` los descarga automáticamente desde SNAP la primera vez que
se ejecuta.

## Estructura del repositorio

```
.
├── scripts/
│   ├── preparar_datos.py    # descarga, procesa y valida los datos; genera los CSV
│   ├── graficar_egos.py     # dibuja las tres ego-redes (Figura 2 del informe)
│   ├── common_grafo.py      # carga los CSV de una ego-red en un grafo de NetworkX
│   ├── comunidades.py       # Kruskal + Union-Find (detección de comunidades)
│   ├── influencers.py       # voraz por grado + BFS de alcance (ranking de influencers)
│   ├── propagacion.py       # BFS + Dijkstra (simulación de propagación)
│   ├── main.py              # integra las tres ramas sobre una misma ego-red (CLI)
│   └── medir_tiempos.py     # mide los tiempos de ejecución (validación empírica)
├── data/processed/
│   ├── nodos.csv            # un nodo por fila: grado, ego-red, círculo real
│   ├── aristas.csv          # una arista por fila: vecinos comunes, peso Jaccard, probabilidades
│   ├── membresias.csv       # pertenencia de cada nodo a ego-redes y círculos
│   └── ego_107/ ego_1684/ ego_1912/   # nodos.csv y aristas.csv por ego-red
├── outputs/
│   ├── resumen_dataset.md   # métricas globales de la red
│   ├── histograma_grados.png # Figura 1 del informe
│   └── figura2_tres_egos.png # Figura 2 del informe
├── app.py                   # interfaz gráfica web con Streamlit
├── requirements.txt         # dependencias de Python
└── README.md
```

## Requisitos previos

- **Python 3.10 o superior** instalado (recomendado 3.12).
  Verifica tu versión con:

  ```bash
  python --version
  ```

  Si tu sistema no reconoce `python`, prueba con `python3` o `py` (Windows).

- Conexión a internet (solo la primera vez, para descargar el dataset y las dependencias).

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/olenkisha14/Complejidad-Redes-Facebook.git
cd Complejidad-Redes-Facebook
```

### 2. (Opcional, recomendado) Crear un entorno virtual

Esto aísla las dependencias del proyecto del resto de tu sistema.

**En Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**En macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

Esto instala NetworkX, pandas, matplotlib, numpy y scipy.

### 4. Instalar Streamlit (solo para la GUI)

```bash
pip install streamlit
```

## Uso

### Opción A: Línea de comandos (CLI)

Para preparar los datos (descarga el dataset y genera los CSV, solo la primera vez):

```bash
python scripts/preparar_datos.py
```

Para generar las visualizaciones:

```bash
python scripts/graficar_egos.py --combinada
```

Para correr una rama específica:

```bash
python scripts/comunidades.py --ego 1684 --k 17
python scripts/influencers.py --ego 1684 --top 10
python scripts/propagacion.py --ego 1684 --origen 1684 --alcance
python scripts/propagacion.py --ego 1684 --origen 2782 --destino 3227 --camino
```

Para correr las tres ramas integradas sobre una ego-red:

```bash
python scripts/main.py --ego 1684 --k 17 --top-influencers 10 --destino 3363
```

Para medir los tiempos de ejecución de cada rama (validación empírica):

```bash
python scripts/medir_tiempos.py
```

### Opción B: Interfaz gráfica web (recomendada para demostración)

Desde la raíz del proyecto:

```bash
python -m streamlit run app.py
```

Streamlit abrirá automáticamente tu navegador en <http://localhost:8501>.

La primera vez puede pedirte un correo (se puede dejar vacío y presionar Enter).

**Cómo usarla:**

1. En la barra lateral izquierda, selecciona la ego-red a analizar (107, 1684 o 1912).
2. Usa las tres pestañas para ejecutar cada rama:
   - **Comunidades:** elige el número de comunidades `k` y presiona *Detectar comunidades*.
   - **Influencers:** elige el `top` de usuarios a listar y presiona *Calcular ranking*.
   - **Propagación:** selecciona un nodo origen (y opcionalmente un destino), luego *Simular propagación*.
3. Cada pestaña muestra el tiempo real de ejecución junto con los resultados.

Para detener la aplicación, presiona `Ctrl + C` en la terminal donde está corriendo.

## Atributos calculados sobre el grafo

- **Peso Jaccard:** `w(u, v) = 1 − |N(u) ∩ N(v)| / |N(u) ∪ N(v)|` (distancia: 0 si los vecindarios son idénticos, 1 si no comparten amigos).
- **Probabilidad de contagio:** `p(u, v) = 1 / grado(v)`, según el modelo de cascada ponderada (Kempe et al., 2003). No es simétrica.

## Técnicas y complejidades

| Rama        | Técnica                                        | Complejidad   |
|-------------|------------------------------------------------|---------------|
| Comunidades | Kruskal + Union-Find (clustering de enlace simple) | O(E log E)   |
| Influencers | Voraz por grado + BFS de alcance (2 saltos)    | O(V·(V+E))    |
| Propagación | BFS por niveles + Dijkstra sobre log(1/p(u, v)) | O(E log V)   |

Las estructuras de bajo nivel (Union-Find, BFS, Dijkstra) están implementadas
desde cero, sin depender de las funciones equivalentes de NetworkX; la librería
se usa solo como contenedor del grafo. Esto permite validar la comprensión
concreta de cada técnica.

## Problemas comunes

- **`python: command not found`**: prueba con `python3` o `py`.
- **`ModuleNotFoundError: streamlit`**: corre `pip install streamlit`.
- **`FileNotFoundError: nodos_1684.csv`**: asegúrate de haber corrido primero `python scripts/preparar_datos.py`, o verifica que la carpeta `data/processed/` tiene los CSV y las subcarpetas `ego_107/`, `ego_1684/`, `ego_1912/`.
- **El navegador no se abre automáticamente al correr Streamlit**: abre manualmente <http://localhost:8501>.

## Estado del proyecto

- **Hito 1 (TB1):** modelado del grafo, cálculo de pesos y propuesta de técnicas. Completado.
- **Hito 2:** diseño e implementación de los tres algoritmos sobre datos reales. Completado.
- **Trabajo Final (Hito 3):** validación empírica de complejidad, interfaz gráfica, informe final y exposición. Completado.
