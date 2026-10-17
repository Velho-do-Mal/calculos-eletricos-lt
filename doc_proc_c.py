"""Procedimentos – Módulos 8 a 11 (campos, interferência, RI/RA e corona)."""
import cmath
import math

import numpy as np

import calc_campos as cc
from doc_proc_a import calc_m2
from doc_proc_base import (EQ, IN_A, REF, V, T, app_tab, checklist, comparacao, dif, f, mfrac, mi, mpar, msqrt, msub, msup, mu, passos)

SQ3 = math.sqrt(3.0)
EPS0 = cc.EPS0
FASES = [("A", -4.5, 24.0), ("B", 0.0, 24.0), ("C", 4.5, 24.0)]
RADIUS = REF["d_mm"] / 2000.0


def pontos_app(R):
    """Bloco comum de cadastro de linhas vizinhas e pontos de estudo (módulos 4, 8, 9 e 10)."""
    R.p("O cadastro de linhas vizinhas e de pontos é feito na aba \"Pontos e vizinhas\", que é a mesma nos módulos 4, 8, 9 e 10: o que for cadastrado em um aparece nos outros. "
        "Cadastre cada linha/rede uma única vez e use-a em quantos pontos precisar.")
    app_tab(R, "Cadastro comum de linhas vizinhas e pontos de estudo (caso de referência)", [
        ("Pontos e vizinhas", "Biblioteca – Nome / Tipo / Disposição das fases / Nº de circuitos", "LT 69 kV / Linha de transmissão / Horizontal / 1", "Até 8 linhas vizinhas"),
        ("Pontos e vizinhas", "Tensão nominal (kV)", "69", ""),
        ("Pontos e vizinhas", "Espaçamento horizontal / vertical entre fases (m)", "3,0 / 0,0", "Geometria da vizinha"),
        ("Pontos e vizinhas", "Altura média da fase mais baixa (m)", "12", ""),
        ("Pontos e vizinhas", "Como informar a corrente normal / Corrente normal (A) / Emergência (A)", "Informar corrente (A) / 200 / 0", "0 = igual à normal; ou \"A partir de P e Q\""),
        ("Pontos e vizinhas", "Sentido do fluxo / Sequência de fases / Defasagem angular", "Mesmo sentido da LT / ABC / Pior caso (automático)", "O pior caso varre 0–360° nos campos"),
        ("Pontos e vizinhas", "Quantidade de pontos de estudo (máx. 12)", "2", ""),
        ("Pontos e vizinhas", "Ponto 1 – Nome / Tipo de ponto / Lado / Carga da LT em estudo", "Paralelismo A / Paralelismo com LT/rede / Direito / Emergência", "Tipos: seção livre, travessia, paralelismo, rodovia/ferrovia, edificação, duto/telecom"),
        ("Pontos e vizinhas", "Ponto 1 – Vizinha / Distância horizontal entre eixos (m) / Comprimento do paralelismo (km) / Ângulo entre eixos (°)", "LT 69 kV / 25 / 1,0 / 0", "Ângulo 0° = paralelismo perfeito"),
        ("Pontos e vizinhas", "Ponto 2 – Nome / Tipo / Carga da LT", "Casa / Edificação/residência / Normal", ""),
        ("Pontos e vizinhas", "Ponto 2 – Distância horizontal do eixo ao ponto (m) / Altura de referência (m)", "20 / 1,5", "Altura do receptor acima do solo")])


# ============================================================================= M8
def calc_m8():
    xs = np.array([f_[1] for f_ in FASES])
    ys = np.array([f_[2] for f_ in FASES])
    req = np.full(3, RADIUS)
    P = cc.matriz_potencial(xs, ys, req)
    Vf = np.array([cc.tensao_fase(REF["un"], n) for n, _, _ in FASES])
    q = np.linalg.solve(P, Vf)
    I = np.array([cc.corrente_fase(IN_A, n, fp=REF["fp"]) for n, _, _ in FASES])
    p = cc.profundidade_complexa(REF["rho"], REF["f"])
    out = dict(P=P, q=q, I=I, p=p, Vf=Vf)
    for X in (0, 10, 13, 20):
        ex, ey = cc.campo_e_cargas(q, xs, ys, np.array([float(X)]), np.array([1.5]))
        bx, by = cc.campo_b_correntes(I, xs, ys, np.array([float(X)]), np.array([1.5]), p)
        out[X] = dict(ex=ex[0], ey=ey[0], bx=bx[0], by=by[0], E=math.sqrt(abs(ex[0]) ** 2 + abs(ey[0]) ** 2) / 1e3, B=math.sqrt(abs(bx[0]) ** 2 + abs(by[0]) ** 2) * 1e6)
    xx = np.arange(-50, 50.01, 0.5)
    ex, ey = cc.campo_e_cargas(q, xs, ys, xx, np.full_like(xx, 1.5))
    out["Emax"] = float(np.max(np.sqrt(np.abs(ex) ** 2 + np.abs(ey) ** 2)) / 1e3)
    out["x_Emax"] = float(xx[int(np.argmax(np.sqrt(np.abs(ex) ** 2 + np.abs(ey) ** 2)))])
    return out


