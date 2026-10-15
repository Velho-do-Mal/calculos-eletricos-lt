import os, sys, tempfile, shutil, warnings
sys.path.insert(0,"/home/claude/bk_lt"); warnings.simplefilter("ignore")
XLSM="/root/.claude/uploads/9d4270f2-2b3e-52a5-b0a9-d0d02b207d6f/682214ad-LINHA_DE_TRANSMISS_O_4.xlsm"
tmp=tempfile.mkdtemp(); os.environ["DATABASE_URL"]=f"sqlite:///{tmp}/t.db"
import db, importar_cabos; db.reset_engine(); importar_cabos.importar(XLSM)
from streamlit.testing.v1 import AppTest
MODS=["📁  1. Dados do Projeto e Sistema","🔌  2. Parâmetros Elétricos"]
at=AppTest.from_file("/home/claude/bk_lt/app.py",default_timeout=120)
at.session_state["dados"]={"cfg":dict(n_circ=2,n_cg=2,cg1='EHS 7/16"',cg2='EHS 7/16"',forma_c1="Vertical",seq_c2="ABC"),
 "geo":dict(h_cg1=30.0,esp_cg_h=6.0,ga_dx=-3.0,ga_dy=4.0,d12y=3.0,d23y=3.0,circ_dx=6.0,f_cond=6.0,f_cg=3.0),
 "sis":dict(km=80.0,freq=60),
 "c1":dict(cond="LINNET 336,4 MCM",un=138.0,mva=60.0,fp=0.95),"c2":dict(cond="GROSBEAK 636 MCM",un=69.0,mva=20.0,fp=0.92,cabos_fase=1)}
at.run(); assert not at.exception,[e.value for e in at.exception]
for m in MODS:
    at.radio(key="modulo_sel").set_value(m).run(); assert not at.exception,(m,[e.value for e in at.exception])
txt=" ".join(x.value for x in at.warning)
print("avisos:",txt[:200])
print([t.label for t in at.tabs][:12])
b=[b for b in at.button if b.label.startswith("Gerar relatório")][0]; b.click().run(); assert not at.exception,[e.value for e in at.exception]
assert at.session_state["_rel_m2"][:2]==b"PK"; print("docx bytes",len(at.session_state["_rel_m2"]))
b=[b for b in at.button if "PDF" in b.label][0]; b.click().run(); assert not at.exception,[e.value for e in at.exception]
assert at.session_state["_pdf_m2"][:4]==b"%PDF"; print("pdf m2",len(at.session_state["_pdf_m2"]))
at.radio(key="modulo_sel").set_value(MODS[0]).run(); assert not at.exception
print("M1 ok"); 
for i in range(3,17):
    pass
shutil.rmtree(tmp)
