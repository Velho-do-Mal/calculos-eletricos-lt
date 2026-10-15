"""
Módulo 7 – Dimensionamento ELÉTRICO do condutor e do cabo guarda (não mecânico).

Critérios (reproduzem e corrigem a planilha BK "LINHA DE TRANSMISSÃO 4.xlsm"):
  1. Máxima corrente   : I = P / (√3·U·cosφ)
  2. Perda joule máxima: 3·R'·L·I² ≤ (p/100)·P                       (a planilha mistura unidades – ver NOTAS_PLANILHA)
  3. Queda de tensão   : √3·I·L·(R'·cosφ + X'·senφ) ≤ ΔV·U
  4. Ampacidade        : ONS (NT Sazonal de LTs) e IEEE Std 738-2006 (regime permanente)
  5. Curto-circuito    : S ≥ Icc·√t / k   (IEC 60949, adiabático); OPGW: Icc²·t ≤ capacidade do fabricante (kA²·s)
  Resistência com a temperatura: R(T) = R20·[1 + α·(T − 20)]

Unidades: A, kV, kW, km, Ω/km, mm², °C, m/s, W/m².
"""
import math

SIGMA = 5.67e-8
RHO_AL20 = 28.264          # Ω·mm²/km (IEC 60949; alumínio a 20 °C)

# Estados com vento de 0,9 m/s (aba "Ampacidade - ONS" da planilha BK)
UF_VENTO_09 = {"PR", "RS", "SC", "RJ", "ES", "SE", "AL"}

# IEC 60949: Qc [J/(K·mm³)], β [K], ρ20 [Ω·mm]
IEC60949 = {"Alumínio": (2.5e-3, 228.0, 28.264e-6), "Aço": (3.8e-3, 202.0, 138.0e-6), "Cobre": (3.45e-3, 234.5, 17.241e-6)}

NOTAS_PLANILHA = [
    "Perda máxima: a planilha calcula R = (p·P)/(√3·L·I²) com p em % (sem dividir por 100), P em kW e √3 no lugar de 3; "
    "a forma física é R = p·P/(100·3·L·I²), com P em W.",
    "Queda de tensão: a expressão da planilha ((1/U)·I·L)/(ΔV·U/√3) não é dimensionalmente consistente; "
    "aqui usa-se ΔV = √3·I·L·(R·cosφ + X·senφ).",
    "Segurança térmica: a fórmula da planilha (precedência '^1/3' e constante k) não tem base normativa identificada; "
    "substituída pelo critério adiabático da IEC 60949.",
    "IEEE 738 (ERRO na planilha): a perda por radiação qr (F9) multiplica pela DENSIDADE DO AR (C21 = 1,076) no lugar da "
    "emissividade (C9 = 0,5), o que subestima a radiação e superestima a ampacidade (586,99 A contra ≈ 517 A com os mesmos dados); "
    "além disso usa A' = 0,0257 m²/m fixo (a área projetada é o diâmetro do cabo, em m²/m) e o qcn de F4 usa (D − ρ) em vez de "
    "(Tc − Ta) – o qcn não entra no resultado (máx. de qc1, qc2).",
    "ONS: não considera evaporação, efeito magnético nem corona (indicado na própria aba).",
]


def r_temp(r20, alfa, t):
    """R(T) = R20·[1 + α·(T − 20)] (Ω/km)."""
    return r20 * (1.0 + alfa * (t - 20.0))


# --------------------------------------------------------------------------- critérios básicos
def corrente_nominal(p_kw, u_kv, cosphi):
    return p_kw / (math.sqrt(3) * u_kv * cosphi)