def m8(R):
    x = calc_m8()
    R.h1("M8 – CAMPO ELÉTRICO E MAGNÉTICO")
    R.h2("Objetivo e quando fazer")
    R.p("Calcular os campos elétrico (kV/m) e magnético (µT) da LT ao nível do solo, em perfil lateral e em pontos de interesse (borda da faixa, edificações, rodovias, "
        "paralelismos), considerando linhas vizinhas e o pior caso de defasagem, e comparar com os limites de exposição do público e dos trabalhadores.")
    R.p("Em todo projeto de LT (licenciamento e atendimento à regulamentação), principalmente com edificações próximas ou paralelismos.", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["REN ANEEL nº 915/2021 – limites de exposição: público 4,17 kV/m e 200 µT; ocupacional 8,33 kV/m e 1000 µT (NECESSITA VALIDAÇÃO com o texto oficial).",
             "Relatório ESS-2ITA-595-87 (Energisa/IOSI), 3.1 (campo elétrico) e 3.2 (campo magnético); Livro 3 – Cálculos Elétricos de LTs, cap. 6.",
             "Diretrizes para Projetos Básicos, 6.10 (campos na faixa de passagem); altura de referência do observador: 1,5 m."])
    R.h2("Metodologia manual")
    R.p("Passo 1 – Campo elétrico por simulação de cargas. Monta-se a matriz de coeficientes de potencial dos condutores (com as imagens no solo) e resolvem-se as cargas por unidade de comprimento "
        "a partir das tensões fase-neutro (fasores, sequência positiva). Os cabos guarda são desprezados por padrão (têm efeito pequeno ao nível do solo).")
    EQ(R, msub(V("P"), T("ii")), T("="), mfrac(T("1"), T("2π") + msub(mi("ε"), mu("0"))), T("ln") + mpar(mfrac(T("2") + msub(V("h"), mu("i")), msub(V("r"), mu("i")))), T(" ;  "),
       msub(V("P"), T("ij")), T("="), mfrac(T("1"), T("2π") + msub(mi("ε"), mu("0"))), T("ln") + mpar(mfrac(msub(V("D'"), T("ij")), msub(V("D"), T("ij")))), T(" ;  ["), V("Q"), T("]=["), V("P"), msup(T("]"), T("−1")), T("["), V("U"), T("]"))
    R.p("Passo 2 – O campo em um ponto (x, y) é a soma das contribuições das cargas e de suas imagens (−y); com fasores complexos, a intensidade eficaz é E = √(|Ex|² + |Ey|²).")
    EQ(R, msub(V("E"), mu("x")), T("="), mfrac(msub(V("q"), mu("i")), T("2π") + msub(mi("ε"), mu("0"))), T("∑"), mpar(mfrac(V("x") + T("−") + msub(V("x"), mu("i")), msup(V("r"), mu("1")) ) + T("−") + mfrac(V("x") + T("−") + msub(V("x"), mu("i")), msup(V("r"), mu("2")))), T(" ;  "),
       V("E"), T("="), msqrt(msup(T("|Ex|"), T("2")) + T("+") + msup(T("|Ey|"), T("2"))))
    R.p("Passo 3 – Campo magnético por Biot-Savart com o retorno pelo solo representado por imagens complexas (Deri), a profundidade complexa p = √(ρ/(jωµ0)); a intensidade é B = √(|Bx|² + |By|²):")
    EQ(R, V("B"), T("="), mfrac(msub(mi("μ"), mu("0")) + V("I"), T("2π")), T("∑"), mpar(mfrac(T("1"), msub(V("r"), mu("1"))) + T("−") + mfrac(T("1"), msub(V("r"), mu("2")))), T(" ;  "), V("p"), T("="), msqrt(mfrac(mi("ρ"), T("j") + mi("ω") + msub(mi("μ"), mu("0")))))
    R.p("Passo 4 – Com linhas vizinhas, somam-se os fasores de cada fonte; a defasagem entre os sistemas é varrida de 0° a 360° e vale o pior caso. Compara-se o valor na borda da faixa (Módulo 4) e nos pontos "
        "de interesse com o limite aplicável (público ou ocupacional).")
    R.h2("Exemplo resolvido – LT 138 kV Exemplo (somente a LT em estudo)")
    R.p("Ponto de interesse: casa a 20 m do eixo, observador a 1,5 m do solo; condutores a 24 m (flecha não abatida); Un = 138 kV; I = 251 A, cosφ = 0,95; ρ = 1000 Ω·m. "
        "As três fases têm a mesma altura e o mesmo raio (10,89 mm).")
    P = x["P"]
    passos(R, "Campo elétrico e magnético na casa", [
        ("P11 = ln(2h/r)/(2πε0)", f"ln(48/0,01089)/(2π × 8,854e-12) = {f(P[0, 0] / 1e11, 3)} × 10¹¹ m/F"),
        ("P12 e P13 (D'/D)", f"P12 = {f(P[0, 1] / 1e11, 3)}; P13 = {f(P[0, 2] / 1e11, 3)} (× 10¹¹ m/F)"),
        ("Tensões fase-neutro (fasores)", "79,67 kV ∠0°, ∠−120°, ∠+120°"),
        ("Cargas Q = P⁻¹·U (módulo)", f"{f(abs(x['q'][0]) * 1e9, 1)}; {f(abs(x['q'][1]) * 1e9, 1)}; {f(abs(x['q'][2]) * 1e9, 1)} nC/m"),
        ("Profundidade complexa |p| = |√(ρ/(jωµ0))|", f"{f(abs(x['p']), 0)} m"),
        ("Correntes: 251 A ∠(−120°·k − 18,19°)", "251 A em cada fase, atrasadas de acos(0,95)"),
        ("E no ponto (x = 20 m; y = 1,5 m)", f"|Ex| = {f(abs(x[20]['ex']), 1)} V/m; |Ey| = {f(abs(x[20]['ey']), 1)} V/m → E = {f(x[20]['E'], 3)} kV/m"),
        ("B no ponto (x = 20 m; y = 1,5 m)", f"B = {f(x[20]['B'], 3)} µT"),
        ("E máximo do perfil (±50 m, passo 0,5 m)", f"{f(x['Emax'], 3)} kV/m em x = ±{f(abs(x['x_Emax']), 1)} m"),
        ("Verificação (público)", f"E = {f(x[20]['E'], 2)} ≤ 4,17 kV/m e B = {f(x[20]['B'], 2)} ≤ 200 µT → ATENDE")])
    comparacao(R, "Manual × app (Módulo 8, ponto \"Casa\", LT sem vizinhas)", [
        ("E no ponto (kV/m)", f(x[20]["E"], 3), "0,192", dif(x[20]["E"], 0.192)),
        ("B no ponto (µT)", f(x[20]["B"], 3), "0,432", dif(x[20]["B"], 0.432)),
        ("E máx. do perfil (kV/m)", f(x["Emax"], 3), "0,211", dif(x["Emax"], 0.211)),
        ("Limite E / B (público)", "4,17 kV/m / 200 µT", "4,17 / 200", "—")])
    R.p("Observação didática: com os condutores a 24 m do solo e a LT isolada, os campos são muito inferiores aos limites. Em paralelismos (ponto \"Paralelismo A\") o app soma a LT de 69 kV vizinha "
        "com defasagem em pior caso: E máx. 0,451 kV/m e B máx. 1,898 µT, ainda ATENDE.")
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 8 – preenchimento (aba Dados de entrada)", [
        ("Dados de entrada", "Tensão para o campo elétrico", "Nominal", "Ou \"Máxima operativa\" (conservador)"),
        ("Dados de entrada", "Correntes de cálculo", "Corrente nominal do circuito (Módulo 1)", "Ou \"Informada\""),
        ("Dados de entrada", "Altura dos condutores", "Automático (altura na estrutura − flecha)", "Ou informar a altura mínima ao solo (conservador)"),
        ("Dados de entrada", "Largura da faixa (para o valor na borda)", "Do Módulo 4", "Ou informar"),
        ("Dados de entrada", "Altura do observador (m)", "1,5", "Referência de exposição"),
        ("Dados de entrada", "Perfil: x mínimo / x máximo / passo (m)", "−50 / 50 / 0,5", ""),
        ("Dados de entrada", "Resistividade do solo (Ω·m)", "1000", "Usada na imagem complexa do campo B"),
        ("Dados de entrada", "Raio equivalente dos cabos das vizinhas (mm)", "15", "Premissa para as vizinhas"),
        ("Dados de entrada", "Incluir guardas aterrados no E", "desmarcado", "Padrão: desprezados"),
        ("Resultados e relatório", "Limite do ponto (Paralelismo A / Casa)", "Público em geral", "Ocupacional apenas onde houver trabalhadores"),
        ("Resultados e relatório", "Ponto para o gráfico / Cenário", "Casa / Normal", "Mostra o perfil lateral de E e B")])
    pontos_app(R)
    R.p("Resultado esperado: Casa – E 0,192 kV/m e B 0,432 µT (ATENDE); Paralelismo A – E máx. 0,451 kV/m e B máx. 1,898 µT (ATENDE).")
    R.h2("Conferência")
    checklist(R, ["Altura mínima ao solo coerente com o Módulo 13 (use a altura mínima na flecha máxima para o campo elétrico máximo).",
                  "Correntes: normal e de emergência; vizinhas com tensão e corrente corretas.",
                  "Defasagem entre sistemas: pior caso quando desconhecida.",
                  "Limites aplicáveis (público/ocupacional) corretos para cada ponto.",
                  "Faixa do Módulo 4 disponível (senão o valor na borda não é avaliado)."])


