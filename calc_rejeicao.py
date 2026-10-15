"""
Módulo 14 – Rejeição de carga (pré-dimensionamento analítico de sobretensão temporária a 60 Hz) – funções puras.

AVISO: as Diretrizes de Projeto Básico (3.2.5, 3.2.6 e 8.4) exigem estudo de transitórios eletromagnéticos (EMT/ATP, modelo de Bergeron, estudo estatístico
com ≥ 200 manobras; ONS Procedimentos de Rede, submódulo 23.3). Este módulo é triagem analítica em regime permanente e NÃO substitui o estudo ATP.

Modelo: linha de sequência positiva (Z1 Ω/km e C1 F/km do Módulo 2) com parâmetros distribuídos (ABCD hiperbólico); fonte de Thévenin atrás da barra de origem
(Zs = Un²/Scc, ângulo atan(X/R)); carga no fim da linha rejeitada (terminal aberto), com reator shunt opcional permanecendo ligado.
  Antes da rejeição:  Vs0 = A·Vr0 + B·Ir0 ;  Is0 = C·Vr0 + D·Ir0 ;  E = Vs0 + Zs·Is0           (E = tensão interna da fonte, constante)
  Depois:             Vr = E / [ (A + B·Ysh) + Zs·(C + D·Ysh) ]                                     (Ysh = −jQ/Un² reator shunt no fim da linha)
Efeito Ferranti (fonte rígida, sem carga):  Vr/Vs = 1/cosh(γ·ℓ).
Limitações: 60 Hz, sequência positiva (carga equilibrada), sem saturação de transformadores, sem sobretensão de manobra/ressonância harmônica e sem a dinâmica do
gerador/regulador; circuito paralelo energizado e acoplamento não considerados.
"""
import cmath
import math


def abcd(Z1, C1, comp_km, f=60.0):
    w = 2 * math.pi * f
    Y = complex(0.0, w * C1)
    Zo = cmath.sqrt(Z1 / Y)
    gl = cmath.sqrt(Z1 * Y) * comp_km
    return cmath.cosh(gl), Zo * cmath.sinh(gl), cmath.sinh(gl) / Zo, cmath.cosh(gl), Zo, gl


def tensao_apos_rejeicao(Z1, C1, comp_km, un_kv, scc_mva, xr, s_mva, fp, q_shunt_mvar, vr0_pu=1.0, f=60.0):
    """Retorna dict com tensões (kV fase-fase) antes/depois e grandezas intermediárias."""
    A, B, C, D, Zo, gl = abcd(Z1, C1, comp_km, f)
    U = un_kv * 1e3
    zs_mod = U ** 2 / (scc_mva * 1e6)
    th = math.atan(xr)
    Zs = zs_mod * complex(math.cos(th), math.sin(th))
    Ysh = complex(0.0, -q_shunt_mvar * 1e6 / U ** 2)                 # reator shunt (indutivo): −jB
    vr0 = vr0_pu * U / math.sqrt(3)
    S = s_mva * 1e6 * complex(fp, math.sqrt(max(0.0, 1 - fp * fp)))
    ir_carga = (S / (3 * vr0)).conjugate() if s_mva > 0 else 0j
    ir0 = ir_carga + Ysh * vr0
    vs0 = A * vr0 + B * ir0
    is0 = C * vr0 + D * ir0
    E = vs0 + Zs * is0
    den = (A + B * Ysh) + Zs * (C + D * Ysh)
    vr = E / den
    vs_depois = (A + B * Ysh) * vr
    return dict(vr_antes_kv=abs(vr0) * math.sqrt(3) / 1e3, vs_antes_kv=abs(vs0) * math.sqrt(3) / 1e3, E_kv=abs(E) * math.sqrt(3) / 1e3,
                vr_kv=abs(vr) * math.sqrt(3) / 1e3, vs_depois_kv=abs(vs_depois) * math.sqrt(3) / 1e3, Zs=Zs, Zo=Zo, gl=gl,
                ferranti=1.0 / abs(cmath.cosh(gl)), zs_ohm=zs_mod)


