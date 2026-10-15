import os, sys, tempfile, shutil, warnings, glob, io, zipfile, re
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); warnings.simplefilter("ignore")
XLSM = (glob.glob("/mnt/user-data/uploads/LINHA_DE_TRANSMISS*4.xlsm") + glob.glob("/root/.claude/uploads/*/*LINHA_DE_TRANSMISS*4.xlsm"))[0]
tmp = tempfile.mkdtemp(); os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
import db, importar_cabos; db.reset_engine(); importar_cabos.importar(XLSM)
import pontos as P
# ---- migração do cadastro antigo
d = {"viz": {"n": 2},
     "viz0": {"nome": "LT 230 kV", "relacao": "Paralelismo", "tensao": 230.0, "p": 100.0, "q": 20.0, "dist_eixos": 40.0, "comp_par": 3.2, "ang_par": 5.0, "sentido": "Sentido oposto", "defas": 30.0},
     "viz1": {"nome": "RD 13,8", "tipo": "Rede de distribuição", "relacao": "Travessia", "tensao": 13.8, "dist_v": 6.5, "ang_trav": 60.0, "dist_trav_est": 80.0},
     "8": {"usar_viz": True, "viz_sel": ["RD 13,8"]}, "9": {"viz_sel": ["LT 230 kV", "RD 13,8"]}}
d, m = P.migrar_viz(d); assert m and "viz" not in d and "viz0" not in d
assert P.migrar_viz(d)[1] is False                                              # idempotente
assert d["lib0"]["defas_modo"] == P.DEFAS_INF and d["lib0"]["modo_i"] == P.MODO_I[1]
b = P.biblioteca(d); assert abs(b[0]["corrente_normal"] - (100**2 + 20**2) ** .5 * 1000 / (3 ** .5 * 230)) < 1e-6
assert [p["nome"] for p in P.selecionados(d, 8)] == ["RD 13,8 (travessia)"]       # filtro por tipo/seleção
assert [p["nome"] for p in P.selecionados(d, 9)] == ["LT 230 kV (paralelismo)"]    # travessia não vale para o M9
d["pt0"]["viz_ids"] = [5]; assert "não existe" in P.pontos(d)[0]["avisos"][0]       # integridade referencial
assert P.corrente_emergencia(dict(modo_i=P.MODO_I[0], i_normal=300.0, i_emerg=0.0)) == 300.0
print("pontos OK")
# ---- app
from streamlit.testing.v1 import AppTest
dados = {"cfg": dict(n_circ=1, n_cg=1, cg1='EHS 7/16"'), "geo": dict(h_cg1=30.0), "sis": dict(km=80.0, freq=60, un=138.0, umax=145.0),
         "c1": dict(cond="LINNET 336,4 MCM"), "proj": dict(nome="T", numero="9", revisao="R0"),
         "3": dict(modo="Estatísticas", unid="km/h", v_med=62.53, tipo_disp="Coeficiente de variação (%)", s=13.0, n=18, uf="SP", alt=870.0,
                   eds_modo="Temperatura média informada", t_media=19.5, t_max=36.5, t_min=3.2, t_coinc=10.8, t_med_max=33.4, est_nome="M", est_cod="A7",
                   municipio="SP", lat=-23.5, lon=-46.6),
         "4": dict(lm=430.0, lp=350.0, flecha=9.5),
         "viz": {"n": 1}, "viz0": {"nome": "LT 230 kV", "relacao": "Paralelismo", "tensao": 230.0, "p": 100.0, "q": 20.0, "dist_eixos": 40.0, "comp_par": 3.2},
         "4b": {}}
dados.pop("4b")
dados["4"]["viz_sel"] = ["LT 230 kV"]
at = AppTest.from_file(os.path.join(RAIZ, "app.py"), default_timeout=180)
at.session_state["dados"] = dados
at.run(); assert not at.exception, [e.value for e in at.exception]
assert "lib" in at.session_state["dados"] and "viz" not in at.session_state["dados"]      # migrou ao abrir
def ir(n):
    m = [o for o in at.radio(key="modulo_sel").options if f"{n}. " in o][0]
    at.radio(key="modulo_sel").set_value(m).run(); assert not at.exception, [e.value for e in at.exception]
ir(2); assert "Linhas e redes vizinhas" not in [t.label for t in at.tabs], [t.label for t in at.tabs]
ir(4); assert "Pontos e vizinhas" in [t.label for t in at.tabs]
assert at.session_state["dados"]["4"]["pts_sel"] == [0], at.session_state["dados"]["4"]
b = [b for b in at.button if b.label.startswith("Gerar relatório")][0]; b.click().run(); assert not at.exception, [e.value for e in at.exception]
x = zipfile.ZipFile(io.BytesIO(at.session_state["_rel_m4"])).read("word/document.xml").decode()
assert "LT 230 kV" in x and "Pontos de estudo" in x
print("M4 relatório com pontos OK")
# novo ponto direto no M8 + relatório genérico
ir(8)
at.number_input(key="k_pts_n").set_value(2).run(); assert not at.exception, [e.value for e in at.exception]
at.selectbox(key="k_pt1_tipo").set_value(P.T_EDIF).run(); assert not at.exception, [e.value for e in at.exception]
at.text_input(key="k_pt1_nome").set_value("Residência km 12").run()
at.multiselect(key="k_8_pts_sel_w").set_value([0, 1]).run(); assert not at.exception, [e.value for e in at.exception]
assert at.session_state["dados"]["8"]["pts_sel"] == [0, 1]
b = [b for b in at.button if b.label.startswith("Gerar relatório")][0]; b.click().run(); assert not at.exception, [e.value for e in at.exception]
x = zipfile.ZipFile(io.BytesIO(at.session_state["_rel_m8"])).read("word/document.xml").decode()
assert "Residência km 12" in x and "230 kV" in x
for n in (9, 10, 16, 3, 5, 6):
    ir(n)
print("M8/M9/M10/M16 OK"); shutil.rmtree(tmp)
