import os, sys, tempfile, shutil, warnings, datetime as dt
sys.path.insert(0, "/home/claude/bk_lt")
def kk(at,k):
    v=at.session_state["_ver"] if "_ver" in at.session_state else 0
    return k+(f"_v{v}" if v else "")

warnings.simplefilter("ignore")
XLSM = "/root/.claude/uploads/9d4270f2-2b3e-52a5-b0a9-d0d02b207d6f/682214ad-LINHA_DE_TRANSMISS_O_4.xlsm"

tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
import db, importar_cabos
db.reset_engine()
importar_cabos.importar(XLSM)
assert db.contar_cabos() == 293

from streamlit.testing.v1 import AppTest

MODS = ["📁  1. Dados do Projeto e Sistema", "🔌  2. Parâmetros Elétricos", "🌬️  3. Estudo dos Ventos",
        "📐  4. Faixa de Domínio", "🛡️  5. Coordenação e Isolamento", "⏚  6. Aterramento",
        "🧵  7. Dimensionamento do Condutor e Cabo Guarda", "🧲  8. Campo Elétrico e Magnético",
        "📡  9. Interferência e Compatibilidade Eletromagnética", "🔊  10. RI e RA", "✨  11. Efeito Corona",
        "🔋  12. Isolamento e Tensão Máxima Operativa", "🌡️  13. Ampacidade e Flecha Máxima",
        "📉  14. Rejeição de Carga", "🔁  15. Religamento Tripolar",
        "⚡  16. Blindagem contra Descargas Atmosféricas"]

def ok(at, ctx):
    assert not at.exception, (ctx, [e.value for e in at.exception])

def ir(at, i):
    at.radio(key="modulo_sel").set_value(MODS[i - 1]).run(); ok(at, MODS[i - 1])

at = AppTest.from_file("/home/claude/bk_lt/app.py", default_timeout=90)
at.run(); ok(at, "inicial")
for i in range(1, 17):
    ir(at, i)
print("[1] 16 módulos sem exceção com o banco carregado")

# --- seleção de cabos no Módulo 1 (aba Configuração da LT) ---
ir(at, 1)
at.selectbox(key=kk(at,"k_cfg_n_cg")).set_value(2).run(); ok(at, "n_cg")
at.selectbox(key=kk(at,"k_c1_cond")).set_value("LINNET 336,4 MCM").run(); ok(at, "cond")
at.selectbox(key=kk(at,"k_cfg_cg1")).set_value('EHS 7/16"').run(); ok(at, "cg1")
at.selectbox(key=kk(at,"k_cfg_cg2")).set_value("OPGW 14,1 mm 48FO").run(); ok(at, "cg2")
opcoes_guarda = at.selectbox(key=kk(at,"k_cfg_cg1")).options
assert any("OPGW" in o for o in opcoes_guarda) and any('EHS 7/16"' in o for o in opcoes_guarda)
assert not any("LINNET" in o for o in opcoes_guarda), "guarda não deve listar condutores"
opcoes_cond = at.selectbox(key=kk(at,"k_c1_cond")).options
assert len(opcoes_cond) == 281 and all("EHS" not in o and "OPGW" not in o for o in opcoes_cond[1:])
print("[2] seleção filtrada por uso: 280 condutores; guardas = 8 aço + 4 OPGW")

# --- Módulo 7 mostra propriedades vindas do banco ---
ir(at, 7)
df = at.dataframe[0].value
lin = df[df["Código"] == "LINNET 336,4 MCM"].iloc[0]
assert lin["R_cc 20 °C (Ω/km)"] == 0.1695 and lin["Diâmetro (mm)"] == 18.29 and abs(lin["RTC (kN)"] - 62.694) < 0.001
avisos = " ".join(w.value for w in at.warning)
assert "RMG não cadastrado" in avisos and "LINNET" in avisos
print("[3] Módulo 7: propriedades do banco (R_cc 0,1695; Ø 18,29; RTC 62,69 kN) e aviso de RMG ausente")

# --- Catálogo: editar RMG pelo formulário ---
ir(at, 2)
cat = at.selectbox(key="cat_ed_cod"); assert cat is not None
cat.set_value("LINNET 336,4 MCM").run(); ok(at, "cat sel")
c = db.obter_cabo("LINNET 336,4 MCM"); ch = f"LINNET 336,4 MCM_{c['atualizado_em']:%Y%m%d%H%M%S%f}"
at.number_input(key=f"cat_{ch}_rmg_mm").set_value(7.31)       # dentro de st.form: sem run intermediário
btn = [b for b in at.button if b.label == "Salvar alterações"][0]; btn.click().run(); ok(at, "rmg save")
assert db.obter_cabo("LINNET 336,4 MCM")["rmg_mm"] == 7.31
assert db.obter_cabo("LINNET 336,4 MCM")["secao_mm2"] == 198      # demais campos intactos
assert abs(db.obter_cabo("LINNET 336,4 MCM")["rtc_kgf"] - 6393) < 0.01   # kgf recalculado a partir de kN
print("[4] editar RMG pelo app grava no banco sem alterar o resto")
ir(at, 7)
avisos = " ".join(w.value for w in at.warning)
assert "LINNET" not in avisos.split("RMG não cadastrado")[-1] if "RMG não cadastrado" in avisos else True
df = at.dataframe[0].value
assert df[df["Código"] == "LINNET 336,4 MCM"].iloc[0]["RMG (mm)"] == 7.31
print("[5] Módulo 7 passa a mostrar RMG 7,31 mm")

