"""
Módulo 10 – Gradiente superficial, rádio-interferência (RI) e ruído audível (RA) – funções puras (sem Streamlit).

Fontes (acervo do projeto):
  • Gradiente: Kiessling et al., 'Overhead Power Lines', 2.3.3 (eq. 2.12 a 2.23, Tabela 2.7): cargas pelos coeficientes de potencial
    e fator de feixe E_i = Q_i / (2π ε0 n r) · (1 + k2·r/s), com k2 = 2(n−1)·sen(π/n). Conferência: eq. 2.22 (gradiente médio) → 17,2 kV/cm
    no exemplo de 420 kV (feixe duplo 562-AL1/49, s = 400 mm).
  • RI, método 1 (tempo bom, 1 MHz): Kiessling eq. 2.24 a 2.26:  NF_i = 3,5·E_i + 12·r_i − 33·log10(D_i/20) − 30  [dB acima de 1 µV/m],
    E_i em kV/cm, r_i = raio do subcondutor em cm, D_i = distância condutor–ponto em m; soma pela regra de 3 dB (eq. 2.25).
  • RI, método 2 (FG alemão, Villas 'Transmissão de Energia' 8.3.2.1, eq. 7 a 9, também no Livro 3):
        E = 53,7 + K(g_m − 16,95) + 40·log10(d/3,93) + E_n + 20·K_D·log10(20/D) + E_FW
    K = 3,5; E_n = −4 dB (n = 1) ou 10·log10(n/4); K_D = 1,6; E_FW = 0 (tempo bom) ou 17 dB (chuva); d em cm. Valor de 50 % de probabilidade (±5 dB).
  • RA (chuva/tempo úmido): Kiessling eq. 2.27 a 2.29 (Chartier & Stearns / BPA):
        NPA_i = −164,6 + 120·log10(E_i) + 55·log10(r_e),  r_e = d (n < 3) ou 0,58·n^0,48·d (n ≥ 3)  [d = diâmetro do subcondutor em mm]
        NPA = 10·log10 Σ exp[0,23·(NPA_i − 11,4·log10(D_i) − 5,8)]
  • Gradiente crítico visual (Peek): E_v = 21,1·m·δ·(1 + 0,301/√(δ·r)) kV_ef/cm (r em cm). NECESSITA VALIDAÇÃO: constantes de Peek
    conforme formulação usual; conferir com o Livro 3 (Cálculos Elétricos de LTs, cap. 7).
Premissas: condutores em altura mínima (condição conservadora); tensão máxima operativa; cabos guarda aterrados incluídos por padrão
(aumentam o gradiente); linhas vizinhas NÃO são consideradas no RI/RA (dados de condutor não cadastrados) – PENDENTE.
"""
import math

import numpy as np

import calc_campos as cc

EPS0 = cc.EPS0


# --------------------------------------------------------------------------- feixe
def r_feixe(n, s):
    """Raio do círculo do feixe R = s / (2·sen(π/n)) (n ≥ 2); n = 1 → 0."""
    return 0.0 if n < 2 else s / (2.0 * math.sin(math.pi / n))


def k1_feixe(n):
    """k1 da Tabela 2.7: r_B = r·(k1·s/r)^((n−1)/n)  ⇒  k1 = n^(1/(n−1)) / (2·sen(π/n))."""
    return 1.0 if n < 2 else n ** (1.0 / (n - 1)) / (2.0 * math.sin(math.pi / n))


def k2_feixe(n):
    """k2 = 2(n−1)·sen(π/n) (Tabela 2.7); n = 1 → 0."""
    return 0.0 if n < 2 else 2.0 * (n - 1) * math.sin(math.pi / n)


def fator_feixe(n, r, s):
    """1 + k2·r/s (eq. 2.15–2.17): relação entre o gradiente máximo no subcondutor e o médio no feixe."""
    return 1.0 if n < 2 else 1.0 + k2_feixe(n) * r / s


def gradiente_medio_kiessling(un_kv, n, r_cm, s_cm, dm, hm):
    """Eq. 2.22 (circuito simples, kV_ef/cm): gradiente médio. dm = distância média entre fases (m); hm = altura média (m)."""
    r_b = r_cm / 100.0 * (k1_feixe(n) * s_cm / r_cm) ** ((n - 1.0) / n) if n > 1 else r_cm / 100.0
    fator = fator_feixe(n, r_cm, s_cm)
    den = n * r_cm * math.log(dm / (r_b * math.sqrt(1.0 + (dm / (2.0 * hm)) ** 2)))
    return fator / den * un_kv / math.sqrt(3.0)


