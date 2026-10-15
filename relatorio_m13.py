"""Relatório do Módulo 13 – Ampacidade e Flecha Máxima, padrão BK."""
import datetime as dt

import matplotlib.pyplot as plt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from relatorio_m2 import AZUL, CINZA, LARANJA, VERM, Rel, estilo_ax, f, mi, mu, mfrac, mpar, msqrt, msub, msup


def _st(ok):
    return "ATENDE" if ok else "NÃO ATENDE"


def fig_flecha(r, e):
    cv = r["curva"]
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    estilo_ax(ax)
    ax.plot([p["th"] for p in cv], [p["clear"] for p in cv], color=AZUL, lw=2, label="Distância ao solo")
    ax.axhline(e["d_min"], color=VERM, ls=":", label=f"Mínima {e['d_min']:g} m")
    ax.set_xlabel("Temperatura do condutor (°C)"); ax.set_ylabel("Distância ao solo (m)")
    ax.set_title("Distância ao solo × temperatura do condutor", fontsize=10)
    ax.legend(fontsize=7)
    return fig


def fig_ampac(r):
    ls = [l for l in r["linhas"] if l["I"]]
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    estilo_ax(ax)
    ax.plot([l["th"] for l in ls], [l["I"] for l in ls], "o-", color=LARANJA, lw=2)
    ax.set_xlabel("Temperatura do condutor (°C)"); ax.set_ylabel("Corrente em regime permanente (A)")
    ax.set_title("Ampacidade (IEEE 738) × temperatura do condutor", fontsize=10)
    return fig


