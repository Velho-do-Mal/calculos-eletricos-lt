"""
Módulo 8 – Campos elétrico (E) e magnético (B) ao nível do solo – funções puras (sem Streamlit).

Métodos (todos vindos do acervo do projeto):
  • E: Método da Simulação de Cargas / das imagens (Livro 3 'Cálculos Elétricos de LTs', cap. 6, eq. 1-12 e 28-33; relatório
    ESS-2ITA-595-87, 3.1): [Q] = [P]^-1 · [V], solo plano e equipotencial, campo por Gauss de cilindro infinito, fasores,
    E = sqrt(|Ex|² + |Ey|² + |Ez|²) (valor eficaz resultante).
  • B: Biot-Savart por fasores com o método das imagens complexas de Deri (ESS-2ITA-595-87, 3.2 e Fig. 3):
    profundidade complexa p = sqrt(ρ / (j·ω·μ0)); imagem em y' = −y − 2p com corrente oposta (solo condutor perfeito: p = 0).
  • Limites: REN ANEEL 915/2021 (60 Hz) conforme o relatório ESS-2ITA-595-87 – NECESSITA VALIDAÇÃO com o texto oficial.
  • Altura de referência: 1,5 m do solo (Diretrizes de projeto básico 6.10; REN 915 conforme o relatório).
Premissas: cabos guarda desprezados no B e, por padrão, também no E (condição mais desfavorável); torres não distorcem o campo;
cargas uniformes ao longo dos cabos; solo plano.

Convenções
  • x lateral (m) a partir do eixo da LT em estudo (+ à direita); y altura (m); z ao longo do eixo da LT em estudo.
  • Condutor: dict(nome, x, y, req [m], V [V eficaz fase-terra, complexo], I [A eficaz, complexo], tipo).
"""
import cmath
import math

import numpy as np

from pontos import T_EDIF, T_VIA

EPS0 = 8.8541878128e-12
MU0 = 4e-7 * math.pi
FASE_ANG = {"A": 0.0, "B": -120.0, "C": 120.0}

# Níveis de referência a 60 Hz: (E kV/m eficaz, B µT eficaz)
LIMITES = {"Público em geral": (4.17, 200.0), "Ocupacional": (8.33, 1000.0)}
LIMITES_FONTE = ("REN ANEEL nº 915/2021 (revoga as RENs 398/2010, 413/2010 e 616/2014), conforme o relatório ESS-2ITA-595-87 "
                 "(Energisa/IOSI): público 4,17 kV/m e 200 µT; ocupacional 8,33 kV/m e 1000 µT. NECESSITA VALIDAÇÃO com o texto oficial.")
H_OBS_PADRAO = 1.5


def fasor(mod, ang_graus=0.0):
    return mod * cmath.exp(1j * math.radians(ang_graus))


def tensao_fase(un_kv, fase, defas=0.0):
    """Tensão fase-terra (V eficaz) da fase A/B/C, sequência positiva."""
    return fasor(un_kv * 1000.0 / math.sqrt(3.0), FASE_ANG[fase] + defas)


def corrente_fase(i_a, fase, defas=0.0, fp=1.0, sentido=1.0):
    """Corrente (A eficaz) em fase com a tensão da própria fase (fp = 1) ou atrasada de acos(fp); sentido = ±1."""
    atraso = -math.degrees(math.acos(max(min(fp, 1.0), 0.0)))
    return sentido * fasor(i_a, FASE_ANG[fase] + defas + atraso)