def criterios_basicos(p_kw, u_kv, cosphi, comp_km, perda_pct, dv_pct, n_sub=1, x_km=0.0, i_a=None, t_op=75.0):
    """Retorna as resistências máximas (Ω/km, POR CABO) e a seção mínima por queda de tensão.
    n_sub: subcondutores por fase; x_km: reatância indutiva da fase (Ω/km, vem do Módulo 2); i_a: corrente de projeto."""
    i = i_a if i_a else corrente_nominal(p_kw, u_kv, cosphi)
    sinphi = math.sqrt(max(0.0, 1.0 - cosphi ** 2))
    # perda: 3·R_fase·L·I² ≤ p/100·P
    r_perda_fase = (perda_pct / 100.0) * p_kw * 1000.0 / (3.0 * comp_km * i ** 2)
    # queda de tensão: √3·I·L·(R·cosφ + X·senφ) ≤ ΔV·U
    lim = dv_pct / 100.0 * u_kv * 1000.0 / (math.sqrt(3) * i * comp_km)
    r_dv_fase = max(0.0, (lim - x_km * sinphi) / cosphi)
    out = dict(i=i, r_perda_fase=r_perda_fase, r_dv_fase=r_dv_fase,
               r_perda_cabo=r_perda_fase * n_sub, r_dv_cabo=r_dv_fase * n_sub)
    out["r_max_cabo"] = min(out["r_perda_cabo"], out["r_dv_cabo"])
    # seção equivalente em alumínio à temperatura de operação (alfa 0,004): S = ρ(T)/R
    out["s_min_mm2"] = RHO_AL20 * (1.0 + 0.004 * (t_op - 20.0)) / out["r_max_cabo"]
    return out


def verificar_cabo(cabo, crit, n_sub=1, t_op=75.0, i_amp=None):
    """Aplica os critérios 1–3 a um cabo do catálogo.  cabo: dict de db.obter_cabo.  Retorna dict com status por critério."""
    r20, al = cabo.get("r_cc_20"), cabo.get("alfa_20c") or 0.004
    out = dict(codigo=cabo["codigo"], r_op=None, ok_perda=None, ok_dv=None, ok_i=None)
    if r20:
        r_op = r_temp(r20, al, t_op)
        out["r_op"] = r_op
        out["ok_perda"] = r_op <= crit["r_perda_cabo"]
        out["ok_dv"] = r_op <= crit["r_dv_cabo"]
    amp = i_amp if i_amp is not None else cabo.get("ampacidade_a")
    if amp:
        out["amp_a"] = amp
        out["ok_i"] = amp * n_sub >= crit["i"]
    return out


# --------------------------------------------------------------------------- ONS (NT Sazonal de LTs)
def _nu_coefs(rr, re):
    """Constantes B2 e m2 do número de Nusselt (aba 'Constantes' da planilha, NT ONS).  Retorna (B2, m2, aviso|None)."""
    if 0.05 < rr < 0.718 and 100 < re < 2650:
        return 0.641, 0.471, None
    if rr < 0.05 and 2650 < re < 50000:
        return 0.178, 0.633, None
    if 0.05 < rr < 0.718 and 2650 < re < 50000:
        return 0.048, 0.8, None
    aviso = (f"Re = {re:.0f} / RR = {rr:.3f} fora das faixas da NT do ONS (RR>0,05 e 100<Re<2650; RR<0,05 e 2650<Re<50000; "
             "RR>0,05 e 2650<Re<50000): adotadas as constantes da faixa mais próxima – NECESSITA VALIDAÇÃO TÉCNICA.")
    if re < 2650:
        return 0.641, 0.471, aviso
    return (0.048, 0.8, aviso) if rr > 0.05 else (0.178, 0.633, aviso)


