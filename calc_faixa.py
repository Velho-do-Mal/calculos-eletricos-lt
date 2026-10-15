"""
Módulo 4 – Faixa de segurança / domínio (ABNT NBR 5422:2024, Seção 17) e distâncias de segurança (Seção 7).

Unidades: m, N/m, Pa, kV, graus.  Todas as funções são puras (sem Streamlit).

Itens da norma usados (lidos no exemplar de 2024):
  8.9.1  β = atan( K · q0 · d · Lm / (p_cond · Lp) ),  K = 1 (Vp<10) ou 0,3 + 3,68·exp(−0,163·Vp)   (Figura 22)
  8.9.3  σβ = 2,25·[1 − exp(−Vp²/230)];  8.9.4 β_máx = β + 2σβ;  8.9.5 β_mín = β − 2σβ
  9.4.1  d_ft,fl = 2,174·[exp( Kcs·(√2/√3)·Us·Fsfl / (1080·kafl·kzfl·kg) ) − 1]   (para d ≤ 25 m);  kzfl = 1 − 1,3·zfl, zfl = 0,06
  7.2    D_Vtip,n = máx(PbV + Pstip + Petip,n ; D_Vlim,n + 0,90);  D_Vlim,n = PbV + Pslim + Pelim   (Pstip=0,90; Pslim=0,60)
         Tabela 5 (kg, PbV);  Tabela 6 (Kcs = 1,35 típica / 1,25 limite)
  7.3    D_H = PbH + Petip,n  (Tabela 7: kg = 1,28; PbH = 4,00 / 1,10 / 3,00)
  17.2.2.5.1  L = 2(b + d + D);  17.2.2.5.2  L = 2(d + D);  17.2.2.6  corredor de n linhas
"""
import math

G_N = 9.80665

# --------------------------------------------------------------------------- Tabela 5 (NBR 5422:2024)
# nome: (kg, altura do obstáculo [m] ou None, PbV [m], PbV depende de H?)
TAB5 = {
    "Locais acessíveis apenas a pedestres": (1.47, 3.90, 4.50),
    "Locais onde circulam máquinas agrícolas": (1.18, 4.00, 4.60),
    "Rodovias, estradas, ruas e avenidas": (1.18, 5.40, 6.00),
    "Ferrovias não eletrificadas": (1.18, 6.40, 7.00),
    "Ferrovias eletrificadas ou com previsão de eletrificação": (1.18, None, 1.90),
    "Suporte de linha pertencente à ferrovia": (1.18, None, 1.90),
    "Águas navegáveis (PbV = H + 4,20)": (1.47, None, 4.20),
    "Águas não navegáveis": (1.47, 3.60, 4.20),
    "Linhas de energia elétrica com cabo para-raios": (1.45, None, 0.80),
    "Linhas de telecomunicações": (1.45, None, 0.80),
    "Vegetação de preservação permanente": (1.18, None, 2.10),
    "Cultura agrícola permanente": (1.18, None, 2.10),
    "Instalações transportadoras (ex.: teleféricos)": (1.18, None, 1.00),
}
# Tabela 7 (distância horizontal): obstáculo -> (kg, PbH)
TAB7 = {
    "Edificações": (1.28, 4.00),
    "Veículos rodoviários e ferroviários": (1.28, 1.10),
    "Vegetação de preservação permanente": (1.28, 3.00),
}
KCS_TIP, KCS_LIM = 1.35, 1.25          # Tabela 6
P_STIP, P_SLIM = 0.90, 0.60            # 7.2.1.2 b)
ZFL = 0.06                             # 9.4.1


# --------------------------------------------------------------------------- 8.9 ângulo de balanço
def fator_K(vp):
    """Fator de efetividade do vento (8.9.1, Figura 22). vp em m/s."""
    return 1.0 if vp < 10.0 else 0.3 + 3.68 * math.exp(-0.163 * vp)


def sigma_beta(vp):
    """8.9.3 – desvio-padrão do ângulo de balanço (graus)."""
    return 2.25 * (1.0 - math.exp(-vp ** 2 / 230.0))


def angulo_balanco(vp, q0, d_m, p_n_m, lm, lp):
    """8.9. vp [m/s] (vento 50 anos/30 s); q0 [Pa]; d [m]; p_cond [N/m]; Lm vão médio [m]; Lp vão gravante [m].
    Retorna dict(K, beta, sigma, beta_max, beta_min) em graus."""
    k = fator_K(vp)
    beta = math.degrees(math.atan(k * q0 * d_m * lm / (p_n_m * lp)))
    s = sigma_beta(vp)
    return dict(K=k, beta=beta, sigma=s, beta_max=min(beta + 2 * s, 90.0), beta_min=max(beta - 2 * s, 0.0))


