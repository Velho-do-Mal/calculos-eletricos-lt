"""
Módulo 16 – Blindagem contra descargas atmosféricas: modelo eletrogeométrico (EGM), falha de blindagem, backflashover e taxa de desligamentos.
Funções puras (sem Streamlit).

Fontes (acervo): Kiessling et al., 'Overhead Power Lines', cap. 4 (eq. 4.1, 4.3, 4.4, 4.7 e Tabela 4.2); Diretrizes de Projeto Básico 6.8 e itens de desempenho
a descargas (≤ 1 desligamento/100 km/ano para ≥ 345 kV; ≤ 2 para ≤ 230 kV; falha de blindagem ≤ 0,01/100 km/ano); Projeto Elétrico de LTs 4.2.1.
  • Distância de atração (strike distance):  D = 6,7·I^0,8  [m; I em kA]  (Kiessling 4.1); ao solo: βs·D, βs = 0,8 (faixa I) ou 0,67 (faixa II) (EPRI/IEC 60071).
  • Densidade de descargas: Ng informada ou a partir do nível ceráunico Nk: Ng ≈ 0,2·Nk (4.3) ou Eriksson Ng = 0,04·Nk^1,25 (4.2, OCR parcialmente ilegível).
  • Sobretensão em descarga direta no condutor: Uc = ½·I·Zc (4.4/4.7); há desligamento se Uc ≥ U50% (4.5, tensão de 60 Hz desprezada → ligeiramente não conservador).
  • Backflashover: corrente crítica I_c = U50 / (Z_ef·(1 − k)), com k = coeficiente de acoplamento guarda–fase (Kiessling 4.4.2, exemplo 550/(10·0,85)).
    A eq. (4.6) está ilegível no OCR: Z_ef = R_i(I) + Z da torre, com R_i(I) = R0/√(1 + I/Ig) (ionização do solo, CIGRE; Ig = E0·ρ/(2π·R0²), E0 = 400 kV/m) – NECESSITA VALIDAÇÃO.
NECESSITA VALIDAÇÃO (não constam no acervo em forma numérica): distribuição de corrente CIGRE/Anderson P(I ≥ i) = 1/(1 + (i/31)^2,6); número de descargas na LT
N_L = Ng·(28·h^0,6 + b)/10 por 100 km (Eriksson/IEEE 1243); fração das descargas em guarda que vão à torre (0,6).
Premissas: terreno plano; alturas médias no vão (altura na estrutura − 2/3 da flecha); sem efeito de corona nos surtos e sem tensão de 60 Hz instantânea.
"""
import math

import numpy as np

import calc_isolamento as ci

KDF = 0.961            # Kiessling (U90% = 0,961·U50%)


def p_corrente(i_ka, mediana=31.0, expo=2.6):
    """P(I ≥ i) – distribuição log-normal aproximada de CIGRE/Anderson (NECESSITA VALIDAÇÃO)."""
    return 1.0 / (1.0 + (np.asarray(i_ka, float) / mediana) ** expo)


def pdf_corrente(i_ka, mediana=31.0, expo=2.6):
    i = np.asarray(i_ka, float)
    u = (i / mediana) ** expo
    return expo * u / (i * (1.0 + u) ** 2)


def ng_de_nk(nk, formula="0,2·Nk"):
    return 0.2 * nk if formula.startswith("0,2") else 0.04 * nk ** 1.25


def r_atracao(i_ka):
    return 6.7 * np.asarray(i_ka, float) ** 0.8


def zc_fase(h, req):
    """Impedância de surto da fase (Ω): 60·ln(2h/r_eq), com h médio e raio equivalente (feixe)."""
    return 60.0 * math.log(2.0 * h / max(req, 1e-4))


