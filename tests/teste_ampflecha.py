import sys; sys.path.insert(0, "/home/claude/bk_lt")
import calc_ampacidade_flecha as af
# Planilha BK: GROSBEAK 636, vão 150, EDS 10% RTC a 20 °C, Tmax 75 -> flecha EDS 3,2066 m; T.max 4,2674 m
cabo = dict(secao_mm2=374.1, diametro_mm=25.15, massa_kg_m=1.2, rtc_kn=88.0, modulo_gpa=70.0, dilatacao_1e6=19.4, r_cc_20=0.0868)
# sanidade interna: EDS 10 % deve resultar flecha parabólica = γ a²/(8σ)
e = dict(a=150, eds_pct=10, th_eds=20, t_min=5, t_amb=30, t_max=75, t_emerg=90, ta=35, vento=1.0, rad=1000, emis=.5, absor=.5, alt_m=0,
         h_fix=15.0, d_min=8.0, corrente=500, n_sub=1, lim_tmin_pct=33)
r = af.calcular(e, cabo); assert not r["erros"], r
l20 = [x for x in r["linhas"] if x["th"] == 20][0]; l75 = [x for x in r["linhas"] if x["th"] == 75][0]
assert abs(l20["T_rtc"] - 10) < 1e-6 and l75["f_par"] > l20["f_par"]
print("f20", l20["f_par"], "f75", l75["f_par"], "I", r["i_term"], "Tnom", r["t_nom"], "th_lim", r["th_lim"])
print("ampflecha OK")
# Planilha BK (GROSBEAK 636 MCM do catálogo): flecha EDS 3,2066 m e 4,2674 m a 75 °C
import glob, os, tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t.db"
import db, importar_cabos; db.reset_engine(); importar_cabos.importar(glob.glob("/root/.claude/uploads/*/*LINHA_DE_TRANSMISS_O_4.xlsm")[0])
rr = af.calcular(dict(e, eds_pct=10, a=150), db.obter_cabo("GROSBEAK 636 MCM"))
f20 = [x for x in rr["linhas"] if x["th"] == 20][0]["f_par"]; f75 = [x for x in rr["linhas"] if x["th"] == 75][0]["f_par"]
assert abs(f20 - 3.2066) < 1e-3 and abs(f75 - 4.2674) < 1e-3, (f20, f75); print("planilha BK reproduzida")
