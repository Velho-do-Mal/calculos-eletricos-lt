"""Relatório do Módulo 15 – Religamento Tripolar (triagem analítica), padrão BK."""
import datetime as dt

import matplotlib.pyplot as plt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from relatorio_m2 import AZUL, CINZA, LARANJA, VERM, Rel, estilo_ax, f, mi, mu, mfrac, mpar, msqrt, msub, msup


def _st(ok):
    return "ATENDE" if ok else "NÃO ATENDE"


def fig_curvas(r):
    e = r["e"]
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 3.0))
    for ax, key, xl in zip(axs, ("c_rpre", "c_res"), ("Resistor de pré-inserção (Ω)", "Tensão residual (%)")):
        estilo_ax(ax)
        ax.plot([p["x"] for p in r[key]], [p["pu"] for p in r[key]], color=AZUL, lw=2)
        ax.axhline(e["lim_pu"], color=VERM, ls=":")
        ax.set_xlabel(xl, fontsize=8); ax.tick_params(labelsize=7)
    axs[0].set_ylabel("Sobretensão (p.u.)", fontsize=8)
    fig.suptitle("Sobretensão de religamento", fontsize=10)
    fig.tight_layout()
    return fig


def gerar(caminho, proj, e, r, codigo="BK-LT-MC-M15", rev="R0"):
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    d = r["det"]
    R = Rel(proj, "Religamento Tripolar – Pré-dimensionamento", codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS E CRITÉRIOS ADOTADOS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. RESULTADOS OBTIDOS", "7. CONCLUSÕES", "8. REFERÊNCIAS BIBLIOGRÁFICAS"])

    R.h1("OBJETIVO")
    R.p("Pré-dimensionar o religamento tripolar da linha de transmissão" + (" " + proj["nome"] if proj.get("nome") else "") +
        ": sobretensão de energização com carga residual, necessidade e valor do resistor de pré-inserção, margem do tempo morto e ângulo através do disjuntor.")
    R.p("este relatório é uma TRIAGEM ANALÍTICA. O estudo estatístico de transitórios eletromagnéticos (EMT/ATP, ≥ 200 manobras, modelo de Bergeron, resistor de pré-inserção "
        "em Ω e tempo de inserção em ms; sequência: falta monofásica, abertura tripolar, +20 ms de teleproteção, ~4 ciclos de extinção, tempo morto de 500 ms, simulação "
        "total ≈ 800 ms), exigido pelas Diretrizes de Projeto Básico (3.2.5, 3.2.6, 3.2.7 e 8.4) e pelo ONS (submódulo 23.3), NÃO é substituído.", "Aviso:")

    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["Diretrizes de projeto básico", "Itens 3.2.5, 3.2.6, 3.2.7 e 8.4 – religamento e rejeição de carga (EMT)", "—", "—"],
        ["ONS – Procedimentos de Rede", "Submódulo 23.3 (consultado apenas via Diretrizes)", "—", "—"]], [3.8, 8.0, 1.4, 2.8])

    R.h1("NORMAS E CRITÉRIOS ADOTADOS")
    R.lista([f"Sobretensão de manobra máxima de {f(e['lim_pu'], 2)} p.u. de √2·Um/√3 (PREMISSA; confirmar com o edital/ONS).",
             f"Tempo morto adotado: {f(e['t_morto_ms'], 0)} ms (Diretrizes: 500 ms).",
             "Tempo de deionização: 10,5 + U/34,5 ciclos (fórmula clássica, NECESSITA VALIDAÇÃO – não consta no acervo).",
             f"Ângulo máximo através do disjuntor: {f(e['ang_max'], 0)}° (PREMISSA)."])

    R.h1("METODOLOGIA DE CÁLCULO")
    R.p("Energização do circuito com tensão residual de polaridade oposta, modelada por um estágio LC (linha em π, capacitância C/2 no terminal remoto aberto):")
    R.eq(mi("ζ") + mu("=") + mfrac(mi("R"), mu("2")) + msqrt(mfrac(mi("C"), mi("L"))) + mu(" ;  ") + mi("κ") + mu("=") + msup(mi("e"), mu("−") + mfrac(mu("π") + mi("ζ"), msqrt(mu("1−") + msup(mi("ζ"), mu("2"))))) +
         mu(" ;  ") + msub(mi("U"), mu("max")) + mu("=") + mi("E") + mu("+") + mpar(mi("E") + mu("−") + msub(mi("V"), mu("0"))) + mi("κ"))
    R.simbolos([("L", "Ls + L da linha", "H"), ("R", "Rs + R da linha + R de pré-inserção", "Ω"), ("C", "capacitância total da linha / 2", "F"), ("V0", "tensão residual (polaridade oposta)", "p.u."),
                ("E", "tensão da fonte", "p.u.")])
    R.p("Com resistor de pré-inserção, calcula-se o 1º estágio (com R_pré durante t_ins) e o 2º estágio (após o curto-circuito do resistor); vale o maior pico. "
        "O resistor mínimo é obtido por bisseção. O ângulo através do disjuntor é δ = asin(P·X_total/Un²).")

    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    R.tabela("Parâmetros do cálculo", ["Parâmetro", "Valor", "Unidade", "Origem"], [
        ["Circuito / comprimento", f"{e['nome_circ']} / {f(e['comp_km'], 1)}", "— / km", "Módulo 1"],
        ["Z1 / C1", f"{f(e['z1'][0], 4)} + j{f(e['z1'][1], 4)} / {f(e['c1'] * 1e9, 3)}", "Ω/km / nF/km", "Módulo 2"],
        ["Un / Umáx", f"{f(e['un_kv'], 1)} / {f(e['umax_kv'], 1)}", "kV", "Módulo 1"],
        ["Scc origem / remoto / X/R", f"{f(e['scc_mva'], 0)} / {f(e['scc_rem_mva'], 0)} / {f(e['xr'], 1)}", "MVA / MVA / —", "PREMISSA"],
        ["Potência transferida", f(e["p_mw"], 1), "MW", "Informado"], ["Tensão residual", f(e["v_res_pu"], 2), "p.u.", "PREMISSA (pior caso)"],
        ["Resistor de pré-inserção / tempo", f"{f(e['r_pre'], 0)} / {f(e['t_ins_ms'], 1)}" if e["r_pre"] else "sem resistor", "Ω / ms", "Informado"],
        ["Tipo de falta", e["tipo_falta"], "—", "Informado"]], [5.2, 4.8, 2.4, 3.6])

    R.h1("RESULTADOS OBTIDOS")
    R.tabela("Grandezas intermediárias", ["Grandeza", "Valor", "Unidade"], [
        ["Xs (fonte) / X da linha / X remoto", f"{f(r['Xs'], 2)} / {f(r['Xl'], 2)} / {f(r['Xr'], 2)}", "Ω"],
        ["L série / C efetiva", f"{f(r['L_mH'], 2)} / {f(r['C_uF'], 3)}", "mH / µF"], ["Frequência natural", f(r["f0_hz"], 0), "Hz"],
        ["ζ do 1º estágio", f(d["zeta"], 3), "—"]], [7.0, 5.0, 2.5])
    R.tabela("Verificações", ["Verificação", "Calculado", "Critério", "Situação"], [
        ["Sobretensão de religamento (p.u.)", f(r["pico_pu"], 2), f"≤ {f(e['lim_pu'], 2)}", _st(r["ok_sobt"])],
        ["Sobretensão sem resistor (p.u.)", f(r["sem_resistor_pu"], 2), "—", "—"],
        ["Tempo morto (ms)", f(e["t_morto_ms"], 0), f"≥ {f(r['t_deion_ms'], 0)}", _st(r["ok_td"])],
        ["Ângulo no disjuntor (°)", f(r["ang"], 1) if r["ang"] is not None else "—", f"≤ {f(e['ang_max'], 0)}", _st(r["ok_ang"])]], [6.5, 3.0, 3.0, 3.0])
    R.figura(fig_curvas(r), "Sensibilidade da sobretensão ao resistor de pré-inserção e à tensão residual.", larg_cm=14.0)

    R.h1("CONCLUSÕES")
    rm = r["r_min"]
    R.lista([f"Sobretensão de religamento: {f(r['pico_pu'], 2)} p.u. (sem resistor: {f(r['sem_resistor_pu'], 2)} p.u.) – " + _st(r["ok_sobt"]) + f" ao limite de {f(e['lim_pu'], 2)} p.u.",
             "Resistor de pré-inserção mínimo: " + ("não necessário." if rm == 0 else "inviável na faixa avaliada." if rm == float("inf") else f"{f(rm, 0)} Ω (indicativo)."),
             f"Tempo morto de {f(e['t_morto_ms'], 0)} ms: " + _st(r["ok_td"]) + f" (deionização estimada {f(r['t_deion_ms'], 0)} ms).",
             "Ângulo através do disjuntor: " + (f"{f(r['ang'], 1)}° – " + _st(r["ok_ang"]) if r["ang"] is not None else "não calculável (P·X > Un²).")])
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Executar o estudo ATP estatístico exigido pelas Diretrizes (≥ 200 manobras, Bergeron, dispersão entre polos, resistor de pré-inserção em Ω e ms).",
             "Verificar a estabilidade durante o tempo morto e o esquema de proteção/teleproteção (+20 ms).",
             "Confirmar o limite de sobretensão de manobra e a tensão residual (com/sem reator shunt) com o ONS e o fabricante do disjuntor."])
    R.p("Grau de confiança: baixo a médio (triagem). Dependem de premissas: Scc e X/R, tensão residual, limite de sobretensão, ângulo máximo e fórmula de deionização.",
        "O que falta para eu informar com certeza:")

    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["Diretrizes para a elaboração de projetos básicos para empreendimentos de transmissão – itens 3.2.5, 3.2.6, 3.2.7 e 8.4.",
             "ONS – Procedimentos de Rede, submódulo 23.3 (não consultado diretamente).",
             "Cálculos Elétricos de Linhas de Transmissão – energização de linhas e sobretensões de manobra."])
    R.salvar(caminho)
    return caminho
