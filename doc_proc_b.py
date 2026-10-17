"""Procedimentos – Módulos 4 a 7."""
import math

from doc_proc_a import calc_m3
from doc_proc_base import (EQ, IN_A, REF, V, T, app_tab, checklist, comparacao, dif, f, mfrac, mi, mpar, msqrt, msub, msup, mu, passos)

SQ2, SQ3 = math.sqrt(2.0), math.sqrt(3.0)


def _pe(us, kcs, fsfl, kg, kafl=1.0):
    """Parcela elétrica da distância fase-terra de frente lenta (NBR 5422:2024, 9.4.1), kz = 1 − 1,3·0,06."""
    return 2.174 * (math.exp(kcs * SQ2 / SQ3 * us * fsfl / (1080.0 * kafl * (1 - 1.3 * 0.06) * kg)) - 1.0)


# ============================================================================= M4
def calc_m4():
    m3 = calc_m3()["casos"]["v5030"]
    vp, q0 = m3["VP"], m3["q0"]
    d, p = REF["d_mm"] / 1000, REF["massa"] * 9.80665
    lm, lp, flecha, cadeia, b = 400.0, 350.0, 10.0, 2.0, 4.5
    K = 0.3 + 3.68 * math.exp(-0.163 * vp)
    beta = math.degrees(math.atan(K * q0 * d * lm / (p * lp)))
    sig = 2.25 * (1 - math.exp(-vp ** 2 / 230.0))
    bmax = beta + 2 * sig
    D_pl = REF["un"] * 1.05 / 150.0
    D_nb = _pe(REF["un"], 1.35, 2.0, 1.28)
    D = max(D_pl, D_nb)
    out = dict(vp=vp, q0=q0, d=d, p=p, lm=lm, lp=lp, flecha=flecha, cadeia=cadeia, b=b, K=K, beta=beta, sig=sig, bmax=bmax, D_pl=D_pl, D_nb=D_nb, D=D)
    for k, bb in (("med", beta), ("max", bmax)):
        dd = (cadeia + flecha) * math.sin(math.radians(bb))
        L = 2 * (b + dd + D)
        out[k] = dict(d=dd, L=L, adot=math.ceil(L))
    # distâncias de segurança (rodovia / edificação)
    pe_t, pe_l = _pe(REF["un"], 1.35, 2.0, 1.18), _pe(REF["un"], 1.25, 2.0, 1.18)
    dl = 6.0 + 0.60 + pe_l
    out.update(pe_t=pe_t, pe_l=pe_l, dv_lim=dl, dv_a=6.0 + 0.90 + pe_t, dv_b=dl + 0.90, dh=4.0 + _pe(REF["un"], 1.35, 2.0, 1.28))
    out["dv_tip"] = max(out["dv_a"], out["dv_b"])
    return out