def calcular(e):
    """e: Z1 [re, im] (Ω/km), C1 (F/km), comp_km, un_kv, umax_kv, f, scc_mva, xr, s_mva, fp, q_shunt, vr0_pu, lim_pu (base Un), nome_circ."""
    erros, avisos = [], []
    if not e.get("z1") or not e.get("c1"):
        return dict(erros=["Parâmetros de sequência positiva indisponíveis (Módulo 2: selecione condutor, cabos guarda e geometria)."], avisos=[])
    if not e.get("comp_km"):
        return dict(erros=["Informe o comprimento da LT (Módulo 1)."], avisos=[])
    Z1 = complex(*e["z1"])
    C1 = e["c1"]
    args = dict(Z1=Z1, C1=C1, comp_km=e["comp_km"], un_kv=e["un_kv"], scc_mva=e["scc_mva"], xr=e["xr"], fp=e["fp"], vr0_pu=e["vr0_pu"], f=e["f"])
    base = tensao_apos_rejeicao(s_mva=e["s_mva"], q_shunt_mvar=e["q_shunt"], **args)
    sem_reator = tensao_apos_rejeicao(s_mva=e["s_mva"], q_shunt_mvar=0.0, **args)
    lim_kv = e["lim_pu"] * e["un_kv"]
    pu = base["vr_kv"] / e["un_kv"]
    # compensação mínima para atender o limite
    q_min = None
    if sem_reator["vr_kv"] > lim_kv:
        lo, hi = 0.0, 5000.0
        if tensao_apos_rejeicao(s_mva=e["s_mva"], q_shunt_mvar=hi, **args)["vr_kv"] > lim_kv:
            q_min = float("inf")
        else:
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                lo, hi = (mid, hi) if tensao_apos_rejeicao(s_mva=e["s_mva"], q_shunt_mvar=mid, **args)["vr_kv"] > lim_kv else (lo, mid)
            q_min = 0.5 * (lo + hi)
    else:
        q_min = 0.0
    # varreduras
    c_carga = []
    for i in range(0, 21):
        s = e["s_mva"] * (0.0 + 0.1 * i) if e["s_mva"] > 0 else 0.0
        c_carga.append(dict(x=float(s), pu=float(tensao_apos_rejeicao(s_mva=s, q_shunt_mvar=e["q_shunt"], **args)["vr_kv"] / e["un_kv"])))
    c_scc = []
    for k in (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0):
        a2 = dict(args, scc_mva=e["scc_mva"] * k)
        c_scc.append(dict(x=float(e["scc_mva"] * k), pu=float(tensao_apos_rejeicao(s_mva=e["s_mva"], q_shunt_mvar=e["q_shunt"], **a2)["vr_kv"] / e["un_kv"])))
    c_q = []
    qmax = max(e["q_shunt"] * 2.0, (q_min if q_min and math.isfinite(q_min) else 0.0) * 1.5, 50.0)
    for i in range(0, 21):
        q = qmax * i / 20.0
        c_q.append(dict(x=float(q), pu=float(tensao_apos_rejeicao(s_mva=e["s_mva"], q_shunt_mvar=q, **args)["vr_kv"] / e["un_kv"])))
    if base["gl"].imag > math.pi / 2:
        avisos.append("Linha com ângulo elétrico > 90°: cosh(γℓ) pode se aproximar de zero (ressonância de 60 Hz). Revisar com estudo EMT.")
    if e["scc_mva"] < 5 * e["s_mva"]:
        avisos.append("Fonte fraca (Scc < 5× carga): sobretensão fortemente dependente da impedância da fonte.")
    avisos.append("TRIAGEM ANALÍTICA: não substitui o estudo de transitórios eletromagnéticos (ATP/EMTP, ≥ 200 manobras) exigido nas Diretrizes 3.2.5/3.2.6/8.4.")
    return dict(erros=erros, avisos=avisos, base=base, sem_reator=sem_reator, pu=float(pu), pu_sem_reator=float(sem_reator["vr_kv"] / e["un_kv"]),
                lim_kv=float(lim_kv), ok=bool(base["vr_kv"] <= lim_kv + 1e-9), q_min=q_min, c_carga=c_carga, c_scc=c_scc, c_q=c_q,
                pu_umax=float(base["vr_kv"] / e["umax_kv"]), e=e)
