"""
Relatório do Módulo 7 – Dimensionamento elétrico do condutor e do cabo guarda, no padrão BK.
Critérios: corrente nominal, perda joule, queda de tensão, ampacidade (ONS NT Sazonal e IEEE 738-2006), curto-circuito (IEC 60949).
"""
import datetime as dt
import math

import matplotlib.pyplot as plt
import numpy as np
from docx.enum.text import WD_ALIGN_PARAGRAPH

import calc_condutor as cc
from relatorio_m2 import (AZUL, CINZA, LARANJA, VERDE, VERM, Rel, estilo_ax, f, mi, mu, mfrac, mpar, msqrt, msub, msup)


def fig_amp_ta(e, cabo, crit, n):
    """Ampacidade IEEE 738 × temperatura ambiente, com a corrente por subcondutor."""
    fig, ax = plt.subplots(figsize=(6.2, 3.7))
    estilo_ax(ax)
    al = cabo.get("alfa_20c") or 0.004
    tas = np.arange(10, 51, 2)
    for tc, cor, nome in ((e["t_norm"], AZUL, "normal"), (e["t_emerg"], LARANJA, "emergência")):
        ys = [cc.ampacidade_ieee738(cabo["diametro_mm"], cc.r_temp(cabo["r_cc_20"], al, tc), ta, tc, e.get("alt_m", 0.0),
                                    e["emis"], e["absort"], e["vento_ieee"], 90.0, e["rad"])["i"] for ta in tas]
        ax.plot(tas, ys, color=cor, lw=2.2, label=f"Ampacidade {nome} ({tc:g} °C)")
    ax.axhline(crit["i"] / n, color=VERM, ls="--", label=f"Corrente por cabo = {crit['i'] / n:.0f} A")
    ax.set_xlabel("Temperatura ambiente (°C)")
    ax.set_ylabel("Corrente admissível (A)")
    ax.set_title(f"Ampacidade IEEE 738-2006 – {cabo['codigo']}", fontsize=10)
    ax.legend(fontsize=8)
    return fig


def fig_amp_sazonal(ons, i_nom):
    fig, ax = plt.subplots(figsize=(6.2, 3.5))
    estilo_ax(ax)
    rot = [f"{l['epoca']}\n{l['periodo']}" for l in ons["linhas"]]
    x = np.arange(len(rot))
    ax.bar(x - 0.18, [l["normal"]["i"] for l in ons["linhas"]], 0.36, color=AZUL, label="Normal")
    ax.bar(x + 0.18, [l["emergencia"]["i"] for l in ons["linhas"]], 0.36, color=LARANJA, label="Emergência")
    ax.axhline(i_nom, color=VERM, ls="--", label=f"Corrente nominal = {i_nom:.0f} A")
    ax.set_xticks(x)
    ax.set_xticklabels(rot, fontsize=8)
    ax.set_ylabel("Ampacidade (A)")
    ax.set_title("Ampacidade sazonal – NT do ONS", fontsize=10)
    ax.legend(fontsize=8)
    return fig


