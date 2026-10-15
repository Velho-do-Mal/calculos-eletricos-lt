"""
Relatório do Módulo 6 – Aterramento de estruturas (contrapeso radial), no padrão BK.
"""
import datetime as dt
import math

import matplotlib.pyplot as plt
import numpy as np
from docx.enum.text import WD_ALIGN_PARAGRAPH

import calc_aterramento as ca
from relatorio_m2 import (AZUL, CINZA, LARANJA, VERDE, VERM, Rel, estilo_ax, f, mi, mu, mfrac, mpar, msqrt, msub, msup)


def _args(e):
    if e["modo_solo"] == "Uniforme":
        return e["rho"], None, None
    return e["rho1"], e["rho2"], e["h1"]


def fig_curvas(e):
    rho, r2, h1 = _args(e)
    a = e["d_cabo_mm"] / 2000.0
    fig, ax = plt.subplots(figsize=(6.2, 3.7))
    estilo_ax(ax)
    Ls = [5, 10, 15, 20, 30, 40, 50, 60, 80, 100]
    for n, cor in ((2, AZUL), (4, LARANJA), (6, VERDE)):
        ax.plot(Ls, [ca.resistencia_radial(rho, n, l, e["h"], a, r2, h1, seg_por_perna=max(10, int(l / 2))) for l in Ls], color=cor, lw=2, label=f"{n} pernas")
    ax.axhline(e["r_meta"], color=VERM, ls="--", label=f"Meta {e['r_meta']:g} Ω")
    ax.axvline(ca.comprimento_efetivo(rho), color=CINZA, ls=":", label="Comprimento efetivo (impulso)")
    ax.set_yscale("log")
    ax.set_xlabel("Comprimento de cada perna (m)")
    ax.set_ylabel("Resistência de pé de torre (Ω)")
    ax.set_title("Resistência × comprimento do contrapeso", fontsize=10)
    ax.legend(fontsize=8)
    return fig


def fig_planta(e):
    fig, ax = plt.subplots(figsize=(4.4, 4.4))
    estilo_ax(ax)
    n, L = e["n_pernas"], e["L"]
    for p in range(n):
        ang = math.radians(360.0 * p / n)
        ax.plot([0, L * math.cos(ang)], [0, L * math.sin(ang)], color=LARANJA, lw=2.5)
    ax.plot(0, 0, "s", color=AZUL, ms=9, label="Estrutura")
    ax.set_aspect("equal")
    ax.set_xlabel("m")
    ax.set_title(f"Contrapeso radial – {n} pernas de {L:g} m (planta)", fontsize=10)
    ax.legend(fontsize=8)
    return fig


def fig_wenner(e):
    pts = e["_pts"]
    a = np.array([p["a"] for p in pts])
    rw = np.array(e["_rho_w"])
    fig, ax = plt.subplots(figsize=(6.0, 3.5))
    estilo_ax(ax)
    ax.semilogx(a, rw, "o", color=AZUL, label="ρ aparente medido (2π·a·R)")
    if e.get("_fit"):
        ft = e["_fit"]
        aa = np.geomspace(a.min(), a.max(), 60)
        ax.semilogx(aa, ca.wenner_2camadas(aa, ft["rho1"], ft["rho2"], ft["h1"]), color=LARANJA, lw=2, label="Modelo de 2 camadas")
    ax.set_xlabel("Espaçamento a (m)")
    ax.set_ylabel("ρ aparente (Ω·m)")
    ax.set_title("Medições de Wenner e estratificação", fontsize=10)
    ax.legend(fontsize=8)
    return fig


