"""
BK Engenharia — Software de Cálculos de Linhas de Transmissão
FASE 1 (v2): Interface (layout + entrada de dados). SEM banco de dados.

- Dados em st.session_state (persistem ao trocar de módulo; somem ao recarregar a página).
- Persistência (Neon/Postgres) só será criada após autorização.
- Geometria da seção transversal: geometria.py (funções puras, testáveis).

Executar:  streamlit run app.py
"""
import copy
import datetime as dt
import math
import os

import pandas as pd
import streamlit as st

import db
import pontos as PT
import calc_ventos as cv
import mod2_calc
import calc_condutor as cc_mod
try:
    import relatorio_m2
    import relatorio_m3
    ERRO_RELATORIO = None
except ImportError as _e:      # app abre mesmo sem python-docx/matplotlib; só o relatório fica indisponível
    relatorio_m2 = relatorio_m3 = None
    ERRO_RELATORIO = f"{_e}. Instale com: pip install -r requirements.txt"
from geometria import (
    C2_ESPELHO, C2_TRANSL, FORMA_H, FORMA_T, FORMA_V, FORMAS, FORMAS_C2,
    SEQUENCIAS, montar_geometria, planta_vizinha,
)

# ----------------------------------------------------------------------------
# Configuração geral e tema (azul, cinza, branco, preto)
# ----------------------------------------------------------------------------
st.set_page_config(page_title="BK | Cálculos de LT", page_icon="⚡",
                   layout="wide", initial_sidebar_state="expanded")

# Impede a tradução automática do navegador (Chrome/Google Tradutor): ela altera o DOM e quebra o React do Streamlit
# com "NotFoundError: removeChild", além de traduzir rótulos ("Catálogo de cabos" → "entrar de cabos").
try:
    import streamlit.components.v1 as _components
    _components.html("""<script>
    try {
      const d = window.parent.document;
      d.documentElement.setAttribute('translate', 'no');
      d.documentElement.setAttribute('lang', 'pt-BR');
      d.body.classList.add('notranslate');
      if (!d.querySelector('meta[name="google"]')) {
        const m = d.createElement('meta'); m.name = 'google'; m.content = 'notranslate'; d.head.appendChild(m);
      }
    } catch (e) {}
    </script>""", height=0)
except Exception:
    pass

AZUL, AZUL_CLARO = "#0B3C74", "#1F6FB8"
CINZA, CINZA_ESC, PRETO = "#F3F5F8", "#5B6573", "#12161C"

st.markdown(
    f"""
    <style>
      .stApp {{ background:#FFFFFF; color:{PRETO}; }}
      [data-testid="stSidebar"] {{ background:{PRETO}; }}
      [data-testid="stSidebar"] * {{ color:#E8ECF1 !important; }}
      [data-testid="stSidebar"] [data-baseweb="select"] *,
      [data-testid="stSidebar"] [data-baseweb="input"] *,
      [data-testid="stSidebar"] .react-aria-ComboBox,
      [data-testid="stSidebar"] .react-aria-ComboBox * {{
          color:{PRETO} !important; -webkit-text-fill-color:{PRETO} !important; }}
      .bk-header {{ background:linear-gradient(90deg,{AZUL},{AZUL_CLARO});
          color:#fff; padding:18px 24px; border-radius:12px; margin-bottom:18px; }}
      .bk-header h1 {{ margin:0; font-size:1.6rem; color:#fff; }}
      .bk-header p  {{ margin:2px 0 0 0; opacity:.85; font-size:.9rem; }}
      .bk-card {{ background:{CINZA}; border-left:5px solid {AZUL_CLARO};
          padding:14px 18px; border-radius:8px; margin-bottom:12px; }}
      .bk-card small {{ color:{CINZA_ESC}; }}
      div[data-testid="stMetric"] {{ background:{CINZA}; padding:10px 14px; border-radius:8px; }}
      .stButton button, [data-testid="stFormSubmitButton"] button {{
          background:{AZUL}; color:#fff !important; border:0; border-radius:8px; }}
      .stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {{
          background:{AZUL_CLARO}; color:#fff !important; }}
      .stButton button:disabled {{ background:#2B3441; color:#8B95A3 !important; opacity:.7; }}
      [data-testid="stSidebar"] [data-testid="stExpander"] {{ border:1px solid #2D3643; border-radius:8px; }}
      [data-testid="stSidebar"] [data-testid="stExpander"] summary {{ background:#1B222C !important; }}
      [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {{ background:#232C38 !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

MODULOS = [
    ("1. Dados do Projeto e Sistema", "📁"),
    ("2. Parâmetros Elétricos", "🔌"),
    ("3. Estudo dos Ventos", "🌬️"),
    ("4. Faixa de Domínio", "📐"),
    ("5. Coordenação e Isolamento", "🛡️"),
    ("6. Aterramento", "⏚"),
    ("7. Dimensionamento do Condutor e Cabo Guarda", "🧵"),
    ("8. Campo Elétrico e Magnético", "🧲"),
    ("9. Interferência e Compatibilidade Eletromagnética", "📡"),
    ("10. RI e RA", "🔊"),
    ("11. Efeito Corona", "✨"),
    ("12. Isolamento e Tensão Máxima Operativa", "🔋"),
    ("13. Ampacidade e Flecha Máxima", "🌡️"),
    ("14. Rejeição de Carga", "📉"),
    ("15. Religamento Tripolar", "🔁"),
    ("16. Blindagem contra Descargas Atmosféricas", "⚡"),
]

NORMAS = {
    2: "Equações de Carson e coeficientes de potencial de Maxwell; NBR 5422; modelo π (livros do acervo)",
    3: "ABNT NBR 5422:2024 (vento – Gumbel, Tabelas 1 a 3, 8 e 9; temperaturas 3.1.49 a 3.1.55; massa específica 4.7); dados INMET",
    4: "ABNT NBR 5422:2024 (7.2, 7.3, 8.9, 9.4.1 e Seção 17); planilha BK (aba Faixa de Servidão)",
    5: "ABNT NBR 5422:2024 (4.5 a 4.8, Seção 9, 14.2, Anexo C); Diretrizes de projeto básico (3.2.13, 4.7, 6.8); livro Projeto Elétrico de LTs (4.6, 4.7); IEC 60099 (para-raios, a validar)",
    6: "IEEE Std 80-2013 (seção do condutor, passo/toque); Dwight/Sunde (contrapeso); CIGRE/IEEE (impulso); livros do acervo; planilha BK (aba Aterramento)",
    7: "ONS NT Sazonal de LTs; IEEE Std 738-2006; IEC 60949 (curto-circuito); NBR 5422:2024 (Seção 5/21, a confirmar); planilha BK",
    8: "ICNIRP 2010 / Res. ANEEL 616/2014 (limites de exposição)",
    9: "CISPR 18 / IEEE 1260 / ITU-T K-series",
    10: "CISPR 18-2, IEEE Std 430 (rádio interferência e ruído audível)",
    11: "Peek (Livro 2, 3.2.5–3.2.6; Livro 3, cap. 7); Kiessling 2.3.3 e 7.3.4 (gradiente e perdas corona)",
    12: "ABNT NBR 5422:2024 (seção 9, Anexo C); Diretrizes 3.2.13, 4.7, 6.8; IEC 60038/60071-1 (a validar)",
    13: "IEEE Std 738-2006; mudança de estado (parábola, planilha BK); NBR 5422 (distância ao solo, a validar)",
    14: "Triagem analítica 60 Hz (ABCD + Thévenin); Diretrizes 3.2.5, 3.2.6, 8.4 (estudo EMT/ATP não substituído)",
    15: "Triagem analítica (energização com carga residual); Diretrizes 3.2.5–3.2.7, 8.4 (estudo EMT/ATP não substituído)",
    16: "Kiessling cap. 4 (EGM, D = 6,7·I^0,8); Diretrizes de projeto básico (metas de desligamentos); IEEE 1243/CIGRE (a validar)",
}

# ----------------------------------------------------------------------------
# Estado da sessão e helpers de widgets com persistência
# ----------------------------------------------------------------------------
ss = st.session_state

CFG_DEF = dict(n_circ=1, cabos_fase=1, esp_sub=400.0, n_cg=1, cond=None, cg1=None, cg2=None,
               forma_c1=FORMA_H, forma_c2=C2_TRANSL, seq_c2="ABC")
GEO_DEF = dict(h_cg1=30.0, esp_cg_h=6.0, dif_cg_v=0.0, ga_dx=-4.5, ga_dy=6.0,
               d12x=4.5, d23x=4.5, d12y=3.0, d23y=3.0,
               circ_dx=10.0, circ_dy=0.0, f_cond=0.0, f_cg=0.0)

def init_state():
    ss.setdefault("dados", {})
    ss.setdefault("proj_id", None)      # id do projeto aberto/salvo no banco (None = ainda não salvo)


try:
    db.init_db()
except Exception as e:                  # DATABASE_URL inválida, arquivo sem permissão etc.
    st.error(f"Não foi possível abrir o banco de dados: {e}")
    st.stop()
init_state()
PT.migrar_viz(ss["dados"])      # projetos antigos: cadastro 'viz' -> biblioteca + pontos


def G(ns, nome, default=None):
    return ss["dados"].get(ns, {}).get(nome, default)


def S(ns, nome, valor):
    ss["dados"].setdefault(ns, {})[nome] = valor
    return valor


def _k(ns, nome):
    """Chave do widget. O sufixo de versão força o navegador a descartar o valor antigo (ao abrir projeto/limpar),
    senão o valor velho do widget volta ao app e sobrescreve os dados carregados."""
    v = ss.get("_ver", 0)
    return f"k_{ns}_{nome}" + (f"_v{v}" if v else "")


def nova_versao_widgets():
    ss["_ver"] = ss.get("_ver", 0) + 1


def num(ns, nome, label, default, minv=None, maxv=None, step=None, fmt=None, c=None, help=None):
    """number_input que lembra o valor ao trocar de módulo."""
    c = c or st
    ss.setdefault("_rot", {})[(ns, nome)] = label
    val = G(ns, nome, default)
    ints = isinstance(default, int) and all(x is None or isinstance(x, int) for x in (minv, maxv, step))
    if not ints:
        val = float(val)
        minv = None if minv is None else float(minv)
        maxv = None if maxv is None else float(maxv)
        step = None if step is None else float(step)
    if minv is not None:
        val = max(val, minv)
    if maxv is not None:
        val = min(val, maxv)
    out = c.number_input(label, min_value=minv, max_value=maxv, value=val, step=step,
                         format=fmt, key=_k(ns, nome), help=help)
    return S(ns, nome, out)


def sel(ns, nome, label, opcoes, default=None, c=None, help=None):
    c = c or st
    ss.setdefault("_rot", {})[(ns, nome)] = label
    val = G(ns, nome, default if default is not None else opcoes[0])
    idx = opcoes.index(val) if val in opcoes else 0
    return S(ns, nome, c.selectbox(label, opcoes, index=idx, key=_k(ns, nome), help=help))


def chk(ns, nome, label, default=False, c=None):
    c = c or st
    ss.setdefault("_rot", {})[(ns, nome)] = label
    return S(ns, nome, c.checkbox(label, value=G(ns, nome, default), key=_k(ns, nome)))


def txt(ns, nome, label, default="", c=None):
    c = c or st
    ss.setdefault("_rot", {})[(ns, nome)] = label
    return S(ns, nome, c.text_input(label, value=G(ns, nome, default), key=_k(ns, nome)))


def limpar(*namespaces):
    for ns in namespaces:
        ss["dados"].pop(ns, None)
        for k in [k for k in ss.keys() if k.startswith(f"k_{ns}_")]:
            del ss[k]
    nova_versao_widgets()


# ----------------------------------------------------------------------------
# Catálogo de cabos (vem do banco)
# ----------------------------------------------------------------------------
PLACEHOLDER = "— selecione —"
USOS_CHAVE = {"condutores": ("CONDUTOR",), "guardas": db.USOS_GUARDA, "contrapeso": ("CONTRAPESO",)}


def codigos(chave):
    return db.codigos_cabos(USOS_CHAVE[chave])


def sel_cabo(ns, nome, label, chave, c=None):
    c = c or st
    lista = db.listar_cabos(USOS_CHAVE[chave])
    if not lista:
        c.selectbox(label, ["— nenhum cabo no catálogo —"], disabled=True, key=_k(ns, nome + "_vazio"))
        return S(ns, nome, None)
    rotulo = {x["codigo"]: x["codigo"] + (f"  ·  {x['tipo']}" if x["tipo"] else "")
              + (f"  ·  {x['secao_mm2']:g} mm²" if x["secao_mm2"] else "") for x in lista}
    opcoes = [PLACEHOLDER] + list(rotulo)
    atual = G(ns, nome)
    if atual and atual not in rotulo:
        c.warning(f"O cabo '{atual}' não existe mais no catálogo.")
    idx = opcoes.index(atual) if atual in opcoes else 0
    v = c.selectbox(label, opcoes, index=idx, key=_k(ns, nome),
                    format_func=lambda x: x if x == PLACEHOLDER else rotulo[x])
    return S(ns, nome, None if v == PLACEHOLDER else v)


def info_cabos():
    """Tabela dos cabos selecionados no projeto (somente leitura)."""
    pares = [(f"Condutor – {circuito(i)['nome']}", circuito(i)["cond"]) for i in range(1, int(G("cfg", "n_circ", 1)) + 1)]
    pares.append(("Cabo guarda 1", G("cfg", "cg1")))
    if G("cfg", "n_cg", 1) == 2:
        pares.append(("Cabo guarda 2", G("cfg", "cg2")))
    linhas, sem_rmg = [], []
    for papel, cod in pares:
        p = db.obter_cabo(cod)
        if cod and p.get("rmg_mm") is None:
            sem_rmg.append(cod)
        linhas.append({"Função": papel, "Código": cod or "— não selecionado —",
                       "Seção (mm²)": p.get("secao_mm2"), "Diâmetro (mm)": p.get("diametro_mm"),
                       "R_cc 20 °C (Ω/km)": p.get("r_cc_20"), "RMG (mm)": p.get("rmg_mm"),
                       "RTC (kN)": p.get("rtc_kn")})
    st.dataframe(pd.DataFrame(linhas), hide_index=True)
    if any(l["Código"] == "— não selecionado —" for l in linhas):
        st.warning("Há cabos não selecionados. Escolha no Módulo 1 → Circuitos / Configuração da LT.")
    if sem_rmg:
        st.warning("RMG não cadastrado para: " + ", ".join(sem_rmg) +
                   ". Necessário para reatância e corona; cadastre em Módulo 2 → Catálogo de cabos → Editar cabo.")
    alertas = [c for c in (cod for _, cod in pares) if c and db.obter_cabo(c).get("alerta_importacao")]
    for cod in alertas:
        st.warning(f"{cod}: {db.obter_cabo(cod)['alerta_importacao']}")


# ----------------------------------------------------------------------------
# Geometria e vizinhas
# ----------------------------------------------------------------------------
def geometria_atual():
    d = {k: G("cfg", k, v) for k, v in CFG_DEF.items()}
    d.update({k: G("geo", k, v) for k, v in GEO_DEF.items()})
    if d["n_cg"] != 2:
        d["esp_cg_h"] = d["dif_cg_v"] = 0.0
    return montar_geometria(d)


C_DEF = dict(nome="", un=138.0, umax=145.0, mva=100.0, fp=0.95, i_lim=0.0, cond=None, cabos_fase=1,
             esp_sub=400.0, status="Energizado")
STATUS_CIRC = ["Energizado", "Desligado (isolado)", "Desligado e aterrado nas pontas"]


def circuito(i):
    """Dados elétricos do circuito i (1 ou 2). Projetos antigos (seção 'sis'/'cfg') servem de fallback."""
    d = dict(C_DEF)
    d["un"], d["umax"], d["mva"] = G("sis", "un", d["un"]), G("sis", "umax", d["umax"]), G("sis", "mva", d["mva"])
    d["cond"], d["cabos_fase"], d["esp_sub"] = G("cfg", "cond"), G("cfg", "cabos_fase", 1), G("cfg", "esp_sub", 400.0)
    d.update({k: v for k, v in ss["dados"].get(f"c{i}", {}).items() if v is not None})
    d["nome"] = d.get("nome") or f"Circuito {i}"
    return d


def corrente_nominal(i=1):
    c = circuito(i)
    return c["mva"] * 1000.0 / (math.sqrt(3) * c["un"]) if c["un"] > 0 else 0.0


def mostrar_plotly(fig):
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


def desenho_secao(res):
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.caption("Instale plotly para ver o desenho da seção transversal (pip install plotly).")
        return
    cond = res["condutores"]
    fig = go.Figure()
    xs, ys = [k["x"] for k in cond], [k["y"] for k in cond]
    fig.add_shape(type="line", x0=min(xs) - 6, x1=max(xs) + 6, y0=0, y1=0,
                  line=dict(color=CINZA_ESC, width=3))
    estilos = [("guarda", None, PRETO, "diamond"), ("fase", 1, AZUL, "circle"), ("fase", 2, AZUL_CLARO, "circle")]
    for tipo, circ, cor, simb in estilos:
        pts = [k for k in cond if k["tipo"] == tipo and k["circuito"] == circ]
        if pts:
            fig.add_trace(go.Scatter(
                x=[k["x"] for k in pts], y=[k["y"] for k in pts], mode="markers+text",
                text=[k["nome"] for k in pts], textposition="top center",
                marker=dict(size=13, color=cor, symbol=simb),
                name="Cabo guarda" if tipo == "guarda" else f"Circuito {circ}",
                hovertemplate="%{text}<br>x = %{x:.2f} m<br>altura = %{y:.2f} m<extra></extra>"))
    fig.add_vline(x=res["eixo_x"], line_dash="dot", line_color=CINZA_ESC,
                  annotation_text="eixo da LT", annotation_position="bottom")
    fig.update_layout(template="plotly_white", height=460, margin=dict(l=10, r=10, t=20, b=10),
                      xaxis_title="x (m) — origem no cabo guarda 1",
                      yaxis_title="Altura na estrutura (m)",
                      yaxis=dict(scaleanchor="x", scaleratio=1, range=[0, max(ys) + 5]))
    mostrar_plotly(fig)


def desenho_planta(relacao, ang, dist_h, lado="Direito", dist_v=None, pos_rel=None):
    """Croqui em PLANTA da LT em estudo × vizinha (paralelismo ou travessia)."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        return
    seg = planta_vizinha(relacao, ang, dist_h, lado)
    fig = go.Figure()
    x0, y0, x1, y1 = seg["lt"]
    fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines", name="LT em estudo",
                             line=dict(color=AZUL, width=4)))
    x0, y0, x1, y1 = seg["viz"]
    fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines", name="Vizinha",
                             line=dict(color=CINZA_ESC, width=4, dash="dash")))
    if relacao == "Travessia":
        ex, ey = seg["estrutura"]
        fig.add_trace(go.Scatter(x=[ex], y=[ey], mode="markers+text", text=["Estrutura mais próxima"],
                                 textposition="bottom center", name="Estrutura",
                                 marker=dict(size=12, color=PRETO, symbol="square")))
        fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers", name="Ponto de travessia",
                                 marker=dict(size=12, color="#C0392B", symbol="x")))
        fig.add_annotation(x=ex / 2, y=0, ay=-35, ax=0, text=f"distância horizontal = {dist_h:.1f} m",
                           showarrow=True, arrowhead=0)
        gap = f" · folga vertical = {dist_v:.1f} m ({pos_rel})" if dist_v is not None else ""
        titulo = f"Planta — travessia, ângulo entre circuitos = {ang:.1f}°{gap}"
    else:
        yy = -dist_h if lado == "Direito" else dist_h
        fig.add_annotation(x=0, y=yy / 2, text=f"distância entre eixos = {dist_h:.1f} m", showarrow=False)
        titulo = f"Planta — paralelismo, ângulo entre eixos = {ang:.1f}° (lado {lado.lower()})"
    fig.update_layout(template="plotly_white", height=300, title=dict(text=titulo, font=dict(size=13)),
                      margin=dict(l=10, r=10, t=40, b=10),
                      xaxis_title="ao longo da LT em estudo (m)", yaxis_title="transversal (m)",
                      yaxis=dict(scaleanchor="x", scaleratio=1))
    mostrar_plotly(fig)


# ----------------------------------------------------------------------------
# Projetos (persistência)
# ----------------------------------------------------------------------------
def titulo_projeto(p):
    return f"#{p['id']} · {p['numero'] or 's/nº'} · {p['nome'] or 'sem nome'}"


def salvar_projeto_atual(novo=False):
    meta = {k: G("proj", k) for k in ("nome", "cliente", "numero", "revisao")}
    pid = db.salvar_projeto(None if novo else ss.get("proj_id"), meta, copy.deepcopy(ss["dados"]))
    ss["proj_id"] = pid
    return pid


def abrir_projeto(pid):
    dados = db.carregar_projeto(pid)
    if dados is None:
        return False
    ss["dados"] = PT.migrar_viz(dados)[0]
    for k in [k for k in ss.keys() if k.startswith("k_")]:     # força os widgets a reler os valores
        del ss[k]
    nova_versao_widgets()
    ss["proj_id"] = pid
    ss.pop("_hash_salvo", None)
    return True


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚡ BK Engenharia")
    st.caption("Cálculos de Linhas de Transmissão")
    nomes_mod = [f"{ic}  {nm}" for nm, ic in MODULOS]
    escolha = st.radio("Módulos", nomes_mod, key="modulo_sel", label_visibility="collapsed")
    idx = nomes_mod.index(escolha) + 1
    st.divider()
    st.caption("Projeto ativo")
    st.write(f"**{G('proj', 'nome') or '— não definido —'}**")
    st.caption(f"{G('proj', 'cliente') or '—'} | Nº {G('proj', 'numero') or '—'}")
    st.caption(f"{G('cfg', 'n_circ', 1)} circuito(s) · {G('cfg', 'n_cg', 1)} cabo(s) guarda · "
               f"{G('cfg', 'forma_c1', FORMA_H)}")
    cabos_ok = all(circuito(i)["cond"] for i in range(1, int(G("cfg", "n_circ", 1)) + 1)) and bool(G("cfg", "cg1")) and (
        G("cfg", "n_cg", 1) == 1 or bool(G("cfg", "cg2")))
    st.caption("Cabos: ✅ selecionados" if cabos_ok else "Cabos: ⏳ pendentes de cadastro/seleção")
    if db.eh_sqlite():
        st.warning(f"⚠️ Banco LOCAL (SQLite) · {db.contar_cabos()} cabos. Os dados NÃO estão no Neon.")
    else:
        st.success(f"☁️ Banco na nuvem (Postgres/Neon)\n\nServidor: {db.descricao_banco()} · {db.contar_cabos()} cabos")

    # --- Projetos salvos no banco ---
    with st.expander("💾 Projetos (banco de dados)", expanded=bool(ss.get("_msg"))):
        msg = ss.pop("_msg", None)
        if msg:
            st.success(msg)
        st.caption(f"Aberto: projeto #{ss['proj_id']}" if ss.get("proj_id") else "Aberto: ainda não salvo")
        projs = db.listar_projetos()
        mapa = {titulo_projeto(p): p["id"] for p in projs}
        escolha_p = st.selectbox("Projetos salvos", list(mapa) or ["— nenhum projeto salvo —"],
                                 key="sel_proj_salvo", disabled=not mapa)
        b1, b2 = st.columns(2)
        if b1.button("Abrir", disabled=not mapa, key="btn_abrir"):
            try:
                ok_abrir = abrir_projeto(mapa[escolha_p])
            except Exception as e_abrir:        # mostra o motivo em vez de falhar em silêncio
                import traceback
                ok_abrir = False
                st.error(f"Falha ao abrir o projeto: {type(e_abrir).__name__}: {e_abrir}")
                st.code(traceback.format_exc()[-1500:])
            else:
                if ok_abrir:
                    ss["_msg"] = f"Projeto #{mapa[escolha_p]} aberto."
                    ss["_toast"] = f"Projeto «{G('proj', 'nome') or mapa[escolha_p]}» aberto."
                    st.rerun()
                else:
                    st.error("Projeto não encontrado no banco (pode ter sido excluído ou o banco é outro).")
        if b2.button("Salvar", key="btn_salvar", help="Atualiza o projeto aberto (ou cria, se ainda não salvo)."):
            ss["_acao_salvar"] = "atual"
        if st.button("Salvar como novo", key="btn_salvar_novo"):
            ss["_acao_salvar"] = "novo"
        conf = st.checkbox("Confirmar exclusão do selecionado", key="conf_del", disabled=not mapa)
        if st.button("Excluir selecionado", disabled=not (mapa and conf), key="btn_excluir"):
            pid_del = mapa[escolha_p]
            db.excluir_projeto(pid_del)
            if ss.get("proj_id") == pid_del:
                ss["proj_id"] = None
            ss["_msg"] = f"Projeto #{pid_del} excluído."
            del ss["conf_del"]
            st.rerun()

if ss.get("_toast"):
    st.toast(ss.pop("_toast"), icon="✅")

# ----------------------------------------------------------------------------
# Cabeçalho
# ----------------------------------------------------------------------------
st.markdown(
    f"""<div class="bk-header"><h1>{MODULOS[idx - 1][1]} {MODULOS[idx - 1][0]}</h1>
    <p>{G('proj', 'nome') or 'Projeto sem nome'} · {' / '.join(f"{circuito(i)['un']:.0f}" for i in range(1, int(G('cfg', 'n_circ', 1)) + 1))} kV ·
    {G('sis', 'km', 50.0):.1f} km · {G('cfg', 'n_circ', 1)} circuito(s)</p></div>""",
    unsafe_allow_html=True,
)
if idx in NORMAS:
    st.markdown(f'<div class="bk-card"><small>Normas de referência</small><br>{NORMAS[idx]}</div>',
                unsafe_allow_html=True)


def aviso_calculo():
    st.info("🔧 Fórmulas e resultados deste módulo serão implementados na próxima etapa. "
            "Esta tela contém a interface de entrada de dados.")


SECOES_M1 = [("proj", "Projeto"), ("sis", "Sistema"), ("cfg", "Configuração da LT"), ("c1", "Circuito 1"), ("c2", "Circuito 2")]