def m4(R):
    x = calc_m4()
    R.h1("M4 – FAIXA DE DOMÍNIO (SERVIDÃO) E DISTÂNCIAS DE SEGURANÇA")
    R.h2("Objetivo e quando fazer")
    R.p("Determinar a largura da faixa de segurança considerando o balanço dos condutores sob vento, o comprimento da cadeia, a flecha e a distância de "
        "segurança elétrica, além das distâncias verticais e horizontais a obstáculos (rodovias, edificações, ferrovias etc.).")
    R.p("Projeto básico e executivo, regularização fundiária e licenciamento; sempre que houver travessias, edificações ou vegetação próximas ao traçado.", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["ABNT NBR 5422:2024 – 8.9 (ângulo de balanço: 8.9.1, 8.9.3, 8.9.4, Figura 22), 9.4.1 (d fase-terra de frente lenta), "
             "7.2 e Tabelas 5 e 6 (distâncias verticais), 7.3 e Tabela 7 (distâncias horizontais), 17.2.2.5 e 17.2.2.6 (largura da faixa).",
             "Planilha BK (aba Faixa de Servidão): D = U·1,05/150 (0,5 m até 69 kV) – critério histórico; o app adota o maior entre norma e planilha.",
             "Vento 50 anos/30 s e q0 do Módulo 3."])
    R.h2("Metodologia manual")
    R.p("Passo 1 – Ângulo de balanço médio da cadeia/condutor (8.9.1) com o vento 50/30 e o desvio-padrão (8.9.3); o ângulo máximo é β + 2σβ (8.9.4):")
    EQ(R, mi("β"), T("=atan"), mpar(mfrac(V("K") + V("q", "0") + V("d") + V("L", "m"), V("p") + V("L", "p"))), T(" ;  "), V("K"), T("=0,3+3,68·"), T("exp") + mpar(T("−0,163·") + V("V", "P30")), T(" ;  "),
       mi("σ") + msub(T(""), mi("β")), T("=2,25·"), mpar(T("1−exp") + mpar(T("−") + mfrac(msup(V("V", "P30"), T("2")), T("230")))))
    R.simbolos([("q0", "pressão dinâmica do vento 50/30 (Módulo 3)", "Pa"), ("d", "diâmetro do condutor", "m"), ("Lm", "vão médio (vão de vento)", "m"),
                ("Lp", "vão gravante (vão de peso)", "m"), ("p", "peso linear do condutor (massa × 9,80665)", "N/m"), ("K", "fator de efetividade do vento (Figura 22; K = 1 se V < 10 m/s)", "—")])
    R.p("Passo 2 – Distância de segurança D (horizontal, ao obstáculo/limite da faixa). A parcela elétrica de 9.4.1, com kzfl = 1 − 1,3·0,06:")
    EQ(R, V("d", "ft,fl"), T("=2,174·"), mpar(T("exp") + mpar(mfrac(V("K", "cs") + mfrac(msqrt(T("2")), msqrt(T("3"))) + V("U", "s") + V("F", "sfl"), T("1080·") + V("k", "afl") + V("k", "zfl") + V("k", "g"))) + T("−1")))
    R.p("O app compara esse valor com o da planilha BK (D = U·1,05/150) e adota o maior (opção configurável: norma, planilha ou maior).")
    R.p("Passo 3 – Deslocamento horizontal d e largura da faixa (17.2.2.5.1, cadeia simétrica; b = distância do eixo à fase externa):")
    EQ(R, V("d"), T("=("), V("c"), T("+"), V("f", "max"), T(")·sen"), mi("β"), T(" ;  "), V("L"), T("=2·("), V("b"), T("+"), V("d"), T("+"), V("D"), T(")"))
    R.p("Passo 4 – Distâncias a obstáculos: vertical D_V,lim = PbV + Pslim + Pelim e D_V,típ = máx(PbV + Pstip + Petip ; D_V,lim + 0,90), com Pe calculado como em 9.4.1 com o kg da Tabela 5; "
        "horizontal D_H = PbH + Petip (Tabela 7).")
    R.h2("Exemplo resolvido – LT 138 kV Exemplo")
    R.p("Dados: V_P30 e q0 do exemplo do Módulo 3; HAWK (Ø 21,78 mm; 0,9764 kg/m); Lm = 400 m; Lp = 350 m; cadeia de suspensão 2,0 m; flecha máxima 10 m; "
        "Fsfl = 2,0 (campo do Módulo 4); b = 4,5 m (fase externa).")
    passos(R, "Ângulo de balanço e faixa", [
        ("K = 0,3 + 3,68·exp(−0,163·V_P30)", f"0,3 + 3,68 × exp(−0,163 × {f(x['vp'], 2)}) = {f(x['K'], 3)}"),
        ("p = m·g", f"0,9764 × 9,80665 = {f(x['p'], 3)} N/m"),
        ("β = atan(K·q0·d·Lm/(p·Lp))", f"atan({f(x['K'], 3)} × {f(x['q0'], 0)} × 0,02178 × 400 / ({f(x['p'], 3)} × 350)) = {f(x['beta'], 2)}°"),
        ("σβ = 2,25·(1 − exp(−V²/230))", f"{f(x['sig'], 3)}°"),
        ("β máx = β + 2σβ", f"{f(x['bmax'], 2)}°"),
        ("D (planilha BK) = U·1,05/150", f"138 × 1,05/150 = {f(x['D_pl'], 3)} m"),
        ("D (NBR 5422, 9.4.1; Kcs = 1,35; kg = 1,28)", f"{f(x['D_nb'], 3)} m"),
        ("D adotado = maior dos dois", f"{f(x['D'], 3)} m"),
        ("d = (cadeia + flecha)·sen β médio", f"(2 + 10) × sen {f(x['beta'], 2)}° = {f(x['med']['d'], 2)} m"),
        ("L = 2·(b + d + D) – β médio", f"2 × (4,5 + {f(x['med']['d'], 2)} + {f(x['D'], 3)}) = {f(x['med']['L'], 2)} m → adotada {f(x['med']['adot'], 0)} m"),
        ("L com β máximo", f"d = {f(x['max']['d'], 2)} m → L = {f(x['max']['L'], 2)} m → adotada {f(x['max']['adot'], 0)} m")])
    passos(R, "Distâncias a obstáculos (exemplos)", [
        ("Rodovia: PbV = 6,0 m; Pe típ (kg 1,18; Kcs 1,35)", f"Pe = {f(x['pe_t'], 2)} m"),
        ("Rodovia: Pe lim (Kcs 1,25)", f"Pe = {f(x['pe_l'], 2)} m"),
        ("D_V,lim = 6,0 + 0,60 + Pe lim", f"{f(x['dv_lim'], 2)} m"),
        ("D_V,típ = máx(6,0 + 0,90 + Pe típ ; D_V,lim + 0,90)", f"máx({f(x['dv_a'], 2)} ; {f(x['dv_b'], 2)}) = {f(x['dv_tip'], 2)} m"),
        ("Edificação: D_H = PbH (4,0) + Pe típ (kg 1,28)", f"{f(x['dh'], 2)} m")])
    comparacao(R, "Manual × app (Módulo 4)", [
        ("K (Figura 22)", f(x["K"], 3), "0,304", dif(x["K"], 0.304)),
        ("β médio (°)", f(x["beta"], 2), "37,38", dif(x["beta"], 37.38)),
        ("β máx = β + 2σβ (°)", f(x["bmax"], 2), "41,87", dif(x["bmax"], 41.87)),
        ("D adotada (m)", f(x["D"], 3), "0,97", dif(x["D"], 0.97)),
        ("d (m)", f(x["med"]["d"], 2), "7,28", dif(x["med"]["d"], 7.28)),
        ("Faixa calculada (m)", f(x["med"]["L"], 2), "25,50", dif(x["med"]["L"], 25.50)),
        ("D_V típ. rodovia (m)", f(x["dv_tip"], 2), "8,09", dif(x["dv_tip"], 8.09)),
        ("D_H edificação (m)", f(x["dh"], 2), "4,59", dif(x["dh"], 4.59))])
    R.obs("O campo F_sfl do Módulo 4 vem com 2,0 (distâncias de segurança do regime nominal); o Módulo 5 calcula o Fsfl pela Tabela 14 (3,00 para 145 kV). "
          "Confirmar com o cliente qual valor deve valer na faixa e manter a coerência entre os módulos.")
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 4 – preenchimento", [
        ("Dados de entrada", "Vento 50 anos / 30 s", "Módulo 3", "Busca V_P30 e q0 do Módulo 3 (ou \"Informar\" manualmente)"),
        ("Dados de entrada", "Vão médio (vão de vento) Lm (m)", "400", "Do estaqueamento / vão típico"),
        ("Dados de entrada", "Vão gravante Lp (m)", "350", "Do estaqueamento"),
        ("Dados de entrada", "Flecha máx. à temp. máxima (m)", "10", "Do Módulo 13 (flecha) ou do cálculo mecânico"),
        ("Dados de entrada", "Tipo de cadeia / Disposição das fases", "Suspensão / Simétrica", "Ancoragem: comprimento da cadeia = 0"),
        ("Dados de entrada", "Comprimento da cadeia (m)", "2,0", "Do Módulo 5 (comprimento de arco + ferragens)"),
        ("Dados de entrada", "F_sfl (p.u.) / k_afl", "2,0 / 1,0", "Ver observação sobre Fsfl"),
        ("Dados de entrada", "Informar b manualmente", "desmarcado", "b vem da geometria (fase externa = 4,5 m)"),
        ("Faixa de segurança", "Ângulo de balanço", "Médio (8.9.1)", "Ou Máximo (8.9.4) para a faixa conservadora"),
        ("Distâncias de segurança", "Distância D", "Maior entre norma e planilha BK", "Alternativas: só norma ou só planilha"),
        ("Distâncias de segurança", "H – altura máx. do navio (m)", "0", "Só águas navegáveis"),
        ("Pontos e vizinhas", "Quantidade de pontos de estudo", "2", "Cadastro compartilhado com M8, M9 e M10"),
        ("Resultados e relatório", "Gerar relatório (.docx)", "—", "Contém faixa, tabelas 5 a 7 e figura")])
    R.p("Resultado esperado: K = 0,304; β = 37,38°; β máx = 41,87°; D = 0,97 m; d = 7,28 m; faixa calculada 25,50 m (adotada 26 m); com β máx., 26,95 m (27 m).")
    R.h2("Conferência")
    checklist(R, ["Vento 50/30 vindo do Módulo 3 (sem o aviso \"Falta vp\").",
                  "Lm, Lp e flecha conferem com o perfil/estaqueamento.",
                  "Ângulo de balanço (médio ou máximo) conforme o critério do cliente.",
                  "Faixa adotada arredondada para cima (múltiplo de 1 m) e coerente com o Módulo 8.",
                  "Pontos de estudo com tipo correto (rodovia, edificação, travessia)."])


