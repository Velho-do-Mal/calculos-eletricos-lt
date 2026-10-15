import os, sys, tempfile, shutil, warnings
sys.path.insert(0,"/home/claude/bk_lt"); warnings.simplefilter("ignore")
XLSM="/root/.claude/uploads/9d4270f2-2b3e-52a5-b0a9-d0d02b207d6f/682214ad-LINHA_DE_TRANSMISS_O_4.xlsm"
tmp=tempfile.mkdtemp(); os.environ["DATABASE_URL"]=f"sqlite:///{tmp}/t.db"
import db, importar_cabos; db.reset_engine(); importar_cabos.importar(XLSM)
from streamlit.testing.v1 import AppTest
at=AppTest.from_file("/home/claude/bk_lt/app.py",default_timeout=120)
at.session_state["dados"]={"cfg":dict(n_circ=1,n_cg=2),"geo":dict(h_cg1=30.0),"sis":dict(km=18.0,freq=60),"c1":dict(un=138.0,mva=60.0,fp=0.95)}
at.run()
at.radio(key="modulo_sel").set_value([o for o in at.radio(key="modulo_sel").options if "2." in o][0]).run()
print("erros antes:",[e.value[:70] for e in at.error])
assert at.error
at.selectbox(key="k_c1_cond").set_value("LINNET 336,4 MCM").run()
at.selectbox(key="k_cfg_cg1").set_value('EHS 7/16"').run()
at.selectbox(key="k_cfg_cg2").set_value('EHS 7/16"').run()
assert not at.exception,[e.value for e in at.exception]
print("erros depois:",[e.value[:70] for e in at.error])
assert not at.error
print([m.label for m in at.metric][:6]); shutil.rmtree(tmp); print("OK")
