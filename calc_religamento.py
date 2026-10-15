"""
Módulo 15 – Religamento tripolar (pré-dimensionamento analítico) – funções puras (sem Streamlit).

AVISO: as Diretrizes de Projeto Básico (3.2.5, 3.2.6, 3.2.7 e 8.4) exigem estudo estatístico de transitórios eletromagnéticos (EMT/ATP, ≥ 200 manobras,
modelo de Bergeron, resistor de pré-inserção em Ω e tempo de inserção em ms; sequência: falta monofásica, abertura tripolar, +20 ms de teleproteção,
~4 ciclos de extinção, tempo morto de 500 ms; simulação total ≈ 800 ms; ONS Procedimentos de Rede, submódulo 23.3). Este módulo é TRIAGEM e NÃO o substitui.

Modelo da sobretensão de energização com carga residual (um estágio LC, linha em π com C/2 no terminal receptor aberto):
    L = Ls + L_linha ;  R = Rs + R_linha + R_pré ;  C = C_linha/2 ;  ζ = (R/2)·√(C/L) ;  κ = exp(−πζ/√(1−ζ²)) (ζ < 1; κ = 0 se ζ ≥ 1)
    pico = E + (E − V0)·κ, com V0 = −Vres·E (polaridade oposta: pior caso).
  Com resistor de pré-inserção: 1º estágio com R_pré durante t_ins; tensão no instante do curto-circuito do resistor V_b = E + (V0 − E)·e^(−t_ins/(R·C))
  (superamortecido) e 2º estágio com R sem o resistor: pico2 = E + (E − V_b)·κ2. Sobretensão = máx(pico1, pico2), em p.u. de √2·Um/√3.
Verificações adicionais:
  • Tempo morto × tempo de deionização do arco: t_d[ciclos] = 10,5 + U[kV]/34,5 (fórmula clássica) – NECESSITA VALIDAÇÃO (não consta no acervo).
  • Ângulo através do disjuntor (sincronismo) ≈ asin(P·X_total/Um²), X_total = Xs + X_linha + X_remoto, assumindo que os sistemas permanecem em sincronismo
    (estabilidade durante o tempo morto exige estudo dedicado).
Limitações: parâmetros de sequência positiva (polos fechados juntos), sem dispersão entre polos, sem frequências de reflexão (Bergeron), sem saturação de reator/TP.
"""
import math


def pico_sobretensao(L, R_serie, C, v_res, r_pre=0.0, t_ins_s=0.008):
    """Sobretensão máxima (p.u. de E) na energização com tensão residual v_res (p.u., sinal oposto)."""
    def kappa(R):
        z = R / 2.0 * math.sqrt(C / L)
        return math.exp(-math.pi * z / math.sqrt(1.0 - z * z)) if z < 1.0 else 0.0, z
    v0 = -abs(v_res)
    k1, z1 = kappa(R_serie + r_pre)
    pico1 = 1.0 + (1.0 - v0) * k1
    if r_pre <= 0:
        return pico1, dict(zeta=z1, kappa=k1, pico1=pico1, pico2=None, v_b=None)
    # resistor inserido: tensão no instante de bypass
    tau = max((R_serie + r_pre) * C, 1e-9)
    if z1 >= 1.0:
        v_b = 1.0 + (v0 - 1.0) * math.exp(-t_ins_s / tau)
    else:
        v_b = pico1                                                    # subamortecido: bypass no pior instante (conservador)
    k2, z2 = kappa(R_serie)
    pico2 = 1.0 + (1.0 - v_b) * k2
    return max(pico1, pico2), dict(zeta=z1, kappa=k1, pico1=pico1, pico2=pico2, v_b=v_b, zeta2=z2)


