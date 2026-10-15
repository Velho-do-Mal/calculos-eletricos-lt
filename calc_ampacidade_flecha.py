"""
Módulo 13 – Ampacidade e flecha máxima – funções puras (sem Streamlit).

Metodologia:
  • Mudança de estado do condutor pela equação da parábola (a mesma da planilha BK 'CALCULO MECANICO DEL CONDUCTOR', 'Método da parábola'):
        σ2²·[ σ2 + E·γ1²·a²/(24·σ1²) − σ1 + E·α·(θ2 − θ1) ] = E·γ2²·a²/24
    σ = tensão específica (N/mm² = MPa), γ = peso específico (N/m/mm²), a = vão regulador (m), E = módulo de elasticidade final (MPa),
    α = coeficiente de dilatação linear (1/°C). Sem vento (peso próprio). Estado inicial = EDS (% da carga de ruptura a θ_EDS).
  • Flecha: parábola f = γ·a²/(8σ) e catenária f = (H/w)·[cosh(w·a/(2H)) − 1], com H = σ·S, w = massa·g.
  • Temperatura do condutor em função da corrente: IEEE Std 738-2006 (calc_condutor.ampacidade_ieee738 / temperatura_equilibrio).
  • Ampacidade limitada pela flecha: corrente em regime permanente que leva o condutor à temperatura em que a distância ao solo atinge o mínimo.
Premissas: vão nivelado e único (vão regulador); módulo de elasticidade final do catálogo (sem fluência separada); sem vento/gelo na flecha;
distância ao solo = altura de fixação do condutor mais baixo − flecha (terreno plano).
NBR 5422/2024 (distâncias de segurança) não consta no acervo: a distância mínima ao solo é dado de entrada – NECESSITA VALIDAÇÃO.
"""
import math

import calc_condutor as cd

G_GRAV = 9.80665


def estado(sig1, th1, th2, gam1, gam2, a, E, alfa):
    """Tensão específica σ2 (MPa) no estado 2 (θ2, γ2) a partir do estado 1 (σ1, θ1, γ1). Bisseção na equação cúbica."""
    k = E * gam2 ** 2 * a ** 2 / 24.0
    A = E * gam1 ** 2 * a ** 2 / (24.0 * sig1 ** 2) - sig1 + E * alfa * (th2 - th1)
    f = lambda s: s * s * (s + A) - k
    lo, hi = 1e-3, max(sig1 * 10.0, 1.0)
    while f(hi) < 0:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return 0.5 * (lo + hi)


def flecha_parabola(gam, a, sig):
    return gam * a ** 2 / (8.0 * sig)


def flecha_catenaria(gam, a, sig, secao):
    H = sig * secao                         # N
    w = gam * secao                         # N/m
    return H / w * (math.cosh(w * a / (2.0 * H)) - 1.0)


