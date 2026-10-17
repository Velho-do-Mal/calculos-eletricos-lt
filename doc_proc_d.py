"""Procedimentos – Módulos 12 a 16 e encerramento."""
import cmath
import math

import numpy as np

import calc_blindagem as cb
from doc_proc_a import calc_m2
from doc_proc_b import calc_m5, _pe
from doc_proc_base import (EQ, IN_A, REF, V, T, app_tab, checklist, comparacao, dif, f, mfrac, mi, mpar, msqrt, msub, msup, mu, passos)
from relatorio_m2 import fc

SQ2, SQ3 = math.sqrt(2.0), math.sqrt(3.0)
Z1 = complex(0.1437, 0.4904)            # Ω/km – sequência positiva (método matricial do M2)
C1 = 8.9655e-9                          # F/km


# ============================================================================= M12
def _d_ft_ff(us, delta, kg):
    kgff = 1.35 * kg - 0.35 * kg ** 2
    return 1.642 * (math.exp((us / SQ3) / (750 * delta * (1 - 3 * 0.03) * kgff)) - 1) ** 0.83


def calc_m12():
    m5 = calc_m5()
    um = REF["um"]
    tov = 1.4 * um / SQ3
    man = 2.2 * SQ2 * um / SQ3
    delta = m5["delta"]
    lo, hi = 1.0, 1500.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if _d_ft_ff(mid, delta, 1.45) <= 1.1 else (lo, mid)
    um_adm = 0.5 * (lo + hi)
    kgpp = 1.80                                                  # Anel–anel, α = 0,5 (Tabela C.3)
    kgff_pp = 1.35 * kgpp - 0.35 * kgpp ** 2
    d_ff_ff = 1.642 * (math.exp(um / (750 * delta * 0.91 * kgff_pp)) - 1) ** 0.83
    d_ff_fr = 1.2 * 820.0 / (530 * delta * (1 - 1.3 * 0.03) * (0.74 + 0.26 * kgpp))
    linhas = [
        ("Fase-terra – frequência fundamental (9.3.2)", m5["d_ff"], 1.1),
        ("Fase-terra – frente lenta (9.4.1)", max(m5["d_seco"], m5["d_chuva"]), 1.1),
        ("Fase-terra – frente rápida (9.5)", m5["d_fr"], 1.1),
        ("Fase-fase – frequência fundamental (9.3.3)", d_ff_ff, 1.5),
        ("Fase-fase – frente rápida (9.5)", d_ff_fr, 1.5)]
    return dict(tov=tov, man=man, um_adm=um_adm, razao=um / REF["un"], linhas=[(n, r, a, (a / r - 1) * 100, (a / r - 1) * 100 >= 15.0) for n, r, a in linhas], m5=m5)


def m12(R):
    x = calc_m12()
    R.h1("M12 – ISOLAMENTO E TENSÃO MÁXIMA OPERATIVA")
    R.h2("Objetivo e quando fazer")
    R.p("Verificar se o isolamento ADOTADO (distâncias no ar fase-terra e fase-fase e cadeia de isoladores) atende à tensão máxima operativa Um e às sobretensões "
        "representativas (temporária e de manobra), com margem mínima. Também informa o maior Um que a distância fase-terra adotada suporta em frequência industrial.")
    R.p("Em retrofit/recapacitação (elevação de tensão), na verificação de estruturas existentes ou quando o cliente pede a tensão máxima operativa admissível.", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["ABNT NBR 5422:2024, seção 9 (9.3.2 e 9.3.3 frequência fundamental; 9.4 frente lenta; 9.5 frente rápida) e Anexo C – reaproveitados do Módulo 5.",
             "IEC 60038 / IEC 60071-1 – série normalizada de Um (NECESSITA VALIDAÇÃO: não consta no acervo); Diretrizes 3.2.13, 4.7 e 6.8.",
             "Sobretensões representativas: temporária 1,4 p.u. de Um/√3 (usual em rejeição de carga) e de manobra 2,2 p.u. de √2·Um/√3 – PREMISSAS a confirmar com o M14/M15 e ATP."])
    R.h2("Metodologia manual")
    R.p("Passo 1 – Sobretensões representativas fase-terra a partir de Um:")
    EQ(R, msub(V("U"), T("TOV")), T("="), msub(V("k"), T("TOV")), mfrac(msub(V("U"), T("m")), msqrt(T("3"))), T("  [kV ef.] ;  "), msub(V("U"), T("man")), T("="), msub(V("k"), T("man")), msqrt(T("2")), mfrac(msub(V("U"), T("m")), msqrt(T("3"))), T("  [kV crista]"))
    R.p("Passo 2 – Distâncias requeridas (as mesmas do Módulo 5) e margem da distância adotada sobre a requerida:")
    EQ(R, V("Margem"), T("="), mpar(mfrac(msub(V("d"), T("adotada")), msub(V("d"), T("requerida"))) + T("−1")), T("·100  [%] ;  atende se "), V("Margem"), T("≥ margem mínima (15 %)"))
    R.p("Passo 3 – Um máximo admissível para a distância fase-terra adotada em frequência industrial: é o valor de Um que torna d_ft,ff (9.3.2) igual à distância adotada (busca por bisseção, pois a equação é transcendente).")
    R.p("Passo 4 – Cadeia: fuga adotada ≥ fuga específica × Um e distância de arco ≥ distância fase-terra governante (resultados do Módulo 5).")
    R.h2("Exemplo resolvido – LT 138 kV Exemplo (distâncias adotadas: 1,1 m fase-terra; 1,5 m fase-fase)")
    passos(R, "Sobretensões e margens", [
        ("Um/Un", f"145/138 = {f(x['razao'], 3)}"),
        ("U_TOV = 1,4·Um/√3", f"1,4 × 145/√3 = {f(x['tov'], 1)} kV ef."),
        ("U_man = 2,2·√2·Um/√3", f"2,2 × 1,4142 × 145/√3 = {f(x['man'], 0)} kV crista"),
        ("Um máx. p/ d fase-terra adotada = 1,1 m", f"{f(x['um_adm'], 0)} kV (frequência industrial)")] +
        [(f"Margem – {n}", f"adotada {f(a, 2)} / requerida {f(r, 2)} → {f(m, 1)} % → {'ATENDE' if ok else 'NÃO ATENDE'}") for n, r, a, m, ok in x["linhas"]])
    comparacao(R, "Manual × app (Módulo 12)", [
        ("Um/Un", f(x["razao"], 3), "1,051", dif(x["razao"], 1.051)),
        ("TOV (kV ef. f-t)", f(x["tov"], 1), "117,2", dif(x["tov"], 117.2)),
        ("Manobra (kV crista f-t)", f(x["man"], 0), "260", dif(x["man"], 260)),
        ("Um máx. p/ d adotada (kV)", f(x["um_adm"], 0), "633", dif(x["um_adm"], 633)),
        ("Margem fase-terra, freq. fundamental (%)", f(x["linhas"][0][3], 1), "299,3", dif(x["linhas"][0][3], 299.27)),
        ("Margem fase-terra, frente rápida (%)", f(x["linhas"][2][3], 1), "−35,8", dif(x["linhas"][2][3], -35.82))])
    R.p("Conclusão: a distância fase-terra de 1,1 m atende frequência industrial e manobra, mas não a frente rápida (exige 1,71 m); a de 1,5 m fase-fase não atende a frente rápida. "
        "Soluções: aumentar as distâncias na estrutura, rever a cadeia/balanço ou demonstrar o desempenho a descargas pelo Módulo 16 (9.5.3.3).")
    R.obs("O Módulo 12 reaproveita o motor do Módulo 5 com os dados do M5 gravados no projeto. Abra e confirme o Módulo 5 (geometria kg, nível de poluição, Fsfl) "
          "ANTES de usar o Módulo 12; sem isso, o M12 usa valores de partida diferentes dos exibidos no M5 (por exemplo, kg fase-fase de \"Condutores cruzados\" em vez de \"Anel–anel\"), e as distâncias fase-fase requeridas mudam.")
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 12 – preenchimento", [
        ("Pré-requisito", "Módulo 5 aberto e confirmado", "—", "Distâncias requeridas e cadeia vêm do M5"),
        ("Dados de entrada", "Sobretensão temporária (p.u. de Um/√3)", "1,4", "PREMISSA; confirmar com M14/ATP"),
        ("Dados de entrada", "Sobretensão de manobra (p.u. de √2·Um/√3)", "2,2", "PREMISSA; confirmar com M15/ATP"),
        ("Dados de entrada", "Margem mínima exigida (%)", "15", "PREMISSA do app"),
        ("Dados de entrada", "Distância no ar fase-terra adotada (m)", "1,1", "Menor distância cadeia/condutor–estrutura na condição de projeto (balanço do M5)"),
        ("Dados de entrada", "Distância no ar fase-fase adotada (m)", "1,5", "Menor distância entre fases na condição de projeto")])
    R.p("Resultado esperado: Um/Un 1,051; TOV 117,2 kV; manobra 260 kV; Um máx. 633 kV; fase-terra de frente rápida NÃO ATENDE (margem −35,8 %); cadeia ATENDE (fuga 3.504 mm ≥ 2.900 mm).")
    R.h2("Conferência")
    checklist(R, ["Un, Um e fatores de sobretensão conferidos; Um na série normalizada.",
                  "Distâncias adotadas medidas no desenho da estrutura na condição de balanço crítica.",
                  "Módulo 5 revisado antes do M12.",
                  "Itens \"NÃO ATENDE\" com ação definida (mudar estrutura ou justificar com estudo de desempenho).",
                  "Registrar as sobretensões como premissas até a conclusão dos estudos de transitórios."])


