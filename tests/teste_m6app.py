import os, sys, tempfile, shutil, warnings, glob
sys.path.insert(0,"/home/claude/bk_lt"); warnings.simplefilter("ignore")
XLSM=glob.glob("/root/.claude/uploads/*/*LINHA_DE_TRANSMISS_O_4.xlsm")[0]
tmp=tempfile.mkdtemp(); os.environ["DATABASE_URL"]=f"sqlite:///{tmp}/t.db"
import db, importar_cabos; db.reset_engine(); importar_cabos.importar(XLSM)
import calc_aterramento as ca
d=ca.carregar_db(); m=[x for x in d["materiais"] if x["nome"]=="Aço Cobreado 40%"][0]
assert abs(ca.secao_minima(4.181,0.5,m["ar"],m["rho"],m["tcap"],250,26,a0=m["a0"])-25.043)<0.001      # planilha
a=0.0052/2
for L in (10,30,60):                                                                                        # Dwight
    assert abs(ca.resistencia_radial(100,1,L,0.5,a,seg_por_perna=40)/ca.dwight_1perna(100,L,0.5,a)-1)<0.01
assert abs(ca.resistencia_radial(100,4,30,0.5,a)-ca.resistencia_radial(100,4,30,0.5,a,100.0001,2.0))<1e-3   # k→0
fit=ca.ajustar_2camadas([1,2,4,8,16,32],ca.wenner_2camadas([1,2,4,8,16,32],150,600,2.5)); assert abs(fit["rho1"]-150)<2 and abs(fit["h1"]-2.5)<0.1
print("motor OK")
from streamlit.testing.v1 import AppTest
at=AppTest.from_file("/home/claude/bk_lt/app.py",default_timeout=180)
at.session_state["dados"]={"proj":dict(nome="LT Teste",numero="BK-001"),"cfg":dict(n_circ=1,n_cg=1,cg1='EHS 7/16"'),"sis":dict(km=80.0,un=138.0),"c1":dict(cond="HAWK 477 MCM"),
 "6":dict(modo_solo="Medições Wenner (2 camadas)",wenner=[{"a":a_,"R":ca.wenner_2camadas(a_,150,600,2.5)/(2*3.14159*a_)} for a_ in (1,2,4,8,16,32)],n_pernas=4,L=30.0)}
at.run(); assert not at.exception,[e.value for e in at.exception]
def ir(n):
    m=[o for o in at.radio(key="modulo_sel").options if o.split(" ",1)[1].strip().startswith(f"{n}. ")][0]
    at.radio(key="modulo_sel").set_value(m).run(); assert not at.exception,(n,[e.value for e in at.exception])
ir(6); print([ (x.label,x.value) for x in at.metric][:6])
b=[b for b in at.button if b.label.startswith("Gerar relatório")][0]; b.click().run(); assert not at.exception,[e.value for e in at.exception]
assert at.session_state["_rel_m6"][:2]==b"PK"; open("/tmp/m6.docx","wb").write(at.session_state["_rel_m6"])
b=[b for b in at.button if "PDF" in b.label][0]; b.click().run(); assert at.session_state["_pdf_m6"][:4]==b"%PDF"; open("/tmp/m6.pdf","wb").write(at.session_state["_pdf_m6"]); print("M6 relatório OK")
# relatórios genéricos
for n in (1,5):
    ir(n)
    bs=[b for b in at.button if b.label.startswith("Gerar relatório")]; assert bs,("sem botão",n)
    bs[0].click().run(); assert not at.exception,(n,[e.value for e in at.exception])
    assert at.session_state[f"_rel_m{n}"][:2]==b"PK",n
    ps=[b for b in at.button if "PDF" in b.label]; assert ps,("sem PDF",n)
    print("módulo",n,"relatório",len(at.session_state[f"_rel_m{n}"]))
shutil.rmtree(tmp); print("M6 + genéricos OK")
