"""Relatório do Módulo 16 – Blindagem contra Descargas Atmosféricas (EGM, falha de blindagem e backflashover), padrão BK."""
import datetime as dt
import math

import matplotlib.pyplot as plt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from relatorio_m2 import AZUL, CINZA, LARANJA, VERM, Rel, estilo_ax, f, mi, mu, mfrac, mpar, msqrt, msub, msup


def _st(ok):
    return "ATENDE" if ok else "NÃO ATENDE"


def fig_egm(r):
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    estilo_ax(ax)
    rs = 6.7 * r["i_graf"] ** 0.8
    for o in r["fases"] + r["guardas"]:
        c = plt.Circle((o["x"], o["y"]), rs, fill=False, ls=":", lw=0.9, color=LARANJA if "nome" in o else CINZA)
        ax.add_patch(c)
    xs = [o["x"] for o in r["fases"] + r["guardas"]]
    ax.plot([min(xs) - rs, max(xs) + rs], [r["beta"] * rs] * 2, color="#8B6B3E", lw=1.5, label=f"Solo (βs·D = {f(r['beta'] * rs, 1)} m)")
    ax.plot([o["x"] for o in r["fases"]], [o["y"] for o in r["fases"]], "o", color=AZUL, label="Fases")
    ax.plot([o["x"] for o in r["guardas"]], [o["y"] for o in r["guardas"]], "D", color="#404040", label="Para-raios")
    for a, b in r["ints_graf"]:
        ax.plot([a, b], [0.3, 0.3], color=VERM, lw=4)
    ax.set_xlim(min(xs) - 1.1 * rs, max(xs) + 1.1 * rs)
    ax.set_ylim(0, max(o["y"] for o in r["fases"] + r["guardas"]) + 0.5 * rs)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)"); ax.set_ylabel("Altura (m)")
    ax.set_title(f"Modelo eletrogeométrico com I = {f(r['i_graf'], 1)} kA (D = {f(rs, 0)} m); vermelho: largura exposta de fase", fontsize=8)
    ax.legend(fontsize=7, loc="upper right")
    return fig


def fig_w(r):
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    estilo_ax(ax)
    ax.plot(r["corr"], r["W"], color=AZUL, lw=2)
    ax.axvline(r["i_flash_sf"], color=VERM, ls=":", label=f"I mín. flashover = {f(r['i_flash_sf'], 1)} kA")
    ax.set_xlabel("Corrente do raio (kA)"); ax.set_ylabel("Largura exposta de fase (m)")
    ax.set_title("Largura exposta × corrente", fontsize=10)
    ax.legend(fontsize=7)
    return fig