def bloco_relatorio_generico(mod, implementado=False):
    """Botões de relatório (.docx e PDF) para módulos sem relatório próprio: registra os dados de entrada e os itens pendentes."""
    nome_mod = MODULOS[mod - 1][0]
    nss = SECOES_M1 if mod == 1 else [(str(mod), "Dados de entrada")]
    secoes = []
    for ns, tit in nss:
        linhas = []
        for k, v in ss["dados"].get(ns, {}).items():
            if k.startswith("_") or k in ("viz_sel", "pts_sel") or v is None:
                continue
            linhas.append((ss.get("_rot", {}).get((ns, k), k.replace("_", " ")), v))
        if ns == "proj" or linhas or mod != 1:
            secoes.append((tit, linhas))
    if mod in PT.MOD_TIPOS:
        secoes.append(("Pontos de estudo considerados", PT.resumo(ss["dados"], mod) or [("Pontos", "nenhum ponto selecionado")]))
    st.markdown("**Relatório (padrão BK) e impressão**")

    def _gg(caminho):
        import relatorio_generico
        proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
        relatorio_generico.gerar(caminho, proj, mod, nome_mod.split(". ", 1)[-1], NORMAS.get(mod, "—"), secoes, implementado,
                                 codigo=(G("proj", "numero") or "BK-LT-MC") + f"-M{mod}", rev=G("proj", "revisao") or "R0")
    if ERRO_RELATORIO:
        st.error(ERRO_RELATORIO)
        return
    if st.button("Gerar relatório (.docx, padrão BK)", key=f"btn_rel_m{mod}"):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            caminho = os.path.join(td, "relatorio.docx")
            _gg(caminho)
            with open(caminho, "rb") as fh:
                ss[f"_rel_m{mod}"] = fh.read()
    if ss.get(f"_rel_m{mod}"):
        st.download_button(f"Baixar relatório do Módulo {mod} (.docx)", ss[f"_rel_m{mod}"],
                           file_name=f"Relatorio_Modulo{mod}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"dl_rel_m{mod}")
    botao_imprimir(f"m{mod}", f"Relatorio_Modulo{mod}.pdf", _gg)
    if not implementado:
        st.caption("O cálculo deste módulo ainda não está implementado: o relatório registra os dados de entrada e marca os itens como PENDENTE.")


def botoes(mod, *extra_ns, so_limpar=False):
    """so_limpar=True nos módulos já implementados: o cálculo fica na aba própria, só resta o botão Limpar.
    Nos demais, o relatório genérico (dados de entrada + pendências) aparece acima dos botões."""
    if not so_limpar:
        bloco_relatorio_generico(mod)
    c1, c2, _ = st.columns([1, 1, 4])
    if not so_limpar and c1.button("Calcular", key=f"calc{mod}"):
        st.warning("Cálculo ainda não implementado nesta fase.")
    if c2.button("Limpar", key=f"clr{mod}"):
        limpar(str(mod), *extra_ns)
        st.rerun()


# ----------------------------------------------------------------------------
# Módulo 1 — Dados do Projeto e Sistema
# ----------------------------------------------------------------------------
def tab_circuitos():
    n = int(G("cfg", "n_circ", 1))
    st.caption("Cada circuito tem alimentação, tensão, carga, condutor e feixe próprios. O comprimento e a "
               "frequência são comuns (aba Sistema). Os Módulos 2, 5, 8, 10–15 leem estes dados.")
    cols = st.columns(n)
    for i in range(1, n + 1):
        ns, c0 = f"c{i}", circuito(i)
        with cols[i - 1]:
            st.markdown(f"##### Circuito {i}")
            txt(ns, "nome", "Nome / alimentação (ex.: SE Origem → SE Destino)", f"Circuito {i}")
            a, b = st.columns(2)
            num(ns, "un", "Tensão nominal (kV)", c0["un"], 13.8, 800.0, 1.0, c=a)
            num(ns, "umax", "Tensão máxima operativa (kV)", c0["umax"], 13.8, 850.0, 1.0, c=b)
            a, b = st.columns(2)
            num(ns, "mva", "Potência na carga (MVA)", c0["mva"], 0.0, 5000.0, 10.0, c=a)
            num(ns, "fp", "Fator de potência (indutivo)", c0["fp"], 0.1, 1.0, 0.01, c=b)
            num(ns, "i_lim", "Limite de corrente / ampacidade (A) — 0 = usar o catálogo", 0.0, 0.0, 5000.0, 10.0)
            sel_cabo(ns, "cond", "Condutor de fase", "condutores")
            a, b = st.columns(2)
            sel(ns, "cabos_fase", "Cabos por fase", [1, 2, 3, 4], default=c0["cabos_fase"], c=a)
            if G(ns, "cabos_fase", c0["cabos_fase"]) > 1:
                num(ns, "esp_sub", "Espaçamento entre subcondutores (mm)", c0["esp_sub"], 50.0, 1500.0, 10.0, c=b,
                    help="Convenção: 2 = horizontal; 3 = triângulo equilátero; 4 = quadrado.")
            sel(ns, "status", "Estado do circuito", STATUS_CIRC,
                help="Desligado/aterrado é usado nos estudos de indução do circuito vizinho (energizado).")
            st.metric("Corrente nominal", f"{corrente_nominal(i):.1f} A")
    if n == 2:
        if st.button("Copiar dados do circuito 1 para o circuito 2", key="btn_copia_c"):
            ss["dados"]["c2"] = {k: v for k, v in circuito(1).items() if k != "nome"}
            for k in [k for k in ss.keys() if k.startswith("k_c2_")]:
                del ss[k]
            nova_versao_widgets()
            st.rerun()


def mod1():
    t1, t2, t3, t4 = st.tabs(["Projeto", "Sistema", "Configuração da LT", "Circuitos"])
    with t1:
        c1, c2 = st.columns(2)
        txt("proj", "cliente", "Cliente", c=c1)
        txt("proj", "nome", "Nome do projeto", c=c2)
        c3, c4, c5 = st.columns(3)
        txt("proj", "numero", "Número do projeto", c=c3)
        S("proj", "data", c4.date_input("Data", value=G("proj", "data", dt.date.today()), key=_k("proj", "data")))
        txt("proj", "revisao", "Revisão", "R0", c=c5)
        txt("proj", "resp", "Responsável técnico (CREA)")
    with t2:
        c1, c2, c3 = st.columns(3)
        num("sis", "un", "Tensão nominal (kV)", 138.0, 13.8, 800.0, 1.0, c=c1)
        num("sis", "umax", "Tensão máxima operativa (kV)", 145.0, 13.8, 850.0, 1.0, c=c2)
        sel("sis", "freq", "Frequência (Hz)", [60, 50], c=c3)
        c4, c5, c6 = st.columns(3)
        num("sis", "mva", "Potência por circuito (MVA) — padrão p/ circuitos", 100.0, 1.0, 5000.0, 10.0, c=c4)
        num("sis", "km", "Comprimento (km)", 50.0, 0.1, 1000.0, 1.0, c=c5)
        c6.caption("Tensão/potência acima são o padrão inicial. Valores próprios de cada circuito: aba **Circuitos**.")
    with t3:
        st.caption("A configuração escolhida aqui define quais campos de geometria aparecem no Módulo 2.")
        a, b, c = st.columns(3)
        n_circ = sel("cfg", "n_circ", "Nº de circuitos", [1, 2], c=a)
        st.markdown("##### Cabos guarda")
        d, e, f = st.columns(3)
        n_cg = sel("cfg", "n_cg", "Nº de cabos guarda", [1, 2], c=e)
        sel_cabo("cfg", "cg1", "Cabo guarda 1", "guardas", c=f)
        if n_cg == 2:
            sel_cabo("cfg", "cg2", "Cabo guarda 2", "guardas", c=d)
        if not codigos("guardas"):
            st.info("Catálogo de cabos vazio. Rode `python importar_cabos.py <planilha.xlsm>` ou cadastre em "
                    "Módulo 2 → Catálogo de cabos.")
        st.markdown("##### Disposição das fases (decisão de projeto)")
        g, h, i = st.columns(3)
        sel("cfg", "forma_c1", "Arranjo das fases do circuito 1", list(FORMAS), c=g)
        if n_circ == 2:
            sel("cfg", "forma_c2", "Forma do circuito 2", list(FORMAS_C2), c=h)
            sel("cfg", "seq_c2", "Sequência de fases do circuito 2 (posições 1', 2', 3')",
                list(SEQUENCIAS), c=i, help="Circuito 1 é sempre A-B-C nas posições 1, 2, 3.")
    with t4:
        tab_circuitos()
    st.divider()
    bloco_relatorio_generico(1, implementado=True)
    st.success("Para gravar ou reabrir este projeto, use **💾 Projetos (banco de dados)** na barra lateral.")


# ----------------------------------------------------------------------------
# Módulo 2 — Parâmetros Elétricos (geometria, vizinhas, catálogo)
# ----------------------------------------------------------------------------
def tab_geometria():
    n_circ, n_cg = G("cfg", "n_circ", 1), G("cfg", "n_cg", 1)
    forma = G("cfg", "forma_c1", FORMA_H)
    st.caption(f"Configuração do projeto: {n_circ} circuito(s), {n_cg} cabo(s) guarda, arranjo **{forma}**. "
               "Altere no Módulo 1 → Configuração da LT. Valores iniciais são ilustrativos — substitua pelos dados do projeto.")
    st.caption("Convenções: origem em x no cabo guarda 1; x positivo à direita; distâncias verticais "
               "informadas \"abaixo\" (positivo = mais baixo); alturas medidas na estrutura.")

    with st.expander("📘 Como a geometria é calculada (convenções e fórmulas)"):
        st.markdown(
            """
**Referencial.** Origem de *x* no cabo guarda 1; *x* positivo à direita; *y* = altura em relação ao solo,
medida **na estrutura** (ponto de fixação). Os deslocamentos verticais são informados como "abaixo do ponto
anterior": coordenada nova **y = y anterior − distância vertical**.

**Cadeia de posicionamento** (cada ponto nasce do anterior, sem dado redundante):
1. Guarda 1 → altura informada. Guarda 2 (se houver) = Guarda 1 + (distância horizontal; −diferença de altura).
2. Fase **A1** = Guarda 1 + (distância horizontal; −distância vertical informadas "fase A × guarda 1").
3. **B1** = A1 + deslocamento A→B; **C1** = B1 + deslocamento B→C.
   Horizontal: só Δx (Δy = 0). Vertical: só Δy (Δx = 0). Triangular/livre: Δx e Δy livres.
4. Circuito 2: posição **1'** = posição 1 (A1) + (distância horizontal entre circuitos; −distância vertical entre circuitos).
   Posições 2' e 3' repetem os deslocamentos do circuito 1 (**translação**) ou com Δx de sinal invertido (**espelhada**).
   As letras das fases em 1', 2', 3' seguem a sequência escolhida no Módulo 1.

**Conferência da distância entre circuitos.** A medida de projeto é posição 1 ↔ posição 1'. Abaixo o app também mostra
a distância entre os **baricentros** dos circuitos e a **menor distância entre fases** de circuitos diferentes.

**Altura média no vão** (usada nos cálculos elétricos): h_média = h_estrutura − (2/3) × flecha.

**Distância entre condutores:** d = √(Δx² + Δy²), com as coordenadas na estrutura.

**Ângulo de blindagem** (guarda → fase): θ = arctan(|Δx| / Δy_vertical), medido a partir da vertical do cabo guarda.

*Exemplo:* guarda a 30,00 m e fase A a (−4,50 m; 6,00 m abaixo) ⇒ A1 = (−4,50; 24,00) e θ = arctan(4,5/6,0) = 36,87°.
            """
        )

    st.markdown("##### Cabo(s) guarda")
    a, b, c = st.columns(3)
    num("geo", "h_cg1", "Altura do cabo guarda 1 (m)", GEO_DEF["h_cg1"], 1.0, 250.0, 0.1, c=a)
    if n_cg == 2:
        num("geo", "esp_cg_h", "Distância horizontal entre guardas (m)", GEO_DEF["esp_cg_h"], 0.0, 80.0, 0.1, c=b)
        num("geo", "dif_cg_v", "Guarda 2 abaixo do guarda 1 (m)", GEO_DEF["dif_cg_v"], -30.0, 30.0, 0.1, c=c)

    st.markdown("##### Fase A do circuito 1 em relação ao cabo guarda 1")
    a, b, _ = st.columns(3)
    num("geo", "ga_dx", "Distância horizontal (m) (+ direita / − esquerda)", GEO_DEF["ga_dx"], -100.0, 100.0, 0.1, c=a)
    num("geo", "ga_dy", "Distância vertical abaixo do guarda (m)", GEO_DEF["ga_dy"], 0.0, 100.0, 0.1, c=b)

    st.markdown(f"##### Fases do circuito 1 — arranjo {forma}")
    a, b, c, d = st.columns(4)
    if forma == FORMA_H:
        num("geo", "d12x", "Distância horizontal A–B (m)", GEO_DEF["d12x"], 0.0, 60.0, 0.1, c=a)
        num("geo", "d23x", "Distância horizontal B–C (m)", GEO_DEF["d23x"], 0.0, 60.0, 0.1, c=b)
        st.caption("Arranjo horizontal: distância vertical entre fases = 0 (fixo).")
    elif forma == FORMA_V:
        num("geo", "d12y", "Distância vertical A–B (m)", GEO_DEF["d12y"], 0.0, 60.0, 0.1, c=a)
        num("geo", "d23y", "Distância vertical B–C (m)", GEO_DEF["d23y"], 0.0, 60.0, 0.1, c=b)
        st.caption("Arranjo vertical: distância horizontal entre fases = 0 (fixo).")
    else:
        num("geo", "d12x", "A→B horizontal (m) (+ direita)", GEO_DEF["d12x"], -60.0, 60.0, 0.1, c=a)
        num("geo", "d12y", "A→B vertical abaixo (m)", GEO_DEF["d12y"], -60.0, 60.0, 0.1, c=b)
        num("geo", "d23x", "B→C horizontal (m) (+ direita)", GEO_DEF["d23x"], -60.0, 60.0, 0.1, c=c)
        num("geo", "d23y", "B→C vertical abaixo (m)", GEO_DEF["d23y"], -60.0, 60.0, 0.1, c=d)

    if n_circ == 2:
        st.markdown("##### Distância entre circuitos (posição 1 do circuito 1 → posição 1' do circuito 2)")
        a, b, _ = st.columns(3)
        num("geo", "circ_dx", "Distância horizontal entre circuitos (m)", GEO_DEF["circ_dx"], -80.0, 80.0, 0.1, c=a)
        num("geo", "circ_dy", "Distância vertical entre circuitos, abaixo (m)", GEO_DEF["circ_dy"], -80.0, 80.0, 0.1, c=b)
        st.caption(f"Forma do circuito 2: {G('cfg', 'forma_c2', C2_TRANSL)} · sequência {G('cfg', 'seq_c2', 'ABC')}.")

    st.markdown("##### Flechas (para altura média no vão)")
    a, b, _ = st.columns(3)
    num("geo", "f_cond", "Flecha do condutor (m)", GEO_DEF["f_cond"], 0.0, 80.0, 0.1, c=a,
        help="Altura média = altura na estrutura − 2/3 × flecha.")
    num("geo", "f_cg", "Flecha do cabo guarda (m)", GEO_DEF["f_cg"], 0.0, 80.0, 0.1, c=b)

    st.markdown("##### Dados complementares")
    a, b, _ = st.columns(3)
    num("2", "rho", "Resistividade do solo (Ω·m)", 1000.0, 1.0, 20000.0, 10.0, c=a)
    chk("2", "transp", "Linha transposta", True, c=b)

    res = geometria_atual()
    for m in res["erros"]:
        st.error(m)
    for m in res["avisos"]:
        st.warning(m)
    if not res["erros"]:
        st.markdown("##### Coordenadas resultantes (com a origem de cada ponto)")
        linhas = [{"Condutor": k["nome"], "x (m)": round(k["x"], 3),
                   "Altura na estrutura (m)": round(k["y"], 3),
                   "Altura média no vão (m)": round(k["y_med"], 3),
                   "Como foi obtido": k["derivacao"]} for k in res["condutores"]]
        st.dataframe(pd.DataFrame(linhas), hide_index=True)

        rs = res["resumo"]
        st.markdown("##### Conferência das medidas")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Largura entre fases externas", f"{rs['largura_fases']:.2f} m")
        if "min_c1" in rs:
            m2.metric("Menor distância entre fases (circ. 1)", f"{rs['min_c1']:.2f} m")
        if "baricentros" in rs:
            bc = rs["baricentros"]
            m3.metric("Entre circuitos: baricentros", f"{bc['d']:.2f} m",
                      help=f"Δx = {bc['dx']:+.2f} m; Δy = {bc['dy']:+.2f} m")
            m4.metric("Menor distância entre fases de circuitos distintos", f"{rs['min_entre_circuitos']:.2f} m")
        with st.expander("Distâncias entre todos os condutores (m)"):
            nomes_c = [k["nome"] for k in res["condutores"]]
            mat = pd.DataFrame(0.0, index=nomes_c, columns=nomes_c)
            for a_, b_, d_ in res["distancias"]:
                mat.loc[a_, b_] = mat.loc[b_, a_] = round(d_, 3)
            st.dataframe(mat)

        st.markdown("##### Ângulo de blindagem (guarda → fase, em relação à vertical)")
        st.dataframe(pd.DataFrame(res["angulos"]), hide_index=True)
        desenho_secao(res)
    st.divider()
    st.caption("Parâmetros ao longo da linha: consideram só o circuito simples ou duplo da própria estrutura. "
               "Linhas paralelas e travessias são tratadas nos estudos pontuais (Módulos 4, 8, 9 e 10).")
    st.caption("O cálculo dos parâmetros elétricos e o relatório estão na aba **Cálculo e relatório**.")
    botoes(2, "geo", so_limpar=True)


def editor_biblioteca():
    st.markdown("##### 📚 Biblioteca de linhas e redes vizinhas")
    st.caption("Cadastre cada linha/rede **uma vez**; ela pode ser usada em vários pontos de estudo. Informe tensão e corrente por circuito: "
               "a corrente de emergência em branco (0) assume a normal. A defasagem entre sistemas, quando desconhecida, "
               "é varrida automaticamente (pior caso) nos estudos de campo.")
    n = num("lib", "n", f"Quantidade de linhas/redes na biblioteca (máx. {PT.MAX_LIB})", 0, 0, PT.MAX_LIB, 1)
    for i in range(int(n)):
        ns = f"lib{i}"
        with st.expander(f"Linha/rede {i + 1} — {G(ns, 'nome', f'Linha {i + 1}')}", expanded=(int(n) == 1)):
            a, b, c = st.columns(3)
            txt(ns, "nome", "Identificação", f"Linha {i + 1}", c=a)
            sel(ns, "tipo", "Tipo", ["Linha de transmissão", "Rede de distribuição"], c=b)
            num(ns, "tensao", "Tensão nominal (kV)", PT.LIB_DEF["tensao"], 0.1, 800.0, 1.0, c=c)
            st.markdown("**Geometria**")
            a, b, c, d = st.columns(4)
            sel(ns, "disp", "Disposição das fases", list(FORMAS), c=a)
            sel(ns, "n_circ", "Nº de circuitos", [1, 2], c=b)
            num(ns, "esp_h", "Espaçamento horizontal entre fases (m)", PT.LIB_DEF["esp_h"], 0.0, 60.0, 0.1, c=c)
            num(ns, "esp_v", "Espaçamento vertical entre fases (m)", PT.LIB_DEF["esp_v"], 0.0, 60.0, 0.1, c=d)
            num(ns, "h_min", "Altura média da fase mais baixa (m)", PT.LIB_DEF["h_min"], 1.0, 100.0, 0.1)
            st.markdown("**Carga por circuito**")
            a, b, c, d = st.columns(4)
            modo = sel(ns, "modo_i", "Como informar a corrente normal", PT.MODO_I, c=a)
            if modo == PT.MODO_I[0]:
                num(ns, "i_normal", "Corrente normal (A)", 0.0, 0.0, 10000.0, 10.0, c=b)
            else:
                p_ = num(ns, "p", "P (MW)", 0.0, 0.0, 5000.0, 1.0, c=b)
                q_ = num(ns, "q", "Q (Mvar)", 0.0, -5000.0, 5000.0, 1.0, c=c)
                v_ = G(ns, "tensao", PT.LIB_DEF["tensao"])
                d.metric("Corrente normal", f"{math.hypot(p_, q_) * 1000 / (math.sqrt(3) * v_):.1f} A")
            num(ns, "i_emerg", "Corrente de emergência (A; 0 = igual à normal)", 0.0, 0.0, 10000.0, 10.0, c=(c if modo == PT.MODO_I[0] else a))
            sel(ns, "sentido", "Sentido do fluxo", PT.SENT)
            with st.expander("Avançado: fase relativa à LT em estudo"):
                a, b, c = st.columns(3)
                sel(ns, "seq", "Sequência de fases da vizinha", ["ABC", "ACB"], c=a)
                dm = sel(ns, "defas_modo", "Defasagem angular entre os sistemas", [PT.DEFAS_PIOR, PT.DEFAS_INF], c=b)
                if dm == PT.DEFAS_INF:
                    num(ns, "defas", "Defasagem (°)", 0.0, -180.0, 180.0, 1.0, c=c)


def editor_pontos():
    st.markdown("##### 📍 Pontos de estudo")
    st.caption("Cada ponto é um local da linha a estudar (um vão, uma travessia, um trecho paralelo, uma edificação...). "
               "Os pontos são compartilhados: o que for cadastrado aqui aparece nos outros estudos pontuais.")
    n = num("pts", "n", f"Quantidade de pontos de estudo (máx. {PT.MAX_PTS})", 0, 0, PT.MAX_PTS, 1)
    lib = PT.biblioteca(ss["dados"])
    nome_lib = {l["i"]: l["nome"] for l in lib}
    for i in range(int(n)):
        ns = f"pt{i}"
        with st.expander(f"Ponto {i + 1} — {G(ns, 'nome', f'Ponto {i + 1}')}", expanded=(int(n) == 1)):
            a, b, c = st.columns(3)
            txt(ns, "nome", "Identificação", f"Ponto {i + 1}", c=a)
            tipo = sel(ns, "tipo", "Tipo de ponto", PT.TIPOS, c=b)
            txt(ns, "local", "Localização (km / estruturas)", c=c)
            sel(ns, "cen_i", "Carga da LT em estudo neste ponto", PT.CEN_I, c=a)
            if tipo in PT.TIPOS_COM_VIZINHA:
                if not lib:
                    st.info("Cadastre antes a linha/rede vizinha na biblioteca (acima).")
                    S(ns, "viz_ids", [])
                    continue
                opc = [l["i"] for l in lib]
                atual = [j for j in G(ns, "viz_ids", []) if j in opc]
                esc = st.multiselect("Linhas/redes vizinhas neste ponto", opc, default=atual,
                                     format_func=lambda j: nome_lib.get(j, f"#{j + 1}"), key=_k(ns, "viz_ids_w"))
                S(ns, "viz_ids", esc)
                for j in esc:
                    st.markdown(f"**{nome_lib[j]} — posição relativa à LT em estudo**")
                    a, b, c, d = st.columns(4)
                    if tipo == PT.T_PAR:
                        sel(ns, f"v{j}_lado", "Lado", ["Direito", "Esquerdo"], c=a)
                        num(ns, f"v{j}_dist_eixos", "Distância horizontal entre eixos (m)", PT.REL_DEF["dist_eixos"], 0.0, 5000.0, 0.5, c=b)
                        num(ns, f"v{j}_comp_par", "Comprimento do paralelismo (km)", PT.REL_DEF["comp_par"], 0.0, 1000.0, 0.1, c=c)
                        num(ns, f"v{j}_ang_par", "Ângulo entre eixos (°)", PT.REL_DEF["ang_par"], 0.0, 90.0, 0.5, c=d, help="0° = paralelas.")
                        desenho_planta("Paralelismo", G(ns, f"v{j}_ang_par", 0.0), G(ns, f"v{j}_dist_eixos", PT.REL_DEF["dist_eixos"]),
                                       G(ns, f"v{j}_lado", "Direito"))
                    else:
                        sel(ns, f"v{j}_pos_rel", "Posição no cruzamento", ["LT em estudo cruza por cima", "LT em estudo cruza por baixo"], c=a)
                        num(ns, f"v{j}_dist_trav_est", "Distância horizontal: travessia → estrutura mais próxima (m)",
                            PT.REL_DEF["dist_trav_est"], 0.0, 5000.0, 1.0, c=b)
                        num(ns, f"v{j}_dist_v", "Distância vertical entre condutores (m)", PT.REL_DEF["dist_v"], 0.0, 200.0, 0.1, c=c,
                            help="Folga entre o condutor mais baixo da linha de cima e o mais alto da linha de baixo, no cruzamento.")
                        num(ns, f"v{j}_ang_trav", "Ângulo entre os circuitos (°)", PT.REL_DEF["ang_trav"], 0.0, 90.0, 0.5, c=d,
                            help="Ângulo agudo entre os eixos em planta (90° = perpendicular).")
                        desenho_planta("Travessia", G(ns, f"v{j}_ang_trav", 90.0), G(ns, f"v{j}_dist_trav_est", PT.REL_DEF["dist_trav_est"]),
                                       dist_v=G(ns, f"v{j}_dist_v", PT.REL_DEF["dist_v"]), pos_rel=G(ns, f"v{j}_pos_rel", "LT em estudo cruza por cima"))
            elif tipo == PT.T_LIVRE:
                st.caption("Seção livre: só a própria LT (altura e carga da geometria do Módulo 2), sem vizinhas.")
            elif tipo == PT.T_DUTO:
                a, b, c = st.columns(3)
                num(ns, "dist_h", "Distância horizontal do eixo ao duto/telecom (m)", 50.0, 0.0, 5000.0, 1.0, c=a)
                num(ns, "comp_par", "Comprimento do paralelismo (km)", 1.0, 0.0, 1000.0, 0.1, c=b)
                num(ns, "ang_par", "Ângulo entre eixos (°)", 0.0, 0.0, 90.0, 0.5, c=c)
            else:
                a, b, _ = st.columns(3)
                num(ns, "dist_h", "Distância horizontal do eixo ao ponto de interesse (m)", 20.0, 0.0, 5000.0, 0.5, c=a)
                num(ns, "alt_ref", "Altura de referência acima do solo (m)", 1.5, 0.0, 30.0, 0.1, c=b)
            txt(ns, "obs", "Observação")


def bloco_pontos(mod):
    """Biblioteca + pontos (cadastro central compartilhado) e escolha dos pontos considerados no estudo `mod`."""
    ns = str(mod)
    st.caption(f"Estudo **{PT.MOD_CLASSE[mod]}**: considera linhas paralelas, travessias e demais interferências em cada ponto, "
               "com a tensão e a corrente de cada linha envolvida.")
    editor_biblioteca()
    st.divider()
    editor_pontos()
    st.divider()
    st.markdown("##### ✅ Pontos considerados neste estudo")
    todos = [p for p in PT.pontos(ss["dados"]) if p["tipo"] in PT.MOD_TIPOS[mod]]
    if not todos:
        st.info("Nenhum ponto cadastrado de tipo compatível com este estudo. Tipos aceitos: " + "; ".join(PT.MOD_TIPOS[mod]) + ".")
        S(ns, "pts_sel", [])
        return []
    opc = [p["i"] for p in todos]
    nome = {p["i"]: f"{p['nome']} — {p['tipo']}" for p in todos}
    atual = [j for j in G(ns, "pts_sel", opc) if j in opc]
    esc = st.multiselect("Quais pontos considerar", opc, default=atual, format_func=lambda j: nome[j], key=_k(ns, "pts_sel_w"))
    S(ns, "pts_sel", esc)
    sel_pts = PT.selecionados(ss["dados"], mod)
    if sel_pts:
        st.dataframe(pd.DataFrame([{"Ponto": p["nome"], "Tipo": p["tipo"], "Local": p["local"], "Carga da LT": p["cen_i"],
                                    "Vizinhas (tensão · corrente normal/emergência)":
                                        "; ".join(f"{v['nome']} ({v['tensao']:g} kV · {v['corrente_normal']:.0f}/{v['corrente_emergencia']:.0f} A)"
                                                  for v in p["vizinhas"]) or "—"} for p in sel_pts]), hide_index=True)
    for p in sel_pts:
        for m in p["avisos"]:
            st.warning(f"{p['nome']}: {m}")
    return sel_pts


CAT_COLS = {
    "codigo": "Código", "uso": "Uso", "tipo": "Tipo", "formacao": "Formação", "secao_mm2": "Seção (mm²)",
    "diametro_mm": "Diâmetro (mm)", "massa_kg_m": "Massa (kg/m)", "rtc_kn": "RTC (kN)",
    "r_cc_20": "R_cc 20 °C (Ω/km)", "r_ca_75": "R_ca 75 °C (Ω/km)", "ampacidade_a": "Ampacidade (A)",
    "modulo_gpa": "Módulo (GPa)", "dilatacao_1e6": "Dilatação (10⁻⁶/°C)", "rmg_mm": "RMG (mm)",
    "fornecedor": "Fornecedor", "alerta_importacao": "Alerta",
}
# (campo, rótulo, passo) — editáveis no formulário
CAT_NUM = [("secao_mm2", "Seção (mm²)"), ("diametro_mm", "Diâmetro externo (mm)"), ("massa_kg_m", "Massa (kg/m)"),
           ("rtc_kn", "RTC – carga de ruptura (kN)"), ("ampacidade_a", "Ampacidade 75 °C (A)"),
           ("r_cc_20", "R_cc 20 °C (Ω/km)"), ("r_ca_75", "R_ca 60 Hz 75 °C (Ω/km)"),
           ("modulo_gpa", "Módulo de elasticidade final (GPa)"), ("dilatacao_1e6", "Dilatação linear (10⁻⁶/°C)"),
           ("rmg_mm", "RMG (mm)")]


def _campos_num(c, chave):
    """Renderiza os campos numéricos do cabo em 3 colunas e devolve {campo: valor}."""
    out, cols = {}, st.columns(3)
    for i, (campo, rot) in enumerate(CAT_NUM):
        out[campo] = cols[i % 3].number_input(rot, min_value=0.0, value=c.get(campo), format="%g",
                                              key=f"cat_{chave}_{campo}")
    return out


def tab_catalogo():
    msg = ss.pop("_msg_cat", None)
    if msg:
        st.success(msg)
    st.caption(f"Fonte: {db.descricao_banco()}. Valores importados da planilha (aba 'Data Base') e "
               "convertidos para SI (kN, GPa). Reimportar a planilha reaplica os valores dela, "
               "preservando RMG e observações.")
    if db.contar_cabos() == 0:
        st.warning("Catálogo vazio. Rode: python importar_cabos.py \"<caminho>/LINHA DE TRANSMISSÃO 4.xlsm\"")
        return

    f1, f2, f3 = st.columns([2, 2, 3])
    usos = f1.multiselect("Uso", list(db.USOS), key="cat_f_uso", placeholder="Todos")
    tipos = f2.multiselect("Tipo", db.tipos_cabos(), key="cat_f_tipo", placeholder="Todos")
    busca = f3.text_input("Buscar pelo código", key="cat_f_busca")
    todos = db.listar_cabos()
    lista = db.listar_cabos(usos or None, tipos or None, busca or None)

    m1, m2, m3 = st.columns(3)
    m1.metric("Cabos no filtro", f"{len(lista)} de {len(todos)}")
    m2.metric("Com alerta de qualidade", sum(1 for x in todos if x["alerta_importacao"]))
    m3.metric("Sem RMG cadastrado", sum(1 for x in todos if x["rmg_mm"] is None))

    if lista:
        df = pd.DataFrame(lista)[list(CAT_COLS)].rename(columns=CAT_COLS)
        st.dataframe(df, hide_index=True, height=380)
    else:
        st.info("Nenhum cabo para o filtro atual.")

    with st.expander("⚠️ Pendências de qualidade dos dados"):
        pend = [{"Código": x["codigo"], "Alerta": x["alerta_importacao"]} for x in todos if x["alerta_importacao"]]
        if pend:
            st.dataframe(pd.DataFrame(pend), hide_index=True)
            st.caption("Os valores foram importados exatamente como estão na planilha. Corrija em 'Editar cabo' "
                       "depois de conferir com o catálogo do fabricante.")
        else:
            st.success("Sem alertas.")

    with st.expander("✏️ Editar cabo (cadastrar RMG, corrigir valores)"):
        cods = [x["codigo"] for x in lista] or [x["codigo"] for x in todos]
        cod = st.selectbox("Cabo", cods, key="cat_ed_cod")
        c = db.obter_cabo(cod)
        if c:
            st.caption(f"Origem: {c['origem']}")
            if c["alerta_importacao"]:
                st.warning(c["alerta_importacao"])
            ch = f"{cod}_{c['atualizado_em']:%Y%m%d%H%M%S%f}"      # muda quando o registro muda
            with st.form(f"cat_form_ed_{ch}"):
                t1, t2 = st.columns(2)
                tipo = t1.text_input("Tipo", value=c["tipo"] or "", key=f"cat_{ch}_tipo")
                form = t2.text_input("Formação", value=c["formacao"] or "", key=f"cat_{ch}_form")
                vals = _campos_num(c, ch)
                obs = st.text_input("Observação", value=c["observacao"] or "", key=f"cat_{ch}_obs")
                resolvido = st.checkbox("Marcar alerta de importação como resolvido",
                                        disabled=not c["alerta_importacao"], key=f"cat_{ch}_res")
                if st.form_submit_button("Salvar alterações"):
                    d = {"codigo": cod, "uso": c["uso"], "tipo": tipo or None, "formacao": form or None,
                         "observacao": obs or None, **vals}
                    for k in ("rtc_kgf", "modulo_kgf_mm2"):      # recalculados a partir de kN / GPa
                        d[k] = None
                    if resolvido:
                        d["alerta_importacao"] = None
                    db.salvar_cabo(d)
                    ss["_msg_cat"] = f"Cabo '{cod}' atualizado."
                    st.rerun()
            if c["origem"] == "manual":
                if st.checkbox("Confirmar exclusão deste cabo (cadastrado manualmente)", key=f"cat_{cod}_del"):
                    if st.button("Excluir cabo", key=f"cat_{cod}_delbtn"):
                        db.excluir_cabo(cod)
                        ss["_msg_cat"] = f"Cabo '{cod}' excluído."
                        st.rerun()
            else:
                st.caption("Cabos importados da planilha não são excluídos pelo app.")

    with st.expander("➕ Adicionar cabo"):
        with st.form("cat_form_novo", clear_on_submit=True):
            n1, n2, n3 = st.columns(3)
            codigo = n1.text_input("Código (único)", key="cat_novo_codigo")
            uso = n2.selectbox("Uso", list(db.USOS), key="cat_novo_uso")
            tipo = n3.text_input("Tipo", key="cat_novo_tipo")
            vals = _campos_num({}, "novo")
            if st.form_submit_button("Cadastrar cabo"):
                codigo = codigo.strip()
                if not codigo:
                    st.error("Informe o código do cabo.")
                elif db.obter_cabo(codigo):
                    st.error(f"Já existe um cabo com o código '{codigo}'.")
                else:
                    db.salvar_cabo({"codigo": codigo, "uso": uso, "tipo": tipo or None, "origem": "manual", **vals})
                    ss["_msg_cat"] = f"Cabo '{codigo}' cadastrado."
                    st.rerun()


def calcular_m2():
    """Executa o motor do Módulo 2 com os dados atuais. Retorna (resultado, geo, erros)."""
    geo = geometria_atual()
    erros = list(geo["erros"])
    n = int(G("cfg", "n_circ", 1))
    circs = {i: circuito(i) for i in range(1, n + 1)}
    for i, c in circs.items():
        if not c["cond"]:
            erros.append(f"Selecione o condutor do circuito {i} (caixa \"Cabos e dados de entrada do cálculo\" acima).")
    gcods = [G("cfg", "cg1")] + ([G("cfg", "cg2")] if G("cfg", "n_cg", 1) == 2 else [])
    if not all(gcods):
        erros.append("Selecione os cabos guarda (caixa \"Cabos e dados de entrada do cálculo\" acima).")
    if erros:
        return None, geo, erros
    gcab = [db.obter_cabo(c) for c in gcods]
    res = mod2_calc.calcular(geo, circs, gcab, G("sis", "km", 50.0), float(G("sis", "freq", 60)),
                             G("2", "rho", 1000.0), obter_cabo=db.obter_cabo)
    return (res, gcab), geo, []


def pdf_impressao(gerar_fn):
    """Gera o relatório em versão PDF para impressão (equações em texto linear). gerar_fn(caminho) cria o .docx."""
    import tempfile
    relatorio_m2.MODO_PDF = True
    try:
        with tempfile.TemporaryDirectory() as td:
            caminho = os.path.join(td, "impressao.docx")
            gerar_fn(caminho)
            return relatorio_m2.docx_para_pdf(caminho)
    finally:
        relatorio_m2.MODO_PDF = False


def botao_imprimir(chave, nome_arq, gerar_fn):
    """Botões 'Gerar PDF para impressão' e 'Baixar PDF'. O .docx continua sendo a versão com equações nativas."""
    if ERRO_RELATORIO:
        return
    if st.button("🖨️ Gerar PDF para impressão", key=f"btn_pdf_{chave}"):
        with st.spinner("Gerando PDF..."):
            ss[f"_pdf_{chave}"] = pdf_impressao(gerar_fn) or b""
        if not ss[f"_pdf_{chave}"]:
            st.error("Conversor de PDF indisponível neste servidor. Baixe o .docx e imprima pelo Word.")
    if ss.get(f"_pdf_{chave}"):
        st.download_button("⬇️ Baixar PDF (imprimir)", ss[f"_pdf_{chave}"], file_name=nome_arq, mime="application/pdf", key=f"dl_pdf_{chave}")
        st.caption("No PDF as equações saem em texto linear; a versão .docx traz as equações nativas do Word.")


def entradas_calculo_m2():
    """Seleção dos cabos e dados do feixe direto na aba de cálculo (como a planilha CELT2). Usa as mesmas chaves do Módulo 1."""
    n = int(G("cfg", "n_circ", 1))
    faltam = any(not circuito(i)["cond"] for i in range(1, n + 1)) or not G("cfg", "cg1") or (G("cfg", "n_cg", 1) == 2 and not G("cfg", "cg2"))
    with st.expander("Cabos e dados de entrada do cálculo", expanded=faltam):
        if not db.listar_cabos(USOS_CHAVE["condutores"]):
            st.warning("Catálogo de cabos vazio. Importe a planilha (`python importar_cabos.py <planilha.xlsm>`) ou cadastre na aba Catálogo de cabos.")
        a, b = st.columns(2)
        num("sis", "km", "Comprimento da linha (km)", 50.0, 0.1, 1000.0, 1.0, c=a)
        sel("sis", "freq", "Frequência (Hz)", [60, 50], c=b)
        cols = st.columns(n)
        for i in range(1, n + 1):
            ns, c0 = f"c{i}", circuito(i)
            with cols[i - 1]:
                st.markdown(f"**Circuito {i}**")
                a, b = st.columns(2)
                num(ns, "un", "Tensão nominal (kV)", c0["un"], 13.8, 800.0, 1.0, c=a)
                num(ns, "mva", "Potência na carga (MVA)", c0["mva"], 0.0, 5000.0, 10.0, c=b)
                num(ns, "fp", "Fator de potência", c0["fp"], 0.1, 1.0, 0.01)
                sel_cabo(ns, "cond", "Condutor de fase (catálogo)", "condutores")
                a, b = st.columns(2)
                sel(ns, "cabos_fase", "Cabos por fase", [1, 2, 3, 4], default=c0["cabos_fase"], c=a)
                if G(ns, "cabos_fase", c0["cabos_fase"]) > 1:
                    num(ns, "esp_sub", "Espaç. subcondutores (mm)", c0["esp_sub"], 50.0, 1500.0, 10.0, c=b)
        st.markdown("**Cabos guarda**")
        a, b = st.columns(2)
        sel_cabo("cfg", "cg1", "Cabo guarda 1", "guardas", c=a)
        if G("cfg", "n_cg", 1) == 2:
            sel_cabo("cfg", "cg2", "Cabo guarda 2", "guardas", c=b)
        st.caption("Estes campos são os mesmos do Módulo 1: editar aqui ou lá dá no mesmo. "
                   "Nº de circuitos e de cabos guarda definem a geometria (aba Geometria da LT).")


def tab_calculo():
    st.caption("Cálculo por circuito: método da planilha CELT2 (referência) e método matricial com acoplamento "
               "(Carson + Maxwell + Kron + componentes simétricas). O modelo π é apresentado para cada circuito.")
    st.caption(f"Resistividade do solo: {G('2', 'rho', 1000.0):.0f} Ω·m (definida na aba Geometria da LT) · "
               f"Linha transposta: {'sim' if G('2', 'transp', True) else 'não'} (a assimetria entre fases é reportada).")
    entradas_calculo_m2()
    out, geo, erros = calcular_m2()
    for e in erros:
        st.error(e)
    if out is None:
        return
    res, gcab = out
    for n in res["notas"]:
        st.warning(n)
    cs = res["circuitos"]
    abas = st.tabs([f"Circuito {c} – {v['dados']['nome']}" for c, v in cs.items()] + (["Acoplamento"] if "mutua" in res else []))
    for ab, (c, v) in zip(abas, cs.items()):
        with ab:
            ce, mt, pi = v["celt2"], v["matricial"], v["celt2"]["pi"]
            a, b, c3, d = st.columns(4)
            a.metric("L (mH/km)", f"{ce['L_mH_km']:.4f}")
            b.metric("C (nF/km)", f"{ce['C_nF_km']:.4f}")
            c3.metric("|Zo| (Ω)", f"{abs(ce['Zo']):.2f}")
            d.metric("Corrente nominal (A)", f"{v['i_nom']:.1f}")
            st.markdown("**Modelo π equivalente**")
            st.dataframe(pd.DataFrame([
                ["Zs (Ω)", f"{pi['Zs']:.3f}", f"{mt['pi']['Zs']:.3f}"],
                ["Yp em cada extremidade (S)", f"{pi['Yp']:.6e}", f"{mt['pi']['Yp']:.6e}"],
                ["Zo (Ω)", f"{ce['Zo']:.2f}", f"{mt['Zo']:.2f}"]],
                columns=["Grandeza", "Método CELT2", "Método matricial"]), hide_index=True)
            if "carga" in ce:
                k = ce["carga"]
                a, b, c3, d = st.columns(4)
                a.metric("Tensão na carga (kV)", f"{k['Vc_kV']:.3f}", delta=f"fonte fixa {k['Vo_kV']:.1f} kV", delta_color="off")
                b.metric("Regulação (%)", f"{k['regulacao_pct']:.3f}")
                c3.metric("Perdas (kW)", f"{k['perdas_kW']:.2f}")
                d.metric("P/SIL", f"{k['Pc_SIL']:.3f}")
            sq = v["seq"]
            st.dataframe(pd.DataFrame([
                ["Z1 (Ω/km)", f"{sq['Z1']:.4f}"], ["Z0 (Ω/km)", f"{sq['Z0']:.4f}"],
                ["C1 (nF/km)", f"{sq['C1'] * 1e9:.4f}"], ["C0 (nF/km)", f"{sq['C0'] * 1e9:.4f}"]],
                columns=["Sequência (matricial)", "Valor"]), hide_index=True)
    if "mutua" in res:
        with abas[-1]:
            m = res["mutua"]
            st.dataframe(pd.DataFrame([
                ["Z1m (Ω/km)", f"{m['Z1m']:.5f}"], ["Z0m (Ω/km)", f"{m['Z0m']:.5f}"],
                ["Acoplamento seq. + (%)", f"{m['acoplamento_Z1'] * 100:.2f}"],
                ["Acoplamento seq. 0 (%)", f"{m['acoplamento_Z0'] * 100:.1f}"],
                ["C1m (nF/km)", f"{m['C1m'] * 1e9:.4f}"], ["C0m (nF/km)", f"{m['C0m'] * 1e9:.4f}"]],
                columns=["Grandeza", "Valor"]), hide_index=True)
    st.divider()
    if ERRO_RELATORIO:
        st.error(ERRO_RELATORIO)
    elif st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m2"):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            caminho = os.path.join(td, "relatorio.docx")
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m2.gerar(caminho, proj, geo, res, None, None, cabos_guarda=gcab,
                               codigo=(G("proj", "numero") or "BK-LT-MC") + "-M2", rev=G("proj", "revisao") or "R0",
                               script_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "calc_parametros.py"))
            with open(caminho, "rb") as fh:
                ss["_rel_m2"] = fh.read()
    def _g2(caminho):
        proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
        relatorio_m2.gerar(caminho, proj, geo, res, None, None, cabos_guarda=gcab,
                           codigo=(G("proj", "numero") or "BK-LT-MC") + "-M2", rev=G("proj", "revisao") or "R0",
                           script_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "calc_parametros.py"))
    botao_imprimir("m2", "Relatorio_Modulo2_Parametros_Eletricos.pdf", _g2)
    if ss.get("_rel_m2"):
        st.download_button("Baixar relatório do Módulo 2", ss["_rel_m2"], file_name="Relatorio_Modulo2_Parametros_Eletricos.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m2")


