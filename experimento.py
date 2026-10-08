"""Ejecución del experimento: resuelve A y B sobre E1..E4 y reporta los siete indicadores."""
import os, re, time, platform, tempfile
import highspy
from importlib.metadata import version
import pyomo.environ as pyo
from datos import generar, TAMANOS
from modelo import construir

LIMITE_TIEMPO = float(os.environ.get("LIMITE_TIEMPO", 600))   # segundos
REPETICIONES = int(os.environ.get("REPETICIONES", 3))
HILOS = 1               # un hilo para que las corridas sean deterministas y comparables
SEMILLA_SOLVER = 0


def _a_mps(modelo, ruta):
    modelo.write(ruta, io_options={"symbolic_solver_labels": False})


def _resolver(ruta_mps, relajacion=False, log=None):
    h = highspy.Highs()
    h.setOptionValue("output_flag", log is not None)
    if log:
        h.setOptionValue("log_file", log)
        h.setOptionValue("log_to_console", False)
    h.setOptionValue("threads", HILOS)
    h.setOptionValue("random_seed", SEMILLA_SOLVER)
    h.setOptionValue("time_limit", LIMITE_TIEMPO)
    h.setOptionValue("mip_rel_gap", 1e-6)
    h.readModel(ruta_mps)
    if relajacion:
        h.setOptionValue("solve_relaxation", True)
    t0 = time.perf_counter()
    h.run()
    t = time.perf_counter() - t0
    info = h.getInfo()
    lp = h.getLp()
    return h, info, t, lp


def _cortes(log):
    """Extrae del log de HiGHS los cortes del pool y los activos en el LP."""
    filas = []
    with open(log) as f:
        for linea in f:
            # Filas de la tabla de B&B: empiezan con un indicador y terminan con tiempo 'Ns'
            if re.search(r"\d+\.\d+s\s*$", linea) and "%" in linea:
                filas.append(linea.split())
    if not filas:
        return 0, 0
    # Columnas finales de la tabla: Gap | Cuts | InLp | Confl. | LpIters | Time
    # 'Cuts' = cortes en el pool de HiGHS; 'InLp' = cortes activos en el LP del nodo.
    # Se reporta el máximo observado de cada columna durante la resolución.
    cortes = max(int(f[-5]) for f in filas)
    activos = max(int(f[-4]) for f in filas)
    return cortes, activos


def correr_instancia(nombre, n):
    d = generar(n)
    oferta = sum(d["G"].values())
    filas = []
    for form in ("A", "B"):
        m = construir(d, form)
        tmp = tempfile.mkdtemp()
        ruta = os.path.join(tmp, f"{nombre}_{form}.mps")
        # Pyomo invierte el sentido al escribir MPS si es max: lo manejamos leyendo el signo
        _a_mps(m, ruta)
        _, info_lp, _, lp = _resolver(ruta, relajacion=True)
        tiempos, ultimo = [], None
        for r in range(REPETICIONES):
            log = os.path.join(tmp, f"{nombre}_{form}_{r}.log")
            h, info, t, _ = _resolver(ruta, log=log)
            tiempos.append(t)
            ultimo = (h, info, log)
        h, info, log = ultimo
        signo = -1 if lp.sense_ == highspy.ObjSense.kMinimize else 1
        z_lp = signo * info_lp.objective_function_value
        z_ip = signo * info.objective_function_value
        cota = signo * info.mip_dual_bound
        cortes_gen, cortes_act = _cortes(log)
        filas.append({
            "instancia": nombre, "lotes": n, "oferta_brutas": oferta,
            "oferta_pct": round(100 * oferta / 9600, 1),
            "formulacion": form,
            "variables": lp.num_col_, "restricciones": lp.num_row_,
            "no_nulos": lp.a_matrix_.index_.__len__(),
            "Z_LP": z_lp, "Z_IP": z_ip, "cota_final": cota,
            "brecha_LP_pct": 100 * (z_lp - z_ip) / abs(z_ip),
            "integrality_gap": z_lp / z_ip,
            "brecha_opt_pct": 100 * info.mip_gap,
            "nodos": info.mip_node_count,
            "cortes_generados": cortes_gen, "cortes_activos": cortes_act,
            "tiempo_medio_s": sum(tiempos) / len(tiempos),
            "tiempos_s": [round(x, 3) for x in tiempos],
            "estado": h.modelStatusToString(h.getModelStatus()),
        })
    return filas


def entorno():
    return {
        "python": platform.python_version(), "sistema": platform.platform(),
        "procesador": platform.processor() or platform.machine(),
        "pyomo": version("pyomo"), "highspy": version("highspy"),
        "hilos": HILOS, "limite_tiempo_s": LIMITE_TIEMPO, "repeticiones": REPETICIONES,
    }


if __name__ == "__main__":
    import pandas as pd
    filas = []
    for nombre, n in TAMANOS.items():
        filas += correr_instancia(nombre, n)
    df = pd.DataFrame(filas)
    df.to_csv("resultados.csv", index=False)
    print(entorno())
    print(df.drop(columns=["tiempos_s"]).to_string())