# ============================================================================= M13
def _estado(sig1, th1, th2, gam1, gam2, a, E, alfa):
    k = E * gam2 ** 2 * a ** 2 / 24.0
    A = E * gam1 ** 2 * a ** 2 / (24.0 * sig1 ** 2) - sig1 + E * alfa * (th2 - th1)
    lo, hi = 1e-3, 1e4
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if mid * mid * (mid + A) < k else (lo, mid)
    return 0.5 * (lo + hi)


def calc_m13():
    S, E, alfa = REF["s_mm2"], REF["e_gpa"] * 1000.0, REF["dil"] * 1e-6
    gam = REF["massa"] * 9.80665 / S
    a = 400.0
    sig1 = 0.20 * REF["rtc_kn"] * 1000.0 / S
    out = dict(S=S, E=E, alfa=alfa, gam=gam, a=a, sig1=sig1, tab=[])
    for th in (5, 20, 45, 75, 90):
        s2 = _estado(sig1, 20.0, th, gam, gam, a, E, alfa)
        fp = gam * a ** 2 / (8 * s2)
        H, w = s2 * S, gam * S
        fc_ = H / w * (math.cosh(w * a / (2 * H)) - 1)
        out["tab"].append((th, s2 / (REF["rtc_kn"] * 1000.0 / S) * 100, fp, fc_, 24.0 - fc_))
    lo, hi = 20.0, 300.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        s2 = _estado(sig1, 20.0, mid, gam, gam, a, E, alfa)
        fc_ = (s2 * S) / (gam * S) * (math.cosh(gam * S * a / (2 * s2 * S)) - 1)
        lo, hi = (mid, hi) if 24.0 - fc_ > 8.0 else (lo, mid)
    out["th_lim"] = 0.5 * (lo + hi)
    return out


