import os, sys, tempfile, shutil, warnings, glob
sys.path.insert(0,"/home/claude/bk_lt"); warnings.simplefilter("ignore")
XLSM=glob.glob("/root/.claude/uploads/*/*LINHA_DE_TRANSMISS_O_4.xlsm")[0]
tmp=tempfile.mkdtemp(); os.environ["DATABASE_URL"]=f"sqlite:///{tmp}/t.db"
import db, importar_cabos; db.reset_engine(); importar_cabos.importar(XLSM)
import calc_faixa as cf
# motor vs planilha
c=db.obter_cabo("LINNET 336,4 MCM"); q=23.72*9.8067
a=cf.angulo_balanco(20.13,q,c["diametro_mm"]/1000,c["massa_kg_m"]*9.8066,86,55); assert abs(a["beta"]-23.36)<0.01,a
fx=cf.faixa(3,0,4.91,23.36,cf.d_planilha(34.5)); assert abs(fx["L"]-10.89)<0.01 and fx["L_adot"]==11
fa=cf.faixa(3,0,4.91,23.36,cf.d_planilha(34.5),False); assert abs(fa["L"]-4.89)<0.01 and fa["L_adot"]==5 and fa["lado_oposto"]==2
assert abs(cf.fator_K(5)-1)<1e-9
print("motor OK")
from streamlit.testing.v1 import AppTest
at=AppTest.from_file("/home/claude/bk_lt/app.py",default_timeout=120)
at.session_state["dados"]={"cfg":dict(n_circ=1,n_cg=1,cg1='EHS 7/16"'),"geo":dict(h_cg1=30.0),"sis":dict(km=80.0,freq=60,un=138.0,umax=145.0),
 "c1":dict(cond="LINNET 336,4 MCM"),
 "3":dict(modo="Estatísticas",unid="km/h",v_med=62.53,tipo_disp="Coeficiente de variação (%)",s=13.0,n=18,uf="SP",alt=870.0,
          eds_modo="Temperatura média informada",t_media=19.5,t_max=36.5,t_min=3.2,t_coinc=10.8,t_med_max=33.4,est_nome="MIRANTE",est_cod="A701",
          municipio="São Paulo",lat=-23.5,lon=-46.6),
 "4":dict(lm=430.0,lp=350.0,flecha=9.5)}
at.run(); assert not at.exception,[e.value for e in at.exception]
opts=at.radio(key="modulo_sel").options; m=[o for o in opts if o.strip().startswith(tuple("🌟")) or "4." in o][0]
m=[o for o in opts if "4. " in o][0]
at.radio(key="modulo_sel").set_value(m).run(); assert not at.exception,[e.value for e in at.exception]
print([t.label for t in at.tabs]); print("avisos:",[w.value[:70] for w in at.warning])
print([ (x.label,x.value) for x in at.metric])
b=[b for b in at.button if b.label.startswith("Gerar relatório")][0]; b.click().run(); assert not at.exception,[e.value for e in at.exception]
assert at.session_state["_rel_m4"][:2]==b"PK"; print("docx",len(at.session_state["_rel_m4"]))
b=[b for b in at.button if "PDF" in b.label][0]; b.click().run(); assert not at.exception,[e.value for e in at.exception]
assert at.session_state["_pdf_m4"][:4]==b"%PDF"; print("pdf",len(at.session_state["_pdf_m4"]))
open("/tmp/m4.docx","wb").write(at.session_state["_rel_m4"]); open("/tmp/m4.pdf","wb").write(at.session_state["_pdf_m4"])
shutil.rmtree(tmp); print("M4 app OK")