def ampacidade_ons(d_mm, d_fio_mm, r20, alfa, u_kv, alt_m=0.0, emis=0.5, absort=0.5, t_norm=75.0, t_emerg=90.0,
                   ta=None, vento=1.0, rad=1000.0, vento_noite=None):
    """Ampacidade pela NT Sazonal de LTs do ONS (reproduz a aba 'Ampacidade - ONS').
    ta: dict(verao_dia, verao_noite, inverno_dia, inverno_noite) em °C.
    Retorna dict(linhas=[...], avisos=[...]) com A e MVA por época/período em condição normal e de emergência."""
    ta = ta or dict(verao_dia=33.0, verao_noite=25.0, inverno_dia=32.0, inverno_noite=24.0)
    vn = vento if vento_noite is None else vento_noite
    D = d_mm / 1000.0
    dfio = d_fio_mm / 1000.0
    rr = dfio / (2.0 * (D - 2.0 * dfio))
    dra = math.exp(-1.16e-4 * alt_m)
    avisos = []
    linhas = []
    for epoca, periodo, chave in (("Verão", "Dia", "verao_dia"), ("Verão", "Noite", "verao_noite"),
                                  ("Inverno", "Dia", "inverno_dia"), ("Inverno", "Noite", "inverno_noite")):
        dia = periodo == "Dia"
        v = vento if dia else vn
        row = dict(epoca=epoca, periodo=periodo, ta=ta[chave])
        for cond, tc in (("normal", t_norm), ("emergencia", t_emerg)):
            tck, tak = tc + 273.15, ta[chave] + 273.15
            tf = (tck + tak) / 2.0
            vf = 1.32e-5 + 9.5e-8 * tf                         # viscosidade cinemática
            re = D * v * dra / vf
            b2, m2, av = _nu_coefs(rr, re)
            if av and av not in avisos:
                avisos.append(av)
            nu = b2 * re ** m2
            lam = 2.42e-2 + 7.2e-5 * tf
            qc = math.pi * lam * nu * (tck - tak)
            qr = math.pi * D * emis * SIGMA * (tck ** 4 - tak ** 4)
            qs = rad * absort * D if dia else 0.0
            r = r_temp(r20, alfa, tc)
            q = max(qc + qr - qs, 0.0)
            i = math.sqrt(q * 1e3 / r)
            mva = i * u_kv * math.sqrt(3) / 1000.0
            row[cond] = dict(tc=tc, r=r, qc=qc, qr=qr, qs=qs, re=re, nu=nu, i=i, mva=mva)
        linhas.append(row)
    return dict(linhas=linhas, avisos=avisos, rr=rr, dra=dra)


# --------------------------------------------------------------------------- IEEE 738-2006
def _propriedades_ar(t_film, alt_m):
    mu = 1.458e-6 * (t_film + 273.0) ** 1.5 / (t_film + 383.4)                       # Pa·s (eq. 13a)
    rho = (1.293 - 1.525e-4 * alt_m + 6.379e-9 * alt_m ** 2) / (1.0 + 0.00367 * t_film)  # kg/m³ (eq. 14a)
    k = 2.424e-2 + 7.477e-5 * t_film - 4.407e-9 * t_film ** 2                          # W/(m·°C) (eq. 15a)
    return mu, rho, k


def ampacidade_ieee738(d_mm, r_tc, ta, tc, alt_m=0.0, emis=0.5, absort=0.5, vento=0.61, ang_vento_deg=90.0,
                       rad=1000.0, ang_sol_deg=90.0, area_proj=None, props=None):
    """IEEE Std 738-2006, regime permanente (eq. 2a, 3a/3b, 4a, 6a/6b/6c, 7a).
    r_tc: resistência em Tc (Ω/km); props: (mu, rho, k) para forçar valores de tabela; area_proj: A' (m²/m, default D em m).
    Retorna dict(i, qc, qr, qs, qc1, qc2, qcn)."""
    t_film = (tc + ta) / 2.0
    mu, rho, kf = props if props else _propriedades_ar(t_film, alt_m)
    phi = math.radians(ang_vento_deg)
    k_ang = 1.194 - math.cos(phi) + 0.194 * math.cos(2 * phi) + 0.368 * math.sin(2 * phi)
    nre = d_mm * rho * vento / mu                         # D em mm (IEEE 738)
    dt = tc - ta
    qc1 = (1.01 + 0.0372 * nre ** 0.52) * kf * k_ang * dt
    qc2 = 0.0119 * nre ** 0.6 * kf * k_ang * dt
    qcn = 0.0205 * rho ** 0.5 * d_mm ** 0.75 * dt ** 1.25
    qc = max(qc1, qc2, qcn)
    qr = 0.0178 * d_mm * emis * (((tc + 273.0) / 100.0) ** 4 - ((ta + 273.0) / 100.0) ** 4)
    a = area_proj if area_proj else d_mm / 1000.0
    qs = absort * rad * math.sin(math.radians(ang_sol_deg)) * a
    i = math.sqrt(max(qc + qr - qs, 0.0) / (r_tc / 1000.0))
    return dict(i=i, qc=qc, qr=qr, qs=qs, qc1=qc1, qc2=qc2, qcn=qcn, nre=nre, t_film=t_film, mu=mu, rho=rho, kf=kf)


