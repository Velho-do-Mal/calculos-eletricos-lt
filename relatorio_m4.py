"""
Relatório do Módulo 4 – Faixa de segurança/servidão (ABNT NBR 5422:2024, Seção 17), no padrão BK.
Reaproveita o gerador de layout BK (classe Rel).
"""
import datetime as dt
import math

import matplotlib.pyplot as plt
import numpy as np
from docx.enum.text import WD_ALIGN_PARAGRAPH
from matplotlib.patches import Rectangle

from relatorio_m2 import (AZUL, CINZA, LARANJA, VERDE, VERM, Rel, estilo_ax, f, mi, mu, mfrac, mpar, msqrt, msub, msup)


def fig_faixa(e, r):
    """Seção transversal: fase externa, ângulo de balanço, distância D e limites da faixa."""
    fx = r["faixa"]
    b, d, D = e["b"], fx["d"], r["D"]
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    estilo_ax(ax)
    if fx["simetrica"]:
        x0, x1 = -fx["L_adot"] / 2, fx["L_adot"] / 2
        ax.plot([-b, b], [0, 0], "o", color=AZUL, ms=7, label="Fases externas (fixação)")
    else:
        x0, x1 = -(fx["lado_oposto"]), fx["lado_isol"]
        ax.plot([0, e["b"]], [0, 0], "o", color=AZUL, ms=7, label="Fases (fixação)")
    ax.add_patch(Rectangle((x0, -1.0), x1 - x0, 1.0, color="#D1FAE5", alpha=0.8, label=f"Faixa adotada = {fx['L_adot']:.0f} m"))
    for xx in (b, -b) if fx["simetrica"] else (b,):
        sgn = 1 if xx > 0 else -1
        ax.plot([xx, xx + sgn * d], [0, 0], "-", color=LARANJA, lw=3, label="d = (cadeia+flecha)·sen β" if sgn == 1 else None)
        ax.plot([xx + sgn * d, xx + sgn * (d + D)], [0, 0], "-", color=VERM, lw=3, label="D (distância de segurança)" if sgn == 1 else None)
    ax.axvline(0, color=CINZA, lw=0.8, ls="--")
    ax.set_xlim(x0 - 2, x1 + 2)
    ax.set_ylim(-1.6, 1.2)
    ax.set_yticks([])
    ax.set_xlabel("Distância ao eixo da LT (m)")
    ax.set_title("Faixa de segurança – seção transversal (esquemático)", fontsize=10)
    ax.legend(fontsize=7, loc="upper center", ncol=2)
    return fig


def fig_beta(e, r):
    """β e faixa em função do vento de projeto."""
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    estilo_ax(ax)
    import calc_faixa as cf
    v = np.linspace(8, 45, 60)
    q = [cf.q0_de_vento(x) for x in v]
    b_ = [cf.angulo_balanco(x, qq, e["d_mm"] / 1000, r["p_n"], e["lm"], e["lp"]) for x, qq in zip(v, q)]
    ax.plot(v, [x["beta"] for x in b_], color=AZUL, lw=2, label="β médio")
    ax.plot(v, [x["beta_max"] for x in b_], color=VERM, lw=2, label="β máx = β + 2σ")
    ax.plot(v, [x["beta_min"] for x in b_], color=VERDE, lw=2, label="β mín = β − 2σ")
    ax.axvline(e["vp"], color=CINZA, ls="--")
    ax.plot(e["vp"], r["ang"]["beta"], "ko")
    ax.set_xlabel("Vento de projeto V_P (m/s)")
    ax.set_ylabel("Ângulo de balanço (°)")
    ax.set_title("Ângulo de balanço × vento (NBR 5422:2024, 8.9)", fontsize=10)
    ax.legend(fontsize=8)
    return fig