def largura_exposta(fases, guardas, i_ka, beta_s, dx=0.05):
    """Largura lateral (m) dos pontos de onde um líder com corrente I atinge um condutor de fase (EGM de Brown-Whitehead).
    fases/guardas: listas de dict(x, y). Retorna (W_total, lista [(x_ini, x_fim)])."""
    rs = float(r_atracao(i_ka))
    rg = beta_s * rs
    xs_all = [f["x"] for f in fases] + [g["x"] for g in guardas]
    x = np.arange(min(xs_all) - rs - 1.0, max(xs_all) + rs + 1.0, dx)
    y_obj = []
    for o in fases + guardas:
        dd = rs ** 2 - (x - o["x"]) ** 2
        y_obj.append(np.where(dd >= 0, o["y"] + np.sqrt(np.maximum(dd, 0.0)), -1e9))
    y_obj = np.array(y_obj)
    n_f = len(fases)
    topo = y_obj.max(axis=0)
    qual = y_obj.argmax(axis=0)
    expo = (qual < n_f) & (topo > rg)
    w = float(expo.sum() * dx)
    # intervalos
    ints, ini = [], None
    for xi, e in zip(x, expo):
        if e and ini is None:
            ini = xi
        if (not e) and ini is not None:
            ints.append((float(ini), float(xi)))
            ini = None
    if ini is not None:
        ints.append((float(ini), float(x[-1])))
    return w, ints


def acoplamento(fases, guardas, req_g):
    """Coeficiente de acoplamento guarda–fase k = Zgf/Zgg (mínimo entre as fases = pior caso) e Zgg efetivo."""
    if not guardas:
        return 0.0
    zgg = []
    for g in guardas:
        zgg.append(60.0 * math.log(2.0 * g["y"] / req_g))
    ks = []
    for f in fases:
        zm = []
        for g in guardas:
            d = math.hypot(f["x"] - g["x"], f["y"] - g["y"])
            dimg = math.hypot(f["x"] - g["x"], f["y"] + g["y"])
            zm.append(60.0 * math.log(dimg / d))
        ks.append(np.mean(zm) / np.mean(zgg))
    return float(min(ks))


def angulos_blindagem(fases, guardas):
    """Ângulo de blindagem (°) de cada fase: entre a vertical do cabo guarda mais alto/próximo e a fase."""
    out = []
    for f in fases:
        melhor = None
        for g in guardas:
            if g["y"] > f["y"]:
                a = math.degrees(math.atan2(abs(f["x"] - g["x"]), g["y"] - f["y"]))
                melhor = a if melhor is None else min(melhor, a)
        out.append(melhor)
    return out


