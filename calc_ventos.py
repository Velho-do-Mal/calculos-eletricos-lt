"""
Módulo 3 – Estudo dos ventos e temperaturas conforme ABNT NBR 5422:2024 (funções puras, sem Streamlit).

Cadeia de cálculo (itens da norma):
  4.9.4.1  V = Vm / (Kint·Krug·Kalt)                  conversão da medição para 10 min, 10 m, terreno B
  A.2      V_R(T) = v̄ + K(T,n)·s                      Gumbel, K = (C_T − C2)/C1, C_T = −ln[−ln(1−1/T)]
  8.2.1.1  V_P = Ktur·V_R                              vento de 10 min de projeto (Tabela 8)
  8.2.2.1  V_P30 = Kint30·Kalt·Krug·V_P                vento de 30 s (Tabela 9)
  8.2.3.4  V_P3 = 1,15·Kint3·V_P                       vento de 3 s (Tabela 2)
  4.7      μ = 1,225·288,15/(t+273,15)·exp(−1,2e-4·alt)   massa específica do ar (t = média das mínimas)
  8.4.2    q0 = ½·μ·V_P²                               pressão dinâmica
C1 e C2 (Tabela A.1) são calculados a partir de n pelas fórmulas do Anexo A (z_i = −ln[−ln(i/(n+1))]).
Valores das Tabelas 1, 2, 3, 8 e 9 foram conferidos nas imagens da norma.
"""
import math

NBR = "ABNT NBR 5422:2024"
CATEGORIAS = ("A", "B", "C", "D")
KRUG = {"A": 1.08, "B": 1.00, "C": 0.85, "D": 0.67}            # Tabela 1 (4.9.4.2)
KINT_3S = {"A": 1.31, "B": 1.41, "C": 1.58, "D": 1.88}         # Tabela 2 (4.9.4.3)
ALFA = {"A": 0.110, "B": 0.160, "C": 0.220, "D": 0.280}        # Tabela 3 (4.9.4.4)
KINT_30S = {"A": 1.17, "B": 1.22, "C": 1.30, "D": 1.48}        # Tabela 9 (8.2.2.1)
KTUR = {"Sul": 1.08, "Sudeste": 1.12, "Centro-Oeste": 1.12, "Norte": 1.16, "Nordeste": 1.16}   # Tabela 8
REGIAO_UF = {
    "Sul": ["PR", "SC", "RS"], "Sudeste": ["SP", "RJ", "MG", "ES"], "Centro-Oeste": ["DF", "GO", "MT", "MS"],
    "Norte": ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]}
UF_REGIAO = {uf: r for r, ufs in REGIAO_UF.items() for uf in ufs}


# ----------------------------------------------------------------------------- Gumbel (Anexo A)
def gumbel_c1c2(n):
    """C1 (desvio-padrão de z) e C2 (média de z) para n anos (Anexo A.2.2.1 / Tabela A.1)."""
    z = [-math.log(-math.log(i / (n + 1))) for i in range(1, n + 1)]
    zb = sum(z) / n
    return math.sqrt(sum((x - zb) ** 2 for x in z) / n), zb


def fator_freq(T, n):
    """K(T,n) = (C_T − C2)/C1 (A.2.5)."""
    c1, c2 = gumbel_c1c2(n)
    ct = -math.log(-math.log(1 - 1 / T))
    return (ct - c2) / c1


def estatisticas_serie(valores):
    """Média e desvio-padrão amostral (n−1) de uma série de máximos anuais."""
    n = len(valores)
    m = sum(valores) / n
    s = math.sqrt(sum((v - m) ** 2 for v in valores) / (n - 1)) if n > 1 else 0.0
    return m, s, n


def converter_medicao(v, integracao, cat_estacao, z_med):
    """4.9.4.1: devolve (V convertida, Kint, Krug, Kalt). integracao: '10 min' ou '3 s'."""
    kint = 1.0 if integracao == "10 min" else KINT_3S[cat_estacao]
    krug = KRUG[cat_estacao]
    kalt = (z_med / 10.0) ** ALFA[cat_estacao]
    return v / (kint * krug * kalt), kint, krug, kalt


# ----------------------------------------------------------------------------- ar
def massa_especifica(t_c, alt_m):
    """4.7: μ em kg/m³ (t = temperatura média das mínimas; alt = altitude média)."""
    return 1.225 * 288.15 / (t_c + 273.15) * math.exp(-1.2e-4 * alt_m)