# --- adicionar cabo manual duplicado → erro; novo → ok ---
ir(at, 2)
at.text_input(key="cat_novo_codigo").set_value("LINNET 336,4 MCM")
[b for b in at.button if b.label == "Cadastrar cabo"][0].click().run(); ok(at, "dup")
assert any("Já existe" in e.value for e in at.error)
at.text_input(key="cat_novo_codigo").set_value("CABO-NOVO")
at.number_input(key="cat_novo_secao_mm2").set_value(120.0)
[b for b in at.button if b.label == "Cadastrar cabo"][0].click().run(); ok(at, "novo")
n = db.obter_cabo("CABO-NOVO"); assert n and n["origem"] == "manual" and n["secao_mm2"] == 120.0
print("[6] cadastro manual: duplicado barrado, novo gravado")

# --- contrapeso no Módulo 6 ---
ir(at, 6)
at.selectbox(key=kk(at,"k_6_cabo_at")).set_value("Aço Cobreado 40% - 25 mm²").run(); ok(at, "contrapeso")
assert at.selectbox(key=kk(at,"k_6_cabo_at")).value == "Aço Cobreado 40% - 25 mm²"
print("[7] Módulo 6 seleciona o cabo contrapeso do catálogo")

# --- projetos: salvar, alterar, abrir (restaura) ---
ir(at, 1)
at.text_input(key=kk(at,"k_proj_nome")).set_value("LT 138 kV Teste").run()
at.text_input(key=kk(at,"k_proj_numero")).set_value("P-777").run()
at.text_input(key=kk(at,"k_proj_cliente")).set_value("ACME").run()
at.button(key="btn_salvar").click().run(); ok(at, "salvar")
projs = db.listar_projetos(); assert len(projs) == 1 and projs[0]["numero"] == "P-777"
pid = projs[0]["id"]
sec = db.carregar_projeto(pid)
assert sec["c1"]["cond"] == "LINNET 336,4 MCM" and sec["cfg"]["cg2"] == "OPGW 14,1 mm 48FO" and sec["cfg"]["n_cg"] == 2
assert sec["6"]["cabo_at"] == "Aço Cobreado 40% - 25 mm²" and sec["proj"]["nome"] == "LT 138 kV Teste"
assert at.session_state["proj_id"] == pid
print("[8] projeto salvo com cabos, contrapeso e dados (incl. última edição)")

# altera e confere que 'Salvar' atualiza o MESMO projeto (não cria outro)
at.text_input(key=kk(at,"k_proj_revisao")).set_value("R3").run()
at.button(key="btn_salvar").click().run(); ok(at, "salvar2")
assert len(db.listar_projetos()) == 1 and db.listar_projetos()[0]["revisao"] == "R3"
# 'Salvar como novo' cria outro
at.button(key="btn_salvar_novo").click().run(); ok(at, "novo")
assert len(db.listar_projetos()) == 2
print("[9] Salvar atualiza o mesmo projeto; Salvar como novo cria outro")

# nova sessão: abre projeto e confere restauração nos widgets
at2 = AppTest.from_file("/home/claude/bk_lt/app.py", default_timeout=90); at2.run(); ok(at2, "at2")
assert at2.session_state["proj_id"] is None
alvo = [p for p in db.listar_projetos() if p["id"] == pid][0]
from importlib import import_module
sel = at2.selectbox(key="sel_proj_salvo"); assert any(f"#{pid}" in o for o in sel.options)
sel.set_value([o for o in sel.options if o.startswith(f"#{pid} ")][0]).run()
at2.button(key="btn_abrir").click().run(); ok(at2, "abrir")
assert at2.session_state["proj_id"] == pid
at2.radio(key="modulo_sel").set_value(MODS[0]).run(); ok(at2, "m1")
assert at2.text_input(key=kk(at2,"k_proj_nome")).value == "LT 138 kV Teste"
assert at2.selectbox(key=kk(at2,"k_c1_cond")).value == "LINNET 336,4 MCM"
assert at2.selectbox(key=kk(at2,"k_cfg_n_cg")).value == 2
print("[10] abrir projeto em nova sessão restaura nome, condutor e nº de guardas nos widgets")

# excluir
at2.checkbox(key="conf_del").check().run()
at2.button(key="btn_excluir").click().run(); ok(at2, "excluir")
assert all(p["id"] != pid for p in db.listar_projetos()) and db.carregar_projeto(pid) is None
print("[11] excluir projeto com confirmação")

db.reset_engine(); shutil.rmtree(tmp)
print("app+db OK")
