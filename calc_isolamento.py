"""
Módulo 5 – Coordenação de isolamento: isoladores, distâncias no ar, sobretensões e para-raios.

Base normativa (lida nos exemplares do acervo do projeto):
  ABNT NBR 5422:2024  4.5 (densidade relativa do ar), 4.6 (umidade absoluta), 4.8 (fatores de correção atmosférica),
                      7.3-7.5, 8.9 (balanço), Seção 9 (isolamento), 14.2 (cargas mecânicas), Anexo C (kg, Kcs)
  Diretrizes para Projetos Básicos (ONS/EPE) 3.2.13, 4.7, 6.8
  Projeto Elétrico de LTs (livro 2) 4.6 e 4.7 (método convencional, GI, distribuição de tensão na cadeia)

Unidades: m, kV (valor eficaz fase-fase para Um/Un, crista onde indicado), graus, mm, kN.
Funções puras (sem Streamlit).  Nada é inventado: o que não tem fonte lida vira PENDENTE / NECESSITA VALIDAÇÃO TÉCNICA.
"""
import math

import calc_faixa as cf

SQ2, SQ3 = math.sqrt(2.0), math.sqrt(3.0)
V_LUZ = 299.792458          # m/µs

# --------------------------------------------------------------------------- tabelas normativas
# Tabela 14 (9.4.3.1) – Fsfl mínimo sem estudo: (limite superior de Us em kV, Fsfl) em relação a √2/√3·Us
TAB14 = [(362.0, 3.00), (550.0, 2.40), (800.0, 2.00), (1e9, 1.80)]
# Tabela 15 (9.5) – Ufr (kV de crista) sem dados específicos, por tensão nominal (kV)
TAB15 = [(69.0, 500.0), (138.0, 820.0), (230.0, 1070.0), (345.0, 1605.0), (440.0, 1870.0), (500.0, 2015.0), (800.0, 2950.0)]
# Tabela C.1 – kg fase-terra (frente lenta)
TAB_C1 = {
    "Braço de torre": 1.45, "Janela": 1.25, "Plano abaixo": 1.15, "Haste abaixo": 1.47,
    "Estrutura lateral": 1.45, "Haste–haste": 1.35, "Estai": 1.40,
}
# Tabela C.3 – kg fase-fase (frente lenta): geometria -> (α = 0,5 ; α = 0,33)
TAB_C3 = {
    "Anel–anel": (1.80, 1.70), "Condutores cruzados": (1.65, 1.53),
    "Haste–haste ou condutor–condutor (ao longo do vão)": (1.62, 1.52),
    "Barramentos sobre isoladores": (1.50, 1.40), "Geometrias assimétricas": (1.45, 1.36),
}
# Distância de fuga específica mínima (mm por kV fase-fase, Um)
FUGA_IEC60815_1986 = {"I – Leve": 16.0, "II – Médio": 20.0, "III – Pesado": 25.0, "IV – Muito pesado": 31.0}   # Celesc E-313.0058 §5.2.1
FUGA_TS60815_2008 = {"a – Muito leve": 22.0, "b – Leve": 27.8, "c – Médio": 34.7, "d – Pesado": 43.3, "e – Muito pesado": 53.7}  # NÃO verificado
FUGA_EDITAL = 14.0                                    # Diretrizes 6.8.2 / edital TAESA (mín. se poluição abaixo de "leve")
ZFR, ZFF, ZFL = 0.03, 0.03, 0.06                      # desvios-padrão relativos (9.3.2, 9.4.1, 9.5)


def _interp_tab(tab, x):
    for lim, v in tab:
        if x <= lim + 1e-9:
            return v
    return tab[-1][1]


def fsfl_minimo(us_kv):
    return _interp_tab(TAB14, us_kv)


def ufr_tabela(un_kv):
    return _interp_tab(TAB15, un_kv)


