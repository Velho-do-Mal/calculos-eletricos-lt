"""
Relatório do Módulo 5 – Coordenação de isolamento (isoladores, distâncias no ar, sobretensões e para-raios), padrão BK.
"""
import datetime as dt
import math

import matplotlib.pyplot as plt
from docx.enum.text import WD_ALIGN_PARAGRAPH

import calc_isolamento as ci
from relatorio_m2 import (AZUL, CINZA, LARANJA, VERDE, VERM, Rel, estilo_ax, f, mi, mu, mfrac, mpar, msqrt, msub, msup)


def _st(ok):
    return "ATENDE" if ok else "NÃO ATENDE"


def fig_cadeia(r):
    iso = r["isol"]
    fig, ax = plt.subplots(figsize=(6.0, 3.3))
    estilo_ax(ax)
    dv = iso["dist_v"]
    ax.bar(range(1, len(dv) + 1), dv, color=AZUL)
    ax.axhline(iso["v_med_unid"], color=VERDE, ls="--", label="Distribuição uniforme")
    ax.set_xlabel("Unidade (1 = lado da linha)")
    ax.set_ylabel("Tensão na unidade (kV rms)")
    ax.set_title("Distribuição de tensão na cadeia (escada capacitiva)", fontsize=10)
    ax.legend(fontsize=8)
    return fig


def fig_silhueta(e, r):
    """Estrutura simplificada e condutores em repouso e deslocados (βmax, vento de frequência fundamental)."""
    fases, bal, iso = e["fases"], r["balanco"], r["isol"]
    fig, ax = plt.subplots(figsize=(5.6, 5.0))
    estilo_ax(ax)
    for a, b in ci.silhueta(fases, e["xf"], e["h_corpo"]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=CINZA, lw=2)
    comp = iso["comp"] if e["tipo_cadeia"] != "Ancoragem" else 0.0
    c = bal["casos"].get("freq")
    for i, (x, y) in enumerate(fases):
        ax.plot(x, y, "s", color=AZUL, ms=5)
        ax.plot([x, x], [y, y - comp], color=AZUL, lw=1.5)
        if c:
            for s in (1, -1):
                p = ci.pos_cadeia(x, y, comp, c["beta_max"], s, e["tipo_cadeia"])
                ax.plot([x, p[0]], [y, p[1]], color=LARANJA, lw=1.2, ls="--")
                ax.plot(p[0], p[1], "o", color=LARANJA, ms=4)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("altura (m)")
    ax.set_title("Cadeias em repouso e com balanço (βmáx, frequência fundamental)", fontsize=10)
    return fig


