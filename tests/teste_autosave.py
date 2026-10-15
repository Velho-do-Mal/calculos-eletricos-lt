import os, sys, tempfile, warnings
sys.path.insert(0,"/home/claude/bk_lt"); warnings.simplefilter("ignore")
tmp=tempfile.mkdtemp(); os.environ["DATABASE_URL"]=f"sqlite:///{tmp}/t.db"
import db; db.reset_engine()
from streamlit.testing.v1 import AppTest
at=AppTest.from_file("/home/claude/bk_lt/app.py",default_timeout=120); at.run()
assert not db.listar_projetos()
at.text_input(key="k_proj_nome").set_value("LT AUTO").run()
assert at.session_state["proj_id"] and len(db.listar_projetos())==1, "não criou"
pid=at.session_state["proj_id"]
at.number_input(key="k_sis_km").set_value(33.0).run()
d=db.carregar_projeto(pid); assert d["sis"]["km"]==33.0, d.get("sis")
at.number_input(key="k_sis_km").set_value(44.0).run()
assert db.carregar_projeto(pid)["sis"]["km"]==44.0 and len(db.listar_projetos())==1
print("autosave OK", [e.value for e in at.exception])
