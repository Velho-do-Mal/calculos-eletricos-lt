"""Valida o motor de corona contra o exemplo do Kiessling (2.3.3.3 a 2.3.4): 420 kV, feixe duplo 562-AL1/49."""
import math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import calc_corona as cr, calc_campos as cc

# Tabela 2.7
assert abs(cr.k1_feixe(4) - 1.12) < 0.01 and abs(cr.k1_feixe(5) - 1.27) < 0.01 and abs(cr.k1_feixe(6) - 1.43) < 0.01 and abs(cr.k1_feixe(8) - 1.76) < 0.01
assert abs(cr.k2_feixe(2) - 2) < 1e-9 and abs(cr.k2_feixe(4) - 4.24) < 0.01
# eq. 2.22: 17,2 kV/cm
E = cr.gradiente_medio_kiessling(420, 2, 1.61, 40.0, 9.45, 15.0)
print("E médio eq. 2.22 =", round(E, 2)); assert abs(E - 17.2) < 0.1
# RI e RA do exemplo, D = 40 m
nf = cr.ri_kiessling_fase(17.2, 1.61, 40); print("RI fase", round(nf, 1)); assert abs(nf - 39.6) < 0.1
assert abs(cr.combina_ri([nf, nf, nf]) - 41.1) < 0.1
assert abs(cr.ri_kiessling_fase(11.5, 1.61, 40) - 19.6) < 0.1
n2 = cr.npa_fase(17.2, 2, 32.2); assert abs(n2 - 66.6) < 0.1, n2
assert abs(cr.npa_fase(11.5, 4, 32.2) - 48.5) < 0.1
# RA total com 3 fases iguais a 40 m (altura do observador ajustada para D=40)
gr = [dict(E=17.2, n=2, d_mm=32.2, x=x, y=0.0) for x in (0, 0, 0)]
ra = cr.ra_ponto(gr, 40.0, 0.0); print("RA", round(ra, 1)); assert abs(ra - 47.3) < 0.1
# estudo completo: 420 kV horizontal 7,5 m, h = 15 m
fases = [dict(nome=f"{f}1", x=x, y=15.0, circuito=1, fase=f, req=0.08025) for x, f in ((-7.5, "A"), (0, "B"), (7.5, "C"))]
e = dict(fases=fases, guardas=[], incluir_guardas=False, circs={"1": dict(umax_kv=420.0, status="Energizado", n=2, d_mm=32.2, s_mm=400.0)},
         h_min=15.0, h_obs=1.5, x_max=60, dx=1.0, semi_faixa=30.0, alt=500, temp=20, m_rug=0.85, chuva=False, lim_ri=55.0, lim_ra=58.0,
         pontos=[dict(nome="Faixa", tipo="Seção livre (vão)", dist_h=0, alt_ref=1.5, vizinhas=[])])
r = cr.calcular_estudo(e); assert not r["erros"], r
for g in r["gradientes"]: print(g["nome"], round(g["E"], 2), "Peek", round(g["E_visual"], 1))
p = r["pontos"][0]; print({k: round(v, 1) for k, v in p.items() if k in ("RI_K", "RI_FG", "RA")})
assert 16.0 < max(g["E"] for g in r["gradientes"]) < 20.0
import json; json.dumps(r, default=str)
print("OK corona")
