import sys; sys.path.insert(0, "/home/claude/bk_lt")
import calc_religamento as cr
e = dict(z1=[0.19, 0.49], c1=9e-9, comp_km=80.0, un_kv=138.0, umax_kv=145.0, f=60.0, scc_mva=3000.0, xr=10.0, scc_rem_mva=2000.0, p_mw=60.0,
         t_morto_ms=500.0, ang_max=30.0, v_res_pu=1.0, r_pre=0.0, t_ins_ms=8.0, lim_pu=2.0, tipo_falta="Monofásica", nome_circ="C1")
r = cr.calcular(e); assert not r["erros"]
print("sem resistor", r["sem_resistor_pu"], "f0", r["f0_hz"], "rmin", r["r_min"], "ang", r["ang"], "tdeion", r["t_deion_ms"])
assert r["sem_resistor_pu"] > 1.0
e["r_pre"] = 400.0; r2 = cr.calcular(e); assert r2["pico_pu"] < r["sem_resistor_pu"], (r2["pico_pu"], r["sem_resistor_pu"])
e["v_res_pu"] = 0.0; e["r_pre"] = 0; assert cr.calcular(e)["pico_pu"] < r["sem_resistor_pu"]
print("religamento OK")
