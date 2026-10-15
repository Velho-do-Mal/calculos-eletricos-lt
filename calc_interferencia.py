"""
Módulo 9 – Interferência eletromagnética de LT sobre dutos, ferrovias/rodovias e telecomunicações – funções puras.

Fonte: Villas et al., 'Transmissão de Energia Elétrica', cap. 10 (acoplamentos resistivo, indutivo e capacitivo; 10.2 e 10.3) e Livro 3
('Cálculos Elétricos de LTs'), impedâncias mútuas de Carson:
    Z_mj = 0,00159·f + j·0,00477·f·log10(De/d_mj)   [Ω/milha],   De = 659·√(ρ/f)  [m]
Critérios do acervo: tensão impressa em poliduto limitada a 5 kV (perfuração do revestimento) e isolamento de cabos telefônicos ≈ 1,6 kV
(Villas 10.1.2 e 10.3).
Modelo implementado (acoplamento indutivo e resistivo; paralelismo com comprimento e ângulo):
  • Regime normal: FEM longitudinal V = L_ef · Σ I_k · z_m(d_k) (fasores; geometria sem transposição = conservador).
  • Falta fase–terra na torre mais próxima: FEM = I_f · z_m(d_k) · κ · L_ef, κ = |1 − z_pg/z_gg| (blindagem dos cabos guarda, Carson; κ = 1 sem blindagem).
  • Acoplamento resistivo: V_res = ρ·I_g/(2π·d_t), limitado a I_g·R_pé; I_g = κ·I_f·(fração pela torre sob falta).
  • Tensão à terra máxima ≈ f_at·FEM (f_at = 0,5: limite superior para extremos isolados; o perfil real exige o modelo de linha de transmissão
    do poliduto – NECESSITA ESTUDO DETALHADO).
NÃO calculado: acoplamento capacitivo; modelo distribuído do poliduto (impedância característica, condutância do revestimento).
"""
import cmath
import math

import calc_campos as cc

MILHA_KM = 1.609344
LIM_POLIDUTO_KV = 5.0
LIM_TELECOM_KV = 1.6


def de_carson(rho, freq):
    """Profundidade equivalente do retorno pelo solo (m): De = 659·√(ρ/f)."""
    return 659.0 * math.sqrt(rho / freq)


def z_mutua_km(d, rho, freq):
    """Impedância mútua de Carson (Ω/km) entre condutores a distância d (m)."""
    d = max(d, 0.05)
    return (0.00159 * freq + 1j * 0.00477 * freq * math.log10(de_carson(rho, freq) / d)) / MILHA_KM


def z_propria_km(r_ohm_km, gmr, rho, freq):
    """Impedância própria com retorno pelo solo (Ω/km): r + 0,00159 f/mi + j·0,00477 f·log10(De/GMR)."""
    return r_ohm_km + (0.00159 * freq + 1j * 0.00477 * freq * math.log10(de_carson(rho, freq) / gmr)) / MILHA_KM


def kappa_blindagem(fase, guardas, rho, freq):
    """κ = 1 − z_pg/z_gg (complexo) para os cabos guarda aterrados em paralelo (média das próprias e mútuas). fase/guardas: dict com x, y."""
    if not guardas:
        return 1.0 + 0j, False
    m = len(guardas)
    z_gg = 0j
    for i, gi in enumerate(guardas):
        for j, gj in enumerate(guardas):
            z_gg += z_propria_km(gi["r_km"], gi["gmr"], rho, freq) if i == j else z_mutua_km(math.hypot(gi["x"] - gj["x"], gi["y"] - gj["y"]), rho, freq)
    z_gg /= m * m
    z_pg = sum(z_mutua_km(math.hypot(fase["x"] - g["x"], fase["y"] - g["y"]), rho, freq) for g in guardas) / m
    return 1.0 - z_pg / z_gg, True