def gerar(caminho, proj, e, r, cabo, guardas, circ, codigo="BK-LT-MC-CONDUTOR", rev="R0"):
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    n = int(e.get("n_sub", 1))
    k = r["crit"]
    cb = r["cabo"]
    R = Rel(proj, "Dimensionamento Elétrico do Condutor e do Cabo Guarda", codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS TÉCNICAS ADOTADAS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. DIMENSIONAMENTO E VERIFICAÇÕES", "7. QUANTITATIVOS",
               "8. RESULTADOS OBTIDOS", "9. CONCLUSÕES", "10. REFERÊNCIAS BIBLIOGRÁFICAS"])

    R.h1("OBJETIVO")
    R.p("Verificar, do ponto de vista elétrico, o condutor de fase e o cabo guarda da linha de transmissão " + (proj.get("nome") or "") +
        ": corrente nominal, perdas joule, queda de tensão, ampacidade em regime normal e de emergência e capacidade de curto-circuito do cabo guarda.")
    R.p("dimensionamento mecânico (trações, EDS, flechas, vãos), efeito corona, campos e coordenação de isolamento.", "Escopo excluído:")

    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["ONS", "Nota Técnica – Ampacidade sazonal de linhas de transmissão (NT Sazonal de LTs, 2016)", "—", "2016"],
        ["IEEE Std 738-2006", "Standard for Calculating the Current-Temperature Relationship of Bare Overhead Conductors", "2006", "2006"],
        ["IEC 60949", "Calculation of thermally permissible short-circuit currents", "—", "—"],
        ["Planilha BK", "LINHA DE TRANSMISSÃO 4.xlsm", "—", "—"]], [3.5, 8.0, 1.5, 3.0])
    R.p("revisões e datas dos documentos externos e a especificação técnica da transmissora não foram fornecidas.", "DADO NÃO INFORMADO —")

    R.h1("NORMAS TÉCNICAS ADOTADAS")
    R.lista(["IEEE Std 738-2006 – balanço térmico em regime permanente (eq. 2a, 3a/3b, 4a, 6a a 6c, 7a).",
             "ONS – NT Sazonal de LTs – balanço térmico sazonal (convecção por número de Nusselt, radiação, ganho solar).",
             "IEC 60949 – temperatura final em curto-circuito, método adiabático.",
             "ABNT NBR 5422:2024 – a Seção 21 (correntes admissíveis por período climático) e o Anexo B (temperatura do cabo) tratam do tema; "
             "o texto desses itens ainda não foi conferido neste estudo."])
    R.p("conferir a Seção 21 e o Anexo B da NBR 5422:2024 antes de emitir a revisão final.", "PENDENTE —")

    R.h1("METODOLOGIA DE CÁLCULO")
    R.h2("Critérios básicos")
    R.p("A corrente nominal é obtida da potência ativa; os limites de resistência vêm da perda joule e da queda de tensão admissíveis.")
    R.eq(mi("I") + mu("=") + mfrac(mi("P"), msqrt(mu("3")) + mi("U") + mi("cosφ")) + mu(" ;  ") +
         msub(mi("R"), mu("perda")) + mu("=") + mfrac(mfrac(mi("p"), mu("100")) + mi("P"), mu("3") + mi("L") + msup(mi("I"), mu("2"))))
    R.eq(msqrt(mu("3")) + mi("I") + mi("L") + mpar(mi("R") + mu("cosφ+") + mi("X") + mu("senφ")) + mu("≤") + mi("ΔV") + mi("U"))
    R.simbolos([("P", "potência ativa", "kW"), ("U", "tensão nominal", "kV"), ("L", "comprimento da LT", "km"), ("p", "perda joule máxima", "%"),
                ("R, X", "resistência e reatância da fase", "Ω/km"), ("ΔV", "queda de tensão máxima", "p.u.")])
    R.p("Resistência com a temperatura: R(T) = R20·[1 + α·(T − 20)], com α do catálogo. A resistência da fase com n subcondutores é R_cabo/n.")
    R.p("a queda de tensão considera X' informado; sem a reatância do Módulo 2 o resultado é aproximado.", "Limitações:")
    R.h2("Ampacidade – IEEE 738-2006")
    R.eq(mi("I") + mu("=") + msqrt(mfrac(msub(mi("q"), mi("c")) + mu("+") + msub(mi("q"), mi("r")) + mu("−") + msub(mi("q"), mi("s")),
                                      mi("R") + mu("(") + msub(mi("T"), mi("c")) + mu(")"))))
    R.simbolos([("qc", "perda por convecção (máx. das eq. forçada 3a/3b e natural 6a)", "W/m"), ("qr", "perda por radiação", "W/m"),
                ("qs", "ganho solar = α·Qs·sen θ·D", "W/m"), ("Tc", "temperatura do condutor", "°C")])
    R.h2("Ampacidade – NT Sazonal do ONS")
    R.p("Convecção q_c = π·λf·Nu·(Tc − Ta), com Nu = B2·Re^m2 e λf = 2,42·10⁻² + 7,2·10⁻⁵·Tf; radiação q_r = π·D·ε·σ·(Tc⁴ − Ta⁴); "
        "ganho solar q_s = Rad·α·D (só de dia); Re = D·V·δ/ν, com δ = exp(−1,16·10⁻⁴·altitude) e ν = 1,32·10⁻⁵ + 9,5·10⁻⁸·Tf. "
        "A corrente resulta de I = √[(q_c + q_r − q_s)/R(Tc)]. Não são considerados evaporação, efeito magnético e corona.")
    R.h2("Curto-circuito do cabo guarda")
    R.eq(mi("S") + mu("≥") + mfrac(msub(mi("I"), mu("cc")) + msqrt(mi("t")), mi("k")) + mu(" ;  ") +
         mi("k") + mu("=") + msqrt(mfrac(msub(mi("Q"), mi("c")) + mpar(mi("β") + mu("+20")), msub(mi("ρ"), mu("20"))) + mu("ln") + mfrac(mi("β") + mu("+") + msub(mi("θ"), mi("f")), mi("β") + mu("+") + msub(mi("θ"), mi("i")))))
    R.p("Para OPGW usa-se a capacidade do fabricante em kA²·s: verifica-se I_cc²·t ≤ capacidade.")

    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    R.tabela("Dados de entrada", ["Parâmetro", "Valor", "Unidade", "Origem"], [
        ["Potência ativa P", f(e["p_kw"], 0), "kW", "Módulo 1 / informado"], ["Tensão nominal U", f(e["u_kv"], 1), "kV", "Módulo 1"],
        ["Fator de potência", f(e["cosphi"], 2), "—", "Módulo 1"], ["Comprimento L", f(e["comp_km"], 1), "km", "Módulo 1"],
        ["Perda máxima / queda de tensão máxima", f"{f(e['perda_pct'], 1)} / {f(e['dv_pct'], 1)}", "%", "PREMISSA (planilha BK)"],
        ["Subcondutores por fase", str(n), "—", "Módulo 1"], ["Reatância X'", f(e["x_km"], 3), "Ω/km", "PREMISSA"],
        ["Temperatura normal / emergência", f"{f(e['t_norm'], 0)} / {f(e['t_emerg'], 0)}", "°C", "Módulo 3 / critério do projeto"],
        ["Condutor", cabo.get("codigo") or "—", "—", "Catálogo"],
        ["Diâmetro / R20 / α", f"{f(cabo.get('diametro_mm'), 2)} / {f(cabo.get('r_cc_20'), 4)} / {f(cabo.get('alfa_20c'), 5)}", "mm · Ω/km · 1/°C", "Catálogo"],
        ["Altitude", f(e["alt_m"], 0), "m", "Módulo 3"], ["Emissividade / absortividade", f"{f(e['emis'], 2)} / {f(e['absort'], 2)}", "—", "PREMISSA (planilha BK)"],
        ["Radiação solar", f(e["rad"], 0), "W/m²", "PREMISSA"],
        ["Vento ONS / IEEE", f"{f(e['vento_ons'], 2)} / {f(e['vento_ieee'], 2)}", "m/s", "NT ONS / IEEE 738"],
        ["Corrente de curto-circuito / duração", f"{f(e['icc_ka'], 1)} / {f(e['t_falta'], 2)}", "kA · s", "PREMISSA – estudo de curto"],
        ["Parcela da corrente de falta no guarda", f(e["frac_guarda"] * 100, 0), "%", "PREMISSA (conservador)"]], [5.5, 4.0, 2.5, 4.0])
    R.h2("Dados não informados e premissas")
    R.p("potência, perda e queda de tensão máximas, X', emissividade, absortividade, radiação e temperaturas ambientes foram adotados como "
        "ponto de partida (valores da planilha BK) e devem ser confirmados com o estudo de fluxo de potência e com a transmissora.", "PREMISSA —")
    R.p("a corrente de curto-circuito e a parcela que circula pelo cabo guarda dependem do estudo de curto-circuito e do aterramento; "
        "100 % é conservador.", "PREMISSA —")
    R.p("o arquivo-modelo DOCUMENTO_PADRAO_BK.docx não foi fornecido; capa, cabeçalho e rodapé seguem a especificação textual.",
        "NECESSITA VALIDAÇÃO TÉCNICA —")
    for m in r.get("avisos", []):
        R.p(m, "NECESSITA VALIDAÇÃO TÉCNICA —")
    for m in (r.get("ons") or {}).get("avisos", []):
        R.p(m, "NECESSITA VALIDAÇÃO TÉCNICA —")

    R.h1("DIMENSIONAMENTO E VERIFICAÇÕES")
    R.h2("Memória de cálculo – critérios básicos")
    R.p("Calcular a corrente nominal e os limites de resistência do condutor.", "Objetivo:")
    R.p(f"I = {f(e['p_kw'], 0)}/(√3·{f(e['u_kv'], 1)}·{f(e['cosphi'], 2)}) = {f(k['i'], 2)} A.", "Substituição:")
    R.p(f"R_perda(fase) = ({f(e['perda_pct'], 1)}/100)·{f(e['p_kw'] * 1000, 0)}/(3·{f(e['comp_km'], 1)}·{f(k['i'], 2)}²) = {f(k['r_perda_fase'], 4)} Ω/km; "
        f"por cabo (×{n}) = {f(k['r_perda_cabo'], 4)} Ω/km.", "Substituição:")
    sinphi = math.sqrt(max(0.0, 1 - e["cosphi"] ** 2))
    lim = e["dv_pct"] / 100 * e["u_kv"] * 1000 / (math.sqrt(3) * k["i"] * e["comp_km"])
    R.p(f"R·cosφ + X·senφ ≤ {f(e['dv_pct'], 1)}/100·{f(e['u_kv'] * 1000, 0)}/(√3·{f(k['i'], 2)}·{f(e['comp_km'], 1)}) = {f(lim, 4)} Ω/km → "
        f"R_dv(fase) = ({f(lim, 4)} − {f(e['x_km'], 3)}·{f(sinphi, 4)})/{f(e['cosphi'], 2)} = {f(k['r_dv_fase'], 4)} Ω/km; por cabo = {f(k['r_dv_cabo'], 4)} Ω/km.",
        "Substituição:")
    R.p(f"verificação independente: perdas com R_perda = 3·{f(k['r_perda_fase'], 4)}·{f(e['comp_km'], 1)}·{f(k['i'], 2)}² = "
        f"{f(3 * k['r_perda_fase'] * e['comp_km'] * k['i'] ** 2 / 1000, 1)} kW; limite = {f(e['perda_pct'] / 100 * e['p_kw'], 1)} kW.", "Verificação independente:")
    R.h2("Condutor adotado")
    r_op = cb["r_op"]
    R.p(f"R({f(e['t_norm'], 0)} °C) = {f(cabo['r_cc_20'], 4)}·[1 + {f(cabo.get('alfa_20c') or 0.004, 5)}·({f(e['t_norm'], 0)} − 20)] = {f(r_op, 4)} Ω/km.", "Substituição:")
    R.tabela("Verificação do condutor adotado", ["Critério", "Valor do condutor", "Limite", "Status"], [
        ["Perda joule", f"{f(r_op, 4)} Ω/km", f"≤ {f(k['r_perda_cabo'], 4)} Ω/km", "ATENDE" if cb["ok_perda"] else "NÃO ATENDE"],
        ["Queda de tensão", f"{f(r_op, 4)} Ω/km", f"≤ {f(k['r_dv_cabo'], 4)} Ω/km", "ATENDE" if cb["ok_dv"] else "NÃO ATENDE"],
        ["Corrente × ampacidade do catálogo", f"{f(k['i'] / n, 1)} A/cabo", f"≤ {f(cabo.get('ampacidade_a'), 0)} A" if cabo.get("ampacidade_a") else "—",
         "PENDENTE" if cb["ok_i"] is None else ("ATENDE" if cb["ok_i"] else "NÃO ATENDE")]], [4.5, 3.8, 4.2, 3.0])
    if r.get("perdas"):
        R.p(f"Perdas joule na corrente nominal: {f(r['perdas']['mw'], 2)} MW = {f(r['perdas']['pct'], 2)} % de P (fator de catenária {f(e['fator_cat'] * 100, 1)} %).",
            "Resultado:")
    cands = [c for c in r["candidatos"] if c["ok"]]
    if cands:
        R.tabela("Condutores do catálogo que atendem aos critérios 1 a 3 (primeiros 12, por seção crescente)", ["Código", "Tipo", "Seção (mm²)", "R op. (Ω/km)", "Amp. (A)"],
                 [[c["codigo"], c["tipo"] or "—", f(c["secao"], 1), f(c["r_op"], 4), f(c.get("amp_a"), 0)] for c in cands[:12]], [5.5, 2.0, 2.8, 3.0, 2.7],
                 fonte="Catálogo de cabos do projeto; cálculo próprio")
    R.h2("Ampacidade")
    if "ons" in r:
        R.tabela("Ampacidade sazonal – NT do ONS", ["Época", "Período", "Ta (°C)", "I normal (A)", "MVA normal", "I emerg. (A)", "MVA emerg."],
                 [[l["epoca"], l["periodo"], f(l["ta"], 0), f(l["normal"]["i"], 1), f(l["normal"]["mva"], 1), f(l["emergencia"]["i"], 1), f(l["emergencia"]["mva"], 1)]
                  for l in r["ons"]["linhas"]], [2.0, 2.0, 1.8, 2.6, 2.4, 2.6, 2.6], fonte="NT Sazonal de LTs (ONS); cálculo próprio")
        R.figura(fig_amp_sazonal(r["ons"], k["i"] / n), "Ampacidade sazonal por época e período",
                 "A Figura 1 compara a ampacidade de cada época e período com a corrente por cabo; o pior caso é verão/dia.")
    if "ieee" in r:
        i_ = r["ieee"]
        R.tabela("Balanço térmico – IEEE 738-2006", ["Condição", "Tc (°C)", "qc (W/m)", "qr (W/m)", "qs (W/m)", "I (A)"],
                 [["Normal", f(e["t_norm"], 0), f(i_["normal"]["qc"], 2), f(i_["normal"]["qr"], 2), f(i_["normal"]["qs"], 2), f(i_["normal"]["i"], 1)],
                  ["Emergência", f(e["t_emerg"], 0), f(i_["emergencia"]["qc"], 2), f(i_["emergencia"]["qr"], 2), f(i_["emergencia"]["qs"], 2), f(i_["emergencia"]["i"], 1)]],
                 [3.0, 2.2, 2.6, 2.6, 2.6, 2.6], fonte=f"IEEE Std 738-2006; Ta = {f(i_['ta'], 0)} °C; cálculo próprio")
        if r.get("tc_op"):
            R.p(f"Na corrente de {f(k['i'] / n, 1)} A por cabo, a temperatura de equilíbrio do condutor é {f(r['tc_op'], 1)} °C (Ta = {f(i_['ta'], 0)} °C).", "Resultado:")
        R.figura(fig_amp_ta(e, cabo, k, n), "Ampacidade × temperatura ambiente (IEEE 738)",
                 "A Figura 2 mostra a queda da ampacidade com o aumento da temperatura ambiente; a linha tracejada é a corrente por cabo.")
    R.p("a planilha BK superestima a ampacidade IEEE (usa a densidade do ar no lugar da emissividade em qr); este relatório usa as equações da norma.",
        "NECESSITA VALIDAÇÃO TÉCNICA —")
    R.h2("Cabo guarda")
    if not r["guardas"]:
        R.p("cabo guarda não selecionado.", "DADO NÃO INFORMADO —")
    for g in r["guardas"]:
        if g.get("ok") is None:
            R.p(f"{g['codigo']}: sem dados para verificar.", "PENDENTE —")
            continue
        if "capacidade" in g:
            R.p(f"I²t = ({f(e['frac_guarda'] * e['icc_ka'], 2)} kA)²·{f(e['t_falta'], 2)} s = {f(g['i2t'], 2)} kA²·s; capacidade do fabricante = {f(g['capacidade'], 1)} kA²·s; "
                f"margem {f(g['margem'], 2)}× → {'ATENDE' if g['ok'] else 'NÃO ATENDE'}.", f"{g['codigo']} –")
        else:
            R.p(f"S_min = {f(e['frac_guarda'] * e['icc_ka'] * 1000, 0)}·√{f(e['t_falta'], 2)}/{f(g['k'], 1)} = {f(g['s_min'], 1)} mm²; seção do cabo = {f(g['secao'], 1)} mm² "
                f"(margem {f(g['margem'], 2)}×) → {'ATENDE' if g['ok'] else 'NÃO ATENDE'}.", f"{g['codigo']} –")
        for m in g["avisos"]:
            R.p(m, "NECESSITA VALIDAÇÃO TÉCNICA —")

    R.h1("QUANTITATIVOS")
    R.p("Não aplicável a este documento.")

    R.h1("RESULTADOS OBTIDOS")
    linhas = [["Corrente nominal", f(k["i"], 1), "A", "I = P/(√3·U·cosφ)"],
              ["R máx. por perda (por cabo)", f(k["r_perda_cabo"], 4), "Ω/km", "Perda joule"],
              ["R máx. por queda de tensão (por cabo)", f(k["r_dv_cabo"], 4), "Ω/km", "Queda de tensão"],
              ["R do condutor a T normal", f(r_op, 4), "Ω/km", "R20·[1+α(T−20)]"]]
    if "ieee" in r:
        linhas += [["Ampacidade normal (IEEE 738)", f(r["ieee"]["normal"]["i"], 1), "A", "IEEE 738"],
                   ["Ampacidade emergência (IEEE 738)", f(r["ieee"]["emergencia"]["i"], 1), "A", "IEEE 738"]]
    R.tabela("Resumo", ["Grandeza", "Valor", "Unidade", "Base"], linhas, [6.2, 2.5, 2.0, 5.3])
    ver = [["Perda joule", "Ω/km por cabo", f(r_op, 4), f"≤ {f(k['r_perda_cabo'], 4)}", "ATENDE" if cb["ok_perda"] else "NÃO ATENDE"],
           ["Queda de tensão", "Ω/km por cabo", f(r_op, 4), f"≤ {f(k['r_dv_cabo'], 4)}", "ATENDE" if cb["ok_dv"] else "NÃO ATENDE"]]
    if "ieee" in r:
        ok = r["ieee"]["normal"]["i"] >= k["i"] / n
        ver.append(["Ampacidade normal", "A por cabo", f(k["i"] / n, 1), f"≤ {f(r['ieee']['normal']['i'], 1)}", "ATENDE" if ok else "NÃO ATENDE"])
    if "ons" in r:
        pior = min(l["normal"]["i"] for l in r["ons"]["linhas"])
        ver.append(["Ampacidade sazonal (pior caso)", "A por cabo", f(k["i"] / n, 1), f"≤ {f(pior, 1)}", "ATENDE" if pior >= k["i"] / n else "NÃO ATENDE"])
    for g in r["guardas"]:
        if g.get("ok") is not None:
            ver.append([f"Curto-circuito – {g['codigo']}", "I²t (kA²·s)", f(g["i2t"], 1), "≤ capacidade", "ATENDE" if g["ok"] else "NÃO ATENDE"])
    R.tabela("Resumo das verificações", ["Verificação", "Grandeza", "Valor", "Limite", "Status"], ver, [4.6, 3.0, 2.6, 3.4, 2.4])
    R.p("os resultados são calculados com as premissas indicadas e não substituem a validação da transmissora.", "RESULTADO:")

    R.h1("CONCLUSÕES")
    R.lista([f"Corrente nominal {f(k['i'], 1)} A ({f(k['i'] / n, 1)} A por cabo).",
             f"Condutor {cabo.get('codigo')}: R({f(e['t_norm'], 0)} °C) = {f(r_op, 4)} Ω/km.",
             "Perda joule: " + ("atende" if cb["ok_perda"] else "não atende") + "; queda de tensão: " + ("atende" if cb["ok_dv"] else "não atende") + "."])
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Substituir X' pelo valor do Módulo 2 e confirmar os limites de perda e de queda de tensão.",
             "Confirmar a Seção 21 e o Anexo B da NBR 5422:2024 e as temperaturas ambientes sazonais do ONS para a região.",
             "Obter a corrente de curto-circuito e a parcela no cabo guarda do estudo de curto-circuito."])
    R.p("Grau de confiança: médio. Equações do IEEE 738, da NT do ONS e da IEC 60949 reproduzidas e conferidas contra a planilha BK, mas com premissas de "
        "carga, X', clima e curto-circuito ainda a confirmar.", "O que falta para eu informar com certeza:")

    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["IEEE Std 738-2006 – Standard for Calculating the Current-Temperature Relationship of Bare Overhead Conductors.",
             "ONS. Nota Técnica – Ampacidade sazonal de linhas de transmissão (NT Sazonal de LTs), 2016.",
             "IEC 60949 – Calculation of thermally permissible short-circuit currents, taking into account non-adiabatic heating effects.",
             "ABNT NBR 5422:2024 – Projeto de linhas aéreas de transmissão de energia elétrica.",
             "Planilha BK – LINHA DE TRANSMISSÃO 4.xlsm."])
    R.salvar(caminho)
    return caminho