def calcular(e):
    """e: fases [dict(x, y, req, circuito, fase, nome)], guardas [dict(x, y, r)], ng, faixa ('I'|'II'), un_kv, umax_kv, cfo_kv (None → tabela 15/0,961),
    r_pe, z_torre, frac_torre, b_guarda_m, h_torre, meta, meta_sf, ang_lim, nk."""
    erros, avisos = [], []
    if not e.get("fases"):
        return dict(erros=["Geometria sem fases: preencha o Módulo 2 / seção transversal."], avisos=[])
    if not e.get("guardas"):
        avisos.append("Sem cabos para-raios: todas as descargas diretas atingem os condutores de fase (blindagem inexistente).")
    fases, guardas = e["fases"], e["guardas"]
    beta = 0.8 if e["faixa"] == "I" else 0.67
    cfo = e.get("cfo_kv") or ci.ufr_tabela(e["un_kv"]) / KDF
    zc = float(np.mean([zc_fase(f["y"], f["req"]) for f in fases]))
    i_flash_sf = 2.0 * cfo / zc                                      # kA: Uc = ½·I·Zc ≥ CFO
    # ---- falha de blindagem
    di = 1.0
    corr = np.arange(2.0, 201.0, di)
    W = []
    for i in corr:
        W.append(largura_exposta(fases, guardas, float(i), beta, dx=0.1)[0] if guardas else 2 * (max(f["x"] for f in fases) - min(f["x"] for f in fases)) + 2.0 * float(r_atracao(i)) * 0 + 0)
    W = np.array(W)
    if not guardas:
        W = np.array([max(0.1, max(f["x"] for f in fases) - min(f["x"] for f in fases) + 2 * float(r_atracao(i))) for i in corr])
    pdf = pdf_corrente(corr)
    ng = e["ng"]
    mask = corr >= i_flash_sf
    n_sf_atinge = float(ng * 0.1 * np.sum(W * pdf * di))               # descargas em fase /100 km/ano
    n_sf = float(ng * 0.1 * np.sum((W * pdf * di)[mask]))             # com flashover
    i_max_blind = float(corr[W > 0].max()) if (W > 0).any() else 0.0
    # ---- backflashover
    k = acoplamento(fases, guardas, e.get("r_guarda", 0.005)) if guardas else 0.0
    r0, zt = e["r_pe"], e["z_torre"]
    ig = (e.get("e0_kv_m", 400.0) * e.get("rho", 1000.0) / (2.0 * math.pi * r0 ** 2)) if (e.get("ioniza", True) and r0 > 0) else None

    def tensao_isol(i):                                   # kV sobre a cadeia: I·(R_i + Z_torre)·(1 − k)
        ri = r0 / math.sqrt(1.0 + i / ig) if ig else r0
        return i * (ri + zt) * (1.0 - k)
    i_c_bf = 0.0
    if guardas:
        lo, hi = 0.1, 5000.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if tensao_isol(mid) < cfo else (lo, mid)
        i_c_bf = 0.5 * (lo + hi)
    z_ef = cfo / (i_c_bf * (1.0 - k)) if i_c_bf else r0 + zt
    h_g = max([g["y"] for g in guardas] or [0.0])
    n_l = ng * (28.0 * (e.get("h_torre") or h_g) ** 0.6 + e["b_guarda_m"]) / 10.0 if guardas else 0.0
    p_bf = float(p_corrente(i_c_bf)) if guardas else 0.0
    n_bf = float(n_l * e["frac_torre"] * p_bf)
    total = n_sf + n_bf
    ang = angulos_blindagem(fases, guardas)
    ang_max = max([a for a in ang if a is not None] or [None]) if any(a is not None for a in ang) else None
    if any(a is None for a in ang):
        avisos.append("Há fase acima (ou na mesma altura) dos cabos para-raios: sem blindagem para essa fase.")
    if ang_max is not None and ang_max > e["ang_lim"]:
        avisos.append(f"Ângulo de blindagem máximo {ang_max:.1f}° acima do limite adotado ({e['ang_lim']:g}°).")
    if len(guardas) < 2 and guardas:
        avisos.append("Edital TAESA/Diretrizes: dimensionar com ao menos dois cabos para-raios.")
    avisos.append("Fórmulas do Kiessling cap. 4 aplicadas; distribuição de corrente (CIGRE), N_L (IEEE 1243) e fração de descargas na torre NECESSITAM VALIDAÇÃO.")
    # geometria para o gráfico: círculos com a corrente crítica
    i_graf = float(min(max(i_flash_sf, 3.0), 100.0))
    w_g, ints = largura_exposta(fases, guardas, i_graf, beta, dx=0.05) if guardas else (0.0, [])
    return dict(erros=erros, avisos=avisos, beta=beta, cfo=float(cfo), zc=zc, i_flash_sf=float(i_flash_sf), corr=corr.tolist(), W=W.tolist(), i_max_blind=i_max_blind,
                n_sf_atinge=n_sf_atinge, n_sf=n_sf, k=k, z_ef=float(z_ef), i_c_bf=float(i_c_bf), n_l=float(n_l), p_bf=p_bf, n_bf=n_bf, total=float(total),
                ok_total=bool(total <= e["meta"] + 1e-9), ok_sf=bool(n_sf <= e["meta_sf"] + 1e-9), ang=ang, ang_max=ang_max, i_graf=i_graf, ints_graf=ints,
                fases=fases, guardas=guardas, e=e)
