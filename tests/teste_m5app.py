import os, sys, tempfile, shutil, warnings, glob
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); warnings.simplefilter("ignore")
XLSM = (glob.glob("/mnt/user-data/uploads/LINHA_DE_TRANSMISS*4.xlsm") + glob.glob("/root/.claude/uploads/*/*LINHA_DE_TRANSMISS*4.xlsm"))[0]
tmp = tempfile.mkdtemp(); os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
import db, importar_cabos; db.reset_engine(); importar_cabos.importar(XLSM)
import calc_isolamento as ci
# motor: conferências à mão
assert abs(ci.g0(1.0) - 1080/500*__import__("math").log(1.46)) < 1e-9
assert ci.n_isol_fuga(145, 20, 292) == 10 and ci.n_isol_convencional(138) == 10 and ci.n_isol_convencional(138, True) == 11
assert ci.fsfl_minimo(145) == 3.0 and ci.ufr_tabela(138) == 820.0
d = ci.distribuicao_cadeia(10, 0.1, 83.7); assert abs(sum(d) - 83.7) < 1e-6 and d[0] == max(d)
p = ci.para_raios(dict(um_kv=145, usurto=400, ures_fl=300, zc=400, km=100, ur_cat=108)); assert abs(p["w_kj"] - 50.03) < 0.05
print("motor OK")
from streamlit.testing.v1 import AppTest
at = AppTest.from_file(os.path.join(RAIZ, "app.py"), default_timeout=180)
at.session_state["dados"] = {"cfg": dict(n_circ=1, n_cg=1, cg1='EHS 7/16"'), "geo": dict(h_cg1=30.0),
 "sis": dict(km=80.0, freq=60, un=138.0, umax=145.0), "c1": dict(cond="LINNET 336,4 MCM"),
 "3": dict(modo="Estatísticas", unid="km/h", v_med=62.53, tipo_disp="Coeficiente de variação (%)", s=13.0, n=18, uf="SP", alt=870.0,
           eds_modo="Temperatura média informada", t_media=19.5, t_max=36.5, t_min=3.2, t_coinc=10.8, t_med_max=33.4, est_nome="MIRANTE",
           est_cod="A701", municipio="São Paulo", lat=-23.5, lon=-46.6),
 "4": dict(lm=430.0, lp=350.0, flecha=9.5)}
at.run(); assert not at.exception, [e.value for e in at.exception]
m = [o for o in at.radio(key="modulo_sel").options if "5. " in o][0]
at.radio(key="modulo_sel").set_value(m).run(); assert not at.exception, [e.value for e in at.exception]
print([t.label for t in at.tabs]); print([(x.label, x.value) for x in at.metric])
b = [b for b in at.button if b.label.startswith("Gerar relatório")][0]; b.click().run(); assert not at.exception, [e.value for e in at.exception]
assert at.session_state["_rel_m5"][:2] == b"PK"; print("docx", len(at.session_state["_rel_m5"]))
b = [b for b in at.button if "PDF" in b.label][0]; b.click().run(); assert not at.exception, [e.value for e in at.exception]
assert at.session_state["_pdf_m5"][:4] == b"%PDF"; print("pdf", len(at.session_state["_pdf_m5"]))
open("/home/claude/out/m5.docx", "wb").write(at.session_state["_rel_m5"]); open("/home/claude/out/m5.pdf", "wb").write(at.session_state["_pdf_m5"])
# poliméricos / ancoragem / Kcs informado
for k, v in (("tipo_isol", "Polimérico"), ("tipo_cadeia", "Ancoragem"), ("kcs_modo", "Informado")):
    at.session_state["dados"].setdefault("5", {})[k] = v
at.run(); assert not at.exception, [e.value for e in at.exception]
print("M5 app OK"); shutil.rmtree(tmp)