def q0_de_vento(vp, mu=1.225):
    """Pressão dinâmica q0 = ½·μ·Vp² (Pa); μ = massa específica do ar [kg/m³]."""
    return 0.5 * mu * vp ** 2


# --------------------------------------------------------------------------- 9.4.1 parcela elétrica
def d_ft_fl(us_kv, kcs, fsfl, kg, kafl=1.0, zfl=ZFL):
    """Distância mínima fase-terra para sobretensões de frente lenta (m) – 9.4.1 (válida para d ≤ 25 m)."""
    kz = 1.0 - 1.3 * zfl
    x = kcs * math.sqrt(2.0) / math.sqrt(3.0) * us_kv * fsfl / (1080.0 * kafl * kz * kg)
    return 2.174 * (math.exp(x) - 1.0)


def dist_vertical(us_kv, obst, fsfl, kafl=1.0, h_navio=0.0, kcs_tip=KCS_TIP, kcs_lim=KCS_LIM):
    """Distância vertical de segurança (7.2) – regime de corrente nominal.
    Retorna dict(PbV, Pe_tip, Pe_lim, D_lim_n, D_tip_n_a, D_tip_n_b, D_tip_n)."""
    kg, _alt, pbv = TAB5[obst]
    if obst.startswith("Águas navegáveis"):
        pbv = h_navio + 4.20
    pe_tip = d_ft_fl(us_kv, kcs_tip, fsfl, kg, kafl)
    pe_lim = d_ft_fl(us_kv, kcs_lim, fsfl, kg, kafl)
    d_lim = pbv + P_SLIM + pe_lim
    a = pbv + P_STIP + pe_tip
    b = d_lim + 0.90
    return dict(kg=kg, PbV=pbv, Pe_tip=pe_tip, Pe_lim=pe_lim, D_lim_n=d_lim, D_tip_a=a, D_tip_b=b, D_tip_n=max(a, b))


def dist_horizontal(us_kv, obst, fsfl, kafl=1.0, kcs_tip=KCS_TIP):
    """Distância horizontal de segurança D_H = PbH + Petip,n (7.3.2, Tabela 7)."""
    kg, pbh = TAB7[obst]
    pe = d_ft_fl(us_kv, kcs_tip, fsfl, kg, kafl)
    return dict(kg=kg, PbH=pbh, Pe_tip=pe, D_H=pbh + pe)


# --------------------------------------------------------------------------- planilha BK (referência histórica)
def d_planilha(u_kv):
    """Distância de segurança D da aba 'Faixa de Servidão' da planilha BK: 0,5 m (U ≤ 69 kV) ou U·1,05/150."""
    return 0.5 if u_kv <= 69 else u_kv * 1.05 / 150.0


def d_seg_planilha(u_kv, base):
    """Aba 'Distância de Segurança' da planilha BK: base + 0,01·(U·1,05/√3 − 50) para U > 69 kV."""
    return base if u_kv <= 69 else base + 0.01 * (u_kv * 1.05 / math.sqrt(3) - 50.0)


# --------------------------------------------------------------------------- 17.2 largura da faixa
def faixa(b, comp_cadeia, flecha_max, beta_graus, D, simetrica=True, lado_isol=None, arred=1.0):
    """Faixa de segurança (17.2.2.5).  b: distância do eixo ao ponto de fixação da cadeia mais externa [m];
    comp_cadeia: 0 em ancoragem/line-post; flecha_max: flecha à temperatura máxima [m]; D: distância horizontal [m].
    d = (cadeia + flecha)·sen β  (projeção horizontal).
    Retorna dict(d, L, L_adot, lado_isol, lado_oposto)."""
    d = (comp_cadeia + flecha_max) * math.sin(math.radians(beta_graus))
    if simetrica:
        L = 2.0 * (b + d + D)                       # 17.2.2.5.1
    else:
        L = 2.0 * (d + D)                           # 17.2.2.5.2
    adot = math.ceil(round(L / arred, 9)) * arred
    out = dict(d=d, L=L, L_adot=adot, simetrica=simetrica)
    if not simetrica:
        li = b if lado_isol is None else lado_isol
        out.update(lado_isol=li, lado_oposto=adot - li)
    else:
        out.update(lado_isol=adot / 2.0, lado_oposto=adot / 2.0)
    return out