# ============================================================================= M9
def calc_m9():
    rho, fr = REF["rho"], REF["f"]
    h = 24.0
    fz = [dict(n=n, x=x_, y=h) for n, x_, _ in FASES]
    I = [cc.corrente_fase(IN_A, f_["n"], fp=REF["fp"]) for f_ in fz]
    de = 659.0 * math.sqrt(rho / fr)
    d_lat, cota, L = 25.0, -1.5, 1.0
    dist = [math.hypot(f_["x"] - d_lat, f_["y"] - cota) for f_ in fz]

    def zm(d):
        return (0.00159 * fr + 1j * 0.00477 * fr * math.log10(de / d)) / 1.609344
    z = [zm(d) for d in dist]
    v_norm = abs(sum(i * zz for i, zz in zip(I, z))) * L
    if_ = 5.0e3
    v_ind = [if_ * abs(zz) * 1.0 * L for zz in z]
    ig = if_ * 1.0 * 1.0
    v_res = min(rho * ig / (2 * math.pi * d_lat), ig * 20.0)
    k = int(np.argmax(v_ind))
    return dict(de=de, dist=dist, z=z, v_norm=v_norm, v_ind=v_ind, k=k, ig=ig, v_res=v_res, total=v_ind[k] + v_res, nomes=[f_["n"] for f_ in fz])