def gerar(caminho, proj, e, r, d, circ, codigo="BK-LT-MC-FAIXA", rev="R0", pontos=None):
    """e: entrada de calc_faixa; r: resultado de calc_faixa.calcular (sem erros); d: dados da seção '4'; circ: circuito 1."""
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    fx = r["faixa"]
    R = Rel(proj, "Faixa de Segurança / Servidão – NBR 5422:2024", codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS TÉCNICAS ADOTADAS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. DIMENSIONAMENTO E VERIFICAÇÕES", "7. QUANTITATIVOS",
               "8. RESULTADOS OBTIDOS", "9. CONCLUSÕES", "10. REFERÊNCIAS BIBLIOGRÁFICAS"])
    cond = circ.get("cond") or "DADO NÃO INFORMADO"

    R.h1("OBJETIVO")
    R.p("Determinar a largura da faixa de segurança (faixa de passagem/servidão) da linha de transmissão " + (proj.get("nome") or "") +
        " pelo critério de balanço dos condutores sob vento (NBR 5422:2024, 17.2.2.2 a 17.2.2.5), e as distâncias de segurança verticais e "
        "horizontais da Seção 7.")
    R.p("campos elétrico e magnético (10.2, 10.3), rádio interferência e ruído audível (10.6, 10.7), restrições de uso da faixa (Seção 18) "
        "e travessias (Seção 20).", "Escopo excluído:")

    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["Módulo 3", "Estudo dos Ventos (vento 50 anos/30 s)", "—", proj["data_txt"]],
        ["ABNT NBR 5422:2024", "Projeto de linhas aéreas de transmissão de energia elétrica", "2024", "2024"],
        ["Planilha BK", "LINHA DE TRANSMISSÃO 4.xlsm (abas Faixa de Servidão e Distância de Segurança)", "—", "—"]], [3.5, 8.0, 1.5, 3.0])

    R.h1("NORMAS TÉCNICAS ADOTADAS")
    R.tabela("Itens da NBR 5422:2024 aplicados", ["Item", "Assunto", "Aplicação neste estudo"], [
        ["7.2, Tabelas 5 e 6", "Distância vertical de segurança", "D_V = PbV + Ps + Pe"],
        ["7.3, Tabela 7", "Distância horizontal de segurança", "D_H = PbH + Petip,n"],
        ["8.9.1 a 8.9.5, Figura 22", "Ângulo de balanço", "β, σβ, β_máx, β_mín"],
        ["9.4.1", "Distância fase-terra – frente lenta", "Parcela elétrica Pe e distância D da faixa"],
        ["17.1, 17.2.1", "Largura da faixa", "Critério de balanço dos condutores"],
        ["17.2.2.2 a 17.2.2.5", "Cálculo da faixa", "L = 2(b + d + D) ou L = 2(d + D)"]], [4.0, 5.5, 6.5])
    R.p("os itens 10.2, 10.3, 10.6, 10.7 (campos, RI e ruído) são remetidos pela 17.2.3 e 17.2.4 e ficam para os Módulos 8 e 10.",
        "PENDENTE —")

    R.h1("METODOLOGIA DE CÁLCULO")
    R.h2("Ângulo de balanço (8.9)")
    R.p("O ângulo médio de balanço do cabo e da cadeia sob vento 50 anos/30 s é calculado pela 8.9.1; o desvio-padrão e os ângulos "
        "máximo e mínimo, pela 8.9.3 a 8.9.5.")
    R.eq(mi("β") + mu("=") + msup(mu("tg"), mu("−1")) + mpar(mi("K") + mfrac(msub(mi("q"), mu("0")) + mi("d") + msub(mi("L"), mi("m")),
                                                                        msub(mi("p"), mu("cond")) + msub(mi("L"), mi("p")))))
    R.eq(msub(mi("σ"), mi("β")) + mu("=2,25[1−exp(−") + mfrac(msup(msub(mi("V"), mi("p")), mu("2")), mu("230")) + mu(")] ;  ") +
         msub(mi("β"), mu("máx")) + mu("=") + mi("β") + mu("+2") + msub(mi("σ"), mi("β")))
    R.simbolos([("K", "fator de efetividade (1 se V_p < 10 m/s; 0,3 + 3,68·exp(−0,163·V_p) se V_p ≥ 10 m/s)", "—"),
                ("q0", "pressão dinâmica para V_p de 30 s", "Pa"), ("d", "diâmetro do cabo", "m"), ("Lm", "vão médio", "m"),
                ("Lp", "vão gravante", "m"), ("p_cond", "peso linear do cabo", "N/m")])
    R.p("a equação vale para condutores singelos e feixes de subcondutores idênticos (8.9.2).", "Limitações:")
    R.h2("Distância de segurança D")
    R.p("A distância horizontal de segurança D da faixa é calculada pela 9.4.1 com k_g = 1,28 e K_cs = 1,35 (17.2.2.5). "
        "A planilha BK adota 0,5 m (U ≤ 69 kV) ou U·1,05/150 (U > 69 kV); este relatório informa as duas e adota o critério escolhido.")
    R.eq(msub(mi("d"), mu("ft,fl")) + mu("=2,174[exp(") + mfrac(msub(mi("K"), mu("cs")) + mfrac(msqrt(mu("2")), msqrt(mu("3"))) + msub(mi("U"), mi("S")) +
                                                          msub(mi("F"), mu("sfl")), mu("1080·") + msub(mi("k"), mu("afl")) + msub(mi("k"), mu("zfl")) + msub(mi("k"), mi("g")))
         + mu(")−1] ;  ") + msub(mi("k"), mu("zfl")) + mu("=1−1,3·") + msub(mi("z"), mu("fl")))
    R.simbolos([("Kcs", "fator de coordenação estatístico (Tabela 6: 1,35 típica, 1,25 limite)", "—"),
                ("Fsfl", "fator de sobretensão de frente lenta fase-terra (2 %)", "p.u."), ("kafl", "correção atmosférica", "—"),
                ("kg", "fator de espaçamento fase-terra", "—"), ("zfl", "coeficiente de variação (0,06)", "—"),
                ("U_S", "tensão nominal entre fases", "kV")])
    R.h2("Largura da faixa (17.2.2.5)")
    R.eq(mi("L") + mu("=2(") + mi("b") + mu("+") + mi("d") + mu("+") + mi("D") + mu(")   (simétrica) ;  ") + mi("L") + mu("=2(") + mi("d") + mu("+") + mi("D") + mu(")   (um lado)"))
    R.eq(mi("d") + mu("=(") + msub(mi("l"), mu("cad")) + mu("+") + msub(mi("f"), mu("máx")) + mu(")·sen") + mi("β"))
    R.simbolos([("b", "distância do eixo ao ponto de fixação do condutor mais externo", "m"),
                ("d", "soma das projeções horizontais da flecha e da cadeia no ângulo de balanço", "m"),
                ("D", "distância horizontal de segurança", "m"), ("l_cad", "comprimento da cadeia (0 em ancoragem e line-post)", "m"),
                ("f_máx", "flecha à temperatura máxima do ar (PLS-CADD)", "m")])
    R.p("a largura adotada é arredondada para cima ao metro inteiro (planilha BK); no caso unilateral, o lado oposto é a faixa adotada menos "
        "a distância do eixo ao lado dos isoladores.", "Critério:")
    R.h2("Distâncias verticais e horizontais (Seção 7)")
    R.eq(msub(mi("D"), mu("Vlim,n")) + mu("=") + msub(mi("P"), mu("bV")) + mu("+") + msub(mi("P"), mu("slim")) + mu("+") + msub(mi("P"), mu("elim")) + mu(" ;  ") +
         msub(mi("D"), mu("Vtip,n")) + mu("=máx(") + msub(mi("P"), mu("bV")) + mu("+") + msub(mi("P"), mu("stip")) + mu("+") + msub(mi("P"), mu("etip,n")) +
         mu(" ; ") + msub(mi("D"), mu("Vlim,n")) + mu("+0,90)"))
    R.p("P_stip = 0,90 m e P_slim = 0,60 m (7.2.1.2). Pe = d_ft,fl (7.2.5.1) com k_g da Tabela 5 e K_cs da Tabela 6. As distâncias verticais devem "
        "ser verificadas até β_máx (7.2.1.3). A distância horizontal é D_H = P_bH + P_etip,n (7.3.2).")

    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    R.tabela("Dados de entrada", ["Parâmetro", "Valor", "Unidade", "Origem"], [
        ["Condutor", cond, "—", "Catálogo (Módulo 1)"],
        ["Diâmetro d", f(e["d_mm"], 2), "mm", "Catálogo"],
        ["Massa linear / peso p_cond", f"{f(e['massa_kg_m'], 4)} / {f(r['p_n'], 3)}", "kg/m · N/m", "Catálogo (×9,80665)"],
        ["Tensão nominal U_S", f(e["un_kv"], 1), "kV", "Módulo 1"],
        ["Vento V_P (50 anos, 30 s)", f(e["vp"], 2), "m/s", "Módulo 3" if d.get("vento_modo", "Módulo 3") == "Módulo 3" else "Informado"],
        ["Pressão dinâmica q0", f(r["q0"], 1), "Pa", "Módulo 3 (½·μ·V²)" if d.get("vento_modo", "Módulo 3") == "Módulo 3" else "½·1,225·V² (PREMISSA)"],
        ["Vão médio Lm / vão gravante Lp", f"{f(e['lm'], 0)} / {f(e['lp'], 0)}", "m", "PLS-CADD (informado)"],
        ["Flecha à temperatura máxima", f(e["flecha"], 2), "m", "PLS-CADD (informado)"],
        ["Cadeia", f"{d.get('tipo_cadeia', 'Suspensão')} – {f(e['comp_cadeia'], 2)} m", "—", "Informado"],
        ["b (eixo → fase externa)", f(e["b"], 2), "m", "Geometria (Módulo 2)" if not d.get("b_man") else "Informado"],
        ["Disposição", "Simétrica" if fx["simetrica"] else "Isoladores de um lado", "—", "Informado"],
        ["F_sfl / k_afl", f"{f(e['fsfl'], 2)} / {f(e['kafl'], 2)}", "p.u. / —", "PREMISSA"]], [5.0, 4.5, 2.0, 4.5])
    R.h2("Pontos de estudo e vizinhas considerados")
    if pontos:
        R.tabela("Pontos de estudo (travessias, paralelismos e demais interferências)", ["Ponto", "Descrição"], [[a, b] for a, b in pontos], [4.0, 11.5])
        R.p("os pontos acima ficam registrados com tensão e corrente das linhas envolvidas; a largura da faixa em corredor de linhas paralelas "
            "(17.2.2.6) e as distâncias entre condutores de linhas diferentes (7.4) dependem de d e D de cada vizinha e não foram calculadas.",
            "PENDENTE —")
    else:
        R.p("nenhum ponto de estudo selecionado; o cálculo acima considera apenas a própria linha.", "Observação:")
    R.h2("Dados não informados e premissas")
    R.p("F_sfl = " + f(e["fsfl"], 2) + " p.u. e k_afl = " + f(e["kafl"], 2) + " foram adotados como ponto de partida; devem vir do estudo de "
        "sobretensões de manobra e da correção atmosférica (Seção 4).", "PREMISSA —")
    R.p("o vão médio, o vão gravante e a flecha máxima dependem do projeto mecânico (PLS-CADD) e foram informados pelo usuário.", "PREMISSA —")
    R.p("critério de ângulo de balanço adotado: " + ("médio (8.9.1)" if e["criterio_beta"] == "medio" else "máximo (8.9.4)") +
        "; a 17.2.2.3 remete à 8.9 sem especificar médio ou máximo.", "NECESSITA VALIDAÇÃO TÉCNICA —")
    R.p("o arquivo-modelo DOCUMENTO_PADRAO_BK.docx não foi fornecido; capa, cabeçalho e rodapé seguem a especificação textual.",
        "NECESSITA VALIDAÇÃO TÉCNICA —")
    for m in r["avisos"]:
        R.p(m, "NECESSITA VALIDAÇÃO TÉCNICA —")

    R.h1("DIMENSIONAMENTO E VERIFICAÇÕES")
    R.h2("Memória de cálculo – ângulo de balanço")
    a = r["ang"]
    R.p("Calcular o ângulo de balanço do condutor sob vento 50/30.", "Objetivo:")
    R.p(f"K = 0,3 + 3,68·exp(−0,163·{f(e['vp'], 2)}) = {f(a['K'], 4)}.", "Substituição (Figura 22):")
    R.p(f"β = tg⁻¹[{f(a['K'], 4)}·{f(r['q0'], 1)}·{f(e['d_mm'] / 1000, 5)}·{f(e['lm'], 0)}/({f(r['p_n'], 3)}·{f(e['lp'], 0)})] = {f(a['beta'], 2)}°.",
        "Substituição (8.9.1):")
    R.p(f"σβ = 2,25·[1 − exp(−{f(e['vp'], 2)}²/230)] = {f(a['sigma'], 3)}°; β_máx = {f(a['beta'], 2)} + 2·{f(a['sigma'], 3)} = {f(a['beta_max'], 2)}°; "
        f"β_mín = {f(a['beta_min'], 2)}°.", "Substituição (8.9.3 a 8.9.5):")
    R.p("tg β = K·q0·d·Lm/(p·Lp) reproduzida por recálculo independente: " +
        f"tg({f(a['beta'], 2)}°) = {f(math.tan(math.radians(a['beta'])), 4)}; K·q0·d·Lm/(p·Lp) = {f(a['K'] * r['q0'] * e['d_mm'] / 1000 * e['lm'] / (r['p_n'] * e['lp']), 4)}.",
        "Verificação independente:")
    R.figura(fig_beta(e, r), "Ângulo de balanço em função do vento de projeto",
             "A Figura 1 mostra a redução do fator K com a velocidade: o ângulo médio cresce menos que proporcionalmente ao quadrado do vento.")
    R.h2("Memória de cálculo – distância D e faixa")
    R.p(f"D(NBR 9.4.1) = 2,174·[exp(1,35·(√2/√3)·{f(e['un_kv'], 1)}·{f(e['fsfl'], 2)}/(1080·{f(e['kafl'], 2)}·0,922·1,28)) − 1] = {f(r['D_norma'], 3)} m; "
        f"D(planilha BK) = {f(r['D_planilha'], 3)} m; D adotada = {f(r['D'], 3)} m.", "Substituição:")
    R.p(f"d = ({f(e['comp_cadeia'], 2)} + {f(e['flecha'], 2)})·sen({f(r['beta_usado'], 2)}°) = {f(fx['d'], 3)} m.", "Substituição:")
    if fx["simetrica"]:
        R.p(f"L = 2·({f(e['b'], 2)} + {f(fx['d'], 3)} + {f(r['D'], 3)}) = {f(fx['L'], 2)} m → adotada {f(fx['L_adot'], 0)} m.", "Substituição (17.2.2.5.1):")
    else:
        R.p(f"L = 2·({f(fx['d'], 3)} + {f(r['D'], 3)}) = {f(fx['L'], 2)} m → adotada {f(fx['L_adot'], 0)} m; "
            f"lado dos isoladores {f(fx['lado_isol'], 2)} m; lado oposto {f(fx['lado_oposto'], 2)} m.", "Substituição (17.2.2.5.2):")
    R.figura(fig_faixa(e, r), "Faixa de segurança – seção transversal", "A Figura 2 mostra a composição da faixa: b + d + D de cada lado.")
    R.tabela("Faixa para β médio e β máximo", ["Ângulo usado", "β (°)", "L calculada (m)", "L adotada (m)"],
             [["β médio", f(a["beta"], 2), f(r["faixa_medio"]["L"], 2), f(r["faixa_medio"]["L_adot"], 0)],
              ["β máximo", f(a["beta_max"], 2), f(r["faixa_max"]["L"], 2), f(r["faixa_max"]["L_adot"], 0)]], [4.5, 3.0, 4.0, 4.0])
    R.h2("Distâncias de segurança")
    R.tabela("Distâncias verticais – 7.2 (regime de corrente nominal)", ["Obstáculo", "kg", "PbV (m)", "Pe típ. (m)", "D_V lim,n (m)", "D_V típ,n (m)"],
             [[k, f(v["kg"], 2), f(v["PbV"], 2), f(v["Pe_tip"], 2), f(v["D_lim_n"], 2), f(v["D_tip_n"], 2)] for k, v in r["verticais"].items()],
             [6.0, 1.2, 1.9, 2.1, 2.4, 2.4], fonte="NBR 5422:2024, Tabelas 5 e 6; cálculo próprio")
    R.tabela("Distâncias horizontais – 7.3", ["Obstáculo", "kg", "PbH (m)", "Pe típ. (m)", "D_H (m)"],
             [[k, f(v["kg"], 2), f(v["PbH"], 2), f(v["Pe_tip"], 2), f(v["D_H"], 2)] for k, v in r["horizontais"].items()],
             [6.5, 1.5, 2.5, 2.5, 2.5], fonte="NBR 5422:2024, Tabela 7; cálculo próprio")
    R.tabela("Comparação – tabela da planilha BK", ["Obstáculo", "Distância (m)"],
             [[k, f(v, 2)] for k, v in r["verticais_planilha"].items()], [9.0, 4.0],
             fonte="Planilha BK, aba Distância de Segurança (lógica da edição anterior da norma)")
    R.p("a planilha e a NBR 5422:2024 diferem; confirmar com a transmissora qual valor vale para o projeto.", "NECESSITA VALIDAÇÃO TÉCNICA —")

    R.h1("QUANTITATIVOS")
    R.p("Não aplicável a este documento.")

    R.h1("RESULTADOS OBTIDOS")
    R.tabela("Resumo", ["Grandeza", "Valor", "Unidade", "Base"], [
        ["β médio", f(a["beta"], 2), "°", "8.9.1"], ["β máximo", f(a["beta_max"], 2), "°", "8.9.4"],
        ["Distância D adotada", f(r["D"], 2), "m", "9.4.1 / planilha BK"],
        ["d (projeção horizontal)", f(fx["d"], 2), "m", "17.2.2.5"],
        ["Faixa calculada", f(fx["L"], 2), "m", "17.2.2.5.1" if fx["simetrica"] else "17.2.2.5.2"],
        ["Faixa adotada", f(fx["L_adot"], 0), "m", "Arredondamento ao metro"]], [5.0, 3.0, 2.0, 5.0])
    R.p("a largura calculada atende ao critério de balanço; a faixa definitiva deve ser a maior entre este critério e os de campo, RI e ruído "
        "(17.2.1), ainda não avaliados.", "RESULTADO:")
    R.tabela("Resumo das verificações", ["Verificação", "Norma/critério", "Valor", "Limite", "Status"], [
        ["Vento de projeto 50 anos/30 s", "17.2.2.2c", f"{f(e['vp'], 2)} m/s", "TR ≥ 50 anos (Módulo 3)", "ATENDE" if d.get("vento_modo", "Módulo 3") == "Módulo 3" else "PENDENTE"],
        ["Faixa por balanço", "17.2.2.5", f"{f(fx['L_adot'], 0)} m", "L ≥ critério de balanço", "ATENDE"],
        ["Campo elétrico/magnético na borda", "17.2.3 / 10.2, 10.3", "não calculado", "limites da Seção 10", "PENDENTE"],
        ["RI e ruído audível na borda", "17.2.4 / 10.6, 10.7", "não calculado", "limites da Seção 10", "PENDENTE"]], [4.4, 3.2, 3.0, 3.6, 1.9])

    R.h1("CONCLUSÕES")
    R.lista([f"Ângulo de balanço médio {f(a['beta'], 2)}° e máximo {f(a['beta_max'], 2)}° (vento {f(e['vp'], 2)} m/s).",
             f"Faixa de segurança por balanço: {f(fx['L'], 2)} m, adotada {f(fx['L_adot'], 0)} m.",
             f"Distância D adotada: {f(r['D'], 2)} m."])
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Confirmar Lm, Lp e flecha máxima com o modelo do PLS-CADD para o vão crítico (17.2.2.9).",
             "Confirmar F_sfl e k_afl no estudo de sobretensões; confirmar médio × máximo na 17.2.2.3.",
             "Verificar campos, RI e ruído (Módulos 8 e 10) e adotar a maior faixa."])
    R.p("Grau de confiança: médio-alto para a faixa por balanço (equações da norma reproduzidas e conferidas contra a planilha BK); "
        "baixo para a faixa final, pois faltam os critérios de campo, RI e ruído.", "O que falta para eu informar com certeza:")

    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["ABNT NBR 5422:2024 – Projeto de linhas aéreas de transmissão de energia elétrica.",
             "Planilha BK – LINHA DE TRANSMISSÃO 4.xlsm."])
    R.salvar(caminho)
    return caminho
