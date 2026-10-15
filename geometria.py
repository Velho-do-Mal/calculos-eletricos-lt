"""
Geometria da seção transversal da LT — funções puras (sem Streamlit), testáveis.

Convenções
----------
- Origem do eixo x: cabo guarda 1. x positivo para a direita.
- y = altura em relação ao solo, medida NA ESTRUTURA (ponto de fixação), em metros.
- Deslocamentos verticais (dy) informados como "abaixo": positivo = mais baixo
  (na coordenada, y_novo = y_anterior - dy).
- Circuito 1: posições 1, 2, 3 = fases A, B, C (por definição).
  A posição da fase A (= posição 1) é referenciada ao cabo guarda 1.
- Circuito 2: posição 1' é referenciada à posição 1 do circuito 1
  (distância horizontal e vertical entre circuitos).
  A sequência de fases do circuito 2 nas posições 1', 2', 3' é escolhida no projeto.
  Forma "espelhada": os deslocamentos horizontais P1'->P2'->P3' têm sinal invertido.
- Altura média no vão (usada nos cálculos elétricos) = altura na estrutura - 2/3 da flecha.
- Distância entre dois condutores: d = sqrt(dx^2 + dy^2), com as coordenadas na estrutura.
- Ângulo de blindagem (guarda -> fase) = arctan(|dx| / dy_vertical), medido a partir da
  vertical que passa pelo cabo guarda.
"""
import math
from itertools import combinations

FORMA_H = "Horizontal"
FORMA_V = "Vertical"
FORMA_T = "Triangular / livre"
FORMAS = (FORMA_H, FORMA_V, FORMA_T)

C2_TRANSL = "Mesma forma do circuito 1 (translação)"
C2_ESPELHO = "Espelhada em relação ao eixo vertical"
FORMAS_C2 = (C2_TRANSL, C2_ESPELHO)

SEQUENCIAS = ("ABC", "ACB", "BAC", "BCA", "CAB", "CBA")

FLECHA_FATOR = 2.0 / 3.0
DIST_MIN_M = 0.05


def _offsets(forma, c):
    """Deslocamentos (dx, dy) P1->P2 e P2->P3; dy positivo = para baixo."""
    if forma == FORMA_H:
        return (c["d12x"], 0.0), (c["d23x"], 0.0)
    if forma == FORMA_V:
        return (0.0, c["d12y"]), (0.0, c["d23y"])
    return (c["d12x"], c["d12y"]), (c["d23x"], c["d23y"])


def _z(v):
    """Evita '-0.00' na exibição."""
    return round(v, 6) + 0.0


def _delta(dx, dy_baixo):
    """Texto do deslocamento em coordenadas (Δx; Δy), com Δy = -dy_baixo."""
    return f"({_z(dx):+.2f} m; {_z(-dy_baixo):+.2f} m)"


