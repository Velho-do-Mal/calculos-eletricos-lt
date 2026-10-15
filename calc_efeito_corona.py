"""
Módulo 11 – Efeito corona (gradiente superficial, critério de Peek e perdas) – funções puras (sem Streamlit). Estudo independente:
atende também clientes que pedem somente o corona.

Fontes (acervo do projeto):
  • Gradiente superficial: simulação de cargas + fator de feixe (Kiessling 2.3.3, eq. 2.12–2.23) – reaproveita calc_corona.gradientes_fases.
  • Densidade relativa do ar: δ = 3,92·p/(273+θ), p = 76·10^(−h/18336) cmHg (Livro 2 – Projeto Elétrico de LTs, 3.2.5; Livro 3, 7.5).
  • Gradiente crítico disruptivo (Peek): E0 = g0·m·δ·(1 + 0,301/√(δ·r)) [kV_ef/cm, r em cm]; g0 = 21,1 (usual) ou 21,6 kV_ef/cm (Livro 3, 7.5).
    Chuva: m multiplicado por mt = 0,8 (Livro 2, 3.2.5). NECESSITA VALIDAÇÃO: a eq. (1) do Livro 3 está ilegível no OCR.
  • Tensão crítica disruptiva (Livro 2, 3.2.5):  Uc = 84·mc·mt·δ·r·n·log10(D/r')   [kV entre fases]; Vc = Uc/√3,
    r' = (n·r·R^(n−1))^(1/n) (raio equivalente do feixe), R = raio do círculo do feixe, D = distância média geométrica entre fases.
  • Perdas (Peek, Livro 2, 3.2.6):  P = (241/δ)·(f+25)·√(r/D)·(V−Vc)²·10⁻⁵  [kW/km por fase; V e Vc em kV fase-neutro, r e D na mesma unidade].
    Limite usual de projeto: 1,2 kW/km (Livro 3 / Villas) ou 1,24 kW/km (Livro 2) para a linha trifásica. Kiessling 7.3.4 (informativo): tempo bom ≈ 2 kW/km,
    chuva ≈ 5 kW/km, geada até 100 kW/km (EHV).
Premissas: condutores na altura mínima (conservador para o gradiente); cabos guarda aterrados incluídos por padrão; gradientes proporcionais à tensão.
Limitações: Peek foi deduzido para condutor cilíndrico; perdas em chuva forte/geada podem ser muito maiores (ver Kiessling).
"""
import math

import calc_campos as cc
import calc_corona as cr

LIM_PERDA_KW_KM = 1.2


def gmd_fases(fases, circ):
    """Distância média geométrica (m) entre as fases do circuito `circ` (3 fases)."""
    ps = [(f["x"], f["y"]) for f in fases if f["circuito"] == circ]
    ds = [math.hypot(a[0] - b[0], a[1] - b[1]) for i, a in enumerate(ps) for b in ps[i + 1:]]
    if not ds:
        return 0.0
    return math.exp(sum(math.log(d) for d in ds) / len(ds))


def r_equiv_feixe(n, r_cm, s_cm):
    """r' = (n·r·R^(n−1))^(1/n) (cm); n = 1 → r."""
    if n < 2:
        return r_cm
    R = cr.r_feixe(n, s_cm)
    return (n * r_cm * R ** (n - 1)) ** (1.0 / n)


def tensao_critica(delta, mc, mt, n, r_cm, s_cm, D_m):
    """Uc (kV entre fases) e Vc (kV fase-neutro) – Livro 2, 3.2.5. D em m."""
    rp = r_equiv_feixe(n, r_cm, s_cm)
    uc = 84.0 * mc * mt * delta * r_cm * n * math.log10(D_m * 100.0 / rp)
    return uc, uc / math.sqrt(3.0), rp


def perda_peek(v_kv, vc_kv, delta, freq, r_cm, D_m):
    """kW/km por fase (Livro 2, 3.2.6). r e D na mesma unidade (aqui: cm)."""
    if v_kv <= vc_kv:
        return 0.0
    return 241.0 / delta * (freq + 25.0) * math.sqrt(r_cm / (D_m * 100.0)) * (v_kv - vc_kv) ** 2 * 1e-5


def e_critico(delta, m, r_cm, g0=21.1):
    """Gradiente crítico de Peek (kV_ef/cm)."""
    return g0 * m * delta * (1.0 + 0.301 / math.sqrt(delta * r_cm))