# ----------------------------------------------------------------------------- vento de projeto
def vento_projeto(v_ref, ktur, cat, h_cabo, integracao):
    """Velocidade de projeto (m/s) a partir de V_R (10 min, 10 m, categoria B convertida)."""
    vp = ktur * v_ref                                            # 8.2.1.1
    if integracao == "10 min":
        return vp, dict(Ktur=ktur)
    if integracao == "30 s":
        kalt = (h_cabo / 10.0) ** ALFA[cat]
        k = dict(Ktur=ktur, Kint=KINT_30S[cat], Kalt=kalt, Krug=KRUG[cat])
        return k["Kint"] * k["Kalt"] * k["Krug"] * vp, k          # 8.2.2.1
    k = dict(Ktur=ktur, Kint=KINT_3S[cat], fator=1.15)
    return 1.15 * k["Kint"] * vp, k                               # 8.2.3.4


def estudo(e):
    """
    e: dict com
      v_med, s (m/s, já convertidos para 10 min/10 m/B), n;
      regiao, cat, h_cabo, alt, t_coinc, casos (lista de dicts: nome, TR, integracao, ref)
    Retorna dict com parâmetros de Gumbel e a lista de casos calculados.
    """
    ktur = KTUR[e["regiao"]]
    mu = massa_especifica(e["t_coinc"], e["alt"])
    c1, c2 = gumbel_c1c2(e["n"])
    out = dict(ktur=ktur, mu=mu, c1=c1, c2=c2, n=e["n"], v_med=e["v_med"], s=e["s"],
               cv=e["s"] / e["v_med"] if e["v_med"] else 0.0, casos=[])
    for c in e["casos"]:
        kt = fator_freq(c["TR"], e["n"])
        vr = e["v_med"] + kt * e["s"]
        vp, fat = vento_projeto(vr, ktur, e["cat"], e["h_cabo"], c["integracao"])
        out["casos"].append(dict(c, K=kt, VR=vr, VP=vp, fatores=fat, q0=0.5 * mu * vp ** 2))
    return out


# ----------------------------------------------------------------------------- casos padrão
CASOS_VENTO_PADRAO = [
    dict(chave="max", nome="Vento máximo (10 min)", TR=50, integracao="10 min", ref="8.2.1 · TR a definir pela transmissora (12.3.3.2)"),
    dict(chave="v5030", nome="Vento 50/30 (faixa de passagem)", TR=50, integracao="30 s", ref="7.1.8.2, 7.3.1.1, 17.2.2.2c · TR ≥ 50 anos"),
    dict(chave="rajada", nome="Vento de rajada (3 s)", TR=150, integracao="3 s", ref="8.2.3 · TR a definir pela transmissora (12.3.3.2)"),
    dict(chave="freq", nome="Frequência industrial", TR=10, integracao="30 s", ref="7.1.8.1, 9.6.2.1a · TR ≥ 10 anos"),
    dict(chave="manobra", nome="Manobra (frente lenta)", TR=2, integracao="30 s", ref="9.6.2.1b · TR ≥ 2 anos"),
]


# ----------------------------------------------------------------------------- orquestração (dados do app)
def _f(x):
    return None if x in (None, "") else float(x)