def mod2():
    t1, t3, t4 = st.tabs(["Geometria da LT", "Catálogo de cabos", "Cálculo e relatório"])
    with t1:
        tab_geometria()
    with t4:
        tab_calculo()
    with t3:
        tab_catalogo()


# ----------------------------------------------------------------------------
# Módulo 3 — Estudo dos Ventos
# ----------------------------------------------------------------------------
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
UFS = sorted(cv.UF_REGIAO.keys())


def _h_cabo_geo():
    """Altura média das fases no vão (m), da geometria do Módulo 2; None se inválida."""
    try:
        g = geometria_atual()
        h = [k["y_med"] for k in g["condutores"] if k["tipo"] == "fase"]
        return sum(h) / len(h) if h else None
    except Exception:
        return None


def mapa_brasil(lat, lon, rotulo):
    import json
    import plotly.graph_objects as go
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados", "brasil_estados.json"), encoding="utf-8") as fh:
        estados = json.load(fh)
    fig = go.Figure()
    for e in estados:
        for poly in e["poly"]:
            xs, ys = [p[0] for p in poly[0]], [p[1] for p in poly[0]]
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", fill="toself", fillcolor="#E5E7EB", line=dict(color="#6B7280", width=0.6),
                                     hoverinfo="text", text=e["nome"], showlegend=False))
    if lat is not None and lon is not None:
        fig.add_trace(go.Scatter(x=[lon], y=[lat], mode="markers+text", text=[rotulo], textposition="top right", showlegend=False,
                                 marker=dict(symbol="star", size=16, color="#EF4444", line=dict(color="black", width=1))))
    fig.update_xaxes(range=[-74.5, -33.5], title="Longitude (°)", scaleanchor="y", scaleratio=1 / 0.966)
    fig.update_yaxes(range=[-34.5, 5.8], title="Latitude (°)")
    fig.update_layout(height=480, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white")
    mostrar_plotly(fig)


def mod3():
    N = "3"
    t1, t2, t3, t4 = st.tabs(["Estação INMET e local", "Vento", "Temperaturas", "Resultados e relatório"])
    with t1:
        st.caption("Dados meteorológicos do INMET (digitados aqui). O relatório cita a estação e o período informados.")
        c1, c2, c3 = st.columns(3)
        txt(N, "est_nome", "Estação INMET (nome)", c=c1)
        txt(N, "est_cod", "Código da estação (ex.: A701)", c=c2)
        txt(N, "municipio", "Município do projeto", c=c3)
        c4, c5, c6 = st.columns(3)
        sel(N, "uf", "UF do projeto", UFS, "SC", c=c4, help="Define a região da Tabela 8 (Ktur) da NBR 5422:2024.")
        regioes = ["Sul", "Sudeste e Centro-Oeste", "Norte e Nordeste"]
        reg_auto = cv.UF_REGIAO.get(G(N, "uf", "SC"))
        c5.text_input("Região (Tabela 8) – automática", value=str(reg_auto), disabled=True, key=_k("3", "reg_auto"))
        sel(N, "regiao_manual_sel", "Substituir região (opcional)", ["(automática)"] + list(cv.KTUR.keys()), c=c6)
        S(N, "regiao_manual", None if G(N, "regiao_manual_sel") == "(automática)" else G(N, "regiao_manual_sel"))
        c7, c8, c9 = st.columns(3)
        num(N, "lat", "Latitude do projeto (°, sul negativo)", -27.6, -34.0, 6.0, 0.01, "%.4f", c=c7)
        num(N, "lon", "Longitude do projeto (°, oeste negativo)", -48.5, -74.0, -34.0, 0.01, "%.4f", c=c8)
        num(N, "alt", "Altitude média do trecho (m)", 0.0, 0.0, 4000.0, 10.0, c=c9, help="NBR 5422:2024, 4.7.")
        c10, c11 = st.columns(2)
        num(N, "serie_ini", "Primeiro ano da série", 2005, 1900, 2100, 1, c=c10)
        num(N, "serie_fim", "Último ano da série", 2024, 1900, 2100, 1, c=c11)
        st.markdown("**Localização do projeto**")
        mapa_brasil(G(N, "lat"), G(N, "lon"), G(N, "municipio") or "Projeto")
    with t2:
        c1, c2, c3 = st.columns(3)
        sel(N, "modo", "Como informar o vento do INMET", ["Série de máximos anuais", "Estatísticas"], c=c1,
            help="Série: o app calcula média e desvio-padrão. Estatísticas: informe média, dispersão e nº de anos.")
        sel(N, "unid", "Unidade", ["m/s", "km/h"], c=c2)
        sel(N, "integ_med", "Integração da medição da estação", ["10 min", "30 s", "3 s"], c=c3,
            help="Velocidade registrada pela estação. Entra na conversão da 4.9.4.1 (Tabela 2).")
        c4, c5 = st.columns(2)
        sel(N, "cat_est", "Categoria de terreno da estação", ["A", "B", "C", "D"], "B", c=c4, help="Tabela 1 (Krug).")
        num(N, "z_med", "Altura de medição da estação (m)", 10.0, 1.0, 100.0, 0.5, c=c5, help="Kalt, Tabela 3.")
        if G(N, "modo") == "Série de máximos anuais":
            base = G(N, "serie") or [{"ano": a, "vmax": None} for a in range(2015, 2025)]
            df = st.data_editor(pd.DataFrame(base), num_rows="dynamic", key=_k("3", "ed_serie"), hide_index=True,
                                column_config={"ano": st.column_config.NumberColumn("Ano", format="%d"),
                                               "vmax": st.column_config.NumberColumn("Vento máximo anual", min_value=0.0)})
            S(N, "serie", [{"ano": r["ano"], "vmax": None if pd.isna(r["vmax"]) else float(r["vmax"])} for r in df.to_dict("records")])
            st.caption("Mínimo de 10 anos (NBR 5422:2024, 4.9.3.2.1).")
        else:
            d1, d2, d3, d4 = st.columns(4)
            num(N, "v_med", "Média dos máximos anuais", 0.0, 0.0, 300.0, 0.1, c=d1)
            sel(N, "tipo_disp", "Dispersão informada como", ["Desvio-padrão", "Coeficiente de variação (%)"], c=d2)
            num(N, "s", "Valor da dispersão", 0.0, 0.0, 300.0, 0.1, c=d3)
            num(N, "n", "Número de anos da série", 0, 0, 100, 1, c=d4)
        st.markdown("**Projeto**")
        e1, e2, e3 = st.columns(3)
        sel(N, "cat", "Categoria de terreno do projeto", ["A", "B", "C", "D"], "B", c=e1)
        chk(N, "usar_h_geo", "Usar altura média das fases da geometria (Módulo 2)", True, c=e2)
        hg = _h_cabo_geo()
        if G(N, "usar_h_geo", True):
            e3.caption(f"Altura média das fases: {hg:.2f} m" if hg else "Geometria inválida/ausente: informe a altura.")
        if not G(N, "usar_h_geo", True) or not hg:
            num(N, "h_cabo", "Altura média do cabo (m)", 20.0, 1.0, 200.0, 0.5, c=e3)
        st.markdown("**Períodos de retorno (anos)**")
        f1, f2, f3, f4, f5, f6 = st.columns(6)
        num(N, "tr_max", "Vento máx. (10 min)", 50.0, 2.0, 1000.0, 1.0, c=f1, help="Definido pela transmissora (12.3.3.2). PREMISSA.")
        num(N, "tr_v5030", "Vento 50/30", 50.0, 2.0, 1000.0, 1.0, c=f2, help="≥ 50 anos (7.1.8.2).")
        num(N, "tr_rajada", "Rajada (3 s)", 150.0, 2.0, 1000.0, 1.0, c=f3, help="Definido pela transmissora (8.2.3.3). PREMISSA.")
        num(N, "tr_freq", "Freq. industrial", 10.0, 2.0, 1000.0, 1.0, c=f4, help="≥ 10 anos (9.6.2.1a).")
        num(N, "tr_manobra", "Manobra", 2.0, 1.0, 1000.0, 1.0, c=f5, help="≥ 2 anos (9.6.2.1b).")
        num(N, "tr_ext", "Extremo (opcional, 0 = não)", 0.0, 0.0, 2000.0, 10.0, c=f6)
    with t3:
        st.caption("Temperaturas do INMET (°C). O EDS é a temperatura média (3.1.54).")
        sel(N, "eds_modo", "EDS a partir de", ["Média das 12 médias mensais", "Temperatura média informada"])
        if G(N, "eds_modo") == "Média das 12 médias mensais":
            base = G(N, "meses") or [{"mes": m, "t": None} for m in MESES]
            df = st.data_editor(pd.DataFrame(base), key=_k("3", "ed_meses"), hide_index=True, disabled=["mes"],
                                column_config={"mes": "Mês", "t": st.column_config.NumberColumn("Temp. média (°C)", format="%.1f")})
            S(N, "meses", [{"mes": r["mes"], "t": None if pd.isna(r["t"]) else float(r["t"])} for r in df.to_dict("records")])
        else:
            num(N, "t_media", "Temperatura média – EDS (°C)", 20.0, -30.0, 60.0, 0.1)
        a1, a2, a3, a4 = st.columns(4)
        num(N, "t_max", "T máx. – 2 % de excedência (°C)", 40.0, -30.0, 70.0, 0.1, c=a1)
        num(N, "t_min", "T mín. – 2 % de ocorrência (°C)", 5.0, -40.0, 40.0, 0.1, c=a2)
        num(N, "t_coinc", "T coincidente – média das mínimas (°C)", 10.0, -40.0, 40.0, 0.1, c=a3)
        num(N, "t_med_max", "Média das máximas anuais (°C)", 35.0, -30.0, 70.0, 0.1, c=a4)
        st.caption("Os valores iniciais são apenas ponto de partida do formulário; substitua pelos do INMET.")
        st.markdown("**Temperaturas do condutor (critério do projeto)**")
        b1, b2, b3, b4 = st.columns(4)
        num(N, "t_cc_max", "CC – máxima (°C)", 75.0, 20.0, 150.0, 1.0, c=b1)
        num(N, "t_cc_emerg", "CC – emergência (°C)", 90.0, 20.0, 150.0, 1.0, c=b2)
        num(N, "t_pr_max", "PR – máxima (°C)", 40.0, 20.0, 150.0, 1.0, c=b3)
        chk(N, "usar_reduzido", "Incluir vento reduzido (60 %) – origem a confirmar", False, c=b4)
    with t4:
        res = cv.montar(dict(ss["dados"].get(N, {})), _h_cabo_geo())
        for m in res["pendencias"]:
            st.warning(m)
        for m in res["avisos"]:
            st.info(m)
        if res["ok"]:
            est = res["estudo"]
            m1, m2, m3_, m4 = st.columns(4)
            m1.metric("Média v̄ (m/s)", f"{est['v_med']:.2f}")
            m2.metric("Desvio-padrão s (m/s)", f"{est['s']:.2f}")
            m3_.metric("C1 / C2", f"{est['c1']:.4f} / {est['c2']:.4f}")
            m4.metric("μ (kg/m³)", f"{est['mu']:.4f}")
            st.markdown("**Velocidades de projeto**")
            st.dataframe(pd.DataFrame([[c["nome"], c["TR"], c["integracao"], round(c["K"], 3), round(c["VR"], 2), round(c["VP"], 2), round(c["q0"])]
                                       for c in est["casos"]],
                                      columns=["Caso", "T (anos)", "Integração", "K(T,n)", "V_R (m/s)", "V_P (m/s)", "q0 (Pa)"]), hide_index=True)
        st.markdown("**Quadro para aprovação da transmissora**")
        st.dataframe(pd.DataFrame([[a["item"], None if a["valor"] is None else round(a["valor"], 4 if a["unidade"] == "kg/m³" else 2), a["unidade"],
                                    None if a.get("pressao") is None else round(a["pressao"], 1), a["base"], a["fonte"]]
                                   for a in res["aprovacao"]], columns=["Parâmetro", "Valor", "Unid.", "Pressão (Pa)", "Base", "Fonte"]), hide_index=True)
        if res["ok"]:
            st.markdown("**Casos de clima para o PLS-CADD**")
            dfp = pd.DataFrame(res["pls"])
            st.dataframe(dfp, hide_index=True)
            st.download_button("Baixar casos PLS-CADD (CSV)", dfp.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                               file_name="casos_clima_PLSCADD.csv", mime="text/csv", key="dl_pls_m3")
        st.divider()
        st.markdown("**Relatório (padrão BK) e impressão**")

        def _g3(caminho):
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m3.gerar(caminho, proj, dict(ss["dados"].get(N, {})), res,
                               codigo=(G("proj", "numero") or "BK-LT-MC") + "-M3", rev=G("proj", "revisao") or "R0")
        if ERRO_RELATORIO:
            st.error(ERRO_RELATORIO)
        elif not res["ok"]:
            st.info("Preencha os dados pendentes (avisos amarelos acima) para liberar o relatório e a impressão.")
            r1, r2 = st.columns(2)
            r1.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m3_off", disabled=True)
            r2.button("🖨️ Gerar PDF para impressão", key="btn_pdf_m3_off", disabled=True)
        else:
            if st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m3"):
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    caminho = os.path.join(td, "relatorio.docx")
                    _g3(caminho)
                    with open(caminho, "rb") as fh:
                        ss["_rel_m3"] = fh.read()
            if ss.get("_rel_m3"):
                st.download_button("Baixar relatório do Módulo 3 (.docx)", ss["_rel_m3"], file_name="Relatorio_Modulo3_Estudo_dos_Ventos.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m3")
            botao_imprimir("m3", "Relatorio_Modulo3_Estudo_dos_Ventos.pdf", _g3)
        botoes(3, so_limpar=True)


# ------------------------------------------------------------------------------
# Módulo 4 — Faixa de Domínio / Servidão (NBR 5422:2024, Seção 17)
# ----------------------------------------------------------------------------
def _cabo_cond_m4():
    """Cabo condutor do circuito 1 (catálogo) ou {}."""
    cod = circuito(1).get("cond")
    return db.obter_cabo(cod) if cod else {}


def _vento_m3():
    """Vento 50/30 e q0 do Módulo 3 (None se o estudo ainda não está completo)."""
    r = cv.montar(dict(ss["dados"].get("3", {})), _h_cabo_geo())
    if not r.get("ok"):
        return None, None
    c = {x["chave"]: x for x in r["estudo"]["casos"]}["v5030"]
    return c["VP"], c["q0"]


def entrada_m4():
    """Monta o dicionário de entrada do motor calc_faixa a partir do estado do app. Retorna (entrada, avisos)."""
    N = "4"
    avisos = []
    cabo = _cabo_cond_m4()
    c1 = circuito(1)
    vp3, q03 = _vento_m3()
    if G(N, "vento_modo", "Módulo 3") == "Módulo 3" and vp3:
        vp, q0 = vp3, q03
    else:
        vp, q0 = G(N, "vp_man", 0.0), None
    g = geometria_atual()
    xs = [k["x"] - g.get("eixo_x", 0.0) for k in g["condutores"] if k["tipo"] == "fase"]
    b_geo = max(abs(x) for x in xs) if xs else 0.0
    b = G(N, "b", None)
    e = dict(vp=vp, q0=q0, d_mm=cabo.get("diametro_mm"), massa_kg_m=cabo.get("massa_kg_m"),
             lm=G(N, "lm", 0.0), lp=G(N, "lp", 0.0), b=b_geo if not G(N, "b_man", False) else G(N, "b", b_geo),
             comp_cadeia=0.0 if G(N, "tipo_cadeia", "Suspensão") != "Suspensão" else G(N, "comp_cadeia", 0.0),
             flecha=G(N, "flecha", 0.0), simetrica=G(N, "simetrica", "Simétrica") == "Simétrica",
             lado_isol=G(N, "lado_isol_m", None) if G(N, "simetrica", "Simétrica") != "Simétrica" else None,
             un_kv=c1["un"], fsfl=G(N, "fsfl", 2.0), kafl=G(N, "kafl", 1.0),
             criterio_beta={"Médio (8.9.1)": "medio", "Máximo (8.9.4)": "maximo"}[G(N, "crit_beta", "Médio (8.9.1)")],
             criterio_D={"Maior entre norma e planilha BK": "maior", "NBR 5422:2024 (9.4.1)": "norma",
                         "Planilha BK (U·1,05/150)": "planilha"}[G(N, "crit_D", "Maior entre norma e planilha BK")],
             h_navio=G(N, "h_navio", 0.0))
    return e, avisos, b_geo, cabo


def mod4():
    N = "4"
    import calc_faixa as cf
    t1, t2, t3, t4, t5 = st.tabs(["Dados de entrada", "Faixa de segurança", "Distâncias de segurança", "Pontos e vizinhas", "Resultados e relatório"])
    cabo = _cabo_cond_m4()
    _g = geometria_atual()
    b_geo = max([abs(k["x"] - _g.get("eixo_x", 0.0)) for k in _g["condutores"] if k["tipo"] == "fase"] or [0.0])
    with t1:
        st.caption("NBR 5422:2024, Seção 17 (largura da faixa de passagem) e 8.9 (ângulo de balanço). "
                   "Cabo e tensão vêm do Módulo 1/2; o vento 50 anos/30 s vem do Módulo 3.")
        info = []
        info.append(f"Condutor: **{circuito(1).get('cond') or 'não selecionado'}** · d = {cabo.get('diametro_mm') or '—'} mm · "
                    f"m = {cabo.get('massa_kg_m') or '—'} kg/m · tensão nominal = {circuito(1)['un']:g} kV")
        st.markdown(" \n".join(info))
        a1, a2 = st.columns(2)
        sel(N, "vento_modo", "Vento 50 anos / 30 s", ["Módulo 3", "Informar manualmente"], c=a1,
            help="17.2.2.2c: vento com TR de 50 anos e integração de 30 s.")
        vp3, q03 = _vento_m3()
        if G(N, "vento_modo", "Módulo 3") == "Módulo 3":
            a2.metric("V_P30 do Módulo 3 (m/s)", f"{vp3:.2f}" if vp3 else "— (complete o Módulo 3)")
        else:
            num(N, "vp_man", "V_P (50 anos, 30 s) (m/s)", 25.0, 0.0, 100.0, 0.1, c=a2)
        st.markdown("**Vãos e flecha (dados do PLS-CADD)**")
        b1, b2, b3 = st.columns(3)
        num(N, "lm", "Vão médio (vão de vento) Lm (m)", 400.0, 10.0, 2000.0, 5.0, c=b1, help="8.9.1")
        num(N, "lp", "Vão gravante Lp (m)", 350.0, 10.0, 2000.0, 5.0, c=b2, help="8.9.1")
        num(N, "flecha", "Flecha máx. à temp. máxima (m)", 10.0, 0.0, 100.0, 0.05, c=b3,
            help="17.2.2.2a: temperatura do condutor = temperatura máxima do ar. Vem do PLS-CADD.")
        st.markdown("**Cadeia e geometria**")
        c1_, c2_, c3_ = st.columns(3)
        sel(N, "tipo_cadeia", "Tipo de cadeia", ["Suspensão", "Ancoragem", "Line-post"], c=c1_,
            help="Ancoragem e line-post: comprimento de cadeia = 0 (planilha BK).")
        num(N, "comp_cadeia", "Comprimento da cadeia (m)", 2.0, 0.0, 15.0, 0.05, c=c2_)
        c3_.metric("b (eixo → fase externa) da geometria (m)", f"{b_geo:.2f}")
        chk(N, "b_man", "Informar b manualmente", False, c=c3_)
        if G(N, "b_man", False):
            num(N, "b", "b (m)", float(b_geo or 3.0), 0.0, 40.0, 0.05)
        d1, d2 = st.columns(2)
        sel(N, "simetrica", "Disposição das fases", ["Simétrica", "Isoladores só de um lado"], c=d1,
            help="17.2.2.5.1 (simétrica) ou 17.2.2.5.2 (todas as fases de um lado).")
        if G(N, "simetrica", "Simétrica") != "Simétrica":
            num(N, "lado_isol_m", "Distância do eixo ao lado dos isoladores (m)", float(b_geo or 3.0), 0.0, 40.0, 0.05, c=d2)
        st.markdown("**Critérios**")
        e1, e2, e3, e4 = st.columns(4)
        sel(N, "crit_beta", "Ângulo de balanço", ["Médio (8.9.1)", "Máximo (8.9.4)"], c=e1,
            help="A planilha usa o médio; 17.2.2.3 remete à 8.9 – confirmar com a transmissora.")
        sel(N, "crit_D", "Distância D", ["Maior entre norma e planilha BK", "NBR 5422:2024 (9.4.1)", "Planilha BK (U·1,05/150)"], c=e2)
        num(N, "fsfl", "F_sfl – fator de sobretensão de manobra (p.u.)", 2.0, 1.0, 4.0, 0.05, c=e3,
            help="9.4.1: fase-terra, 2 % de probabilidade. PREMISSA – vem do estudo de sobretensões.")
        num(N, "kafl", "k_afl – correção atmosférica", 1.0, 0.5, 1.5, 0.01, c=e4, help="9.4.1/Seção 4. PREMISSA (1,0).")
        num(N, "h_navio", "H – altura máx. do navio (m) (só águas navegáveis)", 0.0, 0.0, 100.0, 0.5)
    e, _av, b_geo, cabo = entrada_m4()      # depois dos widgets: usa os valores já digitados
    r = cf.calcular(e)
    with t2:
        if r["erros"]:
            for m in r["erros"]:
                st.warning(m)
        else:
            m1, m2, m3_, m4_ = st.columns(4)
            m1.metric("K (Figura 22)", f"{r['ang']['K']:.3f}")
            m2.metric("β médio (°)", f"{r['ang']['beta']:.2f}")
            m3_.metric("β máx = β+2σ (°)", f"{r['ang']['beta_max']:.2f}")
            m4_.metric("D adotada (m)", f"{r['D']:.2f}")
            fx = r["faixa"]
            n1, n2, n3 = st.columns(3)
            n1.metric("d = (cadeia+flecha)·sen β (m)", f"{fx['d']:.2f}")
            n2.metric("Faixa calculada (m)", f"{fx['L']:.2f}")
            n3.metric("Faixa adotada (m)", f"{fx['L_adot']:.0f}")
            if not fx["simetrica"]:
                st.info(f"Lado dos isoladores: {fx['lado_isol']:.2f} m · lado oposto: {fx['lado_oposto']:.2f} m (soma = {fx['L_adot']:.0f} m).")
            st.dataframe(pd.DataFrame([
                ["Planilha BK: U·1,05/150 (ou 0,5 m ≤ 69 kV)", r["D_planilha"]], ["NBR 5422:2024, 9.4.1 (kg=1,28; Kcs=1,35)", r["D_norma"]]],
                columns=["Origem de D", "D (m)"]).round(3), hide_index=True)
            st.dataframe(pd.DataFrame([["β médio", r["faixa_medio"]["L"], r["faixa_medio"]["L_adot"]],
                                       ["β máximo", r["faixa_max"]["L"], r["faixa_max"]["L_adot"]]],
                                      columns=["Ângulo usado", "Faixa calculada (m)", "Faixa adotada (m)"]).round(2), hide_index=True)
            for m in r["avisos"]:
                st.info(m)
            st.caption("PREMISSA: F_sfl e k_afl a confirmar. Também devem ser verificados os campos elétrico/magnético "
                       "(10.2, 10.3) e RI/ruído audível (10.6, 10.7) na borda da faixa (17.2.3 e 17.2.4) – Módulos 8 e 10.")
    with t3:
        if r["erros"]:
            st.info("Complete os dados de entrada.")
        else:
            st.markdown("**Distâncias verticais – NBR 5422:2024, 7.2 (Tabelas 5 e 6)**")
            st.dataframe(pd.DataFrame([[k, v["kg"], v["PbV"], v["Pe_tip"], v["Pe_lim"], v["D_lim_n"], v["D_tip_n"]]
                                       for k, v in r["verticais"].items()],
                                      columns=["Obstáculo", "kg", "PbV (m)", "Pe típ. (m)", "Pe lim. (m)", "D_V lim,n (m)", "D_V típ,n (m)"]).round(2),
                         hide_index=True)
            st.markdown("**Distâncias horizontais – 7.3 (Tabela 7)**")
            st.dataframe(pd.DataFrame([[k, v["kg"], v["PbH"], v["Pe_tip"], v["D_H"]] for k, v in r["horizontais"].items()],
                                      columns=["Obstáculo", "kg", "PbH (m)", "Pe típ. (m)", "D_H (m)"]).round(2), hide_index=True)
            st.markdown("**Comparação – tabela da planilha BK (aba 'Distância de Segurança')**")
            st.dataframe(pd.DataFrame([[k, v] for k, v in r["verticais_planilha"].items()],
                                      columns=["Obstáculo", "Distância (m)"]).round(2), hide_index=True)
            st.caption("A tabela da planilha segue a lógica da edição anterior da NBR 5422 (valor básico + 0,01·(U·1,05/√3 − 50)); "
                       "a edição 2024 usa PbV + Ps + Pe. NECESSITA VALIDAÇÃO TÉCNICA para escolher qual vale para o projeto. "
                       "Verticais devem ser verificadas até β_máx (7.2.1.3).")
    with t4:
        bloco_pontos(4)
    with t5:
        st.markdown("**Relatório (padrão BK) e impressão**")

        def _g4(caminho):
            import relatorio_m4
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m4.gerar(caminho, proj, e, r, dict(ss["dados"].get(N, {})), circuito(1),
                               codigo=(G("proj", "numero") or "BK-LT-MC") + "-M4", rev=G("proj", "revisao") or "R0",
                               pontos=PT.resumo(ss["dados"], 4))
        if ERRO_RELATORIO:
            st.error(ERRO_RELATORIO)
        elif r["erros"]:
            st.info("Preencha os dados pendentes para liberar o relatório e a impressão.")
            r1, r2 = st.columns(2)
            r1.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m4_off", disabled=True)
            r2.button("🖨️ Gerar PDF para impressão", key="btn_pdf_m4_off", disabled=True)
        else:
            if st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m4"):
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    caminho = os.path.join(td, "relatorio.docx")
                    _g4(caminho)
                    with open(caminho, "rb") as fh:
                        ss["_rel_m4"] = fh.read()
            if ss.get("_rel_m4"):
                st.download_button("Baixar relatório do Módulo 4 (.docx)", ss["_rel_m4"], file_name="Relatorio_Modulo4_Faixa_de_Servidao.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m4")
            botao_imprimir("m4", "Relatorio_Modulo4_Faixa_de_Servidao.pdf", _g4)
        botoes(4, so_limpar=True)


# ----------------------------------------------------------------------------
# Módulo 5 — Coordenação e Isolamento (isoladores, distâncias no ar, balanço e para-raios)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _calc5_cache(chave_json):
    import json
    import calc_isolamento as ci
    return ci.calcular(json.loads(chave_json))


def _casos_vento_m5():
    """{'freq': (V, q0), 'manobra': (V, q0)} do Módulo 3 (vazio se o estudo não está completo)."""
    r = cv.montar(dict(ss["dados"].get("3", {})), _h_cabo_geo())
    if not r.get("ok"):
        return {}
    cs = {x["chave"]: x for x in r["estudo"]["casos"]}
    return {k: (cs[k]["VP"], cs[k]["q0"]) for k in ("freq", "manobra") if k in cs}


def entrada_m5():
    """Monta a entrada do motor calc_isolamento a partir do estado do app. Retorna (entrada, info)."""
    import calc_isolamento as ci
    N = "5"
    c1 = circuito(1)
    um, un = float(c1.get("umax") or 0.0), float(c1.get("un") or 0.0)
    cabo = _cabo_cond_m4()
    g = geometria_atual()
    eixo = g.get("eixo_x", 0.0)
    fases = [[round(k["x"] - eixo, 3), round(k["y"], 3)] for k in g["condutores"] if k["tipo"] == "fase"]
    angs = [min([v for kk, v in l.items() if kk != "Fase" and v is not None] or [None]) for l in g["angulos"]]
    angs = [a for a in angs if a is not None]
    n_cg = int(G("cfg", "n_cg", 1))
    # Fsfl
    fsfl_t = ci.fsfl_minimo(um)
    if G(N, "fsfl_modo", "Tabela 14 (sem estudo)") == "Tabela 14 (sem estudo)":
        fsfl, fsfl_o = fsfl_t, "Tabela 14 (9.4.3.1)"
    else:
        fsfl, fsfl_o = G(N, "fsfl", fsfl_t), "Informado (estudo de transitórios)"
    alfa = float(G(N, "alfa", 0.5))
    kg_ft_nome = G(N, "kg_ft_geo", "Braço de torre")
    kg_ff_nome = G(N, "kg_ff_geo", "Condutores cruzados")
    if G(N, "kg_modo", "Tabelas C.1 e C.3") == "Tabelas C.1 e C.3":
        kg_ft = ci.TAB_C1[kg_ft_nome]
        kg_ff = ci.TAB_C3[kg_ff_nome][0 if alfa >= 0.4 else 1]
        kg_o = f"C.1: {kg_ft_nome}; C.3: {kg_ff_nome}"
    else:
        kg_ft, kg_ff, kg_o = G(N, "kg_ft", 1.3), G(N, "kg_ff", 1.45), "Informado"
    # fuga
    pol = G(N, "poluicao", "II – Médio")
    if G(N, "fuga_modo", "Nível de poluição (IEC 60815:1986)") == "Nível de poluição (IEC 60815:1986)":
        fuga, fuga_o = ci.FUGA_IEC60815_1986[pol], f"IEC 60815 (1986) nível {pol} – Celesc E-313.0058"
    else:
        fuga, fuga_o = G(N, "fuga_esp", 20.0), "Informado"
    ang_bl = max(angs) if angs else None
    e = dict(
        um_kv=um, un_kv=un, modo_delta=G(N, "modo_delta", "Sem medições (NBR 5422, 4.5.3)"),
        alt=G(N, "alt", G("3", "alt", 800.0) or 800.0), lat=G(N, "lat", G("3", "lat", -27.6) or -27.6),
        lon=G(N, "lon", G("3", "lon", -48.5) or -48.5), p_hpa=G(N, "p_hpa", 1013.0), t_c=G(N, "t_c", 20.0), ur_pct=G(N, "ur_pct", 70.0),
        fsfl=fsfl, _fsfl_origem=fsfl_o, rs=G(N, "rs", 1.4), alfa=alfa, kg_ft=kg_ft, kg_ff=kg_ff, _kg_origem=kg_o,
        ftmo=G(N, "ftmo", 1.0), d_trab=G(N, "d_trab", 0.0),
        cv_sfl=G(N, "cv_sfl", 15.0) / 100.0, cv_fl=G(N, "cv_fl", 5.0) / 100.0, n_gaps=int(G(N, "n_gaps", 3)), risco=G(N, "risco", 1e-3),
        kcs_man=(1.05 if G(N, "kcs_modo", "Calculado (Anexo C.3)").startswith("Referência") else
                 (G(N, "kcs_man", 1.05) if G(N, "kcs_modo", "Calculado (Anexo C.3)") == "Informado" else None)),
        ufr=(G(N, "ufr", 0.0) or None) if G(N, "ufr_modo", "Tabela 15") != "Tabela 15" else None,
        tipo_isol=G(N, "tipo_isol", "Vidro"), tipo_cadeia=G(N, "tipo_cadeia", "Suspensão em I"),
        fuga_esp=fuga, _fuga_origem=fuga_o, aplicar_edital=G(N, "edital", True),
        passo_mm=G(N, "passo_mm", 146.0), fuga_unid_mm=G(N, "fuga_unid_mm", 292.0) if G(N, "tipo_isol", "Vidro") != "Polimérico" else G(N, "fuga_total_mm", 4000.0),
        l_arco_mm=G(N, "l_arco_mm", 1300.0), l_ferr=G(N, "l_ferr", 0.3), n_min=int(G(N, "n_min", 1)),
        c1_c=G(N, "c1_c", 0.1), v_unid_adm=G(N, "v_unid_adm", 0.0) or None,
        rbl_kn=G(N, "rbl_kn", 0.0) or None, n_cad=int(G(N, "n_cad", 1)), carga_sv=G(N, "carga_sv", 0.0), carga_cv=G(N, "carga_cv", 0.0),
        fases=fases, xf=G(N, "xf", 0.5), h_corpo=G(N, "h_corpo", 10.0),
        d_cabo_m=(cabo.get("diametro_mm") or 0.0) / 1000.0, p_cabo=(cabo.get("massa_kg_m") or 0.0) * 9.80665,
        lm=G(N, "lm", G("4", "lm", 400.0)), lp=G(N, "lp", G("4", "lp", 350.0)), flecha=G(N, "flecha", G("4", "flecha", 0.0)),
        casos_vento=_casos_vento_m5(),
        pr=dict(uc_ur=G(N, "uc_ur", 0.8), ke=G(N, "ke", 1.4), ktov=G(N, "ktov", 1.10), ur_cat=G(N, "ur_cat", 0.0) or None,
                ur_estudo=G(N, "ur_estudo", 0.0) or None, margem_equip=G(N, "margem_equip", 15.0), bil=G(N, "bil", 0.0) or None,
                sil=G(N, "sil", 0.0) or None, ures_fr=G(N, "ures_fr", 0.0) or None, ures_fl=G(N, "ures_fl", 0.0) or None,
                usurto=G(N, "usurto", 0.0) or None, zc=G(N, "zc", 0.0) or None, km=G(N, "km_surto", 0.0) or None,
                e_cat=G(N, "e_cat", 0.0) or None),
        i_surto=G(N, "i_surto", 0.0) or None, zc=G(N, "zc", 0.0) or None, u_ind_med=G(N, "u_ind_med", 0.0) or None,
        ang_blind=ang_bl, n_cg=n_cg)
    return e


def mod5():
    import json
    import calc_isolamento as ci
    N = "5"
    t1, t2, t3, t4, t5 = st.tabs(["Atmosfera e sobretensões", "Isoladores", "Estrutura e balanço", "Para-raios e coordenação",
                                  "Resultados e relatório"])
    c1 = circuito(1)
    um = float(c1.get("umax") or 0.0)
    with t1:
        st.caption("NBR 5422:2024, 4.5 a 4.8 (fatores atmosféricos), Seção 9 (distâncias no ar) e Anexo C (kg e Kcs). "
                   f"Tensão nominal / máxima do Módulo 1: **{c1['un']:g} / {um:g} kV**.")
        st.markdown("**Atmosfera**")
        a1, a2, a3 = st.columns(3)
        num(N, "alt", "Altitude (m)", float(G("3", "alt", 800.0) or 800.0), 0.0, 5000.0, 10.0, c=a1)
        num(N, "lat", "Latitude (°)", float(G("3", "lat", -27.6) or -27.6), -35.0, 6.0, 0.01, c=a2)
        num(N, "lon", "Longitude (°)", float(G("3", "lon", -48.5) or -48.5), -75.0, -30.0, 0.01, c=a3)
        sel(N, "modo_delta", "Densidade relativa do ar (δ)", ["Sem medições (NBR 5422, 4.5.3)", "Com medições"], c=a1)
        if G(N, "modo_delta") == "Com medições":
            num(N, "p_hpa", "Pressão média p (hPa)", 1013.0, 500.0, 1100.0, 1.0, c=a2)
            num(N, "t_c", "Temperatura média t (°C)", 20.0, -20.0, 50.0, 0.5, c=a3)
            num(N, "ur_pct", "Umidade relativa média (%)", 70.0, 0.0, 100.0, 1.0, c=a1)
        st.markdown("**Sobretensões**")
        b1, b2, b3 = st.columns(3)
        sel(N, "fsfl_modo", "Fator de sobretensão de manobra Fsfl", ["Tabela 14 (sem estudo)", "Informado (estudo de transitórios)"], c=b1,
            help="9.4.3.1: valores mínimos sem estudo. Preferir o estudo de transitórios (EMT).")
        if G(N, "fsfl_modo") != "Tabela 14 (sem estudo)":
            num(N, "fsfl", "Fsfl (p.u. de √2/√3·Us)", float(ci.fsfl_minimo(um)), 1.0, 5.0, 0.05, c=b2)
        else:
            b2.metric("Fsfl (Tabela 14)", f"{ci.fsfl_minimo(um):.2f}")
        num(N, "ftmo", "Ftmo (fator de tensão máxima de operação)", 1.0, 1.0, 1.5, 0.01, c=b3, help="9.3.2. PREMISSA (1,0).")
        sel(N, "ufr_modo", "Ufr (frente rápida)", ["Tabela 15", "Informado"], c=b1)
        if G(N, "ufr_modo") == "Informado":
            num(N, "ufr", "Ufr (kV crista)", 820.0, 0.0, 4000.0, 10.0, c=b2)
        else:
            b2.metric("Ufr (Tabela 15)", f"{ci.ufr_tabela(float(c1['un'])):.0f} kV")
        num(N, "rs", "rs (relação fase-fase, 9.4.2)", 1.4, 1.0, 2.0, 0.05, c=b3, help="Padrão 1,4. PREMISSA.")
        sel(N, "kg_modo", "Fatores de gap kg", ["Tabelas C.1 e C.3", "Informar"], c=b1)
        if G(N, "kg_modo") == "Tabelas C.1 e C.3":
            sel(N, "kg_ft_geo", "Geometria fase-terra (C.1)", list(ci.TAB_C1), c=b2)
            sel(N, "kg_ff_geo", "Geometria fase-fase (C.3)", list(ci.TAB_C3), c=b3)
            sel(N, "alfa", "α (C.3 / 9.4.2)", [0.5, 0.33], c=b1)
        else:
            num(N, "kg_ft", "kg fase-terra", 1.3, 1.0, 1.6, 0.01, c=b2)
            num(N, "kg_ff", "kg fase-fase", 1.45, 1.0, 1.9, 0.01, c=b3)
            sel(N, "alfa", "α (9.4.2)", [0.5, 0.33], c=b1)
        st.markdown("**Fator estatístico Kcs (Anexo C.3)**")
        k1, k2, k3, k4 = st.columns(4)
        sel(N, "kcs_modo", "Kcs", ["Calculado (Anexo C.3)", "Referência Kiessling (1,05)", "Informado"], c=k1,
            help="Kcs = U10% de suportabilidade / sobretensão de 2 % de excedência. Calculado por modelo gaussiano reconstituído "
                 "(NECESSITA VALIDAÇÃO com a Figura C.1). Referência: Kiessling 2.4.5.3 (eq. 2.47/2.48): Kcs = 1,05 ≈ risco de 0,001 para distâncias "
                 "elétricas; fase-fase = 1,4·Kcs·U2 % (coerente com rs = 1,4).")
        if G(N, "kcs_modo") == "Informado":
            num(N, "kcs_man", "Kcs", 1.05, 0.8, 2.0, 0.01, c=k2)
        else:
            num(N, "cv_sfl", "CV da sobretensão (%)", 15.0, 1.0, 50.0, 0.5, c=k2, help="PREMISSA – vem do estudo de manobra.")
            num(N, "cv_fl", "CV da rigidez do gap (%)", 5.0, 1.0, 20.0, 0.5, c=k3, help="PREMISSA.")
            num(N, "n_gaps", "Nº de gaps em paralelo", 3, 1, 3000, 1, c=k4)
            sel(N, "risco", "Risco de falha admitido", [1e-2, 1e-3, 1e-4], 1e-3, c=k1, help="Tabela 6.4 das Diretrizes ilegível no acervo: PREMISSA.")
    with t2:
        st.caption("NBR 5422:2024, 9.3.1 (fuga), 9.x (distância de arco) e 14.2 (cargas); livro 'Projeto Elétrico de LTs' 4.6/4.7.")
        a1, a2, a3 = st.columns(3)
        sel(N, "tipo_isol", "Tipo de isolador", ["Vidro", "Porcelana", "Polimérico"], c=a1)
        sel(N, "tipo_cadeia", "Tipo de cadeia", ["Suspensão em I", "Suspensão em V", "Ancoragem"], c=a2)
        sel(N, "fuga_modo", "Fuga específica", ["Nível de poluição (IEC 60815:1986)", "Informar"], c=a3)
        if G(N, "fuga_modo") == "Informar":
            num(N, "fuga_esp", "Fuga específica (mm/kV fase-fase sobre Um)", 20.0, 5.0, 80.0, 0.5, c=a1)
        else:
            sel(N, "poluicao", "Nível de poluição", list(ci.FUGA_IEC60815_1986), c=a1)
        chk(N, "edital", f"Aplicar mínimo de {ci.FUGA_EDITAL:g} mm/kV (Diretrizes 6.8.2)", True, c=a2)
        if G(N, "tipo_isol", "Vidro") == "Polimérico":
            num(N, "l_arco_mm", "Distância de arco (mm)", 1300.0, 100.0, 6000.0, 10.0, c=a3)
            num(N, "fuga_total_mm", "Fuga total (mm)", 4000.0, 100.0, 20000.0, 10.0, c=a1)
        else:
            num(N, "passo_mm", "Passo da unidade (mm)", 146.0, 80.0, 300.0, 1.0, c=a3)
            num(N, "fuga_unid_mm", "Fuga da unidade (mm)", 292.0, 100.0, 700.0, 1.0, c=a1)
            num(N, "c1_c", "Capacitância à terra / própria (c1/C)", 0.1, 0.0, 0.5, 0.01, c=a2, help="PREMISSA: 0,05 a 0,2 típico; vem do fabricante.")
            num(N, "v_unid_adm", "Tensão admissível por unidade (kV, 0 = não verificar)", 0.0, 0.0, 100.0, 1.0, c=a3)
        b1, b2, b3 = st.columns(3)
        num(N, "l_ferr", "Comprimento de ferragens (m)", 0.3, 0.0, 3.0, 0.05, c=b1)
        num(N, "n_min", "Nº mínimo de unidades", 1, 1, 60, 1, c=b2)
        st.markdown("**Carga mecânica da cadeia (14.2)** – 0 = não verificar")
        m1, m2, m3_, m4_ = st.columns(4)
        num(N, "rbl_kn", "Carga de ruptura da unidade (kN)", 0.0, 0.0, 1000.0, 10.0, c=m1)
        num(N, "n_cad", "Nº de cadeias em paralelo", 1, 1, 6, 1, c=m2)
        num(N, "carga_sv", "Carga sem vento (kN)", 0.0, 0.0, 2000.0, 1.0, c=m3_)
        num(N, "carga_cv", "Carga com vento (kN)", 0.0, 0.0, 2000.0, 1.0, c=m4_)
    with t3:
        st.caption("NBR 5422:2024, 8.9 e 9.6: balanço dos condutores com vento de frequência fundamental (TR ≥ 10 anos) e de manobra (TR ≥ 2 anos), do Módulo 3.")
        cabo = _cabo_cond_m4()
        st.markdown(f"Condutor: **{circuito(1).get('cond') or 'não selecionado'}** · d = {cabo.get('diametro_mm') or '—'} mm · "
                    f"m = {cabo.get('massa_kg_m') or '—'} kg/m")
        cvs = _casos_vento_m5()
        if cvs:
            st.dataframe(pd.DataFrame([[k, v[0], v[1]] for k, v in cvs.items()], columns=["Caso", "V_P (m/s)", "q0 (Pa)"]).round(2), hide_index=True)
        else:
            st.warning("Estudo de ventos (Módulo 3) incompleto: o balanço não será verificado.")
        a1, a2, a3 = st.columns(3)
        num(N, "lm", "Vão médio Lm (m)", float(G("4", "lm", 400.0)), 10.0, 2000.0, 5.0, c=a1)
        num(N, "lp", "Vão gravante Lp (m)", float(G("4", "lp", 350.0)), 10.0, 2000.0, 5.0, c=a2)
        num(N, "flecha", "Flecha máx. (m, meio do vão)", float(G("4", "flecha", 0.0)), 0.0, 100.0, 0.05, c=a3)
        num(N, "xf", "Semi-largura do fuste/estrutura (m)", 0.5, 0.0, 10.0, 0.05, c=a1, help="Silhueta simplificada: confirmar em modelo 3D da estrutura.")
        num(N, "h_corpo", "Altura do corpo abaixo da fase mais baixa (m)", 10.0, 0.0, 100.0, 0.5, c=a2)
        num(N, "d_trab", "Distância de trabalho em linha viva (m, 0 = não informada)", 0.0, 0.0, 10.0, 0.05, c=a3,
            help="7.5 (IEC 61472 / IEEE 516) – não consta no acervo.")
    with t4:
        st.caption("Diretrizes de projeto básico 3.2.13 e 4.7; IEC 60099 (não consultada: NECESSITA VALIDAÇÃO). 0 = não informado.")
        p1, p2, p3, p4 = st.columns(4)
        num(N, "uc_ur", "Uc/Ur (critério de MCOV)", 0.8, 0.5, 1.0, 0.01, c=p1, help="PREMISSA – catálogo do fabricante.")
        num(N, "ke", "ke (fator de falta à terra)", 1.4, 1.0, 2.0, 0.05, c=p2, help="Sistema solidamente aterrado ≈ 1,4. PREMISSA.")
        num(N, "ktov", "Ktov (capacidade de TOV)", 1.10, 1.0, 1.5, 0.01, c=p3, help="Curva TOV do fabricante. PREMISSA.")
        num(N, "ur_cat", "Ur do catálogo adotado (kV)", 0.0, 0.0, 800.0, 3.0, c=p4)
        num(N, "ur_estudo", "Ur do estudo (kV)", 0.0, 0.0, 800.0, 3.0, c=p1)
        num(N, "margem_equip", "Margem no equipamento (%)", 15.0, 0.0, 50.0, 1.0, c=p2, help="Diretrizes 3.2.13: 15 % nos terminais do equipamento.")
        num(N, "bil", "NBI do equipamento (kV)", 0.0, 0.0, 3000.0, 10.0, c=p3)
        num(N, "sil", "NIM do equipamento (kV)", 0.0, 0.0, 2500.0, 10.0, c=p4)
        num(N, "ures_fr", "Ures 8/20 µs (kV)", 0.0, 0.0, 3000.0, 1.0, c=p1)
        num(N, "ures_fl", "Ures 30/60 µs (kV)", 0.0, 0.0, 3000.0, 1.0, c=p2)
        num(N, "usurto", "Sobretensão incidente de manobra (kV)", 0.0, 0.0, 3000.0, 1.0, c=p3)
        num(N, "zc", "Impedância de surto Zc (Ω)", 0.0, 0.0, 1000.0, 5.0, c=p4)
        num(N, "km_surto", "Comprimento de linha para a energia (km)", 0.0, 0.0, 1000.0, 1.0, c=p1)
        num(N, "e_cat", "Capacidade de energia (kJ/kV de Ur)", 0.0, 0.0, 20.0, 0.1, c=p2)
        num(N, "i_surto", "Corrente de surto (kA) – Módulo 16", 0.0, 0.0, 300.0, 1.0, c=p3)
        num(N, "u_ind_med", "Tensão induzida média (kV)", 0.0, 0.0, 3000.0, 10.0, c=p4)
    e = entrada_m5()
    chave = json.dumps(e, sort_keys=True, default=str)
    r = _calc5_cache(chave) if e["um_kv"] > 0 else dict(erros=["Informe a tensão máxima do sistema (Módulo 1)."], avisos=[], pendencias=[])
    with t5:
        if r["erros"]:
            for m in r["erros"]:
                st.warning(m)
        else:
            ds, iso, at_, kc, pr = r["dist"], r["isol"], r["atm"], r["kcs"], r["pr"]
            m1, m2, m3_, m4_ = st.columns(4)
            m1.metric("δ", f"{at_['delta']:.4f}")
            m2.metric("Kcs", f"{kc['kcs']:.3f}")
            m3_.metric("d fase-terra exigida (m)", f"{ds['req_ft']:.3f}")
            m4_.metric("d fase-fase exigida (m)", f"{ds['req_ff']:.3f}")
            st.dataframe(pd.DataFrame([["Frequência fundamental", ds["ft_ff"], ds["ff_ff"]], ["Frente lenta", ds["ft_fl"], ds["ff_fl"]],
                                       ["Frente rápida", ds["ft_fr"], ds["ff_fr"]]], columns=["Solicitação", "Fase-terra (m)", "Fase-fase (m)"]).round(3),
                         hide_index=True)
            n1, n2, n3, n4 = st.columns(4)
            n1.metric("Isoladores por cadeia", f"{iso['n']}")
            n2.metric("Distância de arco (m)", f"{iso['l_arco']:.3f}", "atende" if iso["ok_arco"] else "NÃO atende")
            n3.metric("Fuga total (mm)", f"{iso['fuga_tot']:.0f}", "atende" if iso["ok_fuga"] else "NÃO atende")
            n4.metric("Ur do para-raios (kV)", f"{pr['ur_adot']:.0f}")
            if iso.get("dist_v"):
                st.caption(f"Unidade mais solicitada: {iso['v_max_unid']:.1f} kV (média {iso['v_med_unid']:.1f} kV) · eficiência {iso['efic']:.0f} %")
            bal = r.get("balanco")
            if bal:
                st.dataframe(pd.DataFrame([[l["i"] + 1] + [(f"{l[k][0]:.2f} / {l[k][1]:.2f} " + ("✓" if l[k][2] else "✗")) if k in l else "—"
                                                          for k in ("ff", "fl", "fr")] for l in bal["fases"]],
                                          columns=["Fase", "Freq. (d / exigida m)", "Manobra", "Descarga"]), hide_index=True)
            for m in r["avisos"] + r["pendencias"] + pr["avisos"]:
                st.info(m)
        st.divider()
        st.markdown("**Relatório (padrão BK) e impressão**")

        def _g5(caminho):
            import relatorio_m5
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m5.gerar(caminho, proj, e, r, dict(ss["dados"].get(N, {})),
                               codigo=(G("proj", "numero") or "BK-LT-MC") + "-M5", rev=G("proj", "revisao") or "R0")
        if ERRO_RELATORIO:
            st.error(ERRO_RELATORIO)
        elif r["erros"]:
            st.info("Preencha os dados pendentes para liberar o relatório e a impressão.")
            r1, r2 = st.columns(2)
            r1.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m5_off", disabled=True)
            r2.button("🖨️ Gerar PDF para impressão", key="btn_pdf_m5_off", disabled=True)
        else:
            if st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m5"):
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    caminho = os.path.join(td, "relatorio.docx")
                    _g5(caminho)
                    with open(caminho, "rb") as fh:
                        ss["_rel_m5"] = fh.read()
            if ss.get("_rel_m5"):
                st.download_button("Baixar relatório do Módulo 5 (.docx)", ss["_rel_m5"], file_name="Relatorio_Modulo5_Isolamento.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m5")
            botao_imprimir("m5", "Relatorio_Modulo5_Isolamento.pdf", _g5)
        botoes(5, so_limpar=True)


# ------------------------------------------------------------------------------
# Módulo 6 — Aterramento de estruturas (pé de torre / contrapeso)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _calc6_cache(chave_json):
    import json
    import calc_aterramento as ca
    return ca.calcular(json.loads(chave_json))


def entrada_m6():
    """Entrada do motor calc_aterramento a partir do estado do app. Retorna (entrada, db_aterramento, avisos)."""
    import calc_aterramento as ca
    N = "6"
    dbat = ca.carregar_db()
    modo = G(N, "modo_solo", "Uniforme")
    pts = [p for p in (G(N, "wenner") or []) if p.get("a") and p.get("R")]
    fs = G(N, "fator_sazonal", 1.0)
    rho_w = [ca.rho_wenner(p["a"], p["R"]) for p in pts]
    fit = None
    if modo == "Medições Wenner (2 camadas)" and len(pts) >= 4:
        fit = ca.ajustar_2camadas([p["a"] for p in pts], rho_w)
    mats = {m["nome"]: m for m in dbat["materiais"]}
    cabos = {c["nome"]: c for c in dbat["cabos"]}
    cab = cabos.get(G(N, "cabo_at", "Aço Cobreado 40% - 25 mm²")) or dbat["cabos"][0]
    mat = mats.get(G(N, "material", "Aço Cobreado 40%")) or dbat["materiais"][0]
    conx = {c["nome"]: c["tm"] for c in dbat["conexoes"]}
    e = dict(modo_solo="Uniforme" if modo != "2 camadas (ρ1, ρ2, h1)" and not fit else "2 camadas",
             rho=G(N, "rho", 500.0) * fs, n_pernas=int(G(N, "n_pernas", 4)), L=G(N, "L", 30.0), h=G(N, "h", 0.5),
             d_cabo_mm=cab["d_ext"], r_meta=G(N, "r_meta", 20.0), i_falta_ka=G(N, "i_falta", 4.181), t_falta=G(N, "t_falta", 0.5),
             i_desc_ka=G(N, "i_desc", 31.1), material=mat, tm=conx.get(G(N, "conexao", "Mecânica (Aparafusada ou por pressão)"), 250),
             ta=G(N, "ta", 26.0), fator_corrente=G(N, "fator_corrente", 100.0) / 100.0, fracao_terra=G(N, "fracao_terra", 100.0) / 100.0,
             rho_sup=G(N, "rho", 500.0) * fs, rho_brita=G(N, "rho_brita", 0.0) or None, h_brita=G(N, "h_brita", 0.1),
             peso=int(G(N, "peso", 70)), ang0=0.0)
    if fit:
        e.update(rho1=fit["rho1"] * fs, rho2=fit["rho2"] * fs, h1=fit["h1"])
    elif modo == "2 camadas (ρ1, ρ2, h1)":
        e.update(modo_solo="2 camadas", rho1=G(N, "rho1", 300.0) * fs, rho2=G(N, "rho2", 1000.0) * fs, h1=G(N, "h1", 2.0))
        e["rho_sup"] = e["rho1"]
    e["_fit"] = fit
    e["_rho_w"] = rho_w
    e["_cabo"] = cab
    e["_pts"] = pts
    return e, dbat


def mod6():
    import json
    import calc_aterramento as ca
    N = "6"
    t1, t2, t3, t4 = st.tabs(["Solo", "Contrapeso e meta", "Curto-circuito e tensões", "Resultados e relatório"])
    dbat = ca.carregar_db()
    with t1:
        st.caption("Resistividade para o cálculo da resistência de pé de torre. O fator sazonal multiplica toda a resistividade (PREMISSA: 1,0).")
        a1, a2 = st.columns(2)
        sel(N, "modo_solo", "Modelo do solo", ["Uniforme", "2 camadas (ρ1, ρ2, h1)", "Medições Wenner (2 camadas)"], c=a1,
            help="Wenner: ρ = 2π·a·R; a estratificação é ajustada por mínimos quadrados (mín. 4 medições).")
        num(N, "fator_sazonal", "Fator sazonal (×)", 1.0, 0.5, 3.0, 0.05, c=a2, help="Correção para a estação seca (maior ρ). PREMISSA.")
        modo = G(N, "modo_solo", "Uniforme")
        if modo == "Uniforme":
            num(N, "rho", "Resistividade aparente ρ (Ω·m)", 500.0, 1.0, 50000.0, 10.0)
        elif modo == "2 camadas (ρ1, ρ2, h1)":
            b1, b2, b3 = st.columns(3)
            num(N, "rho1", "ρ1 – camada superior (Ω·m)", 300.0, 1.0, 50000.0, 10.0, c=b1)
            num(N, "rho2", "ρ2 – camada inferior (Ω·m)", 1000.0, 1.0, 50000.0, 10.0, c=b2)
            num(N, "h1", "Espessura h1 (m)", 2.0, 0.3, 50.0, 0.1, c=b3)
        else:
            base = G(N, "wenner") or [{"a": v, "R": None} for v in (1.0, 2.0, 4.0, 8.0, 16.0, 32.0)]
            df = st.data_editor(pd.DataFrame(base), num_rows="dynamic", hide_index=True, key=_k(N, "ed_wenner"),
                                column_config={"a": st.column_config.NumberColumn("Espaçamento a (m)", min_value=0.1),
                                               "R": st.column_config.NumberColumn("Resistência medida R (Ω)", min_value=0.0, format="%.3f")})
            S(N, "wenner", [{"a": None if pd.isna(r_["a"]) else float(r_["a"]), "R": None if pd.isna(r_["R"]) else float(r_["R"])}
                            for r_ in df.to_dict("records")])
    with t2:
        c1, c2, c3, c4 = st.columns(4)
        num(N, "n_pernas", "Nº de pernas radiais", 4, 1, 8, 1, c=c1, help="Diretrizes: 4 ou 6 pernas (cabos contrapeso) por estrutura.")
        num(N, "L", "Comprimento de cada perna (m)", 30.0, 3.0, 200.0, 1.0, c=c2)
        num(N, "h", "Profundidade (m)", 0.5, 0.2, 2.0, 0.05, c=c3, help="Prática: 0,5 m (livro Projeto Elétrico de LT).")
        num(N, "r_meta", "Resistência de referência (Ω)", 20.0, 1.0, 100.0, 0.5, c=c4, help="Diretrizes de projeto básico: em geral ≤ 20 Ω (valor médio).")
        nomes = [c["nome"] for c in dbat["cabos"]]
        sel(N, "cabo_at", "Cabo contrapeso (aba 'DB Aterramento')", nomes, "Aço Cobreado 40% - 25 mm²")
        num(N, "i_desc", "Corrente de descarga p/ resistência impulsiva (kA)", 31.1, 1.0, 200.0, 0.5,
            help="PREMISSA: mediana da distribuição de descargas (31,1 kA, CIGRE/IEEE). Depende da densidade de descargas locais.")
    with t3:
        d1, d2, d3 = st.columns(3)
        sel(N, "material", "Material do condutor", [m["nome"] for m in dbat["materiais"]], "Aço Cobreado 40%", c=d1)
        sel(N, "conexao", "Tipo de conexão (limita Tm)", [c["nome"] for c in dbat["conexoes"]], c=d2)
        num(N, "ta", "Temperatura ambiente (°C)", 26.0, -10.0, 60.0, 0.5, c=d3)
        d4, d5, d6 = st.columns(3)
        num(N, "i_falta", "Corrente de falta fase-terra If (kA)", 4.181, 0.1, 200.0, 0.1, c=d4, help="Do estudo de curto-circuito.")
        num(N, "t_falta", "Duração do curto (s)", 0.5, 0.05, 5.0, 0.05, c=d5)
        num(N, "fator_corrente", "Parcela de If no condutor (%)", 100.0, 10.0, 100.0, 5.0, c=d6,
            help="A planilha cita 60 % do curto para o condutor da malha enterrada, devido à distribuição.")
        d7, d8, d9 = st.columns(3)
        num(N, "fracao_terra", "Parcela de If que escoa pela torre (%)", 100.0, 1.0, 100.0, 1.0, c=d7,
            help="Define o GPR. 100 % é conservador (o cabo guarda e as torres vizinhas drenam parte).")
        sel(N, "peso", "Pessoa (peso)", [50, 70], 70, c=d8)
        num(N, "rho_brita", "ρ da camada superficial (Ω·m, 0 = sem)", 0.0, 0.0, 20000.0, 100.0, c=d9)
        if G(N, "rho_brita", 0.0):
            num(N, "h_brita", "Espessura da camada superficial (m)", 0.1, 0.02, 1.0, 0.01)
    e, dbat = entrada_m6()
    ejson = json.dumps({k: v for k, v in e.items() if not k.startswith("_")}, default=float, sort_keys=True)
    r = _calc6_cache(ejson)
    with t4:
        if r["erros"]:
            for m in r["erros"]:
                st.warning(m)
        else:
            if e.get("_fit"):
                f_ = e["_fit"]
                st.info(f"Estratificação ajustada: ρ1 = {f_['rho1']:.0f} Ω·m, ρ2 = {f_['rho2']:.0f} Ω·m, h1 = {f_['h1']:.2f} m (erro RMS {f_['erro_rms_pct']:.1f} %).")
            elif G(N, "modo_solo") == "Medições Wenner (2 camadas)":
                st.warning("Informe ao menos 4 medições Wenner (a, R) para ajustar as camadas; enquanto isso, ρ uniforme = " + f"{e['rho']:.0f} Ω·m.")
            m1, m2, m3_, m4_ = st.columns(4)
            m1.metric("R de pé de torre (Ω)", f"{r['R']:.2f}")
            m2.metric("Meta (Ω)", f"{e['r_meta']:.1f}", "ATENDE" if r["atende"] else "NÃO ATENDE", delta_color="normal" if r["atende"] else "inverse")
            m3_.metric("R impulsiva (Ω)", f"{r['imp']['Ri']:.2f}")
            m4_.metric("Seção mín. do condutor (mm²)", f"{r.get('secao_min', 0):.1f}")
            cab = e["_cabo"]
            ok_sec = r.get("secao_min", 0) <= cab["s_ef"]
            st.caption(f"Cabo {cab['nome']}: seção efetiva {cab['s_ef']:g} mm² – " + ("ATENDE à seção mínima" if ok_sec else "NÃO ATENDE à seção mínima"))
            st.markdown("**R × comprimento da perna**")
            st.dataframe(pd.DataFrame(r["curva"], columns=["L (m)", "R (Ω)"]).round(2), hide_index=True)
            st.markdown("**Menor perna que atende à meta, por resistividade (mesmo nº de pernas e profundidade)**")
            st.dataframe(pd.DataFrame([[a_, f"{b_:g}" if b_ else "> 80", round(c_, 2)] for a_, b_, c_ in r["tabela_rho"]],
                                      columns=["ρ (Ω·m)", "L mínimo (m)", "R obtida (Ω)"]), hide_index=True)
            g1, g2, g3 = st.columns(3)
            g1.metric("GPR = If·R (kV)", f"{r['gpr'] / 1000:.1f}")
            g2.metric("E_toque adm. (V)", f"{r['lim']['toque']:.0f}")
            g3.metric("E_passo adm. (V)", f"{r['lim']['passo']:.0f}")
            for m in r["avisos"]:
                st.info(m)
            st.caption("O GPR é a elevação de potencial da estrutura; a verificação de passo/toque no terreno requer o perfil de potencial "
                       "(PENDENTE – não calculado). Comportamento impulsivo: CIGRE/IEEE (ionização do solo).")
        st.divider()
        st.markdown("**Relatório (padrão BK) e impressão**")

        def _g6(caminho):
            import relatorio_m6
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m6.gerar(caminho, proj, e, r, dict(ss["dados"].get(N, {})),
                               codigo=(G("proj", "numero") or "BK-LT-MC") + "-M6", rev=G("proj", "revisao") or "R0")
        if ERRO_RELATORIO:
            st.error(ERRO_RELATORIO)
        elif r["erros"]:
            st.info("Preencha os dados pendentes para liberar o relatório e a impressão.")
            r1, r2 = st.columns(2)
            r1.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m6_off", disabled=True)
            r2.button("🖨️ Gerar PDF para impressão", key="btn_pdf_m6_off", disabled=True)
        else:
            if st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m6"):
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    caminho = os.path.join(td, "relatorio.docx")
                    _g6(caminho)
                    with open(caminho, "rb") as fh:
                        ss["_rel_m6"] = fh.read()
            if ss.get("_rel_m6"):
                st.download_button("Baixar relatório do Módulo 6 (.docx)", ss["_rel_m6"], file_name="Relatorio_Modulo6_Aterramento.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m6")
            botao_imprimir("m6", "Relatorio_Modulo6_Aterramento.pdf", _g6)
        botoes(6, so_limpar=True)


# ------------------------------------------------------------------------------
# Módulo 7 — Dimensionamento ELÉTRICO do Condutor e Cabo Guarda
# ----------------------------------------------------------------------------
def entrada_m7():
    """Entrada do motor calc_condutor a partir do estado do app (defaults iguais aos dos widgets)."""
    N = "7"
    c1 = circuito(1)
    p_def = c1["mva"] * c1["fp"] * 1000.0
    e = dict(p_kw=G(N, "p_kw", p_def), u_kv=G(N, "u_kv", c1["un"]), cosphi=G(N, "cosphi", c1["fp"]),
             comp_km=G(N, "comp_km", G("sis", "km", 80.0) or 80.0), perda_pct=G(N, "perda_pct", 2.0), dv_pct=G(N, "dv_pct", 5.0),
             n_sub=int(c1.get("cabos_fase") or 1), x_km=G(N, "x_km", 0.40), fator_cat=G(N, "fator_cat", 3.0) / 100.0,
             t_norm=G(N, "t_norm", G("3", "t_cc_max", 75.0)), t_emerg=G(N, "t_emerg", G("3", "t_cc_emerg", 90.0)),
             alt_m=G(N, "alt_m", G("3", "alt", 0.0) or 0.0), emis=G(N, "emis", 0.5), absort=G(N, "absort", 0.5), rad=G(N, "rad", 1000.0),
             ta=dict(verao_dia=G(N, "ta_vd", 33.0), verao_noite=G(N, "ta_vn", 25.0),
                     inverno_dia=G(N, "ta_id", 32.0), inverno_noite=G(N, "ta_in", 24.0)),
             vento_ons=0.9 if G(N, "uf_ons", "SC") in cc_mod.UF_VENTO_09 else 1.0,
             vento_ieee=G(N, "vento_ieee", 0.61), ta_max=G(N, "ta_max", G("3", "t_max", 40.0)),
             icc_ka=G(N, "icc_ka", 10.0), t_falta=G(N, "t_falta", 0.5), theta_i=G(N, "theta_i", 40.0), theta_f=G(N, "theta_f", 200.0),
             frac_guarda=G(N, "frac_guarda", 100.0) / 100.0, t_guarda=G(N, "theta_i", 40.0))
    cabo = db.obter_cabo(c1.get("cond")) if c1.get("cond") else {}
    guardas = []
    for k in (("cg1",) if G("cfg", "n_cg", 1) != 2 else ("cg1", "cg2")):
        cod = G("cfg", k)
        if cod:
            guardas.append(db.obter_cabo(cod))
    cands = db.listar_cabos(USOS_CHAVE["condutores"]) if G(N, "comparar", True) else []
    return e, cabo, guardas, cands


def mod7():
    N = "7"
    t1, t2, t3, t4, t5 = st.tabs(["Dados de entrada", "Condutor (critérios)", "Ampacidade", "Cabo guarda / OPGW", "Resultados e relatório"])
    c1 = circuito(1)
    with t1:
        st.markdown("##### Cabos selecionados no projeto")
        info_cabos()
        st.caption("Dimensionamento elétrico (não mecânico). Valores iniciais vêm do Módulo 1 (circuito 1) e do Módulo 3; ajuste aqui se necessário.")
        a1, a2, a3, a4 = st.columns(4)
        num(N, "p_kw", "Potência ativa da LT (kW)", float(c1["mva"] * c1["fp"] * 1000.0), 0.0, 5e6, 100.0, c=a1)
        num(N, "u_kv", "Tensão nominal (kV)", float(c1["un"]), 1.0, 1000.0, 0.5, c=a2)
        num(N, "cosphi", "Fator de potência", float(c1["fp"]), 0.1, 1.0, 0.01, c=a3)
        num(N, "comp_km", "Comprimento da LT (km)", float(G("sis", "km", 80.0) or 80.0), 0.1, 2000.0, 0.5, c=a4)
        b1, b2, b3, b4 = st.columns(4)
        num(N, "perda_pct", "Perda joule máxima (% de P)", 2.0, 0.1, 20.0, 0.1, c=b1)
        num(N, "dv_pct", "Queda de tensão máxima (%)", 5.0, 0.1, 20.0, 0.1, c=b2)
        num(N, "x_km", "Reatância X' da fase (Ω/km)", 0.40, 0.0, 2.0, 0.01, c=b3,
            help="PREMISSA: use o valor calculado no Módulo 2. Zero = só resistência.")
        num(N, "fator_cat", "Fator de catenária (%)", 3.0, 0.0, 20.0, 0.5, c=b4, help="Acréscimo de comprimento do cabo (planilha: 3 %).")
        d1, d2, d3 = st.columns(3)
        num(N, "t_norm", "Temperatura normal do condutor (°C)", float(G("3", "t_cc_max", 75.0)), 20.0, 150.0, 1.0, c=d1)
        num(N, "t_emerg", "Temperatura de emergência (°C)", float(G("3", "t_cc_emerg", 90.0)), 20.0, 150.0, 1.0, c=d2)
        chk(N, "comparar", "Comparar com todos os condutores do catálogo", True, c=d3)
    with t3:
        st.caption("ONS: NT Sazonal de LTs (reproduz a aba 'Ampacidade - ONS'). IEEE: Std 738-2006, regime permanente.")
        f1, f2, f3, f4 = st.columns(4)
        sel(N, "uf_ons", "UF (vento 0,9 m/s: PR, RS, SC, RJ, ES, SE, AL)", UFS, "SC", c=f1)
        num(N, "alt_m", "Altitude (m)", float(G("3", "alt", 0.0) or 0.0), 0.0, 5000.0, 10.0, c=f2)
        num(N, "emis", "Emissividade", 0.5, 0.1, 1.0, 0.01, c=f3, help="Alumínio nu: 0,5 (planilha).")
        num(N, "absort", "Absortividade", 0.5, 0.1, 1.0, 0.01, c=f4)
        g1, g2, g3, g4 = st.columns(4)
        num(N, "ta_vd", "Ta verão/dia (°C)", 33.0, -10.0, 60.0, 0.5, c=g1)
        num(N, "ta_vn", "Ta verão/noite (°C)", 25.0, -10.0, 60.0, 0.5, c=g2)
        num(N, "ta_id", "Ta inverno/dia (°C)", 32.0, -10.0, 60.0, 0.5, c=g3)
        num(N, "ta_in", "Ta inverno/noite (°C)", 24.0, -10.0, 60.0, 0.5, c=g4)
        h1, h2, h3 = st.columns(3)
        num(N, "rad", "Radiação solar (W/m²)", 1000.0, 0.0, 1400.0, 10.0, c=h1)
        num(N, "vento_ieee", "Vento IEEE (m/s)", 0.61, 0.0, 10.0, 0.01, c=h2, help="IEEE 738: 0,61 m/s (2 ft/s).")
        num(N, "ta_max", "Ta máx. IEEE (°C)", float(G("3", "t_max", 40.0)), 0.0, 60.0, 0.5, c=h3)

    with t4:
        c1_, c2_, c3_, c4_ = st.columns(4)
        num(N, "icc_ka", "Corrente de curto-circuito (kA)", 10.0, 0.0, 200.0, 0.5, c=c1_)
        num(N, "t_falta", "Duração da falta (s)", 0.5, 0.05, 5.0, 0.05, c=c2_)
        num(N, "frac_guarda", "Parcela da corrente no guarda (%)", 100.0, 1.0, 100.0, 1.0, c=c3_,
            help="100 % = conservador. Valor real depende da malha de aterramento/torres.")
        num(N, "theta_i", "Temperatura inicial (°C)", 40.0, -10.0, 100.0, 1.0, c=c4_)
        num(N, "theta_f", "Temperatura final admissível (°C)", 200.0, 50.0, 400.0, 5.0)
    e, cabo, guardas, cands = entrada_m7()
    r = cc_mod.calcular(e, cabo, guardas, cands)
    with t2:
        if r["erros"]:
            for m in r["erros"]:
                st.warning(m)
        else:
            k = r["crit"]
            m1, m2, m3_, m4_ = st.columns(4)
            m1.metric("Corrente nominal (A)", f"{k['i']:.1f}")
            m2.metric("R máx. por perda (Ω/km, por cabo)", f"{k['r_perda_cabo']:.4f}")
            m3_.metric("R máx. por queda de tensão (Ω/km)", f"{k['r_dv_cabo']:.4f}")
            m4_.metric("Seção mín. equiv. Al (mm²)", f"{k['s_min_mm2']:.0f}")
            if "cabo" in r:
                cb = r["cabo"]
                st.markdown(f"**Condutor adotado: {cabo.get('codigo')}** — R({e['t_norm']:g} °C) = "
                            f"{cb['r_op']:.4f} Ω/km" if cb["r_op"] else "Sem resistência no catálogo")
                tab = [["Perda joule", "ATENDE" if cb["ok_perda"] else "NÃO ATENDE"],
                       ["Queda de tensão", "ATENDE" if cb["ok_dv"] else "NÃO ATENDE"],
                       ["Corrente × ampacidade do catálogo", "—" if cb["ok_i"] is None else ("ATENDE" if cb["ok_i"] else "NÃO ATENDE")]]
                st.dataframe(pd.DataFrame(tab, columns=["Critério", "Status"]), hide_index=True)
                if r.get("perdas"):
                    st.metric("Perdas joule na corrente nominal", f"{r['perdas']['mw']:.2f} MW ({r['perdas']['pct']:.2f} % de P)")
            if cands:
                st.markdown("**Catálogo – condutores que atendem aos critérios 1 a 3**")
                dfc = pd.DataFrame([{"Código": c["codigo"], "Tipo": c["tipo"], "Seção (mm²)": c["secao"], "R op. (Ω/km)": c["r_op"],
                                     "Ampacidade (A)": c.get("amp_a"), "Atende": "SIM" if c["ok"] else "não"} for c in r["candidatos"]])
                so = st.checkbox("Só os que atendem", True, key=_k(N, "so_ok"))
                st.dataframe(dfc[dfc["Atende"] == "SIM"] if so else dfc, hide_index=True)
            with st.expander("Diferenças em relação à planilha BK"):
                for n_ in cc_mod.NOTAS_PLANILHA:
                    st.markdown("- " + n_)
    with t3:
        if "cabo" not in r:
            st.info("Selecione o condutor (Módulo 1).")
        else:
            if "ons" in r:
                st.markdown("**ONS – NT Sazonal**")
                st.dataframe(pd.DataFrame([[l["epoca"], l["periodo"], l["ta"], l["normal"]["i"], l["normal"]["mva"], l["emergencia"]["i"], l["emergencia"]["mva"]]
                                           for l in r["ons"]["linhas"]],
                                          columns=["Época", "Período", "Ta (°C)", "I normal (A)", "MVA normal", "I emerg. (A)", "MVA emerg."]).round(2),
                             hide_index=True)
                for m in r["ons"]["avisos"]:
                    st.info(m)
            if "ieee" in r:
                st.markdown("**IEEE 738-2006**")
                i_ = r["ieee"]
                st.dataframe(pd.DataFrame([["Normal", e["t_norm"], i_["normal"]["qc"], i_["normal"]["qr"], i_["normal"]["qs"], i_["normal"]["i"]],
                                           ["Emergência", e["t_emerg"], i_["emergencia"]["qc"], i_["emergencia"]["qr"], i_["emergencia"]["qs"], i_["emergencia"]["i"]]],
                                          columns=["Condição", "Tc (°C)", "qc (W/m)", "qr (W/m)", "qs (W/m)", "I (A)"]).round(2), hide_index=True)
                if r.get("tc_op"):
                    st.metric("Temperatura do condutor na corrente nominal (IEEE 738)", f"{r['tc_op']:.1f} °C")
            if "amp_cat" in r:
                st.caption(f"Ampacidade do catálogo: {r['amp_cat']:g} A (valor do fabricante/planilha, condições não especificadas).")
    with t4:
        if not r.get("guardas"):
            st.info("Selecione o cabo guarda (Módulo 1 → Configuração da LT).")
        for g in r.get("guardas", []):
            st.markdown(f"**{g['codigo']}** — I²t = {g['i2t']:.1f} kA²·s · método: {g['metodo'] or '—'}")
            if g.get("ok") is not None:
                st.success(f"ATENDE (margem {g['margem']:.2f}×)") if g["ok"] else st.error(f"NÃO ATENDE (margem {g['margem']:.2f}×)")
            if g.get("r40"):
                st.caption(f"R a {e['t_guarda']:g} °C = {g['r40']:.4f} Ω/km")
            for m in g["avisos"]:
                st.warning(m)
    with t5:
        for m in r.get("avisos", []):
            st.info(m)
        st.markdown("**Relatório (padrão BK) e impressão**")

        def _g7(caminho):
            import relatorio_m7
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m7.gerar(caminho, proj, e, r, cabo, guardas, c1,
                               codigo=(G("proj", "numero") or "BK-LT-MC") + "-M7", rev=G("proj", "revisao") or "R0")
        if ERRO_RELATORIO:
            st.error(ERRO_RELATORIO)
        elif r["erros"] or "cabo" not in r:
            st.info("Selecione o condutor e preencha os dados para liberar o relatório e a impressão.")
            r1, r2 = st.columns(2)
            r1.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m7_off", disabled=True)
            r2.button("🖨️ Gerar PDF para impressão", key="btn_pdf_m7_off", disabled=True)
        else:
            if st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m7"):
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    caminho = os.path.join(td, "relatorio.docx")
                    _g7(caminho)
                    with open(caminho, "rb") as fh:
                        ss["_rel_m7"] = fh.read()
            if ss.get("_rel_m7"):
                st.download_button("Baixar relatório do Módulo 7 (.docx)", ss["_rel_m7"], file_name="Relatorio_Modulo7_Condutor_e_Cabo_Guarda.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m7")
            botao_imprimir("m7", "Relatorio_Modulo7_Condutor_e_Cabo_Guarda.pdf", _g7)
        botoes(7, so_limpar=True)


# ----------------------------------------------------------------------------
# Módulo 8 — Campo Elétrico e Magnético
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _calc8_cache(chave_json):
    import json
    import calc_campos as ccm
    return ccm.calcular_estudo(json.loads(chave_json))


def _faixa_m4():
    """Largura adotada da faixa (m) calculada no Módulo 4, ou None se o estudo estiver incompleto."""
    try:
        import calc_faixa as cf
        e4, _a, _b, _c = entrada_m4()
        r4 = cf.calcular(e4)
        return None if r4.get("erros") else float(r4["faixa"]["L_adot"])
    except Exception:
        return None


def entrada_m8(N="8"):
    """Monta a entrada do motor calc_campos a partir do estado do app (N = namespace do módulo chamador). Retorna (entrada, avisos, erros)."""
    avisos, erros = [], []
    g = geometria_atual()
    erros += list(g["erros"])
    n = int(G("cfg", "n_circ", 1))
    eixo = g.get("eixo_x", 0.0)
    reqs = {}
    for i in range(1, n + 1):
        c = circuito(i)
        cab = db.obter_cabo(c["cond"]) if c.get("cond") else {}
        if not cab:
            erros.append(f"Selecione o condutor do circuito {i} (Módulo 1 → Circuitos).")
            continue
        reqs[i] = mod2_calc._cabo_eletrico(cab, int(c["cabos_fase"]), c.get("esp_sub", 0.0))["req"]
    fases = [dict(nome=k["nome"], x=round(k["x"] - eixo, 4), y=round(k["y"], 4), circuito=k["circuito"], fase=k["fase"],
                  req=reqs.get(k["circuito"], 0.015)) for k in g["condutores"] if k["tipo"] == "fase"]
    rg = []
    for cod in [G("cfg", "cg1")] + ([G("cfg", "cg2")] if G("cfg", "n_cg", 1) == 2 else []):
        cab = db.obter_cabo(cod) if cod else {}
        rg.append((cab.get("diametro_mm") or 9.0) / 2000.0)
    guardas = [dict(x=round(k["x"] - eixo, 4), y=round(k["y"], 4), req=rg[j] if j < len(rg) else 0.0045)
               for j, k in enumerate([k for k in g["condutores"] if k["tipo"] == "guarda"])]
    if G(N, "h_modo", "Automático (altura na estrutura − flecha)").startswith("Autom"):
        h_min = min([k["y"] - k["flecha"] for k in g["condutores"] if k["tipo"] == "fase"] or [0.0])
    else:
        h_min = G(N, "h_min_man", 8.0)
    circs = {}
    for i in range(1, n + 1):
        c = circuito(i)
        if G(N, "orig_i", "Corrente nominal do circuito (Módulo 1)") == "Informada":
            i_n, i_e = G(N, f"i_n{i}", corrente_nominal(i)), G(N, f"i_e{i}", corrente_nominal(i))
        else:
            i_n = corrente_nominal(i)
            i_e = float(c.get("i_lim") or 0.0) or i_n
        circs[str(i)] = dict(un_kv=c["un"], umax_kv=c["umax"], i_normal=i_n, i_emerg=i_e, fp=c["fp"], status=c["status"])
    semi = None
    if G(N, "faixa_modo", "Do Módulo 4") == "Do Módulo 4":
        L = _faixa_m4()
        if L:
            semi = L / 2.0
        else:
            avisos.append("Faixa do Módulo 4 indisponível (estudo incompleto): o valor na borda da faixa não foi avaliado.")
    else:
        semi = G(N, "faixa_man", 30.0) / 2.0
    pts = PT.selecionados(ss["dados"], int(N))
    if not pts:
        pts = [dict(nome="Seção livre (perfil da LT em estudo)", tipo=PT.T_LIVRE, cen_i="Normal", dist_h=0.0, alt_ref=G(N, "h_obs", 1.5),
                    vizinhas=[], i=-1)]
    plist = []
    for p in pts:
        plist.append(dict(nome=p["nome"], tipo=p["tipo"], cen_i=p["cen_i"], dist_h=float(p["dist_h"] or 0.0),
                          alt_ref=float(p["alt_ref"] or 0.0), publico=G(N, f"pub{p['i']}", "Público em geral"), vizinhas=p["vizinhas"]))
    e = dict(fases=fases, guardas=guardas, incluir_guardas_e=bool(G(N, "guardas_e", False)), circs=circs,
             tensao_modo=G(N, "tensao_modo", "Nominal"), h_min=round(h_min, 3), h_obs=G(N, "h_obs", 1.5),
             x_min=G(N, "x_min", -50.0), x_max=G(N, "x_max", 50.0), dx=G(N, "dx", 0.5),
             rho=G(N, "rho", G("2", "rho", 1000.0)), freq=float(G("sis", "freq", 60)), semi_faixa=semi,
             req_viz=G(N, "r_viz_mm", 15.0) / 1000.0, passo_theta=10.0, pontos=plist)
    return e, avisos, erros


def _graf8(d, p, cen, semi):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    c = p["cenarios"][cen]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=(f"Campo elétrico a {p['h_obs']:g} m do solo (kV/m)", f"Densidade de fluxo magnético a {p['h_obs']:g} m do solo (µT)"))
    for lin, (k, ke, lim, un) in enumerate((("E", "E_est", p["lim_e"], "kV/m"), ("B", "B_est", p["lim_b"], "µT")), start=1):
        fig.add_trace(go.Scatter(x=c["x"], y=c[k], name="Total (com vizinhas, pior caso)", line=dict(color=AZUL, width=3),
                                 showlegend=lin == 1), row=lin, col=1)
        if p["vizinhas"]:
            fig.add_trace(go.Scatter(x=c["x"], y=c[ke], name="Somente LT em estudo", line=dict(color=CINZA_ESC, dash="dash"),
                                     showlegend=lin == 1), row=lin, col=1)
        fig.add_hline(y=lim, line_color="#C00000", line_dash="dot", row=lin, col=1,
                      annotation_text=f"{p['publico']}: {lim:g} {un}")
        if semi:
            for s in (-semi, semi):
                fig.add_vline(x=s, line_color="#7F7F7F", line_dash="dot", row=lin, col=1)
    fig.update_xaxes(title_text="Distância ao eixo da LT (m)", row=2, col=1)
    fig.update_layout(height=620, margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.15))
    return fig


