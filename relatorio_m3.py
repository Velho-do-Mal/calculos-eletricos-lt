"""
Relatório do Módulo 3 – Estudo dos Ventos e Temperaturas (ABNT NBR 5422:2024), no padrão BK.
Destinado à aprovação da transmissora: traz o quadro de dados (vento máx., 50/30, rajada, frequência industrial,
manobra, EDS, T máx, T mín), a origem INMET, o mapa do Brasil com o local do projeto e a tabela de casos do PLS-CADD.
Reaproveita o gerador de layout BK (classe Rel) do relatório do Módulo 2.
"""
import datetime as dt
import json
import math
import os

import matplotlib.pyplot as plt
import numpy as np
from docx.enum.text import WD_ALIGN_PARAGRAPH
from matplotlib.patches import Polygon

import calc_ventos as cv
from relatorio_m2 import (AZUL, CINZA, LARANJA, VERM, Rel, estilo_ax, f, mi, mu, mfrac, mpar, msqrt, msub, msup)

AQUI = os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------------------- mapa
def fig_mapa(lat, lon, rotulo):
    with open(os.path.join(AQUI, "dados", "brasil_estados.json"), encoding="utf-8") as fh:
        estados = json.load(fh)
    fig, ax = plt.subplots(figsize=(5.6, 5.8))
    ax.set_facecolor("white")
    for e in estados:
        for poly in e["poly"]:
            ax.add_patch(Polygon(poly[0], closed=True, facecolor="#E5E7EB", edgecolor="#6B7280", lw=0.5))
    ax.set_xlim(-74.5, -33.5)
    ax.set_ylim(-34.5, 5.8)
    ax.set_aspect(1 / math.cos(math.radians(15)))
    if lat is not None and lon is not None:
        ax.plot(lon, lat, marker="*", color=VERM, ms=17, mec="black", mew=0.8, zorder=5)
        ax.annotate(rotulo, (lon, lat), textcoords="offset points", xytext=(12, 10), fontsize=8, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#374151", lw=0.6))
    ax.set_xlabel("Longitude (°)", fontsize=8)
    ax.set_ylabel("Latitude (°)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.grid(True, color="#E5E7EB", lw=0.5)
    for s in ax.spines.values():
        s.set_color("#9CA3AF")
    ax.set_title("Localização do projeto", fontsize=10)
    return fig


def fig_vxtr(est):
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    estilo_ax(ax)
    Ts = np.array([2, 3, 5, 10, 20, 30, 50, 100, 150, 250])
    for integ, cor, nome in (("10 min", AZUL, "10 min"), ("30 s", LARANJA, "30 s"), ("3 s", VERM, "3 s")):
        v = []
        for T in Ts:
            vr = est["v_med"] + cv.fator_freq(T, est["n"]) * est["s"]
            v.append(cv.vento_projeto(vr, est["ktur"], est["cat"], est["h_cabo"], integ)[0])
        ax.plot(Ts, v, color=cor, lw=2.2, label=f"V de projeto – {nome}")
    for c in est["casos"]:
        ax.plot(c["TR"], c["VP"], "o", color="black", ms=5)
        ax.annotate(f"{c['nome'].split(' (')[0]}: {f(c['VP'], 1)} m/s", (c["TR"], c["VP"]), textcoords="offset points",
                    xytext=(5, -10), fontsize=6.5)
    ax.set_xscale("log")
    ax.set_xticks(Ts)
    ax.set_xticklabels([str(x) for x in Ts], fontsize=7)
    ax.set_xlabel("Período de retorno T (anos)", fontsize=9)
    ax.set_ylabel("Velocidade de projeto (m/s)", fontsize=9)
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    ax.set_title("Velocidade de projeto × período de retorno", fontsize=10)
    return fig


def fig_3d(est):
    ns = np.arange(10, 31, 2)
    Ts = np.array([10, 30, 50, 100, 150, 250])
    Z = np.array([[est["ktur"] * (est["v_med"] + cv.fator_freq(T, n) * est["s"]) for T in Ts] for n in ns])
    X, Y = np.meshgrid(Ts, ns)
    fig = plt.figure(figsize=(6.2, 4.4))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(np.log10(X), Y, Z, cmap="Blues", edgecolor="none")
    ax.set_xticks(np.log10(Ts))
    ax.set_xticklabels([str(t) for t in Ts], fontsize=7)
    ax.set_xlabel("T (anos)", fontsize=8)
    ax.set_ylabel("Anos de série n", fontsize=8)
    ax.set_zlabel("V_P 10 min (m/s)", fontsize=8)
    ax.view_init(elev=24, azim=-55)
    ax.set_title("Sensibilidade de V_P ao período de retorno e ao tamanho da série", fontsize=9)
    return fig


# ----------------------------------------------------------------------------- relatório
def gerar(caminho, proj, d, res, codigo="BK-LT-MC-VENTOS", rev="R0"):
    """d: dados da seção '3'; res: saída de calc_ventos.montar (deve ter res['ok'])."""
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    est = res["estudo"]
    R = Rel(proj, "Estudo de Ventos e Temperaturas – NBR 5422:2024", codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS TÉCNICAS ADOTADAS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. DIMENSIONAMENTO E VERIFICAÇÕES", "7. QUANTITATIVOS",
               "8. RESULTADOS OBTIDOS", "9. CONCLUSÕES", "10. REFERÊNCIAS BIBLIOGRÁFICAS", "ANEXO A – TABELA DE CASOS PARA O PLS-CADD"])
    mu_ = est["mu"]
    casos = {c["chave"]: c for c in est["casos"]}
    estacao = f"{d.get('est_nome') or 'DADO NÃO INFORMADO'} (código {d.get('est_cod') or 'DADO NÃO INFORMADO'})"

    # 1
    R.h1("OBJETIVO")
    R.p("Estabelecer as velocidades de vento e as temperaturas de projeto da linha de transmissão " + (proj.get("nome") or "") +
        ", conforme a ABNT NBR 5422:2024, a partir de dados meteorológicos do Instituto Nacional de Meteorologia (INMET), para "
        "aprovação pela transmissora e para uso na definição dos casos de carregamento do PLS-CADD.")
    R.p("Este documento não calcula forças do vento sobre cabos, isoladores e suportes (Seção 8.4 a 8.8 da norma), ângulos de balanço, "
        "temperatura do condutor em regime permanente nem distâncias de segurança.", "Escopo excluído:")

    # 2
    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["INMET", f"Dados meteorológicos da estação {estacao}", "—", d.get("serie_fim") and str(d.get("serie_fim")) or "—"],
        ["ABNT NBR 5422:2024", "Projeto de linhas aéreas de transmissão de energia elétrica", "2024", "2024"]], [3.5, 8.0, 1.5, 3.0])
    R.p("códigos, revisões e datas de especificação técnica e edital da transmissora não foram fornecidos.", "DADO NÃO INFORMADO —")

    # 3
    R.h1("NORMAS TÉCNICAS ADOTADAS")
    R.lista(["ABNT NBR 5422:2024 – Projeto de linhas aéreas de transmissão de energia elétrica."])
    R.tabela("Itens da NBR 5422:2024 aplicados", ["Item", "Assunto", "Aplicação neste estudo"], [
        ["3.1.49, 3.1.52 a 3.1.55", "Definições de temperaturas", "Temperatura coincidente, máxima, mínima e média"],
        ["4.3", "Temperatura do ar", "Séries mínimas de 10 anos"],
        ["4.7", "Massa específica do ar", "μ com a temperatura média das mínimas e a altitude média"],
        ["4.9.3 e Anexo A", "Vento – máximos anuais e Gumbel", "Velocidade de referência V_R(T)"],
        ["4.9.4, Tabelas 1 a 3", "Conversão das velocidades medidas", "Kint, Krug e Kalt"],
        ["8.2.1, Tabela 8", "Vento de 10 min", "V_P = Ktur·V_R"],
        ["8.2.2, Tabela 9", "Vento de 30 s", "V_P30 = Kint·Kalt·Krug·V_P"],
        ["8.2.3", "Vento de 3 s", "V_P3 = 1,15·Kint·V_P"],
        ["8.4.2", "Pressão dinâmica", "q0 = ½·μ·V_P²"],
        ["7.1.8, 7.3.1.1, 9.6.2.1, 17.2.2.2", "Períodos de retorno mínimos", "50/30, frequência industrial, manobra"]], [4.0, 5.5, 6.5])

    # 4
    R.h1("METODOLOGIA DE CÁLCULO")
    R.h2("Velocidade de referência por Gumbel")
    R.p("Obtém-se a velocidade do vento de 10 min, a 10 m de altura e terreno categoria B, com período de retorno T, a partir da série "
        "de máximos anuais. A NBR 5422:2024 (4.9.3.2 e Anexo A) modela a série pela distribuição de Gumbel, com série mínima de 10 anos.")
    R.p("Base teórica: Anexo A da própria norma (distribuição de valores máximos de Gumbel, parâmetros C1 e C2 dependentes de n); "
        "livro de apoio: fonte a confirmar no acervo.")
    R.eq(msub(mi("V"), mi("R")) + mu("(") + mi("T") + mu(")=") + mi("v̄") + mu("+") + msub(mi("K"), mu("T,n")) + mi("s") + mu(" ;  ") +
         msub(mi("K"), mu("T,n")) + mu("=") + mfrac(msub(mi("C"), mi("T")) + mu("−") + msub(mi("C"), mu("2")), msub(mi("C"), mu("1"))) + mu(" ;  ") +
         msub(mi("C"), mi("T")) + mu("=−ln[−ln(1−") + mfrac(mu("1"), mi("T")) + mu(")]"))
    R.simbolos([("v̄, s", "média e desvio-padrão da série de máximos anuais", "m/s"), ("n", "anos da série", "—"),
                ("C1, C2", "desvio-padrão e média de z_i = −ln[−ln(i/(n+1))] (Tabela A.1)", "—"), ("T", "período de retorno", "anos")])
    R.p("Fluxo: série → conversão para 10 min/10 m/B (4.9.4) → v̄ e s → C1, C2 → K(T,n) → V_R(T). Limitações: a distribuição assume "
        "máximos anuais independentes e estacionários; séries curtas aumentam a incerteza.")
    R.p("série com no mínimo 10 anos (4.9.3.2.1); coerência de K(T,n) com a Tabela A.2.", "Critério:")
    R.h2("Conversão das medições")
    R.p("Se a estação mede com integração, altura ou terreno diferentes dos de referência, converte-se a velocidade pela Eq. abaixo (4.9.4.1).")
    R.eq(mi("V") + mu("=") + mfrac(msub(mi("V"), mi("m")), msub(mi("K"), mu("int")) + msub(mi("K"), mu("rug")) + msub(mi("K"), mu("alt"))) +
         mu(" ;  ") + msub(mi("K"), mu("alt")) + mu("=") + msup(mpar(mfrac(mi("z"), mu("10"))), mi("α")))
    R.simbolos([("Kint", "fator de integração (Tabela 2)", "—"), ("Krug", "fator de rugosidade (Tabela 1)", "—"),
                ("Kalt", "fator de altura; α pela Tabela 3", "—"), ("z", "altura de medição", "m")])
    R.h2("Velocidades de projeto de 10 min, 30 s e 3 s")
    R.p("Calcula-se o vento de projeto aplicando o fator de turbulência regional (Tabela 8) e, para 30 s e 3 s, os fatores de integração.")
    R.eq(msub(mi("V"), mi("P")) + mu("=") + msub(mi("K"), mu("tur")) + msub(mi("V"), mi("R")) + mu(" ;  ") +
         msub(mi("V"), mu("P30")) + mu("=") + msub(mi("K"), mu("int")) + msub(mi("K"), mu("alt")) + msub(mi("K"), mu("rug")) + msub(mi("V"), mi("P")) +
         mu(" ;  ") + msub(mi("V"), mu("P3")) + mu("=1,15·") + msub(mi("K"), mu("int")) + msub(mi("V"), mi("P")))
    R.simbolos([("Ktur", "fator de turbulência da região (Tabela 8)", "—"), ("Kint (30 s)", "Tabela 9", "—"), ("Kint (3 s)", "Tabela 2", "—")])
    R.p("Limitações: métodos válidos para vãos de 200 a 800 m, suportes até 60 m e terreno sem canalização do vento (8.4.5).")
    R.h2("Massa específica do ar e pressão dinâmica")
    R.eq(mi("μ") + mu("=1,225·") + mfrac(mu("288,15"), mi("t") + mu("+273,15")) + mu("·exp(−1,2·") + msup(mu("10"), mu("−4")) + mi("alt") + mu(") ;  ") +
         msub(mi("q"), mu("0")) + mu("=") + mfrac(mu("1"), mu("2")) + mi("μ") + msup(msub(mi("V"), mi("P")), mu("2")))
    R.simbolos([("t", "temperatura média das mínimas (4.7)", "°C"), ("alt", "altitude média da região", "m"), ("q0", "pressão dinâmica", "Pa")])
    R.h2("Temperaturas")
    R.p("As temperaturas vêm do INMET e seguem as definições da norma: média (3.1.54), máxima (3.1.52), mínima (3.1.55) e coincidente "
        "(3.1.49). O EDS é adotado como a temperatura média (média das médias mensais), conforme critério do projeto.")

    # 5
    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    R.h2("Local do projeto e estação INMET")
    R.tabela("Local e estação", ["Parâmetro", "Valor", "Unidade", "Base"], [
        ["Estação INMET", estacao, "—", "INMET"],
        ["UF / região (Ktur)", f"{d.get('uf') or '—'} / {est['regiao']}", "—", "Tabela 8"],
        ["Município", d.get("municipio") or "—", "—", "Fornecido"],
        ["Latitude", f(d.get("lat"), 4) if d.get("lat") is not None else "—", "°", "Fornecido"],
        ["Longitude", f(d.get("lon"), 4) if d.get("lon") is not None else "—", "°", "Fornecido"],
        ["Altitude média", f(est["alt"], 0), "m", "Fornecido"],
        ["Período da série", f"{d.get('serie_ini') or '—'} a {d.get('serie_fim') or '—'}", "—", "INMET"]], [4.5, 5.5, 1.5, 4.5])
    R.figura(fig_mapa(d.get("lat"), d.get("lon"), d.get("municipio") or proj.get("nome") or "Projeto"),
             "Mapa do Brasil com a localização do projeto",
             "A Figura 1 mostra o ponto do projeto sobre o contorno dos estados; as coordenadas estão na Tabela 3.", larg_cm=11.0)
    R.h2("Dados de vento")
    cvv = est["cv"] * 100
    conv = est.get("conv") or {}
    R.tabela("Estatísticas da série de máximos anuais", ["Parâmetro", "Valor", "Unidade", "Base"], [
        ["Número de anos n", str(est["n"]), "—", "INMET"],
        ["Média v̄ (convertida p/ 10 min, 10 m, B)", f(est["v_med"], 3), "m/s", "INMET + 4.9.4"],
        ["Desvio-padrão s", f(est["s"], 3), "m/s", "INMET + 4.9.4"],
        ["Coeficiente de variação s/v̄", f(cvv, 1), "%", "Calculado"],
        ["C1 / C2", f"{f(est['c1'], 4)} / {f(est['c2'], 4)}", "—", "Anexo A (Tabela A.1)"],
        ["Kint · Krug · Kalt da conversão", f"{f(conv.get('Kint', 1), 2)} · {f(conv.get('Krug', 1), 2)} · {f(conv.get('Kalt', 1), 3)}", "—", "Tabelas 1 a 3"],
        ["Categoria do terreno (projeto)", est["cat"], "—", "Tabela 1"],
        ["Altura média do cabo", f(est["h_cabo"], 1), "m", "Geometria / informado"]], [6.0, 4.0, 1.5, 4.5])
    R.h2("Dados não informados e premissas")
    for n in res["pendencias"]:
        rot, _, resto = n.partition(" — ")
        R.p(resto, rot + " —")
    for n in res["avisos"]:
        rot, _, resto = n.partition(" — ")
        R.p(resto, rot + " —")
    R.p("Os períodos de retorno do vento de 10 min e de 3 s (suporte) foram adotados em " + f"{casos['max']['TR']:g}" + " e " +
        f"{casos['rajada']['TR']:g}" + " anos; a NBR 5422:2024 delega essa escolha à transmissora (12.3.3.2) e o valor deve ser confirmado no edital.", "PREMISSA —")
    R.p("o arquivo-modelo DOCUMENTO_PADRAO_BK.docx não foi fornecido; capa, cabeçalho e rodapé seguem a especificação textual.",
        "NECESSITA VALIDAÇÃO TÉCNICA —")

    # 6
    R.h1("DIMENSIONAMENTO E VERIFICAÇÕES")
    R.h2("Memória de cálculo – amostra completa (vento 50/30)")
    c = casos["v5030"]
    R.p("Calcular a velocidade do vento 50/30 (TR 50 anos, 30 s) para faixa de passagem e distância horizontal.", "Objetivo:")
    R.p(f"K(T,n) = (C_T − C2)/C1 = ({f(-math.log(-math.log(1 - 1 / c['TR'])), 4)} − {f(est['c2'], 4)})/{f(est['c1'], 4)} = {f(c['K'], 3)}.", "Substituição (Gumbel):")
    R.p(f"V_R = {f(est['v_med'], 3)} + {f(c['K'], 3)}·{f(est['s'], 3)} = {f(c['VR'], 3)} m/s.")
    fa = c["fatores"]
    R.p(f"V_P = {f(est['ktur'], 2)}·{f(c['VR'], 3)} = {f(est['ktur'] * c['VR'], 3)} m/s.", "Substituição (8.2.1.1):")
    R.p(f"V_P30 = {f(fa['Kint'], 2)}·{f(fa['Kalt'], 3)}·{f(fa['Krug'], 2)}·{f(est['ktur'] * c['VR'], 3)} = {f(c['VP'], 3)} m/s.", "Substituição (8.2.2.1):")
    R.p(f"q0 = ½·{f(mu_, 4)}·{f(c['VP'], 3)}² = {f(c['q0'], 1)} Pa.", "Substituição (8.4.2):")
    a = est["c1"] / est["s"]
    u = est["v_med"] - est["c2"] / a
    F = math.exp(-math.exp(-a * (c["VR"] - u)))
    R.p(f"F(V_R) = exp{{−exp[−a(V_R − u)]}} = {f(F, 5)}, com a = C1/s = {f(a, 4)} 1/(m/s) e u = v̄ − C2/a = {f(u, 3)} m/s; "
        f"esperado 1 − 1/T = {f(1 - 1 / c['TR'], 5)}. A distribuição reproduz o período de retorno adotado.", "Verificação independente:")
    R.p("Os demais casos seguem a mesma sequência e estão na Tabela 5.")
    R.tabela("Velocidades de projeto por caso", ["Caso", "T (anos)", "Integração", "K(T,n)", "V_R (m/s)", "V_P final (m/s)", "q0 (Pa)", "Item"],
             [[x["nome"], f(x["TR"], 0), x["integracao"], f(x["K"], 3), f(x["VR"], 2), f(x["VP"], 2), f(x["q0"], 0), x["ref"].split(" · ")[0]]
              for x in est["casos"]], [3.8, 1.2, 1.5, 1.4, 1.6, 1.8, 1.4, 3.3], fonte="Cálculo próprio (NBR 5422:2024)")
    R.figura(fig_vxtr(est), "Velocidade de projeto × período de retorno (2D)",
             "A Figura 2 mostra que a velocidade cresce lentamente com T; as curvas de 30 s e 3 s ficam acima da de 10 min pelos fatores de integração. "
             "Os pontos marcados são os casos deste estudo.")
    R.figura(fig_3d(est), "Sensibilidade de V_P ao período de retorno e ao tamanho da série (3D)",
             "A Figura 3 mostra o efeito do número de anos da série: séries curtas elevam a velocidade extrapolada para T grandes.")
    R.h2("Massa específica do ar e temperaturas")
    R.p(f"μ = 1,225·288,15/({f(res['temps']['t_coinc'], 1)}+273,15)·exp(−1,2·10⁻⁴·{f(est['alt'], 0)}) = {f(mu_, 4)} kg/m³; "
        f"Q = μ/2 = {f(mu_ / 2, 4)} kg/m³ (pressão = Q·V²).", "Substituição (4.7):")
    R.p("o estudo usa valores estatísticos fornecidos; a verificação da série (completude, homogeneidade) é responsabilidade da fonte.", "Limitações:")

    # 7
    R.h1("QUANTITATIVOS")
    R.p("Não aplicável a este documento.")

    # 8
    R.h1("RESULTADOS OBTIDOS")
    linhas = []
    for a_ in res["aprovacao"]:
        nd = 2 if a_["unidade"] == "m/s" else (4 if a_["unidade"] == "kg/m³" else 1)
        val = "—" if a_["valor"] is None else f(a_["valor"], nd)
        pr = "—" if a_.get("pressao") is None else f(a_["pressao"], 1)
        linhas.append([a_["item"], val, a_["unidade"], pr, a_["base"], a_["fonte"]])
    R.tabela("Quadro de dados para aprovação da transmissora", ["Parâmetro", "Valor", "Unid.", "Pressão (Pa)", "Base (NBR 5422:2024)", "Fonte do dado"],
             linhas, [4.0, 1.6, 1.2, 1.6, 4.4, 3.2],
             fonte="Dados meteorológicos: INMET, estação " + estacao + ". Cálculo próprio conforme NBR 5422:2024.")
    R.p("o quadro apresenta valores calculados e não declara aprovação; a aprovação cabe à transmissora.", "RESULTADO:")
    R.tabela("Resumo das verificações", ["Verificação", "Norma/critério", "Valor calculado", "Limite", "Status"], [
        ["Série de vento ≥ 10 anos", "NBR 5422:2024, 4.9.3.2.1", f"{est['n']} anos", "≥ 10 anos", "ATENDE" if est["n"] >= 10 else "NÃO ATENDE"],
        ["TR do vento 50/30", "7.1.8.2 / 7.3.1.1", f"{casos['v5030']['TR']:g} anos", "≥ 50 anos", "ATENDE" if casos["v5030"]["TR"] >= 50 else "NÃO ATENDE"],
        ["TR de frequência industrial", "9.6.2.1a", f"{casos['freq']['TR']:g} anos", "≥ 10 anos", "ATENDE" if casos["freq"]["TR"] >= 10 else "NÃO ATENDE"],
        ["TR de manobra", "9.6.2.1b", f"{casos['manobra']['TR']:g} anos", "≥ 2 anos", "ATENDE" if casos["manobra"]["TR"] >= 2 else "NÃO ATENDE"],
        ["TR vento 10 min e 3 s (suporte)", "12.3.3.2 / edital", f"{casos['max']['TR']:g} / {casos['rajada']['TR']:g} anos", "critério da transmissora", "PENDENTE"],
        ["Período de temperatura ≥ 10 anos", "4.3.1 / 4.3.2", "informar período INMET", "≥ 10 anos", "PENDENTE"]],
        [4.0, 3.6, 3.0, 3.0, 2.4])

    # 9
    R.h1("CONCLUSÕES")
    R.p("Resultados calculados:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista([f"{a_['item']}: {f(a_['valor'], 2 if a_['unidade'] == 'm/s' else (4 if a_['unidade'] == 'kg/m³' else 1))} {a_['unidade']}"
             + (f", pressão {f(a_['pressao'], 1)} Pa" if a_.get("pressao") is not None else "") + f" ({a_['base']})"
             for a_ in res["aprovacao"] if a_["valor"] is not None])
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Confirmar com a transmissora os períodos de retorno do vento de 10 min e de 3 s.",
             "Registrar a estação, o período e o tratamento dos dados do INMET.",
             "Validar a convenção do fator Q da tabela de casos no PLS-CADD."])

    # 10
    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["ABNT NBR 5422:2024 – Projeto de linhas aéreas de transmissão de energia elétrica.",
             "INSTITUTO NACIONAL DE METEOROLOGIA (INMET). Dados meteorológicos – estação " + estacao + ".",
             "GUMBEL, E. J. Statistics of Extremes. Columbia University Press, 1958 (a confirmar edição)."])

    # anexo
    R.doc.add_page_break()
    R.h1("ANEXO A – TABELA DE CASOS PARA O PLS-CADD")
    R.p("A tabela abaixo reúne os casos de clima com as velocidades e temperaturas calculadas neste estudo, no formato de colunas do PLS-CADD.")
    R.tabela("Casos de clima – colunas do PLS-CADD", ["#", "Description", "Q (kg/m³)", "Vento (m/s)", "Pressão (Pa)", "T cabo (°C)", "T amb. (°C)", "Modelo altura"],
             [[str(p_["Row #"]), p_["Description"], f(p_["Air Density Factor (Q) (kg/m^3)"], 4),
               "—" if p_["Wind Velocity (m/s)"] is None else f(p_["Wind Velocity (m/s)"], 2),
               "—" if p_["Wind Pressure (Pa)"] is None else f(p_["Wind Pressure (Pa)"], 1),
               "—" if p_["Wire Temp. (deg C)"] is None else f(p_["Wire Temp. (deg C)"], 1),
               "—" if p_["Ambient Temp. (deg C)"] is None else f(p_["Ambient Temp. (deg C)"], 1), p_["Wire Wind Height Adjust Model"]]
              for p_ in res["pls"]], [0.7, 3.6, 1.6, 1.6, 1.8, 1.6, 1.6, 2.6])
    R.p("Q = μ/2 (kg/m³), pressão = Q·V² (Pa). Colunas fixas em todas as linhas: Wire Ice Thickness, Ice Density, Ice Load e NESC Constant = 0; "
        "Weather Load Factor = 1; Wire Gust Response Factor = 1. As linhas \"Frequência Industrial\" e \"Surto manobra\" alimentam o balanço das cadeias (M5/M12).", "Colunas do PLS-CADD:")
    R.p("temperaturas de condutor de cada caso (75 °C, 90 °C, 40 °C) são do projeto, não da norma; o vento reduzido, se listado, tem origem a confirmar.",
        "PREMISSA —")
    R.salvar(caminho)
    return caminho