# --------------------------------------------------------------------------- 4.5 / 4.6 / 4.8 atmosfera
def delta_sem_medicao(alt, lat, lon):
    """4.5.3 – densidade relativa do ar média e desvio-padrão (lat/lon em valor absoluto, graus)."""
    la, lo = abs(lat), abs(lon)
    d = 0.984 - 0.836e-4 * alt + 0.141e-5 * la * alt - 0.788e-6 * lo * alt
    s = 0.977e-2 + 0.256e-5 * alt - 0.205e-3 * la + 0.213e-4 * la * alt
    return d, s


def delta_medido(p_hpa, t_c):
    """4.5.1 – δ = (p/p0)·(273+t0)/(273+t); p0 = 1013 hPa, t0 = 20 °C."""
    return (p_hpa / 1013.0) * (293.0 / (273.0 + t_c))


def umidade_absoluta(t_c, ur_pct):
    """4.6.1 – H (g/m³) a partir de t (°C) e UR (%)."""
    return 6.11 * ur_pct * math.exp(17.6 * t_c / (243.0 + t_c)) / (0.4615 * (273.0 + t_c))


def umidade_sem_medicao(alt, lat):
    """4.6.3 – H média (g/m³)."""
    la = abs(lat)
    return 21.559 - 0.00509 * alt - 0.228 * la - 3.85e-5 * la * alt


def hc_corrigida(h, delta):
    """4.8 – fator de umidade para CA: Hc = 1 + 0,012·(H/δ − 11)."""
    return 1.0 + 0.012 * (h / delta - 11.0)


def g0(d):
    """4.8 – gradiente de referência G0 (função da distância no ar d, m)."""
    if d <= 3.5:
        return 1080.0 / (500.0 * d) * math.log(0.46 * d + 1.0)
    return 3400.0 / (500.0 * d + 4000.0)


def m2_de_d(d):
    g = g0(d)
    return 1.25 * g * (g - 0.2)


def k_ff(delta):
    """kaff = δ^m1, m1 = 1,0 (4.8)."""
    return delta


def k_fl(delta, hc, d, chuva=False):
    """kafl = δ^m2·Hc^m2 (seco) ou δ^m2 (chuva); m2 depende da distância d (iterativo)."""
    m2 = m2_de_d(max(d, 0.05))
    return delta ** m2 if chuva else (delta * hc) ** m2


def k_fr(delta):
    """kafr = δ^m3, m3 = 1,0 (4.8)."""
    return delta


# --------------------------------------------------------------------------- Anexo C.3  Kcs estatístico
def _phi(x):
    return 0.5 * (1.0 + math.erf(x / SQ2))


def risco_gaps(u50, cv_s, cv_f, n, passos=1200):
    """Risco de falha em n gaps em paralelo. Sobretensão normal (média 1,0; σ = CVs), resistência normal (U50; σ = CVf·U50)."""
    lo, hi = 1.0 - 6 * cv_s, 1.0 + 6 * cv_s
    h = (hi - lo) / passos
    r = 0.0
    for i in range(passos + 1):
        v = lo + i * h
        w = 0.5 if i in (0, passos) else 1.0
        f = math.exp(-0.5 * ((v - 1.0) / cv_s) ** 2) / (cv_s * math.sqrt(2 * math.pi))
        pf = _phi((v - u50) / (cv_f * u50))
        r += w * f * (1.0 - (1.0 - pf) ** n)
    return r * h


def kcs_estatistico(cv_s, cv_f, n, risco):
    """Kcs = U90 / V2 (Anexo C.3).  V2 = 1 + 2,054·CVs (sobretensão de 2 % de excedência); U90 = U50·(1 − 1,2816·CVf).
    U50 é obtido por bissecção para o risco `risco`. (Modelo gaussiano reconstituído – conferir com a Figura C.1.)"""
    a, b = 0.8, 3.0
    for _ in range(80):
        m = 0.5 * (a + b)
        if risco_gaps(m, cv_s, cv_f, n) > risco:
            a = m
        else:
            b = m
    u50 = 0.5 * (a + b)
    return u50 * (1.0 - 1.2816 * cv_f) / (1.0 + 2.054 * cv_s), u50