def m13(R):
    x = calc_m13()
    R.h1("M13 – AMPACIDADE E FLECHA MÁXIMA")
    R.h2("Objetivo e quando fazer")
    R.p("Calcular a flecha do condutor em função da temperatura (mudança de estado a partir do EDS), a distância ao solo resultante, a ampacidade por balanço térmico (IEEE 738) "
        "e a corrente máxima limitada pela flecha (temperatura em que a distância ao solo cai ao mínimo exigido).")
    R.p("Em projeto e em recapacitação (aumento de corrente em LT existente), na verificação de travessias e na definição da altura das estruturas.", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["Equação da parábola de mudança de estado (planilha BK \"CALCULO MECANICO DEL CONDUCTOR\") e flecha em catenária.",
             "IEEE Std 738-2006 (temperatura do condutor × corrente); ONS – NT de ampacidade.",
             "NBR 5422:2024 (distâncias de segurança): a distância mínima ao solo é dado de entrada – NECESSITA VALIDAÇÃO com o item aplicável (7.2)."])
    R.h2("Metodologia manual")
    R.p("Passo 1 – Estado inicial (EDS): tensão específica σ1 = EDS (% da RTC) × RTC/S a 20 °C; peso específico γ = massa × g / S (N/m/mm²).")
    R.p("Passo 2 – Mudança de estado para a temperatura θ2 (sem vento/gelo, vão regulador a) pela equação cúbica da parábola, resolvida numericamente (bisseção) em σ2:")
    EQ(R, msup(msub(mi("σ"), T("2")), T("2")), mpar(msub(mi("σ"), T("2")) + T("+") + mfrac(V("E") + msup(mi("γ"), T("2")) + msup(V("a"), T("2")), T("24") + msup(msub(mi("σ"), T("1")), T("2"))) + T("−") + msub(mi("σ"), T("1")) + T("+") + V("E") + mi("α") + mpar(msub(mi("θ"), T("2")) + T("−") + msub(mi("θ"), T("1")))), T("="), mfrac(V("E") + msup(mi("γ"), T("2")) + msup(V("a"), T("2")), T("24")))
    R.p("Passo 3 – Flecha (parábola e catenária) e distância ao solo (terreno plano):")
    EQ(R, V("f"), T("="), mfrac(mi("γ") + msup(V("a"), T("2")), T("8") + msub(mi("σ"), T("2"))), T(" ;  "), V("f", "cat"), T("="), mfrac(V("H"), V("w")), mpar(T("cosh") + mpar(mfrac(V("w") + V("a"), T("2") + V("H"))) + T("−1")), T(" ;  "), V("d", "solo"), T("="), V("h", "fix"), T("−"), V("f"))
    R.p("Passo 4 – Temperatura do condutor para uma corrente (IEEE 738): I²·R(Tc) = qc + qr − qs (ver M7). A corrente limitada pela flecha é a corrente que produz a temperatura Tc em que a distância ao solo = mínimo exigido.")
    R.h2("Exemplo resolvido – LT 138 kV Exemplo")
    R.p("Dados: HAWK (S = 280,8 mm²; 0,9764 kg/m; RTC 87,06 kN; E = 74,46 GPa; α = 18,9·10⁻⁶/°C); vão regulador 400 m; EDS 20 % a 20 °C; altura de fixação 24 m; "
        "distância mínima ao solo 8 m.")
    passos(R, "Mudança de estado e flecha", [
        ("γ = m·g/S", f"0,9764 × 9,80665/280,8 = {f(x['gam'], 5)} N/m/mm²"),
        ("σ1 = 0,20·RTC/S", f"0,20 × 87.063/280,8 = {f(x['sig1'], 2)} MPa"),
        ("Flecha a 20 °C = γ·a²/(8σ1)", f"{f(x['gam'] * x['a'] ** 2 / (8 * x['sig1']), 2)} m"),
        ("Resolver σ2 para 75 °C", f"σ2 = {f(x['tab'][3][1] * REF['rtc_kn'] * 1000 / REF['s_mm2'] / 100, 2)} MPa ({f(x['tab'][3][1], 2)} % RTC)"),
        ("Flecha a 75 °C (parábola / catenária)", f"{f(x['tab'][3][2], 2)} m / {f(x['tab'][3][3], 2)} m"),
        ("Distância ao solo a 75 °C = 24 − f", f"{f(x['tab'][3][4], 2)} m (mín. 8 m → ATENDE)"),
        ("Temperatura em que a distância ao solo = 8 m (flecha 16 m)", f"{f(x['th_lim'], 0)} °C")])
    R.tabela("Flecha e distância ao solo × temperatura do condutor", ["θ (°C)", "Tração (% RTC)", "Flecha parábola (m)", "Flecha catenária (m)", "Dist. ao solo (m)"],
             [[f(t, 0), f(p_, 2), f(fp, 2), f(fc_, 2), f(d, 2)] for t, p_, fp, fc_, d in x["tab"]], [2.4, 3.2, 3.6, 3.6, 3.2])
    comparacao(R, "Manual × app (Módulo 13)", [
        ("Tração a 20 °C (% RTC)", f(x["tab"][1][1], 2), "20,00", dif(x["tab"][1][1], 20.0)),
        ("Flecha a 5 °C (m)", f(x["tab"][0][2], 2), "10,35", dif(x["tab"][0][2], 10.35)),
        ("Flecha a 20 °C (m)", f(x["tab"][1][2], 2), "11,00", dif(x["tab"][1][2], 11.0)),
        ("Flecha a 75 °C – parábola (m)", f(x["tab"][3][2], 2), "13,23", dif(x["tab"][3][2], 13.23)),
        ("Flecha a 75 °C – catenária (m)", f(x["tab"][3][3], 2), "13,24", dif(x["tab"][3][3], 13.24)),
        ("Flecha a 90 °C – parábola (m)", f(x["tab"][4][2], 2), "13,79", dif(x["tab"][4][2], 13.79))])
    R.p("Resultados do app não repetidos à mão: ampacidade IEEE 738 a 75 °C = 634 A (Ta 35 °C; vento 1 m/s; 1000 W/m²), temperatura do condutor em 251 A = 46,2 °C e corrente limitada pela flecha = 1.060 A. "
        "Como a flecha só atinge o limite perto de 150 °C, acima das temperaturas de 75/90 °C, a ampacidade é limitada pela temperatura máxima do condutor (75/90 °C), não pela flecha.")
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 13 – preenchimento", [
        ("Dados de entrada", "Vão regulador (m)", "400", "Do cálculo mecânico"),
        ("Dados de entrada", "EDS (% da RTC) / Temperatura EDS (°C)", "20 / 20", "Premissa BK; conferir com o cliente"),
        ("Dados de entrada", "Temp. ambiente máx. p/ flecha (°C)", "30", ""),
        ("Dados de entrada", "Temp. máx. do condutor – normal / emergência (°C)", "75 / 90", ""),
        ("Dados de entrada", "Altura de fixação do condutor mais baixo (m)", "24", "Altura na estrutura"),
        ("Dados de entrada", "Distância mínima ao solo (m)", "8", "Da norma (7.2) ou edital"),
        ("Dados de entrada", "Temperatura ambiente (°C) / Vento (m/s) / Radiação solar (W/m²)", "35 / 1 / 1000", "Condições da ampacidade"),
        ("Dados de entrada", "Corrente de operação (A, total da fase)", "251", "Do Módulo 7/1"),
        ("Dados de entrada", "Emissividade / Absortividade solar", "0,5 / 0,5", ""),
        ("Dados de entrada", "Limite de tração a Tmín (% RTC)", "33", "Verificação da tração máxima")])
    R.p("Resultado esperado: ampacidade a 75 °C = 634 A; flecha a Tmáx = 13,24 m; temperatura em 251 A = 46,2 °C; corrente limitada pela flecha = 1.060 A.")
    R.h2("Conferência")
    checklist(R, ["Módulo de elasticidade final e dilatação do catálogo corretos (afetam a flecha).",
                  "EDS e vão regulador coerentes com o cálculo mecânico.",
                  "Distância mínima ao solo conferida com a norma/edital e travessias do perfil.",
                  "Flecha em catenária × parábola próximas (vãos até ~500 m); diferença grande indica dado errado.",
                  "Ampacidade comparada com a corrente de emergência do Módulo 1."])


# ============================================================================= M14
def calc_m14(s_mva=60.0, q_shunt=0.0):
    un, f_ = REF["un"], REF["f"]
    w = 2 * math.pi * f_
    Y = complex(0, w * C1)
    Zo = cmath.sqrt(Z1 / Y)
    gl = cmath.sqrt(Z1 * Y) * REF["km"]
    A, B, Cc, D = cmath.cosh(gl), Zo * cmath.sinh(gl), cmath.sinh(gl) / Zo, cmath.cosh(gl)
    U = un * 1e3
    zs_mod = U ** 2 / (3000e6)
    th = math.atan(10.0)
    Zs = zs_mod * complex(math.cos(th), math.sin(th))
    Ysh = complex(0, -q_shunt * 1e6 / U ** 2)
    vr0 = U / SQ3
    S = s_mva * 1e6 * complex(REF["fp"], math.sqrt(1 - REF["fp"] ** 2))
    ir0 = (S / (3 * vr0)).conjugate() + Ysh * vr0
    vs0, is0 = A * vr0 + B * ir0, Cc * vr0 + D * ir0
    E = vs0 + Zs * is0
    vr = E / ((A + B * Ysh) + Zs * (Cc + D * Ysh))
    return dict(A=A, B=B, C=Cc, Zo=Zo, gl=gl, Zs=Zs, zs_mod=zs_mod, vs0=vs0, E=E, vr_kv=abs(vr) * SQ3 / 1e3, ferr=1 / abs(cmath.cosh(gl)), vs0_kv=abs(vs0) * SQ3 / 1e3, E_kv=abs(E) * SQ3 / 1e3)