def m9(R):
    x = calc_m9()
    R.h1("M9 – INTERFERÊNCIA E COMPATIBILIDADE ELETROMAGNÉTICA")
    R.h2("Objetivo e quando fazer")
    R.p("Avaliar a tensão induzida pela LT em estruturas metálicas próximas (polidutos, gasodutos, cabos de telecomunicações e controle, ferrovias/rodovias), em regime normal "
        "(acoplamento indutivo) e em falta fase-terra (acoplamentos indutivo e resistivo), e compará-la com os limites de segurança e de isolamento.")
    R.p("Quando a faixa tem paralelismo ou travessia com dutos, cabos de telecomunicação, ferrovias ou outras instalações metálicas.", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["Villas et al., Transmissão de Energia Elétrica, cap. 10 (acoplamentos resistivo, indutivo e capacitivo; 10.1.2 e 10.3); Livro 3 – impedâncias mútuas de Carson.",
             "Limites do acervo: poliduto/gasoduto 5 kV (perfuração do revestimento); cabo telefônico/controle ≈ 1,6 kV; regime normal: 15 V (valor de segurança de contato, configurável).",
             "Não calculado: acoplamento capacitivo e modelo distribuído do duto (impedância característica e condutância do revestimento) – exigem estudo detalhado."])
    R.h2("Metodologia manual")
    R.p("Passo 1 – Impedância mútua de Carson entre a fase k e a instalação a distância d_k (Ω/km; milha = 1,609344 km) e profundidade equivalente do retorno pelo solo:")
    EQ(R, msub(V("z"), T("m")), T("="), mfrac(T("0,00159·") + V("f") + T("+j·0,00477·") + V("f") + T("·log") + msub(T(""), T("10")) + mpar(mfrac(msub(V("D"), T("e")), msub(V("d"), T("k")))), T("1,609344")), T(" ;  "),
       msub(V("D"), T("e")), T("=659·"), msqrt(mfrac(mi("ρ"), V("f"))))
    R.p("Passo 2 – FEM longitudinal em regime normal (fasores das três fases; geometria sem transposição = conservador), com L_ef = comprimento do paralelismo × cos(ângulo entre eixos):")
    EQ(R, V("V"), T("="), msub(V("L"), T("ef")), T("·"), T("|"), T("∑"), msub(V("I"), mu("k")), msub(V("z"), T("m,k")), T("|"))
    R.p("Passo 3 – Falta fase-terra na torre mais próxima. FEM indutiva com fator de blindagem dos guardas κ (= 1 se desprezados); acoplamento resistivo pela dispersão da corrente na torre:")
    EQ(R, msub(V("V"), T("ind")), T("="), msub(V("I"), T("f")), msub(V("z"), T("m")), mi("κ"), msub(V("L"), T("ef")), T(" ;  "), mi("κ"), T("="), T("|1−"), mfrac(msub(V("z"), T("pg")), msub(V("z"), T("gg"))), T("|"), T(" ;  "),
       msub(V("V"), T("res")), T("="), mfrac(mi("ρ") + msub(V("I"), T("g")), T("2π") + msub(V("d"), T("t"))), T("≤ "), msub(V("I"), T("g")), msub(V("R"), T("pé")))
    R.p("A tensão total é V_ind + V_res (sem atenuação para telecomunicações; para dutos pode-se aplicar o fator de atenuação 0,5 do app para extremos isolados). O resultado é comparado ao limite do ponto.")
    R.h2("Exemplo resolvido – LT 138 kV Exemplo e cabo telefônico a 25 m")
    R.p("Dados: duto/cabo na cota −1,5 m, a 25 m do eixo; paralelismo de 1 km e ângulo 0°; ρ = 1000 Ω·m; 60 Hz; falta fase-terra 5 kA, 100 % da corrente na torre; "
        "R de pé de torre 20 Ω; sem blindagem dos guardas (κ = 1, conservador); fases a 24 m; corrente normal 251 A.")
    passos(R, "Tensão induzida no cabo telefônico", [
        ("De = 659·√(ρ/f)", f"659 × √(1000/60) = {f(x['de'], 1)} m"),
        ("Distâncias fase–cabo d_k (A, B, C)", "; ".join(f"{n}: {f(d, 2)} m" for n, d in zip(x["nomes"], x["dist"]))),
        ("|z_m| (A, B, C) em Ω/km", "; ".join(f"{n}: {f(abs(z), 4)}" for n, z in zip(x["nomes"], x["z"]))),
        ("FEM em regime normal = L·|Σ I_k·z_m,k|", f"{f(x['v_norm'], 2)} V (limite 15 V → ATENDE)"),
        ("V_ind (falta) = I_f·|z_m|·κ·L (pior fase)", f"5.000 × {f(abs(x['z'][x['k']]), 4)} × 1 × 1 = {f(x['v_ind'][x['k']], 0)} V (fase {x['nomes'][x['k']]})"),
        ("I_g = κ·I_f·fração na torre", f"{f(x['ig'], 0)} A"),
        ("V_res = mín(ρ·I_g/(2π·d_t); I_g·R_pé); d_t = 25 m", f"mín({f(1000 * x['ig'] / (2 * math.pi * 25), 0)}; {f(x['ig'] * 20, 0)}) = {f(x['v_res'], 0)} V"),
        ("Tensão total = V_ind + V_res", f"{f(x['total'], 0)} V contra o limite de 1.600 V → NÃO ATENDE")])
    comparacao(R, "Manual × app (Módulo 9, Paralelismo A)", [
        ("FEM em regime normal (V)", f(x["v_norm"], 2), "2,95", dif(x["v_norm"], 2.95)),
        ("FEM de falta + resistivo (V)", f(x["total"], 0), "33.559", dif(x["total"], 33559))])
    R.p("Conclusão: a contribuição resistiva (31,8 kV) domina porque o cabo está a apenas 25 m da torre. Medidas usuais: aumentar a distância, reduzir R de pé de torre, "
        "considerar a blindagem dos guardas (κ < 1), instalar para-raios/blindagem no cabo ou estudar o duto com modelo distribuído.")
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 9 – preenchimento", [
        ("Dados de entrada", "Resistividade do solo (Ω·m)", "1000", "Mesmo valor do Módulo 6/8"),
        ("Dados de entrada", "Blindagem dos cabos guarda", "Sem blindagem (conservador)", "\"Com cabos guarda\" calcula κ por Carson"),
        ("Dados de entrada", "Fator de tensão à terra / FEM (poliduto)", "0,5", "Atenuação do extremo isolado do duto"),
        ("Dados de entrada", "Corrente de falta fase-terra (kA)", "5", "Do estudo de curto-circuito"),
        ("Dados de entrada", "Fração da corrente de terra pela torre sob falta", "1,0", "Conservador"),
        ("Dados de entrada", "Resistência de pé de torre (Ω)", "20", "Resultado do Módulo 6 (ou meta)"),
        ("Dados de entrada", "Limite em regime normal (V)", "15", ""),
        ("Dados de entrada", "Cota do duto/cabo (m; negativa = enterrado)", "−1,5", ""),
        ("Pontos e vizinhas", "Tipo de ponto / Limite do ponto", "Paralelismo / Cabo telefônico / controle (1,6 kV)", "Opções: Poliduto 5 kV; Informar limite"),
        ("Pontos e vizinhas", "Distância, comprimento do paralelismo, ângulo", "25 m / 1,0 km / 0°", "Cadastro comum (ver M8)")])
    R.p("Altura dos condutores e correntes seguem as premissas do Módulo 8. Resultado esperado: regime normal 2,95 V (ATENDE); falta + resistivo 33.559 V contra 1.600 V (NÃO ATENDE).")
    R.h2("Conferência")
    checklist(R, ["Tipo de instalação e limite corretos (poliduto 5 kV; cabo telefônico 1,6 kV).",
                  "Distância à torre mais próxima e ao eixo medidas em planta.",
                  "Corrente de falta e R de pé de torre coerentes com os estudos de curto-circuito e M6.",
                  "Decidir o uso de κ (guardas) com base em dados reais dos guardas.",
                  "Registrar que o acoplamento capacitivo não foi calculado."])