def calcular(e, cabo):
    """e: a (m), eds_pct (% RTC), th_eds, t_min, t_amb, t_max, t_emerg, ta (ambiente p/ corrente), vento, rad, emis, absor, alt_m,
    h_fix (m), d_min (m), corrente (A), n_sub, lim_tmin_pct, temps_extra (lista)."""
    erros, avisos = [], []
    S, d, m = cabo.get("secao_mm2"), cabo.get("diametro_mm"), cabo.get("massa_kg_m")
    rtc, E_gpa, dil, r20 = cabo.get("rtc_kn"), cabo.get("modulo_gpa"), cabo.get("dilatacao_1e6"), cabo.get("r_cc_20")
    faltam = [n for n, v in (("seção", S), ("diâmetro", d), ("massa linear", m), ("carga de ruptura", rtc), ("módulo de elasticidade", E_gpa),
                              ("coef. de dilatação", dil), ("resistência CC a 20 °C", r20)) if not v]
    if faltam:
        return dict(erros=["Cabo sem " + ", ".join(faltam) + " no catálogo (DADO NÃO INFORMADO)."], avisos=[])
    a = float(e["a"])
    if a <= 0:
        return dict(erros=["Informe o vão regulador."], avisos=[])
    alfa = dil * 1e-6
    E = E_gpa * 1000.0                      # MPa
    gam = m * G_GRAV / S                    # N/m/mm²
    sig_eds = e["eds_pct"] / 100.0 * rtc * 1000.0 / S         # MPa
    al = cabo.get("alfa_20c") or 0.004

    def ponto(th):
        sg = estado(sig_eds, e["th_eds"], th, gam, gam, a, E, alfa)
        return dict(th=float(th), sig=float(sg), T_kn=float(sg * S / 1000.0), T_rtc=float(sg * S / 1000.0 / rtc * 100.0),
                    f_par=float(flecha_parabola(gam, a, sg)), f_cat=float(flecha_catenaria(gam, a, sg, S)))

    def ampac(th):
        r = cd.ampacidade_ieee738(d, cd.r_temp(r20, al, th), e["ta"], th, e.get("alt_m", 0.0), e["emis"], e["absor"], e["vento"], 90.0, e["rad"])
        return float(r["i"] * 1.0)

    ths = sorted({round(float(x), 1) for x in [e["t_min"], e["th_eds"], e["t_amb"], 45.0, 60.0, e["t_max"], e["t_emerg"]] + list(e.get("temps_extra", []))
                  if x > e["ta"] or x <= e["ta"]})
    linhas = []
    for th in ths:
        p = ponto(th)
        p["clear"] = float(e["h_fix"] - p["f_cat"])
        p["ok_clear"] = p["clear"] >= e["d_min"] - 1e-9
        p["I"] = ampac(th) * e.get("n_sub", 1) if th > e["ta"] else None
        linhas.append(p)
    # curva fina
    curva = []
    th = e["t_min"]
    while th <= max(e["t_emerg"], e["t_max"]) + 1e-9:
        p = ponto(th)
        curva.append(dict(th=float(th), f=p["f_cat"], clear=float(e["h_fix"] - p["f_cat"])))
        th += 5.0
    # temperatura que esgota a distância ao solo
    th_lim = None
    f_ok = lambda t: e["h_fix"] - ponto(t)["f_cat"] - e["d_min"]
    if f_ok(e["t_max"]) < 0:
        lo, hi = e["th_eds"], e["t_max"]
        if f_ok(lo) < 0:
            avisos.append("A distância mínima ao solo não é atendida nem na temperatura EDS: revise altura de fixação, vão ou EDS.")
            th_lim = lo
        else:
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                lo, hi = (mid, hi) if f_ok(mid) >= 0 else (lo, mid)
            th_lim = 0.5 * (lo + hi)
    else:
        lo, hi = e["t_max"], 400.0
        if f_ok(hi) >= 0:
            th_lim = None
        else:
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                lo, hi = (mid, hi) if f_ok(mid) >= 0 else (lo, mid)
            th_lim = 0.5 * (lo + hi)
    i_ns = e.get("n_sub", 1)
    i_term = ampac(e["t_max"]) * i_ns
    i_flecha = ampac(th_lim) * i_ns if th_lim and th_lim > e["ta"] else None
    i_nom = e.get("corrente")
    t_nom = None
    if i_nom:
        t_nom = cd.temperatura_equilibrio(i_nom / i_ns, d, r20, al, e["ta"], e.get("alt_m", 0.0), e["emis"], e["absor"], e["vento"], e["rad"])
        if t_nom is None:
            avisos.append("A corrente informada excede a ampacidade IEEE 738 mesmo a 250 °C.")
    pm = ponto(e["t_max"])
    pmin = ponto(e["t_min"])
    if pmin["T_rtc"] > e["lim_tmin_pct"]:
        avisos.append(f"Tração a {e['t_min']:g} °C = {pmin['T_rtc']:.1f} % da RTC, acima do limite informado ({e['lim_tmin_pct']:g} %). "
                      "Verificar também a condição de vento máximo (Módulo 3/5).")
    if th_lim is not None and th_lim < e["t_max"]:
        avisos.append(f"Distância ao solo de {e['d_min']:g} m só é mantida até {th_lim:.1f} °C (< {e['t_max']:g} °C): "
                      "limitar a corrente ou aumentar a altura/reduzir o vão.")
    avisos.append("Flecha sem fluência separada (módulo final do catálogo) e sem vento. NBR 5422 não consta no acervo: distância mínima é dado de entrada.")
    return dict(erros=erros, avisos=avisos, linhas=linhas, curva=curva, th_lim=th_lim, i_term=float(i_term), i_flecha=i_flecha,
                t_nom=None if t_nom is None else float(t_nom), pmax=pm, pmin=pmin, sig_eds=float(sig_eds), gam=float(gam),
                S=S, d=d, m=m, rtc=rtc, E_gpa=E_gpa, dil=dil, e=e)