def _graf8_3d(c, g):
    import plotly.graph_objects as go
    s = c["s3d_" + g]
    fig = go.Figure(go.Surface(x=s["x"], y=s["y"], z=s["z"], colorscale="Viridis"))
    fig.update_layout(height=480, margin=dict(l=0, r=0, t=30, b=0),
                      scene=dict(xaxis_title="x (m)", yaxis_title="altura (m)", zaxis_title="kV/m" if g == "E" else "µT"),
                      title="Campo elétrico" if g == "E" else "Densidade de fluxo magnético")
    return fig


def mod8():
    import json
    N = "8"
    t1, t2, t3 = st.tabs(["Dados de entrada", "Pontos e vizinhas", "Resultados e relatório"])
    n = int(G("cfg", "n_circ", 1))
    with t1:
        st.caption("Campo elétrico: método da simulação de cargas com imagens (Livro 'Cálculos Elétricos de LTs', cap. 6; ESS-2ITA-595-87, 3.1). "
                   "Campo magnético: Biot-Savart com imagens complexas de Deri (ESS-2ITA-595-87, 3.2). Limites: REN ANEEL 915/2021 "
                   "(NECESSITA VALIDAÇÃO com o texto oficial). Diretrizes de projeto básico 6.10.")
        st.markdown("**Ponto de cálculo**")
        a, b, c_, d = st.columns(4)
        num(N, "h_obs", "Altura do observador (m)", 1.5, 0.0, 5.0, 0.1, c=a, help="Diretrizes 6.10 e REN 915: 1,5 m acima do solo.")
        num(N, "x_min", "Perfil: x mínimo (m)", -50.0, -500.0, -1.0, 1.0, c=b, help="Distância ao eixo da LT, para a esquerda (50 m para cada lado por padrão).")
        num(N, "x_max", "Perfil: x máximo (m)", 50.0, 1.0, 500.0, 1.0, c=c_)
        num(N, "dx", "Passo do perfil (m)", 0.5, 0.1, 5.0, 0.1, c=d)
        st.markdown("**Premissas elétricas**")
        a, b, c_ = st.columns(3)
        sel(N, "tensao_modo", "Tensão para o campo elétrico", ["Nominal", "Máxima operativa"], c=a,
            help="Diretrizes 6.10 pede tensão nominal; 'Máxima operativa' é a condição conservadora.")
        sel(N, "orig_i", "Correntes de cálculo", ["Corrente nominal do circuito (Módulo 1)", "Informada"], c=b)
        chk(N, "guardas_e", "Incluir guardas aterrados no E (padrão: desprezados)", False, c=c_)
        if G(N, "orig_i", "Corrente nominal do circuito (Módulo 1)") == "Informada":
            cols = st.columns(n * 2)
            for i in range(1, n + 1):
                num(N, f"i_n{i}", f"Circuito {i}: corrente normal (A)", round(corrente_nominal(i), 1), 0.0, 5000.0, 10.0, c=cols[2 * i - 2])
                num(N, f"i_e{i}", f"Circuito {i}: corrente de emergência (A)", round(corrente_nominal(i), 1), 0.0, 5000.0, 10.0, c=cols[2 * i - 1])
        else:
            st.caption("Normal = corrente nominal do circuito (S/√3·Un). Emergência = limite de corrente informado no circuito (Módulo 1); "
                       "se não houver, igual à normal (PREMISSA). " +
                       " · ".join(f"C{i}: {corrente_nominal(i):.0f} A / {(circuito(i).get('i_lim') or corrente_nominal(i)):.0f} A" for i in range(1, n + 1)))
        st.markdown("**Geometria e meio**")
        a, b, c_ = st.columns(3)
        sel(N, "h_modo", "Altura dos condutores", ["Automático (altura na estrutura − flecha)", "Informar altura mínima"], c=a,
            help="Diretrizes 6.10: altura mínima à temperatura máxima. A geometria é deslocada para o condutor mais baixo ficar nessa altura.")
        if not G(N, "h_modo", "Automático (altura na estrutura − flecha)").startswith("Autom"):
            num(N, "h_min_man", "Altura mínima do condutor mais baixo (m)", 8.0, 3.0, 100.0, 0.1, c=b)
        num(N, "rho", "Resistividade do solo (Ω·m)", float(G("2", "rho", 1000.0)), 1.0, 20000.0, 10.0, c=c_,
            help="Só afeta o campo magnético (imagens complexas). Acima de ~50 Ω·m o efeito é pequeno.")
        sel(N, "faixa_modo", "Largura da faixa (para o valor na borda)", ["Do Módulo 4", "Informar"], c=a)
        if G(N, "faixa_modo", "Do Módulo 4") == "Informar":
            num(N, "faixa_man", "Largura total da faixa (m)", 30.0, 2.0, 400.0, 1.0, c=b)
        else:
            L4 = _faixa_m4()
            b.metric("Faixa do Módulo 4 (m)", f"{L4:.0f}" if L4 else "— (complete o Módulo 4)")
        num(N, "r_viz_mm", "Raio equivalente dos cabos das vizinhas (mm)", 15.0, 3.0, 60.0, 1.0, c=c_,
            help="PREMISSA: influência pequena. Informe o raio equivalente do feixe se conhecido.")
    with t2:
        bloco_pontos(8)
        sp = PT.selecionados(ss["dados"], 8)
        if sp:
            st.markdown("**Limite de referência por ponto** (REN 915: público fora da faixa; ocupacional apenas onde houver trabalhadores)")
            cols = st.columns(min(len(sp), 3))
            for j, p in enumerate(sp):
                sel(N, f"pub{p['i']}", p["nome"], list(__import__("calc_campos").LIMITES), c=cols[j % len(cols)])
    e, av8, er8 = entrada_m8()
    chave = json.dumps(e, sort_keys=True, default=str)
    r = _calc8_cache(chave) if not er8 else dict(erros=er8, avisos=[], pontos=[])
    with t3:
        if r["erros"]:
            for m in r["erros"]:
                st.warning(m)
        else:
            for m in av8 + r["avisos"]:
                st.info(m)
            linhas = []
            for p in r["pontos"]:
                for cen, d in p["cenarios"].items():
                    linhas.append({"Ponto": p["nome"], "Cenário": cen + (" ◄" if cen == p["cen_i"] else ""), "Limite": p["publico"],
                                   "E na borda/ponto (kV/m)": d["E_ref"], "E máx. perfil (kV/m)": d["E_max"], "Lim. E": p["lim_e"],
                                   "B na borda/ponto (µT)": d["B_ref"], "B máx. perfil (µT)": d["B_max"], "Lim. B": p["lim_b"],
                                   "Situação": "ATENDE" if d["ok_E"] and d["ok_B"] else "NÃO ATENDE"})
            st.dataframe(pd.DataFrame(linhas).round(3), hide_index=True)
            st.caption("◄ cenário de carga indicado no ponto. 'Borda/ponto' = valor na borda da faixa (pontos em seção livre, paralelismo, travessia) "
                       "ou na posição da rodovia/edificação; vizinhas com defasagem em pior caso quando assim cadastradas.")
            nomes = [p["nome"] for p in r["pontos"]]
            c1, c2 = st.columns(2)
            pn = c1.selectbox("Ponto para o gráfico", nomes, key=_k(N, "graf_pt"))
            p = r["pontos"][nomes.index(pn)]
            cen = c2.selectbox("Cenário", list(p["cenarios"]), index=list(p["cenarios"]).index(p["cen_i"]), key=_k(N, "graf_cen"))
            try:
                mostrar_plotly(_graf8(p["cenarios"][cen], p, cen, r.get("semi_faixa")))
                if "s3d_E" in p["cenarios"][cen]:
                    g1, g2 = st.columns(2)
                    with g1:
                        mostrar_plotly(_graf8_3d(p["cenarios"][cen], "E"))
                    with g2:
                        mostrar_plotly(_graf8_3d(p["cenarios"][cen], "B"))
            except ImportError:
                st.caption("Instale plotly para ver os gráficos (pip install plotly).")
        st.divider()
        st.markdown("**Relatório (padrão BK) e impressão**")

        def _g8(caminho):
            import relatorio_m8
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m8.gerar(caminho, proj, e, r, dict(ss["dados"].get(N, {})), PT.resumo(ss["dados"], 8),
                               codigo=(G("proj", "numero") or "BK-LT-MC") + "-M8", rev=G("proj", "revisao") or "R0")
        if ERRO_RELATORIO:
            st.error(ERRO_RELATORIO)
        elif r["erros"]:
            st.info("Preencha os dados pendentes para liberar o relatório e a impressão.")
            r1, r2 = st.columns(2)
            r1.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m8_off", disabled=True)
            r2.button("🖨️ Gerar PDF para impressão", key="btn_pdf_m8_off", disabled=True)
        else:
            if st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m8"):
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    caminho = os.path.join(td, "relatorio.docx")
                    _g8(caminho)
                    with open(caminho, "rb") as fh:
                        ss["_rel_m8"] = fh.read()
            if ss.get("_rel_m8"):
                st.download_button("Baixar relatório do Módulo 8 (.docx)", ss["_rel_m8"], file_name="Relatorio_Modulo8_Campos_E_B.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m8")
            botao_imprimir("m8", "Relatorio_Modulo8_Campos_E_B.pdf", _g8)
        botoes(8, so_limpar=True)