def gerar(caminho, proj, e, r, d, codigo="BK-LT-MC-ATERRAMENTO", rev="R0"):
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    rho, r2, h1 = _args(e)
    a = e["d_cabo_mm"] / 2000.0
    cab, mat = e["_cabo"], e["material"]
    camadas = e["modo_solo"] != "Uniforme"
    R = Rel(proj, "Aterramento de Estruturas – Contrapeso Radial", codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS TÉCNICAS ADOTADAS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. DIMENSIONAMENTO E VERIFICAÇÕES", "7. QUANTITATIVOS",
               "8. RESULTADOS OBTIDOS", "9. CONCLUSÕES", "10. REFERÊNCIAS BIBLIOGRÁFICAS"])

    R.h1("OBJETIVO")
    R.p("Dimensionar o aterramento das estruturas da linha de transmissão " + (proj.get("nome") or "") +
        ": resistência de pé de torre com contrapeso radial, comportamento sob impulso, seção mínima do condutor pela corrente de falta e "
        "elevação de potencial (GPR).")
    R.p("desempenho da linha a descargas atmosféricas (taxa de desligamentos), distribuição de corrente de curto entre cabo guarda e torres, "
        "tensões de passo e toque no terreno e transferência de potencial a terceiros.", "Escopo excluído:")

    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["IEEE Std 80-2013", "Guide for Safety in AC Substation Grounding", "2013", "2013"],
        ["Diretrizes de projeto básico", "Diretrizes para a elaboração de projetos básicos de empreendimentos de transmissão (item 6.14)", "—", "—"],
        ["Planilha BK", "LINHA DE TRANSMISSÃO 4.xlsm (abas Aterramento e DB Aterramento)", "—", "—"]], [3.5, 8.0, 1.5, 3.0])
    R.p("medições de resistividade do solo em campo e valores de referência da transmissora não foram fornecidos.", "DADO NÃO INFORMADO —")

    R.h1("NORMAS TÉCNICAS ADOTADAS")
    R.lista(["IEEE Std 80-2013 – seção mínima do condutor (eq. 37) e limites de tensão de passo e toque (eq. 29 a 32).",
             "Dwight (1936) e Sunde – resistência de eletrodo horizontal enterrado.",
             "CIGRE / IEEE – comportamento impulsivo de eletrodos (comprimento efetivo e ionização do solo).",
             "Diretrizes para projetos básicos de transmissão, item 6.14 – aterramento em 4 ou 6 pernas e valor médio de referência em geral ≤ 20 Ω.",
             "ABNT NBR 15749 e NBR 7117 (medição de resistividade) – não consultadas neste estudo."])
    R.p("conferir as normas ABNT de aterramento e a prática da transmissora antes da emissão final.", "PENDENTE —")

    R.h1("METODOLOGIA DE CÁLCULO")
    R.h2("Resistividade do solo")
    R.p("A resistividade aparente de cada medição de Wenner é ρ = 2π·a·R. Para solo de duas camadas, ajusta-se (ρ1, ρ2, h1) "
        "às medições pelo modelo de imagens.")
    R.eq(mi("ρ") + mu("=2π·") + mi("a") + mu("·") + mi("R") + mu(" ;  ") + msub(mi("ρ"), mi("a")) + mu("=") + msub(mi("ρ"), mu("1")) + mpar(mu("1+4") +
         mu("Σ") + msup(mi("k"), mi("n")) + mpar(mfrac(mu("1"), msqrt(mu("1+(2n·") + msub(mi("h"), mu("1")) + mu("/a)²"))) + mu("−") +
                                               mfrac(mu("1"), msqrt(mu("4+(2n·") + msub(mi("h"), mu("1")) + mu("/a)²"))))))
    R.simbolos([("a", "espaçamento entre eletrodos", "m"), ("R", "resistência medida", "Ω"), ("k", "(ρ2 − ρ1)/(ρ2 + ρ1)", "—"),
                ("h1", "espessura da camada superior", "m")])
    R.h2("Resistência do contrapeso radial")
    R.p("A resistência de n pernas radiais é obtida pelo método de ponto-colocação: cada perna é dividida em segmentos de corrente uniforme, "
        "impõe-se o mesmo potencial em todos e a resistência é R = 1/ΣI para potencial unitário. O núcleo inclui a imagem do ar e, em solo de duas camadas, "
        "as imagens da interface. Para uma perna isolada, o resultado é conferido pela fórmula de Dwight.")
    R.eq(mi("R") + mu("=") + mfrac(mi("ρ"), mu("2π") + mi("L")) + mu("[ln") + mfrac(mu("2") + mi("L"), mi("a")) + mu("+ln") + mfrac(mi("L"), mi("h")) +
         mu("−2+") + mfrac(mu("2") + mi("h"), mi("L")) + mu("−") + msup(mpar(mfrac(mi("h"), mi("L"))), mu("2")) + mu("]"))
    R.simbolos([("L", "comprimento da perna", "m"), ("h", "profundidade", "m"), ("a", "raio do cabo", "m"), ("ρ", "resistividade", "Ω·m")])
    R.p("válido para cabos na camada superior (h < h1), pernas retilíneas e horizontais; não considera a resistência de fundação da torre.", "Limitações:")
    R.h2("Comportamento sob impulso")
    R.eq(msub(mi("L"), mi("e")) + mu("=1,4") + msqrt(mi("ρ")) + mu(" ;  ") + msub(mi("R"), mi("i")) + mu("=") +
         mfrac(msub(mi("R"), mu("0")), msqrt(mu("1+") + mfrac(mi("I"), msub(mi("I"), mi("g"))))) + mu(" ;  ") + msub(mi("I"), mi("g")) + mu("=") +
         mfrac(mi("ρ") + msub(mi("E"), mu("0")), mu("2π") + msup(msub(mi("R"), mu("0")), mu("2"))))
    R.simbolos([("Le", "comprimento efetivo", "m"), ("E0", "gradiente de ionização (300 kV/m)", "kV/m"), ("I", "corrente de descarga", "kA")])
    R.h2("Seção mínima do condutor e tensões")
    R.eq(mi("A") + mu("=") + mi("I") + msqrt(mfrac(mi("t") + msub(mi("α"), mi("r")) + msub(mi("ρ"), mi("r")) + msup(mu("10"), mu("4")),
                                                    mu("TCAP·ln") + mfrac(msub(mi("K"), mu("0")) + mu("+") + msub(mi("T"), mi("m")), msub(mi("K"), mu("0")) + mu("+") + msub(mi("T"), mi("a"))))))
    R.p("GPR = If·R. Limites (IEEE 80): E_toque = (1000 + 1,5·Cs·ρs)·k/√t e E_passo = (1000 + 6·Cs·ρs)·k/√t, com k = 0,157 (70 kg) ou 0,116 (50 kg).")

    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    linhas = [["Modelo do solo", e["modo_solo"], "—", "Informado"]]
    if camadas:
        linhas += [["ρ1 / ρ2 / h1", f"{f(rho, 0)} / {f(r2, 0)} / {f(h1, 2)}", "Ω·m · Ω·m · m", "Ajuste Wenner / informado"]]
    else:
        linhas += [["Resistividade ρ", f(rho, 0), "Ω·m", "Informado"]]
    linhas += [["Fator sazonal", f(d.get("fator_sazonal", 1.0), 2), "—", "PREMISSA"],
               ["Pernas × comprimento", f"{e['n_pernas']} × {f(e['L'], 0)}", "× m", "Informado"],
               ["Profundidade", f(e["h"], 2), "m", "Informado"],
               ["Cabo contrapeso", cab["nome"], "—", "DB Aterramento (planilha BK)"],
               ["Diâmetro externo / seção efetiva", f"{f(cab['d_ext'], 2)} / {f(cab['s_ef'], 1)}", "mm · mm²", "Planilha BK"],
               ["Resistência de referência", f(e["r_meta"], 1), "Ω", "Diretrizes (≤ 20 Ω em geral)"],
               ["Corrente de descarga", f(e["i_desc_ka"], 1), "kA", "PREMISSA"],
               ["Material / conexão (Tm)", f"{mat['nome']} / {f(e['tm'], 0)} °C", "—", "Planilha BK"],
               ["Corrente de falta If / duração", f"{f(e['i_falta_ka'], 3)} / {f(e['t_falta'], 2)}", "kA · s", "Estudo de curto-circuito"],
               ["Temperatura ambiente", f(e["ta"], 0), "°C", "Planilha BK"]]
    R.tabela("Dados de entrada", ["Parâmetro", "Valor", "Unidade", "Origem"], linhas, [5.0, 5.0, 2.5, 3.5])
    R.h2("Dados não informados e premissas")
    R.p("a resistividade usada deve vir de medições de campo (Wenner) no trecho; sem elas, o valor informado é apenas um ponto de partida.",
        "PREMISSA —")
    R.p("corrente de descarga de " + f(e["i_desc_ka"], 1) + " kA e corrente de falta de " + f(e["i_falta_ka"], 3) + " kA, a confirmar com o estudo de descargas e de curto-circuito.",
        "PREMISSA —")
    R.p("o arquivo-modelo DOCUMENTO_PADRAO_BK.docx não foi fornecido; capa, cabeçalho e rodapé seguem a especificação textual.", "NECESSITA VALIDAÇÃO TÉCNICA —")
    for m in r["avisos"]:
        R.p(m, "NECESSITA VALIDAÇÃO TÉCNICA —")

    R.h1("DIMENSIONAMENTO E VERIFICAÇÕES")
    if e["_pts"] and e.get("_rho_w"):
        R.h2("Resistividade do solo")
        R.tabela("Medições de Wenner", ["a (m)", "R (Ω)", "ρ = 2π·a·R (Ω·m)"],
                 [[f(p["a"], 1), f(p["R"], 3), f(x, 1)] for p, x in zip(e["_pts"], e["_rho_w"])], [4.0, 4.0, 5.0])
        if e.get("_fit"):
            ft = e["_fit"]
            R.p(f"ρ1 = {f(ft['rho1'], 0)} Ω·m; ρ2 = {f(ft['rho2'], 0)} Ω·m; h1 = {f(ft['h1'], 2)} m; erro RMS = {f(ft['erro_rms_pct'], 1)} %.", "Resultado:")
        R.figura(fig_wenner(e), "Medições de Wenner e modelo de duas camadas", "A Figura 1 compara as medições com o modelo ajustado.")
    R.h2("Memória de cálculo – resistência de pé de torre")
    R.p("Calcular a resistência do contrapeso radial.", "Objetivo:")
    R.p(f"n = {e['n_pernas']} pernas; L = {f(e['L'], 0)} m; h = {f(e['h'], 2)} m; a = {f(a * 1000, 3)} mm; ρ = {f(rho, 0)} Ω·m"
        + (f" (camada superior; ρ2 = {f(r2, 0)} Ω·m, h1 = {f(h1, 2)} m)" if camadas else "") + ".", "Substituição:")
    R.p(f"R = {f(r['R'], 2)} Ω (método de ponto-colocação).", "Resultado:")
    if "R_dwight_1" in r:
        dif = 100 * (r["R_1perna"] / r["R_dwight_1"] - 1)
        R.p(f"para 1 perna, Dwight: R = {f(r['R_dwight_1'], 2)} Ω; método numérico: R = {f(r['R_1perna'], 2)} Ω; diferença {f(dif, 2)} %.",
            "Verificação independente:")
    R.figura(fig_planta(e), "Contrapeso radial em planta", "A Figura " + str(R.fig_n + 1) + " mostra a disposição das pernas ao redor da estrutura.", larg_cm=8.0)
    R.figura(fig_curvas(e), "Resistência × comprimento da perna",
             "A curva mostra o ganho decrescente com o comprimento: acima do comprimento efetivo, o acréscimo reduz pouco a impedância de surto.")
    R.tabela("Resistência × comprimento (n = " + str(e["n_pernas"]) + ")", ["L (m)", "R (Ω)"], [[f(a_, 0), f(b_, 2)] for a_, b_ in r["curva"]], [4.0, 4.0])
    R.tabela("Menor perna que atende à meta por faixa de resistividade", ["ρ (Ω·m)", "L mínimo (m)", "R obtida (Ω)"],
             [[f(a_, 0), f(b_, 0) if b_ else "> 80", f(c_, 2)] for a_, b_, c_ in r["tabela_rho"]], [4.0, 4.0, 4.0],
             fonte="Cálculo próprio; mesmas pernas e profundidade; solo uniforme")
    R.h2("Comportamento sob impulso")
    i_ = r["imp"]
    R.p(f"Le = 1,4·√{f(rho, 0)} = {f(i_['Le'], 1)} m; Ig = {f(i_['Ig'], 1)} kA; Ri = {f(r['R'], 2)}/√(1 + {f(e['i_desc_ka'], 1)}/{f(i_['Ig'], 1)}) = {f(i_['Ri'], 2)} Ω.",
        "Substituição:")
    R.h2("Seção mínima do condutor")
    kk = e.get("fator_corrente", 1.0)
    R.p(f"A = {f(e['i_falta_ka'] * kk, 3)}·√[{f(e['t_falta'], 2)}·{f(mat['ar'], 5)}·{f(mat['rho'], 3)}·10⁴/({f(mat['tcap'], 3)}·ln((1/{f(mat['a0'], 5)} + {f(e['tm'], 0)})/"
        f"(1/{f(mat['a0'], 5)} + {f(e['ta'], 0)})))] = {f(r['secao_min'], 2)} mm².", "Substituição:")
    ok = r["secao_min"] <= cab["s_ef"]
    R.tabela("Verificação da seção do cabo", ["Verificação", "Valor", "Limite", "Status"],
             [["Seção efetiva do cabo", f"{f(cab['s_ef'], 1)} mm²", f"≥ {f(r['secao_min'], 2)} mm²", "ATENDE" if ok else "NÃO ATENDE"]], [4.5, 3.5, 4.0, 3.0])
    R.h2("Elevação de potencial e limites de tensão")
    R.p(f"GPR = {f(e['i_falta_ka'] * 1000 * e.get('fracao_terra', 1.0), 0)}·{f(r['R'], 2)} = {f(r['gpr'] / 1000, 2)} kV; "
        f"E_toque adm. = {f(r['lim']['toque'], 0)} V; E_passo adm. = {f(r['lim']['passo'], 0)} V (Cs = {f(r['lim']['Cs'], 2)}).", "Substituição:")
    R.p("o perfil de potencial no terreno não foi calculado; a comparação com os limites de passo e toque exige esse perfil.", "PENDENTE —")

    R.h1("QUANTITATIVOS")
    R.tabela("Quantitativo por estrutura", ["Item", "Quantidade", "Unidade"],
             [["Cabo contrapeso " + cab["nome"], f(e["n_pernas"] * e["L"], 0), "m"],
              ["Massa estimada", f(e["n_pernas"] * e["L"] * cab["peso"] / 1000.0, 1), "kg"]], [8.0, 3.0, 3.0],
             fonte="Peso líquido nominal do cabo (planilha BK); sem perdas e conexões")

    R.h1("RESULTADOS OBTIDOS")
    R.tabela("Resumo", ["Grandeza", "Valor", "Unidade", "Base"], [
        ["Resistência de pé de torre", f(r["R"], 2), "Ω", "Ponto-colocação"],
        ["Resistência impulsiva", f(i_["Ri"], 2), "Ω", "CIGRE/IEEE"],
        ["Comprimento efetivo", f(i_["Le"], 1), "m", "1,4·√ρ"],
        ["Seção mínima", f(r["secao_min"], 2), "mm²", "IEEE 80, eq. 37"],
        ["GPR", f(r["gpr"] / 1000, 2), "kV", "If·R"]], [5.5, 2.5, 2.0, 5.0])
    R.tabela("Resumo das verificações", ["Verificação", "Critério", "Valor", "Limite", "Status"], [
        ["Resistência de pé de torre", "Diretrizes 6.14", f"{f(r['R'], 2)} Ω", f"≤ {f(e['r_meta'], 1)} Ω", "ATENDE" if r["atende"] else "NÃO ATENDE"],
        ["Seção do condutor", "IEEE 80, eq. 37", f"{f(cab['s_ef'], 1)} mm²", f"≥ {f(r['secao_min'], 2)} mm²", "ATENDE" if ok else "NÃO ATENDE"],
        ["Passo e toque", "IEEE 80", "não calculado", "perfil de potencial", "PENDENTE"]], [4.0, 3.0, 3.0, 3.2, 2.3])
    R.p("os resultados valem para as premissas indicadas; a resistência efetiva deve ser confirmada por medição após a instalação.", "RESULTADO:")

    R.h1("CONCLUSÕES")
    R.lista([f"Resistência de pé de torre: {f(r['R'], 2)} Ω ({'atende' if r['atende'] else 'não atende'} à meta de {f(e['r_meta'], 1)} Ω).",
             f"Seção mínima do condutor: {f(r['secao_min'], 2)} mm² ({'atendida' if ok else 'não atendida'} pelo cabo {cab['nome']}).",
             f"Resistência impulsiva: {f(i_['Ri'], 2)} Ω para {f(e['i_desc_ka'], 1)} kA."])
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Medir a resistividade (Wenner) ao longo do traçado e definir as fases de aterramento por faixa de resistividade.",
             "Confirmar a corrente de falta e a parcela que escoa pela torre no estudo de curto-circuito.",
             "Verificar o desempenho a descargas e as tensões de passo/toque em estruturas próximas a áreas habitadas."])
    R.p("Grau de confiança: médio. Resistência conferida contra a fórmula de Dwight (diferença < 1 %) e seção mínima conferida contra a planilha BK; "
        "resistividade, corrente de descarga e corrente de falta são premissas, e passo/toque não foram calculados.", "O que falta para eu informar com certeza:")

    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["IEEE Std 80-2013 – IEEE Guide for Safety in AC Substation Grounding.",
             "DWIGHT, H. B. Calculation of resistances to ground. Electrical Engineering, 1936.",
             "Diretrizes para a elaboração de projetos básicos para empreendimentos de transmissão, item 6.14.",
             "Projeto Elétrico de Linhas de Transmissão – capítulo Aterramento (acervo do projeto).",
             "Planilha BK – LINHA DE TRANSMISSÃO 4.xlsm."])
    R.salvar(caminho)
    return caminho