# --------------------------------------------------------------------------- gradiente por simulação de cargas
def gradientes_fases(est, cabos):
    """est: condutores (de calc_campos.monta_estudo; fases com V, guardas com V = 0).
    cabos: {circuito: dict(n, d_mm, s_mm)}. Retorna lista dict(nome, circuito, fase, E [kV_ef/cm], Q) para as fases."""
    xs = np.array([c["x"] for c in est]); ys = np.array([c["y"] for c in est]); rq = np.array([c["req"] for c in est])
    V = np.array([c.get("V", 0.0) for c in est], complex)
    Q = np.linalg.solve(cc.matriz_potencial(xs, ys, rq), V)
    out = []
    for c, q in zip(est, Q):
        if c.get("tipo") != "fase":
            continue
        cab = cabos[c["circuito"]]
        n, r, s = int(cab["n"]), cab["d_mm"] / 2000.0, cab["s_mm"] / 1000.0
        e = abs(q) / (2 * math.pi * EPS0 * n * r) * fator_feixe(n, r, s)          # V/m
        out.append(dict(nome=c["nome"], circuito=c["circuito"], fase=c["fase"], x=float(c["x"]), y=float(c["y"]), E=float(e / 1e5),
                        n=n, r_cm=r * 100.0, d_mm=cab["d_mm"], s_mm=cab["s_mm"]))
    return out


def delta_ar(alt_m, temp_c):
    """Densidade relativa do ar (Peek): p = 76·10^(−h/18336) cmHg; δ = 3,92·p/(273+t)."""
    p = 76.0 * 10 ** (-alt_m / 18336.0)
    return 3.92 * p / (273.0 + temp_c)


def gradiente_critico_peek(r_cm, delta, m=0.85):
    """Gradiente crítico visual de Peek (kV_ef/cm) para condutor liso/encordoado de raio r (cm); m = fator de superfície."""
    return 21.1 * m * delta * (1.0 + 0.301 / math.sqrt(delta * r_cm))


# --------------------------------------------------------------------------- RI
def ri_kiessling_fase(E, r_cm, D):
    """Eq. 2.24: nível de RI da fase (dB acima de 1 µV/m), tempo bom, 1 MHz."""
    return 3.5 * E + 12.0 * r_cm - 33.0 * math.log10(D / 20.0) - 30.0


def ri_fg_fase(E, d_cm, n, D, chuva=False, kd=1.6):
    """Método FG (eq. 8 do Villas): dB acima de 1 µV/m (valor de 50 %). E = gradiente máximo (kV_ef/cm), d = diâmetro do subcondutor (cm)."""
    en = -4.0 if n <= 1 else 10.0 * math.log10(n / 4.0)
    return (53.7 + 3.5 * (E - 16.95) + 40.0 * math.log10(d_cm / 3.93) + en + 20.0 * kd * math.log10(20.0 / D)
            + (17.0 if chuva else 0.0))


def combina_ri(niveis):
    """Eq. 2.25 / (9): se o maior supera o 2º em ≥ 3 dB vale o maior; senão (N1+N2)/2 + 1,5 (N1, N2 = dois maiores)."""
    s = sorted(niveis, reverse=True)
    if len(s) == 1 or s[0] - s[1] >= 3.0:
        return s[0]
    return (s[0] + s[1]) / 2.0 + 1.5


def soma_quadratica_db(niveis):
    """Soma quadrática de campos (µV/m) de níveis em dB: 20·log10 √Σ 10^(N/10)."""
    return 10.0 * math.log10(sum(10 ** (n / 10.0) for n in niveis))


def ri_ponto(gr, x, h_obs, chuva=False, metodo="kiessling"):
    """RI total (dB µV/m) no ponto (x, h_obs). Circuitos múltiplos: fases homólogas somadas quadraticamente, depois eq. 2.25."""
    por_fase = {}
    for g in gr:
        D = max(math.hypot(x - g["x"], h_obs - g["y"]), 1.0)
        nf = (ri_kiessling_fase(g["E"], g["r_cm"], D) if metodo == "kiessling"
              else ri_fg_fase(g["E"], g["d_mm"] / 10.0, g["n"], D, chuva))
        por_fase.setdefault(g["fase"], []).append(nf)
    return combina_ri([soma_quadratica_db(v) if len(v) > 1 else v[0] for v in por_fase.values()])


# --------------------------------------------------------------------------- RA
def r_equivalente_ra(n, d_mm):
    """Eq. 2.28 (d = diâmetro do subcondutor em mm): re = d (n < 3); re = 0,58·n^0,48·d (n ≥ 3)."""
    return d_mm if n < 3 else 0.58 * n ** 0.48 * d_mm


def npa_fase(E, n, d_mm):
    """Eq. 2.27: potencial de ruído da fase, dB(A)."""
    return -164.6 + 120.0 * math.log10(E) + 55.0 * math.log10(r_equivalente_ra(n, d_mm))


def ra_ponto(gr, x, h_obs):
    """Eq. 2.29: nível de ruído audível (dB(A)) no ponto (x, h_obs), somando todas as fases."""
    tot = 0.0
    for g in gr:
        D = max(math.hypot(x - g["x"], h_obs - g["y"]), 1.0)
        tot += math.exp(0.23 * (npa_fase(g["E"], g["n"], g["d_mm"]) - 11.4 * math.log10(D) - 5.8))
    return 10.0 * math.log10(tot)


