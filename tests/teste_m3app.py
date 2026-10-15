import os, sys, tempfile, shutil, warnings
sys.path.insert(0,"/home/claude/bk_lt"); warnings.simplefilter("ignore")
XLSM="/root/.claude/uploads/9d4270f2-2b3e-52a5-b0a9-d0d02b207d6f/682214ad-LINHA_DE_TRANSMISS_O_4.xlsm"
tmp=tempfile.mkdtemp(); os.environ["DATABASE_URL"]=f"sqlite:///{tmp}/t.db"
import db, importar_cabos; db.reset_engine(); importar_cabos.importar(XLSM)
from streamlit.testing.v1 import AppTest
M3="🌬️  3. Estudo dos Ventos"
at=AppTest.from_file("/home/claude/bk_lt/app.py",default_timeout=120)
at.session_state["dados"]={"cfg":dict(n_circ=1,n_cg=2,cg1='EHS 7/16"',cg2='EHS 7/16"'),"geo":dict(h_cg1=30.0),"sis":dict(km=80.0,freq=60),
 "c1":dict(cond="LINNET 336,4 MCM"),
 "3":dict(modo="Estatísticas",unid="km/h",v_med=62.53,tipo_disp="Coeficiente de variação (%)",s=13.0,n=18,uf="SP",alt=870.0,
          eds_modo="Temperatura média informada",t_media=19.5,t_max=36.5,t_min=3.2,t_coinc=10.8,t_med_max=33.4,est_nome="MIRANTE",est_cod="A701",
          municipio="São Paulo",lat=-23.5,lon=-46.6)}
at.run(); assert not at.exception,[e.value for e in at.exception]
opts=at.radio(key="modulo_sel").options; m=[o for o in opts if "3." in o and "Vento" in o][0]
at.radio(key="modulo_sel").set_value(m).run(); assert not at.exception,[e.value for e in at.exception]
print([t.label for t in at.tabs])
print("avisos:",[w.value[:60] for w in at.warning])
b=[b for b in at.button if b.label.startswith("Gerar relatório")][0]; b.click().run(); assert not at.exception,[e.value for e in at.exception]
assert at.session_state["_rel_m3"][:2]==b"PK"; print("docx",len(at.session_state["_rel_m3"]))
b=[b for b in at.button if "PDF" in b.label][0]; b.click().run(); assert not at.exception,[e.value for e in at.exception]
assert at.session_state["_pdf_m3"][:4]==b"%PDF"; print("pdf m3",len(at.session_state["_pdf_m3"]))
# modo série sem dados
at.session_state["dados"]["3"]["modo"]="Série de máximos anuais"; at.run(); assert not at.exception,[e.value for e in at.exception]
print("pendências série:",[w.value[:50] for w in at.warning])
shutil.rmtree(tmp); print("M3 app OK")
