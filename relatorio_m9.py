"""
Relatório do Módulo 9 – Interferência eletromagnética em dutos, ferrovias/rodovias e telecomunicações, padrão BK.
"""
import datetime as dt

import matplotlib.pyplot as plt
from docx.enum.text import WD_ALIGN_PARAGRAPH

import calc_interferencia as ci
from relatorio_m2 import AZUL, CINZA, LARANJA, VERM, Rel, estilo_ax, f, mi, mu, mfrac, mpar, msqrt, msub, msup


def _st(ok):
    return "ATENDE" if ok else "NÃO ATENDE"


def fig_barras(r):
    fig, ax = plt.subplots(figsize=(6.0, 3.3))
    estilo_ax(ax)
    nomes = [p["nome"] for p in r["pontos"]]
    ax.bar(nomes, [p["pior"]["total"] / 1000.0 for p in r["pontos"]], color=AZUL, label="Tensão em falta (indutiva + resistiva)")
    ax.plot(nomes, [p["lim_kv"] for p in r["pontos"]], "o--", color=VERM, label="Limite do ponto")
    ax.set_ylabel("kV")
    ax.set_title("Tensão impressa em falta fase-terra × limite", fontsize=10)
    ax.tick_params(axis="x", labelsize=7, rotation=15)
    ax.legend(fontsize=7)
    return fig