def calcular_estudo(e):
    erros, avisos = [], []
    fases = e["fases"]
    if not fases:
        return dict(erros=["Geometria sem fases: preencha o Módulo 2 / seção transversal."], avisos=[], pontos=[])
    off = (e["h_min"] - min(f["y"] for f in fases)) if e.get("h_min") else 0.0
    fz = [dict(f, y=f["y"] + off) for f in fases]
    gd = [dict(g, y=g["y"] + off) for g in e["guardas"]]
    rho, fr = float(e["rho"]), float(e["freq"])
    # correntes de regime normal por fase
    I = []
    for f_ in fz:
        c = e["circs"].get(str(f_["circuito"]))
        energ = c and c["status"] == "Energizado"
        I.append(cc.corrente_fase(c["i_normal"], f_["fase"], fp=c["fp"]) if energ else 0j)
    if not any(abs(i) > 0 for i in I):
        avisos.append("Nenhum circuito energizado: FEM em regime normal nula.")
    if not gd:
        avisos.append("Sem cabos guarda: κ = 1 (sem blindagem).")
    pts = []
    for p in e["pontos"]:
        L = float(p["comp_km"]) * math.cos(math.radians(float(p["ang_par"])))
        r = dict(nome=p["nome"], tipo=p["tipo"], d=p["dist"], comp_km=p["comp_km"], ang=p["ang_par"], L_ef=L, lim_kv=p["lim_kv"],
                 lim_nome=p["lim_nome"], vizinhas=p.get("vizinhas", []))
        lados = []
        for lado in (1.0, -1.0):
            xd = lado * p["dist"]
            dist = [math.hypot(f_["x"] - xd, f_["y"] - e["cota"]) for f_ in fz]
            zm = [z_mutua_km(d, rho, fr) for d in dist]
            v_norm = abs(sum(i * z for i, z in zip(I, zm))) * L              # V
            fault = []
            for k, f_ in enumerate(fz):
                kap, tem = kappa_blindagem(f_, gd, rho, fr)
                if e["kappa_modo"].startswith("Sem"):
                    kap_u = 1.0
                else:
                    kap_u = abs(kap)
                v_ind = e["i_falta"] * 1000.0 * abs(zm[k]) * kap_u * L
                i_g = kap_u * e["i_falta"] * 1000.0 * e["f_torre"]
                dt_ = max(p["dist_torre"], 0.5)
                v_res = min(rho * i_g / (2 * math.pi * dt_), i_g * e["r_pe"])
                fault.append(dict(fase=f_["nome"], d=dist[k], zm=abs(zm[k]), kappa=abs(kap), tem_guarda=tem, v_ind=v_ind, i_g=i_g, v_res=v_res,
                                  total=(v_ind + v_res) * e["f_aten"] if p["tipo_inst"] != "telecom" else (v_ind + v_res)))
            pior = max(fault, key=lambda x: x["total"])
            lados.append(dict(lado=lado, dist=dist, zm=zm, v_norm=v_norm, fault=fault, pior=pior))
        w = max(lados, key=lambda x: x["pior"]["total"])
        wn = max(lados, key=lambda x: x["v_norm"])
        r.update(v_norm=wn["v_norm"], v_norm_km=wn["v_norm"] / L if L else 0.0, fault=w["fault"], pior=w["pior"], lado_pior=w["lado"],
                 zm_abs=[abs(z) for z in w["zm"]], dist_fase=w["dist"],
                 ok_falta=w["pior"]["total"] <= p["lim_kv"] * 1000.0 + 1e-9, ok_norm=wn["v_norm"] <= e["lim_reg_v"] + 1e-9)
        pts.append(r)
    if any(p["tipo"] != "Duto/telecomunicações" for p in e["pontos"]):
        avisos.append("Tipos diferentes de duto/telecom usam o mesmo modelo; o limite de cada ponto é indicado na tabela.")
    return dict(erros=erros, avisos=avisos, pontos=pts, rho=rho, freq=fr, i_falta=e["i_falta"], cota=e["cota"], kappa_modo=e["kappa_modo"],
                f_torre=e["f_torre"], r_pe=e["r_pe"], f_aten=e["f_aten"], lim_reg_v=e["lim_reg_v"], h_min=e.get("h_min"), de=de_carson(rho, fr),
                fases=fz, guardas=gd, circs=e["circs"])