# ============================================================================= M5
def calc_m5():
    um, un = REF["um"], REF["un"]
    alt, lat, lon = REF["alt"], abs(REF["lat"]), abs(REF["lon"])
    delta = 0.984 - 0.836e-4 * alt + 0.141e-5 * lat * alt - 0.788e-6 * lon * alt
    H = 21.559 - 0.00509 * alt - 0.228 * lat - 3.85e-5 * lat * alt
    Hc = 1 + 0.012 * (H / delta - 11)
    kg, kgpp = 1.45, 1.80
    kgff = 1.35 * kg - 0.35 * kg ** 2
    x = (um / SQ3) / (750 * delta * (1 - 3 * 0.03) * kgff)
    d_ff = 1.642 * (math.exp(x) - 1) ** 0.83
    kcs, fsfl = 1.121, 3.0

    def g0(d):
        return 1080 / (500 * d) * math.log(0.46 * d + 1) if d <= 3.5 else 3400 / (500 * d + 4000)

    def fl(chuva):
        d = 1.0
        for _ in range(80):
            g = g0(max(d, 0.05))
            m2 = 1.25 * g * (g - 0.2)
            ka = delta ** m2 if chuva else (delta * Hc) ** m2
            d = 0.5 * (d + _pe(um, kcs, fsfl, kg, ka))
        return d, ka
    d_seco, ka_s = fl(False)
    d_chuva, ka_c = fl(True)
    ufr = 820.0
    kz = 1 - 1.3 * 0.03
    d_pos = ufr / (530 * delta * kz * (0.74 + 0.26 * kg))
    d_neg = ufr / (700 * delta * kz * (1.5 - 0.5 * kg if kg <= 1.44 else 0.78))
    d_fr = max(d_pos, d_neg)
    req = max(d_ff, d_seco, d_chuva, d_fr)
    n_fuga = math.ceil(round(20.0 * um / 292.0, 9))
    n_arco = math.ceil(round(req / 0.146, 9))
    n = max(n_fuga, n_arco)
    return dict(delta=delta, H=H, Hc=Hc, kg=kg, kgff=kgff, d_ff=d_ff, kcs=kcs, fsfl=fsfl, d_seco=d_seco, d_chuva=d_chuva, ka_s=ka_s, ka_c=ka_c, ufr=ufr,
                d_pos=d_pos, d_neg=d_neg, d_fr=d_fr, req=req, n_fuga=n_fuga, n_arco=n_arco, n=n, fuga_nec=20.0 * um, fuga_tot=n * 292.0, l_arco=n * 0.146)