def m14(R):
    x = calc_m14()
    R.h1("M14 – REJEIÇÃO DE CARGA")
    R.h2("Objetivo e quando fazer")
    R.p("Estimar a sobretensão temporária a 60 Hz no terminal receptor quando a carga é rejeitada com a linha ainda energizada pela fonte (efeito Ferranti somado à elevação pela impedância da fonte), "
        "e dimensionar a compensação reativa shunt (reator) necessária para respeitar o limite de sobretensão. É uma TRIAGEM ANALÍTICA, não substitui o estudo ATP.")
    R.p("Linhas longas ou com fonte fraca, e em qualquer projeto em que as Diretrizes exijam estudo de transitórios (3.2.5, 3.2.6 e 8.4; ONS submódulo 23.3, ≥ 200 manobras).", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["Diretrizes de Projeto Básico 3.2.5, 3.2.6 e 8.4 (estudo de transitórios eletromagnéticos); ONS Procedimentos de Rede, submódulo 23.3.",
             "Livro 3 e Livro 2 – linha de parâmetros distribuídos, ABCD hiperbólico e efeito Ferranti.",
             "Limitações do app: 60 Hz, sequência positiva, sem saturação de transformadores, sem dinâmica do gerador/regulador, sem circuito paralelo energizado."])
    R.h2("Metodologia manual")
    R.p("Passo 1 – ABCD da linha com Z1 e C1 do Módulo 2 (sequência positiva) e fonte de Thévenin: Zs = Un²/Scc com ângulo atan(X/R).")
    EQ(R, V("A"), T("="), V("D"), T("=cosh"), mpar(mi("γ") + mi("ℓ")), T(" ;  "), V("B"), T("="), msub(V("Z"), T("0")), T("senh"), mpar(mi("γ") + mi("ℓ")), T(" ;  "), V("C"), T("="), mfrac(T("senh") + mpar(mi("γ") + mi("ℓ")), msub(V("Z"), T("0"))), T(" ;  "), msub(V("Z"), T("s")), T("="), mfrac(msup(V("U"), T("n") + T("2")) if False else msup(msub(V("U"), T("n")), T("2")), msub(V("S"), T("cc"))), T("∠ atan"), mpar(V("X") + T("/") + V("R")))
    R.p("Passo 2 – Estado antes da rejeição (carga S, Vr0 = 1,0 p.u.) e tensão interna da fonte, que permanece constante:")
    EQ(R, msub(V("V"), T("s0")), T("="), V("A"), msub(V("V"), T("r0")), T("+"), V("B"), msub(V("I"), T("r0")), T(" ;  "), msub(V("I"), T("s0")), T("="), V("C"), msub(V("V"), T("r0")), T("+"), V("D"), msub(V("I"), T("r0")), T(" ;  "), V("E"), T("="), msub(V("V"), T("s0")), T("+"), msub(V("Z"), T("s")), msub(V("I"), T("s0")))
    R.p("Passo 3 – Depois da rejeição (terminal receptor aberto, reator shunt Ysh = −jQ/Un² permanece):")
    EQ(R, msub(V("V"), T("r")), T("="), mfrac(V("E"), mpar(V("A") + V("B") + msub(V("Y"), T("sh"))) + T("+") + msub(V("Z"), T("s")) + mpar(V("C") + V("D") + msub(V("Y"), T("sh")))), T(" ;  Ferranti: "), mfrac(msub(V("V"), T("r")), msub(V("V"), T("s"))), T("="), mfrac(T("1"), T("|cosh") + mpar(mi("γ") + mi("ℓ")) + T("|")))
    R.p("Passo 4 – Se Vr/Un > limite (1,1 p.u.), procura-se por bisseção o menor Q do reator shunt que traz Vr ao limite.")
    R.h2("Exemplo resolvido – LT 138 kV Exemplo")
    R.p("Dados: Z1 = 0,1437 + j0,4904 Ω/km; C1 = 8,9655 nF/km (M2, método matricial); 80 km; Scc na origem 3000 MVA, X/R = 10; carga rejeitada 60 MVA, fp 0,95; Vr0 = 1,0 p.u.; limite 1,10 p.u.")
    passos(R, "Rejeição de carga", [
        ("γℓ", f"{fc(x['gl'], 5)}"),
        ("Zo", f"{fc(x['Zo'], 2)} Ω"),
        ("Zs = Un²/Scc ∠atan(10)", f"{f(x['zs_mod'], 3)} Ω ∠84,29° = {fc(x['Zs'], 3)} Ω"),
        ("Vs0 antes da rejeição", f"{f(x['vs0_kv'], 2)} kV (linha)"),
        ("Tensão interna da fonte E", f"{f(x['E_kv'], 2)} kV (linha)"),
        ("Vr depois da rejeição", f"{f(x['vr_kv'], 1)} kV = {f(x['vr_kv'] / 138, 3)} p.u. de Un"),
        ("Ferranti 1/|cosh γℓ|", f"{f(x['ferr'], 4)}"),
        ("Verificação do limite 1,10 p.u.", f"{f(x['vr_kv'] / 138, 3)} ≤ 1,10 → ATENDE (reator mínimo 0 Mvar)")])
    comparacao(R, "Manual × app (Módulo 14)", [
        ("Tensão após a rejeição (kV)", f(x["vr_kv"], 1), "150,3", dif(x["vr_kv"], 150.3)),
        ("Sem reator (p.u.)", f(x["vr_kv"] / 138, 3), "1,089", dif(x["vr_kv"] / 138, 1.089)),
        ("Ferranti 1/cosh(γℓ)", f(x["ferr"], 4), "1,0053", dif(x["ferr"], 1.0053))])
    R.p("Interpretação: com 80 km o efeito Ferranti é só 0,5 %; a elevação vem do corte de carga com a impedância da fonte (Scc 3000 MVA). Fonte fraca (Scc < 5 × carga) ou linhas > 200 km exigem estudo EMT.")
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 14 – preenchimento", [
        ("Pré-requisito", "Módulo 2 com condutor, cabos guarda e geometria", "—", "Fornece Z1 e C1 (sequência positiva)"),
        ("Dados de entrada", "Potência de curto na origem (MVA) / Relação X/R da fonte", "3000 / 10", "Do estudo de curto-circuito do ONS/cliente"),
        ("Dados de entrada", "Carga rejeitada (MVA) / Fator de potência da carga", "60 / 0,95", "Carga total do terminal rejeitado"),
        ("Dados de entrada", "Reator shunt no fim da linha (Mvar)", "0", "Se existir, informar o valor permanente"),
        ("Dados de entrada", "Tensão na carga antes da rejeição (p.u. de Un)", "1,0", ""),
        ("Dados de entrada", "Limite de sobretensão (p.u. de Un)", "1,10", "Critério do cliente/ONS")])
    R.p("Resultado esperado: tensão após rejeição 150,3 kV (1,089 p.u.); Ferranti 1,0053; reator mínimo 0 Mvar. O app emite o aviso de TRIAGEM: o estudo ATP continua sendo necessário.")
    R.h2("Conferência")
    checklist(R, ["Scc e X/R da barra de origem do cliente/ONS (cenário de menor curto é o crítico).",
                  "Carga rejeitada = maior carga possível no terminal.",
                  "Z1 e C1 vêm do Módulo 2 (circuito correto).",
                  "Ângulo elétrico da linha < 90° (senão há risco de ressonância a 60 Hz).",
                  "Resultado registrado como triagem; estudo ATP programado."])


