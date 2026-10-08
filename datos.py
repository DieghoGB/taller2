"""Generador reproducible de instancias del packing de tomate (Arica)."""
import numpy as np

CALIBRES = [6, 7, 8, 9, 10]
JORNADAS = ["Dom", "Lun", "Jue", "Vie"]

# Parámetros operacionales (sección 3 del enunciado)
R = 200                # gamelas brutas / hora
H = 12                 # horas por jornada
CAP_CAMION = 24 * 49   # 1.176 gamelas comerciales / camión
MAX_CAMIONES = 2       # camiones por jornada
COSTO_CAMION = 150 * CAP_CAMION   # 176.400 $/camión (150 $/gamela con camión lleno)

# Margen de contribución por gamela comercial, sin transporte ($/gamela). Sintético.
MARGEN = {6: 350, 7: 650, 8: 1100, 9: 1050, 10: 500}

SEMILLA = 2026
TAMANOS = {"E1": 40, "E2": 80, "E3": 160, "E4": 320}


def generar(n_lotes, semilla=SEMILLA):
    """Devuelve un diccionario con los datos de una instancia de n_lotes lotes."""
    rng = np.random.default_rng(semilla + n_lotes)
    G = rng.integers(90, 141, size=n_lotes)                 # gamelas brutas por lote
    eta = rng.uniform(0.85, 0.95, size=n_lotes)             # rendimiento comercial
    # Perfil por calibre: Dirichlet centrado en calibres 7-9, con heterogeneidad entre lotes
    alpha = np.array([1.0, 2.0, 3.0, 3.0, 1.0])
    perfil = rng.dirichlet(alpha * 2.0, size=n_lotes)
    lotes = list(range(n_lotes))
    Q = {(i, c): float(eta[i] * G[i] * perfil[i, k])
         for i in lotes for k, c in enumerate(CALIBRES)}
    return {
        "I": lotes, "C": CALIBRES, "T": JORNADAS,
        "G": {i: int(G[i]) for i in lotes},
        "eta": {i: float(eta[i]) for i in lotes},
        "Q": Q, "m": MARGEN,
        "RH": {t: R * H for t in JORNADAS},
        "cap_camion": CAP_CAMION, "max_camiones": MAX_CAMIONES,
        "costo_camion": COSTO_CAMION,
    }
