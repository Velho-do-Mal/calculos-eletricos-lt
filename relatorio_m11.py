"""Relatório do Módulo 11 – Efeito Corona (gradiente superficial, critério de Peek e perdas), padrão BK."""
import datetime as dt

import matplotlib.pyplot as plt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from relatorio_m2 import AZUL, CINZA, LARANJA, VERM, Rel, estilo_ax, f, mi, mu, mfrac, mpar, msqrt, msub, msup


def _st(ok):
    return "ATENDE" if ok else "NÃO ATENDE"


def fig_gradiente(r):
    gr = r["gradientes"]
    fig, ax = plt.subplots(figsize=(6.0, 3.3))
    estilo_ax(ax)
    ax.bar([g["nome"] for g in gr], [g["E"] for g in gr], color=AZUL, label="Gradiente máximo (Umáx)")
    for k, c in r["circuitos"].items():
        ax.axhline(c["cond"]["Tempo bom"]["E0"], color=VERM, ls="--", lw=1.2, label=f"E0 Peek C{k} (tempo bom)")
        ax.axhline(c["cond"]["Chuva"]["E0"], color=LARANJA, ls=":", lw=1.2, label=f"E0 Peek C{k} (chuva)")
    ax.set_ylabel("kV eficaz / cm")
    ax.set_title("Gradiente superficial × gradiente crítico de Peek", fontsize=10)
    ax.legend(fontsize=7)
    return fig


def fig_perdas(r):
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    estilo_ax(ax)
    for k, c in r["circuitos"].items():
        u = [p["U"] for p in c["curva"]]
        ax.plot(u, [p["Tempo bom"] for p in c["curva"]], color=AZUL, lw=2, label=f"C{k} tempo bom")
        ax.plot(u, [p["Chuva"] for p in c["curva"]], color=LARANJA, lw=2, label=f"C{k} chuva")
        ax.axvline(c["umax"], color=CINZA, ls=":", lw=1)
    ax.axhline(r["lim_perda"], color=VERM, ls=":", label=f"Limite {r['lim_perda']:g} kW/km")
    ax.set_xlabel("Tensão entre fases (kV)"); ax.set_ylabel("Perda corona trifásica (kW/km)")
    ax.set_title("Perdas por efeito corona (Peek)", fontsize=10)
    ax.legend(fontsize=7)
    return fig