def calcular(e):
    """e: z1 [r, x] (Ω/km), c1 (F/km), comp_km, un_kv, umax_kv, f, scc_mva, xr, scc_rem_mva, p_mw, t_morto_ms, ang_max, v_res_pu,
    r_pre (Ω), t_ins_ms, lim_pu, tipo_falta, nome_circ."""
    erros, avisos = [], []
    if not e.get("z1") or not e.get("c1"):
        return dict(erros=["Parâmetros de sequência positiva indisponíveis (Módulo 2: selecione condutor, cabos guarda e geometria)."], avisos=[])
    if not e.get("comp_km"):
        return dict(erros=["Informe o comprimento da LT (Módulo 1)."], avisos=[])
    w = 2 * math.pi * e["f"]
    l = e["comp_km"]
    R_l, L_l, C_l = e["z1"][0] * l, e["z1"][1] / w * l, e["c1"] * l
    Xs = e["un_kv"] ** 2 / e["scc_mva"]
    Rs = Xs / e["xr"]
    Ls = Xs / w
    Xl = e["z1"][1] * l
    Xr = e["un_kv"] ** 2 / e["scc_rem_mva"]
    L, Rser, C = Ls + L_l, Rs + R_l, C_l / 2.0
    f0 = 1.0 / (2 * math.pi * math.sqrt(L * C))
    pico, det = pico_sobretensao(L, Rser, C, e["v_res_pu"], e["r_pre"], e["t_ins_ms"] / 1000.0)
    sem, det0 = pico_sobretensao(L, Rser, C, e["v_res_pu"], 0.0, e["t_ins_ms"] / 1000.0)
    # E em p.u. de √2·Um/√3 = Un/Um (tensão de operação) -> pico em p.u. da base de manobra
    esc = e["un_kv"] / e["umax_kv"]
    pico_pu, sem_pu = pico * esc, sem * esc
    # resistor mínimo
    r_min = None
    if sem_pu <= e["lim_pu"]:
        r_min = 0.0
    else:
        lo, hi = 0.0, 5000.0
        if pico_sobretensao(L, Rser, C, e["v_res_pu"], hi, e["t_ins_ms"] / 1000.0)[0] * esc > e["lim_pu"]:
            r_min = float("inf")
        else:
            for _ in range(50):
                mid = 0.5 * (lo + hi)
                lo, hi = (mid, hi) if pico_sobretensao(L, Rser, C, e["v_res_pu"], mid, e["t_ins_ms"] / 1000.0)[0] * esc > e["lim_pu"] else (lo, mid)
            r_min = 0.5 * (lo + hi)
    c_res = [dict(x=float(100 * i / 20), pu=float(pico_sobretensao(L, Rser, C, i / 20, e["r_pre"], e["t_ins_ms"] / 1000.0)[0] * esc)) for i in range(0, 21)]
    c_rpre = [dict(x=float(r), pu=float(pico_sobretensao(L, Rser, C, e["v_res_pu"], r, e["t_ins_ms"] / 1000.0)[0] * esc)) for r in range(0, 1001, 50)]
    # deionização
    t_deion = (10.5 + e["umax_kv"] / 34.5) / e["f"] * 1000.0 if e["tipo_falta"] != "Sem arco (permanente)" else 0.0
    ok_td = e["t_morto_ms"] >= t_deion
    # ângulo
    xt = Xs + Xl + Xr
    arg = e["p_mw"] * xt / e["un_kv"] ** 2
    ang = math.degrees(math.asin(min(arg, 1.0))) if arg <= 1.0 else None
    ok_ang = ang is not None and ang <= e["ang_max"]
    if ang is None:
        avisos.append("Transferência acima do limite de potência estático (P·X > U²): sincronismo inviável nesta triagem.")
    if e["comp_km"] > 200:
        avisos.append("Linha > 200 km: modelo de um estágio LC é pobre; usar o estudo EMT (Bergeron).")
    if not ok_td:
        avisos.append(f"Tempo morto ({e['t_morto_ms']:g} ms) < tempo de deionização estimado ({t_deion:.0f} ms): risco de religamento mal-sucedido.")
    avisos.append("TRIAGEM ANALÍTICA: não substitui o estudo estatístico EMT/ATP (≥ 200 manobras, Bergeron) das Diretrizes 3.2.5/3.2.6/3.2.7/8.4.")
    return dict(erros=erros, avisos=avisos, pico_pu=float(pico_pu), sem_resistor_pu=float(sem_pu), ok_sobt=bool(pico_pu <= e["lim_pu"] + 1e-9), det=det,
                r_min=r_min, f0_hz=float(f0), L_mH=float(L * 1e3), C_uF=float(C * 1e6), Rser=float(Rser), c_res=c_res, c_rpre=c_rpre,
                t_deion_ms=float(t_deion), ok_td=bool(ok_td), ang=None if ang is None else float(ang), ok_ang=bool(ok_ang), x_total=float(xt),
                Xs=float(Xs), Xl=float(Xl), Xr=float(Xr), e=e)
