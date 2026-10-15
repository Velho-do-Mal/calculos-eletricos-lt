"""Relatório do Módulo 12 – Isolamento e Tensão Máxima Operativa, padrão BK."""
import datetime as dt

import matplotlib.pyplot as plt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from relatorio_m2 import AZUL, CINZA, LARANJA, VERM, VERDE, Rel, estilo_ax, f, mi, mu, mfrac, mpar, msqrt, msub, msup


def _st(ok):
    return "ATENDE" if ok else "NÃO ATENDE"


def fig_dist(r):
    ls = r["linhas"]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    estilo_ax(ax)
    y = range(len(ls))
    ax.barh([i + 0.2 for i in y], [l["req"] for l in ls], height=0.38, color=CINZA, label="Requerida")
    ax.barh([i - 0.2 for i in y], [l["adot"] for l in ls], height=0.38, color=[AZUL if l["ok"] else VERM for l in ls], label="Adotada")
    ax.set_yticks(list(y)); ax.set_yticklabels([l["nome"].split(" (")[0] for l in ls], fontsize=6.5)
    ax.set_xlabel("Distância no ar (m)")
    ax.set_title("Distâncias no ar: requeridas × adotadas", fontsize=10)
    ax.legend(fontsize=7)
    return fig


def gerar(caminho, proj, e, e5, r, codigo="BK-LT-MC-M12", rev="R0"):
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    s, i, atm = r["sobre"], r["iso"], r["atm"]
    R = Rel(proj, "Isolamento e Tensão Máxima Operativa", codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS E CRITÉRIOS ADOTADOS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. RESULTADOS OBTIDOS", "7. CONCLUSÕES", "8. REFERÊNCIAS BIBLIOGRÁFICAS"])

    R.h1("OBJETIVO")
    R.p("Verificar se o isolamento adotado para a linha de transmissão" + (" " + proj["nome"] if proj.get("nome") else "") +
        " (distâncias no ar fase-terra e fase-fase e cadeia de isoladores) atende à tensão máxima operativa e às sobretensões representativas, com a margem de segurança de projeto.")
    R.p("estudo estatístico de desempenho a surtos (Módulos 14, 15 e 16) e coordenação de para-raios de linha.", "Escopo excluído:")

    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["ABNT NBR 5422:2024", "Projeto de linhas aéreas de transmissão – seção 9 e Anexo C", "—", "—"],
        ["Diretrizes de projeto básico", "Itens 3.2.13, 4.7 e 6.8", "—", "—"],
        ["Projeto Elétrico de LTs (Livro 2)", "Itens 4.6 e 4.7 – isoladores", "—", "—"]], [3.8, 8.0, 1.4, 2.8])

    R.h1("NORMAS E CRITÉRIOS ADOTADOS")
    R.lista(["NBR 5422:2024 – 9.3.2 e 9.3.3 (frequência fundamental), 9.4.1 e 9.4.2 (frente lenta, Fsfl, Kcs), 9.5 (frente rápida).",
             f"Margem mínima exigida: {f(e['margem_pct'], 0)} % da distância adotada sobre a requerida (PREMISSA).",
             f"Distância de fuga específica mínima: {f(i['fuga_esp'], 1)} mm/kV (maior entre o nível de poluição e o edital, 14 mm/kV – Diretrizes 6.8.2).",
             "Série normalizada de Um (IEC 60038 / IEC 60071-1) não consta no acervo: NECESSITA VALIDAÇÃO."])

    R.h1("METODOLOGIA DE CÁLCULO")
    R.p("Sobretensões representativas a partir da tensão máxima operativa Um:")
    R.eq(msub(mi("U"), mu("TOV")) + mu("=") + msub(mi("k"), mu("TOV")) + mfrac(msub(mi("U"), mi("m")), msqrt(mu("3"))) + mu(" ;  ") +
         msub(mi("U"), mu("man")) + mu("=") + msub(mi("k"), mu("man")) + msqrt(mu("2")) + mfrac(msub(mi("U"), mi("m")), msqrt(mu("3"))))
    R.p("As distâncias requeridas são calculadas pelo método do Módulo 5 (NBR 5422:2024, seção 9) e comparadas às adotadas. Para a frequência fundamental, "
        "determina-se também a maior Um que a distância fase-terra adotada admite (inversão de 9.3.2).")
    R.eq(msub(mi("d"), mu("ft")) + mu("=1,642") + msup(mpar(msup(mi("e"), mi("x")) + mu("−1")), mu("0,83")) + mu(" ;  ") + mi("x") + mu("=") +
         mfrac(msub(mi("U"), mi("m")) + mu("/") + msqrt(mu("3")), mu("750") + msub(mi("k"), mu("a")) + msub(mi("k"), mi("z")) + msub(mi("k"), mi("g"))))
    R.simbolos([("Um", "tensão máxima operativa", "kV"), ("ka", "fator de correção atmosférica (δ)", "—"), ("kz", "fator estatístico (1 − 3σ)", "—"), ("kg", "fator de geometria do gap", "—")])

    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    R.tabela("Parâmetros", ["Parâmetro", "Valor", "Unidade", "Origem"], [
        ["Un / Um", f"{f(e['un_kv'], 1)} / {f(e['um_kv'], 1)}", "kV", "Módulo 1"], ["Um/Un", f(r["razao"], 3), "—", "Calculado"],
        ["Fator de sobretensão temporária", f(e["k_tov"], 2), "p.u.", "PREMISSA"], ["Fator de sobretensão de manobra", f(e["k_man"], 2), "p.u.", "PREMISSA"],
        ["Distância fase-terra adotada", f(e["d_ft_adot"], 2), "m", "Informado"], ["Distância fase-fase adotada", f(e["d_ff_adot"], 2), "m", "Informado"],
        ["δ (densidade relativa do ar)", f(atm["delta"], 3), "—", "Módulo 5"], ["Kcs / Fsfl", f"{f(s['kcs'], 3)} / {f(s['fsfl'], 2)}", "—", "Módulo 5"],
        ["Isoladores na cadeia", i["n"], "—", "Módulo 5"], ["Margem exigida", f(e["margem_pct"], 0), "%", "PREMISSA"]], [6.0, 3.8, 1.8, 4.4])

    R.h1("RESULTADOS OBTIDOS")
    R.tabela("Tensões de referência", ["Grandeza", "Valor", "Unidade"], [
        ["Tensão de operação de crista fase-terra (√2·Um/√3)", f(s["op_cr_kv"], 1), "kV"],
        ["Sobretensão temporária fase-terra (eficaz)", f(s["tov_kv"], 1), "kV"],
        ["Sobretensão de manobra fase-terra (crista)", f(s["man_kv"], 1), "kV"],
        ["Um máximo admitido pela distância fase-terra adotada (freq. fund.)", f(r["um_adm"], 0) if r["um_adm"] else "—", "kV"]], [9.0, 3.0, 2.0])
    R.tabela("Distâncias no ar", ["Verificação", "Requerida (m)", "Adotada (m)", "Margem (%)", "Situação"],
             [[l["nome"], f(l["req"], 2), f(l["adot"], 2), f(l["margem"], 1), _st(l["ok"])] for l in r["linhas"]], [7.0, 2.2, 2.2, 2.0, 2.4])
    R.figura(fig_dist(r), "Distâncias no ar requeridas e adotadas.", larg_cm=14.0)
    R.tabela("Cadeia de isoladores", ["Item", "Valor", "Situação"], [
        ["Número de isoladores", i["n"], "—"], ["Fuga adotada (mm)", f(i["fuga_tot"], 0), "—"],
        ["Fuga requerida (mm)", f(i["fuga_nec"], 0), _st(r["ok_fuga"])], ["Comprimento de arco (m)", f(i["l_arco"], 2), _st(r["ok_arco"])],
        ["Gradiente médio (mm de fuga/kV)", f(i["gi"], 2), "—"]], [6.5, 4.0, 3.0])

    R.h1("CONCLUSÕES")
    R.lista([f"Um/Un = {f(r['razao'], 3)}; TOV = {f(s['tov_kv'], 1)} kV (eficaz); manobra = {f(s['man_kv'], 0)} kV (crista).",
             "Distâncias no ar: " + ("ATENDEM" if r["ok_dist"] else "NÃO ATENDEM" if r["ok_dist"] is False else "não avaliadas") + f" com margem mínima de {f(e['margem_pct'], 0)} %.",
             "Cadeia de isoladores: fuga " + _st(r["ok_fuga"]) + "; comprimento de arco " + _st(r["ok_arco"]) + ".",
             "Conclusão geral: o isolamento adotado " + ("ATENDE" if r["ok"] else "NÃO ATENDE") + " à tensão máxima operativa."])
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Confirmar os fatores de sobretensão com o estudo de transitórios (Módulos 14/15 e ATP).",
             "Confirmar a poluição local (fuga específica) e a série normalizada de Um com o edital/ONS.",
             "Se não atender: aumentar a distância no ar, o número de isoladores ou a distância de fuga."])
    R.p("Grau de confiança: médio-alto (formulação da NBR 5422:2024 do acervo). Dependem de premissas: fatores de sobretensão, margem, distâncias adotadas e critérios do Módulo 5.",
        "O que falta para eu informar com certeza:")

    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["ABNT NBR 5422:2024 – Projeto de linhas aéreas de transmissão de energia elétrica.",
             "Diretrizes para a elaboração de projetos básicos para empreendimentos de transmissão – itens 3.2.13, 4.7 e 6.8.",
             "Projeto Elétrico de Linhas de Transmissão – itens 4.6 e 4.7.",
             "IEC 60038 / IEC 60071-1 (não consultadas)."])
    R.salvar(caminho)
    return caminho