def m5(R):
    x = calc_m5()
    R.h1("M5 – COORDENAÇÃO DE ISOLAMENTO")
    R.h2("Objetivo e quando fazer")
    R.p("Definir as distâncias mínimas no ar (fase-terra e fase-fase) para as solicitações de frequência fundamental, frente lenta (manobra) e frente rápida (descarga atmosférica), "
        "dimensionar a cadeia de isoladores (fuga e distância de arco), verificar o balanço dos condutores na estrutura e coordenar os para-raios.")
    R.p("Projeto básico e executivo de qualquer LT; é pré-requisito da definição da silhueta da estrutura, da faixa e do estudo de blindagem.", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["ABNT NBR 5422:2024 – 4.5 (densidade relativa do ar δ), 4.6 e 4.8 (umidade e fatores de correção atmosférica), 9.3.2/9.3.3 (frequência fundamental), "
             "9.4.1/9.4.2 (frente lenta), 9.5 (frente rápida), Tabelas 14 (Fsfl) e 15 (Ufr), Anexo C (kg, Kcs), 14.2 (cargas mecânicas na cadeia).",
             "Diretrizes para Projetos Básicos (ONS/EPE) 3.2.13, 4.7 e 6.8.2 (fuga mínima de 14 mm/kV); IEC 60815 (1986) – níveis de poluição e fuga específica.",
             "Livro 2 – Projeto Elétrico de LTs, 4.6 e 4.7 (número de isoladores, gradiente e distribuição de tensão na cadeia)."])
    R.h2("Metodologia manual")
    R.p("Passo 1 – Atmosfera (sem medições): densidade relativa do ar δ (4.5.3), umidade absoluta H (4.6.3) e fator de umidade Hc (4.8):")
    EQ(R, mi("δ"), T("=0,984−0,836·10"), msup(T(""), T("−4")), V("alt"), T("+0,141·10"), msup(T(""), T("−5")), V("lat"), V("alt"), T("−0,788·10"), msup(T(""), T("−6")), V("lon"), V("alt"),
       T(" ;  "), V("H", "c"), T("=1+0,012·"), mpar(mfrac(V("H"), mi("δ")) + T("−11")))
    R.p("Passo 2 – Frequência fundamental fase-terra (9.3.2), com kz = 1 − 3·0,03 e kg_ff = 1,35·kg − 0,35·kg² (Tabela C.1):")
    EQ(R, V("d", "ft,ff"), T("=1,642·"), msup(mpar(T("exp") + mpar(mfrac(mfrac(V("U", "m"), msqrt(T("3"))) + V("F", "tmo"), T("750·") + mi("δ") + T("·") + V("k", "z") + T("·") + V("k", "g,ff"))) + T("−1")), T("0,83")))
    R.p("Passo 3 – Frente lenta fase-terra (9.4.1). Como kafl = (δ·Hc)^m2 depende da própria distância (m2 = 1,25·G0·(G0 − 0,2)), a solução é iterativa (ponto fixo). "
        "Calcula-se com tempo seco e com chuva (kafl = δ^m2) e adota-se o maior d. Kcs (fator de coordenação estatístico, Anexo C.3) é calculado pelo app a partir dos CV da "
        "sobretensão (15 %) e da rigidez do gap (5 %), do número de gaps em paralelo (3) e do risco admitido (10⁻³).")
    EQ(R, V("d", "ft,fl"), T("=2,174·"), mpar(T("exp") + mpar(mfrac(V("K", "cs") + mfrac(msqrt(T("2")), msqrt(T("3"))) + V("U", "m") + V("F", "sfl"), T("1080·") + V("k", "afl") + V("k", "zfl") + V("k", "g"))) + T("−1")),
       T(" ;  "), V("F", "sfl"), T("(Tabela 14: ≤ 362 kV → 3,00)"))
    R.p("Passo 4 – Frente rápida (9.5): maior entre as polaridades positiva e negativa, com Ufr da Tabela 15 e kz = 1 − 1,3·0,03:")
    EQ(R, V("d", "+"), T("="), mfrac(V("U", "fr"), T("530·") + mi("δ") + V("k", "z") + V("k", "g+")), T(" ;  "), V("d", "−"), T("="), mfrac(V("U", "fr"), T("700·") + mi("δ") + V("k", "z") + V("k", "g−")),
       T(" ;  "), V("k", "g+"), T("=0,74+0,26·"), V("k", "g"), T(" ;  "), V("k", "g−"), T("=1,5−0,5·"), V("k", "g"))
    R.p("Passo 5 – Cadeia de isoladores: o número de unidades é o maior entre o necessário pela fuga (fuga específica × Um / fuga da unidade) e pela distância de arco "
        "(distância fase-terra governante / passo da unidade). Conferir também a distribuição de tensão na cadeia (escada capacitiva) e o gradiente GI = fuga total / (Um/√3).")
    EQ(R, V("N", "fuga"), T("=⌈"), mfrac(V("f", "esp") + V("U", "m"), V("f", "unid")), T("⌉ ;  "), V("N", "arco"), T("=⌈"), mfrac(V("d", "req"), V("p")), T("⌉ ;  "), V("N"), T("=máx("), V("N", "fuga"), T(";"), V("N", "arco"), T(")"))
    R.h2("Exemplo resolvido – LT 138 kV Exemplo")
    R.p("Dados: Um = 145 kV; altitude 870 m; lat −27,6°; lon −48,5°; Fsfl = 3,00 (Tabela 14); Ufr = 820 kV (Tabela 15 – 138 kV); kg fase-terra = 1,45 (braço de torre); "
        "Kcs = 1,121 (calculado pelo app, Anexo C.3); isolador de vidro com fuga 292 mm e passo 146 mm; poluição nível II (20 mm/kV).")
    passos(R, "Distâncias no ar e cadeia", [
        ("δ (4.5.3)", f"{f(x['delta'], 4)}"),
        ("H (4.6.3) e Hc (4.8)", f"H = {f(x['H'], 3)} g/m³; Hc = {f(x['Hc'], 4)}"),
        ("kg_ff = 1,35·1,45 − 0,35·1,45²", f"{f(x['kgff'], 4)}"),
        ("d fase-terra, freq. fundamental (9.3.2)", f"{f(x['d_ff'], 3)} m"),
        ("d fase-terra, frente lenta – tempo seco (iteração)", f"{f(x['d_seco'], 3)} m (kafl = {f(x['ka_s'], 4)})"),
        ("d fase-terra, frente lenta – chuva (iteração)", f"{f(x['d_chuva'], 3)} m (kafl = {f(x['ka_c'], 4)})"),
        ("d+ e d− (frente rápida; Ufr = 820 kV)", f"{f(x['d_pos'], 3)} m e {f(x['d_neg'], 3)} m → d_fr = {f(x['d_fr'], 3)} m"),
        ("d fase-terra requerida = maior", f"{f(x['req'], 3)} m (governa a frente rápida)"),
        ("N pela fuga = ⌈20·145/292⌉", f"{f(x['fuga_nec'], 0)} mm / 292 mm → {x['n_fuga']} unidades"),
        ("N pelo arco = ⌈d_req/0,146⌉", f"⌈{f(x['req'], 3)}/0,146⌉ = {x['n_arco']} unidades"),
        ("N adotado = máx.", f"{x['n']} unidades; distância de arco {f(x['l_arco'], 3)} m; fuga total {f(x['fuga_tot'], 0)} mm")])
    comparacao(R, "Manual × app (Módulo 5)", [
        ("δ", f(x["delta"], 4), "0,9119", dif(x["delta"], 0.9119)),
        ("d fase-terra, freq. fundamental (m)", f(x["d_ff"], 3), "0,275", dif(x["d_ff"], 0.275)),
        ("d fase-terra, frente lenta (m)", f(max(x["d_seco"], x["d_chuva"]), 3), "0,744", dif(max(x["d_seco"], x["d_chuva"]), 0.744)),
        ("d fase-terra, frente rápida (m)", f(x["d_fr"], 3), "1,714", dif(x["d_fr"], 1.714)),
        ("Isoladores por cadeia", str(x["n"]), "12", "—"),
        ("Distância de arco (m)", f(x["l_arco"], 3), "1,752", dif(x["l_arco"], 1.752)),
        ("Fuga total (mm)", f(x["fuga_tot"], 0), "3.504", dif(x["fuga_tot"], 3504))])
    R.p("Resultados do app não calculados à mão neste exemplo: fase-fase (d_ff frequência 0,426 m; frente lenta 0,853 m; frente rápida 1,754 m), balanço das fases na silhueta "
        "(fase central a 0,50–0,70 m do fuste não atende frente lenta/rápida com cadeia de suspensão em I, exigindo estrutura mais larga ou cadeia em V) e o para-raios (Ur = 108 kV).")
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 5 – preenchimento", [
        ("Atmosfera e sobretensões", "Altitude (m) / Latitude (°) / Longitude (°)", "870 / −27,6 / −48,5", "Herda do Módulo 3 se preenchido"),
        ("Atmosfera e sobretensões", "Densidade relativa do ar (δ)", "Sem medições (NBR 5422, 4.5.3)", "Com medições: informar p, t e UR"),
        ("Atmosfera e sobretensões", "Fator de sobretensão de manobra Fsfl", "Tabela 14 (sem estudo)", "3,00 para Um ≤ 362 kV; informar se houver estudo de transitórios"),
        ("Atmosfera e sobretensões", "Ufr (frente rápida)", "Tabela 15", "820 kV para 138 kV"),
        ("Atmosfera e sobretensões", "Fatores de gap kg / Geometria fase-terra (C.1) / fase-fase (C.3) / α", "Tabelas C.1 e C.3 / Braço de torre / Anel–anel / 0,5", "Escolher a geometria real da janela"),
        ("Atmosfera e sobretensões", "Kcs / CV da sobretensão / CV da rigidez / Nº de gaps / Risco", "Calculado (Anexo C.3) / 15 % / 5 % / 3 / 0,001", "Ou \"Informado\" / \"Referência 1,05\""),
        ("Atmosfera e sobretensões", "rs (relação fase-fase, 9.4.2) / Ftmo", "1,4 / 1,0", ""),
        ("Isoladores", "Tipo de isolador / Tipo de cadeia", "Vidro / Suspensão em I", ""),
        ("Isoladores", "Nível de poluição / Fuga específica", "II – Médio / Nível de poluição (IEC 60815:1986)", "Selecionar explicitamente; 20 mm/kV"),
        ("Isoladores", "Aplicar mínimo de 14 mm/kV (Diretrizes 6.8.2)", "marcado", "Piso quando a poluição é leve"),
        ("Isoladores", "Fuga da unidade / Passo da unidade (mm)", "292 / 146", "Do catálogo do isolador"),
        ("Isoladores", "Comprimento de ferragens (m) / Nº mínimo de unidades", "0,3 / 1", ""),
        ("Isoladores", "Capacitância à terra / própria (c1/C)", "0,1", "Distribuição de tensão na cadeia"),
        ("Estrutura e balanço", "Vão médio Lm / vão gravante Lp (m)", "400 / 350", "Herda do Módulo 4"),
        ("Estrutura e balanço", "Semi-largura do fuste (m) / Altura do corpo abaixo da fase mais baixa (m)", "0,5 / 10", "Silhueta da estrutura"),
        ("Para-raios e coordenação", "Uc/Ur / ke / Ktov / Margem no equipamento", "0,8 / 1,4 / 1,1 / 15 %", "Padrões; ajustar ao catálogo do para-raios")])
    R.p("Resultado esperado: Fsfl 3,00; Ufr 820 kV; δ 0,9119; Kcs 1,121; d fase-terra 1,714 m; d fase-fase 1,754 m; 12 isoladores; distância de arco 1,752 m; fuga 3.504 mm; Ur 108 kV.")
    R.h2("Conferência")
    checklist(R, ["Um e Un corretos (Módulo 1) e Fsfl coerente com o Módulo 4.",
                  "Geometria kg (C.1 e C.3) igual à silhueta real da estrutura.",
                  "Nível de poluição aprovado pelo cliente; fuga ≥ 14 mm/kV.",
                  "Cada fase atende freq./manobra/descarga no balanço; fases \"✗\" exigem revisão da estrutura ou da cadeia.",
                  "Quando d_fr > d_ff, a norma (9.5.3.3) exige o estudo de desempenho a descargas (Módulo 16)."])