# ============================================================================= M10
def calc_m10():
    um = REF["um"]
    xs = np.array([-4.5, 0.0, 4.5, 0.0, 6.0])
    ys = np.array([24.0, 24.0, 24.0, 30.0, 30.0])
    rq = np.array([RADIUS] * 3 + [0.0062, 0.005555])
    P = cc.matriz_potencial(xs, ys, rq)
    Vv = np.array([cc.tensao_fase(um, n) for n in "ABC"] + [0, 0])
    q = np.linalg.solve(P, Vv)
    E = [abs(q[i]) / (2 * math.pi * EPS0 * RADIUS) / 1e5 for i in range(3)]
    delta = 3.92 * 76 * 10 ** (-REF["alt"] / 18336.0) / (273 + 25)
    r_cm = RADIUS * 100
    ev = 21.1 * 0.85 * delta * (1 + 0.301 / math.sqrt(delta * r_cm))
    out = dict(E=E, delta=delta, ev=ev)
    pts = {}
    for xp in (20.0, -20.0):
        ri_k, ri_f, ra = [], [], []
        for i in range(3):
            D = max(math.hypot(xp - xs[i], 1.5 - ys[i]), 1.0)
            ri_k.append(3.5 * E[i] + 12 * r_cm - 33 * math.log10(D / 20.0) - 30)
            ri_f.append(53.7 + 3.5 * (E[i] - 16.95) + 40 * math.log10(2 * r_cm / 3.93) - 4.0 + 20 * 1.6 * math.log10(20.0 / D))
        npa = [-164.6 + 120 * math.log10(E[i]) + 55 * math.log10(REF["d_mm"]) for i in range(3)]
        tot = sum(math.exp(0.23 * (npa[i] - 11.4 * math.log10(max(math.hypot(xp - xs[i], 1.5 - ys[i]), 1.0)) - 5.8)) for i in range(3))
        ra = 10 * math.log10(tot)

        def comb(n):
            s = sorted(n, reverse=True)
            return s[0] if s[0] - s[1] >= 3 else (s[0] + s[1]) / 2 + 1.5
        pts[xp] = dict(ri_k=comb(ri_k), ri_f=comb(ri_f), ra=ra, nk=ri_k, nf=ri_f, npa=npa)
    out["pts"] = pts
    out["pior"] = max(pts, key=lambda k: pts[k]["ri_k"])
    return out


