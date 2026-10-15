import math, sys
sys.path.insert(0, "/home/claude/bk_lt")
from geometria import *

def base(**kw):
    d = dict(n_circ=1, n_cg=1, forma_c1=FORMA_H, forma_c2=C2_TRANSL, seq_c2="ABC",
             h_cg1=30.0, esp_cg_h=0.0, dif_cg_v=0.0, ga_dx=-4.5, ga_dy=6.0,
             d12x=4.5, d23x=4.5, d12y=3.0, d23y=3.0, circ_dx=10.0, circ_dy=0.0,
             f_cond=0.0, f_cg=0.0)
    d.update(kw); return d

def pos(res):
    return {k["nome"]: (round(k["x"], 4), round(k["y"], 4), round(k["y_med"], 4)) for k in res["condutores"]}

# 1) Horizontal, 1 guarda
r = montar_geometria(base())
p = pos(r)
assert p["A1"] == (-4.5, 24.0, 24.0) and p["B1"] == (0.0, 24.0, 24.0) and p["C1"] == (4.5, 24.0, 24.0), p
assert abs(r["angulos"][0]["Guarda 1"] - math.degrees(math.atan(4.5/6))) < 0.01
assert abs(r["angulos"][1]["Guarda 1"] - 0.0) < 1e-9
assert abs(r["eixo_x"] - 0.0) < 1e-9
assert not r["erros"], r["erros"]

# 2) Flecha: altura média = h - 2/3 f
r = montar_geometria(base(f_cond=6.0, f_cg=3.0))
p = pos(r)
assert p["A1"][2] == 20.0 and p["Guarda 1"][2] == 28.0, p

# 3) Vertical, circuito duplo, circuitos lados opostos, seq CBA
r = montar_geometria(base(n_circ=2, n_cg=2, forma_c1=FORMA_V, ga_dx=-3.0, ga_dy=4.0,
                          d12y=3.0, d23y=3.0, circ_dx=6.0, esp_cg_h=6.0, seq_c2="CBA"))
p = pos(r)
assert p["A1"][:2] == (-3.0, 26.0) and p["B1"][:2] == (-3.0, 23.0) and p["C1"][:2] == (-3.0, 20.0), p
assert p["C2"][:2] == (3.0, 26.0) and p["B2"][:2] == (3.0, 23.0) and p["A2"][:2] == (3.0, 20.0), p
assert p["Guarda 2"][:2] == (6.0, 30.0), p
assert not r["erros"], r["erros"]

# 4) Triangular / livre: B abaixo-esquerda de A, C à direita no mesmo nível de B
r = montar_geometria(base(forma_c1=FORMA_T, ga_dx=0.0, ga_dy=5.0, d12x=-3.0, d12y=3.0, d23x=6.0, d23y=0.0))
p = pos(r)
assert p["A1"][:2] == (0.0, 25.0) and p["B1"][:2] == (-3.0, 22.0) and p["C1"][:2] == (3.0, 22.0), p

# 5) Circuito 2 espelhado (triangular): offsets em x invertidos
r = montar_geometria(base(n_circ=2, forma_c1=FORMA_T, forma_c2=C2_ESPELHO, ga_dx=-8.0, ga_dy=5.0,
                          d12x=-3.0, d12y=3.0, d23x=6.0, d23y=0.0, circ_dx=16.0, seq_c2="ABC"))
p = pos(r)
assert p["A2"][:2] == (8.0, 25.0) and p["B2"][:2] == (11.0, 22.0) and p["C2"][:2] == (5.0, 22.0), p

# 6) Validações
r = montar_geometria(base(d12x=0.0))
assert any("sobrepostos" in e for e in r["erros"]), r["erros"]
r = montar_geometria(base(ga_dy=40.0))
assert any("altura na estrutura" in e for e in r["erros"]), r["erros"]
r = montar_geometria(base(f_cond=40.0))
assert any("altura média" in e for e in r["erros"]), r["erros"]
r = montar_geometria(base(ga_dy=0.0))
assert any("não está abaixo" in a for a in r["avisos"]), r["avisos"]
print("geometria OK")

# ---- App headless ----
from streamlit.testing.v1 import AppTest
import pandas as pd

MODS = ["📁  1. Dados do Projeto e Sistema", "🔌  2. Parâmetros Elétricos", "🌬️  3. Estudo dos Ventos",
        "📐  4. Faixa de Domínio", "🛡️  5. Coordenação e Isolamento", "⏚  6. Aterramento",
        "🧵  7. Dimensionamento do Condutor e Cabo Guarda", "🧲  8. Campo Elétrico e Magnético",
        "📡  9. Interferência e Compatibilidade Eletromagnética", "🔊  10. RI e RA", "✨  11. Efeito Corona",
        "🔋  12. Isolamento e Tensão Máxima Operativa", "🌡️  13. Ampacidade e Flecha Máxima",
        "📉  14. Rejeição de Carga", "🔁  15. Religamento Tripolar",
        "⚡  16. Blindagem contra Descargas Atmosféricas"]

def rodar(preset=None, label=""):
    at = AppTest.from_file("/home/claude/bk_lt/app.py", default_timeout=60)
    if preset:
        preset(at)
    at.run()
    assert not at.exception, (label, "inicial", [e.value for e in at.exception])
    for m in MODS:
        at.radio(key="modulo_sel").set_value(m).run()
        assert not at.exception, (label, m, [e.value for e in at.exception])
    return at

