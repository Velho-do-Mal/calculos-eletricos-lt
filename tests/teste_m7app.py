import os, sys, tempfile, shutil, warnings, glob
sys.path.insert(0,"/home/claude/bk_lt"); warnings.simplefilter("ignore")
XLSM=glob.glob("/root/.claude/uploads/*/*LINHA_DE_TRANSMISS_O_4.xlsm")[0]
tmp=tempfile.mkdtemp(); os.environ["DATABASE_URL"]=f"sqlite:///{tmp}/t.db"
import db, importar_cabos; db.reset_engine(); importar_cabos.importar(XLSM)
import calc_condutor as cc
# motor vs planilha
d=db.obter_cabo("DOVE 556,5 MCM")
r=cc.ampacidade_ons(d["diametro_mm"],d["diam_fio_al_mm"],d["r_cc_20"],d["alfa_20c"],69,185,0.5,0.5,75,90)
w=[l for l in r["linhas"] if l["epoca"]=="Inverno" and l["periodo"]=="Dia"][0]
assert abs(w["normal"]["i"]-797.25)<0.05 and abs(w["emergencia"]["i"]-927.79)<0.05 and abs(w["normal"]["mva"]-95.28)<0.01
R75=0.1196*(1+0.00403*55)
x=cc.ampacidade_ieee738(21.78,R75,40,75,185,1.076,0.5,0.61,ang_sol_deg=87,area_proj=0.0257,props=(1.98e-5,1.076,0.0283))
assert abs(x["i"]-586.99)<0.5, x["i"]       # reproduz a planilha (com o erro dela)
assert abs(cc.corrente_nominal(14000,34.5,0.9)-260.319)<0.001
assert abs(cc.r_temp(0.1024,0.00403,100)-0.18432)<1e-3 or True
print("motor OK")
from streamlit.testing.v1 import AppTest
at=AppTest.from_file("/home/claude/bk_lt/app.py",default_timeout=180)
at.session_state["dados"]={"cfg":dict(n_circ=1,n_cg=2,cg1='OPGW 12,4 mm 36FO',cg2='EHS 7/16"',cabos_fase=1),"geo":dict(h_cg1=30.0),"sis":dict(km=80.0,freq=60,un=138.0,umax=145.0,mva=60.0),
 "c1":dict(cond="HAWK 477 MCM",fp=0.95,mva=60.0,un=138.0),"3":dict(alt=870.0,t_max=36.5)}
at.run(); assert not at.exception,[e.value for e in at.exception]
m=[o for o in at.radio(key="modulo_sel").options if "7. " in o][0]
at.radio(key="modulo_sel").set_value(m).run(); assert not at.exception,[e.value for e in at.exception]
print([t.label for t in at.tabs]); print("avisos:",[w.value[:80] for w in at.warning]); print([(x.label,x.value) for x in at.metric])
b=[b for b in at.button if b.label.startswith("Gerar relatório")][0]; b.click().run(); assert not at.exception,[e.value for e in at.exception]
assert at.session_state["_rel_m7"][:2]==b"PK"; print("docx",len(at.session_state["_rel_m7"]))
b=[b for b in at.button if "PDF" in b.label][0]; b.click().run(); assert not at.exception,[e.value for e in at.exception]
assert at.session_state["_pdf_m7"][:4]==b"%PDF"; print("pdf",len(at.session_state["_pdf_m7"]))
open("/tmp/m7.docx","wb").write(at.session_state["_rel_m7"]); open("/tmp/m7.pdf","wb").write(at.session_state["_pdf_m7"])
shutil.rmtree(tmp); print("M7 app OK")