def m10(R):
    x = calc_m10()
    pp = x["pts"][x["pior"]]
    R.h1("M10 – RÁDIO INTERFERÊNCIA (RI) E RUÍDO AUDÍVEL (RA)")
    R.h2("Objetivo e quando fazer")
    R.p("Calcular o gradiente superficial dos condutores e, a partir dele, os níveis de rádio-interferência (dB acima de 1 µV/m) e de ruído audível (dB(A)) na borda da faixa e em "
        "edificações, comparando com os limites de projeto.")
    R.p("LTs de 138 kV ou mais, com receptores sensíveis (residências, escolas, estações de rádio) e exigência ambiental/do cliente.", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["Kiessling et al., Overhead Power Lines – 2.3.3 (gradiente por simulação de cargas, eq. 2.12 a 2.23), RI eq. 2.24 a 2.26, RA eq. 2.27 a 2.29.",
             "Villas, Transmissão de Energia, 8.3.2.1 (método FG alemão, eq. 7 a 9); Diretrizes 6.10 (RI/RA no limite da faixa).",
             "Limites do app (editáveis): RI 55 dBµV/m; RA 58 dB(A) – PREMISSAS a validar com o edital. Condutores na altura mínima e tensão máxima operativa."])
    R.h2("Metodologia manual")
    R.p("Passo 1 – Gradiente superficial máximo de cada fase pela simulação de cargas (mesma matriz do Módulo 8, agora com os guardas aterrados, V = 0, e a tensão máxima operativa). "
        "Para feixe de n subcondutores multiplica-se pelo fator de feixe (1 + k2·r/s); para n = 1, o fator é 1.")
    EQ(R, msub(V("E"), mu("i")), T("="), mfrac(msub(V("Q"), mu("i")), T("2π") + msub(mi("ε"), mu("0")) + V("n") + V("r")), mpar(T("1+") + mfrac(msub(V("k"), T("2")) + V("r"), V("s"))), T(" ;  "), msub(V("k"), T("2")), T("=2(n−1)·sen"), mpar(mfrac(mi("π"), V("n"))))
    R.p("Passo 2 – RI do método 1 (Kiessling, tempo bom, 1 MHz): por fase, depois combinação pela regra de 3 dB (se o maior nível supera o segundo em ≥ 3 dB vale o maior; senão média dos dois maiores + 1,5 dB):")
    EQ(R, msub(V("NF"), mu("i")), T("=3,5·"), msub(V("E"), mu("i")), T("+12·"), msub(V("r"), mu("i")), T("−33·log"), msub(T(""), T("10")), mpar(mfrac(msub(V("D"), mu("i")), T("20"))), T("−30"))
    R.p("Passo 3 – RI do método 2 (FG alemão, valor de 50 %; E_n = −4 dB para n = 1; K = 3,5; K_D = 1,6; E_FW = 0 em tempo bom ou 17 dB em chuva):")
    EQ(R, V("E", "RI"), T("=53,7+3,5·("), V("g"), T("−16,95)+40·log"), msub(T(""), T("10")), mpar(mfrac(V("d"), T("3,93"))), T("+"), msub(V("E"), T("n")), T("+20·1,6·log"), msub(T(""), T("10")), mpar(mfrac(T("20"), V("D"))), T("+"), msub(V("E"), T("FW")))
    R.p("Passo 4 – RA (Chartier & Stearns / BPA), com r_e = d (n < 3) ou 0,58·n^0,48·d (n ≥ 3), d em mm, D em m:")
    EQ(R, msub(V("NPA"), mu("i")), T("=−164,6+120·log"), msub(T(""), T("10")), msub(V("E"), mu("i")), T("+55·log"), msub(T(""), T("10")), msub(V("r"), T("e")), T(" ;  "), V("RA"), T("=10·log"), msub(T(""), T("10")), T("∑ exp[0,23·("), msub(V("NPA"), mu("i")), T("−11,4·log"), msub(T(""), T("10")), msub(V("D"), mu("i")), T("−5,8)]"))
    R.p("Passo 5 – Gradiente crítico visual de Peek (comparação): E_v = 21,1·m·δ·(1 + 0,301/√(δ·r)) kV/cm, com r em cm e δ = 3,92·p/(273 + t), p = 76·10^(−h/18336) cmHg.")
    R.h2("Exemplo resolvido – LT 138 kV Exemplo (ponto \"Casa\" a 20 m)")
    R.p("Condições: tensão máxima 145 kV; condutores a 24 m; guardas a 30 m aterrados; altitude 870 m; 25 °C; m = 0,85; observador a 1,5 m; HAWK n = 1, r = 1,089 cm.")
    passos(R, "Gradiente, RI e RA", [
        ("Gradientes máximos E_i = |Q_i|/(2π·ε0·r) (kV_ef/cm)", f"A = {f(x['E'][0], 2)}; B = {f(x['E'][1], 3)}; C = {f(x['E'][2], 2)}"),
        ("δ do ar", f"3,92 × 76 × 10^(−870/18336)/(273 + 25) = {f(x['delta'], 3)}"),
        ("E visual de Peek", f"21,1 × 0,85 × {f(x['delta'], 3)} × (1 + 0,301/√({f(x['delta'], 3)} × 1,089)) = {f(x['ev'], 2)} kV/cm"),
        ("RI Kiessling por fase em x = " + f(abs(x['pior']), 0) + " m (A, B, C)", "; ".join(f(v, 1) for v in pp["nk"]) + " dBµV/m"),
        ("RI Kiessling combinado (regra de 3 dB)", f"{f(pp['ri_k'], 1)} dBµV/m"),
        ("RI FG combinado", f"{f(pp['ri_f'], 1)} dBµV/m"),
        ("RA combinado", f"{f(pp['ra'], 1)} dB(A)"),
        ("Verificação", f"RI {f(max(pp['ri_k'], pp['ri_f']), 1)} ≤ 55 dBµV/m e RA {f(pp['ra'], 1)} ≤ 58 dB(A) → ATENDE")])
    comparacao(R, "Manual × app (Módulo 10)", [
        ("Gradiente máximo fase B (kV/cm)", f(x["E"][1], 3), "13,065", dif(x["E"][1], 13.065)),
        ("Gradiente crítico visual (kV/cm)", f(x["ev"], 1), "21,0", dif(x["ev"], 21.0)),
        ("RI Kiessling na casa (dBµV/m)", f(pp["ri_k"], 1), "23,6", dif(pp["ri_k"], 23.6)),
        ("RI FG na casa (dBµV/m)", f(pp["ri_f"], 1), "20,8", dif(pp["ri_f"], 20.8)),
        ("RA na casa (dB(A))", f(pp["ra"], 1), "22,9", dif(pp["ra"], 22.9))])
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 10 – preenchimento", [
        ("Dados de entrada", "Condição climática", "Tempo bom", "Ou \"Chuva\" (RI com +17 dB no método FG; corona em chuva)"),
        ("Dados de entrada", "Altura do ponto de medição (m)", "1,5", ""),
        ("Dados de entrada", "Fator de superfície m (Peek)", "0,85", "Condutor encordoado novo/usado"),
        ("Dados de entrada", "Perfil: ± x (m)", "60", "Extensão do perfil lateral"),
        ("Dados de entrada", "Altitude (m) / Temperatura ambiente (°C)", "870 / 25", "Densidade relativa do ar"),
        ("Dados de entrada", "Critério de limite", "Limite fixo", "Ou \"Sinal a proteger − relação S/N\""),
        ("Dados de entrada", "Limite de RI na faixa (dB µV/m) / Limite de RA na faixa (dB(A))", "55 / 58", "PREMISSAS: confirmar com o cliente"),
        ("Dados de entrada", "Incluir guardas aterrados no gradiente (conservador)", "marcado", "Aumenta o gradiente"),
        ("Pontos e vizinhas", "Pontos de estudo", "Paralelismo A, Casa", "Cadastro comum (ver M8). Vizinhas não entram no RI/RA (PENDENTE)")])
    R.p("Resultado esperado: gradiente máximo 13,07 kV/cm (fase B); crítico visual 21,0 kV/cm; Casa – RI 23,6 dBµV/m (Kiessling) e 20,8 (FG); RA 22,9 dB(A); ATENDE.")
    R.h2("Conferência")
    checklist(R, ["Gradiente < ~17 kV/cm (acima disso espera-se RI/RA elevados).",
                  "Condição de chuva avaliada para RA e para o método FG quando solicitado.",
                  "Limites de RI/RA do edital (55 dBµV/m e 58 dB(A) são premissas do app).",
                  "Altura mínima dos condutores e posição do receptor em planta.",
                  "Linhas vizinhas não consideradas: registrar a limitação no relatório."])