# ============================================================================= M15
def _pico(L, Rs, C, vres, rpre=0.0, tins=0.008):
    def kappa(Rr):
        z = Rr / 2 * math.sqrt(C / L)
        return (math.exp(-math.pi * z / math.sqrt(1 - z * z)) if z < 1 else 0.0), z
    v0 = -abs(vres)
    k1, z1 = kappa(Rs + rpre)
    p1 = 1 + (1 - v0) * k1
    if rpre <= 0:
        return p1, dict(zeta=z1, kappa=k1)
    tau = max((Rs + rpre) * C, 1e-9)
    vb = 1 + (v0 - 1) * math.exp(-tins / tau) if z1 >= 1 else p1
    k2, _ = kappa(Rs)
    return max(p1, 1 + (1 - vb) * k2), dict(zeta=z1, kappa=k1)


def calc_m15():
    un, um, f_, l = REF["un"], REF["um"], REF["f"], REF["km"]
    w = 2 * math.pi * f_
    Xs = un ** 2 / 3000.0
    Rs = Xs / 10.0
    Ls = Xs / w
    Rl, Ll, Cl = Z1.real * l, Z1.imag / w * l, C1 * l
    L, Rser, C = Ls + Ll, Rs + Rl, Cl / 2
    f0 = 1 / (2 * math.pi * math.sqrt(L * C))
    pico, det = _pico(L, Rser, C, 1.0)
    esc = un / um
    pico_pu = pico * esc
    lo, hi = 0.0, 5000.0
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if _pico(L, Rser, C, 1.0, mid)[0] * esc > 2.0 else (lo, mid)
    rmin = 0.5 * (lo + hi)
    td = (10.5 + um / 34.5) / f_ * 1000
    Xl, Xr = Z1.imag * l, un ** 2 / 2000.0
    xt = Xs + Xl + Xr
    ang = math.degrees(math.asin(57.0 * xt / un ** 2))
    return dict(Xs=Xs, Rs=Rs, Ls=Ls, Rl=Rl, Ll=Ll, Cl=Cl, L=L, Rser=Rser, C=C, f0=f0, zeta=det["zeta"], kappa=det["kappa"], pico=pico, pico_pu=pico_pu, esc=esc, rmin=rmin, td=td, Xl=Xl, Xr=Xr, xt=xt, ang=ang)


