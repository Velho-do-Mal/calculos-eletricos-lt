"""
Camada de persistência — BK Cálculos de LT.

- Banco LOCAL por padrão: SQLite em ./bk_lt.db (ao lado deste arquivo).
- Portável: usa SQLAlchemy Core com tipos genéricos. Para migrar para Postgres (Neon, Railway,
  Supabase...) basta definir DATABASE_URL (variável de ambiente ou .streamlit/secrets.toml), ex.:
      DATABASE_URL = "postgresql+psycopg2://usuario:senha@host/banco"
  e rodar `python importar_cabos.py <planilha.xlsm>` para recarregar o catálogo.
- Sem dependência de Streamlit (a leitura de st.secrets é opcional e tolerante a falhas).

Tabelas
-------
cabos          catálogo de cabos (condutores, para-raios, OPGW, contrapeso)
projetos       cabeçalho dos projetos (nome, cliente, número, revisão)
projeto_secoes dados de cada projeto por seção ('proj', 'sis', 'cfg', 'geo', 'viz', 'viz0'.., '3'..'16'),
               em JSON texto (portável entre SQLite e Postgres)
"""
import datetime as dt
import json
import os
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import event

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_URL = f"sqlite:///{BASE_DIR / 'bk_lt.db'}"

KGF_PARA_KN = 0.00980665          # 1 kgf = 9,80665 N
KGF_MM2_PARA_GPA = 0.00980665     # 1 kgf/mm² = 9,80665 MPa = 0,00980665 GPa

USOS = ("CONDUTOR", "PARA-RAIOS", "OPGW", "CONTRAPESO")
USOS_GUARDA = ("PARA-RAIOS", "OPGW")

# Campos numéricos e textuais do catálogo (ordem usada nas telas)
CABO_NUM = [
    "secao_mm2", "diametro_mm", "massa_kg_m", "rtc_kgf", "rtc_kn", "ampacidade_a",
    "r_cc_20", "r_ca_75", "modulo_kgf_mm2", "modulo_gpa", "dilatacao_1e6", "alfa_20c",
    "curto_ka_s", "diam_fio_al_mm", "diam_fio_aco_mm", "rmg_mm",
]
CABO_TXT = [
    "codigo", "uso", "tipo", "nome", "bitola", "formacao", "fornecedor",
    "origem", "alerta_importacao", "observacao",
]
CABO_CAMPOS = CABO_TXT[:7] + CABO_NUM + CABO_TXT[7:]

metadata = sa.MetaData()

cabos = sa.Table(
    "cabos", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("codigo", sa.String(120), nullable=False, unique=True),   # ex.: 'LINNET 336,4 MCM'
    sa.Column("uso", sa.String(20), nullable=False),                    # CONDUTOR | PARA-RAIOS | OPGW | CONTRAPESO
    sa.Column("tipo", sa.String(40)),                                   # CAA, CA, CAL, T-CAA, AÇO, OPGW...
    sa.Column("nome", sa.String(80)),                                   # nome comercial (LINNET, EHS...)
    sa.Column("bitola", sa.String(40)),
    sa.Column("formacao", sa.String(40)),                               # ex.: '26 x 7'
    sa.Column("secao_mm2", sa.Float),
    sa.Column("diametro_mm", sa.Float),
    sa.Column("massa_kg_m", sa.Float),
    sa.Column("rtc_kgf", sa.Float),                                     # carga de ruptura (kgf), como na planilha
    sa.Column("rtc_kn", sa.Float),                                      # = kgf x 0,00980665
    sa.Column("ampacidade_a", sa.Float),                                # a 75 °C, valor do fabricante
    sa.Column("r_cc_20", sa.Float),                                     # Ω/km, CC a 20 °C
    sa.Column("r_ca_75", sa.Float),                                     # Ω/km, CA 60 Hz a 75 °C
    sa.Column("modulo_kgf_mm2", sa.Float),                              # módulo de elasticidade final (kgf/mm²)
    sa.Column("modulo_gpa", sa.Float),                                  # = kgf/mm² x 0,00980665
    sa.Column("dilatacao_1e6", sa.Float),                               # coef. de dilatação linear em 10⁻⁶/°C
    # Rótulo na planilha: "coef. de dilatação linear por grau a 20 °C (α)"; os valores (0,00403 Al /
    # 0,0032 aço) correspondem ao coeficiente de temperatura da resistência. Guardado como veio.
    sa.Column("alfa_20c", sa.Float),
    sa.Column("curto_ka_s", sa.Float),                                  # 'kA.s' conforme planilha (só OPGW)
    sa.Column("fornecedor", sa.String(60)),
    sa.Column("diam_fio_al_mm", sa.Float),
    sa.Column("diam_fio_aco_mm", sa.Float),
    sa.Column("rmg_mm", sa.Float),                                      # NÃO consta da planilha: cadastrar à mão
    sa.Column("origem", sa.String(200)),                                # 'planilha ... linha N' ou 'manual'
    sa.Column("alerta_importacao", sa.Text),                            # preenchido automaticamente na importação
    sa.Column("observacao", sa.Text),                                   # livre, preservado nas reimportações
    sa.Column("criado_em", sa.DateTime),
    sa.Column("atualizado_em", sa.DateTime),
)

