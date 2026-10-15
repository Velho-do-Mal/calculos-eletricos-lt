"""
Relatório do Módulo 10 – Gradiente superficial, rádio-interferência (RI) e ruído audível (RA), padrão BK.
"""
import datetime as dt

import matplotlib.pyplot as plt
from docx.enum.text import WD_ALIGN_PARAGRAPH

import calc_corona as cr
from relatorio_m2 import AZUL, CINZA, LARANJA, VERM, Rel, estilo_ax, f, mi, mu, mfrac, mpar, msqrt, msub, msup


def _st(ok):
    return "ATENDE" if ok else "NÃO ATENDE"


def fig_gradiente(r):
    gr = r["gradientes"]
    fig, ax = plt.subplots(figsize=(6.0, 3.3))
    estilo_ax(ax)
    ax.bar([g["nome"] for g in gr], [g["E"] for g in gr], color=AZUL, label="Gradiente máximo calculado")
    ax.plot([g["nome"] for g in gr], [g["E_visual"] for g in gr], "o--", color=VERM, label="Gradiente crítico visual (Peek)")
    ax.axhline(17.0, color=LARANJA, ls=":", label="Referência prática ≈ 17 kV/cm")
    ax.set_ylabel("kV eficaz / cm")
    ax.set_title("Gradiente superficial por fase", fontsize=10)
    ax.legend(fontsize=7)
    return fig


def fig_perfil(r):
    pf = r["perfil"]
    fig, axs = plt.subplots(2, 1, figsize=(6.2, 5.4), sharex=True)
    estilo_ax(axs[0]); estilo_ax(axs[1])
    axs[0].plot(pf["x"], pf["RI_K"], color=AZUL, lw=2, label="Kiessling (tempo bom)")
    axs[0].plot(pf["x"], pf["RI_FG"], color=CINZA, lw=1.5, ls="--", label="Método FG" + (" (chuva)" if r["chuva"] else " (tempo bom)"))
    axs[0].axhline(r["lim_ri"], color=VERM, ls=":", label=f"Limite {r['lim_ri']:.0f} dB µV/m")
    axs[0].set_ylabel("RI (dB µV/m)")
    axs[1].plot(pf["x"], pf["RA"], color=LARANJA, lw=2, label="RA (chuva)")
    axs[1].axhline(r["lim_ra"], color=VERM, ls=":", label=f"Limite {r['lim_ra']:.0f} dB(A)")
    axs[1].set_ylabel("RA (dB(A))")
    axs[1].set_xlabel("Distância ao eixo da LT (m)")
    for ax in axs:
        ax.legend(fontsize=7, loc="upper right")
        if r.get("semi_faixa"):
            for s in (-r["semi_faixa"], r["semi_faixa"]):
                ax.axvline(s, color=CINZA, ls=":", lw=1)
    axs[0].set_title(f"Perfis lateral de RI e RA a {f(r['h_obs'], 1)} m do solo", fontsize=10)
    return fig