def m15(R):
    x = calc_m15()
    R.h1("M15 – RELIGAMENTO TRIPOLAR")
    R.h2("Objetivo e quando fazer")
    R.p("Estimar a sobretensão de manobra no religamento tripolar (energização com carga residual na linha), a necessidade e o valor mínimo do resistor de pré-inserção do disjuntor, "
        "a coerência do tempo morto com o tempo de deionização do arco e o ângulo através do disjuntor. É TRIAGEM ANALÍTICA, não substitui o estudo estatístico EMT/ATP.")
    R.p("LTs de transmissão com religamento automático; as Diretrizes (3.2.5, 3.2.6, 3.2.7 e 8.4) exigem estudo estatístico com ≥ 200 manobras, modelo de Bergeron e tempo morto de 500 ms.", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["Diretrizes de Projeto Básico 3.2.5, 3.2.6, 3.2.7 e 8.4; ONS Procedimentos de Rede, submódulo 23.3.",
             "Modelo de um estágio LC (linha em π, C/2 no terminal aberto) – amortecimento ζ e fator de pico κ.",
             "Deionização do arco: t_d = 10,5 + U/34,5 ciclos (fórmula clássica) – NECESSITA VALIDAÇÃO (não consta no acervo)."])
    R.h2("Metodologia manual")
    R.p("Passo 1 – Circuito equivalente: L = Ls + L_linha; R = Rs + R_linha (+ R_pré); C = C_linha/2; com Xs = Un²/Scc, Rs = Xs/(X/R), Ls = Xs/ω.")
    EQ(R, V("L"), T("="), msub(V("L"), T("s")), T("+"), msub(V("L"), T("l")), T(" ;  "), V("R"), T("="), msub(V("R"), T("s")), T("+"), msub(V("R"), T("l")), T("+"), msub(V("R"), T("pré")), T(" ;  "), V("C"), T("="), mfrac(msub(V("C"), T("l")), T("2")), T(" ;  "), mi("ζ"), T("="), mfrac(V("R"), T("2")), msqrt(mfrac(V("C"), V("L"))))
    R.p("Passo 2 – Pico da tensão no terminal aberto, com tensão residual V0 = −Vres·E (polaridade oposta, pior caso) e amortecimento κ:")
    EQ(R, mi("κ"), T("=exp"), mpar(T("−") + mfrac(mi("π") + mi("ζ"), msqrt(T("1−") + msup(mi("ζ"), T("2"))))), T(" ;  "), V("pico"), T("="), V("E"), T("+"), mpar(V("E") + T("−") + msub(V("V"), T("0"))) + mi("κ"), T("  (p.u. de E)"))
    R.p("Passo 3 – Conversão para a base de manobra (p.u. de √2·Um/√3): multiplica-se por Un/Um. Com resistor de pré-inserção há dois estágios (R+R_pré durante t_ins e depois R), e adota-se o maior pico; "
        "o app procura por bisseção o menor R_pré que atende o limite.")
    R.p("Passo 4 – Tempo morto × deionização e ângulo através do disjuntor:")
    EQ(R, msub(V("t"), T("d")), T("="), mfrac(T("10,5+") + msub(V("U"), T("m")) + T("/34,5"), V("f")), T("  [s] ;  "), mi("θ"), T("="), T("asen") + mpar(mfrac(V("P") + msub(V("X"), T("total")), msup(msub(V("U"), T("n")), T("2")))), T(" ;  "), msub(V("X"), T("total")), T("="), msub(V("X"), T("s")), T("+"), msub(V("X"), T("l")), T("+"), msub(V("X"), T("rem")))
    R.h2("Exemplo resolvido – LT 138 kV Exemplo")
    R.p("Dados: Z1 e C1 do M2; Scc origem 3000 MVA (X/R = 10); Scc remoto 2000 MVA; tempo morto 500 ms; ângulo máx. 30°; tensão residual 1,0 p.u.; transferência 57 MW; limite de sobretensão 2,0 p.u.; falta monofásica.")
    passos(R, "Religamento tripolar", [
        ("Xs = Un²/Scc; Rs = Xs/10; Ls = Xs/ω", f"Xs = {f(x['Xs'], 3)} Ω; Rs = {f(x['Rs'], 3)} Ω; Ls = {f(x['Ls'] * 1e3, 2)} mH"),
        ("Linha: R = 0,1437·80; L = 0,4904·80/ω; C = 8,9655·80 nF", f"{f(x['Rl'], 2)} Ω; {f(x['Ll'] * 1e3, 1)} mH; {f(x['Cl'] * 1e6, 3)} µF"),
        ("L; R; C = Cl/2", f"{f(x['L'] * 1e3, 1)} mH; {f(x['Rser'], 2)} Ω; {f(x['C'] * 1e6, 3)} µF"),
        ("Frequência natural f0 = 1/(2π√(LC))", f"{f(x['f0'], 0)} Hz"),
        ("ζ = (R/2)·√(C/L); κ", f"ζ = {f(x['zeta'], 4)}; κ = {f(x['kappa'], 4)}"),
        ("Pico = E + (E − V0)·κ (V0 = −1,0 p.u.)", f"1 + 2 × {f(x['kappa'], 4)} = {f(x['pico'], 3)} p.u. de E"),
        ("Base de manobra: × Un/Um", f"{f(x['pico'], 3)} × {f(x['esc'], 4)} = {f(x['pico_pu'], 2)} p.u. → limite 2,0: NÃO ATENDE"),
        ("R de pré-inserção mínimo (bisseção)", f"{f(x['rmin'], 0)} Ω"),
        ("t_d = (10,5 + 145/34,5)/60", f"{f(x['td'], 0)} ms ≤ 500 ms → ATENDE"),
        ("X total = Xs + Xl + Xrem; θ = asen(P·X/Un²)", f"{f(x['Xs'], 2)} + {f(x['Xl'], 2)} + {f(x['Xr'], 2)} = {f(x['xt'], 2)} Ω; θ = {f(x['ang'], 1)}° ≤ 30° → ATENDE")])
    comparacao(R, "Manual × app (Módulo 15)", [
        ("Sobretensão (p.u.)", f(x["pico_pu"], 2), "2,79", dif(x["pico_pu"], 2.79)),
        ("R de pré-inserção mínimo (Ω)", f(x["rmin"], 0), "204", dif(x["rmin"], 204)),
        ("Tempo de deionização (ms)", f(x["td"], 0), "245", dif(x["td"], 245)),
        ("Ângulo no disjuntor (°)", f(x["ang"], 1), "9,5", dif(x["ang"], 9.5))])
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 15 – preenchimento", [
        ("Pré-requisito", "Módulo 2 completo (Z1 e C1)", "—", ""),
        ("Dados de entrada", "Tipo de falta", "Monofásica", "Define a existência de arco (deionização); \"Sem arco (permanente)\" zera t_d"),
        ("Dados de entrada", "Tempo morto (ms) / Ângulo máx. no disjuntor (°)", "500 / 30", "Diretrizes: 500 ms"),
        ("Dados de entrada", "Tensão residual na linha (p.u.)", "1,0", "Pior caso: polaridade oposta"),
        ("Dados de entrada", "Scc na origem (MVA) / X/R da fonte", "3000 / 10", ""),
        ("Dados de entrada", "Scc no terminal remoto (MVA)", "2000", "Para o ângulo através do disjuntor"),
        ("Dados de entrada", "Potência transferida (MW)", "57", ""),
        ("Dados de entrada", "Limite de sobretensão de manobra (p.u. de √2·Um/√3)", "2,0", "Critério do edital"),
        ("Dados de entrada", "Disjuntor com resistor de pré-inserção", "desmarcado", "Marcar e informar R/t_ins para testar a solução")])
    R.p("Resultado esperado: sobretensão 2,79 p.u. (NÃO ATENDE); R de pré-inserção mínimo 204 Ω; tempo morto 500 ms contra 245 ms (ATENDE); ângulo 9,5° (ATENDE).")
    R.h2("Conferência")
    checklist(R, ["Scc origem/remoto e X/R conforme o cliente (cenário de menor curto).",
                  "Tensão residual coerente com o esquema de proteção (até 1,0 p.u.).",
                  "Resistor de pré-inserção em Ω e tempo de inserção em ms no relatório.",
                  "Tempo morto ≥ tempo de deionização; ângulo ≤ limite.",
                  "Resultado tratado como triagem; estudo ATP estatístico programado."])


# ============================================================================= M16
def calc_m16():
    cfo = 820.0 / cb.KDF
    fases = [dict(x=x_, y=y_, req=REF["d_mm"] / 2000.0) for _, x_, y_ in REF["fases"]]
    guardas = [dict(x=x_, y=y_, r=0.005) for _, x_, y_ in REF["guardas"]]
    zc = float(np.mean([cb.zc_fase(f_["y"], f_["req"]) for f_ in fases]))
    i_fl = 2 * cfo / zc
    ng, beta = 6.0, 0.8
    corr = np.arange(2.0, 201.0, 1.0)
    W = np.array([cb.largura_exposta(fases, guardas, float(i), beta, dx=0.1)[0] for i in corr])
    pdf = cb.pdf_corrente(corr)
    n_sf = float(ng * 0.1 * np.sum((W * pdf)[corr >= i_fl]))
    k = cb.acoplamento(fases, guardas, 0.0062)
    r0, rho, zt = 20.0, 1000.0, 0.0
    ig = 400.0 * rho / (2 * math.pi * r0 ** 2)
    lo, hi = 0.1, 5000.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        u = mid * (r0 / math.sqrt(1 + mid / ig) + zt) * (1 - k)
        lo, hi = (mid, hi) if u < cfo else (lo, mid)
    ic = 0.5 * (lo + hi)
    n_l = ng * (28 * 30.0 ** 0.6 + 0.0) / 10.0
    p_bf = 1 / (1 + (ic / 31.0) ** 2.6)
    n_bf = n_l * 0.6 * p_bf
    ang = cb.angulos_blindagem(fases, guardas)
    tab_w = [(i, 6.7 * i ** 0.8, float(W[int(i - 2)])) for i in (3.4, 5, 10, 20, 40)]
    tab_w = [(i, 6.7 * i ** 0.8, float(cb.largura_exposta(fases, guardas, i, beta, dx=0.05)[0])) for i in (3.4, 5, 10, 20, 40)]
    return dict(cfo=cfo, zc=zc, i_fl=i_fl, n_sf=n_sf, k=k, ig=ig, ic=ic, n_l=n_l, p_bf=p_bf, n_bf=n_bf, ang=ang, tab_w=tab_w, total=n_sf + n_bf)