# --------------------------------------------------------------------------- estudo completo
def calcular_estudo(e):
    """e (JSON-serializável): fases, guardas, incluir_guardas, circs {id: dict(umax_kv, status, n, d_mm, s_mm)}, h_min, h_obs, x_max, dx,
    semi_faixa, alt, temp, m_rug, chuva, lim_ri, lim_ra, pontos [dict(nome, tipo, dist_h, alt_ref, vizinhas)]."""
    erros, avisos = [], []
    if not e.get("fases"):
        return dict(erros=["Geometria sem fases: preencha o Módulo 2 / seção transversal."], avisos=[], pontos=[])
    circs = {}
    for k, c in e["circs"].items():
        if not c.get("umax_kv"):
            erros.append(f"Tensão máxima do circuito {k} não informada.")
        circs[int(k)] = dict(un_kv=c["umax_kv"], i_a=0.0, fp=1.0, status=c["status"])
    if erros:
        return dict(erros=erros, avisos=[], pontos=[])
    est = cc.monta_estudo(e["fases"], circs, e["guardas"], e["incluir_guardas"], e.get("h_min"))
    cabos = {int(k): dict(n=c["n"], d_mm=c["d_mm"], s_mm=c["s_mm"]) for k, c in e["circs"].items()}
    gr = gradientes_fases(est, cabos)
    if not gr:
        return dict(erros=["Nenhum circuito energizado para o cálculo."], avisos=[], pontos=[])
    delta = delta_ar(e["alt"], e["temp"])
    peek = {}
    for k, c in cabos.items():
        peek[k] = gradiente_critico_peek(c["d_mm"] / 20.0, delta, e["m_rug"])
    for g in gr:
        g["E_visual"] = peek[g["circuito"]]
        g["E_rel"] = g["E"] / g["E_visual"]
    gmax = max(g["E"] for g in gr)
    if gmax > 17.0:
        avisos.append(f"Gradiente máximo {gmax:.1f} kV/cm acima da referência prática de ~17 kV_ef/cm (Kiessling 2.3.3.1): "
                      "esperar RI/RA elevados.")
    if any(p["vizinhas"] for p in e["pontos"]):
        avisos.append("Linhas vizinhas não são consideradas no RI/RA (dados de condutor não cadastrados) – PENDENTE.")
    xs = np.arange(-e["x_max"], e["x_max"] + e["dx"] / 2, e["dx"])
    prof = dict(x=xs.tolist(),
                RI_K=[ri_ponto(gr, float(x), e["h_obs"]) for x in xs],
                RI_FG=[ri_ponto(gr, float(x), e["h_obs"], e["chuva"], "fg") for x in xs],
                RA=[ra_ponto(gr, float(x), e["h_obs"]) for x in xs])
    pts = []
    for p in e["pontos"]:
        puntual = p["tipo"] == "Edificação/residência"
        h = float(p["alt_ref"]) if puntual and p["alt_ref"] > 0 else float(e["h_obs"])
        if puntual:
            xs_p = [abs(p["dist_h"]), -abs(p["dist_h"])]
        elif e.get("semi_faixa"):
            xs_p = [e["semi_faixa"], -e["semi_faixa"]]
        else:
            xs_p = []
        r = dict(nome=p["nome"], tipo=p["tipo"], h_obs=h, vizinhas=[v["nome"] for v in p["vizinhas"]], x_aval=xs_p)
        if xs_p:
            ri_k = [ri_ponto(gr, x, h) for x in xs_p]
            ri_f = [ri_ponto(gr, x, h, e["chuva"], "fg") for x in xs_p]
            ra = [ra_ponto(gr, x, h) for x in xs_p]
            r.update(RI_K=float(max(ri_k)), RI_FG=float(max(ri_f)), RA=float(max(ra)), x_pior=xs_p[int(np.argmax([max(a, b) for a, b in zip(ri_k, ri_f)]))])
            ri_gov = max(r["RI_FG"], r["RI_K"]) if not e["chuva"] else r["RI_FG"]
            r.update(RI_gov=ri_gov, ok_RI=ri_gov <= e["lim_ri"] + 1e-9, ok_RA=r["RA"] <= e["lim_ra"] + 1e-9)
        else:
            avisos.append(f"{p['nome']}: faixa não definida (Módulo 4) – RI/RA na borda não avaliados.")
        pts.append(r)
    return dict(erros=erros, avisos=avisos, gradientes=gr, delta=delta, perfil=prof, pontos=pts, lim_ri=e["lim_ri"], lim_ra=e["lim_ra"],
                chuva=e["chuva"], h_obs=e["h_obs"], semi_faixa=e.get("semi_faixa"), incluir_guardas=e["incluir_guardas"],
                alt=e["alt"], temp=e["temp"], m_rug=e["m_rug"], circs=e["circs"], h_min=e.get("h_min"), fases=e["fases"],
                guardas=e["guardas"], modo_lim_ri=e.get("modo_lim_ri", ""))