def temperatura_equilibrio(i, d_mm, r20, alfa, ta, alt_m=0.0, emis=0.5, absort=0.5, vento=0.61, rad=1000.0, **kw):
    """Tc (°C) em que a ampacidade IEEE 738 iguala a corrente i (bisseção, 30–250 °C)."""
    lo, hi = ta + 0.5, 250.0
    f = lambda tc: ampacidade_ieee738(d_mm, r_temp(r20, alfa, tc), ta, tc, alt_m, emis, absort, vento, rad=rad, **kw)["i"] - i
    if f(hi) < 0:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return (lo + hi) / 2


# --------------------------------------------------------------------------- perdas na linha
def perdas_joule(i_a, r_km, comp_km, p_mw=None, n_fases=3, fator_cat=0.0):
    """Perdas joule (MW) = n·R·L·(1+fc)·I².  Retorna (MW, % de p_mw)."""
    l_corr = comp_km * (1.0 + fator_cat)
    mw = n_fases * (i_a ** 2) * r_km * l_corr / 1e6
    return mw, (100.0 * mw / p_mw if p_mw else None)


# --------------------------------------------------------------------------- curto-circuito
def k_iec60949(material, theta_i, theta_f):
    qc, beta, rho20 = IEC60949[material]
    return math.sqrt(qc * (beta + 20.0) / rho20 * math.log((beta + theta_f) / (beta + theta_i)))


def secao_min_curto(icc_ka, t_s, material, theta_i, theta_f, fracao=1.0):
    """S_min (mm²) = Icc·√t / k (IEC 60949, adiabático).  fracao: parcela da corrente de falta que circula no cabo."""
    k = k_iec60949(material, theta_i, theta_f)
    return fracao * icc_ka * 1000.0 * math.sqrt(t_s) / k, k


def verificar_guarda(cabo, icc_ka, t_s, theta_i=40.0, theta_f=200.0, fracao=1.0, material=None):
    """Verifica o cabo guarda quanto ao curto-circuito.  Se o catálogo tem capacidade em kA²·s (OPGW), usa-a;
    caso contrário usa a IEC 60949 sobre a seção total (material: 'Aço' para EHS/AÇO, senão 'Alumínio' – conservador a validar)."""
    i2t = (fracao * icc_ka) ** 2 * t_s
    out = dict(codigo=cabo["codigo"], i2t=i2t, metodo=None, ok=None, avisos=[])
    cap = cabo.get("curto_ka_s")
    if cap:
        out.update(metodo="Capacidade do fabricante (kA²·s)", capacidade=cap, ok=cap >= i2t, margem=cap / i2t if i2t else None)
        return out
    sec = cabo.get("secao_mm2")
    if not sec:
        out["avisos"].append("Sem seção nem capacidade de curto no catálogo – DADO NÃO INFORMADO.")
        return out
    mat = material or ("Aço" if "AÇO" in (cabo.get("tipo") or "").upper() or "EHS" in (cabo.get("codigo") or "").upper() else "Alumínio")
    smin, k = secao_min_curto(icc_ka, t_s, mat, theta_i, theta_f, fracao)
    out.update(metodo=f"IEC 60949 ({mat}, {theta_i:g}→{theta_f:g} °C)", k=k, s_min=smin, secao=sec, ok=sec >= smin, margem=sec / smin)
    out["avisos"].append("Capacidade calculada pela seção total; para cabos mistos (ACSR/AACSR) confirmar a composição – NECESSITA VALIDAÇÃO TÉCNICA.")
    return out


