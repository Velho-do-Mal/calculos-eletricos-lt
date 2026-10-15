import math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import calc_interferencia as ci
# De: ρ = 100, f = 60  -> 659·√(100/60) = 850,8 m
assert abs(ci.de_carson(100, 60) - 850.8) < 0.5
# Z mútua a 60 Hz, d = 30 m, ρ = 100: (0,0954 + j0,2862·log10(850,8/30))/1,609 Ω/km
z = ci.z_mutua_km(30, 100, 60); ref = (0.0954 + 1j*0.2862*math.log10(850.8/30)) / 1.609344
assert abs(z - ref) < 1e-3, (z, ref)
fases=[dict(nome=f"{f}1", x=x, y=20.0, circuito=1, fase=f) for x, f in ((-4.5, 'A'), (0, 'B'), (4.5, 'C'))]
gd=[dict(x=-3, y=27, r_km=1.2, gmr=0.003), dict(x=3, y=27, r_km=1.2, gmr=0.003)]
k, ok = ci.kappa_blindagem(fases[0], gd, 100, 60); print("kappa", round(abs(k), 3)); assert ok and 0.2 < abs(k) < 1.0
e = dict(fases=fases, guardas=gd, circs={"1": dict(i_normal=300.0, fp=0.95, status="Energizado")}, h_min=15.0, rho=100.0, freq=60.0, i_falta=5.0,
         cota=-1.5, kappa_modo="Com cabos guarda", f_torre=1.0, r_pe=20.0, f_aten=0.5, lim_reg_v=15.0,
         pontos=[dict(nome="Poliduto", tipo="Duto/telecomunicações", tipo_inst="poliduto", dist=40.0, comp_km=3.0, ang_par=0.0, dist_torre=40.0,
                      lim_kv=5.0, lim_nome="Poliduto (5 kV)", vizinhas=[])])
r = ci.calcular_estudo(e); p = r["pontos"][0]
print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in p.items() if k in ("v_norm", "ok_falta", "ok_norm", "L_ef")}, round(p["pior"]["total"], 1), round(p["pior"]["v_ind"], 1), round(p["pior"]["v_res"], 1))
assert p["pior"]["v_ind"] > 0
import json; json.dumps(r, default=str); print("OK interf")