def gerar(caminho, proj, e, r, d, resumo_pontos, codigo="BK-LT-MC-M10", rev="R0"):
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    gr = r["gradientes"]
    R = Rel(proj, "Gradiente Superficial, Rádio-Interferência e Ruído Audível", codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS E CRITÉRIOS ADOTADOS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. RESULTADOS OBTIDOS", "7. CONCLUSÕES", "8. REFERÊNCIAS BIBLIOGRÁFICAS"])

    R.h1("OBJETIVO")
    R.p("Determinar o gradiente de potencial na superfície dos condutores e os níveis de rádio-interferência (RI) e de ruído audível (RA) gerados por efeito corona "
        "pela linha de transmissão" + (" " + proj["nome"] if proj.get("nome") else "") + ", no limite da faixa de servidão e nos pontos de estudo, "
        "com a tensão máxima operativa, e compará-los aos limites de projeto.")
    R.p("perdas por efeito corona (Módulo 11), interferência em linhas e dutos (Módulo 9) e contribuição de linhas vizinhas no RI/RA "
        "(PENDENTE: dados de condutor das vizinhas não cadastrados).", "Escopo excluído:")

    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["Diretrizes de projeto básico", "Item 6.10: RI e RA no limite da faixa com a máxima tensão operativa", "—", "—"],
        ["Kiessling et al.", "Overhead Power Lines – Planning, Design, Construction, 2.3.3 e 2.3.4", "—", "—"],
        ["Villas et al.", "Transmissão de Energia Elétrica – estudos elétricos, caps. 8 e 9", "—", "—"]], [3.5, 8.0, 1.5, 3.0])

    R.h1("NORMAS E CRITÉRIOS ADOTADOS")
    R.lista(["Diretrizes de projeto básico 6.10 – RI e RA no limite da faixa, com a máxima tensão operativa.",
             "Gradiente máximo usual: ≈ 17 kV eficaz/cm (Kiessling 2.3.3.1); gradiente crítico visual de Peek como verificação de início de corona.",
             f"RI: limite de projeto {f(r['lim_ri'], 1)} dB µV/m" + (" (sinal a proteger − relação S/N)" if e.get("modo_lim_ri", "").startswith("Sinal") else " (valor fixo informado)") +
             "; níveis de 50 a 60 dB são usuais no limite da faixa (Villas 8.3.2.2). Critério S/N: Kiessling Tabela 2.9.",
             f"RA: limite de projeto {f(r['lim_ra'], 1)} dB(A) no limite da faixa (edital da transmissora); referências do Kiessling: 50 dB(A) sem reclamações, "
             "55 dB(A) com reclamações prováveis. NBR 10151 não consta no acervo: NECESSITA VALIDAÇÃO do limite aplicável ao zoneamento."])

    R.h1("METODOLOGIA DE CÁLCULO")
    R.h2("Gradiente superficial")
    R.p("As cargas das fases são obtidas pela matriz de coeficientes de potencial (condutores, guardas aterrados e imagens, com o feixe substituído pelo raio equivalente). "
        "O gradiente máximo no subcondutor inclui o efeito de proximidade do feixe (Kiessling 2.15 a 2.17):")
    R.eq(msub(mi("E"), mi("i")) + mu("=") + mfrac(mu("|") + msub(mi("Q"), mi("i")) + mu("|"), mu("2π") + msub(mi("ε"), mu("0")) + mi("n") + mi("r")) +
         mpar(mu("1+") + msub(mi("k"), mu("2")) + mfrac(mi("r"), mi("s"))) + mu(" ;  ") + msub(mi("k"), mu("2")) + mu("=2") + mpar(mi("n") + mu("−1")) + mu("sen") + mpar(mfrac(mu("π"), mi("n"))))
    R.simbolos([("Qi", "carga linear da fase i (módulo)", "C/m"), ("n", "número de subcondutores", "—"), ("r", "raio do subcondutor", "m"), ("s", "espaçamento entre subcondutores", "m")])
    R.p("Como conferência, o gradiente médio de circuito simples (eq. 2.22) resulta em: "
        + "; ".join(f"{g['nome']}: {f(g['E'], 2)} kV/cm" for g in gr[:3]) + " (valores calculados pelo método matricial).")
    R.h2("Rádio-interferência (1 MHz)")
    R.eq(msub(mi("N"), mi("i")) + mu("=3,5") + msub(mi("E"), mi("i")) + mu("+12") + msub(mi("r"), mi("i")) + mu("−33") + mu("log") + mpar(mfrac(msub(mi("D"), mi("i")), mu("20"))) + mu("−30"))
    R.eq(mi("N") + mu("=") + mfrac(msub(mi("N"), mu("1")) + mu("+") + msub(mi("N"), mu("2")), mu("2")) + mu("+1,5") + mu("  (se N1−N2 < 3 dB; caso contrário N = N1)"))
    R.p("Método FG (Villas, eq. 8): E = 53,7 + K·(gm − 16,95) + 40·log(d/3,93) + En + 20·KD·log(20/D) + EFW, com K = 3,5, KD = 1,6, "
        "En = −4 dB (n = 1) ou 10·log(n/4) e EFW = 0 (tempo bom) ou 17 dB (chuva). Valor de 50 % de probabilidade, com dispersão de ±5 dB.")
    R.simbolos([("Ei", "gradiente máximo do condutor i", "kV/cm"), ("ri", "raio do subcondutor", "cm"), ("Di", "distância do condutor ao ponto de medição", "m"),
                ("d", "diâmetro do subcondutor", "cm")])
    R.h2("Ruído audível (chuva)")
    R.eq(msub(mi("NPA"), mi("i")) + mu("=−164,6+120") + mu("log") + msub(mi("E"), mi("i")) + mu("+55") + mu("log") + msub(mi("r"), mu("e")) + mu(" ;  ") +
         mi("NPA") + mu("=10") + mu("log") + mu("∑") + msup(mi("e"), mu("0,23(") + msub(mi("NPA"), mi("i")) + mu("−11,4") + mu("log") + msub(mi("D"), mi("i")) + mu("−5,8)")))
    R.simbolos([("re", "raio equivalente: d (n < 3) ou 0,58·n^0,48·d (n ≥ 3), d em mm", "mm"), ("NPAi", "potencial de ruído da fase i", "dB(A)")])
    R.h2("Gradiente crítico visual (Peek)")
    R.eq(msub(mi("E"), mi("v")) + mu("=21,1") + mi("m") + mi("δ") + mpar(mu("1+") + mfrac(mu("0,301"), msqrt(mi("δ") + mi("r")))))
    R.p("NECESSITA VALIDAÇÃO: constantes de Peek conforme formulação usual (m = fator de superfície, δ = densidade relativa do ar); conferir com o Livro 3, cap. 7.")

    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    lin = [["Altura do ponto de medição", f(r["h_obs"], 2), "m", "PREMISSA (1,5 m)"],
           ["Altura mínima do condutor mais baixo", f(r["h_min"], 2), "m", "Altura na estrutura − flecha"],
           ["Altitude / temperatura", f"{f(r['alt'], 0)} / {f(r['temp'], 0)}", "m / °C", "Informado"],
           ["δ (densidade relativa do ar)", f(r["delta"], 3), "—", "Peek"],
           ["Fator de superfície m", f(r["m_rug"], 2), "—", "PREMISSA"],
           ["Cabos guarda no gradiente", "incluídos (aterrados)" if r["incluir_guardas"] else "desprezados", "—", "PREMISSA"],
           ["Condição de RI", "Chuva" if r["chuva"] else "Tempo bom", "—", "Informado"],
           ["Semi-largura da faixa", f(r["semi_faixa"], 1) if r.get("semi_faixa") else "não avaliada", "m", "Módulo 4 / informado"]]
    R.tabela("Parâmetros do cálculo", ["Parâmetro", "Valor", "Unidade", "Origem"], lin, [6.0, 3.5, 2.0, 4.5])
    R.tabela("Circuitos (tensão máxima operativa)", ["Circuito", "Umáx (kV)", "Subcond.", "d (mm)", "s (mm)"],
             [[k, f(c["umax_kv"], 1), c["n"], f(c["d_mm"], 1), f(c["s_mm"], 0)] for k, c in sorted(r["circs"].items())], [2.5, 3.0, 3.0, 3.0, 3.0])
    if resumo_pontos:
        R.tabela("Pontos de estudo", ["Ponto", "Descrição"], [[a, b] for a, b in resumo_pontos], [4.5, 11.5])

    R.h1("RESULTADOS OBTIDOS")
    R.h2("Gradiente superficial")
    R.tabela("Gradiente máximo por fase", ["Fase", "E máx. (kV/cm)", "E visual (kV/cm)", "E / E visual"],
             [[g["nome"], f(g["E"], 2), f(g["E_visual"], 1), f(g["E_rel"], 2)] for g in gr], [4.0, 4.0, 4.0, 4.0])
    R.figura(fig_gradiente(r), "Gradiente superficial por fase e gradiente crítico visual.", larg_cm=13.0)
    R.h2("RI e RA nos pontos de estudo")
    lin = []
    for p in r["pontos"]:
        if "RA" in p:
            lin.append([p["nome"], ", ".join(f(x, 1) for x in p["x_aval"]), f(p["RI_K"], 1), f(p["RI_FG"], 1), f(p["RA"], 1),
                        _st(p["ok_RI"] and p["ok_RA"])])
        else:
            lin.append([p["nome"], "—", "—", "—", "—", "não avaliado"])
    R.tabela("RI e RA", ["Ponto", "Posição x (m)", "RI Kiessling (dB µV/m)", "RI FG (dB µV/m)", "RA (dB(A))", "Situação"], lin, [4.0, 2.6, 2.8, 2.6, 2.2, 2.4])
    R.figura(fig_perfil(r), "Perfis laterais de RI e RA.", larg_cm=14.0)

    R.h1("CONCLUSÕES")
    av = [p for p in r["pontos"] if "RA" in p]
    ok = all(p["ok_RI"] and p["ok_RA"] for p in av) if av else None
    R.lista([f"Gradiente máximo: {f(max(g['E'] for g in gr), 2)} kV/cm ({f(max(g['E_rel'] for g in gr) * 100, 0)} % do gradiente crítico visual).",
             (f"RI no limite da faixa: até {f(max(p['RI_gov'] for p in av), 1)} dB µV/m (limite {f(r['lim_ri'], 1)}); "
              f"RA: até {f(max(p['RA'] for p in av), 1)} dB(A) (limite {f(r['lim_ra'], 1)})." if av else "RI/RA no limite da faixa não avaliados (faixa não definida)."),
             ("Os pontos verificados " + ("ATENDEM" if ok else "NÃO ATENDEM") + " aos limites adotados.") if av else "Defina a faixa (Módulo 4) para concluir."])
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Confirmar o limite de RI com o sinal de rádio local e a relação S/N exigida (edital/ANATEL) e o limite de RA com o zoneamento (NBR 10151).",
             "Se o limite for excedido: aumentar o número de subcondutores/diâmetro, a altura mínima ou o afastamento entre fases.",
             "Considerar medições de RI de fundo antes da construção (Kiessling, 2.3.3.4)."])
    R.p("Grau de confiança: médio. Fórmulas do Kiessling e do Villas reproduzidas contra o exemplo do Kiessling (17,2 kV/cm; RI 39,6/19,6 dB; RA 47,3/29,2 dB(A)); "
        "os métodos empíricos têm dispersão de ±5 dB. Dependem de premissas a altura do ponto de medição, o fator m de Peek e os limites de projeto.",
        "O que falta para eu informar com certeza:")

    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["Kiessling, F. et al. – Overhead Power Lines: Planning, Design, Construction – 2.3.3 (gradiente, RI) e 2.3.4 (RA), eq. 2.12 a 2.29.",
             "Villas, J. E. et al. – Transmissão de Energia Elétrica, caps. 8 (RI, método FG) e 9 (RA).",
             "Diretrizes para a elaboração de projetos básicos para empreendimentos de transmissão – item 6.10.",
             "Cálculos Elétricos de Linhas de Transmissão – cap. 7 (efeito corona).",
             "ABNT NBR 10151 (não consultada)."])
    R.salvar(caminho)
    return caminho