projetos = sa.Table(
    "projetos", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("nome", sa.String(200)),
    sa.Column("cliente", sa.String(200)),
    sa.Column("numero", sa.String(60)),
    sa.Column("revisao", sa.String(20)),
    sa.Column("criado_em", sa.DateTime),
    sa.Column("atualizado_em", sa.DateTime),
)

projeto_secoes = sa.Table(
    "projeto_secoes", metadata,
    sa.Column("projeto_id", sa.Integer, sa.ForeignKey("projetos.id"), primary_key=True),
    sa.Column("secao", sa.String(20), primary_key=True),
    sa.Column("dados", sa.Text, nullable=False),                        # JSON
    sa.Column("atualizado_em", sa.DateTime),
)

_engine = None


def _agora():
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


def get_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        try:
            import streamlit as st
            url = st.secrets.get("DATABASE_URL")
        except Exception:
            url = None
    url = url or DEFAULT_URL
    # Neon/Railway entregam "postgres://" ou "postgresql://": fixa o driver psycopg2 (o padrão do SQLAlchemy varia por versão)
    for pref in ("postgres://", "postgresql://"):
        if url.startswith(pref):
            url = "postgresql+psycopg2://" + url[len(pref):]
            break
    return url


def get_engine():
    global _engine
    if _engine is None:
        url = get_url()
        _engine = sa.create_engine(url, future=True, pool_pre_ping=True)
        if _engine.dialect.name == "sqlite":
            @event.listens_for(_engine, "connect")
            def _fk_on(dbapi_conn, _):
                dbapi_conn.execute("PRAGMA foreign_keys=ON")
        metadata.create_all(_engine)
    return _engine


def reset_engine():
    """Descarta o engine (usado em testes ao trocar DATABASE_URL)."""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


def init_db():
    return get_engine()


def eh_sqlite():
    """True se o app está usando o banco local (SQLite) — ou seja, DATABASE_URL não foi aplicada."""
    return sa.engine.make_url(get_url()).get_backend_name() == "sqlite"


def descricao_banco():
    url = sa.engine.make_url(get_url())
    if url.get_backend_name() == "sqlite":
        return f"SQLite local ({Path(url.database).name})"
    return f"{url.get_backend_name()} ({url.host})"


# ----------------------------------------------------------------------------
# Cabos
# ----------------------------------------------------------------------------
def _linha(row):
    return dict(row._mapping)


def contar_cabos():
    with get_engine().connect() as c:
        return c.execute(sa.select(sa.func.count()).select_from(cabos)).scalar_one()


def listar_cabos(usos=None, tipos=None, busca=None):
    q = sa.select(cabos).order_by(cabos.c.uso, cabos.c.tipo, cabos.c.secao_mm2, cabos.c.codigo)
    if usos:
        q = q.where(cabos.c.uso.in_(list(usos)))
    if tipos:
        q = q.where(cabos.c.tipo.in_(list(tipos)))
    if busca:
        q = q.where(cabos.c.codigo.ilike(f"%{busca.strip()}%"))
    with get_engine().connect() as c:
        return [_linha(r) for r in c.execute(q)]


def codigos_cabos(usos):
    q = (sa.select(cabos.c.codigo).where(cabos.c.uso.in_(list(usos)))
         .order_by(cabos.c.tipo, cabos.c.secao_mm2, cabos.c.codigo))
    with get_engine().connect() as c:
        return [r[0] for r in c.execute(q)]


def tipos_cabos():
    with get_engine().connect() as c:
        return [r[0] for r in c.execute(sa.select(cabos.c.tipo).distinct().order_by(cabos.c.tipo)) if r[0]]


def obter_cabo(codigo):
    if not codigo:
        return {}
    with get_engine().connect() as c:
        r = c.execute(sa.select(cabos).where(cabos.c.codigo == codigo)).first()
    return _linha(r) if r else {}