def m16(R):
    x = calc_m16()
    R.h1("M16 – BLINDAGEM CONTRA DESCARGAS ATMOSFÉRICAS")
    R.h2("Objetivo e quando fazer")
    R.p("Avaliar a blindagem dos cabos para-raios e o desempenho da LT frente a descargas atmosféricas: ângulo de blindagem, falha de blindagem (descarga direta nas fases) pelo modelo "
        "eletrogeométrico (EGM), backflashover e taxa total de desligamentos por 100 km e por ano.")
    R.p("Todo projeto de LT (metas das Diretrizes: ≤ 2 desligamentos/100 km/ano até 230 kV, ≤ 1 acima; falha de blindagem ≤ 0,01/100 km/ano); obrigatório quando d_fr > d_ff no M5 (9.5.3.3).", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["Kiessling et al., Overhead Power Lines, cap. 4 – eq. 4.1 (distância de atração), 4.3 (Ng), 4.4/4.7 (sobretensão e corrente crítica) e Tabela 4.2; 4.4.2 (ângulo de blindagem 10°–35°).",
             "Diretrizes de Projeto Básico 6.8 (metas de desempenho) e Projeto Elétrico de LTs (Livro 2) 4.2.1.",
             "NECESSITAM VALIDAÇÃO: distribuição de corrente CIGRE/Anderson P(I ≥ i) = 1/(1 + (i/31)^2,6), N_L (IEEE 1243) e fração 0,6 das descargas em guarda que vão à torre."])
    R.h2("Metodologia manual")
    R.p("Passo 1 – Impedância de surto da fase, tensão na fase por descarga direta e corrente mínima de flashover (CFO = Ufr/0,961):")
    EQ(R, msub(V("Z"), T("c")), T("=60·ln"), mpar(mfrac(T("2") + V("h"), msub(V("r"), T("eq")))), T(" ;  "), msub(V("U"), T("c")), T("="), mfrac(T("1"), T("2")), V("I"), msub(V("Z"), T("c")), T(" ;  "), msub(V("I"), T("fl")), T("="), mfrac(T("2") + msub(V("U"), T("50")), msub(V("Z"), T("c"))))
    R.p("Passo 2 – Modelo eletrogeométrico: distância de atração D = 6,7·I^0,8 (ao solo: βs·D, βs = 0,8 faixa I ou 0,67 faixa II). Com círculos de raio D em torno de fases e para-raios e o plano a βs·D do solo, "
        "a largura W(I) é a faixa lateral cuja primeira superfície atingida é uma fase. A taxa de falha de blindagem integra W(I) com a densidade de probabilidade de corrente p(I):")
    EQ(R, V("D"), T("=6,7·"), msup(V("I"), T("0,8")), T(" ;  "), msub(V("N"), T("sf")), T("="), msub(V("N"), mi("g")), T("·0,1·"), T("∑"), V("W") + mpar(V("I")) + V("p") + mpar(V("I")) + mi("ΔI"), T("  (I ≥ "), msub(V("I"), T("fl")), T(")"))
    R.p("Passo 3 – Backflashover: a corrente crítica é aquela em que a tensão sobre a cadeia atinge o CFO, com o acoplamento k entre guarda e fase e a resistência impulsiva Ri(I) (ionização do solo):")
    EQ(R, V("I"), mpar(msub(V("R"), mu("i")) + mpar(V("I")) + T("+") + msub(V("Z"), T("t"))) + mpar(T("1−") + V("k")), T("="), msub(V("U"), T("50")), T(" ;  "), msub(V("R"), mu("i")), T("="), mfrac(msub(V("R"), T("0")), msqrt(T("1+") + mfrac(V("I"), msub(V("I"), T("g"))))), T(" ;  "), V("k"), T("="), mfrac(msub(V("Z"), T("gf")), msub(V("Z"), T("gg"))))
    R.p("Passo 4 – Descargas na linha e taxa de backflashover (por 100 km e por ano), com P(I ≥ Ic) da distribuição de corrente:")
    EQ(R, msub(V("N"), T("L")), T("="), msub(V("N"), mi("g")), mfrac(T("28·") + msup(V("h"), T("0,6")) + T("+") + V("b"), T("10")), T(" ;  "), msub(V("N"), T("BF")), T("="), msub(V("N"), T("L")), msub(V("f"), T("t")), V("P") + mpar(V("I") + T("≥") + msub(V("I"), T("c,BF"))), T(" ;  "), msub(V("N"), T("total")), T("="), msub(V("N"), T("sf")), T("+"), msub(V("N"), T("BF")))
    R.h2("Exemplo resolvido – LT 138 kV Exemplo")
    R.p("Dados: Ng = 6 descargas/km²/ano (ilustrativo); faixa de tensão I (βs = 0,8); R0 = 20 Ω; Z da torre desprezada (0 Ω); ρ = 1000 Ω·m; E0 = 400 kV/m; fração para a torre 0,6; torre 30 m; "
        "guardas a 30 m separados de 6 m; fases a 24 m; raio do guarda OPGW 6,2 mm; b = 0 m; CFO = Tabela 15 ÷ 0,961.")
    passos(R, "Cálculo manual de blindagem e backflashover", [
        ("CFO = 820/0,961", f"{f(x['cfo'], 0)} kV"),
        ("Zc = 60·ln(2h/r) (h = 24 m; r = 10,89 mm)", f"{f(x['zc'], 0)} Ω"),
        ("I_fl = 2·CFO/Zc", f"{f(x['i_fl'], 2)} kA"),
        ("Ângulos de blindagem (fases A, B, C)", " ; ".join(f"{n}: {f(a, 1)}°" for n, a in zip("ABC", x["ang"])) + " → máx. 36,9° > 30° adotado"),
        ("k = Zgf/Zgg (pior fase)", f"{f(x['k'], 3)}"),
        ("Ig = E0·ρ/(2π·R0²)", f"{f(x['ig'], 1)} kA"),
        ("I_c,BF: I·(Ri(I) + 0)·(1 − k) = CFO (bisseção)", f"{f(x['ic'], 1)} kA"),
        ("N_L = Ng·(28·30^0,6 + b)/10 (b = 0 m, padrão do app)", f"{f(x['n_l'], 1)} descargas/100 km/ano"),
        ("P(I ≥ Ic) = 1/(1 + (Ic/31)^2,6)", f"{f(x['p_bf'], 4)}"),
        ("N_BF = N_L·0,6·P", f"{f(x['n_bf'], 2)} /100 km/ano"),
        ("N_sf (EGM; integração numérica de W(I)·p(I) para I ≥ I_fl)", f"{f(x['n_sf'], 3)} /100 km/ano"),
        ("Total = N_sf + N_BF", f"{f(x['total'], 2)} /100 km/ano → meta 2,0: NÃO ATENDE; N_sf contra 0,01: NÃO ATENDE")])
    R.tabela("Largura exposta W(I) do EGM (fases a 24 m; guardas a 30 m)", ["I (kA)", "D = 6,7·I^0,8 (m)", "W (m)"], [[f(i, 1), f(d, 1), f(w, 2)] for i, d, w in x["tab_w"]], [4.0, 6.0, 4.0])
    comparacao(R, "Manual × app (Módulo 16)", [
        ("CFO (kV)", f(x["cfo"], 0), "853", dif(x["cfo"], 853)),
        ("Zc da fase (Ω)", f(x["zc"], 0), "503", dif(x["zc"], 503)),
        ("Corrente mínima de flashover (kA)", f(x["i_fl"], 1), "3,4", dif(x["i_fl"], 3.4)),
        ("Coeficiente de acoplamento k", f(x["k"], 3), "0,190", dif(x["k"], 0.190)),
        ("Corrente crítica de backflashover (kA)", f(x["ic"], 0), "62", dif(x["ic"], 62)),
        ("Falha de blindagem (/100 km/ano)", f(x["n_sf"], 3), "2,607", dif(x["n_sf"], 2.607)),
        ("Backflashover (/100 km/ano)", f(x["n_bf"], 2), "10,93", dif(x["n_bf"], 10.93)),
        ("Total (/100 km/ano)", f(x["total"], 2), "13,54", dif(x["total"], 13.54))])
    R.p("Conclusão didática: com guardas a 6 m um do outro e fases a 6 m abaixo, o ângulo de blindagem (36,9° na estrutura) excede 30° e a taxa de falha de blindagem (2,6/100 km/ano) é 260 vezes a meta. "
        "Além disso o backflashover é alto porque R0 = 20 Ω e ρ = 1000 Ω·m. Soluções: aproximar os guardas das fases (reduzir o ângulo), reduzir R0 (contrapeso mais longo – M6), "
        "aumentar o isolamento (CFO) ou instalar para-raios de linha.")
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 16 – preenchimento", [
        ("Pré-requisitos", "Módulos 1, 2 (geometria), 5 (Ufr/CFO) e 6 (R0)", "—", "Geometria e cabos guarda vêm do M1/M2"),
        ("Dados de entrada", "Origem de Ng", "Ng informado", "Ou Nk → 0,2·Nk (Kiessling 4.3) / Eriksson (4.2)"),
        ("Dados de entrada", "Densidade de descargas Ng (descargas/km²/ano)", "6", "Mapa ceráunico/INPE do local"),
        ("Dados de entrada", "Faixa de tensão (βs)", "I", "I → βs = 0,8; II → 0,67"),
        ("Dados de entrada", "CFO (U50 % do isolamento)", "Tabela 15 (NBR 5422) ÷ 0,961", "Ou informar o CFO real da cadeia"),
        ("Dados de entrada", "Resistência de pé de torre R0 (Ω)", "20", "Do Módulo 6"),
        ("Dados de entrada", "Z de surto da torre (Ω, em série)", "0", "Premissa"),
        ("Dados de entrada", "Resistividade do solo (Ω·m)", "1000", "Para a ionização"),
        ("Dados de entrada", "Ionização do solo R_i(I) = R0/√(1 + I/Ig)", "marcado", "Desmarcar usa R0 constante (conservador)"),
        ("Dados de entrada", "Fração das descargas em guarda que vão à torre", "0,6", "NECESSITA VALIDAÇÃO"),
        ("Dados de entrada", "Altura da torre (m)", "30", "Para N_L"),
        ("Dados de entrada", "Meta de desligamentos (/100 km/ano) / Meta de falha de blindagem", "2,0 / 0,01", "Diretrizes"),
        ("Dados de entrada", "Ângulo de blindagem máximo (°)", "30", "Premissa de projeto (10°–35°)")])
    R.p("Resultado esperado: CFO 853 kV; Zc 503 Ω; I_fl 3,4 kA; k 0,190; falha de blindagem 2,607; backflashover 10,93; total 13,54 /100 km/ano; corrente crítica ≈ 62 kA (todos NÃO ATENDE).")
    R.h2("Conferência")
    checklist(R, ["Ng da fonte oficial (INPE/ELAT) para o local; usar o maior valor do trecho.",
                  "R0 vindo do Módulo 6; ρ coerente.",
                  "Ângulo de blindagem ≤ 30° (ou limite do cliente) para todas as fases.",
                  "Mínimo de dois cabos guarda; guardas acima das fases.",
                  "Itens NECESSITA VALIDAÇÃO (distribuição de corrente, N_L, fração à torre) discutidos com o cliente."])


