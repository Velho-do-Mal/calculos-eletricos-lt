"""Relatório do Módulo 14 – Rejeição de Carga (triagem analítica), padrão BK."""
import datetime as dt

import matplotlib.pyplot as plt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from relatorio_m2 import AZUL, CINZA, LARANJA, VERM, Rel, estilo_ax, f, mi, mu, mfrac, mpar, msqrt, msub, msup


def fig_curvas(r):
    e = r["e"]
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 3.0))
    for ax, key, xl in zip(axs, ("c_carga", "c_scc", "c_q"), ("Carga rejeitada (MVA)", "Scc da fonte (MVA)", "Reator shunt (Mvar)")):
        estilo_ax(ax)
        ax.plot([p["x"] for p in r[key]], [p["pu"] for p in r[key]], color=AZUL, lw=2)
        ax.axhline(e["lim_pu"], color=VERM, ls=":")
        ax.set_xlabel(xl, fontsize=8); ax.tick_params(labelsize=7)
    axs[0].set_ylabel("Sobretensão (p.u. de Un)", fontsize=8)
    fig.suptitle("Sensibilidade da sobretensão após rejeição de carga", fontsize=10)
    fig.tight_layout()
    return fig


def gerar(caminho, proj, e, r, codigo="BK-LT-MC-M14", rev="R0"):
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    b = r["base"]
    R = Rel(proj, "Rejeição de Carga – Pré-dimensionamento de Sobretensão Temporária", codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS E CRITÉRIOS ADOTADOS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. RESULTADOS OBTIDOS", "7. CONCLUSÕES", "8. REFERÊNCIAS BIBLIOGRÁFICAS"])

    R.h1("OBJETIVO")
    R.p("Estimar a sobretensão temporária de frequência industrial no terminal receptor da linha de transmissão" + (" " + proj["nome"] if proj.get("nome") else "") +
        " após a rejeição total de carga, em regime permanente, e dimensionar preliminarmente a compensação reativa shunt necessária.")
    R.p("este relatório é uma TRIAGEM ANALÍTICA. O estudo de transitórios eletromagnéticos (EMT/ATP, modelo de Bergeron, estudo estatístico com ≥ 200 manobras), exigido "
        "pelas Diretrizes de Projeto Básico (3.2.5, 3.2.6 e 8.4) e pelo ONS (Procedimentos de Rede, submódulo 23.3), NÃO é substituído.", "Aviso:")

    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["Diretrizes de projeto básico", "Itens 3.2.5, 3.2.6 e 8.4 – rejeição de carga e religamento (estudos EMT)", "—", "—"],
        ["ONS – Procedimentos de Rede", "Submódulo 23.3 (consultado apenas via Diretrizes)", "—", "—"]], [3.8, 8.0, 1.4, 2.8])

    R.h1("NORMAS E CRITÉRIOS ADOTADOS")
    R.lista([f"Limite de sobretensão temporária: {f(e['lim_pu'], 2)} p.u. de Un ({f(r['lim_kv'], 1)} kV) – PREMISSA; confirmar com o ONS/edital e com a suportabilidade dos equipamentos (Módulo 12).",
             "Modelo de sequência positiva a 60 Hz; sem saturação de transformadores e sem dinâmica de máquinas.",
             "Critérios do ONS para sobretensões de manobra/religamento: NECESSITA VALIDAÇÃO (procedimento não consta integralmente no acervo)."])

    R.h1("METODOLOGIA DE CÁLCULO")
    R.p("Linha de parâmetros distribuídos (quadripolo ABCD): A = D = cosh(γℓ), B = Zo·senh(γℓ), C = senh(γℓ)/Zo, com Zo = √(Z1/Y1) e γ = √(Z1·Y1). "
        "Fonte de Thévenin atrás da origem, Zs = Un²/Scc com ângulo atan(X/R).")
    R.eq(mi("E") + mu("=") + msub(mi("V"), mu("s0")) + mu("+") + msub(mi("Z"), mi("s")) + msub(mi("I"), mu("s0")) + mu(" ;  ") +
         msub(mi("V"), mi("r")) + mu("=") + mfrac(mi("E"), mpar(mi("A") + mu("+") + mi("B") + msub(mi("Y"), mu("sh"))) + mu("+") + msub(mi("Z"), mi("s")) + mpar(mi("C") + mu("+") + mi("D") + msub(mi("Y"), mu("sh")))))
    R.simbolos([("E", "tensão interna da fonte (constante)", "V"), ("Vs0, Is0", "tensão e corrente na origem antes da rejeição", "V, A"), ("Ysh", "admitância do reator shunt (−jQ/Un²)", "S"),
                ("Vr", "tensão no terminal receptor após a rejeição", "V")])
    R.p("Efeito Ferranti com fonte rígida e sem carga: Vr/Vs = 1/cosh(γℓ). A compensação mínima é obtida por bisseção em Q até Vr ≤ limite.")

    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    R.tabela("Parâmetros do cálculo", ["Parâmetro", "Valor", "Unidade", "Origem"], [
        ["Circuito em estudo", e["nome_circ"], "—", "Módulo 1"], ["Comprimento", f(e["comp_km"], 1), "km", "Módulo 1"],
        ["Z1 (sequência positiva)", f"{f(e['z1'][0], 4)} + j{f(e['z1'][1], 4)}", "Ω/km", "Módulo 2"], ["C1", f(e["c1"] * 1e9, 3), "nF/km", "Módulo 2"],
        ["Un / Umáx", f"{f(e['un_kv'], 1)} / {f(e['umax_kv'], 1)}", "kV", "Módulo 1"],
        ["Scc na origem / X/R", f"{f(e['scc_mva'], 0)} MVA / {f(e['xr'], 1)}", "—", "PREMISSA"],
        ["Carga rejeitada / fp", f"{f(e['s_mva'], 1)} MVA / {f(e['fp'], 2)}", "—", "Informado"],
        ["Reator shunt", f(e["q_shunt"], 1), "Mvar", "Informado"], ["Tensão pré-rejeição na carga", f(e["vr0_pu"], 2), "p.u.", "PREMISSA"]], [5.2, 4.5, 2.0, 4.3])

    R.h1("RESULTADOS OBTIDOS")
    R.tabela("Tensão após a rejeição", ["Grandeza", "Com reator informado", "Sem reator"], [
        ["Tensão interna da fonte E (kV)", f(b["E_kv"], 1), f(r["sem_reator"]["E_kv"], 1)],
        ["Tensão no terminal receptor (kV)", f(b["vr_kv"], 1), f(r["sem_reator"]["vr_kv"], 1)],
        ["Tensão (p.u. de Un)", f(r["pu"], 3), f(r["pu_sem_reator"], 3)],
        ["Tensão na origem após rejeição (kV)", f(b["vs_depois_kv"], 1), f(r["sem_reator"]["vs_depois_kv"], 1)],
        ["Fator Ferranti 1/cosh(γℓ)", f(b["ferranti"], 4), "—"]], [6.5, 4.5, 4.5])
    R.figura(fig_curvas(r), "Sensibilidade da sobretensão à carga rejeitada, à potência de curto da fonte e ao reator shunt.", larg_cm=15.5)

    R.h1("CONCLUSÕES")
    qm = r["q_min"]
    R.lista([f"Sobretensão após a rejeição: {f(b['vr_kv'], 1)} kV ({f(r['pu'], 3)} p.u. de Un; {f(r['pu_umax'], 3)} p.u. de Umáx): " + ("ATENDE" if r["ok"] else "NÃO ATENDE") +
             f" ao limite de {f(e['lim_pu'], 2)} p.u.",
             "Reator shunt mínimo para atender o limite: " + ("não necessário." if qm == 0 else "inviável na faixa avaliada." if qm == float("inf") else f"{f(qm, 1)} Mvar.")])
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Executar o estudo ATP estatístico (Diretrizes 3.2.5/3.2.6/8.4) com a Scc real mínima/máxima e os dados de transformadores e compensação.",
             "Confirmar o limite de sobretensão temporária e a duração admissível com o ONS e a suportabilidade dos equipamentos (Módulo 12).",
             "Avaliar a variação da Scc (fonte fraca) e a influência do circuito paralelo."])
    R.p("Grau de confiança: baixo a médio (triagem analítica, regime permanente). Dependem de premissas: Scc e X/R da fonte, tensão pré-rejeição e limite adotado.",
        "O que falta para eu informar com certeza:")

    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["Diretrizes para a elaboração de projetos básicos para empreendimentos de transmissão – itens 3.2.5, 3.2.6 e 8.4.",
             "ONS – Procedimentos de Rede, submódulo 23.3 (não consultado diretamente).",
             "Cálculos Elétricos de Linhas de Transmissão – linhas longas e efeito Ferranti."])
    R.salvar(caminho)
    return caminho
