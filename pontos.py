"""
Pontos de estudo e biblioteca de linhas/redes vizinhas — funções puras (sem Streamlit).

Classes de estudo
  A. ao longo da linha  (M2 parâmetros, M3 ventos, M5 isolamento, M6 aterramento, M7 condutor, M11 corona, M14, M15, M16):
     só interessa se o circuito é simples ou duplo (a mesma estrutura). NÃO usam vizinhas.
  B. pontual            (M4 distâncias/travessias, M8 campos elétrico e magnético, M10 RI/RA na borda da faixa).
  C. por trecho         (M9 interferência em dutos/ferrovias/telecom; faixa em corredor de LTs paralelas, M4).

Modelo de dados (tudo dentro de st.session_state["dados"], salvo por projeto, em JSON):
  "lib"        {"n": N}                      quantidade de linhas na biblioteca (máx. MAX_LIB)
  "lib{i}"     campos de LIB_DEF             uma linha/rede vizinha, reutilizável em vários pontos
  "pts"        {"n": N}                      quantidade de pontos de estudo (máx. MAX_PTS)
  "pt{i}"      campos de PT_DEF + "viz_ids" (índices da biblioteca) + "v{j}_<campo>" (posição relativa da vizinha j no ponto)
  "<módulo>"   {"pts_sel": [índices]}        pontos considerados em cada estudo
Os dados antigos ("viz", "viz0".."viz3": cadastro único com seleção por módulo) são convertidos por migrar_viz().
"""
import math

from geometria import FORMA_H

MAX_LIB, MAX_PTS = 8, 12

T_LIVRE = "Seção livre (vão)"
T_TRAV = "Travessia de LT/rede"
T_PAR = "Paralelismo com LT/rede"
T_VIA = "Rodovia/ferrovia"
T_EDIF = "Edificação/residência"
T_DUTO = "Duto/telecomunicações"
TIPOS = [T_LIVRE, T_TRAV, T_PAR, T_VIA, T_EDIF, T_DUTO]
TIPOS_COM_VIZINHA = (T_TRAV, T_PAR)

# tipos de ponto que cada estudo aceita
MOD_TIPOS = {
    4: TIPOS,
    8: [T_LIVRE, T_TRAV, T_PAR, T_VIA, T_EDIF],
    9: [T_PAR, T_VIA, T_DUTO],
    10: [T_LIVRE, T_PAR, T_EDIF],
}
MOD_CLASSE = {4: "pontual e por trecho", 8: "pontual", 9: "por trecho", 10: "pontual"}

CEN_I = ["Normal", "Emergência"]
DEFAS_PIOR = "Pior caso (automático)"
DEFAS_INF = "Informar"
SENT = ["Mesmo sentido da LT em estudo", "Sentido oposto"]
MODO_I = ["Informar corrente (A)", "A partir de P e Q"]

LIB_DEF = dict(nome="", tipo="Linha de transmissão", disp=FORMA_H, n_circ=1, esp_h=4.0, esp_v=0.0, h_min=15.0,
               tensao=138.0, modo_i=MODO_I[0], i_normal=0.0, p=0.0, q=0.0, i_emerg=0.0,
               sentido=SENT[0], seq="ABC", defas_modo=DEFAS_PIOR, defas=0.0)

PT_DEF = dict(nome="", tipo=T_LIVRE, local="", cen_i=CEN_I[0], dist_h=0.0, alt_ref=1.5, comp_par=1.0, ang_par=0.0, obs="")

REL_DEF = dict(lado="Direito", dist_eixos=30.0, comp_par=1.0, ang_par=0.0,
               pos_rel="LT em estudo cruza por cima", dist_trav_est=100.0, dist_v=5.0, ang_trav=90.0)


# --------------------------------------------------------------------------- biblioteca
def corrente_normal(l):
    """Corrente por circuito (A): informada, ou calculada de P e Q e da tensão nominal."""
    if l.get("modo_i") == MODO_I[1] and l.get("tensao", 0) > 0:
        return math.hypot(l.get("p", 0.0), l.get("q", 0.0)) * 1000.0 / (math.sqrt(3.0) * l["tensao"])
    return float(l.get("i_normal") or 0.0)


def corrente_emergencia(l):
    """Corrente de emergência (A); 0 informado = igual à normal."""
    return float(l.get("i_emerg") or 0.0) or corrente_normal(l)


def n_lib(dados):
    return max(0, min(MAX_LIB, int(dados.get("lib", {}).get("n", 0) or 0)))


def n_pts(dados):
    return max(0, min(MAX_PTS, int(dados.get("pts", {}).get("n", 0) or 0)))


def biblioteca(dados):
    out = []
    for i in range(n_lib(dados)):
        l = {k: dados.get(f"lib{i}", {}).get(k, d) for k, d in LIB_DEF.items()}
        l["nome"] = l["nome"] or f"Linha {i + 1}"
        l["i"] = i
        l["corrente_normal"] = corrente_normal(l)
        l["corrente_emergencia"] = corrente_emergencia(l)
        out.append(l)
    return out