def gerar(caminho, proj, e, cabo, r, codigo="BK-LT-MC-M13", rev="R0"):
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    R = Rel(proj, "Ampacidade e Flecha Máxima do Condutor", codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS E CRITÉRIOS ADOTADOS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. RESULTADOS OBTIDOS", "7. CONCLUSÕES", "8. REFERÊNCIAS BIBLIOGRÁFICAS"])

    R.h1("OBJETIVO")
    R.p("Determinar a ampacidade do condutor " + (cabo.get("codigo") or "") + " da linha de transmissão" + (" " + proj["nome"] if proj.get("nome") else "") +
        " em função da temperatura, a flecha por mudança de estado e a distância ao solo, identificando a corrente máxima compatível com a distância mínima de segurança.")
    R.p("verificação mecânica com vento e gelo (Módulos 3 e 5) e fluência do condutor.", "Escopo excluído:")

    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["IEEE Std 738-2006", "Calculating the Current-Temperature Relationship of Bare Overhead Conductors", "—", "—"],
        ["Planilha BK", "Cálculo mecânico do condutor – método da parábola", "—", "—"]], [3.5, 8.0, 1.5, 3.0])

    R.h1("NORMAS E CRITÉRIOS ADOTADOS")
    R.lista(["IEEE Std 738-2006, regime permanente: balanço térmico qc + qr = qs + I²·R(Tc).",
             f"Distância mínima ao solo no meio do vão: {f(e['d_min'], 2)} m (dado de entrada). NBR 5422 não consta no acervo: NECESSITA VALIDAÇÃO.",
             f"Tração a Tmín limitada a {f(e['lim_tmin_pct'], 0)} % da RTC (PREMISSA)."])

    R.h1("METODOLOGIA DE CÁLCULO")
    R.h2("Mudança de estado (parábola)")
    R.eq(msup(mi("σ"), mu("2")) + mu("·[") + msub(mi("σ"), mu("2")) + mu("+") + mfrac(mi("E") + msup(mi("γ"), mu("2")) + msup(mi("a"), mu("2")), mu("24") + msup(msub(mi("σ"), mu("1")), mu("2"))) +
         mu("−") + msub(mi("σ"), mu("1")) + mu("+") + mi("E") + mi("α") + mpar(msub(mi("θ"), mu("2")) + mu("−") + msub(mi("θ"), mu("1"))) + mu("]=") + mfrac(mi("E") + msup(mi("γ"), mu("2")) + msup(mi("a"), mu("2")), mu("24")))
    R.simbolos([("σ", "tensão específica", "N/mm²"), ("γ", "peso específico = m·g/S", "N/m/mm²"), ("a", "vão regulador", "m"), ("E", "módulo de elasticidade final", "N/mm²"),
                ("α", "coeficiente de dilatação linear", "1/°C"), ("θ", "temperatura do condutor", "°C")])
    R.eq(mi("f") + mu("=") + mfrac(mi("γ") + msup(mi("a"), mu("2")), mu("8") + mi("σ")) + mu(" (parábola) ;  ") + mi("f") + mu("=") + mfrac(mi("H"), mi("w")) + mpar(mu("cosh") + mpar(mfrac(mi("w") + mi("a"), mu("2") + mi("H"))) + mu("−1")) + mu(" (catenária)"))
    R.h2("Ampacidade (IEEE 738)")
    R.eq(msub(mi("q"), mi("c")) + mu("+") + msub(mi("q"), mi("r")) + mu("=") + msub(mi("q"), mi("s")) + mu("+") + msup(mi("I"), mu("2")) + mi("R") + mpar(msub(mi("T"), mi("c"))))
    R.p("A distância ao solo é a altura de fixação menos a flecha (catenária). A corrente limitada pela flecha é a ampacidade na temperatura em que a distância atinge o mínimo.")

    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    R.tabela("Condutor", ["Parâmetro", "Valor", "Unidade"], [
        ["Código", cabo.get("codigo") or "—", "—"], ["Seção", f(r["S"], 1), "mm²"], ["Diâmetro", f(r["d"], 2), "mm"], ["Massa linear", f(r["m"], 4), "kg/m"],
        ["Carga de ruptura (RTC)", f(r["rtc"], 1), "kN"], ["Módulo de elasticidade final", f(r["E_gpa"], 1), "GPa"],
        ["Coef. de dilatação", f(r["dil"], 1), "10⁻⁶/°C"], ["Subcondutores por fase", e["n_sub"], "—"]], [6.0, 4.0, 3.0])
    R.tabela("Parâmetros do cálculo", ["Parâmetro", "Valor", "Unidade", "Origem"], [
        ["Vão regulador", f(e["a"], 0), "m", "Informado"], ["EDS", f"{f(e['eds_pct'], 1)} % a {f(e['th_eds'], 0)} °C", "% RTC", "PREMISSA"],
        ["Altura de fixação (condutor mais baixo)", f(e["h_fix"], 2), "m", "Módulo 2"], ["Distância mínima ao solo", f(e["d_min"], 2), "m", "Informado"],
        ["Temp. ambiente / vento / radiação", f"{f(e['ta'], 0)} °C / {f(e['vento'], 2)} m/s / {f(e['rad'], 0)} W/m²", "—", "IEEE 738"],
        ["Emissividade / absortividade", f"{f(e['emis'], 2)} / {f(e['absor'], 2)}", "—", "PREMISSA"],
        ["Corrente de operação", f(e["corrente"], 0), "A", "Módulo 1"]], [6.0, 4.5, 1.8, 3.7])

    R.h1("RESULTADOS OBTIDOS")
    R.tabela("Flecha, tração, distância ao solo e corrente", ["θ (°C)", "Tração (% RTC)", "Flecha parábola (m)", "Flecha catenária (m)", "Dist. ao solo (m)", "I IEEE 738 (A)", "Situação"],
             [[f(l["th"], 0), f(l["T_rtc"], 1), f(l["f_par"], 2), f(l["f_cat"], 2), f(l["clear"], 2), f(l["I"], 0) if l["I"] else "—", _st(l["ok_clear"])] for l in r["linhas"]],
             [1.6, 2.4, 2.6, 2.6, 2.4, 2.4, 2.2])
    R.figura(fig_flecha(r, e), "Distância ao solo em função da temperatura do condutor.", larg_cm=13.0)
    R.figura(fig_ampac(r), "Ampacidade em função da temperatura do condutor.", larg_cm=13.0)

    R.h1("CONCLUSÕES")
    R.lista([f"Ampacidade a {f(e['t_max'], 0)} °C (IEEE 738, {f(e['ta'], 0)} °C, {f(e['vento'], 2)} m/s): {f(r['i_term'], 0)} A.",
             f"Flecha máxima a {f(e['t_max'], 0)} °C: {f(r['pmax']['f_cat'], 2)} m; distância ao solo {f(e['h_fix'] - r['pmax']['f_cat'], 2)} m (mínima {f(e['d_min'], 2)} m).",
             ("Temperatura do condutor na corrente de operação: " + f(r["t_nom"], 1) + " °C.") if r["t_nom"] else "Temperatura na corrente de operação não determinada.",
             ("Corrente máxima compatível com a distância mínima: " + f(r["i_flecha"], 0) + " A (condutor a " + f(r["th_lim"], 1) + " °C).") if r["i_flecha"]
             else "A distância mínima ao solo é mantida em toda a faixa de temperatura avaliada."])
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Confirmar a distância mínima ao solo e as condições climáticas de projeto (NBR 5422) e a temperatura máxima do condutor.",
             "Se a distância não for atendida: reduzir o vão, aumentar a altura ou a tração (EDS) ou limitar a corrente.",
             "Verificar a tração em vento máximo e a fluência nos Módulos 3 e 5."])
    R.p("Grau de confiança: alto para a flecha (reproduz a planilha BK: GROSBEAK, vão 150 m, EDS 10 %: 3,21 m a 20 °C e 4,27 m a 75 °C); médio para a ampacidade (IEEE 738). "
        "Dependem de premissas: EDS, distância mínima ao solo e condições do meio.", "O que falta para eu informar com certeza:")

    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["IEEE Std 738-2006 – Standard for Calculating the Current-Temperature Relationship of Bare Overhead Conductors.",
             "Planilha BK – Cálculo mecânico do condutor (método da parábola).",
             "ABNT NBR 5422 – Projeto de linhas aéreas de transmissão (não consultada)."])
    R.salvar(caminho)
    return caminho
