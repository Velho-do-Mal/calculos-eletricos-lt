"""
Orquestra o cálculo do Módulo 2 por circuito: monta as entradas (geometria + catálogo + dados do circuito),
executa o método CELT2 (referência) e o método matricial com acoplamento, e devolve tudo rastreável
(com as etiquetas DADO NÃO INFORMADO / PREMISSA do padrão BK).
"""
import math

import calc_parametros as cp

FATOR_DS = 0.7788       # Ds = 0,7788·r para condutor sólido — usado só quando o RMG não está cadastrado


def _cabo_eletrico(cabo, n=1, a_mm=0.0, usar_rca=True):
    """Propriedades elétricas do cabo (ou feixe) em SI + lista de etiquetas de premissa."""
    notas = []
    d = (cabo.get("diametro_mm") or 0) / 1000
    r = d / 2
    if cabo.get("rmg_mm"):
        ds, base_ds = cabo["rmg_mm"] / 1000, "RMG do catálogo"
    else:
        ds, base_ds = FATOR_DS * r, "PREMISSA — Ds = 0,7788·r (RMG não cadastrado)"
        notas.append(f"DADO NÃO INFORMADO — RMG do cabo {cabo.get('codigo')}: adotado Ds = 0,7788·r = {ds*1000:.2f} mm.")
    rcc, rca = cabo.get("r_cc_20"), cabo.get("r_ca_75")
    if usar_rca and rca and (not rcc or rca >= rcc):
        R, base_r = rca, "R_CA 75 °C do catálogo"
    elif rcc:
        R, base_r = rcc, "R_CC 20 °C do catálogo"
        if usar_rca:
            notas.append(f"PREMISSA — R_CA 75 °C ausente/incoerente para {cabo.get('codigo')}: usado R_CC 20 °C "
                     f"({rcc:g} Ω/km), sem correção de temperatura.")
    else:
        R, base_r = 0.0, "ausente"
        notas.append(f"DADO NÃO INFORMADO — resistência elétrica de {cabo.get('codigo')}.")
    if cabo.get("alerta_importacao"):
        notas.append(f"NECESSITA VALIDAÇÃO TÉCNICA — {cabo.get('codigo')}: {cabo['alerta_importacao']}")
    req, dseq = cp.feixe(r, ds, n, a_mm / 1000)
    return dict(codigo=cabo.get("codigo"), d=d, r=r, ds=ds, R=R / n, req=req, ds_eq=dseq, d_eq=2 * req,
                n=n, a=a_mm / 1000, base_ds=base_ds, base_r=base_r, amp=cabo.get("ampacidade_a"),
                secao=cabo.get("secao_mm2"), notas=notas)


def calcular(geo, circs, guardas_db, comp_km, f=60.0, rho=1000.0, obter_cabo=None):
    """
    geo: saída de montar_geometria; circs: {1: dict, 2: dict} (dados do circuito, ver app.circuito);
    guardas_db: lista de dicts de cabos guarda (catálogo); retorna dict com 'circuitos', 'mutua', 'notas'.
    """
    notas = []
    res = {"circuitos": {}, "notas": notas, "f": f, "rho": rho, "comp_km": comp_km}
    pos = {k["nome"]: k for k in geo["condutores"]}
    fases = {c: {k["fase"]: k for k in geo["condutores"] if k["tipo"] == "fase" and k["circuito"] == c}
             for c in circs}
    gds = [k for k in geo["condutores"] if k["tipo"] == "guarda"]
    ele = {}
    for c, dc in circs.items():
        cab = obter_cabo(dc["cond"]) if dc.get("cond") else {}
        if not cab:
            notas.append(f"DADO NÃO INFORMADO — condutor do circuito {c} não selecionado; cálculo do circuito não executado.")
            continue
        ele[c] = _cabo_eletrico(cab, int(dc["cabos_fase"]), dc.get("esp_sub", 0.0))
        notas += ele[c]["notas"]
    g_ele = []
    for k, cab in zip(gds, guardas_db):
        e = _cabo_eletrico(cab, 1, 0.0, usar_rca=False)
        notas += e["notas"]
        g_ele.append(dict(nome=k["nome"], x=k["x"], h=k["y_med"], r=e["r"], ds=e["ds"], req=e["r"], R=e["R"]))

    # ---- listas para o método matricial
    F, ordem = [], []
    for c in sorted(ele):
        idx = []
        for fase in "ABC":
            k = fases[c][fase]
            e = ele[c]
            idx.append(len(F))
            F.append(dict(nome=k["nome"], circuito=c, fase=fase, x=k["x"], h=k["y_med"],
                          r=e["req"], ds=e["ds_eq"], req=e["req"], R=e["R"]))
        ordem.append(idx)
    if not F:
        return res
    Z, C = cp.matrizes(F, g_ele, f=f, rho=rho)
    # sequências só para os circuitos calculados (F só contém circuitos com cabo)
    Zs, Cs, seqs = cp.sequencias(Z, C, ordem)
    res["Zseq"], res["Cseq"], res["Zfase"], res["Cfase"] = Zs, Cs, Z, C
    for n, c in enumerate(sorted(ele)):
        dc, e = circs[c], ele[c]
        pf = {fase: fases[c][fase] for fase in "ABC"}
        dist = lambda a, b: math.hypot(pf[a]["x"] - pf[b]["x"], pf["A"]["y_med"] * 0 + pf[a]["y_med"] - pf[b]["y_med"])
        Dab, Dbc, Dca = dist("A", "B"), dist("B", "C"), dist("C", "A")
        status = dc.get("status", "Energizado")
        calc = dict(dados=dc, cabo=e, Dab=Dab, Dbc=Dbc, Dca=Dca)
        fp = dc.get("fp", 0.95)
        S_kva = dc["mva"] * 1000
        if status == "Energizado" and S_kva > 0:
            calc["celt2"] = cp.celt2(e["d_eq"], e["ds_eq"], e["R"], Dab, Dbc, Dca, comp_km, f=f,
                                     vs_kv=dc["un"], sc_kva=S_kva, fp=fp)
        else:
            calc["celt2"] = cp.celt2(e["d_eq"], e["ds_eq"], e["R"], Dab, Dbc, Dca, comp_km, f=f)
        sq = seqs[f"c{n + 1}"]
        calc["seq"] = sq
        if status == "Energizado" and S_kva > 0:
            calc["matricial"] = cp.desempenho_pi(sq["Z1"], sq["C1"], comp_km, dc["un"], S_kva, fp, f=f)
        else:
            calc["matricial"] = cp.desempenho_pi(sq["Z1"], sq["C1"], comp_km, dc["un"], 1e-6, 1.0, f=f)
        i_nom = S_kva / (math.sqrt(3) * dc["un"]) if dc["un"] else 0.0
        amp = dc.get("i_lim") or e["amp"]
        calc["i_nom"], calc["amp"] = i_nom, amp
        calc["amp_base"] = "informado no circuito" if dc.get("i_lim") else "catálogo (ampacidade)"
        calc["densidade_A_mm2"] = i_nom / (e["secao"] * e["n"]) if e.get("secao") else None
        if not amp:
            notas.append(f"DADO NÃO INFORMADO — ampacidade do circuito {c}; verificação de corrente PENDENTE.")
        res["circuitos"][c] = calc
    notas[:] = list(dict.fromkeys(notas))
    if "mutua" in seqs:
        res["mutua"] = seqs["mutua"]
    return res