# --------------------------------------------------------------------------- Seção 9 – distâncias no ar
def kg_ff(kg):
    return 1.35 * kg - 0.35 * kg ** 2


def d_ft_ff(us_kv, delta, kg, ftmo=1.0):
    """9.3.2 – fase-terra, frequência fundamental (m)."""
    kz = 1.0 - 3.0 * ZFF
    x = (us_kv / SQ3 * ftmo) / (750.0 * k_ff(delta) * kz * kg_ff(kg))
    return 1.642 * (math.exp(x) - 1.0) ** 0.83


def d_ff_ff(us_kv, delta, kg_pp, ftmo=1.0):
    """9.3.3 – fase-fase, frequência fundamental (m); kg_pp da Tabela C.3."""
    kz = 1.0 - 3.0 * ZFF
    x = (us_kv * ftmo) / (750.0 * k_ff(delta) * kz * kg_ff(kg_pp))
    return 1.642 * (math.exp(x) - 1.0) ** 0.83


def _iter_d(fun, d0=1.0):
    d = d0
    for _ in range(60):
        dn = fun(d)
        if abs(dn - d) < 1e-6:
            return dn
        d = 0.5 * (d + dn)
    return d


def d_ft_fl(us_kv, kcs, fsfl, kg, delta, hc, chuva=False):
    """9.4.1 – fase-terra, frente lenta (m); kafl depende de d (iteração). Retorna (d, kafl)."""
    def f(d):
        return cf.d_ft_fl(us_kv, kcs, fsfl, kg, k_fl(delta, hc, d, chuva))
    d = _iter_d(f)
    return d, k_fl(delta, hc, d, chuva)


def d_ff_fl(us_kv, kcs, fsfl, rs, kg_pp, alfa, delta, hc, chuva=False):
    """9.4.2 – fase-fase, frente lenta (m). 1 < d ≤ 4 m: forma de 9.4.1 com rs·Fsfl; 4 < d < 10 m: expressão de U50 %.
    Retorna (d, kafl, faixa)."""
    def f(d):
        return cf.d_ft_fl(us_kv, kcs, fsfl * rs, kg_pp, k_fl(delta, hc, d, chuva))
    d = _iter_d(f)
    kafl = k_fl(delta, hc, d, chuva)
    if d <= 4.0:
        return d, kafl, "1 < d ≤ 4 m"
    kz = 1.0 - 1.3 * ZFL

    def g(d_):
        ka = k_fl(delta, hc, d_, chuva)
        u50 = kcs * SQ2 / SQ3 * us_kv * rs * fsfl / (ka * kz)
        rad = 54.3115 * alfa ** 2 + 212.6589 * alfa - 0.1019 * u50 + 286.0043
        return 15.3726 + 7.0846 * alfa - math.sqrt(max(rad, 0.0))
    d2 = _iter_d(g, 5.0)
    return d2, k_fl(delta, hc, d2, chuva), ("4 < d < 10 m" if d2 < 10.0 else "d ≥ 10 m (fora do campo de validade)")


def kg_fr_pos(kg):
    return 0.74 + 0.26 * kg


def kg_fr_neg(kg):
    return 1.5 - 0.5 * kg if kg <= 1.44 else 0.78


def d_ft_fr(ufr_kv, delta, kg):
    """9.5 – fase-terra, frente rápida: maior entre polaridade positiva e negativa. Retorna (d, d_pos, d_neg)."""
    kz = 1.0 - 1.3 * ZFR
    dp = ufr_kv / (530.0 * k_fr(delta) * kz * kg_fr_pos(kg))
    dn = ufr_kv / (700.0 * k_fr(delta) * kz * kg_fr_neg(kg))
    return max(dp, dn), dp, dn


