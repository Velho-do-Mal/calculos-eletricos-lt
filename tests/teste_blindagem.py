import sys; sys.path.insert(0, "/home/claude/bk_lt")
import calc_blindagem as cb
# Whitehead: D = 6,7·I^0,8
assert abs(float(cb.r_atracao(10.0)) - 6.7 * 10 ** 0.8) < 1e-9
# acoplamento do exemplo do Kiessling: 550/(10·0,85) ≈ 65 kA
assert abs(550 / (10 * 0.85) - 64.7) < 0.1
fases = [dict(x=-4.0, y=20.0, req=0.012, circuito=1, fase="A", nome="A"), dict(x=0.0, y=20.0, req=0.012, circuito=1, fase="B", nome="B"), dict(x=4.0, y=20.0, req=0.012, circuito=1, fase="C", nome="C")]
base = dict(fases=fases, guardas=[dict(x=-2.0, y=25.0), dict(x=2.0, y=25.0)], ng=6.0, faixa="I", un_kv=138.0, umax_kv=145.0, cfo_kv=None, r_pe=20.0, z_torre=0.0, ioniza=True, rho=1000.0,
            frac_torre=0.6, b_guarda_m=0.0, h_torre=25.0, meta=2.0, meta_sf=0.01, ang_lim=30.0, r_guarda=0.005)
r = cb.calcular(base); assert not r["erros"], r
print("SF", r["n_sf"], "BF", r["n_bf"], "k", r["k"], "Ic_bf", r["i_c_bf"], "ang", r["ang_max"], "Imax", r["i_max_blind"])
# guardas mais altos/próximos -> menos falha de blindagem
b2 = dict(base, guardas=[dict(x=-2.0, y=30.0), dict(x=2.0, y=30.0)]); assert cb.calcular(b2)["n_sf"] <= r["n_sf"]
# sem guarda -> muito pior
b3 = dict(base, guardas=[]); assert cb.calcular(b3)["total"] > 0
# Ng maior -> proporcional
b4 = dict(base, ng=12.0); assert abs(cb.calcular(b4)["total"] / r["total"] - 2.0) < 1e-6
print("blindagem OK")