# ----------------------------------------------------------------------------
# Módulo 9 — Interferência e Compatibilidade Eletromagnética
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _calc9_cache(chave_json):
    import json
    import calc_interferencia as cif
    return cif.calcular_estudo(json.loads(chave_json))


INST9 = ["Poliduto / gasoduto (5 kV)", "Cabo telefônico / controle (1,6 kV)", "Informar limite"]


def entrada_m9():
    """Entrada do motor calc_interferencia (geometria, alturas e correntes como nos Módulos 8). Retorna (entrada, avisos, erros)."""
    N = "9"
    e8, av, er = entrada_m8()
    gd = []
    cods = [G("cfg", "cg1")] + ([G("cfg", "cg2")] if G("cfg", "n_cg", 1) == 2 else [])
    for j, g in enumerate(e8["guardas"]):
        cab = db.obter_cabo(cods[j]) if j < len(cods) and cods[j] else {}
        r_m = (cab.get("diametro_mm") or 9.0) / 2000.0
        gd.append(dict(x=g["x"], y=g["y"], r_km=cab.get("r_cc_20") or 1.0, gmr=(cab.get("rmg_mm") or 0.7788 * r_m * 1000.0) / 1000.0))
    circs = {k: dict(i_normal=c["i_normal"], fp=c["fp"], status=c["status"]) for k, c in e8["circs"].items()}
    pts = []
    for p in PT.selecionados(ss["dados"], 9):
        base = dict(tipo=p["tipo"])
        itens = []
        if p["tipo"] == PT.T_PAR:
            for v in p["vizinhas"]:
                itens.append((f"{p['nome']} – {v['nome']}", float(v["dist_eixos"]), float(v["comp_par"]), float(v["ang_par"]), [v["nome"]]))
        else:
            itens.append((p["nome"], float(p["dist_h"] or 0.0), float(p["comp_par"] or 0.0), float(p["ang_par"] or 0.0), []))
        padrao = INST9[0] if p["tipo"] == PT.T_DUTO else INST9[1]
        inst = G(N, f"inst{p['i']}", padrao)
        if inst == INST9[0]:
            lim, nome, ti = 5.0, "Poliduto (5 kV)", "poliduto"
        elif inst == INST9[1]:
            lim, nome, ti = 1.6, "Cabo telefônico (1,6 kV)", "telecom"
        else:
            lim, nome, ti = G(N, f"lim{p['i']}", 1.6), "Limite informado", "outro"
        for nm, d, comp, ang, viz in itens:
            pts.append(dict(base, nome=nm, dist=d, comp_km=comp, ang_par=ang, dist_torre=d, lim_kv=lim, lim_nome=nome, tipo_inst=ti, vizinhas=viz))
    e = dict(fases=e8["fases"], guardas=gd, circs=circs, h_min=e8["h_min"], rho=G(N, "rho_solo", float(G("2", "rho", 1000.0))),
             freq=float(G("sis", "freq", 60)), i_falta=G(N, "i_falta", 5.0), cota=G(N, "cota", -1.5),
             kappa_modo=G(N, "kappa_modo", "Sem blindagem (conservador)"), f_torre=G(N, "f_torre", 1.0), r_pe=G(N, "r_pe", 20.0),
             f_aten=G(N, "f_aten", 0.5), lim_reg_v=G(N, "lim_reg", 15.0), pontos=pts)
    return e, av, list(er)


