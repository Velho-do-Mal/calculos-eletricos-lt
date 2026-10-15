"""AppTest do M8: tela, vizinha paralela, relatório .docx e PDF."""
import os, sys, tempfile, shutil, warnings, glob
sys.path.insert(0, "/home/claude/bk_lt"); warnings.simplefilter("ignore")
XLSM = glob.glob("/root/.claude/uploads/*/*LINHA_DE_TRANSMISS_O_4.xlsm")[0]
tmp = tempfile.mkdtemp(); os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
import db, importar_cabos; db.reset_engine(); importar_cabos.importar(XLSM)
from streamlit.testing.v1 import AppTest
at = AppTest.from_file("/home/claude/bk_lt/app.py", default_timeout=240)
at.session_state["dados"] = {
    "cfg": dict(n_circ=1, n_cg=2, cg1='OPGW 12,4 mm 36FO', cg2='EHS 7/16"', cabos_fase=1),
    "geo": dict(h_cg1=30.0), "sis": dict(km=80.0, freq=60, un=138.0, umax=145.0, mva=60.0),
    "c1": dict(cond="HAWK 477 MCM", fp=0.95, mva=60.0, un=138.0), "3": dict(alt=870.0),
    "lib": {"n": 1}, "lib0": dict(nome="LT 69 kV", tensao=69.0, i_normal=200.0, esp_h=3.0, h_min=12.0),
    "pts": {"n": 2},
    "pt0": dict(nome="Paralelismo A", tipo="Paralelismo com LT/rede", viz_ids=[0], v0_dist_eixos=25.0, cen_i="Emergência"),
    "pt1": dict(nome="Casa", tipo="Edificação/residência", dist_h=20.0, alt_ref=1.5),
    "16": dict()}
at.run(); assert not at.exception, [e.value for e in at.exception]
m = [o for o in at.radio(key="modulo_sel").options if "16. " in o][0]
at.radio(key="modulo_sel").set_value(m).run(); assert not at.exception, [e.value for e in at.exception]
print([t.label for t in at.tabs]); print("avisos:", [w.value[:90] for w in at.warning]); print([(x.label, x.value) for x in at.metric][:6])
b = [b for b in at.button if b.label.startswith("Gerar relatório")][0]; b.click().run(); assert not at.exception, [e.value for e in at.exception]
assert at.session_state["_rel_m16"][:2] == b"PK"; print("docx", len(at.session_state["_rel_m16"]))
b = [b for b in at.button if "PDF" in b.label][0]; b.click().run(); assert not at.exception, [e.value for e in at.exception]
assert at.session_state["_pdf_m16"][:4] == b"%PDF"; print("pdf", len(at.session_state["_pdf_m16"]))
open("/tmp/m16.docx", "wb").write(at.session_state["_rel_m16"]); open("/tmp/m16.pdf", "wb").write(at.session_state["_pdf_m16"])
shutil.rmtree(tmp); print("M16 app OK")