def montar_geometria(c):
    """
    Entrada (dict c): n_circ, n_cg, forma_c1, forma_c2, seq_c2,
      h_cg1, esp_cg_h, dif_cg_v, ga_dx, ga_dy, d12x, d12y, d23x, d23y,
      circ_dx, circ_dy, f_cond, f_cg
    Saída: dict com condutores (cada um com 'derivacao'), erros, avisos, angulos
      (blindagem), eixo_x, distancias (todos os pares) e resumo.
    """
    erros, avisos = [], []
    n_circ = int(c["n_circ"])
    n_cg = int(c["n_cg"])
    cond = []

    def add(nome, tipo, circ, fase, x, y, flecha, derivacao):
        cond.append({
            "nome": nome, "tipo": tipo, "circuito": circ, "fase": fase,
            "x": x, "y": y, "flecha": flecha,
            "y_med": y - FLECHA_FATOR * flecha, "derivacao": derivacao,
        })

    # Cabos guarda
    add("Guarda 1", "guarda", None, None, 0.0, c["h_cg1"], c["f_cg"],
        f"Origem de x; altura informada = {c['h_cg1']:.2f} m")
    if n_cg == 2:
        add("Guarda 2", "guarda", None, None, c["esp_cg_h"], c["h_cg1"] - c["dif_cg_v"], c["f_cg"],
            f"Guarda 1 + {_delta(c['esp_cg_h'], c['dif_cg_v'])}")

    # Circuito 1 (posição 1 = fase A referenciada ao guarda 1)
    o12, o23 = _offsets(c["forma_c1"], c)
    p1 = (c["ga_dx"], c["h_cg1"] - c["ga_dy"])
    p2 = (p1[0] + o12[0], p1[1] - o12[1])
    p3 = (p2[0] + o23[0], p2[1] - o23[1])
    add("A1", "fase", 1, "A", p1[0], p1[1], c["f_cond"],
        f"Guarda 1 + {_delta(c['ga_dx'], c['ga_dy'])}")
    add("B1", "fase", 1, "B", p2[0], p2[1], c["f_cond"], f"A1 + {_delta(*o12)}")
    add("C1", "fase", 1, "C", p3[0], p3[1], c["f_cond"], f"B1 + {_delta(*o23)}")

    # Circuito 2
    if n_circ == 2:
        s = 1.0 if c["forma_c2"] == C2_TRANSL else -1.0
        q1 = (p1[0] + c["circ_dx"], p1[1] - c["circ_dy"])
        q2 = (q1[0] + s * o12[0], q1[1] - o12[1])
        q3 = (q2[0] + s * o23[0], q2[1] - o23[1])
        seq = c["seq_c2"]
        add(f"{seq[0]}2", "fase", 2, seq[0], q1[0], q1[1], c["f_cond"],
            f"Posição 1' = A1 + {_delta(c['circ_dx'], c['circ_dy'])} (distância entre circuitos)")
        add(f"{seq[1]}2", "fase", 2, seq[1], q2[0], q2[1], c["f_cond"],
            f"Posição 2' = {seq[0]}2 + {_delta(s * o12[0], o12[1])}")
        add(f"{seq[2]}2", "fase", 2, seq[2], q3[0], q3[1], c["f_cond"],
            f"Posição 3' = {seq[1]}2 + {_delta(s * o23[0], o23[1])}")

    # ---- Validações ----
    for k in cond:
        if k["y"] <= 0:
            erros.append(f"{k['nome']}: altura na estrutura ≤ 0 (y = {k['y']:.2f} m).")
        elif k["y_med"] <= 0:
            erros.append(f"{k['nome']}: altura média no vão ≤ 0 (verifique a flecha).")

    distancias = []
    for a, b in combinations(cond, 2):
        d = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
        distancias.append((a["nome"], b["nome"], d))
        if d < DIST_MIN_M:
            erros.append(f"{a['nome']} e {b['nome']} estão sobrepostos (distância {d:.3f} m).")

    guardas = [k for k in cond if k["tipo"] == "guarda"]
    fases = [k for k in cond if k["tipo"] == "fase"]
    for f in fases:
        if any(g["y"] <= f["y"] for g in guardas):
            avisos.append(f"Fase {f['nome']} não está abaixo de todos os cabos guarda — verifique a geometria.")
    if c["f_cond"] == 0 and c["f_cg"] == 0:
        avisos.append("Flechas = 0: a altura média no vão será igual à altura na estrutura.")

    # ---- Ângulo de blindagem (guarda -> fase), em relação à vertical do guarda ----
    angulos = []
    for f in fases:
        linha = {"Fase": f["nome"]}
        for g in guardas:
            dy = g["y"] - f["y"]
            linha[g["nome"]] = (
                round(math.degrees(math.atan2(abs(g["x"] - f["x"]), dy)), 2) if dy > 0 else None
            )
        angulos.append(linha)

    # ---- Resumo / conferência das medidas entre circuitos ----
    dmap = {frozenset((a, b)): d for a, b, d in distancias}
    resumo = {}
    xs = [f["x"] for f in fases]
    if fases:
        resumo["largura_fases"] = max(xs) - min(xs)
    c1 = [f for f in fases if f["circuito"] == 1]
    c2 = [f for f in fases if f["circuito"] == 2]
    if c1 and c2:
        bx1 = sum(f["x"] for f in c1) / 3.0
        by1 = sum(f["y"] for f in c1) / 3.0
        bx2 = sum(f["x"] for f in c2) / 3.0
        by2 = sum(f["y"] for f in c2) / 3.0
        resumo["baricentros"] = {
            "dx": bx2 - bx1, "dy": by2 - by1, "d": math.hypot(bx2 - bx1, by2 - by1)}
        resumo["min_entre_circuitos"] = min(dmap[frozenset((a["nome"], b["nome"]))] for a in c1 for b in c2)
    for k, grupo in (("min_c1", c1), ("min_c2", c2)):
        if len(grupo) == 3:
            resumo[k] = min(dmap[frozenset((a["nome"], b["nome"]))] for a, b in combinations(grupo, 2))

    return {
        "condutores": cond,
        "erros": erros,
        "avisos": avisos,
        "angulos": angulos,
        "eixo_x": (min(xs) + max(xs)) / 2.0 if xs else 0.0,
        "distancias": distancias,
        "resumo": resumo,
    }


def planta_vizinha(relacao, ang_graus, dist_h, lado="Direito", comprimento=None):
    """
    Segmentos (x0, y0, x1, y1) para o croqui em PLANTA da LT em estudo (horizontal, ao longo de x)
    e da vizinha.
    - Paralelismo: vizinha passa a dist_h do eixo (lado Direito = y negativo, Esquerdo = y positivo
      quando se olha a LT no sentido +x) e forma ângulo ang com o eixo.
    - Travessia: vizinha cruza a LT na origem com ângulo ang; dist_h é a distância do ponto de
      travessia à estrutura mais próxima da LT em estudo (em x = -dist_h).
    Retorna dict com 'lt', 'viz' e (travessia) 'estrutura'.
    """
    L = comprimento or max(1.5 * dist_h, 100.0)
    a = math.radians(ang_graus)
    lt = (-L, 0.0, L, 0.0)
    if relacao == "Travessia":
        viz = (-L * math.cos(a), -L * math.sin(a), L * math.cos(a), L * math.sin(a))
        return {"lt": lt, "viz": viz, "estrutura": (-dist_h, 0.0)}
    y0 = -dist_h if lado == "Direito" else dist_h
    viz = (-L * math.cos(a), y0 - L * math.sin(a), L * math.cos(a), y0 + L * math.sin(a))
    return {"lt": lt, "viz": viz, "estrutura": None}