def mod9():
    import json
    N = "9"
    t1, t2, t3 = st.tabs(["Dados de entrada", "Pontos e vizinhas", "Resultados e relatório"])
    with t1:
        st.caption("Acoplamentos indutivo e resistivo de LT sobre poliduto, ferrovia/rodovia e telecomunicações. Impedâncias mútuas de Carson "
                   "(Villas, cap. 10; Livro 3), limites: poliduto 5 kV e cabo telefônico ≈ 1,6 kV (Villas 10.1.2 e 10.3). "
                   "Geometria, alturas e correntes seguem as premissas do Módulo 8. Acoplamento capacitivo e modelo distribuído do poliduto: NÃO calculados.")
        a, b, c_ = st.columns(3)
        num(N, "rho_solo", "Resistividade do solo (Ω·m)", float(G("2", "rho", 1000.0)), 1.0, 20000.0, 10.0, c=a)
        num(N, "i_falta", "Corrente de falta fase-terra (kA)", 5.0, 0.0, 100.0, 0.1, c=b, help="Maior curto monofásico na torre mais próxima (estudo de curto-circuito).")
        num(N, "cota", "Cota do duto/cabo (m; negativa = enterrado)", -1.5, -10.0, 30.0, 0.5, c=c_)
        sel(N, "kappa_modo", "Blindagem dos cabos guarda", ["Sem blindagem (conservador)", "Com cabos guarda"], c=a,
            help="κ = 1 − Zpg/Zgg (Carson). Vale para linhas longas com guardas aterrados nas duas pontas. PREMISSA.")
        num(N, "f_torre", "Fração da corrente de terra pela torre sob falta", 1.0, 0.0, 1.0, 0.05, c=b, help="PREMISSA conservadora: 100 %.")
        num(N, "r_pe", "Resistência de pé de torre (Ω)", 20.0, 0.5, 200.0, 0.5, c=c_, help="Limita o potencial resistivo (GPR). Ver Módulo 6.")
        num(N, "f_aten", "Fator de tensão à terra / FEM (poliduto)", 0.5, 0.05, 1.0, 0.05, c=a,
            help="0,5 = limite superior para extremos isolados. O perfil real exige o modelo de linha do poliduto (Villas 10.3).")
        num(N, "lim_reg", "Limite em regime normal (V)", 15.0, 1.0, 100.0, 1.0, c=b,
            help="PREMISSA (15 V, contato em dutos, NACE SP0177) – não consta no acervo: NECESSITA VALIDAÇÃO.")
    with t2:
        bloco_pontos(9)
        sp = PT.selecionados(ss["dados"], 9)
        if sp:
            st.markdown("**Instalação induzida e limite por ponto**")
            cols = st.columns(min(len(sp), 3))
            for j, p in enumerate(sp):
                with cols[j % len(cols)]:
                    sel(N, f"inst{p['i']}", p["nome"], INST9, default=INST9[0] if p["tipo"] == PT.T_DUTO else INST9[1])
                    if G(N, f"inst{p['i']}", INST9[1]) == INST9[2]:
                        num(N, f"lim{p['i']}", "Limite (kV)", 1.6, 0.1, 50.0, 0.1)
    e, av9, er9 = entrada_m9()
    if not er9 and not e["pontos"]:
        er9 = ["Selecione ao menos um ponto de duto/telecomunicações, rodovia/ferrovia ou paralelismo (aba 'Pontos e vizinhas')."]
    chave = json.dumps(e, sort_keys=True, default=str)
    r = _calc9_cache(chave) if not er9 else dict(erros=er9, avisos=[], pontos=[])
    with t3:
        if r["erros"]:
            for m in r["erros"]:
                st.warning(m)
        else:
            for m in av9 + r["avisos"]:
                st.info(m)
            st.dataframe(pd.DataFrame([{"Ponto": p["nome"], "d (m)": p["d"], "L ef. (km)": p["L_ef"], "FEM regime (V)": p["v_norm"],
                                        "FEM falta + resistivo (V)": p["pior"]["total"], "Limite": p["lim_nome"],
                                        "Regime": "ATENDE" if p["ok_norm"] else "NÃO ATENDE", "Falta": "ATENDE" if p["ok_falta"] else "NÃO ATENDE"}
                                       for p in r["pontos"]]).round(2), hide_index=True)
            st.caption(f"De = {r['de']:.0f} m · κ calculado do pior caso: " + ", ".join(f"{p['nome']}: {p['pior']['kappa']:.2f}" for p in r["pontos"]))
        st.divider()
        st.markdown("**Relatório (padrão BK) e impressão**")

        def _g9(caminho):
            import relatorio_m9
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m9.gerar(caminho, proj, e, r, dict(ss["dados"].get(N, {})), PT.resumo(ss["dados"], 9),
                               codigo=(G("proj", "numero") or "BK-LT-MC") + "-M9", rev=G("proj", "revisao") or "R0")
        if ERRO_RELATORIO:
            st.error(ERRO_RELATORIO)
        elif r["erros"]:
            st.info("Preencha os dados pendentes para liberar o relatório e a impressão.")
            r1, r2 = st.columns(2)
            r1.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m9_off", disabled=True)
            r2.button("🖨️ Gerar PDF para impressão", key="btn_pdf_m9_off", disabled=True)
        else:
            if st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m9"):
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    caminho = os.path.join(td, "relatorio.docx")
                    _g9(caminho)
                    with open(caminho, "rb") as fh:
                        ss["_rel_m9"] = fh.read()
            if ss.get("_rel_m9"):
                st.download_button("Baixar relatório do Módulo 9 (.docx)", ss["_rel_m9"], file_name="Relatorio_Modulo9_Interferencia.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m9")
            botao_imprimir("m9", "Relatorio_Modulo9_Interferencia.pdf", _g9)
        botoes(9, so_limpar=True)


# ----------------------------------------------------------------------------
# Módulo 10 — RI e RA
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _calc10_cache(chave_json):
    import json
    import calc_corona as crn
    return crn.calcular_estudo(json.loads(chave_json))


def entrada_m10():
    """Entrada do motor calc_corona (geometria e altura como no Módulo 8). Retorna (entrada, avisos, erros)."""
    N = "10"
    e8, av, er = entrada_m8()
    n = int(G("cfg", "n_circ", 1))
    circs = {}
    for i in range(1, n + 1):
        c = circuito(i)
        cab = db.obter_cabo(c["cond"]) if c.get("cond") else {}
        circs[str(i)] = dict(umax_kv=c["umax"], status=c["status"], n=int(c["cabos_fase"]), d_mm=cab.get("diametro_mm") or 0.0,
                             s_mm=float(c.get("esp_sub") or 0.0))
    if G(N, "lim_modo", "Limite fixo") == "Limite fixo":
        lim_ri = G(N, "lim_ri", 55.0)
    else:
        lim_ri = G(N, "sinal", 66.0) - G(N, "sn", 22.0)
    pts = PT.selecionados(ss["dados"], 10)
    if not pts:
        pts = [dict(nome="Limite da faixa (seção livre)", tipo=PT.T_LIVRE, dist_h=0.0, alt_ref=G(N, "h_obs", 1.5), vizinhas=[])]
    e = dict(fases=e8["fases"], guardas=e8["guardas"], incluir_guardas=bool(G(N, "guardas", True)), circs=circs, h_min=e8["h_min"],
             h_obs=G(N, "h_obs", 1.5), x_max=G(N, "x_max", 60.0), dx=1.0, semi_faixa=e8["semi_faixa"],
             alt=G(N, "alt", G("3", "alt", 800.0) or 800.0), temp=G(N, "temp", 25.0), m_rug=G(N, "m_rug", 0.85),
             chuva=G(N, "cond", "Tempo bom") == "Chuva", lim_ri=lim_ri, lim_ra=G(N, "lim_ra", 58.0), modo_lim_ri=G(N, "lim_modo", "Limite fixo"),
             pontos=[dict(nome=p["nome"], tipo=p["tipo"], dist_h=float(p["dist_h"] or 0.0), alt_ref=float(p["alt_ref"] or 0.0),
                          vizinhas=[dict(nome=v["nome"]) for v in p["vizinhas"]]) for p in pts])
    erros = list(er) + [f"Circuito {k}: selecione o condutor." for k, c in circs.items() if not c["d_mm"]]
    return e, av, erros