def gerar(caminho, proj, e, r, d, codigo="BK-LT-MC-M11", rev="R0"):
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    R = Rel(proj, "Efeito Corona – Gradiente Superficial, Critério de Peek e Perdas", codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS E CRITÉRIOS ADOTADOS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. RESULTADOS OBTIDOS", "7. CONCLUSÕES", "8. REFERÊNCIAS BIBLIOGRÁFICAS"])

    R.h1("OBJETIVO")
    R.p("Avaliar o efeito corona da linha de transmissão" + (" " + proj["nome"] if proj.get("nome") else "") +
        ": gradiente de potencial na superfície dos condutores, gradiente e tensão críticos disruptivos (Peek) e perdas por efeito corona, "
        "em tempo bom e em chuva, nas tensões nominal e máxima operativa.")
    R.p("rádio-interferência e ruído audível (Módulo 10) e interferência em linhas e dutos (Módulo 9).", "Escopo excluído:")

    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["Projeto Elétrico de LTs (Livro 2)", "Itens 3.2.5 (tensão crítica disruptiva) e 3.2.6 (perdas de Peek)", "—", "—"],
        ["Cálculos Elétricos de LTs (Livro 3)", "Cap. 7 – Efeito corona (gradiente crítico, Tabela 7.2)", "—", "—"],
        ["Kiessling et al.", "Overhead Power Lines, 2.3.3 (gradiente) e 7.3.4 (perdas)", "—", "—"]], [3.8, 8.0, 1.4, 2.8])

    R.h1("NORMAS E CRITÉRIOS ADOTADOS")
    R.lista(["Gradiente de superfície máximo × gradiente crítico de Peek (E/E0 < 1: sem corona visual).",
             f"Perda corona limite de projeto: {f(r['lim_perda'], 2)} kW/km trifásica (Livro 3/Villas: 1,2 kW/km; Livro 2: 1,24 kW/km). PREMISSA: confirmar com o cliente/edital.",
             "Kiessling 7.3.4 (informativo): perdas típicas de ≈ 2 kW/km em tempo bom, ≈ 5 kW/km em chuva e até 100 kW/km sob geada (EHV).",
             "Norma brasileira específica de perdas corona não consta no acervo: NECESSITA VALIDAÇÃO."])

    R.h1("METODOLOGIA DE CÁLCULO")
    R.h2("Densidade relativa do ar")
    R.eq(mi("δ") + mu("=") + mfrac(mu("3,92") + mi("p"), mu("273+") + mi("θ")) + mu(" ;  ") + mi("p") + mu("=76·") + msup(mu("10"), mu("−") + mfrac(mi("h"), mu("18336"))))
    R.simbolos([("p", "pressão barométrica", "cmHg"), ("h", "altitude", "m"), ("θ", "temperatura ambiente", "°C")])
    R.h2("Gradiente superficial")
    R.p("Cargas pela matriz de coeficientes de potencial (feixe → raio equivalente; guardas aterrados e imagens) e gradiente máximo no subcondutor com o fator de feixe "
        "(Kiessling eq. 2.15 a 2.17); os gradientes são proporcionais à tensão.")
    R.eq(msub(mi("E"), mi("i")) + mu("=") + mfrac(mu("|") + msub(mi("Q"), mi("i")) + mu("|"), mu("2π") + msub(mi("ε"), mu("0")) + mi("n") + mi("r")) +
         mpar(mu("1+") + msub(mi("k"), mu("2")) + mfrac(mi("r"), mi("s"))))
    R.h2("Gradiente crítico e tensão crítica (Peek)")
    R.eq(msub(mi("E"), mu("0")) + mu("=") + msub(mi("g"), mu("0")) + mi("m") + msub(mi("m"), mi("t")) + mi("δ") + mpar(mu("1+") + mfrac(mu("0,301"), msqrt(mi("δ") + mi("r")))))
    R.eq(msub(mi("U"), mi("c")) + mu("=84") + msub(mi("m"), mi("c")) + msub(mi("m"), mi("t")) + mi("δ") + mi("r") + mi("n") + mu("log") + mpar(mfrac(mi("D"), mu("r′"))) +
         mu(" ;  ") + msub(mi("V"), mi("c")) + mu("=") + mfrac(msub(mi("U"), mi("c")), msqrt(mu("3"))))
    R.simbolos([("g0", "gradiente de referência (21,1 ou 21,6)", "kV/cm"), ("m", "fator de superfície", "—"), ("mt", "fator de tempo (1,0 seco; 0,8 chuva)", "—"),
                ("r", "raio do subcondutor", "cm"), ("n", "subcondutores por fase", "—"), ("D", "distância média geométrica entre fases", "m"),
                ("r′", "raio equivalente do feixe (n·r·R^(n−1))^(1/n)", "cm")])
    R.h2("Perdas por efeito corona (Peek)")
    R.eq(mi("P") + mu("=") + mfrac(mu("241"), mi("δ")) + mpar(mi("f") + mu("+25")) + msqrt(mfrac(mi("r"), mi("D"))) + msup(mpar(mi("V") + mu("−") + msub(mi("V"), mi("c"))), mu("2")) + mu("·") + msup(mu("10"), mu("−5")))
    R.simbolos([("P", "perda por fase", "kW/km"), ("f", "frequência", "Hz"), ("V, Vc", "tensões fase-neutro (operação e crítica)", "kV")])
    R.p("NECESSITA VALIDAÇÃO: a equação (1) do Livro 3 está ilegível no acervo; adotou-se a formulação clássica de Peek com g0 selecionável. "
        "Nas perdas usa-se o raio equivalente do feixe r′. A fórmula de Peek tende a subestimar perdas em chuva forte e geada (Kiessling 7.3.4).")

    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    R.tabela("Parâmetros do cálculo", ["Parâmetro", "Valor", "Unidade", "Origem"], [
        ["Altitude / temperatura", f"{f(r['alt'], 0)} / {f(r['temp'], 0)}", "m / °C", "Informado"],
        ["δ (densidade relativa do ar)", f(r["delta"], 3), "—", "Peek"],
        ["Frequência", f(r["freq"], 0), "Hz", "Módulo 1"],
        ["Fator de superfície m", f(r["m_sup"], 2), "—", "PREMISSA"],
        ["Fator de tempo mt (chuva)", f(r["mt_chuva"], 2), "—", "Livro 2"],
        ["g0 (Peek)", f(r["g0"], 1), "kV/cm", "PREMISSA – NECESSITA VALIDAÇÃO"],
        ["Altura mínima do condutor mais baixo", f(r["h_min"], 2), "m", "Altura na estrutura − flecha"],
        ["Cabos guarda no gradiente", "incluídos (aterrados)" if r["incluir_guardas"] else "desprezados", "—", "PREMISSA"],
        ["Limite de perda", f(r["lim_perda"], 2), "kW/km", "PREMISSA"]], [6.0, 3.5, 2.0, 4.5])
    R.tabela("Circuitos", ["Circuito", "Un (kV)", "Umáx (kV)", "Subcond.", "d (mm)", "s (mm)", "D (m)"],
             [[k, f(c["un"], 1), f(c["umax"], 1), c["n"], f(c["d_mm"], 1), f(c["s_mm"], 0), f(c["D"], 2)] for k, c in sorted(r["circuitos"].items())],
             [1.8, 2.2, 2.4, 2.0, 2.2, 2.2, 2.2])

    R.h1("RESULTADOS OBTIDOS")
    R.h2("Gradiente superficial")
    gr = r["gradientes"]
    R.tabela("Gradiente máximo por fase (Umáx)", ["Fase", "E máx. (kV/cm)", "E0 tempo bom (kV/cm)", "E/E0 tempo bom", "E0 chuva (kV/cm)", "E/E0 chuva"],
             [[g["nome"], f(g["E"], 2), f(r["circuitos"][g["circuito"]]["cond"]["Tempo bom"]["E0"], 2), f(g["E"] / r["circuitos"][g["circuito"]]["cond"]["Tempo bom"]["E0"], 2),
               f(r["circuitos"][g["circuito"]]["cond"]["Chuva"]["E0"], 2), f(g["E"] / r["circuitos"][g["circuito"]]["cond"]["Chuva"]["E0"], 2)]
              for g in gr if g["circuito"] in r["circuitos"]], [3.0, 2.6, 3.0, 2.6, 2.8, 2.6])
    R.figura(fig_gradiente(r), "Gradiente superficial por fase e gradiente crítico de Peek.", larg_cm=13.0)
    R.h2("Tensão crítica e perdas")
    lin = []
    for k, c in sorted(r["circuitos"].items()):
        for cn, cd in c["cond"].items():
            for rot, t in cd["tens"].items():
                lin.append([f"C{k}", cn, f"{rot} {f(t['U'], 1)}", f(cd["Uc"], 1), f(t["V_rel"], 2), f(t["P_trif"], 3), _st(t["ok_P"])])
    R.tabela("Tensão crítica e perdas por circuito", ["Circ.", "Condição", "Tensão (kV)", "Uc (kV)", "V/Vc", "Perda (kW/km)", "Situação"], lin,
             [1.4, 2.4, 3.0, 2.2, 1.8, 2.8, 2.4])
    R.figura(fig_perdas(r), "Perdas corona trifásicas × tensão de operação.", larg_cm=13.0)

    R.h1("CONCLUSÕES")
    pk = max(t["P_trif"] for c in r["circuitos"].values() for cd in c["cond"].values() for t in cd["tens"].values())
    ok = all(t["ok_P"] for c in r["circuitos"].values() for cd in c["cond"].values() for t in cd["tens"].values())
    ratio = max(g["E"] / r["circuitos"][g["circuito"]]["cond"]["Tempo bom"]["E0"] for g in gr if g["circuito"] in r["circuitos"])
    R.lista([f"Gradiente máximo: {f(max(g['E'] for g in gr), 2)} kV/cm ({f(ratio * 100, 0)} % do gradiente crítico de Peek em tempo bom).",
             f"Perda corona máxima calculada: {f(pk, 3)} kW/km (limite {f(r['lim_perda'], 2)} kW/km): " + ("ATENDE." if ok else "NÃO ATENDE.")])
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Se E/E0 ≥ 1 ou a perda exceder o limite: aumentar o diâmetro/número de subcondutores ou o espaçamento do feixe.",
             "Validar g0, m e mt com o Livro 3 (cap. 7) e confirmar o limite de perda com o cliente/edital.",
             "Considerar sobretensões e variações de altitude ao longo do traçado (δ menor → mais corona)."])
    R.p("Grau de confiança: médio (método de Peek, empírico). Dependem de premissas: fator m, g0, mt e o limite de perda. Perdas em chuva forte/geada podem ser maiores.",
        "O que falta para eu informar com certeza:")

    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["Projeto Elétrico de Linhas de Transmissão – itens 3.2.5 e 3.2.6.",
             "Cálculos Elétricos de Linhas de Transmissão – cap. 7 (efeito corona).",
             "Kiessling, F. et al. – Overhead Power Lines – 2.3.3 e 7.3.4.",
             "Villas, J. E. et al. – Transmissão de Energia Elétrica – cap. 8."])
    R.salvar(caminho)
    return caminho