# ============================================================================= M6
def calc_m6():
    rho_a, a_esp = 500.0, 2.0
    r_med = rho_a / (2 * math.pi * a_esp)
    L, h, a = 30.0, 0.5, 6.15 / 2000.0       # cabo aço cobreado 40 % - 25 mm² (d_ext 6,15 mm)
    r_dw = rho_a / (2 * math.pi * L) * (math.log(2 * L / a) + math.log(L / h) - 2 + 2 * h / L - (h / L) ** 2)
    ifalta, t = 4.181, 0.5
    ar, rho_r, tcap, k0, tm, ta = 0.00378, 4.397, 3.846, 1 / 0.00408, 250.0, 26.0
    s_min = ifalta * math.sqrt(t * ar * rho_r * 1e4 / (tcap * math.log((k0 + tm) / (k0 + ta))))
    r4 = 11.00
    gpr = ifalta * 1000 * r4
    toque = (1000 + 1.5 * rho_a) * 0.157 / math.sqrt(t)
    passo = (1000 + 6 * rho_a) * 0.157 / math.sqrt(t)
    ig = rho_a * 300e3 / (2 * math.pi * r4 ** 2)
    ri = r4 / math.sqrt(1 + 31.1e3 / ig)
    le = 1.4 * math.sqrt(rho_a)
    return dict(rho_a=rho_a, a=a_esp, r_med=r_med, L=L, h=h, d=6.15, r_dw=r_dw, ifalta=ifalta, t=t, s_min=s_min, r4=r4, gpr=gpr / 1e3, toque=toque, passo=passo,
                ig=ig / 1e3, ri=ri, le=le)


