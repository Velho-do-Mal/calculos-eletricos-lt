import sys; sys.path.insert(0, "/home/claude/bk_lt")
import calc_rejeicao as cr
# LT 138 kV, 80 km: Z1 = 0.19+j0.49, C1 = 9 nF/km; fonte forte -> sobretensão ≈ Ferranti + elevação por Zs
e = dict(z1=[0.19, 0.49], c1=9e-9, comp_km=80.0, un_kv=138.0, umax_kv=145.0, f=60.0, scc_mva=3000.0, xr=10.0, s_mva=0.0, fp=0.95, q_shunt=0.0, vr0_pu=1.0, lim_pu=1.1)
r = cr.calcular(e); assert not r["erros"]
# sem carga e sem reator: pré e pós coincidem
assert abs(r["base"]["vr_kv"] - 138.0) < 1e-6, r["base"]["vr_kv"]
e["s_mva"] = 80.0; r = cr.calcular(e)
print("pu", r["pu"], "q_min", r["q_min"], "ferranti", r["base"]["ferranti"])
assert r["pu"] > 1.0
e["q_shunt"] = 30.0; r2 = cr.calcular(e); assert r2["pu"] < r["pu"]
# fonte fraca eleva mais
e["q_shunt"] = 0; e["scc_mva"] = 300.0; assert cr.calcular(e)["pu"] > r["pu"]
print("rejeicao OK")