def mod10():
    import json
    N = "10"
    t1, t2, t3 = st.tabs(["Dados de entrada", "Pontos e vizinhas", "Resultados e relatório"])
    n = int(G("cfg", "n_circ", 1))
    with t1:
        st.caption("Gradiente: simulação de cargas + fator de feixe (Kiessling, 2.3.3). RI: Kiessling eq. 2.24–2.26 e método FG (Villas, 8.3.2.1). "
                   "RA: Kiessling eq. 2.27–2.29. Tensão máxima operativa; condutores na altura mínima (premissas do Módulo 8). "
                   "Diretrizes 6.10: RI/RA no limite da faixa.")
        st.markdown("**Circuitos (dados do Módulo 1)**")
        for i in range(1, n + 1):
            c = circuito(i)
            cab = db.obter_cabo(c["cond"]) if c.get("cond") else {}
            st.markdown(f"C{i}: **{c['cond'] or 'não selecionado'}** · d = {cab.get('diametro_mm') or '—'} mm · {c['cabos_fase']} subcondutor(es) · "
                        f"s = {c['esp_sub']:.0f} mm · Umáx = {c['umax']:g} kV")
        st.markdown("**Ponto de cálculo e meio**")
        a, b, c_, d = st.columns(4)
        num(N, "h_obs", "Altura do ponto de medição (m)", 1.5, 0.0, 10.0, 0.1, c=a, help="PREMISSA: 1,5 m (mesma do Módulo 8).")
        num(N, "x_max", "Perfil: ± x (m)", 60.0, 10.0, 300.0, 5.0, c=b)
        num(N, "alt", "Altitude (m)", float(G("3", "alt", 800.0) or 800.0), 0.0, 5000.0, 10.0, c=c_)
        num(N, "temp", "Temperatura ambiente (°C)", 25.0, -10.0, 50.0, 1.0, c=d)
        num(N, "m_rug", "Fator de superfície m (Peek)", 0.85, 0.5, 1.0, 0.01, c=a, help="NECESSITA VALIDAÇÃO com o Livro 3 (cap. 7).")
        chk(N, "guardas", "Incluir guardas aterrados no gradiente (conservador)", True, c=b)
        st.markdown("**Rádio-interferência (RI)**")
        a, b, c_, d = st.columns(4)
        sel(N, "cond", "Condição climática", ["Tempo bom", "Chuva"], c=a,
            help="Tempo bom: métodos Kiessling e FG. Chuva: método FG com +17 dB (E_FW).")
        sel(N, "lim_modo", "Critério de limite", ["Limite fixo", "Sinal a proteger − relação S/N"], c=b)
        if G(N, "lim_modo", "Limite fixo") == "Limite fixo":
            num(N, "lim_ri", "Limite de RI na faixa (dB µV/m)", 55.0, 30.0, 80.0, 0.5, c=c_,
                help="Níveis de 50 a 60 dB são usuais nos limites da faixa (Villas 8.3.2.2). PREMISSA: confirmar com o edital.")
        else:
            num(N, "sinal", "Sinal a proteger (dB µV/m)", 66.0, 40.0, 90.0, 1.0, c=c_, help="Kiessling: 65 a 75 dB nas regulamentações.")
            num(N, "sn", "Relação S/N exigida (dB)", 22.0, 6.0, 40.0, 1.0, c=d, help="Classe C = 22 dB (Kiessling Tabela 2.9). TAESA: 24 dB em 50 % do tempo.")
        st.caption("Frequência de referência 1 MHz (Kiessling); o método FG vale de 0,5 a 1,6 MHz.")
        st.markdown("**Ruído audível (RA)** – chuva/tempo úmido")
        num(N, "lim_ra", "Limite de RA na faixa (dB(A))", 58.0, 30.0, 80.0, 0.5,
            help="Edital TAESA: 58 dB(A) no limite da faixa. Referências: 50 dB(A) sem reclamações; 55 dB(A) com reclamações prováveis (Kiessling).")
    with t2:
        bloco_pontos(10)
    e, av10, er10 = entrada_m10()
    chave = json.dumps(e, sort_keys=True, default=str)
    r = _calc10_cache(chave) if not er10 else dict(erros=er10, avisos=[], pontos=[])
    with t3:
        if r["erros"]:
            for m in r["erros"]:
                st.warning(m)
        else:
            for m in av10 + r["avisos"]:
                st.info(m)
            gr = r["gradientes"]
            m1, m2, m3_, m4_ = st.columns(4)
            m1.metric("Gradiente máx. (kV/cm)", f"{max(g['E'] for g in gr):.2f}")
            m2.metric("Gradiente crítico visual (kV/cm)", f"{min(g['E_visual'] for g in gr):.1f}")
            m3_.metric("δ do ar", f"{r['delta']:.3f}")
            m4_.metric("Limites RI / RA", f"{r['lim_ri']:.0f} dBµV/m · {r['lim_ra']:.0f} dB(A)")
            st.dataframe(pd.DataFrame([{"Fase": g["nome"], "E máx. (kV/cm)": g["E"], "E/E visual": g["E_rel"], "n × d (mm)": f"{g['n']} × {g['d_mm']:.1f}"}
                                       for g in gr]).round(3), hide_index=True)
            linhas = [{"Ponto": p["nome"], "Posição (m)": ", ".join(f"{x:g}" for x in p["x_aval"]) or "—",
                       "RI Kiessling (dBµV/m)": p.get("RI_K"), "RI FG (dBµV/m)": p.get("RI_FG"), "RA (dB(A))": p.get("RA"),
                       "Situação": ("ATENDE" if p.get("ok_RI") and p.get("ok_RA") else "NÃO ATENDE") if "RA" in p else "—"} for p in r["pontos"]]
            st.dataframe(pd.DataFrame(linhas).round(1), hide_index=True)
            try:
                import plotly.graph_objects as go
                pf = r["perfil"]
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=pf["x"], y=pf["RI_K"], name="RI Kiessling (tempo bom)", line=dict(color=AZUL, width=3)))
                fig.add_trace(go.Scatter(x=pf["x"], y=pf["RI_FG"], name="RI método FG", line=dict(color=AZUL_CLARO, dash="dash")))
                fig.add_trace(go.Scatter(x=pf["x"], y=pf["RA"], name="RA (dB(A))", line=dict(color="#C55A11", width=3)))
                fig.add_hline(y=r["lim_ri"], line_dash="dot", line_color=AZUL, annotation_text=f"Limite RI {r['lim_ri']:.0f}")
                fig.add_hline(y=r["lim_ra"], line_dash="dot", line_color="#C55A11", annotation_text=f"Limite RA {r['lim_ra']:.0f}")
                if r.get("semi_faixa"):
                    for s_ in (-r["semi_faixa"], r["semi_faixa"]):
                        fig.add_vline(x=s_, line_dash="dot", line_color="#7F7F7F")
                fig.update_layout(height=420, xaxis_title="Distância ao eixo da LT (m)", yaxis_title="dB µV/m  ·  dB(A)",
                                  margin=dict(l=10, r=10, t=20, b=10), legend=dict(orientation="h", y=-0.25))
                mostrar_plotly(fig)
            except ImportError:
                st.caption("Instale plotly para ver o gráfico.")
        st.divider()
        st.markdown("**Relatório (padrão BK) e impressão**")

        def _g10(caminho):
            import relatorio_m10
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m10.gerar(caminho, proj, e, r, dict(ss["dados"].get(N, {})), PT.resumo(ss["dados"], 10),
                                codigo=(G("proj", "numero") or "BK-LT-MC") + "-M10", rev=G("proj", "revisao") or "R0")
        if ERRO_RELATORIO:
            st.error(ERRO_RELATORIO)
        elif r["erros"]:
            st.info("Preencha os dados pendentes para liberar o relatório e a impressão.")
            r1, r2 = st.columns(2)
            r1.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m10_off", disabled=True)
            r2.button("🖨️ Gerar PDF para impressão", key="btn_pdf_m10_off", disabled=True)
        else:
            if st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m10"):
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    caminho = os.path.join(td, "relatorio.docx")
                    _g10(caminho)
                    with open(caminho, "rb") as fh:
                        ss["_rel_m10"] = fh.read()
            if ss.get("_rel_m10"):
                st.download_button("Baixar relatório do Módulo 10 (.docx)", ss["_rel_m10"], file_name="Relatorio_Modulo10_RI_RA.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m10")
            botao_imprimir("m10", "Relatorio_Modulo10_RI_RA.pdf", _g10)
        botoes(10, so_limpar=True)


# ----------------------------------------------------------------------------
# Módulo 11 — Efeito Corona
# ----------------------------------------------------------------------------
def _calc11_cache(chave_json):
    import json
    import calc_efeito_corona as cec
    return cec.calcular_estudo(json.loads(chave_json))


def entrada_m11():
    """Entrada do motor calc_efeito_corona (geometria e altura próprias do Módulo 11). Retorna (entrada, avisos, erros)."""
    N = "11"
    ss["dados"].setdefault(N, {}).setdefault("faixa_modo", "Informar")      # não depende da faixa do M4
    e8, av, er = entrada_m8(N)
    n = int(G("cfg", "n_circ", 1))
    circs = {}
    for i in range(1, n + 1):
        c = circuito(i)
        cab = db.obter_cabo(c["cond"]) if c.get("cond") else {}
        circs[str(i)] = dict(un_kv=c["un"], umax_kv=c["umax"], status=c["status"], n=int(c["cabos_fase"]), d_mm=cab.get("diametro_mm") or 0.0,
                             s_mm=float(c.get("esp_sub") or 0.0))
    m = G(N, "m_rug", 0.85)
    e = dict(fases=e8["fases"], guardas=e8["guardas"], incluir_guardas=bool(G(N, "guardas", True)), circs=circs, h_min=e8["h_min"],
             alt=G(N, "alt", G("3", "alt", 800.0) or 800.0), temp=G(N, "temp", 25.0), freq=float(G("sis", "freq", 60)),
             mc=m, m_sup=m, g0=21.6 if str(G(N, "g0", "21,1 kV/cm (usual)")).startswith("21,6") else 21.1,
             mt_chuva=G(N, "mt", 0.8), lim_perda=G(N, "lim_p", 1.2))
    erros = [x for x in er if "faixa" not in x.lower()]
    return e, [a for a in av if "Faixa" not in a], erros


def _graf11(r):
    import plotly.graph_objects as go
    fig = go.Figure()
    for k, c in r["circuitos"].items():
        cv = c["curva"]
        fig.add_trace(go.Scatter(x=[p["U"] for p in cv], y=[p["Tempo bom"] for p in cv], name=f"C{k} tempo bom", line=dict(color=AZUL, width=3)))
        fig.add_trace(go.Scatter(x=[p["U"] for p in cv], y=[p["Chuva"] for p in cv], name=f"C{k} chuva", line=dict(color="#C55A11", width=3)))
        fig.add_vline(x=c["umax"], line_dash="dot", line_color="#7F7F7F", annotation_text=f"Umáx C{k}")
    fig.add_hline(y=r["lim_perda"], line_dash="dot", line_color="#C00000", annotation_text=f"Limite {r['lim_perda']:g} kW/km")
    fig.update_layout(height=400, xaxis_title="Tensão entre fases (kV)", yaxis_title="Perda corona trifásica (kW/km)",
                      margin=dict(l=10, r=10, t=20, b=10), legend=dict(orientation="h", y=-0.25))
    return fig


def mod11():
    import json
    N = "11"
    t1, t3 = st.tabs(["Dados de entrada", "Resultados e relatório"])
    n = int(G("cfg", "n_circ", 1))
    with t1:
        st.caption("Estudo independente de efeito corona: gradiente superficial (Kiessling 2.3.3), gradiente crítico e tensão crítica de Peek e perdas "
                   "(Livro 2, 3.2.5–3.2.6; Livro 3, cap. 7). Pode ser emitido isoladamente para clientes que pedem apenas o corona.")
        st.markdown("**Circuitos (dados do Módulo 1)**")
        for i in range(1, n + 1):
            c = circuito(i)
            cab = db.obter_cabo(c["cond"]) if c.get("cond") else {}
            st.markdown(f"C{i}: **{c['cond'] or 'não selecionado'}** · d = {cab.get('diametro_mm') or '—'} mm · {c['cabos_fase']} subcondutor(es) · "
                        f"s = {c['esp_sub']:.0f} mm · Un = {c['un']:g} kV · Umáx = {c['umax']:g} kV")
        st.markdown("**Geometria e meio**")
        a, b, c_, d = st.columns(4)
        sel(N, "h_modo", "Altura dos condutores", ["Automático (altura na estrutura − flecha)", "Informar altura mínima"], c=a,
            help="Condutor na altura mínima (conservador para o gradiente).")
        if not G(N, "h_modo", "Automático (altura na estrutura − flecha)").startswith("Autom"):
            num(N, "h_min_man", "Altura mínima do condutor mais baixo (m)", 8.0, 3.0, 100.0, 0.1, c=b)
        num(N, "alt", "Altitude (m)", float(G("3", "alt", 800.0) or 800.0), 0.0, 5000.0, 10.0, c=c_)
        num(N, "temp", "Temperatura ambiente (°C)", 25.0, -10.0, 50.0, 1.0, c=d)
        a, b, c_, d = st.columns(4)
        num(N, "m_rug", "Fator de superfície m", 0.85, 0.5, 1.0, 0.01, c=a,
            help="Livro 2: 1,0 liso; 0,9–0,93 oxidado; 0,83–0,87 cabo encordoado. Livro 3 (Tabela 7.2): 0,92 cabos novos secos. NECESSITA VALIDAÇÃO.")
        num(N, "mt", "Fator de tempo mt (chuva)", 0.8, 0.5, 1.0, 0.05, c=b, help="Livro 2: 1,0 tempo seco; 0,8 chuva.")
        sel(N, "g0", "Gradiente de referência g0 (Peek)", ["21,1 kV/cm (usual)", "21,6 kV/cm (Livro 3)"], c=c_,
            help="Eq. (1) do Livro 3 ilegível no OCR: NECESSITA VALIDAÇÃO. 21,1 é o valor usual (mais conservador).")
        num(N, "lim_p", "Limite de perda corona (kW/km, trifásica)", 1.2, 0.1, 10.0, 0.1, c=d,
            help="Livro 3/Villas: 1,2 kW/km; Livro 2: 1,24 kW/km. PREMISSA: confirmar com o edital/cliente.")
        chk(N, "guardas", "Incluir guardas aterrados no gradiente (conservador)", True)
    e, av11, er11 = entrada_m11()
    chave = json.dumps(e, sort_keys=True, default=str)
    r = _calc11_cache(chave) if not er11 else dict(erros=er11, avisos=[])
    with t3:
        if r["erros"]:
            for m in r["erros"]:
                st.warning(m)
        else:
            for m in av11 + r["avisos"]:
                st.info(m)
            m1, m2, m3_, m4_ = st.columns(4)
            m1.metric("δ do ar", f"{r['delta']:.3f}")
            gmax = max(g["E"] for g in r["gradientes"])
            m2.metric("Gradiente máx. (kV/cm)", f"{gmax:.2f}")
            pmax = max(c["cond"][cn]["tens"]["Umáx"]["P_trif"] for c in r["circuitos"].values() for cn in c["cond"])
            m3_.metric("Perda máx. (kW/km)", f"{pmax:.3f}")
            m4_.metric("Limite (kW/km)", f"{r['lim_perda']:g}")
            linhas = []
            for k, c in r["circuitos"].items():
                for cn, cd in c["cond"].items():
                    for rot, t in cd["tens"].items():
                        linhas.append({"Circ.": f"C{k}", "Condição": cn, "Tensão": f"{rot} = {t['U']:g} kV", "E máx. (kV/cm)": t["E_max"],
                                       "E0 Peek (kV/cm)": cd["E0"], "E/E0": t["E_rel"], "Vc (kV)": cd["Vc"], "V/Vc": t["V_rel"],
                                       "Perda (kW/km)": t["P_trif"], "Situação": "ATENDE" if t["ok_P"] else "NÃO ATENDE"})
            st.dataframe(pd.DataFrame(linhas).round(3), hide_index=True)
            try:
                mostrar_plotly(_graf11(r))
            except ImportError:
                st.caption("Instale plotly para ver o gráfico.")
        st.divider()
        st.markdown("**Relatório (padrão BK) e impressão**")

        def _g11(caminho):
            import relatorio_m11
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m11.gerar(caminho, proj, e, r, dict(ss["dados"].get(N, {})),
                                codigo=(G("proj", "numero") or "BK-LT-MC") + "-M11", rev=G("proj", "revisao") or "R0")
        if ERRO_RELATORIO:
            st.error(ERRO_RELATORIO)
        elif r["erros"]:
            st.info("Preencha os dados pendentes para liberar o relatório e a impressão.")
            r1, r2 = st.columns(2)
            r1.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m11_off", disabled=True)
            r2.button("🖨️ Gerar PDF para impressão", key="btn_pdf_m11_off", disabled=True)
        else:
            if st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m11"):
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    caminho = os.path.join(td, "relatorio.docx")
                    _g11(caminho)
                    with open(caminho, "rb") as fh:
                        ss["_rel_m11"] = fh.read()
            if ss.get("_rel_m11"):
                st.download_button("Baixar relatório do Módulo 11 (.docx)", ss["_rel_m11"], file_name="Relatorio_Modulo11_Efeito_Corona.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m11")
            botao_imprimir("m11", "Relatorio_Modulo11_Efeito_Corona.pdf", _g11)
        botoes(11, so_limpar=True)


# ----------------------------------------------------------------------------
# Módulo 12 — Isolamento e Tensão Máxima Operativa
# ----------------------------------------------------------------------------
def entrada_m12():
    """Entrada do Módulo 12 e, por reaproveitamento, do motor do Módulo 5. Retorna (e12, e5)."""
    N = "12"
    c1 = circuito(1)
    e5 = entrada_m5()
    e = dict(um_kv=float(c1.get("umax") or 0.0), un_kv=float(c1.get("un") or 0.0), k_tov=G(N, "fator_sob", 1.4), k_man=G(N, "fator_man", 2.2),
             d_ft_adot=G(N, "dist_ar", 1.1), d_ff_adot=G(N, "dist_ff", 1.5), margem_pct=G(N, "margem", 15.0))
    return e, e5


def mod12():
    import json
    import calc_tensao_operativa as cto
    N = "12"
    t1, t3 = st.tabs(["Dados de entrada", "Resultados e relatório"])
    c1 = circuito(1)
    with t1:
        st.caption("Verificação do isolamento ADOTADO contra a tensão máxima operativa. As distâncias requeridas e a cadeia de isoladores vêm do Módulo 5 "
                   "(NBR 5422:2024, seção 9); ajuste lá os critérios (Fsfl, kg, Kcs, poluição, isoladores).")
        st.markdown(f"Un = **{c1['un']:g} kV** · Um (tensão máxima operativa) = **{c1['umax']:g} kV** · Um/Un = {c1['umax'] / c1['un']:.3f} (Módulo 1 → Circuitos)")
        a, b, c_ = st.columns(3)
        num(N, "fator_sob", "Sobretensão temporária (p.u. de Um/√3)", 1.4, 1.0, 3.0, 0.05, c=a, help="PREMISSA: 1,4 p.u. usual em rejeição de carga; confirmar com o Módulo 14/ATP.")
        num(N, "fator_man", "Sobretensão de manobra (p.u. de √2·Um/√3)", 2.2, 1.0, 4.0, 0.05, c=b, help="PREMISSA; confirmar com estudo de transitórios.")
        num(N, "margem", "Margem mínima exigida (%)", 15.0, 0.0, 50.0, 1.0, c=c_, help="PREMISSA – margem de d adotada sobre d requerida.")
        a, b = st.columns(2)
        num(N, "dist_ar", "Distância no ar fase-terra adotada (m)", 1.1, 0.0, 10.0, 0.01, c=a, help="Menor distância cadeia/condutor–estrutura na condição de projeto (balanço no Módulo 5).")
        num(N, "dist_ff", "Distância no ar fase-fase adotada (m)", 1.5, 0.0, 15.0, 0.01, c=b)
    e, e5 = entrada_m12()
    chave = json.dumps(e5, sort_keys=True, default=str)
    r5 = _calc5_cache(chave) if e["um_kv"] > 0 else dict(erros=["Informe a tensão máxima do sistema (Módulo 1)."], avisos=[], pendencias=[])
    r = cto.verificar(e, e5, r5) if not r5.get("erros") else dict(erros=list(r5["erros"]), avisos=[])
    with t3:
        if r["erros"]:
            for m in r["erros"]:
                st.warning(m)
        else:
            for m in r["avisos"]:
                st.info(m)
            s = r["sobre"]
            m1, m2, m3_, m4_ = st.columns(4)
            m1.metric("Um/Un", f"{r['razao']:.3f}")
            m2.metric("TOV (kV ef. f-t)", f"{s['tov_kv']:.1f}")
            m3_.metric("Manobra (kV crista f-t)", f"{s['man_kv']:.0f}")
            m4_.metric("Um máx. p/ d adotada (kV)", "—" if r["um_adm"] is None else f"{r['um_adm']:.0f}")
            st.dataframe(pd.DataFrame([{"Verificação": l["nome"], "d requerida (m)": l["req"], "d adotada (m)": l["adot"], "Margem (%)": l["margem"],
                                        "Situação": "ATENDE" if l["ok"] else "NÃO ATENDE"} for l in r["linhas"]]).round(2), hide_index=True)
            i = r["iso"]
            st.dataframe(pd.DataFrame([["Cadeia (Módulo 5)", i["n"], f"{i['fuga_tot']:.0f}", f"{i['fuga_nec']:.0f}", "ATENDE" if r["ok_fuga"] else "NÃO ATENDE",
                                        "ATENDE" if r["ok_arco"] else "NÃO ATENDE"]],
                                      columns=["Item", "Nº isol.", "Fuga adotada (mm)", "Fuga requerida (mm)", "Fuga", "Comprimento de arco"]), hide_index=True)
            (st.success if r["ok"] else st.error)("Isolamento adotado " + ("ATENDE" if r["ok"] else "NÃO ATENDE") + " à tensão máxima operativa.")
        st.divider()
        st.markdown("**Relatório (padrão BK) e impressão**")

        def _g12(caminho):
            import relatorio_m12
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m12.gerar(caminho, proj, e, e5, r, codigo=(G("proj", "numero") or "BK-LT-MC") + "-M12", rev=G("proj", "revisao") or "R0")
        if ERRO_RELATORIO:
            st.error(ERRO_RELATORIO)
        elif r["erros"]:
            st.info("Preencha os dados pendentes para liberar o relatório e a impressão.")
            r1, r2 = st.columns(2)
            r1.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m12_off", disabled=True)
            r2.button("🖨️ Gerar PDF para impressão", key="btn_pdf_m12_off", disabled=True)
        else:
            if st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m12"):
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    caminho = os.path.join(td, "relatorio.docx")
                    _g12(caminho)
                    with open(caminho, "rb") as fh:
                        ss["_rel_m12"] = fh.read()
            if ss.get("_rel_m12"):
                st.download_button("Baixar relatório do Módulo 12 (.docx)", ss["_rel_m12"], file_name="Relatorio_Modulo12_Isolamento_Tensao_Maxima.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m12")
            botao_imprimir("m12", "Relatorio_Modulo12_Isolamento_Tensao_Maxima.pdf", _g12)
        botoes(12, so_limpar=True)


# ----------------------------------------------------------------------------
# Módulo 13 — Ampacidade e Flecha Máxima
# ----------------------------------------------------------------------------
def _calc13_cache(chave_json):
    import json
    import calc_ampacidade_flecha as caf
    d = json.loads(chave_json)
    return caf.calcular(d["e"], d["cabo"])


def entrada_m13():
    """Entrada do motor calc_ampacidade_flecha. Retorna (e, cabo, avisos, erros)."""
    N = "13"
    n = int(G("cfg", "n_circ", 1))
    ic = int(G(N, "circ", 1)) if n > 1 else 1
    c = circuito(ic)
    cabo = db.obter_cabo(c["cond"]) if c.get("cond") else {}
    erros = [] if cabo else [f"Selecione o condutor do circuito {ic} (Módulo 1 → Circuitos)."]
    g = geometria_atual()
    h_def = min([k["y"] for k in g["condutores"] if k["tipo"] == "fase" and k["circuito"] == ic] or [15.0])
    e = dict(a=G(N, "vao_f", 400.0), eds_pct=G(N, "eds", 20.0), th_eds=G(N, "th_eds", 20.0), t_min=G("3", "t_min", 5.0),
             t_amb=G(N, "t_amb_f", 30.0), t_max=G(N, "t_cond", G("3", "t_cc_max", 75.0) or 75.0),
             t_emerg=G(N, "t_emerg", G("3", "t_cc_emerg", 90.0) or 90.0), ta=G(N, "t_amb", 35.0), vento=G(N, "v_vento", 1.0),
             rad=G(N, "rad", 1000.0), emis=G(N, "emis", 0.5), absor=G(N, "absor", 0.5), alt_m=float(G("3", "alt", 0.0) or 0.0),
             h_fix=G(N, "h_fix", round(float(h_def), 2)), d_min=G(N, "d_min", 8.0), corrente=G(N, "i_op", corrente_nominal(ic)),
             n_sub=int(c["cabos_fase"]), lim_tmin_pct=G(N, "lim_tmin", 33.0))
    return e, cabo, [], erros


def mod13():
    import json
    N = "13"
    t1, t3 = st.tabs(["Dados de entrada", "Resultados e relatório"])
    n = int(G("cfg", "n_circ", 1))
    with t1:
        st.caption("Ampacidade (IEEE Std 738-2006, regime permanente), flecha por mudança de estado (equação da parábola, como na planilha BK) e catenária. "
                   "Dados do cabo vêm do catálogo (massa, RTC, módulo, dilatação).")
        if n > 1:
            sel(N, "circ", "Circuito em estudo", list(range(1, n + 1)), 1)
        ic = int(G(N, "circ", 1)) if n > 1 else 1
        c = circuito(ic)
        st.markdown(f"C{ic}: **{c['cond'] or 'não selecionado'}** · {c['cabos_fase']} subcondutor(es)/fase · In = {corrente_nominal(ic):.0f} A")
        st.markdown("**Estado inicial (EDS) e vão**")
        a, b, c_, d = st.columns(4)
        num(N, "vao_f", "Vão regulador (m)", 400.0, 50.0, 1500.0, 10.0, c=a)
        num(N, "eds", "EDS (% da RTC)", 20.0, 5.0, 40.0, 0.5, c=b, help="Planilha BK usa 10 % no exemplo GROSBEAK; 20 % é usual (PREMISSA).")
        num(N, "th_eds", "Temperatura EDS (°C)", 20.0, -10.0, 40.0, 1.0, c=c_)
        num(N, "t_amb_f", "Temp. ambiente máx. p/ flecha (°C)", 30.0, 0.0, 60.0, 1.0, c=d)
        st.markdown("**Condutor e distância ao solo**")
        a, b, c_, d = st.columns(4)
        num(N, "t_cond", "Temp. máx. do condutor – normal (°C)", float(G("3", "t_cc_max", 75.0) or 75.0), 40.0, 250.0, 1.0, c=a)
        num(N, "t_emerg", "Temp. do condutor – emergência (°C)", float(G("3", "t_cc_emerg", 90.0) or 90.0), 40.0, 250.0, 1.0, c=b)
        g = geometria_atual()
        h_def = min([k["y"] for k in g["condutores"] if k["tipo"] == "fase" and k["circuito"] == ic] or [15.0])
        num(N, "h_fix", "Altura de fixação do condutor mais baixo (m)", round(float(h_def), 2), 3.0, 120.0, 0.1, c=c_, help="Vem da geometria (Módulo 2).")
        num(N, "d_min", "Distância mínima ao solo (m)", 8.0, 3.0, 30.0, 0.1, c=d,
            help="NBR 5422 não consta no acervo: informe o valor do projeto. NECESSITA VALIDAÇÃO.")
        st.markdown("**Meio (IEEE 738)**")
        a, b, c_, d = st.columns(4)
        num(N, "t_amb", "Temperatura ambiente (°C)", 35.0, 0.0, 55.0, 1.0, c=a)
        num(N, "v_vento", "Vento (m/s)", 1.0, 0.0, 10.0, 0.1, c=b, help="IEEE 738: 0,61 m/s; ONS: 1,0 m/s.")
        num(N, "rad", "Radiação solar (W/m²)", 1000.0, 0.0, 1400.0, 10.0, c=c_)
        num(N, "i_op", "Corrente de operação (A, total da fase)", float(round(corrente_nominal(ic), 1)), 0.0, 10000.0, 10.0, c=d)
        a, b, c_ = st.columns(3)
        num(N, "emis", "Emissividade", 0.5, 0.1, 1.0, 0.05, c=a)
        num(N, "absor", "Absortividade solar", 0.5, 0.1, 1.0, 0.05, c=b)
        num(N, "lim_tmin", "Limite de tração a Tmín (% RTC)", 33.0, 10.0, 60.0, 1.0, c=c_, help="PREMISSA – confirmar com a verificação mecânica (Módulo 3/5).")
    e, cabo, av13, er13 = entrada_m13()
    chave = json.dumps(dict(e=e, cabo=cabo), sort_keys=True, default=str)
    r = _calc13_cache(chave) if not er13 else dict(erros=er13, avisos=[])
    with t3:
        if r["erros"]:
            for m in r["erros"]:
                st.warning(m)
        else:
            for m in av13 + r["avisos"]:
                st.info(m)
            m1, m2, m3_, m4_ = st.columns(4)
            m1.metric(f"Ampacidade a {e['t_max']:g} °C (A)", f"{r['i_term']:.0f}")
            m2.metric("Flecha a Tmáx (m)", f"{r['pmax']['f_cat']:.2f}")
            m3_.metric("Temp. do condutor em In (°C)", "—" if r["t_nom"] is None else f"{r['t_nom']:.1f}")
            m4_.metric("Corrente limite por flecha (A)", "—" if not r["i_flecha"] else f"{r['i_flecha']:.0f}")
            st.dataframe(pd.DataFrame([{"θ condutor (°C)": l["th"], "Tração (% RTC)": l["T_rtc"], "Flecha parábola (m)": l["f_par"], "Flecha catenária (m)": l["f_cat"],
                                        "Dist. ao solo (m)": l["clear"], "Corrente IEEE 738 (A)": l["I"],
                                        "Situação": "ATENDE" if l["ok_clear"] else "NÃO ATENDE"} for l in r["linhas"]]).round(2), hide_index=True)
            try:
                import plotly.graph_objects as go
                cv = r["curva"]
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=[p["th"] for p in cv], y=[p["clear"] for p in cv], name="Distância ao solo (m)", line=dict(color=AZUL, width=3)))
                fig.add_hline(y=e["d_min"], line_dash="dot", line_color="#C00000", annotation_text=f"Mínima {e['d_min']:g} m")
                fig.update_layout(height=380, xaxis_title="Temperatura do condutor (°C)", yaxis_title="Distância ao solo no meio do vão (m)",
                                  margin=dict(l=10, r=10, t=20, b=10))
                mostrar_plotly(fig)
            except ImportError:
                st.caption("Instale plotly para ver o gráfico.")
        st.divider()
        st.markdown("**Relatório (padrão BK) e impressão**")

        def _g13(caminho):
            import relatorio_m13
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m13.gerar(caminho, proj, e, cabo, r, codigo=(G("proj", "numero") or "BK-LT-MC") + "-M13", rev=G("proj", "revisao") or "R0")
        if ERRO_RELATORIO:
            st.error(ERRO_RELATORIO)
        elif r["erros"]:
            st.info("Preencha os dados pendentes para liberar o relatório e a impressão.")
            r1, r2 = st.columns(2)
            r1.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m13_off", disabled=True)
            r2.button("🖨️ Gerar PDF para impressão", key="btn_pdf_m13_off", disabled=True)
        else:
            if st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m13"):
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    caminho = os.path.join(td, "relatorio.docx")
                    _g13(caminho)
                    with open(caminho, "rb") as fh:
                        ss["_rel_m13"] = fh.read()
            if ss.get("_rel_m13"):
                st.download_button("Baixar relatório do Módulo 13 (.docx)", ss["_rel_m13"], file_name="Relatorio_Modulo13_Ampacidade_Flecha.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m13")
            botao_imprimir("m13", "Relatorio_Modulo13_Ampacidade_Flecha.pdf", _g13)
        botoes(13, so_limpar=True)


# ----------------------------------------------------------------------------
# Módulo 14 — Rejeição de Carga
# ----------------------------------------------------------------------------
def _calc14_cache(chave_json):
    import json
    import calc_rejeicao as crj
    return crj.calcular(json.loads(chave_json))


def entrada_m14():
    """Entrada do motor calc_rejeicao (Z1/C1 do Módulo 2). Retorna (e, avisos, erros)."""
    N = "14"
    n = int(G("cfg", "n_circ", 1))
    ic = int(G(N, "circ", 1)) if n > 1 else 1
    c = circuito(ic)
    out, _geo, erros = calcular_m2()
    z1 = c1 = None
    if out is not None:
        v = out[0]["circuitos"].get(ic)
        if v and v.get("seq"):
            z1 = [float(v["seq"]["Z1"].real), float(v["seq"]["Z1"].imag)]
            c1 = float(v["seq"]["C1"])
        else:
            erros = list(erros) + [f"Circuito {ic}: parâmetros de sequência não calculados (Módulo 2)."]
    e = dict(z1=z1, c1=c1, comp_km=float(G("sis", "km", 80.0) or 0.0), un_kv=c["un"], umax_kv=c["umax"], f=float(G("sis", "freq", 60)),
             scc_mva=G(N, "scc_origem", 3000.0), xr=G(N, "xr", 10.0), s_mva=G(N, "carga_rej", float(c["mva"])), fp=G(N, "fp", float(c["fp"])),
             q_shunt=G(N, "comp_reat", 0.0), vr0_pu=G(N, "vr0", 1.0), lim_pu=G(N, "lim_sob", 1.1), nome_circ=f"C{ic}")
    return e, [], list(erros)