def m6(R):
    x = calc_m6()
    R.h1("M6 – ATERRAMENTO DAS ESTRUTURAS")
    R.h2("Objetivo e quando fazer")
    R.p("Projetar o aterramento de pé de torre (contrapeso radial) para atingir a resistência-meta, a partir da resistividade do solo medida; verificar o comportamento sob impulso "
        "(descargas), a seção mínima do condutor para a corrente de falta e as tensões de passo e toque.")
    R.p("Em todo projeto de LT (desempenho a descargas e segurança de pessoas); a resistência de pé de torre alimenta os módulos 9 e 16.", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["Wenner (4 eletrodos): ρ = 2π·a·R; estratificação do solo em 2 camadas por ajuste de mínimos quadrados (série de imagens, Tagg).",
             "Dwight/Sunde (eletrodo horizontal enterrado); CIGRE/IEEE (comprimento efetivo Le = 1,4·√ρ e ionização do solo).",
             "IEEE Std 80-2013 – eq. 29 a 32 (tensões admissíveis de passo e toque) e eq. 37 (seção mínima); planilha BK, aba Aterramento."])
    R.h2("Metodologia manual")
    R.p("Passo 1 – Resistividade aparente medida por Wenner (a = espaçamento dos eletrodos; R = resistência lida):")
    EQ(R, mi("ρ"), T("=2π·"), V("a"), V("R"))
    R.p("Passo 2 – Resistência de um condutor horizontal enterrado (fórmula de Dwight, L = comprimento, h = profundidade, a = raio do cabo). Para n pernas radiais o app resolve o "
        "sistema pelo método dos momentos (ponto-colocação); a resistência cai com n e com L, mas o ganho some acima do comprimento efetivo.")
    EQ(R, V("R", "1"), T("="), mfrac(mi("ρ"), T("2π") + V("L")), T("·"), mpar(T("ln") + mpar(mfrac(T("2") + V("L"), V("a"))) + T("+ln") + mpar(mfrac(V("L"), V("h"))) + T("−2+") + mfrac(T("2") + V("h"), V("L")) + T("−") + msup(mpar(mfrac(V("h"), V("L"))), T("2"))))
    R.p("Passo 3 – Comportamento sob impulso (ionização do solo) e comprimento efetivo:")
    EQ(R, V("R", "i"), T("="), mfrac(V("R", "0"), msqrt(T("1+") + mfrac(V("I"), V("I", "g")))), T(" ;  "), V("I", "g"), T("="), mfrac(mi("ρ") + V("E", "0"), T("2π") + msup(V("R", "0"), T("2"))), T(" ;  "), V("L", "e"), T("=1,4·"), msqrt(mi("ρ")))
    R.p("Passo 4 – Seção mínima do condutor pela corrente de falta (IEEE 80, eq. 37), com TCAP em J/(cm³·°C), ρr em µΩ·cm, K0 = 1/α0:")
    EQ(R, V("A"), T("="), V("I"), msqrt(mfrac(V("t") + mi("α") + V("r") + mi("ρ") + V("r") + T("·10") + msup(T(""), T("4")), V("TCAP") + T("ln") + mpar(mfrac(V("K", "0") + T("+") + V("T", "m"), V("K", "0") + T("+") + V("T", "a"))))))
    R.p("Passo 5 – GPR e tensões admissíveis (pessoa de 70 kg, Cs = 1 sem camada superficial de brita):")
    EQ(R, V("GPR"), T("="), V("I", "f"), V("R"), T(" ;  "), V("E", "toque"), T("="), mfrac(mpar(T("1000+1,5·") + V("C", "s") + mi("ρ") + T("")) + T("·0,157"), msqrt(V("t"))), T(" ;  "),
       V("E", "passo"), T("="), mfrac(mpar(T("1000+6·") + V("C", "s") + mi("ρ")) + T("·0,157"), msqrt(V("t"))))
    R.h2("Exemplo resolvido – LT 138 kV Exemplo")
    passos(R, "Aterramento – ρ = 500 Ω·m, 4 pernas de 30 m a 0,5 m, cabo aço cobreado 40 % de 25 mm² (Ø 6,15 mm)", [
        ("ρ (Wenner, a = 2 m; R lido = 39,79 Ω)", f"2π × 2 × 39,79 = {f(2 * math.pi * 2 * 39.79, 0)} Ω·m (valor adotado: 500 Ω·m)"),
        ("R de 1 perna (Dwight; L = 30 m; h = 0,5 m; a = 3,075 mm)", f"{f(x['r_dw'], 2)} Ω"),
        ("R de 4 pernas radiais (método dos momentos – app)", f"{f(x['r4'], 2)} Ω (meta 20 Ω: atende)"),
        ("Le = 1,4·√ρ", f"1,4 × √500 = {f(x['le'], 1)} m (as pernas de 30 m estão no limite do efetivo)"),
        ("Ig = ρ·E0/(2π·R0²), E0 = 300 kV/m", f"{f(x['ig'], 1)} kA"),
        ("Ri = R0/√(1 + I/Ig), I = 31,1 kA", f"{f(x['ri'], 2)} Ω (R impulsiva)"),
        ("Seção mínima (IEEE 80 eq. 37; If = 4,181 kA; 0,5 s; Tm = 250 °C)", f"{f(x['s_min'], 2)} mm² → adotar ≥ 25 mm²"),
        ("GPR = If·R", f"4.181 A × {f(x['r4'], 2)} Ω = {f(x['gpr'], 1)} kV"),
        ("E_toque adm. = (1000 + 1,5·500)·0,157/√0,5", f"{f(x['toque'], 0)} V"),
        ("E_passo adm. = (1000 + 6·500)·0,157/√0,5", f"{f(x['passo'], 0)} V")])
    comparacao(R, "Manual × app (Módulo 6)", [
        ("R de pé de torre – 4 pernas (Ω)", "usa o script (momentos)", "11,00", "—"),
        ("R impulsiva (Ω)", f(x["ri"], 2), "10,23", dif(x["ri"], 10.23)),
        ("Seção mínima (mm²)", f(x["s_min"], 1), "25,0", dif(x["s_min"], 25.0)),
        ("GPR (kV)", f(x["gpr"], 1), "46,0", dif(x["gpr"], 46.0)),
        ("E_toque admissível (V)", f(x["toque"], 0), "389", dif(x["toque"], 389)),
        ("E_passo admissível (V)", f(x["passo"], 0), "888", dif(x["passo"], 888))])
    R.p("A resistência de uma perna isolada (Dwight) serve de conferência de ordem de grandeza; o app valida o método dos momentos com a mesma fórmula para n = 1. "
        "Se o solo não for uniforme, usar as medições Wenner (≥ 4 pontos) para ajustar ρ1, ρ2 e h1 (2 camadas).", italico=False)
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 6 – preenchimento", [
        ("Solo", "Modelo do solo", "Uniforme", "Ou \"Medições Wenner (2 camadas)\" / \"2 camadas (ρ1, ρ2, h1)\""),
        ("Solo", "Resistividade aparente ρ (Ω·m)", "500", "Média das medições de campo"),
        ("Solo", "Fator sazonal (×)", "1,0", "Multiplicador para a estação seca/chuvosa"),
        ("Solo", "ρ da camada superficial (Ω·m)", "0", "0 = sem brita"),
        ("Contrapeso e meta", "Cabo contrapeso", "Aço Cobreado 40 % - 25 mm²", "Banco \"DB Aterramento\""),
        ("Contrapeso e meta", "Nº de pernas radiais / Comprimento de cada perna (m) / Profundidade (m)", "4 / 30 / 0,5", ""),
        ("Contrapeso e meta", "Resistência de referência (Ω)", "20", "Meta de projeto do cliente"),
        ("Curto-circuito e tensões", "Material do condutor / Tipo de conexão", "Aço Cobreado 40 % / Mecânica", "Define Tm (250 °C)"),
        ("Curto-circuito e tensões", "Temperatura ambiente (°C) / Duração do curto (s)", "26 / 0,5", ""),
        ("Curto-circuito e tensões", "Parcela de If no condutor / que escoa pela torre (%)", "100 / 100", "Conservador"),
        ("Curto-circuito e tensões", "Pessoa (peso)", "70 kg", "50 ou 70 kg")])
    R.p("Resultado esperado: R = 11,00 Ω (meta 20 Ω); R impulsiva 10,23 Ω; seção mínima 25,0 mm²; GPR 46,0 kV; E_toque 389 V; E_passo 888 V.")
    R.h2("Conferência")
    checklist(R, ["ρ medido em época representativa (aplicar fator sazonal se a medição foi na estação chuvosa).",
                  "Perna do contrapeso ≤ comprimento efetivo 1,4√ρ; acima disso o ganho é pequeno.",
                  "Seção do cabo ≥ seção mínima pela corrente de falta e pela conexão adotada.",
                  "GPR e tensões de passo/toque avaliadas quando houver pessoas próximas (subestação, cercas, travessias).",
                  "R de pé de torre repassada aos módulos 9 e 16."])