def d_ff_fr(ufr_kv, delta, kg_pp):
    """9.5 – fase-fase, frente rápida (m)."""
    kz = 1.0 - 1.3 * ZFR
    return 1.2 * ufr_kv / (530.0 * k_fr(delta) * kz * kg_fr_pos(kg_pp))


# --------------------------------------------------------------------------- isoladores
def n_isol_fuga(um_kv, fuga_esp, fuga_unid_mm):
    """9.3.1 – nº mínimo de isoladores pela fuga específica (mm/kV fase-fase sobre Um)."""
    return math.ceil(round(fuga_esp * um_kv / fuga_unid_mm, 9))


def n_isol_convencional(un_kv, ancoragem=False):
    """Livro 'Projeto Elétrico de LTs', 4.6.1 (até 230 kV): N = Vn/15 (+1 em ancoragem)."""
    return math.ceil(round(un_kv / 15.0, 9)) + (1 if ancoragem else 0)


def gradiente_isolador(fuga_total_mm, vmax_fase_neutro_kv):
    """Livro 4.7 – GI = d·N/Vmax em cm/kV (d·N = fuga total da cadeia; Vmax fase-terra)."""
    return fuga_total_mm / 10.0 / vmax_fase_neutro_kv


def distribuicao_cadeia(n, c1_c, v_total_kv):
    """Escada capacitiva (capacitância shunt à terra c1 por junção / capacitância própria C): tensão em cada unidade
    (da fase para a terra). cosh α = 1 + c1/(2C); V(k)=V·sinh(kα)/sinh(nα), k contado a partir da terra."""
    if n < 1:
        return []
    if c1_c <= 0:
        return [v_total_kv / n] * n
    a = math.acosh(1.0 + c1_c / 2.0)
    vk = [v_total_kv * math.sinh(k * a) / math.sinh(n * a) for k in range(n + 1)]
    return [vk[k] - vk[k - 1] for k in range(n, 0, -1)]        # unidade 1 = lado da linha (a mais solicitada)


def mecanico(rbl_kn, n_cad, carga_sv_kn, carga_cv_kn):
    """14.2.2/14.2.3/14.2.4 – utilização da cadeia: sem vento ≤ 40 % da RBL; com vento/construção/manutenção ≤ 60 %."""
    cap = rbl_kn * max(n_cad, 1)
    u1, u2 = carga_sv_kn / cap * 100.0, carga_cv_kn / cap * 100.0
    return dict(u_sv=u1, u_cv=u2, ok_sv=u1 <= 40.0, ok_cv=u2 <= 60.0, cap=cap)