def gerar(caminho, proj, e, r, d, codigo="BK-LT-MC-ISOLAMENTO", rev="R0"):
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    at, ds, iso, kc, pr = r["atm"], r["dist"], r["isol"], r["kcs"], r["pr"]
    bal = r.get("balanco")
    R = Rel(proj, "Coordenação de Isolamento – Isoladores, Distâncias no Ar e Para-raios", codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS TÉCNICAS ADOTADAS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. DIMENSIONAMENTO E VERIFICAÇÕES", "7. PARA-RAIOS E COORDENAÇÃO",
               "8. RESULTADOS OBTIDOS", "9. CONCLUSÕES", "10. REFERÊNCIAS BIBLIOGRÁFICAS"])

    R.h1("OBJETIVO")
    R.p("Definir o isolamento da linha de transmissão " + (proj.get("nome") or "") + ": número de isoladores por cadeia, distâncias mínimas no ar "
        "(fase-terra e fase-fase) para tensão de frequência fundamental, sobretensões de manobra (frente lenta) e de descarga (frente rápida), "
        "verificação com balanço dos condutores, cargas mecânicas da cadeia e especificação preliminar de para-raios.")
    R.p("estudo de transitórios eletromagnéticos (EMT), desempenho a descargas atmosféricas (taxa de desligamento) e rádio-interferência.",
        "Escopo excluído:")

    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["ABNT NBR 5422:2024", "Projeto de linhas aéreas de transmissão de energia elétrica", "2024", "2024"],
        ["Diretrizes de projeto básico", "Diretrizes para projetos básicos de empreendimentos de transmissão (3.2.13, 4.7, 6.8)", "—", "—"],
        ["Projeto Elétrico de LTs", "Livro do acervo (itens 4.6 e 4.7: número de isoladores e gradiente)", "—", "—"],
        ["Planilha BK", "LINHA DE TRANSMISSÃO 4.xlsm (abas Distância de Segurança e EDS Para-raios)", "—", "—"]], [3.5, 8.0, 1.5, 3.0])

    R.h1("NORMAS TÉCNICAS ADOTADAS")
    R.lista(["NBR 5422:2024, 4.5 a 4.8 – densidade relativa do ar, umidade absoluta e fatores de correção atmosférica.",
             "NBR 5422:2024, 9.1 a 9.6 – projeto do isolamento: fuga, frequência fundamental, frente lenta, frente rápida e balanço dos condutores.",
             "NBR 5422:2024, Anexo C – fatores de gap kg (Tabelas C.1 e C.3) e fator estatístico Kcs (C.3).",
             "NBR 5422:2024, 14.2 – carga nas cadeias: ≤ 40 % da carga de ruptura sem vento e ≤ 60 % com vento/construção/manutenção.",
             "Diretrizes de projeto básico 3.2.13, 4.7 e 6.8 – margens de coordenação, para-raios de ZnO e desempenho (60 Hz, manobra, descargas).",
             "IEC 60815 (poluição), IEC 60099 (para-raios), IEC 61472 / IEEE 516 (distâncias de trabalho): não constam no acervo; valores ligados a elas "
             "são informados pelo usuário ou marcados para validação."])

    R.h1("METODOLOGIA DE CÁLCULO")
    R.h2("Fatores atmosféricos (NBR 5422, 4.5 a 4.8)")
    R.eq(mi("δ") + mu("=") + mfrac(mi("p"), msub(mi("p"), mu("0"))) + mu("·") + mfrac(mu("273+") + msub(mi("t"), mu("0")), mu("273+") + mi("t")) +
         mu(" ;  ") + msub(mi("H"), mi("c")) + mu("=1+0,012") + mpar(mfrac(mi("H"), mi("δ")) + mu("−11")))
    R.simbolos([("δ", "densidade relativa do ar", "—"), ("H", "umidade absoluta", "g/m³"), ("p0, t0", "1013 hPa e 20 °C", "—")])
    R.p("Sem medição local, δ e H são estimadas por altitude e coordenadas (4.5.3 e 4.6.3). Os fatores são kaff = δ (frequência fundamental), "
        "kafl = (δ·Hc)^m2 em tempo seco ou δ^m2 sob chuva, com m2 = 1,25·G0·(G0 − 0,2) e G0 função da distância no ar (processo iterativo), e kafr = δ (frente rápida). "
        "Para frente lenta adota-se o caso que resulta em maior distância.")
    R.h2("Distâncias no ar (9.3 a 9.5)")
    R.eq(msub(mi("d"), mu("ft,ff")) + mu("=1,642") + msup(mu("[") + msup(mi("e"), mfrac(mfrac(msub(mi("U"), mi("s")), msqrt(mu("3"))) + msub(mi("F"), mu("tmo")),
         mu("750") + msub(mi("k"), mu("aff")) + msub(mi("k"), mu("zff")) + msub(mi("k"), mu("gff")))) + mu("−1]"), mu("0,83")))
    R.eq(msub(mi("d"), mu("ft,fl")) + mu("=2,174") + mu("[") + msup(mi("e"), mfrac(msub(mi("K"), mu("cs")) + mfrac(msqrt(mu("2")), msqrt(mu("3"))) + msub(mi("U"), mi("s")) + msub(mi("F"), mu("sfl")),
         mu("1080") + msub(mi("k"), mu("afl")) + msub(mi("k"), mu("zfl")) + msub(mi("k"), mi("g")))) + mu("−1]"))
    R.eq(msub(mi("d"), mu("ft,fr")) + mu("=máx") + mpar(mfrac(msubp := msub(mi("U"), mu("fr")), mu("530") + msub(mi("k"), mu("afr")) + msub(mi("k"), mu("zfr")) + msub(mi("k"), mu("gfr+"))) +
         mu(" ; ") + mfrac(msub(mi("U"), mu("fr")), mu("700") + msub(mi("k"), mu("afr")) + msub(mi("k"), mu("zfr")) + msub(mi("k"), mu("gfr−")))))
    R.simbolos([("Us", "tensão máxima do sistema (eficaz, fase-fase)", "kV"), ("Ftmo", "fator de tensão máxima de operação", "—"),
                ("Fsfl", "fator de sobretensão de manobra (Tabela 14 ou estudo)", "—"), ("Kcs", "fator estatístico (Anexo C.3)", "—"),
                ("kg", "fator de gap (Tabela C.1 / C.3)", "—"), ("Ufr", "tensão suportável de frente rápida (Tabela 15)", "kV crista")])
    R.p("Fase-fase: d_ff,ff pela mesma forma de 9.3.2 com Us e kg da Tabela C.3; d_ff,fl por 9.4.2 com rs·Fsfl (até 4 m) ou pela expressão de U50 % (4 a 10 m); "
        "d_ff,fr = 1,2·Ufr/(530·kafr·kzfr·kgfr+). O fator Kcs é obtido do risco de falha admitido, com modelo gaussiano para sobretensão (CVsfl) e para a rigidez "
        "do gap (CVfl) em n gaps em paralelo.")
    R.h2("Isoladores (9.3.1, 14.2 e livro de Projeto Elétrico)")
    R.eq(msub(mi("N"), mu("fuga")) + mu("=") + mfrac(msub(mi("d"), mu("fe")) + msub(mi("U"), mi("m")), msub(mi("c"), mu("u"))) + mu(" ;  ") +
         msub(mi("N"), mu("arco")) + mu("=") + mfrac(msub(mi("d"), mu("req")), mi("p")))
    R.simbolos([("dfe", "fuga específica adotada", "mm/kV"), ("Um", "tensão máxima fase-fase", "kV"), ("cu", "fuga de uma unidade", "mm"),
                ("dreq", "maior distância fase-terra exigida", "m"), ("p", "passo do isolador", "m")])
    R.p("O número adotado é o maior entre o da fuga e o do arco. Como conferência, o método convencional (Projeto Elétrico de LTs, 4.6.1) usa N = Vn/15 em suspensão e +1 em ancoragem, "
        "e o gradiente GI = (fuga total)/Vmax. A distribuição de tensão na cadeia usa escada capacitiva com capacitância à terra por junção c1 e própria C.")
    R.h2("Balanço dos condutores (8.9 e 9.6)")
    R.p("O ângulo β vem de 8.9 (β = atan[K·q0·d·Lm/(p·Lp)]), com βmax/βmin = β ± 2σβ. Vento de frequência fundamental: TR ≥ 10 anos; frente lenta: TR ≥ 2 anos; frente rápida: sem vento. "
        "Condutor-estrutura com βmax; fase-fase com uma fase em βmax e a outra em βmin no mesmo sentido, no apoio e no meio do vão.")

    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    linhas = [["Tensão nominal / máxima", f"{f(e['un_kv'], 0)} / {f(e['um_kv'], 1)}", "kV", "Módulo 1"],
              ["Altitude", f(e["alt"], 0), "m", "Informado"],
              ["Latitude / longitude", f"{f(e['lat'], 2)} / {f(e['lon'], 2)}", "°", "Informado"],
              ["δ", f(at["delta"], 4), "—", e["modo_delta"]],
              ["H / Hc", f"{f(at['H'], 2)} / {f(at['Hc'], 3)}", "g/m³ · —", "NBR 5422, 4.6 e 4.8"],
              ["Fsfl", f(e["fsfl"], 2), "—", e.get("_fsfl_origem", "Tabela 14")],
              ["rs / α", f"{f(e['rs'], 2)} / {f(e['alfa'], 2)}", "—", "9.4.2 (rs padrão 1,4)"],
              ["kg fase-terra / fase-fase", f"{f(e['kg_ft'], 2)} / {f(e['kg_ff'], 2)}", "—", e.get("_kg_origem", "Tabelas C.1 e C.3")],
              ["CVsfl / CVfl / n gaps / risco", f"{f(e['cv_sfl'] * 100, 1)} % / {f(e['cv_fl'] * 100, 1)} % / {int(e['n_gaps'])} / {e['risco']:.0e}", "—", "PREMISSA (Anexo C.3)"],
              ["Kcs", f(kc["kcs"], 3), "—", ("Calculado" if not e.get("kcs_man") else ("Referência Kiessling 2.4.5.3 (1,05 ≈ risco 0,001)" if abs(e["kcs_man"] - 1.05) < 1e-9 else "Informado"))],
              ["Ufr", f(ds["ufr"], 0), "kV", "Informado" if e.get("ufr") else "Tabela 15"],
              ["Tipo de isolador", e["tipo_isol"], "—", "Informado"],
              ["Fuga específica adotada", f(iso["fuga_esp"], 1), "mm/kV", e.get("_fuga_origem", "Informado")],
              ["Tipo de cadeia", e["tipo_cadeia"], "—", "Informado"]]
    if e["tipo_isol"] != "Polimérico":
        linhas += [["Passo / fuga por unidade", f"{f(e['passo_mm'], 0)} / {f(e['fuga_unid_mm'], 0)}", "mm", "Informado"]]
    R.tabela("Dados de entrada", ["Parâmetro", "Valor", "Unidade", "Origem"], linhas, [5.0, 4.5, 2.5, 4.0])
    R.h2("Dados não informados e premissas")
    R.p("Tabela 6.4 das Diretrizes (risco de falha por manobra) não está legível no acervo: o risco adotado é premissa do usuário.", "DADO NÃO INFORMADO —")
    R.p("valores de fuga de IEC/TS 60815-1 não foram verificados contra a norma; os de IEC 60815 (1986) vêm de especificação da Celesc (E-313.0058).", "NECESSITA VALIDAÇÃO TÉCNICA —")
    R.p("latitude e longitude entram em valor absoluto nas fórmulas de 4.5.3 e 4.6.3; o comprimento de ferragens não foi somado à distância de arco.", "PREMISSA —")
    R.p("o modelo de Kcs (Anexo C.3) foi reconstituído em forma analítica; conferir com a Figura C.1 da norma.", "NECESSITA VALIDAÇÃO TÉCNICA —")
    for m in r["avisos"] + r.get("pendencias", []):
        R.p(m, "NECESSITA VALIDAÇÃO TÉCNICA —")

    R.h1("DIMENSIONAMENTO E VERIFICAÇÕES")
    R.h2("Fatores atmosféricos e Kcs")
    R.p(f"δ = {f(at['delta'], 4)}; H = {f(at['H'], 2)} g/m³; Hc = {f(at['Hc'], 3)}; kaff = {f(ds['kaff'], 4)}; kafl = {f(ds['kafl'], 4)}; kafr = {f(ds['kafr'], 4)}; "
        f"Kcs = {f(kc['kcs'], 3)}.", "Resultado:")
    R.h2("Distâncias mínimas no ar")
    R.tabela("Distâncias no ar exigidas", ["Solicitação", "Fase-terra (m)", "Fase-fase (m)", "Item"], [
        ["Frequência fundamental", f(ds["ft_ff"], 3), f(ds["ff_ff"], 3), "9.3.2 / 9.3.3"],
        ["Frente lenta (manobra)", f(ds["ft_fl"], 3), f(ds["ff_fl"], 3), "9.4.1 / 9.4.2"],
        ["Frente rápida (descarga)", f(ds["ft_fr"], 3), f(ds["ff_fr"], 3), "9.5"],
        ["Trabalho em linha viva", f(ds["trab"], 3) if ds["trab"] else "não informado", "—", "7.5 (IEC 61472 / IEEE 516)"],
        ["Exigida (máximo)", f(ds["req_ft"], 3), f(ds["req_ff"], 3), "—"]], [5.0, 3.0, 3.0, 4.0])
    R.p(f"frente rápida: polaridade positiva {f(ds['ft_fr_pos'], 3)} m e negativa {f(ds['ft_fr_neg'], 3)} m; vale a maior (9.5).", "Observação:")
    if ds["ft_fr"] > ds["ft_ff"]:
        R.p("a distância de frente rápida supera a de frequência fundamental; a NBR 5422 (9.5.3.3) exige estudo de desempenho a descargas atmosféricas.",
            "NECESSITA VALIDAÇÃO TÉCNICA —")
    R.h2("Cadeia de isoladores")
    linhas = [["Fuga específica adotada", f(iso["fuga_esp"], 1), "mm/kV"], ["Fuga necessária", f(iso["fuga_nec_mm"], 0), "mm"]]
    if iso.get("n_fuga"):
        linhas += [["N pela fuga", str(iso["n_fuga"]), "un."], ["N pela distância de arco", str(iso["n_arco"]), "un."]]
    linhas += [["Cadeia adotada", f"{iso['n']}" + (" (polimérico)" if e["tipo_isol"] == "Polimérico" else " un."), ""],
               ["Distância de arco", f(iso["l_arco"], 3), "m"], ["Fuga total", f(iso["fuga_tot"], 0), "mm"],
               ["Gradiente GI", f(iso["gi"], 2), "cm/kV"]]
    if iso.get("n_conv"):
        linhas.append(["N pelo método convencional (Vn/15)", str(iso["n_conv"]), "un."])
    R.tabela("Cadeia de isoladores", ["Item", "Valor", "Unidade"], linhas, [8.0, 4.0, 3.0])
    R.tabela("Verificações da cadeia", ["Verificação", "Resultado", "Status"], [
        ["Fuga total ≥ necessária", f"{f(iso['fuga_tot'], 0)} ≥ {f(iso['fuga_nec_mm'], 0)} mm", _st(iso["ok_fuga"])],
        ["Distância de arco ≥ exigida", f"{f(iso['l_arco'], 3)} ≥ {f(ds['req_ft'], 3)} m", _st(iso["ok_arco"])]] +
        ([["Carga sem vento ≤ 40 % da RBL", f"{f(iso['mec']['u_sv'], 1)} %", _st(iso["mec"]["ok_sv"])],
          ["Carga com vento ≤ 60 % da RBL", f"{f(iso['mec']['u_cv'], 1)} %", _st(iso["mec"]["ok_cv"])]] if iso.get("mec") else
         [["Cargas mecânicas (14.2)", "carga de ruptura não informada", "PENDENTE"]]), [6.0, 6.0, 3.0])
    if iso.get("dist_v"):
        R.figura(fig_cadeia(r), "Distribuição de tensão ao longo da cadeia",
                 f"Unidade mais solicitada: {f(iso['v_max_unid'], 1)} kV (média {f(iso['v_med_unid'], 1)} kV); eficiência da cadeia {f(iso['efic'], 0)} %. "
                 "Modelo sem capacitância à linha (conservador); PREMISSA c1/C informada.")
    R.h2("Balanço e distâncias com os condutores deslocados")
    if bal:
        linhas = [[f"{k}", f(v["beta"], 1), f(v["sigma"], 2), f(v["beta_max"], 1), f(v["beta_min"], 1)] for k, v in bal["casos"].items()]
        R.tabela("Ângulos de balanço (8.9)", ["Caso de vento", "β (°)", "σβ (°)", "βmax (°)", "βmin (°)"], linhas, [4.0, 2.5, 2.5, 2.5, 2.5])
        linhas = []
        for ln in bal["fases"]:
            lin = [f"Fase {ln['i'] + 1}"]
            for k in ("ff", "fl", "fr"):
                v = ln.get(k)
                lin.append(f"{f(v[0], 2)} / {f(v[1], 2)} {'✓' if v[2] else '✗'}" if v else "—")
            linhas.append(lin)
        R.tabela("Condutor-estrutura: distância no balanço / exigida (m)", ["Fase", "Freq. fundamental", "Frente lenta", "Frente rápida"], linhas, [2.5, 4.2, 4.2, 4.2])
        linhas = [[("Fase " + str(p["par"][0] + 1) + "-" + str(p["par"][1] + 1)), p["onde"], {"ff": "Freq.", "fl": "Manobra", "fr": "Descarga"}[p["caso"]],
                   f(p["d"], 2), f(p["req"], 2), _st(p["ok"])] for p in bal["pares"]]
        R.tabela("Distâncias fase-fase", ["Par", "Local", "Solicitação", "d (m)", "Exigida (m)", "Status"], linhas, [2.5, 3.5, 2.5, 2.0, 2.5, 2.5])
        R.figura(fig_silhueta(e, r), "Estrutura simplificada e cadeias deslocadas",
                 "Silhueta simplificada (fuste e braços); a estrutura real deve ser verificada em modelo 3D (9.6.3).")
    else:
        R.p("faltam vento do Módulo 3, cabo, vãos ou geometria das fases para verificar o balanço.", "PENDENTE —")
    R.p("distâncias entre condutores de linhas diferentes (7.4) e distância de trabalho em linha viva (7.5) não foram calculadas; informe a distância de trabalho para incluí-la.",
        "PENDENTE —")

    R.h1("PARA-RAIOS E COORDENAÇÃO")
    R.h2("Para-raios de ZnO (Diretrizes 4.7)")
    R.p("Para-raios de estação em entradas de linha, transformadores, reatores e bancos de capacitores sem autoproteção, conforme IEC 60099; Ur nunca acima do Ur do estudo.")
    R.tabela("Seleção preliminar do para-raios", ["Item", "Valor", "Unidade", "Base"], [
        ["Uc mínima (Um/√3)", f(pr["uc_min"], 1), "kV", "Tensão de operação contínua"],
        ["Ur pelo critério de Uc (Uc/Ur = " + f(e["pr"].get("uc_ur", 0.8), 2) + ")", f(pr["ur_mcov"], 1), "kV", "PREMISSA"],
        ["TOV fase-terra (ke·Um/√3)", f(pr["tov"], 1), "kV", "ke = " + f(e["pr"].get("ke", 1.4), 2)],
        ["Ur pelo critério de TOV (Ktov = " + f(e["pr"].get("ktov", 1.10), 2) + ")", f(pr["ur_tov"], 1), "kV", "PREMISSA – curva do fabricante"],
        ["Ur mínima / padronizada", f"{f(pr['ur_min'], 1)} / {f(pr['ur_pad'], 0)}", "kV", "múltiplos de 3 kV (PREMISSA)"],
        ["Ur adotada", f(pr["ur_adot"], 0), "kV", "Catálogo / padronizada"]], [6.0, 3.0, 2.0, 5.0])
    linhas = []
    if pr.get("mp_fr") is not None:
        linhas.append(["Frente rápida: NBI/Ures", f"{f(pr['mp_fr'] * 100, 1)} %", f"≥ {f(pr['margem_exigida'] * 100, 0)} %", _st(pr["ok_fr"])])
    if pr.get("mp_fl") is not None:
        linhas.append(["Manobra: NIM/Ures", f"{f(pr['mp_fl'] * 100, 1)} %", f"≥ {f(pr['margem_exigida'] * 100, 0)} %", _st(pr["ok_fl"])])
    if pr.get("w_kj") is not None:
        linhas.append(["Energia de descarga de linha", f"{f(pr['w_kj_kv'], 2)} kJ/kV de Ur", f"≤ {f(e['pr'].get('e_cat', 0), 2)} kJ/kV" if e["pr"].get("e_cat") else "catálogo", "—" if "ok_e" not in pr else _st(pr["ok_e"])])
    if linhas:
        R.tabela("Margens de proteção", ["Verificação", "Valor", "Limite", "Status"], linhas, [6.0, 4.0, 3.0, 2.5])
    else:
        R.p("tensões residuais do catálogo (8/20 µs e 30/60 µs) e níveis de isolamento do equipamento não informados: margens de proteção não calculadas.", "PENDENTE —")
    for m in pr["avisos"]:
        R.p(m, "NECESSITA VALIDAÇÃO TÉCNICA —")
    R.p("seleção por IEC 60099-4/-5 (Ktov, classe de descarga de linha, separação para-raios-equipamento) deve ser validada com o fabricante e o estudo de transitórios.",
        "NECESSITA VALIDAÇÃO TÉCNICA —")
    R.h2("Margens de coordenação (Diretrizes 3.2.13)")
    R.p("Margem de segurança de 5 % sobre o NBI para isolamento em ar autorrecuperante e de 15 % nos terminais de equipamentos; ondas de 1/50 µs (descarga direta) e 0,5/50 µs (indireta).")
    if r["coord"]:
        R.tabela("Sobretensões de descarga", ["Origem", "Uc (kV)", "Uc com margem (kV)", "Margem"], [[a, f(b, 0), f(c, 0), dd] for a, b, c, dd in r["coord"]], [7.0, 2.5, 3.5, 3.0])
    else:
        R.p("corrente de surto (modelo eletrogeométrico) e tensão induzida média não informadas; dependem do Módulo 16.", "PENDENTE —")
    R.h2("Cabo para-raios e blindagem")
    ang = r["blind"]["ang"]
    R.p(f"número de cabos para-raios: {r['blind']['n_cg'] if r['blind']['n_cg'] is not None else '—'}; ângulo de blindagem da geometria: "
        f"{f(ang, 1) + '°' if ang is not None else 'não calculado'}. O edital da TAESA exige ao menos dois cabos para-raios e falha de blindagem < 0,01/100 km/ano; "
        "limite de desligamentos 1/100 km/ano (≥ 345 kV) e 2/100 km/ano (≤ 230 kV).", "Dados:")
    if r.get("eds_pr"):
        R.p(f"tração do cabo para-raios {f(r['eds_pr'][0], 0)} N ({f(r['eds_pr'][1], 2)} % da RBL), pelo método da planilha BK (aba EDS Para-raios).", "Resultado:")
    R.p("taxa de desligamento por falha de blindagem e por backflashover (modelo eletrogeométrico, soma com Módulo 6) não foi calculada.", "PENDENTE —")

    R.h1("RESULTADOS OBTIDOS")
    ver = [["Distância de arco da cadeia", f"{f(iso['l_arco'], 3)} m", f"≥ {f(ds['req_ft'], 3)} m", _st(iso["ok_arco"])],
           ["Fuga total da cadeia", f"{f(iso['fuga_tot'], 0)} mm", f"≥ {f(iso['fuga_nec_mm'], 0)} mm", _st(iso["ok_fuga"])]]
    if bal:
        ok_est = all(v[2] for ln in bal["fases"] for k, v in ln.items() if k in ("ff", "fl", "fr"))
        ok_pp = all(p["ok"] for p in bal["pares"])
        ver += [["Condutor-estrutura com balanço", "ver tabela", "≥ exigida", _st(ok_est)], ["Fase-fase com balanço", "ver tabela", "≥ exigida", _st(ok_pp)]]
    R.tabela("Resumo das verificações", ["Verificação", "Valor", "Limite", "Status"], ver, [5.5, 3.5, 3.5, 2.5])
    R.p(f"{iso['n']} " + ("unidade polimérica" if e["tipo_isol"] == "Polimérico" else "isoladores por cadeia") + f", com distância de arco de {f(iso['l_arco'], 2)} m.", "RESULTADO:")

    R.h1("CONCLUSÕES")
    R.lista([f"Cadeia adotada: {iso['n']} " + ("(polimérico)" if e["tipo_isol"] == "Polimérico" else "isoladores") +
             f"; fuga específica {f(iso['fuga_esp'], 1)} mm/kV; distância de arco {f(iso['l_arco'], 2)} m.",
             f"Distâncias exigidas: fase-terra {f(ds['req_ft'], 2)} m e fase-fase {f(ds['req_ff'], 2)} m.",
             f"Para-raios: Ur adotada {f(pr['ur_adot'], 0)} kV (mínima padronizada {f(pr['ur_pad'], 0)} kV)."])
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Rodar estudo de transitórios (EMT) para Fsfl, risco e energia dos para-raios, substituindo os valores de Tabela 14 e premissas.",
             "Validar a classe de poluição (IEC/TS 60815) e a fuga específica com a transmissora.",
             "Verificar o desempenho a descargas atmosféricas (Módulo 16) quando a distância de frente rápida superar a de 60 Hz.",
             "Conferir o balanço com a estrutura real em modelo 3D."])
    R.p("Grau de confiança: médio. Fórmulas das Seções 4 e 9 transcritas da NBR 5422:2024; o Kcs é modelo reconstituído e deve ser conferido com a Figura C.1; "
        "dependem de premissas o risco admitido, a classe de poluição, os parâmetros de capacitância da cadeia, os dados do catálogo de para-raios, "
        "a silhueta simplificada da estrutura e as distâncias de trabalho (IEC 61472 / IEEE 516), que não constam no acervo.",
        "O que falta para eu informar com certeza:")

    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["ABNT NBR 5422:2024 – Projeto de linhas aéreas de transmissão de energia elétrica.",
             "Diretrizes para a elaboração de projetos básicos para empreendimentos de transmissão (itens 3.2.13, 4.7 e 6.8).",
             "Projeto Elétrico de Linhas de Transmissão – itens 4.6 e 4.7 (acervo do projeto).",
             "IEC 60815 / IEC/TS 60815-1; IEC 60099-4 e -5; IEC 61472; IEEE Std 516 (não consultadas).",
             "Celesc E-313.0058 – distância de fuga específica por nível de poluição.",
             "Kiessling, F. et al. – Overhead Power Lines, 2.4.5.3 (eq. 2.47 e 2.48): Kcs = 1,05 (risco ≈ 0,001) e fase-fase = 1,4·Kcs·U2 %.",
             "Planilha BK – LINHA DE TRANSMISSÃO 4.xlsm."])
    R.salvar(caminho)
    return caminho