# --------------------------------------------------------------------------- campo elétrico (simulação de cargas)
def matriz_potencial(xs, ys, req):
    xs, ys, req = (np.asarray(a, float) for a in (xs, ys, req))
    dx = xs[:, None] - xs[None, :]
    s = ys[:, None] + ys[None, :]
    d = ys[:, None] - ys[None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        P = np.log(np.sqrt(dx ** 2 + s ** 2) / np.sqrt(dx ** 2 + d ** 2)) / (2 * math.pi * EPS0)
    n = len(xs)
    for i in range(n):
        P[i, i] = math.log(2 * ys[i] / req[i]) / (2 * math.pi * EPS0)
    return P


def campo_e_cargas(q, xs, ys, X, Y):
    """Componentes (Ex, Ey) complexas em V/m nos pontos (X, Y) para as cargas q (C/m) e imagens em −y."""
    X, Y = np.asarray(X, float), np.asarray(Y, float)
    dx = X[..., None] - np.asarray(xs, float)
    dy1 = Y[..., None] - np.asarray(ys, float)
    dy2 = Y[..., None] + np.asarray(ys, float)
    r1 = np.maximum(dx ** 2 + dy1 ** 2, 1e-6)
    r2 = np.maximum(dx ** 2 + dy2 ** 2, 1e-6)
    k = np.asarray(q, complex) / (2 * math.pi * EPS0)
    ex = np.sum(k * (dx / r1 - dx / r2), axis=-1)
    ey = np.sum(k * (dy1 / r1 - dy2 / r2), axis=-1)
    return ex, ey


# --------------------------------------------------------------------------- campo magnético (Biot-Savart + imagens complexas)
def profundidade_complexa(rho, freq):
    """p = sqrt(ρ/(j ω μ0)) (m). ρ ≤ 0: solo condutor perfeito (p = 0)."""
    if not rho or rho <= 0:
        return 0.0 + 0.0j
    return cmath.sqrt(rho / (1j * 2 * math.pi * freq * MU0))


def campo_b_correntes(i, xs, ys, X, Y, p):
    """Componentes (Bx, By) complexas em T para as correntes i (A) em (xs, ys) e imagens em y' = −y − 2p com corrente oposta."""
    X, Y = np.asarray(X, float), np.asarray(Y, float)
    dx = X[..., None] - np.asarray(xs, float)
    dy1 = Y[..., None] - np.asarray(ys, float)
    dy2 = Y[..., None] + np.asarray(ys, float) + 2 * p           # = y − y'
    r1 = np.maximum(dx ** 2 + dy1 ** 2, 1e-6)
    r2 = dx ** 2 + dy2 ** 2
    r2 = np.where(np.abs(r2) < 1e-6, 1e-6, r2)
    k = np.asarray(i, complex) * MU0 / (2 * math.pi)
    bx = -np.sum(k * (dy1 / r1 - dy2 / r2), axis=-1)
    by = np.sum(k * (dx / r1 - dx / r2), axis=-1)
    return bx, by


# --------------------------------------------------------------------------- vizinhas: geometria na seção
def condutores_vizinha(v, y_ref=None):
    """Posições (x local, y) das fases da vizinha a partir da biblioteca: disp, n_circ, esp_h, esp_v, h_min, seq.
    x local é medido a partir do eixo da vizinha. Retorna lista de dict(fase, circuito, x, y)."""
    forma = v.get("disp", "Horizontal")
    eh, ev = float(v.get("esp_h") or 0.0), float(v.get("esp_v") or 0.0)
    h = float(y_ref if y_ref is not None else v.get("h_min") or 15.0)
    if forma == "Vertical":
        base = [(0.0, h), (0.0, h + ev), (0.0, h + 2 * ev)]
        deslocar = max(eh, 1.0)
    elif forma == "Triangular / livre":
        base = [(-eh / 2, h), (eh / 2, h), (0.0, h + ev)]
        deslocar = max(eh, 1.0)
    else:
        base = [(-eh, h), (0.0, h), (eh, h)]
        deslocar = 3.0 * max(eh, 1.0)
    seq = (v.get("seq") or "ABC")
    n_c = int(v.get("n_circ") or 1)
    out = []
    for c in range(n_c):
        off = 0.0 if n_c == 1 else (-deslocar / 2 if c == 0 else deslocar / 2)
        for (x, y), f in zip(base, seq):
            out.append(dict(fase=f, circuito=c + 1, x=x + off, y=y))
    return out


# --------------------------------------------------------------------------- sistema e campos
class Sistema:
    """LT em estudo + vizinhas em paralelo (mesma seção, acopladas eletricamente) + vizinhas em travessia (seção própria, ângulo α).
    est: lista de condutores da LT em estudo (inclui, se for o caso, guardas com V = 0 e I = 0).
    vizinhas: lista de dict(nome, modo 'paralelo'|'travessia', conds=[condutor com V, I], x0 (paralelo: posição do eixo),
              ang (travessia: ângulo entre eixos, graus))."""

    def __init__(self, est, vizinhas=(), rho=100.0, freq=60.0):
        self.est = list(est)
        self.vizs = list(vizinhas)
        self.p = profundidade_complexa(rho, freq)
        self.rho, self.freq = rho, freq
        grupo = list(self.est)
        self.fontes = [dict(nome="LT em estudo", tipo="est", idx=list(range(len(self.est))), ang=0.0)]
        for v in self.vizs:
            if v["modo"] == "paralelo":
                ini = len(grupo)
                cs = [dict(c, x=c["x"] + v.get("x0", 0.0)) for c in v["conds"]]
                grupo += cs
                self.fontes.append(dict(nome=v["nome"], tipo="par", idx=list(range(ini, len(grupo))), ang=0.0, viz=v))
            else:
                self.fontes.append(dict(nome=v["nome"], tipo="cruz", conds=v["conds"], ang=float(v.get("ang", 90.0)), viz=v))
        self.grupo = grupo
        self.xs = np.array([c["x"] for c in grupo])
        self.ys = np.array([c["y"] for c in grupo])
        self.req = np.array([c["req"] for c in grupo])
        self.Pinv = np.linalg.inv(matriz_potencial(self.xs, self.ys, self.req))
        self.V = np.array([c.get("V", 0.0) for c in grupo], complex)
        self.I = np.array([c.get("I", 0.0) for c in grupo], complex)

    # -- campos de cada fonte em (X, Y); devolve lista de (E[3], B[3]) complexos (x, y, z) por fonte
    def campos_fontes(self, X, Y):
        X, Y = np.asarray(X, float), np.asarray(Y, float)
        out = []
        for f in self.fontes:
            if f["tipo"] in ("est", "par"):
                m = np.zeros(len(self.grupo), bool)
                m[f["idx"]] = True
                q = self.Pinv @ np.where(m, self.V, 0.0)
                ex, ey = campo_e_cargas(q, self.xs, self.ys, X, Y)
                bx, by = campo_b_correntes(np.where(m, self.I, 0.0), self.xs, self.ys, X, Y, self.p)
                z = np.zeros_like(ex)
                out.append((np.array([ex, ey, z]), np.array([bx, by, z])))
            else:
                cs = f["conds"]
                xl = np.array([c["x"] for c in cs])
                yl = np.array([c["y"] for c in cs])
                rq = np.array([c["req"] for c in cs])
                Vv = np.array([c.get("V", 0.0) for c in cs], complex)
                Ii = np.array([c.get("I", 0.0) for c in cs], complex)
                q = np.linalg.solve(matriz_potencial(xl, yl, rq), Vv)
                a = math.radians(f["ang"])
                u = X * math.cos(a)                    # distância horizontal ao eixo da vizinha (perpendicular)
                eu, ey = campo_e_cargas(q, xl, yl, u, Y)
                bu, by = campo_b_correntes(Ii, xl, yl, u, Y, self.p)
                out.append((np.array([eu * math.cos(a), ey, -eu * math.sin(a)]),
                            np.array([bu * math.cos(a), by, -bu * math.sin(a)])))
        return out

    @staticmethod
    def combinar(campos, thetas, grandeza):
        """Soma fasorial das fontes com defasagem theta (graus) por fonte; retorna módulo eficaz resultante."""
        tot = 0
        for (e, b), th in zip(campos, thetas):
            tot = tot + (e if grandeza == "E" else b) * cmath.exp(1j * math.radians(th))
        return np.sqrt(np.sum(np.abs(tot) ** 2, axis=0))


def _pior_defasagem(campos, grandeza, alvo, passo=10.0, modos=None, informados=None):
    """Escolhe, por subida de coordenadas, as defasagens das vizinhas que maximizam max(campo[alvo]).
    modos[k] = 'pior' | 'informar' (defasagem fixa em informados[k]). Retorna (thetas, valor)."""
    n = len(campos)
    th = [0.0] * n
    for k in range(1, n):
        if modos and modos[k] == "informar":
            th[k] = float(informados[k])
    livres = [k for k in range(1, n) if not (modos and modos[k] == "informar")]
    ang = np.arange(0.0, 360.0, passo)

    def valor(t):
        return float(np.max(Sistema.combinar(campos, t, grandeza)[alvo]))
    for _ in range(3 if len(livres) > 1 else 1):
        for k in livres:
            melhor, mv = th[k], -1.0
            for a in ang:
                t = list(th)
                t[k] = float(a)
                v = valor(t)
                if v > mv + 1e-12:
                    mv, melhor = v, float(a)
            th[k] = melhor
    return th, valor(th)


def calcular_ponto(est, vizinhas, x_min=-50.0, x_max=50.0, dx=0.5, h_obs=H_OBS_PADRAO, rho=100.0, freq=60.0,
                   semi_faixa=None, x_pontos=None, modos=None, informados=None, passo_theta=10.0, y_max_3d=None):
    """Perfil lateral de E (kV/m) e B (µT) em h_obs, com pior caso de defasagem das vizinhas.
    semi_faixa: metade da largura da faixa (m) para o valor na borda; x_pontos: lista de |x| (m) de interesse (edificação, rodovia).
    modos/informados: por vizinha ('pior' ou 'informar' + graus), na ordem de `vizinhas`."""
    s = Sistema(est, vizinhas, rho, freq)
    xs = np.arange(x_min, x_max + dx / 2, dx)
    campos = s.campos_fontes(xs, np.full_like(xs, h_obs))
    n = len(campos)
    md = [None] + list(modos or ["pior"] * (n - 1))
    inf = [0.0] + list(informados or [0.0] * (n - 1))

    def idx_x(vals):
        return [int(np.argmin(np.abs(xs - v))) for v in vals]
    alvos = {"max": np.arange(len(xs))}
    if semi_faixa:
        alvos["borda"] = np.array(idx_x([-semi_faixa, semi_faixa]))
    if x_pontos:
        alvos["pontos"] = np.array(idx_x([-abs(v) for v in x_pontos] + [abs(v) for v in x_pontos]))
    r = dict(x=xs, h_obs=h_obs, fontes=[f["nome"] for f in s.fontes], rho=rho, freq=freq)
    for g, un, chave in (("E", 1e-3, "E"), ("B", 1e6, "B")):
        res = {}
        for nome, ia in alvos.items():
            th, v = _pior_defasagem(campos, g, ia, passo_theta, md, inf)
            res[nome] = (th, v * un)
        th_max = res["max"][0]
        perfil = Sistema.combinar(campos, th_max, g) * un
        isolado = Sistema.combinar(campos[:1], [0.0], g) * un
        r[chave] = perfil
        r[chave + "_est"] = isolado
        r[chave + "_max"] = float(np.max(perfil))
        r[chave + "_x_max"] = float(xs[int(np.argmax(perfil))])
        r[chave + "_theta"] = th_max
        if "borda" in res:
            r[chave + "_borda"], r[chave + "_borda_theta"] = res["borda"][1], res["borda"][0]
        if "pontos" in res:
            r[chave + "_pontos"], r[chave + "_pontos_theta"] = res["pontos"][1], res["pontos"][0]
    r["sistema"] = s
    r["campos"] = campos
    return r


def superficie_3d(r, grandeza, y_max, nx=61, ny=25):
    """Malha E(x, y) ou B(x, y) (kV/m ou µT) com a defasagem de pior caso do perfil r (usa só a região abaixo dos condutores)."""
    s = r["sistema"]
    xs = np.linspace(r["x"][0], r["x"][-1], nx)
    ys = np.linspace(0.2, y_max, ny)
    X, Y = np.meshgrid(xs, ys)
    campos = s.campos_fontes(X, Y)
    th = r[grandeza + "_theta"]
    v = Sistema.combinar(campos, th, grandeza) * (1e-3 if grandeza == "E" else 1e6)
    return xs, ys, v


# --------------------------------------------------------------------------- montagem a partir dos dados do app
def monta_estudo(fases, circs, guardas=None, incluir_guardas_e=False, h_min=None):
    """fases: lista de dict(x, y, circuito, fase, req) (coordenadas relativas ao eixo; y = altura média no vão).
    circs: {circ: dict(un_kv, i_a, fp, status)} ; guardas: lista de dict(x, y, req).
    h_min: se informado, desloca todos os condutores para que o mais baixo fique nesta altura (flecha em T máx.).
    Retorna lista de condutores com V (fase-terra) e I."""
    off = 0.0
    if h_min and fases:
        off = float(h_min) - min(f["y"] for f in fases)
    est = []
    for f in fases:
        c = circs.get(f["circuito"])
        if c is None:
            continue
        st = c.get("status", "Energizado")
        if st == "Desligado (isolado)":
            continue                                           # circuito flutuante: desprezado
        energ = st == "Energizado"
        V = tensao_fase(c["un_kv"], f["fase"]) if energ else 0.0     # desligado e aterrado: condutor a 0 V
        I = corrente_fase(c["i_a"], f["fase"], fp=c.get("fp", 1.0)) if energ else 0.0
        est.append(dict(nome=f.get("nome", f["fase"]), x=f["x"], y=f["y"] + off, req=f["req"], V=V, I=I, tipo="fase", fase=f["fase"],
                        circuito=f["circuito"]))
    if incluir_guardas_e and guardas:
        for g in guardas:
            est.append(dict(nome="Guarda", x=g["x"], y=g["y"] + off, req=g["req"], V=0.0, I=0.0, tipo="guarda"))
    return est


def monta_vizinha(v, y_est_min, y_est_max, i_a, defas=0.0, req=0.012):
    """Converte uma vizinha resolvida (pontos.pontos) em dict para Sistema.
    Travessia: 'LT em estudo cruza por cima' -> o topo da vizinha fica dist_v abaixo do condutor mais baixo da LT em estudo;
    caso contrário a base da vizinha fica dist_v acima do condutor mais alto. i_a: corrente por circuito (A) do cenário."""
    relacao = v.get("relacao", "Paralelismo")
    sentido = -1.0 if "oposto" in (v.get("sentido") or "").lower() else 1.0
    cs = condutores_vizinha(v, 0.0 if relacao == "Travessia" else None)
    if relacao == "Travessia":
        dv = float(v.get("dist_v") or 0.0)
        if "por cima" in (v.get("pos_rel") or ""):
            desloc = (y_est_min - dv) - max(c["y"] for c in cs)
        else:
            desloc = (y_est_max + dv) - min(c["y"] for c in cs)
        for c in cs:
            c["y"] += desloc
    conds = [dict(nome=f"{v['nome']} {c['fase']}{c['circuito']}", x=c["x"], y=c["y"], req=req,
                  V=tensao_fase(v["tensao"], c["fase"], defas), I=corrente_fase(i_a, c["fase"], defas, 1.0, sentido),
                  tipo="fase", fase=c["fase"], circuito=c["circuito"]) for c in cs]
    if relacao == "Paralelismo":
        x0 = float(v.get("dist_eixos") or 0.0) * (1.0 if v.get("lado", "Direito") == "Direito" else -1.0)
        return dict(nome=v["nome"], modo="paralelo", conds=conds, x0=x0)
    return dict(nome=v["nome"], modo="travessia", conds=conds, ang=float(v.get("ang_trav") or 90.0))


# --------------------------------------------------------------------------- estudo completo (entrada JSON-serializável)
CENARIOS = ("Normal", "Emergência")


def calcular_estudo(e):
    """Calcula E e B para todos os pontos e cenários. `e` é um dict JSON-serializável (ver app.entrada_m8).
    Retorna dict com 'pontos' (lista), 'erros', 'avisos', 'limites' e a geometria usada."""
    erros, avisos = [], []
    if not e.get("fases"):
        return dict(erros=["Geometria sem fases: preencha o Módulo 2 / seção transversal."], avisos=[], pontos=[])
    for k in ("1", "2"):
        c = e["circs"].get(k)
        if c and not c.get("un_kv"):
            erros.append(f"Tensão do circuito {k} não informada.")
    if erros:
        return dict(erros=erros, avisos=[], pontos=[])
    if not e.get("guardas"):
        avisos.append("Cabos guarda desprezados no campo magnético; no campo elétrico conforme a opção selecionada.")
    pts_out = []
    for p in e["pontos"]:
        res_p = dict(nome=p["nome"], tipo=p["tipo"], publico=p["publico"], cen_i=p["cen_i"], dist_h=p["dist_h"],
                     alt_ref=p["alt_ref"], vizinhas=[v["nome"] for v in p["vizinhas"]], cenarios={})
        puntual = p["tipo"] in (T_VIA, T_EDIF)
        h = float(p["alt_ref"]) if puntual and p["alt_ref"] > 0 else float(e["h_obs"])
        res_p["h_obs"] = h
        lim_e, lim_b = LIMITES[p["publico"]]
        res_p["lim_e"], res_p["lim_b"] = lim_e, lim_b
        for cen in CENARIOS:
            circs = {}
            for k, c in e["circs"].items():
                un = c["umax_kv"] if e["tensao_modo"] == "Máxima operativa" else c["un_kv"]
                circs[int(k)] = dict(un_kv=un, i_a=c["i_normal"] if cen == CENARIOS[0] else c["i_emerg"], fp=c["fp"], status=c["status"])
            est = monta_estudo(e["fases"], circs, e["guardas"], e["incluir_guardas_e"], e.get("h_min"))
            if not est:
                continue
            fz = [c for c in est if c.get("tipo") == "fase"]
            y_min, y_max = min(c["y"] for c in fz), max(c["y"] for c in fz)
            vizs, modos, inf = [], [], []
            for v in p["vizinhas"]:
                i_v = v["corrente_normal"] if cen == CENARIOS[0] else v["corrente_emergencia"]
                vizs.append(monta_vizinha(v, y_min, y_max, i_v, 0.0, e["req_viz"]))
                modos.append("informar" if v.get("defas_modo") == "Informar" else "pior")
                inf.append(float(v.get("defas") or 0.0))
            x_pts = [abs(p["dist_h"])] if puntual else None
            semi = None if puntual else (e.get("semi_faixa") or None)
            r = calcular_ponto(est, vizs, e["x_min"], e["x_max"], e["dx"], h, e["rho"], e["freq"], semi, x_pts, modos, inf,
                               e.get("passo_theta", 10.0))
            ref_e = r.get("E_pontos", r.get("E_borda"))
            ref_b = r.get("B_pontos", r.get("B_borda"))
            d = dict(x=r["x"].tolist(), E=r["E"].tolist(), B=r["B"].tolist(), E_est=r["E_est"].tolist(), B_est=r["B_est"].tolist(),
                     E_max=r["E_max"], B_max=r["B_max"], E_x_max=r["E_x_max"], B_x_max=r["B_x_max"],
                     E_ref=ref_e, B_ref=ref_b, theta_E=r["E_theta"], theta_B=r["B_theta"],
                     E_est_max=float(np.max(r["E_est"])), B_est_max=float(np.max(r["B_est"])),
                     fontes=r["fontes"], y_min=y_min, y_max=y_max, n_cond=len(est))
            d["ok_E"] = (ref_e if ref_e is not None else r["E_max"]) <= lim_e + 1e-9
            d["ok_B"] = (ref_b if ref_b is not None else r["B_max"]) <= lim_b + 1e-9
            d["max_ok_ocup"] = (r["E_max"] <= LIMITES["Ocupacional"][0] + 1e-9 and r["B_max"] <= LIMITES["Ocupacional"][1] + 1e-9)
            if cen == p["cen_i"]:
                ymax3 = max(y_min * 0.0 + 6.0, 4.0)
                for g in ("E", "B"):
                    xs3, ys3, v3 = superficie_3d(r, g, ymax3, 41, 13)
                    d["s3d_" + g] = dict(x=xs3.tolist(), y=ys3.tolist(), z=v3.tolist())
            res_p["cenarios"][cen] = d
        pts_out.append(res_p)
    return dict(erros=erros, avisos=avisos, pontos=pts_out, limites=LIMITES, freq=e["freq"], rho=e["rho"], h_obs=e["h_obs"],
                semi_faixa=e.get("semi_faixa"), tensao_modo=e["tensao_modo"], incluir_guardas_e=e["incluir_guardas_e"],
                x_min=e["x_min"], x_max=e["x_max"], req_viz=e["req_viz"], fases=e["fases"], guardas=e["guardas"], h_min=e.get("h_min"))