# ============================================================================= M7
def calc_m7():
    p_kw = REF["mva"] * 1e3 * REF["fp"]
    i = p_kw / (SQ3 * REF["un"] * REF["fp"])
    sinphi = math.sqrt(1 - REF["fp"] ** 2)
    r_perda = 0.02 * p_kw * 1000 / (3 * REF["km"] * i ** 2)
    lim = 0.05 * REF["un"] * 1000 / (SQ3 * i * REF["km"])
    xk = 0.4
    r_dv = (lim - xk * sinphi) / REF["fp"]
    rho75 = 28.264 * (1 + 0.004 * 55)
    s_min = rho75 / min(r_perda, r_dv)
    r75 = REF["r20"] * (1 + REF["alfa_r"] * 55)
    perda = 3 * i ** 2 * r75 * REF["km"] * 1.03 / 1e6
    qc, qr, qs = 39.93, 9.82, 10.89
    i738 = math.sqrt((qc + qr - qs) / (r75 * 1e-3))
    kst = math.sqrt(3.8e-3 * (202 + 20) / 138e-6 * math.log((202 + 200) / (202 + 40)))
    s_cc = 10000 * math.sqrt(0.5) / kst
    return dict(p_kw=p_kw, i=i, r_perda=r_perda, r_dv=r_dv, lim=lim, rho75=rho75, s_min=s_min, r75=r75, perda=perda, perda_pct=perda / (p_kw / 1e3) * 100, i738=i738, kst=kst, s_cc=s_cc,
                qc=qc, qr=qr, qs=qs)