# ============================================================================= M11
def calc_m11():
    um, un = REF["um"], REF["un"]
    delta = 3.92 * 76 * 10 ** (-REF["alt"] / 18336.0) / (273 + 25)
    r_cm = RADIUS * 100
    D_cm = (4.5 * 4.5 * 9.0) ** (1 / 3) * 100
    out = dict(delta=delta, r_cm=r_cm, D_cm=D_cm)
    for nome, mt in (("seco", 1.0), ("chuva", 0.8)):
        e0 = 21.1 * 0.85 * mt * delta * (1 + 0.301 / math.sqrt(delta * r_cm))
        uc = 84 * 0.85 * mt * delta * r_cm * 1 * math.log10(D_cm / r_cm)
        out[nome] = dict(mt=mt, e0=e0, uc=uc, vc=uc / SQ3)
    out["v_un"], out["v_um"] = un / SQ3, um / SQ3
    vc = out["chuva"]["vc"]
    v_ilus = 95.0
    out["perda_ilus"] = 241 / delta * (REF["f"] + 25) * math.sqrt(r_cm / D_cm) * (v_ilus - vc) ** 2 * 1e-5
    out["v_ilus"] = v_ilus
    return out


def m11(R):
    x = calc_m11()
    m10 = calc_m10()
    R.h1("M11 – EFEITO CORONA")
    R.h2("Objetivo e quando fazer")
    R.p("Verificar a ocorrência de efeito corona: gradiente superficial máximo, gradiente crítico disruptivo e tensão crítica de Peek (tempo bom e chuva) e perdas por corona. "
        "O estudo é independente do M10 e pode ser emitido sozinho para clientes que pedem somente o corona.")
    R.p("Projetos de 138 kV ou mais, altitudes elevadas ou condutores de pequeno diâmetro; sempre que o cliente exigir a verificação de perdas por corona.", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["Kiessling 2.3.3 (gradiente superficial) e 7.3.4 (perdas, informativo); Livro 2 – Projeto Elétrico de LTs, 3.2.5 (tensão crítica) e 3.2.6 (perdas de Peek); Livro 3, cap. 7.",
             "Gradiente de referência g0 = 21,1 kV/cm (usual) ou 21,6 kV/cm (Livro 3); a equação (1) do Livro 3 está ilegível no OCR – NECESSITA VALIDAÇÃO.",
             "Limite usual de perdas: 1,2 kW/km (trifásica) – Livro 3/Villas; 1,24 kW/km no Livro 2."])
    R.h2("Metodologia manual")
    R.p("Passo 1 – Densidade relativa do ar (Peek) e gradiente crítico disruptivo (r em cm; m = fator de superfície; mt = 0,8 em chuva):")
    EQ(R, mi("δ"), T("="), mfrac(T("3,92·") + V("p"), T("273+") + V("θ")), T(" ;  "), V("p"), T("=76·10"), msup(T(""), mpar(T("−") + mfrac(V("h"), T("18336")))), T(" ;  "), msub(V("E"), T("0")), T("="), msub(V("g"), T("0")), V("m"), mi("δ"), mpar(T("1+") + mfrac(T("0,301"), msqrt(mi("δ") + V("r")))))
    R.p("Passo 2 – Tensão crítica disruptiva (kV entre fases) e fase-neutro; r' é o raio equivalente do feixe (r' = r para n = 1) e D a distância média geométrica entre fases:")
    EQ(R, msub(V("U"), T("c")), T("=84·"), msub(V("m"), T("c")), msub(V("m"), T("t")), mi("δ"), V("r"), V("n"), T("log"), msub(T(""), T("10")), mpar(mfrac(V("D"), V("r'"))), T(" ;  "), msub(V("V"), T("c")), T("="), mfrac(msub(V("U"), T("c")), msqrt(T("3"))))
    R.p("Passo 3 – Perdas por efeito corona (Peek), por fase, quando V > Vc (V e Vc fase-neutro em kV; r e D na mesma unidade; f em Hz):")
    EQ(R, V("P"), T("="), mfrac(T("241"), mi("δ")), mpar(V("f") + T("+25")), msqrt(mfrac(V("r"), V("D"))), msup(mpar(V("V") + T("−") + msub(V("V"), T("c"))), T("2")), T("·10"), msup(T(""), T("−5")), T("  [kW/km/fase]"))
    R.p("Passo 4 – Verificações: E_máx/E_0 < 1 (sem corona visual); V/Vc < 1 (sem corona); perda trifásica ≤ limite (1,2 kW/km). O gradiente máximo é o do Módulo 10 (simulação de cargas).")
    R.h2("Exemplo resolvido – LT 138 kV Exemplo")
    r = x["seco"]
    c = x["chuva"]
    passos(R, "Peek – tempo bom e chuva", [
        ("δ (870 m; 25 °C)", f"{f(x['delta'], 3)}"),
        ("E0 tempo bom = 21,1·0,85·δ·(1 + 0,301/√(δ·r))", f"{f(r['e0'], 2)} kV/cm"),
        ("E0 chuva (m·mt, mt = 0,8)", f"{f(c['e0'], 2)} kV/cm"),
        ("Gradiente máximo (Um = 145 kV; fase B)", f"{f(m10['E'][1], 3)} kV/cm → E/E0 = {f(m10['E'][1] / r['e0'], 3)} (seco) e {f(m10['E'][1] / c['e0'], 3)} (chuva)"),
        ("Uc = 84·mc·mt·δ·r·n·log10(D/r')", f"84 × 0,85 × 1 × {f(x['delta'], 3)} × 1,089 × log10({f(x['D_cm'], 1)}/1,089) = {f(r['uc'], 1)} kV"),
        ("Vc = Uc/√3 (tempo bom)", f"{f(r['vc'], 2)} kV"),
        ("Vc (chuva; mt = 0,8)", f"{f(c['vc'], 2)} kV"),
        ("V/Vc em Um (145/√3 = 83,72 kV)", f"{f(x['v_um'] / r['vc'], 3)} (seco) e {f(x['v_um'] / c['vc'], 3)} (chuva) → V < Vc: sem corona"),
        ("Perda de corona", "0 kW/km (V < Vc) → ATENDE (limite 1,2 kW/km)"),
        ("Ilustração da equação de perdas (V = 95 kV hipotético, Vc chuva)", f"P = (241/{f(x['delta'], 3)})·85·√(1,089/{f(x['D_cm'], 1)})·({f(x['v_ilus'], 0)}−{f(c['vc'], 1)})²·10⁻⁵ = {f(x['perda_ilus'], 2)} kW/km/fase")])
    comparacao(R, "Manual × app (Módulo 11)", [
        ("E0 de Peek – tempo bom (kV/cm)", f(r["e0"], 3), "20,972", dif(r["e0"], 20.972)),
        ("E0 de Peek – chuva (kV/cm)", f(c["e0"], 3), "16,778", dif(c["e0"], 16.778)),
        ("Vc tempo bom (kV)", f(r["vc"], 3), "109,299", dif(r["vc"], 109.299)),
        ("Vc chuva (kV)", f(c["vc"], 3), "87,439", dif(c["vc"], 87.439)),
        ("V/Vc em Um – chuva", f(x["v_um"] / c["vc"], 3), "0,957", dif(x["v_um"] / c["vc"], 0.957))])
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 11 – preenchimento", [
        ("Dados de entrada", "Altura dos condutores", "Automático (altura na estrutura − flecha)", "Ou informar a altura mínima (conservador)"),
        ("Dados de entrada", "Altitude (m) / Temperatura ambiente (°C)", "870 / 25", "Entra em δ"),
        ("Dados de entrada", "Fator de superfície m", "0,85", "Condutor novo 0,8–0,9; usado ≈ 0,85"),
        ("Dados de entrada", "Fator de tempo mt (chuva)", "0,8", "Livro 2, 3.2.5"),
        ("Dados de entrada", "Gradiente de referência g0 (Peek)", "21,1 kV/cm (usual)", "Ou 21,6 (Livro 3): menos conservador"),
        ("Dados de entrada", "Limite de perda corona (kW/km, trifásica)", "1,2", "Limite usual de projeto"),
        ("Dados de entrada", "Incluir guardas aterrados no gradiente (conservador)", "marcado", "Aumenta ligeiramente o gradiente"),
        ("Resultados e relatório", "Gerar relatório (.docx)", "—", "Contém gradiente, Peek, perdas e curva de perdas × tensão")])
    R.p("Resultado esperado: δ = 0,896; gradiente máximo 13,07 kV/cm; E0 = 20,97 kV/cm (seco) e 16,78 (chuva); Vc = 109,3 kV e 87,4 kV; perda máx. 0,000 kW/km; ATENDE.")
    R.h2("Conferência")
    checklist(R, ["Altitude e temperatura do trecho mais crítico (maior altitude ⇒ menor δ ⇒ menor Vc).",
                  "Condição de chuva sempre avaliada (V/Vc em chuva é o caso crítico).",
                  "Gradiente máximo < ~17 kV/cm; E/E0 < 1.",
                  "Fator m e g0 coerentes com o condutor (encordoado, novo ou usado).",
                  "Perdas estimadas pela fórmula de Peek valem para tempo bom/chuva leve; chuva forte e geada podem exigir estudo específico."])
