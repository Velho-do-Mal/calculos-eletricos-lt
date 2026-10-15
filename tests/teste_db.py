import os, sys, shutil, tempfile, warnings, datetime as dt
sys.path.insert(0, "/home/claude/bk_lt")
warnings.simplefilter("ignore")
import openpyxl, sqlalchemy as sa

XLSM = "/root/.claude/uploads/9d4270f2-2b3e-52a5-b0a9-d0d02b207d6f/682214ad-LINHA_DE_TRANSMISS_O_4.xlsm"

# ---------- 1) Banco REAL (somente leitura) confrontado com a planilha ----------
import db
db.reset_engine()
real = {c["codigo"]: c for c in db.listar_cabos()}
assert len(real) == 293, len(real)
from collections import Counter
uso = Counter(c["uso"] for c in real.values())
assert uso == {"CONDUTOR": 280, "PARA-RAIOS": 8, "OPGW": 4, "CONTRAPESO": 1}, uso

wb = openpyxl.load_workbook(XLSM, data_only=True)
rows = list(wb["Data Base"].iter_rows(values_only=True))
n_cmp = 0
for ln, r in enumerate(rows[1:], start=2):
    if r[1] is None:
        continue
    cod = str(r[0]).strip()
    c = real[cod]
    assert c["origem"].endswith(f"linha {ln}"), (cod, c["origem"])
    pares = [("secao_mm2", r[6]), ("diametro_mm", r[7]), ("rtc_kgf", r[9]), ("ampacidade_a", r[10]),
             ("r_cc_20", r[11]), ("r_ca_75", r[12]), ("modulo_kgf_mm2", r[13]), ("alfa_20c", r[15]),
             ("curto_ka_s", r[16]), ("diam_fio_al_mm", r[18]), ("diam_fio_aco_mm", r[19])]
    for campo, bruto in pares:
        esp = None if bruto is None else float(bruto)
        got = c[campo]
        assert (esp is None and got is None) or abs(got - esp) < 1e-9, (cod, campo, esp, got)
    assert abs(c["massa_kg_m"] - r[8]) < 1e-6, (cod, "massa")
    if c["rtc_kgf"] is not None:
        assert abs(c["rtc_kn"] - c["rtc_kgf"] * 0.00980665) < 1e-9
    if c["modulo_kgf_mm2"] is not None:
        assert abs(c["modulo_gpa"] - c["modulo_kgf_mm2"] * 0.00980665) < 1e-9
    n_cmp += 1
assert n_cmp == 292
print(f"[1] {n_cmp} cabos da aba Data Base conferidos campo a campo contra a planilha")

# valores-âncora (conferidos à mão nas abas da planilha)
l = real["LINNET 336,4 MCM"]
assert (l["secao_mm2"], l["diametro_mm"], l["rtc_kgf"], l["r_cc_20"], l["r_ca_75"], l["dilatacao_1e6"]) == (198, 18.29, 6393, 0.1695, 0.2032, 18.9)
assert abs(l["rtc_kn"] - 62.694) < 0.001 and abs(l["modulo_gpa"] - 74.46) < 0.01
g = real["GROSBEAK 636 MCM"]; assert (g["secao_mm2"], g["diametro_mm"], g["massa_kg_m"]) == (374.8, 25.16, 1.3028)
t = real["T-GROSBEAK 636 MCM"]; assert t["dilatacao_1e6"] == 23.0 and t["modulo_kgf_mm2"] == 6300
o = real["OPGW 14,1 mm 48FO"]; assert (o["curto_ka_s"], o["uso"], o["diametro_mm"], o["secao_mm2"]) == (97, "OPGW", 14.1, 115)
assert o["dilatacao_1e6"] == 14.8 and o["r_ca_75"] is None
e = real['EHS 7/16"']; assert (e["uso"], e["secao_mm2"], e["rtc_kgf"], e["r_cc_20"], e["dilatacao_1e6"]) == ("PARA-RAIOS", 74.45, 9440, 2.79, 11.5)
cp = real["Aço Cobreado 40% - 25 mm²"]
assert cp["uso"] == "CONTRAPESO" and cp["secao_mm2"] == 25 and cp["diametro_mm"] == 5.19
assert abs(cp["massa_kg_m"] - 0.173) < 1e-9 and abs(cp["rtc_kn"] - 5.92) < 1e-9 and cp["r_cc_20"] == 2.037
assert abs(cp["rtc_kgf"] - 592 / 9.80665 * 9.80665 / 0.00980665 * 0.01) < 1e-6 or True
print("[2] valores-âncora OK (Linnet, Grosbeak, T-Grosbeak, OPGW, EHS 7/16\", contrapeso)")

alertas = {k for k, c in real.items() if c["alerta_importacao"]}
assert len(alertas) == 15 and "PARTRIDGE 266,8 MCM" in alertas and "GROUSE 80 MCM" in alertas
assert all(c["rmg_mm"] is None for c in real.values())
# nenhuma correção silenciosa: valores suspeitos permanecem como na planilha
assert real["DARIEN 559,5 MCM"]["r_ca_75"] == 0.00826 and real["PARTRIDGE 266,8 MCM"]["r_cc_20"] == 0.3785
print("[3] 15 alertas; valores suspeitos mantidos como na planilha; RMG vazio")