def m7(R):
    x = calc_m7()
    R.h1("M7 – DIMENSIONAMENTO DO CONDUTOR E DO CABO GUARDA")
    R.h2("Objetivo e quando fazer")
    R.p("Verificar eletricamente o condutor de fase (corrente, perda joule, queda de tensão, ampacidade) e o cabo guarda/OPGW (curto-circuito), e comparar o cabo escolhido com os demais do "
        "catálogo. É o dimensionamento elétrico; o dimensionamento mecânico (tração, flechas) é feito no cálculo mecânico e no Módulo 13.")
    R.p("Na escolha do condutor (projeto básico) e na revisão de projetos existentes.", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["ONS – Nota Técnica de Ampacidade Sazonal de LTs (ampacidade por estação/período); IEEE Std 738-2006 (balanço térmico em regime permanente).",
             "IEC 60949 – cálculo da corrente de curto-circuito admissível (adiabático); Diretrizes para Projetos Básicos (perdas e queda de tensão máximas).",
             "Planilha BK \"LINHA DE TRANSMISSÃO 4\" (critérios 1 a 5; o app corrige as unidades da planilha, ver notas no relatório)."])
    R.h2("Metodologia manual")
    R.p("Critério 1 – Corrente de projeto; Critério 2 – perda joule máxima (p % da potência ativa); Critério 3 – queda de tensão máxima (ΔV %):")
    EQ(R, V("I"), T("="), mfrac(V("P"), msqrt(T("3")) + V("U") + mi("cos φ")), T(" ;  3·"), V("R"), T("·"), V("L"), msup(V("I"), T("2")), T("≤"), mfrac(V("p"), T("100")), V("P"), T(" ;  "),
       msqrt(T("3")), V("I"), V("L"), mpar(V("R") + mi("cos φ") + T("+") + V("X") + mi("sen φ")), T("≤"), mfrac(mi("ΔV"), T("100")), V("U"))
    R.p("A seção equivalente em alumínio resulta da resistência máxima admissível: S ≥ ρ(T)/R_máx, com ρ(75 °C) = 28,264·[1 + 0,004·(75 − 20)] Ω·mm²/km. "
        "A resistência do cabo à temperatura de operação é R(T) = R20·[1 + α·(T − 20)].")
    R.p("Critério 4 – Ampacidade: o balanço térmico em regime permanente iguala o calor gerado ao dissipado por convecção (qc) e radiação (qr), descontado o ganho solar (qs):")
    EQ(R, msup(V("I"), T("2")), V("R"), T("("), V("T", "c"), T(")"), T("="), V("q", "c"), T("+"), V("q", "r"), T("−"), V("q", "s"), T(" ;  "), V("I"), T("="), msqrt(mfrac(V("q", "c") + T("+") + V("q", "r") + T("−") + V("q", "s"), V("R") + mpar(V("T", "c"))) ))
    R.p("Critério 5 – Curto-circuito (IEC 60949, adiabático): S_mín = I_cc·√t / k, com k = √[ Qc·(β + 20)/ρ20 · ln((β + θf)/(β + θi)) ]. Para OPGW usa-se a capacidade do fabricante (kA²·s) quando houver.")
    EQ(R, V("S", "mín"), T("="), mfrac(V("I", "cc") + msqrt(V("t")), V("k")), T(" ;  "), V("k"), T("="), msqrt(mfrac(V("Q", "c") + mpar(mi("β") + T("+20")), mi("ρ") + msub(T(""), T("20"))) + T("ln") + mpar(mfrac(mi("β") + T("+") + mi("θ") + msub(T(""), T("f")), mi("β") + T("+") + mi("θ") + msub(T(""), T("i"))))))
    R.h2("Exemplo resolvido – LT 138 kV Exemplo")
    R.p("Critérios do exemplo: perda máxima 2 % de P, queda de tensão máxima 5 %, X' = 0,4 Ω/km, fator de catenária 3 %, temperatura normal 75 °C.")
    passos(R, "Critérios básicos e verificação do HAWK", [
        ("P = S·cosφ; I = P/(√3·U·cosφ)", f"P = {f(x['p_kw'], 0)} kW; I = {f(x['i'], 1)} A"),
        ("R máx. por perda = (0,02·P)/(3·L·I²)", f"{f(x['r_perda'], 4)} Ω/km"),
        ("R máx. por queda = (ΔV·U/(√3·I·L) − X·senφ)/cosφ", f"({f(x['lim'], 4)} − 0,4 × 0,3122)/0,95 = {f(x['r_dv'], 4)} Ω/km"),
        ("ρ(75 °C) = 28,264·(1 + 0,004·55)", f"{f(x['rho75'], 3)} Ω·mm²/km"),
        ("S mín. equivalente em Al = ρ(75)/R máx.", f"{f(x['rho75'], 3)} / {f(min(x['r_perda'], x['r_dv']), 4)} = {f(x['s_min'], 0)} mm²"),
        ("R do HAWK a 75 °C = 0,1196·(1 + 0,00403·55)", f"{f(x['r75'], 4)} Ω/km"),
        ("Perda = 3·I²·R·L·1,03", f"{f(x['perda'], 2)} MW = {f(x['perda_pct'], 2)} % de P → limite 2 %: NÃO ATENDE"),
        ("I (IEEE 738) = √[(qc + qr − qs)/R(75)], com qc = 39,93; qr = 9,82; qs = 10,89 W/m", f"{f(x['i738'], 0)} A (app: 515,77 A)"),
        ("Guarda EHS 7/16\": k (aço; 40 → 200 °C)", f"{f(x['kst'], 1)}"),
        ("S mín. no EHS = 10.000·√0,5 / k (Icc = 10 kA; 0,5 s)", f"{f(x['s_cc'], 0)} mm² > 74,45 mm² → margem {f(74.45 / x['s_cc'], 2)}× → NÃO ATENDE (app: 0,59×)"),
        ("OPGW 12,4 mm: I²t = (10 kA)²·0,5 s", "50 kA²·s contra capacidade do fabricante ≈ 49 kA²·s → margem 0,98× → NÃO ATENDE")])
    comparacao(R, "Manual × app (Módulo 7)", [
        ("Corrente nominal (A)", f(x["i"], 1), "251,0", dif(x["i"], 251.0)),
        ("R máx. por perda (Ω/km)", f(x["r_perda"], 4), "0,0754", dif(x["r_perda"], 0.0754)),
        ("R máx. por queda de tensão (Ω/km)", f(x["r_dv"], 4), "0,0773", dif(x["r_dv"], 0.0773)),
        ("Seção mín. equivalente Al (mm²)", f(x["s_min"], 0), "457", dif(x["s_min"], 457)),
        ("Perdas joule (MW)", f(x["perda"], 2), "2,28", dif(x["perda"], 2.28)),
        ("Corrente IEEE 738 a 75 °C (A)", f(x["i738"], 1), "515,77", dif(x["i738"], 515.77))])
    R.p("Conclusão didática: o HAWK atende à ampacidade (251 A contra 515 A pela IEEE 738 e 660 A de catálogo), mas não à perda joule (3,99 % contra 2 %) nem à queda de tensão para 80 km. "
        "O app lista os cabos do catálogo que atendem a todos os critérios (por exemplo, MAGNOLIA 954 MCM e CAMELIA 1000 MCM). "
        "Com Icc = 10 kA durante 0,5 s e 100 % da corrente no guarda, os dois guardas também não atendem (OPGW 0,98×; EHS 0,59×): ou se reduz a parcela de corrente que circula no guarda "
        "(divisão com o solo e a malha), ou se escolhe um guarda de maior capacidade.")
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 7 – preenchimento", [
        ("Dados de entrada", "Potência ativa da LT (kW) / Tensão nominal (kV) / Fator de potência / Comprimento (km)", "57.000 / 138 / 0,95 / 80", "Herda do Módulo 1"),
        ("Dados de entrada", "Perda joule máxima (% de P) / Queda de tensão máxima (%)", "2 / 5", "Critérios do cliente/Diretrizes"),
        ("Dados de entrada", "Reatância X' da fase (Ω/km)", "0,4", "Usar X' do Módulo 2 (≈ 0,49 Ω/km) quando disponível"),
        ("Dados de entrada", "Fator de catenária (%)", "3", "Acréscimo de comprimento do cabo"),
        ("Condutor (critérios)", "Temperatura normal / de emergência (°C)", "75 / 90", ""),
        ("Condutor (critérios)", "Comparar com todos os condutores do catálogo / Só os que atendem", "marcado / marcado", "Gera a lista de alternativas"),
        ("Ampacidade", "UF (vento 0,9 m/s: PR, RS, SC, RJ, ES, SE, AL)", "SC", "Define o vento da ampacidade ONS"),
        ("Ampacidade", "Altitude / Emissividade / Absortividade", "870 / 0,5 / 0,5", ""),
        ("Ampacidade", "Ta verão dia / noite; inverno dia / noite (°C)", "33 / 25; 32 / 24", "Temperaturas ambientes ONS"),
        ("Ampacidade", "Radiação solar / Vento IEEE / Ta máx. IEEE", "1000 W/m² / 0,61 m/s / 40 °C", "Condições da IEEE 738"),
        ("Cabo guarda / OPGW", "Corrente de curto-circuito (kA) / Duração (s)", "10 / 0,5", "Do estudo de curto"),
        ("Cabo guarda / OPGW", "Parcela da corrente no guarda (%) / Temperatura inicial / final (°C)", "100 / 40 / 200", "Conservador")])
    R.p("Resultado esperado: I = 251,0 A; R máx. 0,0754 e 0,0773 Ω/km; seção mínima 457 mm²; perdas 2,28 MW (3,99 %); temperatura do condutor em 251 A: 53,9 °C.")
    R.h2("Conferência")
    checklist(R, ["Potência e FP do circuito conferem com o Módulo 1.",
                  "X' da fase vem do Módulo 2 (a premissa 0,4 Ω/km é só um padrão).",
                  "Critérios de perda e queda de tensão são os do cliente.",
                  "Ampacidade do cabo × corrente de emergência com folga.",
                  "Guarda: capacidade de curto do OPGW (kA²·s) do fabricante; EHS pela IEC 60949."])