# --------------------------------------------------------------------------- pacote principal do Módulo 7
def calcular(e, cabo, guardas, candidatos):
    """e: entrada (dict); cabo: dict do condutor selecionado ({} se nenhum); guardas: lista de dicts de cabos guarda;
    candidatos: lista de dicts de condutores do catálogo.  Retorna dict com 'erros', 'avisos' e resultados."""
    r = dict(erros=[], avisos=[])
    if not e.get("p_kw") or not e.get("u_kv") or not e.get("comp_km"):
        r["erros"].append("Informe potência, tensão e comprimento da LT.")
        return r
    n = int(e.get("n_sub", 1))
    crit = criterios_basicos(e["p_kw"], e["u_kv"], e["cosphi"], e["comp_km"], e["perda_pct"], e["dv_pct"], n,
                             e.get("x_km", 0.0), t_op=e["t_norm"])
    r["crit"] = crit
    # candidatos: ampacidade por IEEE 738 só quando o catálogo traz diâmetro e resistência
    cands = []
    for c in candidatos:
        v = verificar_cabo(c, crit, n, e["t_norm"])
        v.update(secao=c.get("secao_mm2"), diam=c.get("diametro_mm"), tipo=c.get("tipo"))
        v["ok"] = all(x for x in (v["ok_perda"], v["ok_dv"], v["ok_i"]) if x is not None) and v["r_op"] is not None
        cands.append(v)
    cands.sort(key=lambda v: (not v["ok"], v.get("secao") or 1e9))
    r["candidatos"] = cands
    if cabo:
        r["cabo"] = verificar_cabo(cabo, crit, n, e["t_norm"])
        r["perdas"] = None
        if r["cabo"]["r_op"]:
            # R da fase = R_cabo/n; perdas = 3·R_fase·L·(1+fc)·I²
            mw, pc = perdas_joule(crit["i"], r["cabo"]["r_op"] / n, e["comp_km"], e["p_kw"] / 1000.0, 3, e.get("fator_cat", 0.03))
            r["perdas"] = dict(mw=mw, pct=pc)
        d, dfio = cabo.get("diametro_mm"), cabo.get("diam_fio_al_mm")
        if d and cabo.get("r_cc_20"):
            al = cabo.get("alfa_20c") or 0.004
            if dfio:
                r["ons"] = ampacidade_ons(d, dfio, cabo["r_cc_20"], al, e["u_kv"], e.get("alt_m", 0.0), e["emis"], e["absort"],
                                          e["t_norm"], e["t_emerg"], e["ta"], e["vento_ons"], e["rad"])
            else:
                r["avisos"].append("Cabo sem diâmetro do fio de alumínio no catálogo: ampacidade ONS não calculada (DADO NÃO INFORMADO).")
            tn = ampacidade_ieee738(d, r_temp(cabo["r_cc_20"], al, e["t_norm"]), e["ta_max"], e["t_norm"], e.get("alt_m", 0.0),
                                    e["emis"], e["absort"], e["vento_ieee"], 90.0, e["rad"])
            te = ampacidade_ieee738(d, r_temp(cabo["r_cc_20"], al, e["t_emerg"]), e["ta_max"], e["t_emerg"], e.get("alt_m", 0.0),
                                    e["emis"], e["absort"], e["vento_ieee"], 90.0, e["rad"])
            r["ieee"] = dict(normal=tn, emergencia=te, ta=e["ta_max"])
            r["tc_op"] = temperatura_equilibrio(crit["i"] / n, d, cabo["r_cc_20"], al, e["ta_max"], e.get("alt_m", 0.0), e["emis"],
                                               e["absort"], e["vento_ieee"], e["rad"])
        else:
            r["avisos"].append("Cabo sem diâmetro/resistência no catálogo: ampacidade não calculada.")
        if cabo.get("ampacidade_a"):
            r["amp_cat"] = cabo["ampacidade_a"]
        if (cabo.get("r_cc_20") or 0) and (cabo.get("r_ca_75") or 0):
            r["r_ca75_cat"] = cabo["r_ca_75"]
    else:
        r["avisos"].append("Condutor não selecionado (Módulo 1 → Circuitos).")
    # cabo guarda
    r["guardas"] = []
    for g in guardas:
        v = verificar_guarda(g, e["icc_ka"], e["t_falta"], e["theta_i"], e["theta_f"], e["frac_guarda"])
        if g.get("r_cc_20"):
            v["r40"] = r_temp(g["r_cc_20"], g.get("alfa_20c") or 0.004, e.get("t_guarda", 40.0))
        r["guardas"].append(v)
    if not guardas:
        r["avisos"].append("Cabo guarda não selecionado (Módulo 1 → Configuração da LT).")
    return r
