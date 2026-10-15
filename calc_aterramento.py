"""
Módulo 6 – Aterramento de estruturas de linhas de transmissão (pé de torre / contrapeso).

Conteúdo
  1. Resistividade: aparente por Wenner (ρ = 2π·a·R) e estratificação em 2 camadas (ajuste por mínimos quadrados).
  2. Resistência de aterramento em baixa frequência: n pernas radiais enterradas (método dos momentos / ponto-colocação,
     solo de 1 ou 2 camadas por série de imagens), com verificação pela fórmula de Dwight/Sunde para 1 perna.
  3. Comportamento impulsivo (CIGRE/IEEE): comprimento efetivo, ionização do solo e resistência impulsiva.
  4. Seção mínima do condutor pela corrente de falta (IEEE Std 80, eq. 37 – aba "Aterramento" da planilha BK).
  5. Tensões: GPR = If·R e limites de passo/toque (IEEE Std 80-2013, eq. 29 a 32).

Unidades: m, Ω, Ω·m, kA, A, s, °C. As funções são puras (sem Streamlit).
"""
import json
import math
import os

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))


def carregar_db():
    with open(os.path.join(AQUI, "dados", "db_aterramento.json"), encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- 1. resistividade
def rho_wenner(a_m, r_ohm):
    """Resistividade aparente (Ω·m) pelo método de Wenner: ρ = 2π·a·R."""
    return 2.0 * math.pi * a_m * r_ohm


def wenner_2camadas(a, rho1, rho2, h1, n_termos=200):
    """ρ aparente de Wenner (Ω·m) para solo de 2 camadas (série de imagens, Tagg).  a: espaçamento (m, escalar ou array)."""
    escalar = np.ndim(a) == 0
    a = np.atleast_1d(np.asarray(a, dtype=float))
    k = (rho2 - rho1) / (rho2 + rho1)
    n = np.arange(1, n_termos + 1)[:, None]
    x = 2.0 * n * h1 / a[None, :]
    s = (k ** n) * (1.0 / np.sqrt(1.0 + x ** 2) - 1.0 / np.sqrt(4.0 + x ** 2))
    out = rho1 * (1.0 + 4.0 * s.sum(axis=0))
    return float(out[0]) if escalar else out


def ajustar_2camadas(a, rho_ap):
    """Ajusta (ρ1, ρ2, h1) às medições Wenner (mínimos quadrados sobre ln ρ).  Retorna dict(rho1, rho2, h1, erro_rms_pct)."""
    a = np.asarray(a, float)
    y = np.log(np.asarray(rho_ap, float))
    g1 = np.geomspace(max(1.0, 0.2 * rho_ap[0]), 5.0 * max(rho_ap[0], 1.0), 26)
    g2 = np.geomspace(max(1.0, 0.1 * min(rho_ap)), 10.0 * max(rho_ap), 40)
    gh = np.geomspace(0.3, max(a) * 1.5, 30)

    def err(p):
        r1, r2, h = p
        return float(np.sqrt(np.mean((np.log(wenner_2camadas(a, r1, r2, h)) - y) ** 2)))
    melhor = min(((err((r1, r2, h)), r1, r2, h) for r1 in g1 for r2 in g2 for h in gh))
    try:
        from scipy.optimize import minimize
        res = minimize(lambda p: err(np.abs(p)), melhor[1:], method="Nelder-Mead", options=dict(xatol=1e-3, fatol=1e-9, maxiter=2000))
        e, p = res.fun, np.abs(res.x)
        if e < melhor[0]:
            melhor = (e, *p)
    except Exception:
        pass
    e, r1, r2, h = melhor
    return dict(rho1=float(r1), rho2=float(r2), h1=float(h), erro_rms_pct=100.0 * (math.exp(e) - 1.0))


# --------------------------------------------------------------------------- 2. resistência de aterramento
def dwight_1perna(rho, L, h, a):
    """Resistência (Ω) de um condutor horizontal enterrado, comprimento total L, profundidade h e raio a (Dwight/Sunde,
    com l = L/2 e s = 2h):  R = ρ/(2πL)·[ln(2L/a) + ln(L/h) − 2 + 2h/L − h²/L²]."""
    return rho / (2.0 * math.pi * L) * (math.log(2.0 * L / a) + math.log(L / h) - 2.0 + 2.0 * h / L - (h / L) ** 2)


def _gauss(n):
    x, w = np.polynomial.legendre.leggauss(n)
    return x, w


def resistencia_radial(rho1, n_pernas, L, h, a, rho2=None, h1=None, seg_por_perna=24, n_gauss=10, n_imagens=60, ang0_deg=0.0):
    """Resistência (Ω) de n pernas radiais iguais, saindo do centro, à profundidade h (m), raio do cabo a (m).
    Solo uniforme (rho2=None) ou de 2 camadas (rho1 até a profundidade h1, rho2 abaixo).  Pernas devem estar na camada 1 (h < h1).
    Método: ponto-colocação (potencial no ponto médio de cada segmento), corrente uniforme por segmento, núcleo
    com as imagens do ar e da interface:  V = ρ1/(4π)·Σ_n k^|n|·[1/√(ρ²+(2n·h1)²) + 1/√(ρ²+(2h+2n·h1)²)]."""
    k = 0.0
    if rho2 is not None and h1 is not None:
        k = (rho2 - rho1) / (rho2 + rho1)
    m = seg_por_perna
    ell = L / m
    ini, fim = [], []
    for p in range(n_pernas):
        ang = math.radians(ang0_deg + 360.0 * p / n_pernas)
        d = np.array([math.cos(ang), math.sin(ang)])
        for s_ in range(m):
            ini.append(d * (s_ * ell))
            fim.append(d * ((s_ + 1) * ell))
    ini, fim = np.array(ini), np.array(fim)            # (S, 2)  – todas as pernas à mesma profundidade
    S = len(ini)
    mid = 0.5 * (ini + fim)
    xg, wg = _gauss(n_gauss)
    t, w = 0.5 * (xg + 1.0), 0.5 * wg                  # pontos e pesos (média ao longo do segmento)
    pts = ini[:, None, :] + (fim - ini)[:, None, :] * t[None, :, None]       # (S_fonte, G, 2)
    nn = np.arange(-n_imagens, n_imagens + 1) if k != 0 else np.array([0])
    kk = k ** np.abs(nn) if k != 0 else np.array([1.0])
    off = 2.0 * nn * (h1 if k != 0 else 0.0)
    Z = np.zeros((S, S))
    for i in range(S):                                  # i = ponto de observação
        rho2d = np.sqrt(((pts - mid[i]) ** 2).sum(axis=2))               # (S_fonte, G)
        # imagem do ar e imagens da interface (todas, inclusive n=0 do ar)
        img = (kk[:, None, None] / np.sqrt(rho2d[None] ** 2 + (2.0 * h + off)[:, None, None] ** 2)).sum(axis=0)
        # termo direto (z = z0) + imagens de interface n≠0
        sel = nn != 0
        if sel.any():
            img = img + (kk[sel][:, None, None] / np.sqrt(rho2d[None] ** 2 + off[sel][:, None, None] ** 2)).sum(axis=0)
        direto = 1.0 / np.sqrt(rho2d ** 2 + 1e-300)
        Z[i, :] = ((img + direto) * w[None, :]).sum(axis=1)
        # próprio segmento: termo direto analítico com o raio do cabo (média de 1/√(s²+a²))
        dpr = (2.0 / ell) * math.asinh(ell / (2.0 * a))
        Z[i, i] = Z[i, i] - ((direto[i]) * w).sum() + dpr
    Z *= rho1 / (4.0 * math.pi)
    I = np.linalg.solve(Z, np.ones(S))
    return 1.0 / I.sum()


# --------------------------------------------------------------------------- 3. impulso
def comprimento_efetivo(rho):
    """CIGRE: comprimento efetivo de eletrodo horizontal sob impulso, Le = 1,4·√ρ (m)."""
    return 1.4 * math.sqrt(rho)


def resistencia_impulsiva(r0, rho, i_kA, e0_kv_m=300.0):
    """CIGRE/IEEE: R_i = R0/√(1 + I/I_g), I_g = ρ·E0/(2π·R0²).  i_kA: corrente de descarga (kA).  Retorna (R_i, I_g em kA)."""
    ig = rho * (e0_kv_m * 1000.0) / (2.0 * math.pi * r0 ** 2)
    ri = r0 / math.sqrt(1.0 + (i_kA * 1000.0) / ig)
    return ri, ig / 1000.0


# --------------------------------------------------------------------------- 4. seção mínima
def secao_minima(i_ka, t_s, ar, rho_r, tcap, tm, ta, k0=None, a0=None):
    """IEEE Std 80, eq. 37 (planilha BK): A[mm²] = I·√[ t·αr·ρr·10⁴ / (TCAP·ln((K0+Tm)/(K0+Ta))) ].
    i_ka: kA; t_s: s; ar: αr (1/°C); rho_r: μΩ·cm; tcap: J/(cm³·°C); tm, ta: °C; k0 = 1/α0 (°C)."""
    if k0 is None:
        k0 = 1.0 / a0
    return i_ka * math.sqrt((t_s * ar * rho_r * 1e4) / (tcap * math.log((k0 + tm) / (k0 + ta))))


# --------------------------------------------------------------------------- 5. tensões
def limites_passo_toque(rho_s, rho_brita, h_brita, t_s, peso_kg=70):
    """IEEE Std 80-2013: E_passo e E_toque admissíveis (V).  rho_brita=None → sem camada superficial (Cs = 1)."""
    cs = 1.0
    if rho_brita and h_brita:
        cs = 1.0 - 0.09 * (1.0 - rho_s / rho_brita) / (2.0 * h_brita + 0.09)
        rs = rho_brita
    else:
        rs = rho_s
    # 0,116 → 50 kg; 0,157 → 70 kg  (eq. 29 a 32)
    k = {50: 0.116, 70: 0.157}[peso_kg]
    return dict(Cs=cs, passo=(1000.0 + 6.0 * cs * rs) * k / math.sqrt(t_s), toque=(1000.0 + 1.5 * cs * rs) * k / math.sqrt(t_s))


def gpr(i_a, r_ohm):
    return i_a * r_ohm


# --------------------------------------------------------------------------- pacote principal
def calcular(e):
    """e: dict de entrada.  Chaves: rho (Ω·m, uniforme) ou camadas (rho1, rho2, h1); n_pernas, L, h, d_cabo_mm,
    r_meta, i_falta_ka, t_falta, i_desc_ka, material (dict do DB), conexao_tm, ta, rho_brita, h_brita, peso, L_lista."""
    r = dict(erros=[], avisos=[])
    if e.get("modo_solo", "Uniforme") == "Uniforme":
        rho1, rho2, h1 = e["rho"], None, None
    else:
        rho1, rho2, h1 = e["rho1"], e["rho2"], e["h1"]
        if e["h"] >= h1:
            r["avisos"].append("A profundidade do contrapeso é maior que a espessura da 1ª camada: o modelo exige o cabo na 1ª camada – NECESSITA VALIDAÇÃO TÉCNICA.")
    a = e["d_cabo_mm"] / 2000.0
    if a <= 0:
        r["erros"].append("Informe o diâmetro do cabo contrapeso.")
        return r
    n, L, h = int(e["n_pernas"]), e["L"], e["h"]
    r["R"] = resistencia_radial(rho1, n, L, h, a, rho2, h1, ang0_deg=e.get("ang0", 0.0))
    if rho2 is None:
        r["R_dwight_1"] = dwight_1perna(rho1, L, h, a)
        r["R_1perna"] = resistencia_radial(rho1, 1, L, h, a)
    r["rho_ref"] = rho1
    # curva R × L
    Ls = sorted(set([5, 10, 15, 20, 30, 40, 50, 60, 80, 100] + [L]))
    r["curva"] = [(l, resistencia_radial(rho1, n, l, h, a, rho2, h1, ang0_deg=e.get("ang0", 0.0), seg_por_perna=max(12, int(l / 2)))) for l in Ls]
    # impulsiva
    rho_imp = rho1 if rho2 is None else rho1
    ri, ig = resistencia_impulsiva(r["R"], rho_imp, e["i_desc_ka"])
    r["imp"] = dict(Le=comprimento_efetivo(rho_imp), Ri=ri, Ig=ig, L_acima_Le=L > comprimento_efetivo(rho_imp))
    if r["imp"]["L_acima_Le"]:
        r["avisos"].append(f"L = {L:g} m excede o comprimento efetivo sob impulso (1,4·√ρ = {r['imp']['Le']:.0f} m): o trecho excedente pouco reduz a impedância de surto.")
    r["atende"] = r["R"] <= e["r_meta"]
    # tabela de projeto: menor L (lista) que atende a meta, por faixa de ρ
    r["tabela_rho"] = []
    for rho_t in e.get("rho_lista", [100, 300, 500, 1000, 2000, 3000, 5000]):
        achado = None
        for l in e.get("L_lista", [6, 10, 15, 20, 30, 40, 60, 80]):
            if resistencia_radial(rho_t, n, l, h, a, seg_por_perna=max(8, int(l / 3))) <= e["r_meta"]:
                achado = l
                break
        r["tabela_rho"].append((rho_t, achado, resistencia_radial(rho_t, n, achado or max(e.get("L_lista", [80])), h, a, seg_por_perna=16)))
    # seção mínima
    mat = e["material"]
    ok_cond = e["i_falta_ka"] > 0
    if ok_cond:
        k = e.get("fator_corrente", 1.0)
        r["secao_min"] = secao_minima(e["i_falta_ka"] * k, e["t_falta"], mat["ar"], mat["rho"], mat["tcap"], e["tm"], e["ta"], a0=mat["a0"])
    # tensões
    r["gpr"] = gpr(e["i_falta_ka"] * 1000.0 * e.get("fracao_terra", 1.0), r["R"])
    r["lim"] = limites_passo_toque(e["rho_sup"], e.get("rho_brita"), e.get("h_brita"), e["t_falta"], e.get("peso", 70))
    return r