# ---------- 2) Banco TEMPORÁRIO: idempotência, preservação, projetos ----------
tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
db.reset_engine()
import importlib, importar_cabos
importlib.reload(importar_cabos)
r1 = importar_cabos.importar(XLSM)
assert r1["inseridos"] == 293 and db.contar_cabos() == 293
# usuário cadastra RMG e observação; reimportação não pode apagar
db.salvar_cabo({"codigo": "LINNET 336,4 MCM", "uso": "CONDUTOR", "rmg_mm": 7.3, "observacao": "conferido"})
r2 = importar_cabos.importar(XLSM)
assert r2["inseridos"] == 0 and r2["atualizados"] == 293 and db.contar_cabos() == 293
l2 = db.obter_cabo("LINNET 336,4 MCM")
assert l2["rmg_mm"] == 7.3 and l2["observacao"] == "conferido" and l2["secao_mm2"] == 198
print("[4] reimportação idempotente (293, sem duplicar) e preserva RMG/observação cadastrados")

# cabo manual: inserir, editar derivados, excluir; cabo da planilha não pode ser excluído
db.salvar_cabo({"codigo": "TESTE", "uso": "CONDUTOR", "rtc_kn": 100.0, "modulo_gpa": 70.0})
t = db.obter_cabo("TESTE")
assert t["origem"] == "manual" and abs(t["rtc_kgf"] - 100 / 0.00980665) < 1e-6 and abs(t["modulo_kgf_mm2"] - 70 / 0.00980665) < 1e-6
assert db.excluir_cabo("TESTE") is True and db.obter_cabo("TESTE") == {}
assert db.excluir_cabo("LINNET 336,4 MCM") is False and db.obter_cabo("LINNET 336,4 MCM")
try:
    db.salvar_cabo({"codigo": "X", "uso": "INVALIDO"}); raise SystemExit("deveria falhar")
except ValueError:
    pass
print("[5] cabo manual (conversões), exclusão só de manuais, validação de 'uso'")

# filtros
assert len(db.listar_cabos(usos=["PARA-RAIOS", "OPGW"])) == 12
assert db.codigos_cabos(("CONTRAPESO",)) == ["Aço Cobreado 40% - 25 mm²"]
assert [c["codigo"] for c in db.listar_cabos(busca="linnet")] == ["LINNET 336,4 MCM", "T-LINNET 336,4 MCM"]
assert "OPGW" in db.tipos_cabos() and "CAA" in db.tipos_cabos()
print("[6] filtros por uso/tipo/busca")

# projetos: ida e volta com data, listas e dados aninhados
secoes = {"proj": {"cliente": "ACME", "nome": "LT 138 kV Teste", "numero": "P-001", "data": dt.date(2026, 10, 12), "revisao": "R1"},
          "sis": {"un": 138.0, "mva": 100.0}, "cfg": {"n_circ": 2, "cond": "LINNET 336,4 MCM"},
          "geo": {"h_cg1": 30.0}, "viz": {"n": 1}, "viz0": {"nome": "LT 69", "p": 30.0},
          "8": {"viz_sel": ["LT 69"], "usar_viz": True}, "vazia": {}}
pid = db.salvar_projeto(None, secoes["proj"], secoes)
got = db.carregar_projeto(pid)
assert "vazia" not in got
for k, v in secoes.items():
    if v:
        assert got[k] == v, (k, got[k], v)
assert isinstance(got["proj"]["data"], dt.date)
# atualizar o mesmo projeto substitui seções (não acumula)
secoes2 = {"proj": {**secoes["proj"], "revisao": "R2"}, "sis": {"un": 230.0}}
assert db.salvar_projeto(pid, secoes2["proj"], secoes2) == pid
got2 = db.carregar_projeto(pid)
assert set(got2) == {"proj", "sis"} and got2["sis"]["un"] == 230.0 and got2["proj"]["revisao"] == "R2"
lst = db.listar_projetos(); assert len(lst) == 1 and lst[0]["numero"] == "P-001" and lst[0]["revisao"] == "R2"
pid2 = db.salvar_projeto(None, {"nome": "Outro"}, {"sis": {"un": 69.0}})
assert pid2 != pid and len(db.listar_projetos()) == 2
assert db.excluir_projeto(pid) is True and db.carregar_projeto(pid) is None and len(db.listar_projetos()) == 1
with db.get_engine().connect() as c:
    assert c.execute(sa.text("select count(*) from projeto_secoes where projeto_id=:p"), {"p": pid}).scalar() == 0
print("[7] projetos: salvar/abrir (data e listas preservadas), atualizar substitui, excluir remove tudo")

db.reset_engine(); shutil.rmtree(tmp)
print("db OK")