# A) estado padrão
rodar(label="padrao")

# B) 2 circuitos, 2 guardas, triangular, 2 vizinhas, catálogo preenchido
def preset(at):
    at.session_state["catalogo"] = {
        "condutores": pd.DataFrame({"Código": ["COND-TESTE"], "Tipo": ["CAA"], "Diâmetro externo (mm)": [25.0],
                                    "Seção total (mm²)": [500.0], "Massa linear (kg/m)": [1.5], "RTC (kN)": [100.0],
                                    "R_cc 20 °C (Ω/km)": [0.09], "RMG (mm)": [10.0],
                                    "Módulo de elasticidade final (GPa)": [70.0], "Coef. de dilatação (10⁻⁶/°C)": [19.0]}),
        "guardas": pd.DataFrame({"Código": ["GUARDA-TESTE"], "Tipo": ["OPGW"], "Diâmetro externo (mm)": [13.0],
                                 "Seção total (mm²)": [80.0], "Massa linear (kg/m)": [0.5], "RTC (kN)": [60.0],
                                 "R_cc 20 °C (Ω/km)": [0.5], "RMG (mm)": [5.0],
                                 "Módulo de elasticidade final (GPa)": [120.0], "Coef. de dilatação (10⁻⁶/°C)": [15.0],
                                 "Capacidade de curto (kA²·s)": [50.0]}),
    }
    at.session_state["dados"] = {
        "cfg": dict(n_circ=2, cabos_fase=2, esp_sub=400.0, n_cg=2, cond="COND-TESTE", cg1="GUARDA-TESTE",
                    cg2="GUARDA-TESTE", forma_c1=FORMA_T, forma_c2=C2_ESPELHO, seq_c2="CBA"),
        "geo": dict(ga_dx=-8.0, ga_dy=5.0, d12x=-3.0, d12y=3.0, d23x=6.0, d23y=0.0, circ_dx=16.0, f_cond=5.0, f_cg=3.0),
        "viz": {"n": 2},
        "viz0": {"nome": "LT 69 kV Norte", "relacao": "Paralelismo", "tensao": 69.0, "p": 30.0, "q": 5.0},
        "viz1": {"nome": "RD 13,8 kV", "tipo": "Rede de distribuição", "relacao": "Travessia", "tensao": 13.8, "p": 3.0},
        "8": {"usar_viz": True, "viz_sel": ["LT 69 kV Norte", "RD 13,8 kV"]},
    }

at = rodar(preset, "completo")
at.radio(key="modulo_sel").set_value(MODS[7]).run()
assert not at.exception
dd = at.session_state["dados"]                      # cadastro antigo migrado para biblioteca + pontos
assert "viz" not in dd and dd["lib"]["n"] == 2 and dd["8"]["pts_sel"] == [0, 1], dd.get("8")
assert any(m.key.endswith("pts_sel_w") for m in at.multiselect), "seleção de pontos não apareceu no M8"
print("app OK (16 módulos, 2 cenários)")

# ---- Novos: derivação, resumo e planta ----
import math
from geometria import planta_vizinha
r = montar_geometria(base(n_circ=2, forma_c1=FORMA_V, ga_dx=-3.0, ga_dy=4.0, d12y=3.0, d23y=3.0,
                          circ_dx=6.0, seq_c2="CBA"))
d = {k["nome"]: k["derivacao"] for k in r["condutores"]}
assert d["A1"] == "Guarda 1 + (-3.00 m; -4.00 m)", d["A1"]
assert d["B1"] == "A1 + (+0.00 m; -3.00 m)", d["B1"]
assert d["C2"].startswith("Posição 1' = A1 + (+6.00 m; +0.00 m)"), d["C2"]
assert d["B2"] == "Posição 2' = C2 + (+0.00 m; -3.00 m)", d["B2"]
rs = r["resumo"]
assert abs(rs["largura_fases"] - 6.0) < 1e-9
assert abs(rs["baricentros"]["d"] - 6.0) < 1e-9 and abs(rs["baricentros"]["dy"]) < 1e-9
assert abs(rs["min_entre_circuitos"] - 6.0) < 1e-9 and abs(rs["min_c1"] - 3.0) < 1e-9
# distâncias: A1-B1 = 3 ; A1-A2 (C2 em posição 1') etc.
dm = {frozenset((a, b)): x for a, b, x in r["distancias"]}
assert abs(dm[frozenset(("A1", "B1"))] - 3.0) < 1e-9
assert abs(dm[frozenset(("A1", "C2"))] - 6.0) < 1e-9
assert abs(dm[frozenset(("A1", "A2"))] - math.hypot(6.0, 6.0)) < 1e-9
# planta: travessia a 90° e paralelismo
pl = planta_vizinha("Travessia", 90.0, 100.0)
assert pl["estrutura"] == (-100.0, 0.0)
assert abs(pl["viz"][0]) < 1e-9 and abs(pl["viz"][2]) < 1e-9 and pl["viz"][3] > 0
pp = planta_vizinha("Paralelismo", 0.0, 30.0, "Direito")
assert pp["viz"][1] == -30.0 and pp["viz"][3] == -30.0
pp = planta_vizinha("Paralelismo", 0.0, 30.0, "Esquerdo")
assert pp["viz"][1] == 30.0
print("geometria (derivação/resumo/planta) OK")
