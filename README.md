# Taller 2 — Reformulación de un modelo entero mixto
Programación semanal de lotes de tomate en un packing de Arica.
Diego Baltazar · Pedro Limarí — Investigación de Operaciones, Doctorado en Ingeniería, Consorcio UV–UTA.

## Contenido
| Archivo | Descripción |
|---|---|
| `datos.py` | Parámetros del caso y generador de instancias (semilla 2026) |
| `modelo.py` | Modelo Pyomo; `construir(datos, formulacion="A" o "B")` |
| `experimento.py` | Resolución con HiGHS y extracción de los siete indicadores |
| `resultados.ipynb` | Cuaderno que reproduce la tabla del informe de principio a fin |
| `requirements.txt` | Declaración de entorno |

## Reproducción
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute resultados.ipynb
```
Condiciones de ejecución: HiGHS con 1 hilo, semilla del solver 0, límite de 600 s, tolerancia de brecha 10⁻⁶, 3 repeticiones por combinación.

## Modelo
**Conjuntos.** Lotes $i\in I$; calibres $c\in C=\{6,7,8,9,10\}$; jornadas $t\in T=\{\text{Dom},\text{Lun},\text{Jue},\text{Vie}\}$.

**Parámetros.** $G_i$ gamelas brutas del lote; $\eta_i$ rendimiento comercial; $p_{ic}$ fracción del calibre $c$ ($\sum_c p_{ic}=1$); $Q_{ic}=\eta_i G_i p_{ic}$ gamelas comerciales esperadas por calibre; $m_c$ margen por gamela comercial sin transporte; $RH_t=200\cdot12$ capacidad de selección; $K=1.176$ gamelas por camión; $F=176.400$ costo por camión.

**Variables.** $z_i\in\{0,1\}$ lote incorporado; $y_t\in\{0,1,2\}$ camiones despachados; $q_{it}\ge0$ gamelas brutas procesadas; $x_{ict}\ge0$ gamelas comerciales por calibre.

**Formulación A.**
$$\max\ \sum_{i,c,t} m_c x_{ict} - F\sum_t y_t$$
$$\sum_t q_{it}=G_i z_i\quad\forall i \qquad\qquad \sum_c x_{ict}=\eta_i q_{it}\quad\forall i,t$$
$$\sum_t x_{ict}\le Q_{ic}\quad\forall i,c \qquad\qquad \sum_i q_{it}\le RH_t\quad\forall t \qquad\qquad \sum_{i,c} x_{ict}\le K y_t\quad\forall t$$

**Formulación B.** A más $\ \sum_t x_{ict}\le Q_{ic}\,z_i\quad\forall i,c$.

**Equivalencia (argumento algebraico).** Si $z_i=0$, ambas fuerzan $q_{it}=0$ y por tanto $x_{ict}=0$, y la restricción de B se cumple. Si $z_i=1$, la restricción de B coincide con $\sum_t x_{ict}\le Q_{ic}$, ya presente en A. Luego los conjuntos de soluciones enteras coinciden. Se complementa con verificación numérica en el cuaderno.