def salvar_cabo(d, preservar=()):
    """
    Insere ou atualiza por 'codigo'. Em atualização, campos em `preservar` mantêm o valor
    existente quando ele não for nulo (usado na reimportação para não apagar o RMG cadastrado).
    Deriva rtc_kn/rtc_kgf e modulo_gpa/modulo_kgf_mm2 quando só um dos pares é informado.
    Retorna 'inserido' ou 'atualizado'.
    """
    d = {k: v for k, v in d.items() if k in CABO_CAMPOS}
    d["codigo"] = (d.get("codigo") or "").strip()
    if not d["codigo"]:
        raise ValueError("Código do cabo é obrigatório.")
    if d.get("uso") not in USOS:
        raise ValueError(f"Uso inválido: {d.get('uso')!r}. Use um de {USOS}.")
    if d.get("rtc_kn") is None and d.get("rtc_kgf") is not None:
        d["rtc_kn"] = d["rtc_kgf"] * KGF_PARA_KN
    elif d.get("rtc_kgf") is None and d.get("rtc_kn") is not None:
        d["rtc_kgf"] = d["rtc_kn"] / KGF_PARA_KN
    if d.get("modulo_gpa") is None and d.get("modulo_kgf_mm2") is not None:
        d["modulo_gpa"] = d["modulo_kgf_mm2"] * KGF_MM2_PARA_GPA
    elif d.get("modulo_kgf_mm2") is None and d.get("modulo_gpa") is not None:
        d["modulo_kgf_mm2"] = d["modulo_gpa"] / KGF_MM2_PARA_GPA
    agora = _agora()
    with get_engine().begin() as c:
        atual = c.execute(sa.select(cabos).where(cabos.c.codigo == d["codigo"])).first()
        if atual is None:
            d.setdefault("origem", "manual")
            c.execute(sa.insert(cabos).values(**d, criado_em=agora, atualizado_em=agora))
            return "inserido"
        atual = _linha(atual)
        for campo in preservar:
            if atual.get(campo) is not None:
                d[campo] = atual[campo]
        c.execute(sa.update(cabos).where(cabos.c.id == atual["id"]).values(**d, atualizado_em=agora))
        return "atualizado"


def excluir_cabo(codigo):
    """Só exclui cabos cadastrados manualmente (origem = 'manual')."""
    with get_engine().begin() as c:
        r = c.execute(sa.delete(cabos).where(cabos.c.codigo == codigo, cabos.c.origem == "manual"))
        return r.rowcount > 0


# ----------------------------------------------------------------------------
# Projetos
# ----------------------------------------------------------------------------
def _enc(o):
    if isinstance(o, (dt.date, dt.datetime)):
        return {"__date__": o.isoformat()}
    if hasattr(o, "item"):          # numpy escalar
        return o.item()
    return str(o)


def _dec(o):
    if "__date__" in o:
        return dt.date.fromisoformat(o["__date__"][:10])
    return o


def listar_projetos():
    q = sa.select(projetos).order_by(projetos.c.atualizado_em.desc(), projetos.c.id.desc())
    with get_engine().connect() as c:
        return [_linha(r) for r in c.execute(q)]


def salvar_projeto(pid, meta, secoes):
    """
    pid: id existente ou None (cria). meta: dict com nome/cliente/numero/revisao.
    secoes: {secao: dict}. Substitui todas as seções do projeto. Retorna o id.
    """
    agora = _agora()
    campos = {k: (meta.get(k) or None) for k in ("nome", "cliente", "numero", "revisao")}
    with get_engine().begin() as c:
        existe = pid is not None and c.execute(
            sa.select(projetos.c.id).where(projetos.c.id == pid)).first() is not None
        if existe:
            c.execute(sa.update(projetos).where(projetos.c.id == pid).values(**campos, atualizado_em=agora))
        else:
            pid = c.execute(sa.insert(projetos).values(**campos, criado_em=agora, atualizado_em=agora)
                            ).inserted_primary_key[0]
        c.execute(sa.delete(projeto_secoes).where(projeto_secoes.c.projeto_id == pid))
        linhas = [{"projeto_id": pid, "secao": str(s), "atualizado_em": agora,
                   "dados": json.dumps(v, default=_enc, ensure_ascii=False)}
                  for s, v in secoes.items() if v]
        if linhas:
            c.execute(sa.insert(projeto_secoes), linhas)
    return pid


def carregar_projeto(pid):
    with get_engine().connect() as c:
        if c.execute(sa.select(projetos.c.id).where(projetos.c.id == pid)).first() is None:
            return None
        rows = c.execute(sa.select(projeto_secoes.c.secao, projeto_secoes.c.dados)
                         .where(projeto_secoes.c.projeto_id == pid))
        return {s: json.loads(d, object_hook=_dec) for s, d in rows}


def excluir_projeto(pid):
    with get_engine().begin() as c:
        c.execute(sa.delete(projeto_secoes).where(projeto_secoes.c.projeto_id == pid))
        return c.execute(sa.delete(projetos).where(projetos.c.id == pid)).rowcount > 0