def faixa_corredor(linhas, dist_eixos):
    """17.2.2.6 – corredor de n linhas.  linhas: lista de dict(b, d, D) em ordem; dist_eixos: n−1 distâncias entre eixos [m].
    L = Σ ds_j + d1 + b1 + D1 + dn + bn + Dn."""
    if len(linhas) < 2 or len(dist_eixos) != len(linhas) - 1:
        raise ValueError("Informe ao menos 2 linhas e (n−1) distâncias entre eixos.")
    a, z = linhas[0], linhas[-1]
    L = sum(dist_eixos) + a["d"] + a["b"] + a["D"] + z["d"] + z["b"] + z["D"]
    return dict(L=L, L_adot=math.ceil(round(L, 9)))


# --------------------------------------------------------------------------- pacote principal
def calcular(e):
    """e: dict de entrada.  Chaves:
       vp, q0 (opcional), d_mm, peso_kgf_m (ou massa_kg_m), lm, lp, b, comp_cadeia, flecha, simetrica, lado_isol,
       un_kv, fsfl, kafl, criterio_beta ('medio'|'maximo'), criterio_D ('norma'|'planilha'|'maior'), obst_h (lista)."""
    r = dict(erros=[], avisos=[])
    for k in ("vp", "d_mm", "lm", "lp", "flecha", "un_kv"):
        if e.get(k) in (None, 0) and k != "flecha":
            r["erros"].append(f"Falta '{k}'.")
    massa = e.get("massa_kg_m")
    if not massa:
        r["erros"].append("Falta a massa linear do cabo (cadastre no catálogo).")
    if r["erros"]:
        return r
    p_n = massa * G_N
    q0 = e.get("q0") or q0_de_vento(e["vp"])
    ang = angulo_balanco(e["vp"], q0, e["d_mm"] / 1000.0, p_n, e["lm"], e["lp"])
    beta = ang["beta"] if e.get("criterio_beta", "medio") == "medio" else ang["beta_max"]
    us = e["un_kv"]
    fs, ka = e.get("fsfl", 2.0), e.get("kafl", 1.0)
    # D horizontal (17.2.2.5: 9.4.1 com kg = 1,28 e Kcs = 1,35)
    D_norma = d_ft_fl(us, KCS_TIP, fs, 1.28, ka)
    D_pl = d_planilha(us)
    modo = e.get("criterio_D", "maior")
    D = {"norma": D_norma, "planilha": D_pl, "maior": max(D_norma, D_pl)}[modo]
    fx = faixa(e["b"], e["comp_cadeia"], e["flecha"], beta, D, e.get("simetrica", True), e.get("lado_isol"))
    r.update(p_n=p_n, q0=q0, ang=ang, beta_usado=beta, D_norma=D_norma, D_planilha=D_pl, D=D, faixa=fx)
    # verificação extra: faixa com β_máx e com β médio
    r["faixa_medio"] = faixa(e["b"], e["comp_cadeia"], e["flecha"], ang["beta"], D, e.get("simetrica", True), e.get("lado_isol"))
    r["faixa_max"] = faixa(e["b"], e["comp_cadeia"], e["flecha"], ang["beta_max"], D, e.get("simetrica", True), e.get("lado_isol"))
    # distâncias verticais e horizontais de segurança
    r["verticais"] = {k: dist_vertical(us, k, fs, ka, e.get("h_navio", 0.0)) for k in TAB5}
    r["horizontais"] = {k: dist_horizontal(us, k, fs, ka) for k in TAB7}
    r["verticais_planilha"] = {k: d_seg_planilha(us, base) for k, base in PLAN_BASES.items()}
    if e["vp"] < 10:
        r["avisos"].append("Vp < 10 m/s: K = 1 (8.9.1).")
    if D_norma > 25:
        r["avisos"].append("d_ft,fl > 25 m: a expressão de 9.4.1 não se aplica (NECESSITA VALIDAÇÃO TÉCNICA).")
    return r


# bases da aba 'Distância de Segurança' da planilha BK (histórico, estilo NBR 5422:1985)
PLAN_BASES = {
    "Locais acessíveis apenas a pedestres": 6.0,
    "Locais onde circulam máquinas agrícolas": 6.5,
    "Rodovias, ruas e avenidas": 8.0,
    "Ferrovias não eletrificadas": 9.0,
    "Ferrovias eletrificadas ou com previsão de eletrificação": 12.0,
    "Suporte de linha pertencente à ferrovia": 4.0,
    "Águas não navegáveis": 6.0,
    "Linhas de telecomunicações": 1.8,
    "Telhados e terraços": 4.0,
    "Paredes": 3.0,
    "Instalações transportadoras": 3.0,
    "Veículos rodoviários e ferroviários": 3.0,
}