# --------------------------------------------------------------------------- geometria de balanço
def _d_pt_seg(p, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def silhueta(fases, xf, h_corpo):
    """Segmentos da estrutura: fuste vertical em x = ±xf e braços (do fuste ao ponto de fixação de cada fase)."""
    ytop = max(y for _, y in fases) + 2.0
    ybot = min(y for _, y in fases) - h_corpo
    segs = [((xf, ybot), (xf, ytop)), ((-xf, ybot), (-xf, ytop))]
    for x, y in fases:
        s = 1.0 if x >= 0 else -1.0
        segs.append(((s * xf, y), (x, y)))
    return segs


def pos_cadeia(x, y, comp, beta_deg, sentido, tipo="Suspensão em I"):
    """Posição do condutor na extremidade da cadeia deslocada de β (sentido = +1/−1 para o vento)."""
    if tipo != "Suspensão em I":
        return (x, y - comp)                         # V / ancoragem: a cadeia não balança
    b = math.radians(beta_deg) * sentido
    return (x + comp * math.sin(b), y - comp * math.cos(b))


def d_cond_estrutura(fases, i, comp, beta, segs, tipo):
    """Menor distância (m) do condutor da fase i à estrutura, nos dois sentidos de vento. Retorna (d_min, sentido)."""
    x, y = fases[i]
    best = (1e9, 0)
    for s in (1, -1):
        p = pos_cadeia(x, y, comp, beta, s, tipo)
        d = min(_d_pt_seg(p, a, b) for a, b in segs)
        if d < best[0]:
            best = (d, s)
    return best


def d_fase_fase(fases, comp, b_i, b_j, tipo, flecha=0.0):
    """Menor distância entre as fases i e j com a fase i em b_i e a j em b_j, mesmo sentido (9.6.3). `comp` = cadeia (apoio)
    ou flecha (meio do vão, com tipo 'vão')."""
    out = {}
    n = len(fases)
    for i in range(n):
        for j in range(i + 1, n):
            best = 1e9
            for s in (1, -1):
                for bi, bj in ((b_i, b_j), (b_j, b_i)):
                    if tipo == "vão":
                        pi = (fases[i][0] + flecha * math.sin(math.radians(bi) * s), fases[i][1] - flecha * math.cos(math.radians(bi) * s))
                        pj = (fases[j][0] + flecha * math.sin(math.radians(bj) * s), fases[j][1] - flecha * math.cos(math.radians(bj) * s))
                    else:
                        pi = pos_cadeia(*fases[i], comp, bi, s, tipo)
                        pj = pos_cadeia(*fases[j], comp, bj, s, tipo)
                    best = min(best, math.hypot(pi[0] - pj[0], pi[1] - pj[1]))
            out[(i, j)] = best
    return out


# --------------------------------------------------------------------------- para-raios
UR_PASSO = 3.0


def para_raios(e):
    """Especificação preliminar de para-raios de ZnO de estação (Diretrizes 4.7; IEC 60099 – não consultada: NECESSITA VALIDAÇÃO)."""
    um = e["um_kv"]
    uc_min = um / SQ3
    ur1 = uc_min / e.get("uc_ur", 0.8)
    tov = e.get("ke", 1.4) * um / SQ3
    ur2 = tov / e.get("ktov", 1.10)
    ur_min = max(ur1, ur2)
    ur_pad = math.ceil(round(ur_min / UR_PASSO, 9)) * UR_PASSO
    r = dict(uc_min=uc_min, ur_mcov=ur1, tov=tov, ur_tov=ur2, ur_min=ur_min, ur_pad=ur_pad, avisos=[])
    ur = e.get("ur_cat") or ur_pad
    r["ur_adot"] = ur
    if e.get("ur_estudo") and ur > e["ur_estudo"] + 1e-9:
        r["avisos"].append(f"Ur adotado ({ur:g} kV) acima do Ur do estudo ({e['ur_estudo']:g} kV): Diretrizes 4.7 vedam.")
    mg = e.get("margem_equip", 15.0) / 100.0
    r["mp_fr"] = r["mp_fl"] = None
    if e.get("ures_fr") and e.get("bil"):
        r["mp_fr"] = e["bil"] / e["ures_fr"] - 1.0
        r["ok_fr"] = r["mp_fr"] >= mg
    if e.get("ures_fl") and e.get("sil"):
        r["mp_fl"] = e["sil"] / e["ures_fl"] - 1.0
        r["ok_fl"] = r["mp_fl"] >= mg
    r["margem_exigida"] = mg
    if e.get("usurto") and e.get("ures_fl") and e.get("zc") and e.get("km"):
        t_s = e["km"] * 1000.0 / 2.998e8                        # tempo de percurso da onda no comprimento de linha (s)
        # IEC 60099-5: W = 2·Ures·(Usurto − Ures)/Zc·T, tensões em V → energia em J
        w = 2.0 * e["ures_fl"] * 1e3 * (e["usurto"] - e["ures_fl"]) * 1e3 / e["zc"] * t_s
        r["w_kj"] = w / 1e3                                   # kJ
        r["w_kj_kv"] = r["w_kj"] / ur
        if e.get("e_cat"):
            r["ok_e"] = e["e_cat"] >= r["w_kj_kv"]
    return r


# --------------------------------------------------------------------------- cabo para-raios (planilha BK, aba "EDS Para-raios")
def eds_para_raios(w_pr, w_cond, t_cond, rel_flechas, rbl_pr):
    """T_pr = Wpr·T_cond/(relação_flechas·Wcond); retorna (T_pr [N], % da RBL)."""
    t = w_pr * t_cond / (rel_flechas * w_cond)
    return t, t / rbl_pr * 100.0


# --------------------------------------------------------------------------- cálculo completo
def calcular(e):
    """e: dict de entrada (ver app.entrada_m5). Retorna dict com blocos 'atm', 'kcs', 'dist', 'isol', 'balanco', 'pr', 'avisos', 'erros'."""
    erros, avisos, pend = [], [], []
    r = dict(erros=erros, avisos=avisos, pendencias=pend)
    um, un = e.get("um_kv") or 0.0, e.get("un_kv") or 0.0
    if um <= 0:
        erros.append("Informe a tensão máxima do sistema (Módulo 1).")
        return r
    # ---- atmosfera
    if e["modo_delta"] == "Sem medições (NBR 5422, 4.5.3)":
        delta, sd = delta_sem_medicao(e["alt"], e["lat"], e["lon"])
    else:
        delta, sd = delta_medido(e["p_hpa"], e["t_c"]), None
    if e.get("ur_pct") and e.get("t_c") is not None and e["modo_delta"] != "Sem medições (NBR 5422, 4.5.3)":
        h = umidade_absoluta(e["t_c"], e["ur_pct"])
    else:
        h = umidade_sem_medicao(e["alt"], e["lat"])
    hc = hc_corrigida(h, delta)
    r["atm"] = dict(delta=delta, sigma_delta=sd, H=h, Hc=hc)
    # ---- Kcs
    if e.get("kcs_man"):
        kcs, u50n = e["kcs_man"], None
    else:
        kcs, u50n = kcs_estatistico(e["cv_sfl"], e["cv_fl"], max(int(e["n_gaps"]), 1), e["risco"])
    r["kcs"] = dict(kcs=kcs, u50=u50n)
    kg = e["kg_ft"]
    kgpp = e["kg_ff"]
    fsfl = e["fsfl"]
    # ---- distâncias requeridas
    dist = {}
    dist["ft_ff"] = d_ft_ff(um, delta, kg, e.get("ftmo", 1.0))
    dist["ff_ff"] = d_ff_ff(um, delta, kgpp, e.get("ftmo", 1.0))
    # frente lenta: usa o caso mais conservador (chuva = kafl menor) como adotado
    d_seco, k_seco = d_ft_fl(um, kcs, fsfl, kg, delta, hc, False)
    d_chuv, k_chuv = d_ft_fl(um, kcs, fsfl, kg, delta, hc, True)
    dist["ft_fl_seco"], dist["ft_fl_chuva"] = d_seco, d_chuv
    dist["ft_fl"], dist["kafl"] = (d_chuv, k_chuv) if d_chuv >= d_seco else (d_seco, k_seco)
    dpp_s, _, _ = d_ff_fl(um, kcs, fsfl, e["rs"], kgpp, e["alfa"], delta, hc, False)
    dpp_c, kpp, faixa_pp = d_ff_fl(um, kcs, fsfl, e["rs"], kgpp, e["alfa"], delta, hc, True)
    dist["ff_fl"], dist["faixa_ff_fl"] = max(dpp_s, dpp_c), faixa_pp
    ufr = e.get("ufr") or ufr_tabela(un)
    dist["ufr"] = ufr
    dist["ft_fr"], dist["ft_fr_pos"], dist["ft_fr_neg"] = d_ft_fr(ufr, delta, kg)
    dist["ff_fr"] = d_ff_fr(ufr, delta, kgpp)
    dist["kaff"], dist["kafr"] = k_ff(delta), k_fr(delta)
    dist["trab"] = e.get("d_trab") or 0.0              # 7.5 – distância de trabalho em linha viva (IEEE 516/IEC 61472), informada
    dist["req_ft"] = max(dist["ft_ff"], dist["ft_fl"], dist["ft_fr"], dist["trab"])
    dist["req_ff"] = max(dist["ff_ff"], dist["ff_fl"], dist["ff_fr"])
    if dist["ft_fr"] > dist["ft_ff"] and not e.get("ufr"):
        pass
    if dist["ft_fr"] > dist["ft_ff"]:
        avisos.append("9.5.3.3: a distância de frente rápida supera a de frequência fundamental — exige estudo de desempenho a descargas atmosféricas (Módulo 16).")
    if dist["ft_fl"] > 25.0:
        avisos.append("NECESSITA VALIDAÇÃO TÉCNICA — d fase-terra de frente lenta acima de 25 m (fora do campo de 9.4.1).")
    r["dist"] = dist
    # ---- isoladores
    iso = {}
    ancor = e["tipo_cadeia"] == "Ancoragem"
    iso["n_conv"] = n_isol_convencional(un, ancor) if un <= 230 else None
    fuga = max(e["fuga_esp"], FUGA_EDITAL if e.get("aplicar_edital", True) else 0.0)
    iso["fuga_esp"], iso["fuga_nec_mm"] = fuga, fuga * um
    if e["tipo_isol"] == "Polimérico":
        iso["n"] = 1
        iso["l_arco"] = e["l_arco_mm"] / 1000.0
        iso["fuga_tot"] = e["fuga_unid_mm"]
        iso["ok_fuga"] = iso["fuga_tot"] >= iso["fuga_nec_mm"]
        iso["ok_arco"] = iso["l_arco"] >= dist["req_ft"]
        iso["n_fuga"] = iso["n_arco"] = None
    else:
        iso["n_fuga"] = n_isol_fuga(um, fuga, e["fuga_unid_mm"])
        iso["n_arco"] = math.ceil(round(dist["req_ft"] / (e["passo_mm"] / 1000.0), 9))
        iso["n"] = max(iso["n_fuga"], iso["n_arco"], e.get("n_min", 1))
        iso["l_arco"] = iso["n"] * e["passo_mm"] / 1000.0
        iso["fuga_tot"] = iso["n"] * e["fuga_unid_mm"]
        iso["ok_fuga"] = iso["fuga_tot"] >= iso["fuga_nec_mm"]
        iso["ok_arco"] = iso["l_arco"] >= dist["req_ft"]
        if iso["n_conv"] and iso["n"] < iso["n_conv"]:
            avisos.append(f"O método convencional (N = Vn/15) daria {iso['n_conv']} isoladores, mais que os {iso['n']} adotados — conferir a prática da transmissora.")
    iso["gi"] = gradiente_isolador(iso["fuga_tot"], um / SQ3)
    iso["comp"] = iso["l_arco"] + e.get("l_ferr", 0.0)
    iso["fuga_us_iec"] = {k: v for k, v in FUGA_IEC60815_1986.items()}
    if e["tipo_isol"] != "Polimérico":
        dv = distribuicao_cadeia(iso["n"], e.get("c1_c", 0.2), um / SQ3)
        iso["dist_v"] = dv
        iso["v_max_unid"] = max(dv)
        iso["v_med_unid"] = (um / SQ3) / iso["n"]
        iso["efic"] = (um / SQ3) / (iso["n"] * max(dv)) * 100.0
        if e.get("v_unid_adm"):
            iso["ok_unid"] = max(dv) <= e["v_unid_adm"]
            if not iso["ok_unid"]:
                avisos.append(f"Unidade mais solicitada com {max(dv):.1f} kV (> {e['v_unid_adm']:g} kV): avaliar anel de guarda/corona.")
    if e.get("rbl_kn"):
        iso["mec"] = mecanico(e["rbl_kn"], int(e.get("n_cad", 1)), e.get("carga_sv", 0.0), e.get("carga_cv", 0.0))
    r["isol"] = iso
    # ---- balanço e distâncias de segurança na estrutura
    fases = e.get("fases") or []
    bal = None
    if fases and e.get("d_cabo_m") and e.get("p_cabo") and e.get("lm") and e.get("lp") and e.get("casos_vento"):
        comp = iso["comp"] if e["tipo_cadeia"] != "Ancoragem" else 0.0
        segs = silhueta(fases, e["xf"], e["h_corpo"])
        bal = dict(casos={}, fases=[])
        for ch, (vp, q0) in e["casos_vento"].items():
            if vp:
                bal["casos"][ch] = cf.angulo_balanco(vp, q0, e["d_cabo_m"], e["p_cabo"], e["lm"], e["lp"])
        req = {"ff": dist["ft_ff"], "fl": dist["ft_fl"], "fr": dist["ft_fr"]}
        ch_de = {"ff": "freq", "fl": "manobra"}
        for i, (x, y) in enumerate(fases):
            linha = dict(i=i, x=x, y=y)
            for k in ("ff", "fl"):
                c = bal["casos"].get(ch_de[k])
                if c:
                    d, s = d_cond_estrutura(fases, i, comp, c["beta_max"], segs, e["tipo_cadeia"])
                    linha[k] = (d, req[k], d >= req[k], c["beta_max"])
            d0, _ = d_cond_estrutura(fases, i, comp, 0.0, segs, e["tipo_cadeia"])
            linha["fr"] = (d0, req["fr"], d0 >= req["fr"], 0.0)
            bal["fases"].append(linha)
        bal["pares"] = []
        for k, rq in (("ff", dist["ff_ff"]), ("fl", dist["ff_fl"])):
            c = bal["casos"].get(ch_de[k])
            if not c:
                continue
            ap = d_fase_fase(fases, comp, c["beta_max"], c["beta_min"], e["tipo_cadeia"])
            vao = d_fase_fase(fases, 0.0, c["beta_max"], c["beta_min"], "vão", e.get("flecha", 0.0)) if e.get("flecha") else {}
            for (i, j), d in ap.items():
                bal["pares"].append(dict(caso=k, onde="apoio", par=(i, j), d=d, req=rq, ok=d >= rq))
            for (i, j), d in vao.items():
                bal["pares"].append(dict(caso=k, onde="meio do vão", par=(i, j), d=d, req=rq, ok=d >= dist["ff_ff"] if k == "ff" else d >= rq))
        for (i, j), d in d_fase_fase(fases, comp, 0.0, 0.0, e["tipo_cadeia"]).items():
            bal["pares"].append(dict(caso="fr", onde="apoio (sem vento)", par=(i, j), d=d, req=dist["ff_fr"], ok=d >= dist["ff_fr"]))
        r["balanco"] = bal
    else:
        pend.append("Balanço do condutor: faltam vento (Módulo 3), cabo, vãos Lm/Lp ou a geometria das fases.")
    # ---- para-raios
    r["pr"] = para_raios(dict(e.get("pr", {}), um_kv=um))
    # ---- coordenação (Diretrizes 3.2.13): margens
    coord = []
    mar_ar, mar_eq = 1.05, 1.15
    if e.get("i_surto") and e.get("zc"):
        uc = e["i_surto"] / 2.0 * e["zc"]
        coord.append(("Descarga direta (Uc = Isurto/2·Zc)", uc, uc * mar_ar, "ar (+5 %)"))
    if e.get("u_ind_med"):
        uc = e["u_ind_med"] * (1.0 + 3.0 * 0.03)
        coord.append(("Descarga indireta (Uc = Um·(1+3s), s = 3 %)", uc, uc * mar_ar, "ar (+5 %)"))
    r["coord"] = coord
    # ---- blindagem (informativo)
    r["blind"] = dict(ang=e.get("ang_blind"), n_cg=e.get("n_cg"))
    if e.get("n_cg") is not None and e["n_cg"] < 2:
        avisos.append("Edital TAESA: critérios de desempenho a raios exigem ao menos dois cabos para-raios.")
    if e.get("eds_pr"):
        r["eds_pr"] = eds_para_raios(*e["eds_pr"])
    return r