# ============================================================================= encerramento
def final(R):
    R.h1("FECHAMENTO DO ESTUDO E EMISSÃO DO RELATÓRIO")
    R.h2("Checklist de emissão (todos os módulos)")
    checklist(R, ["Cabeçalho: cliente, projeto, número, revisão e responsável preenchidos no Módulo 1.",
                  "Nenhum aviso \"DADO NÃO INFORMADO\" restante; premissas listadas e justificadas.",
                  "Itens \"NECESSITA VALIDAÇÃO\" conferidos com norma/edital, ou mantidos no relatório com a etiqueta.",
                  "Resultados \"NÃO ATENDE\" com conclusão e ação (mudar projeto ou justificar).",
                  "Comparar pelo menos um resultado de cada módulo com o cálculo manual deste procedimento.",
                  "Relatório .docx revisado no Word (equações, tabelas, figuras, sumário) e PDF para impressão gerado.",
                  "Script de cálculo (Anexo A) presente e coerente com a versão do app.",
                  "Projeto salvo com a revisão correta; arquivos do cliente anexados à pasta do projeto."])
    R.h2("Erros comuns de novos usuários")
    R.tabela("Erros frequentes e como evitá-los", ["Erro", "Consequência", "Como evitar"], [
        ["Alterar valores padrão sem registrar a fonte", "Relatório sem rastreabilidade; premissa indevida", "Anotar norma/edital/medição em cada alteração"],
        ["Confundir kV de linha com fase-neutro", "Campos, corona e distâncias errados por √3", "Conferir o rótulo da unidade e a coluna da tabela"],
        ["Não abrir o Módulo 5 antes do M12", "Distâncias requeridas diferentes do M5", "Abrir e confirmar o M5 antes do M12"],
        ["Esquecer a flecha na altura dos condutores", "Campos e corona subestimados", "Usar altura mínima ao solo na condição crítica"],
        ["Usar vento de outra região", "Ktur e faixa errados", "Conferir a UF e a estação INMET"],
        ["Série de vento com menos de 10 anos", "Gumbel instável", "Ampliar a série ou usar outra estação"],
        ["Não resolver alertas do catálogo (R_ca 75 °C)", "Parâmetros e perdas incorretos", "Corrigir o cabo no catálogo e marcar o alerta como resolvido"]], [5.0, 5.5, 6.5])
    R.h2("Referências bibliográficas")
    R.lista(["ABNT NBR 5422:2024 – Projeto de linhas aéreas de transmissão de energia elétrica.",
             "Kiessling, F. et al. Overhead Power Lines – Planning, Design, Construction. Springer.",
             "Villas, J. E. et al. Transmissão de Energia Elétrica (cap. 8 a 10).",
             "Livro 2 – Projeto Elétrico de Linhas de Transmissão; Livro 3 – Cálculos Elétricos de Linhas de Transmissão; Livro 4 – Linhas de Transmissão.",
             "Diretrizes para Elaboração de Projetos Básicos de Linhas de Transmissão (ONS/EPE).",
             "IEEE Std 738-2006; IEEE Std 80-2013; IEC 60949; IEC 60815 (1986); IEC 60071-1; IEC 60038.",
             "REN ANEEL nº 915/2021 (limites de exposição a campos elétricos e magnéticos).",
             "Planilhas BK: CELT2-IPOG (cálculo elétrico), TFCC2-IPOG (cálculo mecânico) e LINHA DE TRANSMISSÃO 4."])
