import os, sys, tempfile, warnings
sys.path.insert(0,"/home/claude/bk_lt"); warnings.simplefilter("ignore")
tmp=tempfile.mkdtemp(); os.environ["DATABASE_URL"]=f"sqlite:///{tmp}/t.db"
import db; db.reset_engine()
from streamlit.testing.v1 import AppTest
def kk(at,k):
    v=at.session_state["_ver"] if "_ver" in at.session_state else 0
    return k+(f"_v{v}" if v else "")
at=AppTest.from_file("/home/claude/bk_lt/app.py",default_timeout=120); at.run()
at.text_input(key="k_proj_nome").set_value("LT X").run()
at.number_input(key="k_sis_km").set_value(77.0).run()
at.selectbox(key="k_sis_freq").set_value(50).run()
pid=at.session_state["proj_id"]
at2=AppTest.from_file("/home/claude/bk_lt/app.py",default_timeout=120); at2.run()
at2.button(key="btn_abrir").click().run()
assert at2.session_state["_ver"]==1
at2.run(); at2.run()
assert at2.number_input(key=kk(at2,"k_sis_km")).value==77.0
d=db.carregar_projeto(pid); assert d["sis"]["km"]==77.0 and d["sis"]["freq"]==50, d["sis"]
# Módulo 3: sem dados, botões de relatório/impressão aparecem (desabilitados)
at2.radio(key="modulo_sel").set_value([o for o in at2.radio(key="modulo_sel").options if "3." in o][0]).run()
rot=[b.label for b in at2.button]; print([r for r in rot if "relatório" in r or "PDF" in r])
assert any("PDF" in r for r in rot)
print("abrir/dados OK")