def gerar(caminho, proj, e, r, codigo="BK-LT-MC-M16", rev="R0"):
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    R = Rel(proj, "Blindagem contra Descargas Atmosféricas", codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS E CRITÉRIOS ADOTADOS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. RESULTADOS OBTIDOS", "7. CONCLUSÕES", "8. REFERÊNCIAS BIBLIOGRÁFICAS"])

    R.h1("OBJETIVO")
    R.p("Avaliar a blindagem dos cabos para-raios e o desempenho frente a descargas atmosféricas da linha de transmissão" + (" " + proj["nome"] if proj.get("nome") else "") +
        ": ângulo de blindagem, falha de blindagem (descarga direta nas fases) pelo modelo eletrogeométrico, backflashover e taxa total de desligamentos por 100 km e por ano.")
    R.p("descargas indiretas (induzidas, desprezíveis acima de 90 kV – Kiessling 4.3.3), descargas no meio do vão com análise de ondas viajantes e estudo estatístico "
        "completo (Monte Carlo/FLASH/ATP).", "Escopo excluído:")

    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["Diretrizes de projeto básico", "Desempenho a descargas atmosféricas (metas de desligamentos e de falha de blindagem)", "—", "—"],
        ["Kiessling et al.", "Overhead Power Lines, cap. 4 (eq. 4.1 a 4.7, Tabela 4.2)", "—", "—"],
        ["Projeto Elétrico de LTs (Livro 2)", "Item 4.2.1 – isolamento para descargas atmosféricas", "—", "—"]], [3.8, 8.0, 1.4, 2.8])

    R.h1("NORMAS E CRITÉRIOS ADOTADOS")
    R.lista([f"Meta de desligamentos por descargas: ≤ {f(e['meta'], 1)} por 100 km por ano (Diretrizes: 2 até 230 kV; 1 a partir de 345 kV).",
             f"Meta de falha de blindagem: ≤ {f(e['meta_sf'], 3)} por 100 km por ano, independentemente do nível de tensão (Diretrizes).",
             f"Ângulo de blindagem máximo adotado: {f(e['ang_lim'], 0)}° (Kiessling 4.4.2: 10° a 35° conforme a importância da linha) – PREMISSA.",
             "Mínimo de dois cabos para-raios (edital TAESA / Diretrizes)."])

    R.h1("METODOLOGIA DE CÁLCULO")
    R.h2("Modelo eletrogeométrico")
    R.p("A distância de atração (Kiessling eq. 4.1) é D = 6,7·I^0,8; ao solo, βs·D, com βs = " + f(r["beta"], 2) + ". Percorrem-se posições laterais do líder; "
        "a primeira superfície atrativa encontrada (círculos de raio D em torno de fases e para-raios, ou o plano a βs·D do solo) define o ponto de impacto. "
        "A largura lateral em que o impacto ocorre numa fase é a largura exposta W(I).")
    R.eq(mi("D") + mu("=6,7") + msup(mi("I"), mu("0,8")) + mu(" ;  ") + msub(mi("U"), mi("c")) + mu("=") + mfrac(mu("1"), mu("2")) + mi("I") + msub(mi("Z"), mi("c")) + mu(" ;  ") +
         msub(mi("I"), mu("fl")) + mu("=") + mfrac(mu("2") + msub(mi("U"), mu("50")), msub(mi("Z"), mi("c"))))
    R.eq(msub(mi("N"), mu("sf")) + mu("=") + msub(mi("N"), mi("g")) + mu("·0,1·") + mu("∑") + mi("W") + mpar(mi("I")) + mi("p") + mpar(mi("I")) + mi("ΔI") + mu("  (I ≥ ") + msub(mi("I"), mu("fl")) + mu(")"))
    R.simbolos([("D", "distância de atração", "m"), ("I", "corrente de pico do raio", "kA"), ("Zc", "impedância de surto da fase", "Ω"), ("U50", "tensão crítica de descarga (CFO)", "kV"),
                ("Ng", "densidade de descargas ao solo", "1/km²/ano"), ("W(I)", "largura exposta de fase", "m"), ("p(I)", "densidade de probabilidade da corrente", "1/kA")])
    R.h2("Backflashover")
    R.eq(msub(mi("I"), mu("c,BF")) + mu(":  ") + mi("I") + mpar(msub(mi("R"), mi("i")) + mpar(mi("I")) + mu("+") + msub(mi("Z"), mu("t"))) + mpar(mu("1−") + mi("k")) + mu("=") + msub(mi("U"), mu("50")) + mu(" ;  ") +
         msub(mi("R"), mi("i")) + mu("=") + mfrac(msub(mi("R"), mu("0")), msqrt(mu("1+") + mfrac(mi("I"), msub(mi("I"), mi("g"))))))
    R.eq(msub(mi("N"), mu("BF")) + mu("=") + msub(mi("N"), mi("L")) + msub(mi("f"), mu("t")) + mi("P") + mpar(mi("I") + mu("≥") + msub(mi("I"), mu("c,BF"))) + mu(" ;  ") +
         msub(mi("N"), mi("L")) + mu("=") + mfrac(msub(mi("N"), mi("g")) + mpar(mu("28") + msup(mi("h"), mu("0,6")) + mu("+") + mi("b")), mu("10")))
    R.simbolos([("k", "coeficiente de acoplamento guarda–fase", "—"), ("Ri", "resistência de pé de torre com ionização", "Ω"), ("Zt", "impedância de surto da torre", "Ω"),
                ("Ig", "corrente limite de ionização = E0·ρ/(2π·R0²)", "kA"), ("ft", "fração das descargas em guarda que vão à torre", "—"), ("NL", "descargas na LT", "1/100 km/ano")])
    R.p("NECESSITA VALIDAÇÃO: a eq. (4.6) do Kiessling está ilegível no acervo; a distribuição de corrente P(I ≥ i) = 1/(1+(i/31)^2,6) (CIGRE/Anderson), o número de "
        "descargas N_L (Eriksson/IEEE 1243), a ionização do solo e a fração ft = 0,6 são formulações usuais fora do acervo.")

    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    R.tabela("Parâmetros do cálculo", ["Parâmetro", "Valor", "Unidade", "Origem"], [
        ["Densidade de descargas Ng", f(e["ng"], 2), "1/km²/ano", "PREMISSA / informado"], ["Faixa de tensão (βs)", f"{e['faixa']} ({f(r['beta'], 2)})", "—", "Kiessling 4.4.1"],
        ["Un / Umáx", f"{f(e['un_kv'], 1)} / {f(e['umax_kv'], 1)}", "kV", "Módulo 1"], ["CFO (U50 %)", f(r["cfo"], 0), "kV", "Tabela 15 ÷ 0,961 ou informado"],
        ["Zc da fase", f(r["zc"], 0), "Ω", "60·ln(2h/r_eq)"], ["Resistência de pé de torre R0", f(e["r_pe"], 1), "Ω", "Módulo 6 / informado"],
        ["Z da torre em série", f(e["z_torre"], 1), "Ω", "PREMISSA"], ["Ionização do solo", "sim (ρ = " + f(e["rho"], 0) + " Ω·m)" if e["ioniza"] else "não", "—", "PREMISSA"],
        ["Altura da torre (N_L)", f(e["h_torre"], 1), "m", "Módulo 2"], ["Fração na torre ft", f(e["frac_torre"], 2), "—", "PREMISSA"]], [5.2, 4.0, 2.4, 4.4])
    R.tabela("Geometria (alturas médias no vão = altura na estrutura − 2/3 da flecha)", ["Condutor", "x (m)", "y médio (m)", "Ângulo de blindagem (°)"],
             [[o["nome"], f(o["x"], 2), f(o["y"], 2), f(a, 1) if a is not None else "sem blindagem"] for o, a in zip(r["fases"], r["ang"])] +
             [[f"Para-raios {i + 1}", f(o["x"], 2), f(o["y"], 2), "—"] for i, o in enumerate(r["guardas"])], [4.0, 3.0, 3.0, 4.0])

    R.h1("RESULTADOS OBTIDOS")
    R.figura(fig_egm(r), "Modelo eletrogeométrico para a corrente mínima de flashover.", larg_cm=14.0)
    R.figura(fig_w(r), "Largura exposta de fase em função da corrente.", larg_cm=13.0)
    R.tabela("Desempenho (por 100 km e por ano)", ["Grandeza", "Valor", "Meta", "Situação"], [
        ["Descargas em fase (falha de blindagem)", f(r["n_sf_atinge"], 3), "—", "—"],
        ["Falha de blindagem com flashover", f(r["n_sf"], 3), f"≤ {f(e['meta_sf'], 3)}", _st(r["ok_sf"])],
        ["Corrente crítica de backflashover (kA)", f(r["i_c_bf"], 1), "—", "—"], ["Backflashover", f(r["n_bf"], 2), "—", "—"],
        ["Total de desligamentos", f(r["total"], 2), f"≤ {f(e['meta'], 1)}", _st(r["ok_total"])]], [6.5, 3.0, 3.0, 3.0])
    R.p(f"Corrente máxima de falha de blindagem: {f(r['i_max_blind'], 0)} kA; coeficiente de acoplamento k = {f(r['k'], 3)}; corrente mínima para flashover em fase = {f(r['i_flash_sf'], 1)} kA.")

    R.h1("CONCLUSÕES")
    R.lista([f"Falha de blindagem: {f(r['n_sf'], 3)} desligamentos/100 km/ano (meta {f(e['meta_sf'], 3)}): " + _st(r["ok_sf"]) + ".",
             f"Backflashover: {f(r['n_bf'], 2)} desligamentos/100 km/ano (corrente crítica {f(r['i_c_bf'], 0)} kA).",
             f"Total: {f(r['total'], 2)} desligamentos/100 km/ano (meta {f(e['meta'], 1)}): " + _st(r["ok_total"]) + ".",
             "Ângulo de blindagem máximo: " + (f"{f(r['ang_max'], 1)}° (limite {f(e['ang_lim'], 0)}°)." if r["ang_max"] is not None else "não aplicável.")])
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Se a falha de blindagem exceder a meta: reduzir o ângulo de blindagem, elevar ou aproximar os para-raios, ou usar para-raios de linha (Kiessling 4.4.3).",
             "Se o backflashover exceder a meta: reduzir a resistência de pé de torre (contrapeso, Módulo 6) ou aumentar o isolamento (CFO).",
             "Confirmar Ng local (mapa de densidade de descargas) e, para o projeto básico, executar o estudo estatístico (Monte Carlo/FLASH/ATP) exigido pelas Diretrizes."])
    R.p("Grau de confiança: médio (método simplificado). Dependem de premissas: Ng, CFO, R de pé de torre, distribuição de corrente, N_L e ft.", "O que falta para eu informar com certeza:")

    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["Kiessling, F. et al. – Overhead Power Lines: Planning, Design, Construction – cap. 4 (eq. 4.1 a 4.7, Tabela 4.2).",
             "Diretrizes para a elaboração de projetos básicos para empreendimentos de transmissão – desempenho a descargas atmosféricas.",
             "Projeto Elétrico de Linhas de Transmissão – item 4.2.1.",
             "IEEE Std 1243 / CIGRE TB 63 (não consultados – NECESSITAM VALIDAÇÃO)."])
    R.salvar(caminho)
    return caminho