def gerar(caminho, proj, e, r, d, resumo_pontos, codigo="BK-LT-MC-M9", rev="R0"):
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    R = Rel(proj, "Interferência Eletromagnética em Dutos, Vias e Telecomunicações", codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. CRITÉRIOS ADOTADOS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. RESULTADOS OBTIDOS", "7. CONCLUSÕES", "8. REFERÊNCIAS BIBLIOGRÁFICAS"])

    R.h1("OBJETIVO")
    R.p("Avaliar as tensões induzidas, por acoplamento indutivo e resistivo, pela linha de transmissão" + (" " + proj["nome"] if proj.get("nome") else "") +
        " em instalações paralelas ou próximas (dutos, rodovias/ferrovias, cabos de telecomunicações e outras linhas), em regime normal e em falta fase-terra, "
        "e verificá-las contra os limites de integridade e segurança.")
    R.p("acoplamento capacitivo (campo elétrico) e modelo distribuído do poliduto (impedância característica, condutância do revestimento, perfil de tensão ao longo da tubulação), "
        "que exigem dados da instalação induzida.", "Escopo excluído:")

    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["Villas et al.", "Transmissão de Energia Elétrica – estudos elétricos, cap. 10 (interferências LT × comunicação e poliduto)", "—", "—"],
        ["Cálculos Elétricos de LTs", "Livro do acervo – impedâncias mútuas de Carson", "—", "—"],
        ["Diretrizes de projeto básico", "Diretrizes para projetos básicos de empreendimentos de transmissão", "—", "—"]], [3.5, 8.0, 1.5, 3.0])

    R.h1("CRITÉRIOS ADOTADOS")
    R.lista(["Poliduto: tensão impressa limitada a 5 kV para evitar perfuração do revestimento (Villas 10.3).",
             "Cabos telefônicos, de controle e sinalização: nível de isolamento da ordem de 1,6 kV (Villas 10.1.2).",
             f"Regime normal: FEM longitudinal limitada a {f(r['lim_reg_v'], 0)} V (PREMISSA – contato em dutos, NACE SP0177; não consta no acervo: NECESSITA VALIDAÇÃO).",
             "Limites por instalação conforme a Tabela de pontos; ferrovias, rodovias e linhas vizinhas usam o limite informado pelo proprietário da instalação."])

    R.h1("METODOLOGIA DE CÁLCULO")
    R.h2("Impedâncias mútuas de Carson")
    R.eq(msub(mi("Z"), mi("mj")) + mu("=0,00159") + mi("f") + mu("+") + mi("j") + mu("0,00477") + mi("f") + mu("log") + mpar(mfrac(msub(mi("D"), mi("e")), msub(mi("d"), mi("mj")))) +
         mu(" [Ω/mi] ;  ") + msub(mi("D"), mi("e")) + mu("=659") + msqrt(mfrac(mi("ρ"), mi("f"))) + mu(" [m]"))
    R.simbolos([("f", "frequência", "Hz"), ("ρ", "resistividade do solo", "Ω·m"), ("dmj", "distância entre o condutor m (fase) e a instalação j", "m"),
                ("De", "profundidade equivalente do retorno pelo solo", "m")])
    R.p("Os valores em Ω/mi são convertidos para Ω/km (1 mi = 1,609 km).")
    R.h2("Acoplamento indutivo")
    R.eq(msub(mi("V"), mu("norm")) + mu("=") + msub(mi("L"), mu("ef")) + mu("|") + mu("∑") + msub(mi("I"), mi("k")) + msub(mi("Z"), mu("m,k")) + mu("|") + mu(" ;  ") +
         msub(mi("V"), mu("ind")) + mu("=") + msub(mi("I"), mi("f")) + mu("|") + msub(mi("Z"), mu("m,k")) + mu("|") + mi("κ") + msub(mi("L"), mu("ef")))
    R.eq(mi("κ") + mu("=") + mu("|1−") + mfrac(msub(mi("Z"), mu("pg")), msub(mi("Z"), mu("gg"))) + mu("|") + mu(" ;  ") + msub(mi("L"), mu("ef")) + mu("=") + mi("L") + mu("cos") + mi("θ"))
    R.simbolos([("Lef", "comprimento de exposição projetado no eixo da instalação", "km"), ("Ik", "corrente fasorial da fase k (regime normal)", "A"),
                ("If", "corrente de falta fase-terra", "A"), ("κ", "fator de blindagem dos cabos guarda (κ = 1 sem guardas ou sem blindagem)", "—"),
                ("Zpg, Zgg", "impedância mútua fase–guarda e própria dos guardas, com retorno pelo solo", "Ω/km"), ("θ", "ângulo entre a LT e a instalação", "°")])
    R.p("A fase em falta é a que produz o maior efeito (varredura das três fases e dos dois lados da LT). Em regime normal usa-se a geometria sem transposição (conservador).")
    R.h2("Acoplamento resistivo")
    R.eq(msub(mi("V"), mu("res")) + mu("=") + mu("mín") + mpar(mfrac(mi("ρ") + msub(mi("I"), mi("g")), mu("2π") + msub(mi("d"), mi("t"))) + mu(" ; ") + msub(mi("I"), mi("g")) + msub(mi("R"), mu("pé"))) +
         mu(" ;  ") + msub(mi("I"), mi("g")) + mu("=") + mi("κ") + msub(mi("I"), mi("f")) + msub(mi("f"), mu("torre")))
    R.simbolos([("Ig", "corrente injetada no solo pela torre sob falta (a parcela auto-neutralizada, que circula pelos guardas, não difunde)", "A"),
                ("dt", "distância da torre ao duto", "m"), ("Rpé", "resistência de aterramento da torre", "Ω")])
    R.p("Tensão à terra do poliduto: (V_ind + V_res) × f_at, com f_at = 0,5 (limite superior para extremos isolados). Para cabos de telecomunicações "
        "adota-se a soma integral. O perfil real de tensão exige o modelo de linha de transmissão do poliduto (Villas 10.3.2): NECESSITA ESTUDO DETALHADO.")

    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    lin = [["Resistividade do solo", f(r["rho"], 0), "Ω·m", "Informado"], ["De", f(r["de"], 0), "m", "Carson"],
           ["Corrente de falta fase-terra", f(r["i_falta"], 2), "kA", "Informado"],
           ["Cota do duto/cabo", f(r["cota"], 1), "m", "Informado"], ["Blindagem dos guardas", r["kappa_modo"], "—", "PREMISSA"],
           ["Fração da corrente de terra pela torre", f(r["f_torre"], 2), "—", "PREMISSA"], ["Resistência de pé de torre", f(r["r_pe"], 1), "Ω", "PREMISSA"],
           ["Fator de tensão à terra / FEM (poliduto)", f(r["f_aten"], 2), "—", "PREMISSA"],
           ["Altura do condutor mais baixo", f(r["h_min"], 2), "m", "Módulo 8"]]
    R.tabela("Parâmetros do cálculo", ["Parâmetro", "Valor", "Unidade", "Origem"], lin, [6.0, 3.5, 2.0, 4.5])
    R.tabela("Circuitos", ["Circuito", "I normal (A)", "FP", "Situação"],
             [[k, f(c["i_normal"], 0), f(c["fp"], 2), c["status"]] for k, c in sorted(r["circs"].items())], [2.5, 3.5, 3.0, 5.0])
    if resumo_pontos:
        R.tabela("Pontos de estudo", ["Ponto", "Descrição"], [[a, b] for a, b in resumo_pontos], [4.5, 11.5])
    R.p("Premissas e limitações: condutores à altura mínima; distância ao duto constante ao longo do paralelismo; torre mais próxima à mesma distância do duto "
        "(conservador); solo homogêneo; corrente de falta estática; acoplamentos capacitivo e de transferência por transposição não considerados.", "Considerações:")

    R.h1("RESULTADOS OBTIDOS")
    lin = [[p["nome"], f(p["d"], 1), f(p["L_ef"], 2), f(p["v_norm"], 1), _st(p["ok_norm"]), f(p["pior"]["v_ind"], 0), f(p["pior"]["v_res"], 0),
            f(p["pior"]["total"], 0), p["lim_nome"], _st(p["ok_falta"])] for p in r["pontos"]]
    R.tabela("Resultados por ponto", ["Ponto", "d (m)", "Lef (km)", "FEM regime (V)", "Regime", "V ind. falta (V)", "V res. (V)", "V total (V)", "Limite", "Falta"], lin,
             [2.6, 1.2, 1.3, 1.6, 1.8, 1.6, 1.4, 1.6, 2.2, 1.8])
    for p in r["pontos"]:
        R.h2(p["nome"])
        R.tabela(f"Detalhe da falta – {p['nome']}", ["Fase em falta", "d (m)", "|Zm| (Ω/km)", "κ", "V ind. (V)", "Ig (A)", "V res. (V)", "Total (V)"],
                 [[x["fase"], f(x["d"], 1), f(x["zm"], 3), f(x["kappa"], 2), f(x["v_ind"], 0), f(x["i_g"], 0), f(x["v_res"], 0), f(x["total"], 0)] for x in p["fault"]],
                 [2.4, 1.6, 2.2, 1.6, 2.2, 2.0, 2.2, 2.2])
    R.figura(fig_barras(r), "Tensão impressa em falta e limites por ponto.", larg_cm=13.0)

    R.h1("CONCLUSÕES")
    ok = all(p["ok_falta"] and p["ok_norm"] for p in r["pontos"])
    R.lista([f"Maior tensão em falta: {f(max(p['pior']['total'] for p in r['pontos']) / 1000.0, 2)} kV; maior FEM em regime: {f(max(p['v_norm'] for p in r['pontos']), 1)} V.",
             "Todos os pontos " + ("ATENDEM" if ok else "NÃO ATENDEM (ver Seção 6)") + " aos limites adotados, nas premissas conservadoras acima."])
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Para poliduto com resultado crítico, executar o estudo detalhado (modelo de linha, condutância do revestimento, perfil de tensão) com os dados do proprietário.",
             "Confirmar a corrente de falta fase-terra com o estudo de curto-circuito e a resistência de pé de torre com o Módulo 6.",
             "Avaliar o acoplamento capacitivo para dutos aéreos ou trechos não aterrados; considerar mitigação (aterramento do duto, blindagem, transposição) quando necessário."])
    R.p("Grau de confiança: médio-baixo para o valor absoluto (modelo simplificado, conservador); a ordem de grandeza e a tendência são confiáveis. "
        "Dependem de premissas a blindagem dos guardas, a fração de corrente de terra, a resistência de pé de torre, o fator de tensão à terra e o limite em regime.",
        "O que falta para eu informar com certeza:")

    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["Villas et al. – Transmissão de Energia Elétrica, cap. 10 (10.1.2, 10.2, 10.3).",
             "Cálculos Elétricos de Linhas de Transmissão – impedâncias mútuas de Carson.",
             "Carson, J. R. – Wave propagation in overhead wires with ground return. Bell System Technical Journal, 1926.",
             "NACE SP0177 (não consultada)."])
    R.salvar(caminho)
    return caminho