def calcular_estudo(e):
    """e (JSON): fases, guardas, incluir_guardas, circs {id: dict(un_kv, umax_kv, status, n, d_mm, s_mm)}, h_min, alt, temp, freq,
    mc (rugosidade do cabo, Livro 2), m_sup (fator m de superfície no gradiente), g0, mt_chuva, lim_perda, lim_g_rel (E/E0 aceito)."""
    erros, avisos = [], []
    if not e.get("fases"):
        return dict(erros=["Geometria sem fases: preencha o Módulo 2 / seção transversal."], avisos=[])
    circs = {}
    for k, c in e["circs"].items():
        if not c.get("umax_kv"):
            erros.append(f"Tensão máxima do circuito {k} não informada.")
        if not c.get("d_mm"):
            erros.append(f"Condutor do circuito {k} não selecionado.")
        circs[int(k)] = dict(un_kv=c["umax_kv"], i_a=0.0, fp=1.0, status=c["status"])
    if erros:
        return dict(erros=erros, avisos=[])
    est = cc.monta_estudo(e["fases"], circs, e["guardas"], e["incluir_guardas"], e.get("h_min"))
    cabos = {int(k): dict(n=c["n"], d_mm=c["d_mm"], s_mm=c["s_mm"]) for k, c in e["circs"].items()}
    gr = cr.gradientes_fases(est, cabos)            # gradientes na tensão máxima operativa
    if not gr:
        return dict(erros=["Nenhum circuito energizado para o cálculo."], avisos=[])
    delta = cr.delta_ar(e["alt"], e["temp"])
    f_hz = float(e.get("freq", 60.0))
    out_c = {}
    for k, c in e["circs"].items():
        k = int(k)
        if c["status"] == "Inexistente":
            continue
        n, r_cm, s_cm = int(c["n"]), c["d_mm"] / 20.0, c["s_mm"] / 10.0
        D = gmd_fases(e["fases"], k)
        fk = float(c["un_kv"]) / float(c["umax_kv"]) if c["umax_kv"] else 1.0
        gk = [g for g in gr if g["circuito"] == k]
        if not gk:
            continue
        cond = {}
        for nome_c, mt in (("Tempo bom", 1.0), ("Chuva", e["mt_chuva"])):
            uc, vc, rp = tensao_critica(delta, e["mc"], mt, n, r_cm, s_cm, D)
            e0 = e_critico(delta, e["m_sup"] * mt, r_cm, e["g0"])
            tens = {}
            for rot, un in (("Un", c["un_kv"]), ("Umáx", c["umax_kv"])):
                v_f = un / math.sqrt(3.0)
                p_f = perda_peek(v_f, vc, delta, f_hz, rp, D)
                emax = max(g["E"] for g in gk) * (un / c["umax_kv"])
                tens[rot] = dict(U=float(un), V=float(v_f), E_max=float(emax), E_rel=float(emax / e0), V_rel=float(v_f / vc),
                                 P_fase=float(p_f), P_trif=float(3 * p_f), ok_P=3 * p_f <= e["lim_perda"] + 1e-9, corona=bool(v_f > vc))
            cond[nome_c] = dict(mt=mt, Uc=float(uc), Vc=float(vc), E0=float(e0), rp=float(rp), tens=tens)
        # curva perdas × tensão (80 % a 120 % de Un)
        curva = []
        for i in range(0, 41):
            u = c["un_kv"] * (0.8 + 0.01 * i)
            v_f = u / math.sqrt(3.0)
            curva.append(dict(U=float(u), **{nm: float(3 * perda_peek(v_f, cond[nm]["Vc"], delta, f_hz, cond[nm]["rp"], D)) for nm in cond}))
        out_c[k] = dict(n=n, d_mm=c["d_mm"], s_mm=c["s_mm"], r_cm=r_cm, D=float(D), un=float(c["un_kv"]), umax=float(c["umax_kv"]),
                        cond=cond, curva=curva, gradientes=[dict(g, E_un=float(g["E"] * fk)) for g in gk])
    if not out_c:
        return dict(erros=["Nenhum circuito existente/energizado para o cálculo."], avisos=[])
    gmax = max(g["E"] for g in gr)
    if gmax > 17.0:
        avisos.append(f"Gradiente máximo {gmax:.1f} kV/cm acima da referência prática de ~17 kV_ef/cm (Kiessling 2.3.3.1).")
    if e["g0"] > 21.2:
        avisos.append("g0 = 21,6 kV/cm (Livro 3): resultado menos conservador que g0 = 21,1 kV/cm.")
    return dict(erros=erros, avisos=avisos, delta=float(delta), circuitos=out_c, gradientes=gr, h_min=e.get("h_min"), alt=e["alt"], temp=e["temp"],
                freq=f_hz, mc=e["mc"], m_sup=e["m_sup"], g0=e["g0"], mt_chuva=e["mt_chuva"], lim_perda=e["lim_perda"],
                incluir_guardas=e["incluir_guardas"], fases=e["fases"], guardas=e["guardas"], circs=e["circs"])
