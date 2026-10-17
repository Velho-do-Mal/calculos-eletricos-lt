"""Base do documento "Procedimentos para Estudos Elétricos" (padrão BK): auxiliares de texto, equações, tabelas e blocos comuns.

O documento ensina, para cada estudo (Módulos 1 a 16 do app "BK | Cálculos de LT"), (a) a metodologia manual com equações,
(b) um exemplo resolvido passo a passo com o CASO DE REFERÊNCIA e (c) como preencher o mesmo estudo no app.
"""
import math

from docx.enum.text import WD_ALIGN_PARAGRAPH

from relatorio_m2 import f, mi, mu, mfrac, mpar, msqrt, msub, msup  # noqa: F401  (reexportados para os módulos de conteúdo)

# ----------------------------------------------------------------------------- caso de referência
REF = dict(
    nome="LT 138 kV Exemplo", cliente="Energisa", numero="BK-EX-001",
    un=138.0, um=145.0, f=60.0, km=80.0, mva=60.0, fp=0.95,
    cabo="HAWK 477 MCM", d_mm=21.78, s_mm2=280.8, massa=0.9764, rtc_kn=87.0634, r20=0.1196, r75=0.1435, e_gpa=74.4619, dil=18.9,
    alfa_r=0.00403,
    fases=[("A", -4.5, 24.0), ("B", 0.0, 24.0), ("C", 4.5, 24.0)], guardas=[("CG1 (OPGW 12,4 mm 36FO)", 0.0, 30.0), ("CG2 (EHS 7/16\")", 6.0, 30.0)],
    alt=870.0, lat=-27.6, lon=-48.5, rho=1000.0,
)
IN_A = REF["mva"] * 1e3 / (math.sqrt(3) * REF["un"])        # corrente nominal (A)


# ----------------------------------------------------------------------------- equações (atalhos)
def V(n, s=None):
    """Variável em itálico com índice romano opcional."""
    return msub(mi(n), mu(s)) if s else mi(n)


def T(t):
    return mu(t)


def EQ(R, *partes):
    R.eq("".join(partes))


# ----------------------------------------------------------------------------- tabelas e blocos padrão
def passos(R, titulo, linhas, larg=(1.0, 10.3, 4.7)):
    """Tabela Passo | Cálculo (expressão e substituição) | Resultado."""
    R.tabela(titulo, ["Passo", "Cálculo (expressão → substituição)", "Resultado"],
             [[str(i), a, b] for i, (a, b) in enumerate(linhas, start=1)], list(larg))


def app_tab(R, titulo, linhas, larg=(2.6, 5.9, 3.3, 5.2)):
    """Tabela de preenchimento no app: Aba | Campo | Valor do exemplo | Observação."""
    R.tabela(titulo, ["Aba", "Campo no app", "Valor", "Observação"], [list(x) for x in linhas], list(larg))


def comparacao(R, titulo, linhas):
    """Manual × app: Grandeza | Manual (este documento) | App | Diferença."""
    R.tabela(titulo, ["Grandeza", "Cálculo manual", "Resultado do app", "Diferença"], [list(x) for x in linhas], [6.0, 3.6, 3.6, 3.8])


def dif(m, a, n=2):
    """Diferença relativa (%) entre manual e app."""
    if not a:
        return "—"
    return f"{f(100.0 * (m - a) / a, n)} %"


def checklist(R, itens):
    R.lista(["[ ] " + i for i in itens])


def cabecalho_estudo(R, n, nome, objetivo, quando, normas):
    """Abre o capítulo do estudo com objetivo, quando fazer e normas/referências."""
    R.h1(f"M{n} – {nome.upper()}")
    R.h2("Objetivo e quando fazer")
    R.p(objetivo)
    R.p(quando, "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(normas)


def fonte_mod(R, texto):
    R.p(texto, italico=True)


def aviso_validacao(R, txt):
    R.p(txt, "NECESSITA VALIDAÇÃO:")


def sub(R, titulo):
    R.h2(titulo)


def justificado(R, txt):
    R.p(txt, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