def montar(d, h_cabo_geo=None):
    """
    d: dict da seção '3' do app. Retorna dict com 'ok', 'pendencias', 'avisos', 'estudo', 'aprovacao', 'pls', 'temps'.
    Nunca inventa dado: o que faltar vira pendência e o item correspondente não é calculado.
    """
    pend, avisos = [], []
    r = dict(ok=False, pendencias=pend, avisos=avisos, estudo=None, aprovacao=[], pls=[], temps={})
    # --- série de vento ---------------------------------------------------
    unid = d.get("unid", "m/s")
    fu = 1 / 3.6 if unid == "km/h" else 1.0
    if d.get("modo", "Série de máximos anuais") == "Série de máximos anuais":
        vals = [float(x["vmax"]) * fu for x in (d.get("serie") or []) if x.get("vmax") not in (None, "") and float(x["vmax"]) > 0]
        if len(vals) < 2:
            pend.append("DADO NÃO INFORMADO — série de máximos anuais de vento (INMET) com ao menos 2 valores.")
            vm = s = n = None
        else:
            vm, s, n = estatisticas_serie(vals)
    else:
        vm, disp, n = _f(d.get("v_med")), _f(d.get("s")), d.get("n")
        if vm and disp:
            s = vm * disp / 100.0 if d.get("tipo_disp", "Desvio-padrão") == "Coeficiente de variação (%)" else disp
            vm, s = vm * fu, s * fu
        else:
            vm = s = None
        if not vm or not s or not n:
            pend.append("DADO NÃO INFORMADO — média, dispersão e número de anos da série de ventos (INMET).")
            vm = s = n = None
    if n is not None and n < 10:
        avisos.append(f"NECESSITA VALIDAÇÃO TÉCNICA — série com {int(n)} anos; a NBR 5422:2024 (4.9.3.2.1) exige no mínimo 10 anos de máximos anuais.")
    # --- conversão da medição (4.9.4.1) ---
    conv = None
    if vm:
        v_c, kint, krug, kalt = converter_medicao(1.0, d.get("integ_med", "10 min"), d.get("cat_est", "B"), float(d.get("z_med", 10.0)))
        fator = v_c
        vm, s = vm * fator, s * fator
        conv = dict(Kint=kint, Krug=krug, Kalt=kalt, fator=fator)
    # --- local e região ---
    uf = d.get("uf")
    regiao = d.get("regiao_manual") or UF_REGIAO.get(uf)
    if not regiao:
        pend.append("DADO NÃO INFORMADO — UF/região geopolítica (define Ktur, Tabela 8).")
    alt = _f(d.get("alt"))
    if alt is None:
        pend.append("DADO NÃO INFORMADO — altitude média do trecho (4.7).")
    # --- temperaturas ---
    t = {}
    if d.get("eds_modo", "Média das 12 médias mensais") == "Média das 12 médias mensais":
        meses = [x.get("t") for x in (d.get("meses") or []) if x.get("t") not in (None, "")]
        t["eds"] = sum(float(x) for x in meses) / len(meses) if len(meses) == 12 else None
        if t["eds"] is None:
            pend.append("DADO NÃO INFORMADO — as 12 temperaturas médias mensais (INMET) para o EDS.")
    else:
        t["eds"] = _f(d.get("t_media"))
        if t["eds"] is None:
            pend.append("DADO NÃO INFORMADO — temperatura média (EDS).")
    for k, nome in (("t_max", "temperatura máxima (2 % de excedência anual, 3.1.52)"),
                    ("t_min", "temperatura mínima (2 % de ocorrência anual, 3.1.55)"),
                    ("t_coinc", "temperatura coincidente — média das mínimas diárias (3.1.49)"),
                    ("t_med_max", "temperatura média das máximas anuais (7.3.1.1)")):
        t[k] = _f(d.get(k))
        if t[k] is None:
            pend.append(f"DADO NÃO INFORMADO — {nome}.")
    r["temps"] = t
    # --- altura do cabo ---
    h = _f(d.get("h_cabo")) if not d.get("usar_h_geo", True) else h_cabo_geo
    if h is None:
        h = _f(d.get("h_cabo"))
    if h is None or h <= 0:
        pend.append("DADO NÃO INFORMADO — altura média do cabo (Kalt, 8.2.2.1).")
    # --- cálculo ---
    if vm and regiao and alt is not None and h and t["t_coinc"] is not None:
        casos = [dict(c, TR=float(d.get(f"tr_{c['chave']}", c["TR"]))) for c in CASOS_VENTO_PADRAO]
        if d.get("tr_ext"):
            casos.append(dict(chave="ext", nome="Vento extremo (opcional)", TR=float(d["tr_ext"]), integracao="10 min",
                              ref="critério do cliente"))
        for c in casos:
            if c["chave"] == "v5030" and c["TR"] < 50:
                avisos.append("NECESSITA VALIDAÇÃO TÉCNICA — TR do vento 50/30 abaixo de 50 anos (7.1.8.2/7.3.1.1).")
            if c["chave"] == "freq" and c["TR"] < 10:
                avisos.append("NECESSITA VALIDAÇÃO TÉCNICA — TR de frequência industrial abaixo de 10 anos (9.6.2.1a).")
            if c["chave"] == "manobra" and c["TR"] < 2:
                avisos.append("NECESSITA VALIDAÇÃO TÉCNICA — TR de manobra abaixo de 2 anos (9.6.2.1b).")
        est = estudo(dict(v_med=vm, s=s, n=int(n), regiao=regiao, cat=d.get("cat", "B"), h_cabo=h, alt=alt,
                          t_coinc=t["t_coinc"], casos=casos))
        est["conv"], est["regiao"], est["cat"], est["h_cabo"], est["alt"] = conv, regiao, d.get("cat", "B"), h, alt
        r["estudo"], r["ok"] = est, True
        v = {c["chave"]: c for c in est["casos"]}
        fonte_v = "INMET (série) + NBR 5422:2024"
        def linha(item, val, un, base, fonte):
            r["aprovacao"].append(dict(item=item, valor=val, unidade=un, base=base, fonte=fonte))
        linha("VENTO MÁX (10 min)", v["max"]["VP"], "m/s", f"8.2.1.1 · TR {v['max']['TR']:g} anos", fonte_v)
        linha("VENTO 50/30", v["v5030"]["VP"], "m/s", f"8.2.2.1 · TR {v['v5030']['TR']:g} anos, 30 s", fonte_v)
        linha("VENTO RAJADA (3 s)", v["rajada"]["VP"], "m/s", f"8.2.3.4 · TR {v['rajada']['TR']:g} anos", fonte_v)
        linha("FREQUÊNCIA INDUSTRIAL", v["freq"]["VP"], "m/s", f"9.6.2.1a · TR {v['freq']['TR']:g} anos, 30 s", fonte_v)
        linha("MANOBRA", v["manobra"]["VP"], "m/s", f"9.6.2.1b · TR {v['manobra']['TR']:g} anos, 30 s", fonte_v)
    # temperaturas entram no quadro mesmo sem vento
    for nome, k, base in (("EDS (temperatura média)", "eds", "3.1.54, 4.3.1"), ("T MÁX", "t_max", "3.1.52"),
                          ("T MÍN", "t_min", "3.1.55"), ("T COINCIDENTE (média das mínimas)", "t_coinc", "3.1.49, 11.2.4"),
                          ("T MÉDIA DAS MÁXIMAS ANUAIS", "t_med_max", "7.3.1.1")):
        r["aprovacao"].append(dict(item=nome, valor=t[k], unidade="°C", base=base,
                                   fonte="INMET" if t[k] is not None else "DADO NÃO INFORMADO"))
    # --- tabela de casos para o PLS-CADD ---
    if r["ok"]:
        q = est["mu"] / 2.0
        v = {c["chave"]: c["VP"] for c in est["casos"]}
        tc, tm = t["t_coinc"], t["t_min"]
        tcc = _f(d.get("t_cc_max", 75.0)); tem = _f(d.get("t_cc_emerg", 90.0)); tpr = _f(d.get("t_pr_max", 40.0))
        linhas = [("EDS", 0.0, t["eds"], t["eds"], "None"),
                  ("V. Máximo (10 min)", v["max"], tc, tc, "IEC"),
                  ("V. Máximo 50/30", v["v5030"], tc, tc, "None"),
                  ("V. Rajada CC (3 s)", v["rajada"], tc, tc, "None"),
                  ("V. Rajada PR (3 s)", v["rajada"], tc, tc, "None"),
                  ("Temp. mínima", 0.0, tm, tm, "None"),
                  ("Temp. máx. CC", 0.0, tcc, t["t_max"], "None"),
                  ("Temp. emergência CC", 0.0, tem, t["t_max"], "None"),
                  ("Temp. máx. PR", 0.0, tpr, t["t_max"], "None"),
                  ("Temp. coincidente", 0.0, tc, tc, "None"),
                  ("Faixa de segurança (50/30)", v["v5030"], t["t_med_max"], t["t_med_max"], "None"),
                  ("Balanço freq. industrial", v["freq"], tc, tc, "None"),
                  ("Balanço manobra", v["manobra"], tc, tc, "None")]
        if "ext" in v:
            linhas.insert(1, ("V. Extremo (10 min)", v["ext"], tc, tc, "IEC"))
        if d.get("usar_reduzido"):
            linhas.append(("V. Reduzido 60 % (origem a confirmar)", 0.6 * v["max"], tc, tc, "IEC"))
        for i, (nome, vel, tfio, tamb, mod) in enumerate(linhas, start=1):
            r["pls"].append({"Row #": i, "Description": nome, "Air Density Factor (Q) (kg/m^3)": round(q, 4),
                             "Wind Velocity (m/s)": round(vel, 2), "Wind Pressure (Pa)": round(q * vel ** 2, 1),
                             "Wire Ice Thickness (cm)": 0.0, "Wire Ice Density (daN/dm^3)": 0.0, "Wire Ice Load (daN/m)": 0.0,
                             "Wire Temp. (deg C)": None if tfio is None else round(tfio, 1),
                             "Ambient Temp. (deg C)": None if tamb is None else round(tamb, 1),
                             "Weather Load Factor": 1.0, "NESC Constant (daN/m)": 0.0, "Wire Wind Height Adjust Model": mod})
        avisos.append("NECESSITA VALIDAÇÃO TÉCNICA — Q = μ/2 (pressão = Q·V²). A planilha de referência usa μ nessa coluna; confirmar a convenção no PLS-CADD.")
    return r
