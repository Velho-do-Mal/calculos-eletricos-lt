"""
Módulo 12 – Isolamento e tensão máxima operativa: verificação do isolamento adotado – funções puras (sem Streamlit).

Reaproveita o motor do Módulo 5 (calc_isolamento: NBR 5422:2024 seção 9 e Anexo C; Diretrizes 3.2.13, 4.7, 6.8) para as distâncias requeridas
e para a cadeia de isoladores, e verifica o que foi ADOTADO (distâncias no ar fase-terra e fase-fase, cadeia) contra a tensão máxima operativa Um.
Entradas adicionais: sobretensões representativas (temporária e de manobra) e margem de segurança.
Premissas/limitações: série normalizada de Um (IEC 60038 / IEC 60071-1) não consta no acervo – NECESSITA VALIDAÇÃO; Um máximo admissível calculado só para
frequência industrial (9.3.2); frente lenta e frente rápida são verificadas pela relação d adotada / d requerida.
"""
import math

import calc_isolamento as ci

SQ2, SQ3 = math.sqrt(2.0), math.sqrt(3.0)
UM_PADRAO = [7.2, 12, 17.5, 24, 36, 52, 72.5, 123, 145, 170, 245, 300, 362, 420, 550, 800]     # kV (IEC 60038) – NECESSITA VALIDAÇÃO


def um_max_por_distancia(d_adot, delta, kg, ftmo=1.0):
    """Maior Um (kV) cuja distância fase-terra de frequência fundamental (9.3.2) é ≤ d_adot."""
    lo, hi = 1.0, 1500.0
    if ci.d_ft_ff(hi, delta, kg, ftmo) <= d_adot:
        return hi
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if ci.d_ft_ff(mid, delta, kg, ftmo) <= d_adot else (lo, mid)
    return 0.5 * (lo + hi)


def verificar(e, e5, r5):
    """e: um_kv, un_kv, k_tov, k_man, d_ft_adot, d_ff_adot, margem_pct. e5/r5: entrada e resultado do motor calc_isolamento."""
    erros, avisos = [], []
    um, un = float(e["um_kv"]), float(e["un_kv"])
    if um <= 0 or un <= 0:
        return dict(erros=["Informe Un e Um (Módulo 1 → Circuitos)."], avisos=[])
    if r5.get("erros"):
        return dict(erros=list(r5["erros"]), avisos=[])
    d, iso, atm = r5["dist"], r5["isol"], r5["atm"]
    razao = um / un
    um_norm = min([u for u in UM_PADRAO if u >= un * 1.0 - 1e-9], default=None)
    sobre = dict(
        tov_kv=e["k_tov"] * um / SQ3,                         # eficaz fase-terra
        man_kv=e["k_man"] * SQ2 * um / SQ3,                   # crista fase-terra
        op_cr_kv=SQ2 * um / SQ3,
        fsfl=e5["fsfl"], kcs=r5["kcs"]["kcs"])
    marg = e["margem_pct"] / 100.0
    linhas = []

    def lin(nome, req, adot):
        if req is None or not adot:
            return
        m = adot / req - 1.0
        linhas.append(dict(nome=nome, req=float(req), adot=float(adot), margem=float(m * 100.0), ok=bool(m >= marg - 1e-9)))
    lin("Fase-terra – frequência fundamental (9.3.2)", d["ft_ff"], e["d_ft_adot"])
    lin("Fase-terra – frente lenta (9.4.1)", d["ft_fl"], e["d_ft_adot"])
    lin("Fase-terra – frente rápida (9.5)", d["ft_fr"], e["d_ft_adot"])
    lin("Fase-terra – governante (inclui distância de trabalho)", d["req_ft"], e["d_ft_adot"])
    lin("Fase-fase – frequência fundamental (9.3.3)", d["ff_ff"], e["d_ff_adot"])
    lin("Fase-fase – frente lenta (9.4.2)", d["ff_fl"], e["d_ff_adot"])
    lin("Fase-fase – frente rápida (9.5)", d["ff_fr"], e["d_ff_adot"])
    um_adm = um_max_por_distancia(e["d_ft_adot"], atm["delta"], e5["kg_ft"], e5.get("ftmo", 1.0)) if e["d_ft_adot"] else None
    ok_fuga = bool(iso["ok_fuga"])
    gi = iso["gi"]
    if razao > 1.1 + 1e-9:
        avisos.append(f"Um/Un = {razao:.3f}: acima de 1,10 – conferir a tensão máxima operativa informada.")
    if um_norm and abs(um - um_norm) > 1e-6 and not any(abs(um - u) < 1e-6 for u in UM_PADRAO):
        avisos.append(f"Um = {um:g} kV não pertence à série normalizada (IEC 60038): NECESSITA VALIDAÇÃO com o edital/ONS.")
    if um_adm is not None and um_adm < um:
        avisos.append(f"A distância fase-terra adotada só atende a frequência industrial até Um = {um_adm:.0f} kV (< {um:g} kV).")
    ok_dist = all(l["ok"] for l in linhas) if linhas else None
    return dict(erros=erros, avisos=avisos, razao=float(razao), um_norm=um_norm, sobre=sobre, linhas=linhas, um_adm=None if um_adm is None else float(um_adm),
                ok_dist=ok_dist, ok_fuga=ok_fuga, ok_arco=bool(iso.get("ok_arco")), iso=dict(n=iso["n"], fuga_tot=float(iso["fuga_tot"]), fuga_nec=float(iso["fuga_nec_mm"]),
                fuga_esp=float(iso["fuga_esp"]), l_arco=float(iso["l_arco"]), gi=float(gi)), dist=d, atm=atm, e=e,
                ok=bool(ok_dist is not False and ok_fuga and iso.get("ok_arco")))