# --------------------------------------------------------------------------- pontos
def pontos(dados):
    """Lista de pontos com as vizinhas já resolvidas (dados da biblioteca + posição relativa no ponto)."""
    lib = {l["i"]: l for l in biblioteca(dados)}
    out = []
    for i in range(n_pts(dados)):
        raw = dados.get(f"pt{i}", {})
        p = {k: raw.get(k, d) for k, d in PT_DEF.items()}
        p["nome"] = p["nome"] or f"Ponto {i + 1}"
        p["i"] = i
        p["vizinhas"], p["avisos"] = [], []
        if p["tipo"] in TIPOS_COM_VIZINHA:
            relacao = "Paralelismo" if p["tipo"] == T_PAR else "Travessia"
            ids = [j for j in raw.get("viz_ids", []) if isinstance(j, int)]
            for j in ids:
                if j not in lib:
                    p["avisos"].append(f"Vizinha #{j + 1} não existe mais na biblioteca.")
                    continue
                v = dict(lib[j])
                v.update({k: raw.get(f"v{j}_{k}", d) for k, d in REL_DEF.items()})
                v["relacao"] = relacao
                p["vizinhas"].append(v)
            if not p["vizinhas"]:
                p["avisos"].append("Selecione ao menos uma linha/rede vizinha da biblioteca.")
        out.append(p)
    return out


def selecionados(dados, mod):
    """Pontos escolhidos no estudo `mod` e compatíveis com ele."""
    ok = set(MOD_TIPOS.get(mod, TIPOS))
    sel = set(int(i) for i in dados.get(str(mod), {}).get("pts_sel", []) if str(i).lstrip("-").isdigit())
    return [p for p in pontos(dados) if p["i"] in sel and p["tipo"] in ok]


def resumo(dados, mod):
    """Linhas (rótulo, valor) para relatórios: pontos do estudo e suas vizinhas."""
    linhas = []
    for p in selecionados(dados, mod):
        txt = [p["tipo"]]
        if p["local"]:
            txt.append(f"local: {p['local']}")
        if p["tipo"] in TIPOS_COM_VIZINHA:
            for v in p["vizinhas"]:
                s = (f"{v['nome']} ({v['tensao']:g} kV, {v['corrente_normal']:.0f} A normal / "
                     f"{v['corrente_emergencia']:.0f} A emergência, {v['sentido'].lower()})")
                if p["tipo"] == T_PAR:
                    s += f"; d = {v['dist_eixos']:g} m, ângulo {v['ang_par']:g}°, comprimento {v['comp_par']:g} km"
                else:
                    s += f"; d horizontal = {v['dist_trav_est']:g} m, d vertical = {v['dist_v']:g} m, ângulo {v['ang_trav']:g}°"
                txt.append(s)
        elif p["tipo"] == T_DUTO:
            txt.append(f"d = {p['dist_h']:g} m, comprimento {p['comp_par']:g} km, ângulo {p['ang_par']:g}°")
        elif p["tipo"] != T_LIVRE:
            txt.append(f"d horizontal do eixo = {p['dist_h']:g} m, altura de referência {p['alt_ref']:g} m")
        txt.append(f"carga da LT em estudo: {p['cen_i']}")
        linhas.append((p["nome"], " · ".join(txt)))
    return linhas


# --------------------------------------------------------------------------- migração do cadastro antigo
def migrar_viz(dados):
    """Converte o cadastro antigo ('viz', 'viz0'..'viz3') em biblioteca + pontos. Idempotente; não perde dados.
    Retorna (dados, migrou: bool). Altera e devolve o mesmo dict."""
    antigo_n = int(dados.get("viz", {}).get("n", 0) or 0)
    tem_novo = "lib" in dados or "pts" in dados
    if antigo_n <= 0 or tem_novo:
        if not tem_novo:
            for k in [k for k in dados if k == "viz" or (k.startswith("viz") and k[3:].isdigit())]:
                dados.pop(k, None)
        return dados, False
    n = min(antigo_n, MAX_LIB)
    dados["lib"] = {"n": n}
    dados["pts"] = {"n": n}
    for i in range(n):
        o = dados.get(f"viz{i}", {})
        l = {k: o[k] for k in LIB_DEF if k in o}
        l["nome"] = o.get("nome") or f"Vizinha {i + 1}"
        if o.get("p") or o.get("q"):
            l["modo_i"] = MODO_I[1]
        if o.get("defas") not in (None, 0, 0.0):
            l["defas_modo"] = DEFAS_INF
        dados[f"lib{i}"] = l
        rel = o.get("relacao", "Paralelismo")
        pt = dict(nome=f"{l['nome']} ({'paralelismo' if rel == 'Paralelismo' else 'travessia'})",
                  tipo=T_PAR if rel == "Paralelismo" else T_TRAV, viz_ids=[i])
        pt.update({f"v{i}_{k}": o[k] for k in REL_DEF if k in o})
        dados[f"pt{i}"] = pt
    for k in [k for k in dados if k == "viz" or (k.startswith("viz") and k[3:].isdigit())]:
        dados.pop(k, None)
    for mod in list(dados):                                  # seleções por módulo (nomes) -> pontos
        sel = dados[mod].get("viz_sel") if isinstance(dados[mod], dict) else None
        if sel is not None:
            nomes = {dados[f"lib{i}"]["nome"]: i for i in range(n)}
            dados[mod]["pts_sel"] = [nomes[x] for x in sel if x in nomes]
            dados[mod].pop("viz_sel", None)
            dados[mod].pop("usar_viz", None)
    return dados, True