def mod14():
    import json
    N = "14"
    t1, t3 = st.tabs(["Dados de entrada", "Resultados e relatório"])
    n = int(G("cfg", "n_circ", 1))
    with t1:
        st.warning("TRIAGEM ANALÍTICA (60 Hz, regime permanente). As Diretrizes de Projeto Básico (3.2.5, 3.2.6, 8.4) exigem estudo de transitórios "
                   "eletromagnéticos (ATP, ≥ 200 manobras, ONS submódulo 23.3): este módulo não o substitui.")
        if n > 1:
            sel(N, "circ", "Circuito em estudo", list(range(1, n + 1)), 1)
        ic = int(G(N, "circ", 1)) if n > 1 else 1
        c = circuito(ic)
        st.caption(f"C{ic}: Z1 e C1 vêm do Módulo 2 · comprimento {G('sis', 'km', 80.0):g} km (Módulo 1) · Un = {c['un']:g} kV.")
        a, b, c_, d = st.columns(4)
        num(N, "scc_origem", "Potência de curto na origem (MVA)", 3000.0, 10.0, 100000.0, 50.0, c=a, help="Fonte de Thévenin atrás da barra de origem.")
        num(N, "xr", "Relação X/R da fonte", 10.0, 1.0, 50.0, 0.5, c=b)
        num(N, "carga_rej", "Carga rejeitada (MVA)", float(c["mva"]), 0.0, 5000.0, 1.0, c=c_)
        num(N, "fp", "Fator de potência da carga", float(c["fp"]), 0.5, 1.0, 0.01, c=d)
        a, b, c_ = st.columns(3)
        num(N, "comp_reat", "Reator shunt no fim da linha (Mvar)", 0.0, 0.0, 1000.0, 1.0, c=a, help="Permanece ligado após a rejeição.")
        num(N, "vr0", "Tensão na carga antes da rejeição (p.u. de Un)", 1.0, 0.8, 1.2, 0.01, c=b)
        num(N, "lim_sob", "Limite de sobretensão (p.u. de Un)", 1.1, 1.0, 2.0, 0.01, c=c_, help="PREMISSA – confirmar com o ONS/edital e a suportabilidade (Módulo 12).")
    e, av14, er14 = entrada_m14()
    chave = json.dumps(e, sort_keys=True, default=str)
    r = _calc14_cache(chave) if not er14 else dict(erros=er14, avisos=[])
    with t3:
        if r["erros"]:
            for m in r["erros"]:
                st.warning(m)
        else:
            for m in r["avisos"]:
                st.info(m)
            b = r["base"]
            m1, m2, m3_, m4_ = st.columns(4)
            m1.metric("Tensão após rejeição (kV)", f"{b['vr_kv']:.1f}", delta=f"{r['pu']:.3f} p.u.", delta_color="off")
            m2.metric("Sem reator (p.u.)", f"{r['pu_sem_reator']:.3f}")
            m3_.metric("Ferranti 1/cosh(γℓ)", f"{b['ferranti']:.4f}")
            m4_.metric("Reator mínimo (Mvar)", "—" if r["q_min"] is None else ("inviável" if r["q_min"] == float("inf") else f"{r['q_min']:.1f}"))
            (st.success if r["ok"] else st.error)(f"{'ATENDE' if r['ok'] else 'NÃO ATENDE'}: {r['pu']:.3f} p.u. × limite {e['lim_pu']:.2f} p.u. ({r['lim_kv']:.1f} kV)")
            try:
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=[p["x"] for p in r["c_carga"]], y=[p["pu"] for p in r["c_carga"]], name="× carga rejeitada (MVA)", line=dict(color=AZUL, width=3)))
                fig.add_hline(y=e["lim_pu"], line_dash="dot", line_color="#C00000", annotation_text="Limite")
                fig.update_layout(height=360, xaxis_title="Carga rejeitada (MVA)", yaxis_title="Sobretensão (p.u. de Un)", margin=dict(l=10, r=10, t=20, b=10))
                mostrar_plotly(fig)
            except ImportError:
                st.caption("Instale plotly para ver o gráfico.")
        st.divider()
        st.markdown("**Relatório (padrão BK) e impressão**")

        def _g14(caminho):
            import relatorio_m14
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m14.gerar(caminho, proj, e, r, codigo=(G("proj", "numero") or "BK-LT-MC") + "-M14", rev=G("proj", "revisao") or "R0")
        if ERRO_RELATORIO:
            st.error(ERRO_RELATORIO)
        elif r["erros"]:
            st.info("Preencha os dados pendentes para liberar o relatório e a impressão.")
            r1, r2 = st.columns(2)
            r1.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m14_off", disabled=True)
            r2.button("🖨️ Gerar PDF para impressão", key="btn_pdf_m14_off", disabled=True)
        else:
            if st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m14"):
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    caminho = os.path.join(td, "relatorio.docx")
                    _g14(caminho)
                    with open(caminho, "rb") as fh:
                        ss["_rel_m14"] = fh.read()
            if ss.get("_rel_m14"):
                st.download_button("Baixar relatório do Módulo 14 (.docx)", ss["_rel_m14"], file_name="Relatorio_Modulo14_Rejeicao_de_Carga.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m14")
            botao_imprimir("m14", "Relatorio_Modulo14_Rejeicao_de_Carga.pdf", _g14)
        botoes(14, so_limpar=True)


# ----------------------------------------------------------------------------
# Módulo 15 — Religamento Tripolar
# ----------------------------------------------------------------------------
def _z1c1_m2(ic):
    """Z1 [Ω/km: re, im] e C1 (F/km) do circuito ic (Módulo 2). Retorna (z1, c1, erros)."""
    out, _geo, erros = calcular_m2()
    erros = list(erros)
    if out is not None:
        v = out[0]["circuitos"].get(ic)
        if v and v.get("seq"):
            return [float(v["seq"]["Z1"].real), float(v["seq"]["Z1"].imag)], float(v["seq"]["C1"]), erros
        erros.append(f"Circuito {ic}: parâmetros de sequência não calculados (Módulo 2).")
    return None, None, erros


def _calc15_cache(chave_json):
    import json
    import calc_religamento as crl
    return crl.calcular(json.loads(chave_json))


def entrada_m15():
    """Entrada do motor calc_religamento. Retorna (e, avisos, erros)."""
    N = "15"
    n = int(G("cfg", "n_circ", 1))
    ic = int(G(N, "circ", 1)) if n > 1 else 1
    c = circuito(ic)
    z1, c1, erros = _z1c1_m2(ic)
    e = dict(z1=z1, c1=c1, comp_km=float(G("sis", "km", 80.0) or 0.0), un_kv=c["un"], umax_kv=c["umax"], f=float(G("sis", "freq", 60)),
             scc_mva=G(N, "scc_origem", 3000.0), xr=G(N, "xr", 10.0), scc_rem_mva=G(N, "scc_rem", 2000.0), p_mw=G(N, "p_mw", float(c["mva"]) * float(c["fp"])),
             t_morto_ms=G(N, "t_morto", 500.0), ang_max=G(N, "ang_max", 30.0), v_res_pu=G(N, "v_res", 1.0),
             r_pre=G(N, "r_pre", 400.0) if G(N, "res_pre", False) else 0.0, t_ins_ms=G(N, "t_ins", 8.0), lim_pu=G(N, "sobt_man", 2.0),
             tipo_falta=G(N, "tipo_falta", "Monofásica"), nome_circ=f"C{ic}")
    return e, [], erros


def mod15():
    import json
    N = "15"
    t1, t3 = st.tabs(["Dados de entrada", "Resultados e relatório"])
    n = int(G("cfg", "n_circ", 1))
    with t1:
        st.warning("TRIAGEM ANALÍTICA. As Diretrizes de Projeto Básico (3.2.5, 3.2.6, 3.2.7, 8.4) exigem estudo estatístico de transitórios (ATP, ≥ 200 manobras, "
                   "Bergeron, resistor de pré-inserção em Ω e tempo de inserção em ms; tempo morto de 500 ms): este módulo não o substitui.")
        if n > 1:
            sel(N, "circ", "Circuito em estudo", list(range(1, n + 1)), 1)
        ic = int(G(N, "circ", 1)) if n > 1 else 1
        c = circuito(ic)
        st.caption(f"C{ic}: Z1/C1 do Módulo 2 · {G('sis', 'km', 80.0):g} km · Un = {c['un']:g} kV · Umáx = {c['umax']:g} kV.")
        st.markdown("**Sequência de religamento**")
        a, b, c_, d = st.columns(4)
        sel(N, "tipo_falta", "Tipo de falta", ["Monofásica", "Bifásica", "Trifásica"], c=a)
        num(N, "t_morto", "Tempo morto (ms)", 500.0, 100.0, 5000.0, 10.0, c=b, help="Diretrizes: 500 ms.")
        num(N, "ang_max", "Ângulo máx. no disjuntor (°)", 30.0, 0.0, 90.0, 1.0, c=c_, help="PREMISSA: verificação de sincronismo (synchro-check).")
        num(N, "v_res", "Tensão residual na linha (p.u.)", 1.0, 0.0, 1.0, 0.05, c=d, help="Pior caso 1,0 p.u. com polaridade oposta. Com reator shunt a carga decai/oscila: usar estudo.")
        st.markdown("**Sistema e disjuntor**")
        a, b, c_, d = st.columns(4)
        num(N, "scc_origem", "Scc na origem (MVA)", 3000.0, 10.0, 100000.0, 50.0, c=a)
        num(N, "xr", "X/R da fonte", 10.0, 1.0, 50.0, 0.5, c=b)
        num(N, "scc_rem", "Scc no terminal remoto (MVA)", 2000.0, 10.0, 100000.0, 50.0, c=c_)
        num(N, "p_mw", "Potência transferida (MW)", float(round(c["mva"] * c["fp"], 1)), 0.0, 10000.0, 1.0, c=d)
        a, b, c_ = st.columns(3)
        num(N, "sobt_man", "Limite de sobretensão de manobra (p.u. de √2·Um/√3)", 2.0, 1.0, 4.0, 0.05, c=a, help="PREMISSA: 2,0 p.u. usual; confirmar com o edital/ONS.")
        chk(N, "res_pre", "Disjuntor com resistor de pré-inserção", False, c=b)
        if G(N, "res_pre", False):
            num(N, "r_pre", "Resistor de pré-inserção (Ω)", 400.0, 10.0, 3000.0, 10.0, c=c_)
            num(N, "t_ins", "Tempo de inserção (ms)", 8.0, 1.0, 30.0, 0.5, c=a)
    e, av15, er15 = entrada_m15()
    chave = json.dumps(e, sort_keys=True, default=str)
    r = _calc15_cache(chave) if not er15 else dict(erros=er15, avisos=[])
    with t3:
        if r["erros"]:
            for m in r["erros"]:
                st.warning(m)
        else:
            for m in r["avisos"]:
                st.info(m)
            m1, m2, m3_, m4_ = st.columns(4)
            m1.metric("Sobretensão (p.u.)", f"{r['pico_pu']:.2f}", delta=f"sem resistor {r['sem_resistor_pu']:.2f}", delta_color="off")
            m2.metric("R pré-inserção mínimo (Ω)", "—" if r["r_min"] is None else ("inviável" if r["r_min"] == float("inf") else f"{r['r_min']:.0f}"))
            m3_.metric("Tempo morto × deionização", f"{e['t_morto_ms']:.0f} / {r['t_deion_ms']:.0f} ms")
            m4_.metric("Ângulo no disjuntor (°)", "—" if r["ang"] is None else f"{r['ang']:.1f}")
            st.dataframe(pd.DataFrame([
                ["Sobretensão de religamento", f"{r['pico_pu']:.2f} p.u.", f"≤ {e['lim_pu']:.2f} p.u.", "ATENDE" if r["ok_sobt"] else "NÃO ATENDE"],
                ["Tempo morto", f"{e['t_morto_ms']:.0f} ms", f"≥ {r['t_deion_ms']:.0f} ms", "ATENDE" if r["ok_td"] else "NÃO ATENDE"],
                ["Ângulo através do disjuntor", "—" if r["ang"] is None else f"{r['ang']:.1f}°", f"≤ {e['ang_max']:g}°", "ATENDE" if r["ok_ang"] else "NÃO ATENDE"]],
                columns=["Verificação", "Calculado", "Critério", "Situação"]), hide_index=True)
            try:
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=[p["x"] for p in r["c_rpre"]], y=[p["pu"] for p in r["c_rpre"]], name="× resistor de pré-inserção (Ω)", line=dict(color=AZUL, width=3)))
                fig.add_hline(y=e["lim_pu"], line_dash="dot", line_color="#C00000", annotation_text="Limite")
                fig.update_layout(height=360, xaxis_title="Resistor de pré-inserção (Ω)", yaxis_title="Sobretensão (p.u.)", margin=dict(l=10, r=10, t=20, b=10))
                mostrar_plotly(fig)
            except ImportError:
                st.caption("Instale plotly para ver o gráfico.")
        st.divider()
        st.markdown("**Relatório (padrão BK) e impressão**")

        def _g15(caminho):
            import relatorio_m15
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m15.gerar(caminho, proj, e, r, codigo=(G("proj", "numero") or "BK-LT-MC") + "-M15", rev=G("proj", "revisao") or "R0")
        if ERRO_RELATORIO:
            st.error(ERRO_RELATORIO)
        elif r["erros"]:
            st.info("Preencha os dados pendentes para liberar o relatório e a impressão.")
            r1, r2 = st.columns(2)
            r1.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m15_off", disabled=True)
            r2.button("🖨️ Gerar PDF para impressão", key="btn_pdf_m15_off", disabled=True)
        else:
            if st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m15"):
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    caminho = os.path.join(td, "relatorio.docx")
                    _g15(caminho)
                    with open(caminho, "rb") as fh:
                        ss["_rel_m15"] = fh.read()
            if ss.get("_rel_m15"):
                st.download_button("Baixar relatório do Módulo 15 (.docx)", ss["_rel_m15"], file_name="Relatorio_Modulo15_Religamento_Tripolar.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m15")
            botao_imprimir("m15", "Relatorio_Modulo15_Religamento_Tripolar.pdf", _g15)
        botoes(15, so_limpar=True)


# ----------------------------------------------------------------------------
# Módulo 16 — Blindagem contra Descargas Atmosféricas
# ----------------------------------------------------------------------------
def _calc16_cache(chave_json):
    import json
    import calc_blindagem as cbl
    return cbl.calcular(json.loads(chave_json))


def entrada_m16():
    """Entrada do motor calc_blindagem (geometria do Módulo 2, alturas médias no vão). Retorna (e, avisos, erros)."""
    import calc_blindagem as cbl
    import calc_isolamento as ci
    N = "16"
    g = geometria_atual()
    erros = list(g["erros"])
    eixo = g.get("eixo_x", 0.0)
    n = int(G("cfg", "n_circ", 1))
    reqs = {}
    for i in range(1, n + 1):
        c = circuito(i)
        cab = db.obter_cabo(c["cond"]) if c.get("cond") else {}
        if not cab:
            erros.append(f"Selecione o condutor do circuito {i} (Módulo 1 → Circuitos).")
            continue
        reqs[i] = mod2_calc._cabo_eletrico(cab, int(c["cabos_fase"]), c.get("esp_sub", 0.0))["req"]
    fases = [dict(nome=k["nome"], x=round(k["x"] - eixo, 3), y=round(k["y"] - 2.0 / 3.0 * (k.get("flecha") or 0.0), 3), circuito=k["circuito"], fase=k["fase"],
                  req=reqs.get(k["circuito"], 0.015)) for k in g["condutores"] if k["tipo"] == "fase"]
    guardas = [dict(x=round(k["x"] - eixo, 3), y=round(k["y"] - 2.0 / 3.0 * (k.get("flecha") or 0.0), 3)) for k in g["condutores"] if k["tipo"] == "guarda"]
    cg = db.obter_cabo(G("cfg", "cg1")) if G("cfg", "cg1") else {}
    c1 = circuito(1)
    um, un = float(c1.get("umax") or 0.0), float(c1.get("un") or 0.0)
    modo = G(N, "ng_modo", "Ng informado")
    nk = G(N, "nk", 40.0)
    ng = G(N, "ng", 6.0) if modo == "Ng informado" else cbl.ng_de_nk(nk, "0,2·Nk" if modo.startswith("Nk → 0,2") else "Eriksson")
    h_g = max([k["y"] for k in guardas] or [25.0])
    e = dict(fases=fases, guardas=guardas, ng=float(ng), faixa=G(N, "faixa", "I" if un <= 300 else "II"), un_kv=un, umax_kv=um,
             cfo_kv=(G(N, "cfo", 800.0) if G(N, "cfo_modo", "Tabela 15 (NBR 5422) ÷ 0,961") == "Informado" else None),
             r_pe=G(N, "r_pe", 20.0), z_torre=G(N, "z_torre", 0.0), ioniza=bool(G(N, "ioniza", True)), rho=G(N, "rho", float(G("2", "rho", 1000.0))),
             frac_torre=G(N, "frac_torre", 0.6), b_guarda_m=G(N, "b_guarda", 0.0), h_torre=G(N, "h_torre", round(h_g, 1)),
             meta=G(N, "meta", 1.0 if un >= 345 else 2.0), meta_sf=G(N, "meta_sf", 0.01), ang_lim=G(N, "ang_lim", 30.0),
             r_guarda=(cg.get("diametro_mm") or 9.0) / 2000.0)
    return e, [], erros


def _graf16(r):
    import plotly.graph_objects as go
    fig = go.Figure()
    ths = [i / 40 * 2 * math.pi for i in range(41)]
    rs = float(6.7 * r["i_graf"] ** 0.8)
    for o in r["fases"] + r["guardas"]:
        fase = "nome" in o
        fig.add_trace(go.Scatter(x=[o["x"] + rs * math.cos(t) for t in ths], y=[o["y"] + rs * math.sin(t) for t in ths], mode="lines",
                                 line=dict(color="#C55A11" if fase else "#7F7F7F", width=1, dash="dot"), showlegend=False, hoverinfo="skip"))
    xs = [o["x"] for o in r["fases"] + r["guardas"]]
    xr = [min(xs) - rs, max(xs) + rs]
    fig.add_trace(go.Scatter(x=xr, y=[r["beta"] * rs] * 2, mode="lines", line=dict(color="#8B6B3E"), name=f"Solo (βs·D = {r['beta'] * rs:.1f} m)"))
    fig.add_trace(go.Scatter(x=[o["x"] for o in r["fases"]], y=[o["y"] for o in r["fases"]], mode="markers+text", text=[o["nome"] for o in r["fases"]], textposition="top center",
                             marker=dict(size=10, color=AZUL), name="Fases"))
    fig.add_trace(go.Scatter(x=[o["x"] for o in r["guardas"]], y=[o["y"] for o in r["guardas"]], mode="markers", marker=dict(size=10, symbol="diamond", color="#404040"), name="Para-raios"))
    for a, b in r["ints_graf"]:
        fig.add_shape(type="rect", x0=a, x1=b, y0=0, y1=0.4, line=dict(color="#C00000"), fillcolor="#C00000")
    ymax = max(o["y"] for o in r["fases"] + r["guardas"]) + 0.6 * rs
    fig.update_layout(height=440, xaxis=dict(title="x (m)", scaleanchor="y"), yaxis=dict(title="Altura (m)", range=[0, ymax]),
                      margin=dict(l=10, r=10, t=30, b=10), title=f"EGM com I = {r['i_graf']:.1f} kA (D = {rs:.0f} m); em vermelho: largura exposta de fase")
    return fig


def mod16():
    import json
    N = "16"
    t1, t3 = st.tabs(["Dados de entrada", "Resultados e relatório"])
    with t1:
        st.caption("Modelo eletrogeométrico (Kiessling cap. 4: D = 6,7·I^0,8; βs ao solo) para falha de blindagem e Uc = ½·I·Zc; backflashover pela corrente crítica "
                   "I = CFO/(Zef·(1−k)); metas das Diretrizes de Projeto Básico (≤ 2 desl./100 km/ano até 230 kV; ≤ 1 acima; falha de blindagem ≤ 0,01).")
        res = geometria_atual()
        angs = [v for l in res["angulos"] for k, v in l.items() if k != "Fase" and v is not None]
        c1_, c2_ = st.columns(2)
        c1_.metric("Cabos guarda (Módulo 1)", G("cfg", "n_cg", 1))
        c2_.metric("Maior ângulo de blindagem (Módulo 2)", f"{max(angs):.1f} °" if angs else "—")
        st.markdown("**Descargas atmosféricas**")
        a, b, c_ = st.columns(3)
        sel(N, "ng_modo", "Origem de Ng", ["Ng informado", "Nk → 0,2·Nk (Kiessling 4.3)", "Nk → Eriksson (4.2)"], c=a)
        if G(N, "ng_modo", "Ng informado") == "Ng informado":
            num(N, "ng", "Densidade de descargas Ng (descargas/km²/ano)", 6.0, 0.1, 30.0, 0.1, c=b, help="Mapa de densidade local (ex.: ELAT/INPE). PREMISSA.")
        else:
            num(N, "nk", "Nível ceráunico Nk (dias de trovoada/ano)", 40.0, 1.0, 200.0, 1.0, c=b)
        sel(N, "faixa", "Faixa de tensão (βs)", ["I", "II"], "I" if circuito(1)["un"] <= 300 else "II", c=c_, help="βs = 0,8 (faixa I) / 0,67 (faixa II) – Kiessling 4.4.1.")
        st.markdown("**Isolamento e aterramento**")
        a, b, c_, d = st.columns(4)
        sel(N, "cfo_modo", "CFO (U50 % do isolamento)", ["Tabela 15 (NBR 5422) ÷ 0,961", "Informado"], c=a)
        if G(N, "cfo_modo", "Tabela 15 (NBR 5422) ÷ 0,961") == "Informado":
            num(N, "cfo", "CFO (kV)", 800.0, 100.0, 4000.0, 10.0, c=b)
        num(N, "r_pe", "Resistência de pé de torre R0 (Ω)", 20.0, 1.0, 200.0, 0.5, c=c_, help="Valor médio (Módulo 6). Diretrizes: informar média ou distribuição.")
        num(N, "z_torre", "Z de surto da torre (Ω, em série)", 0.0, 0.0, 60.0, 1.0, c=d, help="0 = só o aterramento (como no exemplo do Kiessling). NECESSITA VALIDAÇÃO.")
        a, b, c_, d = st.columns(4)
        chk(N, "ioniza", "Ionização do solo R_i(I) = R0/√(1+I/Ig)", True, c=a)
        num(N, "rho", "Resistividade do solo (Ω·m)", float(G("2", "rho", 1000.0)), 1.0, 20000.0, 10.0, c=b)
        num(N, "frac_torre", "Fração das descargas em guarda que vão à torre", 0.6, 0.1, 1.0, 0.05, c=c_, help="PREMISSA (IEEE 1243: 60 %).")
        num(N, "h_torre", "Altura da torre (m)", round(max([k["y"] for k in res["condutores"] if k["tipo"] == "guarda"] or [25.0]), 1), 5.0, 150.0, 0.5, c=d)
        st.markdown("**Metas**")
        a, b, c_ = st.columns(3)
        num(N, "meta", "Meta de desligamentos (/100 km/ano)", 1.0 if circuito(1)["un"] >= 345 else 2.0, 0.1, 20.0, 0.1, c=a, help="Diretrizes: 1 (≥ 345 kV) ou 2 (≤ 230 kV).")
        num(N, "meta_sf", "Meta de falha de blindagem (/100 km/ano)", 0.01, 0.001, 1.0, 0.001, c=b, fmt="%.3f")
        num(N, "ang_lim", "Ângulo de blindagem máximo (°)", 30.0, 5.0, 45.0, 1.0, c=c_, help="Kiessling 4.4.2: 10° a 35° conforme a importância da linha. PREMISSA.")
    e, av16, er16 = entrada_m16()
    chave = json.dumps(e, sort_keys=True, default=str)
    r = _calc16_cache(chave) if not er16 else dict(erros=er16, avisos=[])
    with t3:
        if r["erros"]:
            for m in r["erros"]:
                st.warning(m)
        else:
            for m in r["avisos"]:
                st.info(m)
            m1, m2, m3_, m4_ = st.columns(4)
            m1.metric("Falha de blindagem (/100 km/ano)", f"{r['n_sf']:.3f}", delta="ATENDE" if r["ok_sf"] else "NÃO ATENDE", delta_color="off")
            m2.metric("Backflashover (/100 km/ano)", f"{r['n_bf']:.2f}")
            m3_.metric("Total (/100 km/ano)", f"{r['total']:.2f}", delta="ATENDE" if r["ok_total"] else "NÃO ATENDE", delta_color="off")
            m4_.metric("Corrente crítica BF (kA)", f"{r['i_c_bf']:.0f}")
            st.dataframe(pd.DataFrame([
                ["Ng (descargas/km²/ano)", f"{e['ng']:.2f}"], ["CFO (kV)", f"{r['cfo']:.0f}"], ["Zc da fase (Ω)", f"{r['zc']:.0f}"],
                ["Corrente mínima p/ flashover em fase (kA)", f"{r['i_flash_sf']:.1f}"], ["Corrente máx. de falha de blindagem (kA)", f"{r['i_max_blind']:.0f}"],
                ["Descargas em fase (/100 km/ano)", f"{r['n_sf_atinge']:.3f}"], ["Coeficiente de acoplamento k", f"{r['k']:.3f}"],
                ["Ângulo de blindagem máx. (°)", "—" if r["ang_max"] is None else f"{r['ang_max']:.1f}"], ["Descargas na LT N_L (/100 km/ano)", f"{r['n_l']:.1f}"],
                ["P(I ≥ I_c,BF)", f"{r['p_bf']:.3f}"]], columns=["Grandeza", "Valor"]), hide_index=True)
            try:
                mostrar_plotly(_graf16(r))
                import plotly.graph_objects as go
                f2 = go.Figure(go.Scatter(x=r["corr"], y=r["W"], line=dict(color=AZUL, width=3)))
                f2.add_vline(x=r["i_flash_sf"], line_dash="dot", line_color="#C00000", annotation_text="I mín. flashover")
                f2.update_layout(height=320, xaxis_title="Corrente do raio (kA)", yaxis_title="Largura exposta de fase (m)", margin=dict(l=10, r=10, t=20, b=10))
                mostrar_plotly(f2)
            except ImportError:
                st.caption("Instale plotly para ver os gráficos.")
        st.divider()
        st.markdown("**Relatório (padrão BK) e impressão**")

        def _g16(caminho):
            import relatorio_m16
            proj = {k: G("proj", k) for k in ("cliente", "nome", "numero", "revisao", "data", "resp")}
            relatorio_m16.gerar(caminho, proj, e, r, codigo=(G("proj", "numero") or "BK-LT-MC") + "-M16", rev=G("proj", "revisao") or "R0")
        if ERRO_RELATORIO:
            st.error(ERRO_RELATORIO)
        elif r["erros"]:
            st.info("Preencha os dados pendentes para liberar o relatório e a impressão.")
            r1, r2 = st.columns(2)
            r1.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m16_off", disabled=True)
            r2.button("🖨️ Gerar PDF para impressão", key="btn_pdf_m16_off", disabled=True)
        else:
            if st.button("Gerar relatório (.docx, padrão BK)", key="btn_rel_m16"):
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    caminho = os.path.join(td, "relatorio.docx")
                    _g16(caminho)
                    with open(caminho, "rb") as fh:
                        ss["_rel_m16"] = fh.read()
            if ss.get("_rel_m16"):
                st.download_button("Baixar relatório do Módulo 16 (.docx)", ss["_rel_m16"], file_name="Relatorio_Modulo16_Blindagem.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_rel_m16")
            botao_imprimir("m16", "Relatorio_Modulo16_Blindagem.pdf", _g16)
        botoes(16, so_limpar=True)


ROTAS = {1: mod1, 2: mod2, 3: mod3, 4: mod4, 5: mod5, 6: mod6, 7: mod7, 8: mod8,
         9: mod9, 10: mod10, 11: mod11, 12: mod12, 13: mod13, 14: mod14, 15: mod15, 16: mod16}
ROTAS[idx]()

# Salvamento automático: grava no banco sempre que os dados mudam (projeto aberto, ou novo quando já tem nome).
def _autosave():
    import json as _json
    import time as _time
    if not (ss.get("proj_id") or G("proj", "nome")):
        return
    h = _json.dumps(ss["dados"], default=str, sort_keys=True, ensure_ascii=False)
    if h == ss.get("_hash_salvo"):
        return
    try:
        salvar_projeto_atual()
        ss["_hash_salvo"] = h
        ss["_ult_salvo"] = _time.strftime("%H:%M:%S")
        ss.pop("_erro_salvar", None)
    except Exception as e_save:
        ss["_erro_salvar"] = f"{type(e_save).__name__}: {e_save}"


if not ss.get("_acao_salvar"):
    _autosave()
if ss.get("_erro_salvar"):
    st.sidebar.error("Falha ao salvar no banco: " + ss["_erro_salvar"])
elif ss.get("_ult_salvo"):
    st.sidebar.caption(f"💾 Salvo automaticamente às {ss['_ult_salvo']} ({db.descricao_banco()})")

# Ações de salvar são executadas por último, para incluir o que foi editado nesta mesma interação.
_acao = ss.pop("_acao_salvar", None)
if _acao:
    _pid = salvar_projeto_atual(novo=(_acao == "novo"))
    ss["_msg"] = f"Projeto #{_pid} salvo."
    st.rerun()
