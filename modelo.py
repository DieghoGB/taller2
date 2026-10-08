"""Modelo del packing con dos formulaciones seleccionables por parámetro."""
import pyomo.environ as pyo


def construir(d, formulacion="A"):
    assert formulacion in ("A", "B")
    m = pyo.ConcreteModel(name=f"packing_{formulacion}")
    m.I = pyo.Set(initialize=d["I"])
    m.C = pyo.Set(initialize=d["C"])
    m.T = pyo.Set(initialize=d["T"])

    m.z = pyo.Var(m.I, domain=pyo.Binary)                       # lote incorporado
    m.y = pyo.Var(m.T, domain=pyo.NonNegativeIntegers,
                  bounds=(0, d["max_camiones"]))                # camiones por jornada
    m.q = pyo.Var(m.I, m.T, domain=pyo.NonNegativeReals)        # gamelas brutas
    m.x = pyo.Var(m.I, m.C, m.T, domain=pyo.NonNegativeReals)   # gamelas comerciales

    m.obj = pyo.Objective(
        expr=sum(d["m"][c] * m.x[i, c, t] for i in m.I for c in m.C for t in m.T)
        - d["costo_camion"] * sum(m.y[t] for t in m.T),
        sense=pyo.maximize)

    # (1) Un lote incorporado se procesa completo dentro de la semana
    m.completo = pyo.Constraint(m.I, rule=lambda m, i:
        sum(m.q[i, t] for t in m.T) == d["G"][i] * m.z[i])
    # (2) Rendimiento comercial por jornada
    m.rendimiento = pyo.Constraint(m.I, m.T, rule=lambda m, i, t:
        sum(m.x[i, c, t] for c in m.C) == d["eta"][i] * m.q[i, t])
    # (3) Perfil por calibre (versión agregada, común a A y B)
    m.perfil = pyo.Constraint(m.I, m.C, rule=lambda m, i, c:
        sum(m.x[i, c, t] for t in m.T) <= d["Q"][i, c])
    # (4) Capacidad de la seleccionadora
    m.seleccion = pyo.Constraint(m.T, rule=lambda m, t:
        sum(m.q[i, t] for i in m.I) <= d["RH"][t])
    # (5) Despacho: capacidad de los camiones enviados
    m.despacho = pyo.Constraint(m.T, rule=lambda m, t:
        sum(m.x[i, c, t] for i in m.I for c in m.C) <= d["cap_camion"] * m.y[t])

    if formulacion == "B":
        # (6) Restricción desagregada por calibre ligada a la selección del lote
        m.perfil_z = pyo.Constraint(m.I, m.C, rule=lambda m, i, c:
            sum(m.x[i, c, t] for t in m.T) <= d["Q"][i, c] * m.z[i])
    return m
