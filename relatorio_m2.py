"""
Relatório do Módulo 2 – Parâmetros Elétricos, no padrão BK (memória de cálculo), em .docx.

- Estrutura de 10 itens + anexo (script), etiquetas padrão, tabelas com cabeçalho cinza, equações OMML nativas.
- Cada circuito é calculado e apresentado (circuito duplo: os dois, com a seção de acoplamento).
- O MODELO π é item obrigatório: equações, valores de Zs e Yp, quadripolo ABCD e esquema, por circuito.
- Layout: reproduzido a partir da especificação textual do PADRÃO DE RELATÓRIO (o arquivo-modelo
  DOCUMENTO_PADRAO_BK.docx não foi fornecido; logos, razão social/CNPJ e rodapé institucional ficam marcados).
"""
import cmath
import datetime as dt
import io
import math
import os
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor

import calc_parametros as cp

BASE = os.path.dirname(os.path.abspath(__file__))
MODELO_BK = os.path.join(BASE, "dados", "modelo_bk.docx")   # DOCUMENTO PADRÃO BK (base de todos os relatórios)

# scripts de cálculo anexados (ANEXO A) por relatório
SCRIPTS_POR_MODULO = {
    "relatorio_m2": ["calc_parametros.py", "mod2_calc.py"],
    "relatorio_m3": ["calc_ventos.py"],
    "relatorio_m4": ["calc_faixa.py"],
    "relatorio_m5": ["calc_isolamento.py"],
    "relatorio_m6": ["calc_aterramento.py"],
    "relatorio_m7": ["calc_condutor.py"],
    "relatorio_m8": ["calc_campos.py", "calc_faixa.py"],
    "relatorio_m9": ["calc_interferencia.py"],
    "relatorio_m10": ["calc_corona.py"],
    "relatorio_m11": ["calc_efeito_corona.py"],
    "relatorio_m12": ["calc_tensao_operativa.py", "calc_isolamento.py"],
    "relatorio_m13": ["calc_ampacidade_flecha.py"],
    "relatorio_m14": ["calc_rejeicao.py"],
    "relatorio_m15": ["calc_religamento.py"],
    "relatorio_m16": ["calc_blindagem.py", "calc_isolamento.py"],
}
_MODULO_CHAMADOR = [None]


def _scripts_do_chamador():
    """Descobre qual relatorio_mN está gerando o documento e devolve os caminhos dos scripts de cálculo."""
    import inspect
    for fr in inspect.stack()[2:]:
        nome = os.path.splitext(os.path.basename(fr.filename))[0]
        if nome.startswith("relatorio_m") and nome in SCRIPTS_POR_MODULO:
            _MODULO_CHAMADOR[0] = nome + ".py"
            return [os.path.join(BASE, a) for a in SCRIPTS_POR_MODULO[nome]]
    return []


AZUL, LARANJA, VERDE, ROXO, VERM, CINZA = "#2563EB", "#F59E0B", "#10B981", "#8B5CF6", "#EF4444", "#6B7280"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


# ----------------------------------------------------------------------------- formatação pt-BR
def f(x, n=2):
    s = f"{x:,.{n}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fc(z, n=3):
    """Complexo retangular em pt-BR: a + jb."""
    return f"{f(z.real, n)} {'+' if z.imag >= 0 else '−'} j{f(abs(z.imag), n)}"


def fp(z, n=2, na=2):
    """Complexo polar: |z| ∠ ângulo°."""
    return f"{f(abs(z), n)} ∠ {f(math.degrees(cmath.phase(z)), na)}°"


# ----------------------------------------------------------------------------- OMML
def _t(t, up=False):
    sty = '<m:rPr><m:sty m:val="p"/></m:rPr>' if up else ""
    t = t.replace("&", "&amp;").replace("<", "&lt;")
    return f'<m:r>{sty}<m:t xml:space="preserve">{t}</m:t></m:r>'


def mi(t):   return _t(t)                                  # itálico (variável)
def mu(t):   return _t(t, True)                            # romano (unidade, função, número)
def msub(b, s): return f"<m:sSub><m:e>{b}</m:e><m:sub>{s}</m:sub></m:sSub>"
def msup(b, s): return f"<m:sSup><m:e>{b}</m:e><m:sup>{s}</m:sup></m:sSup>"
def mfrac(n, d): return f"<m:f><m:num>{n}</m:num><m:den>{d}</m:den></m:f>"
def msqrt(x):   return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{x}</m:e></m:rad>'
def mrad(n, x): return f"<m:rad><m:deg>{n}</m:deg><m:e>{x}</m:e></m:rad>"
def mpar(x):    return f"<m:d><m:e>{x}</m:e></m:d>"


MODO_PDF = False   # True ao gerar a versão para impressão em PDF (equações em texto linear)


def omml_linear(xml):
    """Converte o OMML construído acima em texto linear (a/b → (a)/(b), x_y, x^y, √)."""
    from lxml import etree
    raiz = etree.fromstring(f'<r xmlns:m="{M_NS}">{xml}</r>')
    q = lambda t: f"{{{M_NS}}}{t}"

    def tx(e):
        if e.tag == q("t"):
            return e.text or ""
        filhos = lambda n: "".join(tx(x) for x in (e.find(q(n)) if e.find(q(n)) is not None else []))
        if e.tag == q("f"):
            return f"({filhos('num')})/({filhos('den')})"
        if e.tag == q("sSub"):
            b, sb = filhos("e"), filhos("sub")
            return f"{b}_{sb}" if len(sb) == 1 else f"{b}_({sb})"
        if e.tag == q("sSup"):
            return f"{filhos('e')}^({filhos('sup')})"
        if e.tag == q("rad"):
            return f"√({filhos('e')})"
        if e.tag == q("d"):
            return f"({filhos('e')})"
        return "".join(tx(x) for x in e)
    return tx(raiz)


def omath(xml):
    return parse_xml(f'<m:oMath xmlns:m="{M_NS}">{xml}</m:oMath>')


# ----------------------------------------------------------------------------- documento
class Rel:
    def __init__(self, proj, titulo, codigo, rev, scripts=None):
        # Base = DOCUMENTO PADRÃO BK (capa/carimbo, cabeçalho, rodapé, estilos e numeração originais)
        self.doc = Document(MODELO_BK)
        self.proj, self.titulo, self.codigo, self.rev = proj, titulo, codigo, rev
        self.eq_n = 0
        self.tab_n = 0
        self.fig_n = 0
        self.tmp = tempfile.mkdtemp()
        self.sec = [0, 0]
        self._toc = []            # (nível, texto) coletados para o SUMÁRIO
        self._toc_anchor = None
        self.scripts = list(scripts) if scripts is not None else _scripts_do_chamador()
        self._limpar_corpo()

    def _limpar_corpo(self):
        """Mantém capa + quebra de seção do modelo; remove o conteúdo de exemplo do corpo."""
        body = self.doc.element.body
        filhos = list(body)
        for el in filhos[3:-1]:          # 0 capa, 1-2 parágrafos com a seção 1, último = sectPr da seção 2
            body.remove(el)

    @staticmethod
    def _sombra(cell, cor):
        cell._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{cor}"/>'))

    @staticmethod
    def _bordas(tbl, sz=4):
        tblPr = tbl._tbl.tblPr
        b = parse_xml(f'<w:tblBorders {nsdecls("w")}>' + "".join(
            f'<w:{x} w:val="single" w:sz="{sz}" w:space="0" w:color="000000"/>'
            for x in ("top", "left", "bottom", "right", "insideH", "insideV")) + "</w:tblBorders>")
        tblPr.append(b)

    @staticmethod
    def _campo(par, instr, texto="1", tam=None):
        r = par.add_run()
        if tam:
            r.font.size = Pt(tam)
        for xml in (f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>',
                    f'<w:instrText {nsdecls("w")} xml:space="preserve"> {instr} </w:instrText>',
                    f'<w:fldChar {nsdecls("w")} w:fldCharType="separate"/>'):
            r._r.append(parse_xml(xml))
        r._r.append(parse_xml(f'<w:t {nsdecls("w")}>{texto}</w:t>'))
        r._r.append(parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>'))

    # --- utilitários de célula do modelo
    @staticmethod
    def _settc(tc, txt):
        """Escreve txt na 1ª célula-parágrafo preservando a formatação da 1ª run (ou da marca de parágrafo)."""
        p = tc.findall(qn("w:p"))[0]
        runs = [r for r in p.findall(qn("w:r")) if r.find(qn("w:fldChar")) is None and r.find(qn("w:instrText")) is None]
        if runs:
            r0 = runs[0]
            for r in runs[1:]:
                p.remove(r)
            for ch in list(r0):
                if ch.tag != qn("w:rPr"):
                    r0.remove(ch)
        else:
            r0 = parse_xml(f'<w:r {nsdecls("w")}/>')
            ppr = p.find(qn("w:pPr"))
            rpr = ppr.find(qn("w:rPr")) if ppr is not None else None
            if rpr is not None:
                import copy
                r0.append(copy.deepcopy(rpr))
            p.append(r0)
        t = parse_xml(f'<w:t {nsdecls("w")} xml:space="preserve"/>')
        t.text = str(txt)
        r0.append(t)

    def _logo_cliente(self, tc, tam=9):
        """Mantém o logotipo do cliente só para a Energisa (logo do modelo); senão troca pelo nome do cliente."""
        cli = (self.proj.get("cliente") or "").strip()
        if "energisa" in cli.casefold():
            return
        for r in list(tc.iter(qn("w:r"))):
            if r.find(qn("w:drawing")) is not None or r.find(qn("w:pict")) is not None:
                r.getparent().remove(r)
        p = tc.findall(qn("w:p"))[0]
        if cli:
            r = parse_xml(f'<w:r {nsdecls("w")}><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>'
                          f'<w:b/><w:sz w:val="{tam*2}"/></w:rPr><w:t xml:space="preserve"></w:t></w:r>')
            r.find(qn("w:t")).text = cli
            p.append(r)

    def _preencher_modelo(self, obra, revisoes):
        """Preenche a capa (carimbo) e o cabeçalho do modelo BK."""
        d = self.doc
        proj = self.proj
        resp = proj.get("resp") or "-"
        data = proj.get("data_txt") or ""
        numrev = str(self.rev).replace("R", "") or "0"
        # ---- capa
        trs = d.tables[0]._tbl.findall(qn("w:tr"))
        cel = lambda i: trs[i].findall(qn("w:tc"))
        # histórico de revisões: linhas 19-23 (a última é a mais recente)
        hist = [r for r in revisoes if any(str(x).strip() for x in r)]
        for k, lin in enumerate(reversed(hist[-5:])):
            tcs = cel(23 - k)
            vals = list(lin) + [""] * 6
            vals = [vals[0] or numrev, vals[1], vals[2] or data, vals[3] or resp, vals[4] or "-", vals[5]]
            for tc, v in zip(tcs, vals[:6]):
                self._settc(tc, v)
        self._logo_cliente(cel(25)[1], 12)
        self._settc(cel(26)[1], data)
        self._settc(cel(27)[1], resp)
        self._settc(cel(28)[1], "-")
        self._settc(cel(29)[1], "")
        self._settc(cel(30)[0], obra)
        self._settc(cel(32)[0], self.titulo.upper())
        self._settc(cel(33)[1], self.codigo)
        self._settc(cel(33)[5], numrev)
        # ---- cabeçalho (seção do corpo)
        t = d.sections[-1].header.tables[0]._tbl
        htr = t.findall(qn("w:tr"))
        self._logo_cliente(htr[0].findall(qn("w:tc"))[2], 9)
        linha = htr[2].findall(qn("w:tc"))
        self._settc(linha[0], self.codigo)
        self._settc(linha[1], self.rev)
        self._settc(linha[2], f"{self.titulo} — {obra}" if obra and obra != "—" else self.titulo)
        cp = d.core_properties
        cp.title, cp.author, cp.subject = f"{self.titulo} – {obra}", "BARABACH & KNOPP ENGENHARIA E TECNOLOGIA", self.codigo

    def capa(self, obra, revisoes):
        self._preencher_modelo(obra, revisoes)

    # --- blocos de texto
    def h1(self, txt, numerado=True):
        """Título principal no estilo do modelo (a numeração 1., 2., ... é automática do estilo)."""
        par = self.doc.add_paragraph(txt, style="1. Título BK principal")
        if numerado:
            self.sec[0] += 1
            self.sec[1] = 0
            self._toc.append((1, f"{self.sec[0]}. {txt.upper()}"))
        else:
            par._p.get_or_add_pPr().append(parse_xml(
                f'<w:numPr {nsdecls("w")}><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>'))
            self._toc.append((1, txt.upper()))
        return par

    def h2(self, txt):
        """Subtítulo: o modelo usa numeração manual (N.M.) no texto."""
        self.sec[1] += 1
        t = f"{self.sec[0]}.{self.sec[1]}. {txt}"
        self._toc.append((2, t))
        par = self.doc.add_paragraph(t, style="1.1. Subtítulo BK")
        par._p.get_or_add_pPr().append(parse_xml(
            f'<w:numPr {nsdecls("w")}><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>'))   # numeração é manual no modelo
        return par

    def p(self, txt="", rotulo=None, italico=False, align=None):
        par = self.doc.add_paragraph(style="Body Text")
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if rotulo:
            r = par.add_run(rotulo + " ")
            r.bold = True
            if rotulo.startswith(("Substituição", "Resultado", "Verificação", "Comparação")):
                par.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = par.add_run(txt)
        r.italic = italico
        if align is not None:
            par.alignment = align
        return par

    def lista(self, itens):
        for it in itens:
            par = self.doc.add_paragraph(style="Body Text")
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            par.add_run("- " + it)

    def obs(self, txt):
        self.p("Observação: " + txt, italico=True)

    def eq(self, xml):
        """Equação OMML centralizada com numeração à direita (tabulações)."""
        self.eq_n += 1
        par = self.doc.add_paragraph(style="Body Text")
        par.alignment = WD_ALIGN_PARAGRAPH.LEFT
        ts = par.paragraph_format.tab_stops
        ts.add_tab_stop(Cm(8.0), WD_TAB_ALIGNMENT.CENTER)
        ts.add_tab_stop(Cm(16.0), WD_TAB_ALIGNMENT.RIGHT)
        par.add_run("\t")
        if MODO_PDF:       # o conversor de PDF (LibreOffice) não exibe OMML: usa a forma linear
            par.add_run(omml_linear(xml)).italic = True
        else:
            par._p.append(omath(xml))
        par.add_run(f"\t({self.eq_n})")
        return self.eq_n

    def simbolos(self, linhas):
        self.p("Onde:", align=WD_ALIGN_PARAGRAPH.LEFT)
        self.lista([f"{s} — {m} [{u}]" if u else f"{s} — {m}" for s, m, u in linhas])

    def tabela(self, titulo, cab, linhas, larg=None, fonte=None):
        self.tab_n += 1
        cp_ = self.doc.add_paragraph(style="Body Text")
        cp_.alignment = WD_ALIGN_PARAGRAPH.LEFT
        cp_.paragraph_format.keep_with_next = True
        r = cp_.add_run(f"Tabela {self.tab_n} – {titulo}")
        r.bold, r.font.size = True, Pt(10)
        t = self.doc.add_table(1 + len(linhas), len(cab))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        self._bordas(t)
        for i, h in enumerate(cab):
            c = t.cell(0, i)
            self._sombra(c, "D9D9D9")
            c.text = ""
            rr = c.paragraphs[0].add_run(h)
            rr.bold, rr.font.size, rr.font.name = True, Pt(9), "Arial"
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        for j, lin in enumerate(linhas, start=1):
            for i, v in enumerate(lin):
                c = t.cell(j, i)
                c.text = ""
                par = c.paragraphs[0]
                par.paragraph_format.space_after = Pt(0)
                txt = str(v)
                num = txt.replace(".", "").replace(",", "").replace("−", "").replace(" ", "").replace("j", "") \
                    .replace("∠", "").replace("°", "").replace("+", "").replace("%", "")
                par.alignment = WD_ALIGN_PARAGRAPH.RIGHT if (num.isdigit() and i > 0) else WD_ALIGN_PARAGRAPH.LEFT
                run = par.add_run(txt)
                run.font.size, run.font.name = Pt(9), "Arial"
                if txt in ("ATENDE", "NÃO ATENDE", "PENDENTE"):
                    run.bold = True
        for ri, row in enumerate(t.rows):
            trPr = row._tr.get_or_add_trPr()
            trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
            if ri == 0:      # cabeçalho repete em nova página
                trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
            for c in row.cells:
                for pp in c.paragraphs:
                    pp.style = "Table Paragraph"
                    pp.paragraph_format.space_after = Pt(0)
                    if ri < 2:   # cabeçalho nunca fica sozinho no fim da página
                        pp.paragraph_format.keep_with_next = True
        if larg:
            for row in t.rows:
                for i, w in enumerate(larg):
                    row.cells[i].width = Cm(w)
        if fonte:
            p_ = self.doc.add_paragraph(style="Body Text")
            p_.alignment = WD_ALIGN_PARAGRAPH.LEFT
            rr = p_.add_run("Fonte: " + fonte)
            rr.font.size, rr.italic = Pt(8), True
        else:
            self.doc.add_paragraph(style="Body Text").paragraph_format.space_after = Pt(2)

    def figura(self, fig, legenda, comentario=None, larg_cm=15.0):
        self.fig_n += 1
        path = os.path.join(self.tmp, f"fig{self.fig_n}.png")
        fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        par = self.doc.add_paragraph(style="Body Text")
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.keep_with_next = True
        par.add_run().add_picture(path, width=Cm(larg_cm))
        c = self.doc.add_paragraph(style="Body Text")
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = c.add_run(f"Figura {self.fig_n} – {legenda}")
        r.font.size, r.bold = Pt(9), True
        if comentario:
            self.p(comentario)

    def sumario(self, itens=None):
        """Página SUMÁRIO no formato do modelo; a lista é gerada a partir dos títulos efetivamente emitidos."""
        par = self.doc.add_paragraph(style="Body Text")
        par.add_run("SUMÁRIO").bold = True
        self._toc_anchor = par._p
        pb = self.doc.add_paragraph(style="Body Text")
        pb.add_run().add_break(WD_BREAK.PAGE)

    def _preencher_sumario(self):
        if self._toc_anchor is None:
            return
        ant = self._toc_anchor
        for nivel, txt in self._toc:
            par = self.doc.add_paragraph(style="Body Text")
            par.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if nivel == 2:
                par.paragraph_format.left_indent = Cm(0.6)
            par.add_run(txt)
            ant.addnext(par._p)
            ant = par._p

    def anexo_script(self):
        """ANEXO A – SCRIPT DE CÁLCULO: código-fonte dos módulos de cálculo (Courier New 7 pt, como no relatório do M2)."""
        arqs = [a for a in self.scripts if os.path.exists(a)]
        if not arqs:
            return
        self.doc.add_page_break()
        self.h1("ANEXO A – SCRIPT DE CÁLCULO", numerado=False)
        nomes = ", ".join(os.path.basename(a) for a in arqs)
        self.p(f"O cálculo é reprodutível: os módulos {nomes} (motor de cálculo) e {self._nome_gerador()} (este documento) "
               "são entregues junto com o relatório.")
        for a in arqs:
            par = self.doc.add_paragraph(style="Body Text")
            par.alignment = WD_ALIGN_PARAGRAPH.LEFT
            par.paragraph_format.space_before, par.paragraph_format.space_after = Pt(6), Pt(2)
            par.paragraph_format.keep_with_next = True
            rr = par.add_run(f"Arquivo: {os.path.basename(a)}")
            rr.bold, rr.font.size = True, Pt(9)
            with open(a, encoding="utf-8") as fh:
                for ln in fh.read().splitlines():
                    par = self.doc.add_paragraph(style="Body Text")
                    par.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    par.paragraph_format.space_after = Pt(0)
                    rr = par.add_run(ln.replace("\t", "    ") or " ")
                    rr.font.name, rr.font.size = "Courier New", Pt(7)

    @staticmethod
    def _nome_gerador():
        return _MODULO_CHAMADOR[0] or "relatorio_m2.py"

    def salvar(self, caminho):
        self.anexo_script()
        self._preencher_sumario()
        self.doc.save(caminho)


# ----------------------------------------------------------------------------- gráficos
def estilo_ax(ax):
    ax.set_facecolor("white")
    ax.grid(True, color="#E5E7EB", lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#9CA3AF")
    ax.tick_params(colors="#374151", labelsize=8)


def fig_secao(geo):
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    estilo_ax(ax)
    cores = {1: AZUL, 2: LARANJA}
    for k in geo["condutores"]:
        if k["tipo"] == "guarda":
            ax.plot(k["x"], k["y_med"], "v", color=CINZA, ms=8)
            ax.annotate(k["nome"], (k["x"], k["y_med"]), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=7)
        else:
            ax.plot(k["x"], k["y_med"], "o", color=cores[k["circuito"]], ms=8)
            ax.annotate(k["nome"], (k["x"], k["y_med"]), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=7)
    ax.axhline(0, color="#374151", lw=1.2)
    ax.set_xlabel("Posição horizontal x (m)", fontsize=9)
    ax.set_ylabel("Altura média no vão (m)", fontsize=9)
    ax.set_title("Seção transversal (alturas médias no vão)", fontsize=10)
    ax.set_ylim(bottom=-1)
    return fig


def fig_pi(nome, zs, yp):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.plot([0.5, 2], [3, 3], color="black", lw=1.5)
    ax.add_patch(plt.Rectangle((2, 2.7), 3.6, 0.6, fill=False, lw=1.8, ec=AZUL))
    ax.text(3.8, 3.0, f"Zs = {fc(zs, 2)} Ω", ha="center", va="center", fontsize=8)
    ax.plot([5.6, 9.5], [3, 3], color="black", lw=1.5)
    for x in (2.0, 9.0):
        ax.plot([x, x], [3, 2.2], color="black", lw=1.5)
        ax.add_patch(plt.Rectangle((x - 0.35, 1.5), 0.7, 0.7, fill=False, lw=1.8, ec=LARANJA))
        ax.plot([x, x], [1.5, 0.8], color="black", lw=1.5)
        ax.plot([x - 0.4, x + 0.4], [0.8, 0.8], color="black", lw=1.5)
        ax.plot([x - 0.25, x + 0.25], [0.65, 0.65], color="black", lw=1.2)
        ax.plot([x - 0.1, x + 0.1], [0.5, 0.5], color="black", lw=1.0)
    ax.text(2.0, 1.85, "Yp", ha="right", va="center", fontsize=8, color=LARANJA, fontweight="bold")
    ax.text(9.0, 1.85, "Yp", ha="right", va="center", fontsize=8, color=LARANJA, fontweight="bold")
    ax.text(5.0, 0.5, f"Yp = {fc(yp, 6)} S (em cada extremidade)", ha="center", fontsize=8)
    ax.text(0.4, 3.35, "Vs, Is", fontsize=8)
    ax.text(9.3, 3.35, "Vr, Ir", fontsize=8)
    ax.set_title(f"Modelo π equivalente – {nome}", fontsize=10)
    return fig


def varrer(calc, comp_km, f_hz, ptos=25, fps=None):
    """Regulação e perdas × carga (2D) e × (carga, fp) (3D) pelo modelo π do método matricial."""
    dc, sq = calc["dados"], calc["seq"]
    p_nom = dc["mva"] * 1000
    return dict(
        P=np.linspace(0.05, 1.6, ptos) * p_nom / 1000,
        reg=[cp.desempenho_pi(sq["Z1"], sq["C1"], comp_km, dc["un"], x * p_nom, dc.get("fp", 0.95), f_hz)["regulacao_pct"]
             for x in np.linspace(0.05, 1.6, ptos)],
        perd=[cp.desempenho_pi(sq["Z1"], sq["C1"], comp_km, dc["un"], x * p_nom, dc.get("fp", 0.95), f_hz)["perdas_pct"]
              for x in np.linspace(0.05, 1.6, ptos)])


def fig_reg2d(nome, calc, comp_km, f_hz):
    v = varrer(calc, comp_km, f_hz)
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    estilo_ax(ax)
    ax.plot(v["P"], v["reg"], color=AZUL, lw=2.2, label="Regulação de tensão")
    ax.set_xlabel("Potência aparente na carga (MVA)", fontsize=9)
    ax.set_ylabel("Regulação (%)", fontsize=9, color=AZUL)
    ax2 = ax.twinx()
    ax2.plot(v["P"], v["perd"], color=LARANJA, lw=2.2, ls="--", label="Perdas Joule")
    ax2.set_ylabel("Perdas (% da potência na fonte)", fontsize=9, color=LARANJA)
    ax2.spines["top"].set_visible(False)
    pn = calc["dados"]["mva"]
    ax.axvline(pn, color=CINZA, ls=":", lw=1.5)
    ax.annotate(f"Operação: {f(pn, 1)} MVA", (pn, ax.get_ylim()[0]), textcoords="offset points", xytext=(4, 6), fontsize=8)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8, frameon=False, loc="upper left")
    ax.set_title(f"{nome}: regulação e perdas × carga (modelo π)", fontsize=10)
    return fig


def fig_reg3d(nome, calc, comp_km, f_hz):
    dc, sq = calc["dados"], calc["seq"]
    Ps = np.linspace(0.1, 1.5, 18) * dc["mva"] * 1000
    fps = np.linspace(0.80, 1.0, 14)
    Z = np.array([[cp.desempenho_pi(sq["Z1"], sq["C1"], comp_km, dc["un"], p_, q, f_hz)["regulacao_pct"] for p_ in Ps] for q in fps])
    X, Y = np.meshgrid(Ps / 1000, fps)
    fig = plt.figure(figsize=(6.2, 4.4))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(X, Y, Z, cmap="Blues", edgecolor="none", alpha=0.95)
    ax.set_xlabel("Carga (MVA)", fontsize=8)
    ax.set_ylabel("Fator de potência", fontsize=8)
    ax.set_zlabel("Regulação (%)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.view_init(elev=24, azim=-58)
    ax.set_title(f"{nome}: regulação × carga × fator de potência", fontsize=10)
    return fig


# ----------------------------------------------------------------------------- relatório
def gerar(caminho, proj, geo, res, circs_dados, cfg, codigo="BK-LT-MC-0001", rev="R0", cabos_guarda=(),
          script_path=None):
    """proj: dict (cliente, nome, numero, data, revisao, resp); res: saída de mod2_calc.calcular."""
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    dup = len(res["circuitos"]) == 2
    titulo = "Memória de Cálculo – Parâmetros Elétricos"
    R = Rel(proj, titulo, codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS TÉCNICAS ADOTADAS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. DIMENSIONAMENTO E VERIFICAÇÕES", "7. QUANTITATIVOS",
               "8. RESULTADOS OBTIDOS", "9. CONCLUSÕES", "10. REFERÊNCIAS BIBLIOGRÁFICAS", "ANEXO A – SCRIPT"])
    comp, fhz, rho = res["comp_km"], res["f"], res["rho"]
    cs = res["circuitos"]

    # 1 ------------------------------------------------------------------ objetivo
    R.h1("OBJETIVO")
    R.p(f"Determinar os parâmetros elétricos de sequência positiva (R, L, C, G) {'de cada um dos dois circuitos' if dup else 'do circuito'} "
        f"da linha de transmissão {proj.get('nome') or ''}, a impedância característica, a constante de propagação, "
        "a potência natural (SIL) e o desempenho em regime permanente (tensão e corrente na fonte, regulação e perdas), "
        "representando a linha pelo modelo π equivalente.")
    if dup:
        R.p("Por haver dois circuitos na mesma estrutura, o cálculo considera o acoplamento eletromagnético e eletrostático "
            "entre eles (impedâncias e capacitâncias mútuas), além do cálculo isolado de cada circuito pelo método da planilha CELT2-IPOG.")
    R.p("Este documento não cobre: campo elétrico e magnético no solo, efeito corona, rádio interferência, ruído audível, "
        "coordenação de isolamento, ampacidade térmica detalhada e estudos de transitórios, tratados nos demais módulos.", "Escopo excluído:")

    # 2 ------------------------------------------------------------------ documentos
    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos do projeto", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["CELT2-IPOG", "Planilha de cálculo elétrico de LTs (circuito simples) – fornecida pelo cliente interno", "—", "—"],
        ["LINHA DE TRANSMISSÃO 4", "Planilha de cabos (catálogo importado para o banco do software)", "—", "—"]],
        [3.5, 8.0, 1.5, 3.0])
    R.p("DADO NÃO INFORMADO — códigos, revisões e datas de desenhos de estruturas e de especificação do cliente não foram fornecidos.",)

    # 3 ------------------------------------------------------------------ normas
    R.h1("NORMAS TÉCNICAS ADOTADAS")
    R.lista(["ABNT NBR 5422 – Projeto de linhas aéreas de transmissão de energia elétrica (edição a confirmar na edição vigente)."])
    R.tabela("Aplicação das normas e referências", ["Documento", "Onde é aplicado", "Item/capítulo"], [
        ["ABNT NBR 5422", "Premissas gerais de projeto (altura média no vão = altura na estrutura − 2/3 da flecha)", "a confirmar na edição vigente"],
        ["Carson (1926)", "Impedância série com retorno por terra (Eq. 9 e 10)", "método clássico; ver Seção 4"],
        ["Maxwell / imagens", "Coeficientes de potencial e capacitâncias (Eq. 11)", "Seção 4"]],
        [3.5, 8.0, 4.5])
    R.p("NBR 5422 não fornece as equações de parâmetros: elas vêm da teoria clássica (Seção 4 e Seção 10). "
        "A citação de item específico da norma fica a confirmar.", "PREMISSA —")

    # 4 ------------------------------------------------------------------ metodologia
    R.h1("METODOLOGIA DE CÁLCULO")
    R.h2("Parâmetros de sequência positiva – método CELT2 (referência)")
    R.p("Verifica-se a resistência, a indutância e a capacitância por fase de um circuito simples idealmente transposto, "
        "com cabos equivalentes de feixe. Base: planilha CELT2-IPOG, aba Calc. Retorno por terra e efeito dos cabos guarda são desprezados.")
    R.p("Base teórica: Stevenson, Elementos de Análise de Sistemas de Potência; Fuchs, Transmissão de Energia Elétrica; "
        "Checa, Líneas de Transporte de Energía (fonte e página a confirmar na edição do acervo).")
    R.eq(msub(mi("D"), mu("eq")) + mu("=") + mrad(mu("3"), msub(mi("D"), mu("ab")) + msub(mi("D"), mu("bc")) + msub(mi("D"), mu("ca"))))
    R.eq(mi("L") + mu("=") + mu("2·") + msup(mu("10"), mu("−7")) + mu("·") +
         mu("ln") + mpar(mfrac(msub(mi("D"), mu("eq")), msub(mi("D"), mi("s")))) + mu("·1000"))
    R.eq(mi("C") + mu("=") + mfrac(mu("2") + mi("π") + mi("ε"), mu("ln") + mpar(mfrac(mu("2") + msub(mi("D"), mu("eq")), mi("d")))) + mu("·1000"))
    R.simbolos([("Dab, Dbc, Dca", "distâncias entre fases (altura média)", "m"), ("Deq", "distância média geométrica", "m"),
                ("Ds", "raio médio geométrico equivalente do feixe", "m"), ("d", "diâmetro equivalente do feixe", "m"),
                ("ε", "permissividade do meio (εr·10⁻⁹/36π)", "F/m"), ("L, C", "indutância e capacitância por fase", "H/km, F/km")])
    R.p("Fluxo: (1) coordenadas × alturas médias → (2) Dab, Dbc, Dca → (3) Deq → (4) L, C → (5) ZL, YL → (6) Zo, γ → (7) modelo π → "
        "(8) desempenho. Limitações: sem retorno por terra, sem cabos guarda, linha idealmente transposta, uma só linha.")
    R.p("não há limite normativo para L e C; a verificação é de coerência com a planilha CELT2 (diferença < 0,01 %).", "Critério:")

    R.h2("Modelo π equivalente da linha longa")
    R.p("Representa a linha de comprimento l por um quadripolo exato (inclui efeito distribuído de R, L, C, G), com impedância série "
        "Zs e duas admitâncias em derivação Yp, uma em cada extremidade. É a forma exigida para estudos de fluxo de potência, curto-circuito "
        "e transitórios eletromecânicos. Base: planilha CELT2-IPOG, abas PI-calc e Circuito PI.")
    R.eq(msub(mi("Z"), mi("o")) + mu("=") + msqrt(mfrac(msub(mi("Z"), mi("L")), msub(mi("Y"), mi("L")))) + mu(" ;  ") + mi("γ") + mu("=") +
         msqrt(msub(mi("Z"), mi("L")) + msub(mi("Y"), mi("L"))))
    R.eq(msub(mi("Z"), mi("s")) + mu("=") + msub(mi("Z"), mi("o")) + mu("·senh") + mpar(mi("γ") + mi("l")))
    R.eq(msub(mi("Y"), mi("p")) + mu("=") + mfrac(mu("1"), msub(mi("Z"), mi("o"))) + mu("·tanh") + mpar(mfrac(mi("γ") + mi("l"), mu("2"))))
    R.eq(mi("A") + mu("=") + mi("D") + mu("=") + mu("1+") + msub(mi("Z"), mi("s")) + msub(mi("Y"), mi("p")) + mu(" ;  ") + mi("B") + mu("=") +
         msub(mi("Z"), mi("s")) + mu(" ;  ") + mi("C") + mu("=") + msub(mi("Y"), mi("p")) + mpar(mu("2+") + msub(mi("Z"), mi("s")) + msub(mi("Y"), mi("p"))))
    R.simbolos([("ZL = R + jωL", "impedância série por km", "Ω/km"), ("YL = G + jωC", "admitância em derivação por km", "S/km"),
                ("Zo", "impedância característica", "Ω"), ("γ = α + jβ", "constante de propagação", "1/km"), ("l", "comprimento da linha", "km"),
                ("Zs", "impedância série do modelo π", "Ω"), ("Yp", "admitância em derivação de cada extremidade", "S"),
                ("A, B, C, D", "constantes do quadripolo", "—")])
    R.p("Fluxo: Zo e γ → Zs e Yp → ABCD → tensão e corrente na fonte para a carga dada → regulação e perdas. "
        "Premissas: parâmetros uniformes, regime senoidal permanente, carga trifásica equilibrada. Para l ≲ 80 km o modelo nominal "
        "(Zs = ZL·l; Yp = YL·l/2) é uma aproximação; o relatório apresenta os dois para comparação.")
    R.p("o modelo π deve reproduzir a tensão da fonte da linha longa exata (diferença < 10⁻⁶ kV); limites de regulação e perdas "
        "dependem do critério do cliente.", "Critério:")

    R.h2("Acoplamento entre circuitos – método matricial" if dup else "Verificação por método matricial (Carson e Maxwell)")
    R.p("Em linha com dois circuitos (ou para considerar retorno por terra e cabos guarda), a CELT2 não se aplica diretamente. "
        "Monta-se a matriz completa de impedâncias (equações de Carson) e a de coeficientes de potencial (Maxwell, método das imagens); "
        "os cabos guarda, aterrados em todas as estruturas, são eliminados por redução de Kron; aplica-se a transformação em componentes simétricas.")
    R.eq(msub(mi("Z"), mi("ii")) + mu("=") + msub(mi("R"), mi("i")) + mu("+j") + mfrac(mi("ω") + msub(mi("μ"), mu("0")), mu("2") + mi("π")) + mu("ln") +
         mpar(mfrac(mu("2") + mpar(msub(mi("h"), mi("i")) + mu("+") + mi("p")), msub(mi("Ds"), mi("i")))))
    R.eq(msub(mi("Z"), mi("ij")) + mu("=j") + mfrac(mi("ω") + msub(mi("μ"), mu("0")), mu("2") + mi("π")) + mu("ln") +
         mpar(mfrac(msqrt(msup(mpar(msub(mi("h"), mi("i")) + mu("+") + msub(mi("h"), mi("j")) + mu("+2") + mi("p")), mu("2")) + msup(msub(mi("x"), mi("ij")), mu("2"))),
                    msub(mi("d"), mi("ij")))))
    R.eq(msub(mi("P"), mi("ii")) + mu("=") + mfrac(mu("1"), mu("2") + mi("π") + msub(mi("ε"), mu("0"))) + mu("ln") + mpar(mfrac(mu("2") + msub(mi("h"), mi("i")), msub(mi("r"), mu("eq,") + mi("i")))) +
         mu(" ;  ") + msub(mi("P"), mi("ij")) + mu("=") + mfrac(mu("1"), mu("2") + mi("π") + msub(mi("ε"), mu("0"))) + mu("ln") + mpar(mfrac(msub(mi("D'"), mi("ij")), msub(mi("d"), mi("ij")))) +
         mu(" ;  ") + mi("C") + mu("=") + msup(mi("P"), mu("−1")))
    R.eq(msub(mi("Z"), mu("red")) + mu("=") + msub(mi("Z"), mu("pp")) + mu("−") + msub(mi("Z"), mu("pg")) + msup(msub(mi("Z"), mu("gg")), mu("−1")) + msub(mi("Z"), mu("gp")) +
         mu(" ;  ") + msub(mi("Z"), mu("seq")) + mu("=") + msup(mi("T"), mu("−1")) + msub(mi("Z"), mu("fase")) + mi("T"))
    R.simbolos([("p = √(ρ/jωμ0)", "profundidade complexa de penetração no solo (ρ = resistividade)", "m"),
                ("hi", "altura média do condutor i", "m"), ("xij, dij", "distância horizontal e distância entre condutores", "m"),
                ("D'ij", "distância entre o condutor i e a imagem de j", "m"), ("req", "raio equivalente do feixe", "m"),
                ("T", "matriz de componentes simétricas (a = 1∠120°)", "—")])
    R.p("Fluxo: coordenadas → Z, P → redução dos guardas → C = P⁻¹ → sequências (0, 1, 2) → Z1, C1 por circuito; Z0, Z0m, Z1m entre circuitos "
        "→ modelo π de cada circuito com Z1 e C1 próprios. Limitações: aproximação de Carson por profundidade complexa (válida em 60 Hz para h ≪ p); "
        "solo homogêneo; tensões induzidas por circuito vizinho desligado não fazem parte deste item.")
    R.p(f"coerência entre os dois métodos (diferença de L da ordem de 1 %); o acoplamento é reportado, sem limite normativo.", "Critério:")

    # 5 ------------------------------------------------------------------ dados
    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    R.h2("Dados do projeto")
    R.tabela("Dados do projeto e do sistema", ["Parâmetro", "Valor", "Unidade", "Base"], [
        ["Cliente", proj.get("cliente") or "DADO NÃO INFORMADO", "—", "Fornecido"],
        ["Obra", proj.get("nome") or "DADO NÃO INFORMADO", "—", "Fornecido"],
        ["Comprimento da linha", f(comp, 2), "km", "Fornecido"],
        ["Frequência", f(fhz, 0), "Hz", "Fornecido"],
        ["Resistividade do solo", f(rho, 0), "Ω·m", "PREMISSA (Módulo 6 não preenchido)"],
        ["Circuitos", str(len(cs)), "—", "Fornecido"]],
        [5.5, 4.5, 2.0, 4.0])
    cab_c = ["Parâmetro"] + [f"Circuito {c}" for c in cs]
    lin = [["Nome / alimentação"] + [cs[c]["dados"]["nome"] for c in cs],
           ["Tensão nominal (kV)"] + [f(cs[c]["dados"]["un"], 1) for c in cs],
           ["Tensão máxima operativa (kV)"] + [f(cs[c]["dados"]["umax"], 1) for c in cs],
           ["Potência na carga (MVA)"] + [f(cs[c]["dados"]["mva"], 2) for c in cs],
           ["Fator de potência"] + [f(cs[c]["dados"]["fp"], 3) for c in cs],
           ["Corrente nominal (A)"] + [f(cs[c]["i_nom"], 1) for c in cs],
           ["Estado do circuito"] + [cs[c]["dados"]["status"] for c in cs],
           ["Condutor"] + [cs[c]["cabo"]["codigo"] for c in cs],
           ["Cabos por fase"] + [str(cs[c]["cabo"]["n"]) for c in cs],
           ["Espaçamento entre subcondutores (mm)"] + [f(cs[c]["cabo"]["a"] * 1000, 0) if cs[c]["cabo"]["n"] > 1 else "—" for c in cs]]
    R.tabela("Dados elétricos por circuito", cab_c, lin, fonte="Módulo 1 – aba Circuitos")
    R.h2("Geometria e características dos cabos")
    R.figura(fig_secao(geo), "Seção transversal da estrutura com alturas médias no vão",
             "A Figura 1 mostra as posições adotadas nos cálculos. Altura média = altura na estrutura − 2/3 da flecha (premissa de projeto).")
    linhas = [[k["nome"], f(k["x"], 2), f(k["y"], 2), f(k["y_med"], 2)] for k in geo["condutores"]]
    R.tabela("Coordenadas dos condutores", ["Condutor", "x (m)", "Altura na estrutura (m)", "Altura média (m)"], linhas, fonte="Módulo 2 – Geometria")
    cab_k = ["Parâmetro"] + [f"Condutor C{c}" for c in cs]
    lk = [["Código"] + [cs[c]["cabo"]["codigo"] for c in cs],
          ["Diâmetro (mm)"] + [f(cs[c]["cabo"]["d"] * 1000, 2) for c in cs],
          ["Seção (mm²)"] + [f(cs[c]["cabo"]["secao"] or 0, 1) for c in cs],
          ["Ds do cabo (mm)"] + [f(cs[c]["cabo"]["ds"] * 1000, 2) for c in cs],
          ["Base de Ds"] + [cs[c]["cabo"]["base_ds"] for c in cs],
          ["R usado (Ω/km por fase)"] + [f(cs[c]["cabo"]["R"], 4) for c in cs],
          ["Base de R"] + [cs[c]["cabo"]["base_r"] for c in cs],
          ["Ds equivalente do feixe (mm)"] + [f(cs[c]["cabo"]["ds_eq"] * 1000, 2) for c in cs],
          ["Diâmetro equivalente (mm)"] + [f(cs[c]["cabo"]["d_eq"] * 1000, 2) for c in cs]]
    R.tabela("Propriedades elétricas dos condutores", cab_k, lk, fonte="Catálogo de cabos (banco de dados)")
    if cabos_guarda:
        R.tabela("Cabos guarda", ["Cabo", "Diâmetro (mm)", "R_cc 20 °C (Ω/km)"],
                 [[g.get("codigo"), f(g.get("diametro_mm") or 0, 2), f(g.get("r_cc_20") or 0, 3)] for g in cabos_guarda],
                 fonte="Catálogo de cabos; aterrados em todas as estruturas (PREMISSA)")
    R.h2("Dados não informados e premissas")
    for n in res["notas"]:
        rot, _, resto = n.partition(" — ")
        R.p(resto, rot + " —")
    R.p("Resistividade do solo adotada " + f(rho, 0) + " Ω·m; cabos guarda aterrados em todas as torres; carga trifásica equilibrada; "
        "linha idealmente transposta no método CELT2; sem transposição no método matricial.", "PREMISSA —")
    R.p("o arquivo-modelo DOCUMENTO_PADRAO_BK.docx não foi fornecido; capa, cabeçalho e rodapé seguem a especificação textual, "
        "com logos, razão social/CNPJ e texto institucional a preencher.", "NECESSITA VALIDAÇÃO TÉCNICA —")

    # 6 ------------------------------------------------------------------ cálculos
    R.h1("DIMENSIONAMENTO E VERIFICAÇÕES")
    resumo = []
    for c, v in cs.items():
        e, ce, mt, d = v["cabo"], v["celt2"], v["matricial"], v["dados"]
        pi = ce["pi"]
        R.h2(f"Circuito {c} – {d['nome']}")
        R.p("Determinar L, C, Zo, γ, SIL, modelo π e o desempenho do circuito.", "Objetivo:")
        R.tabela(f"Entradas do circuito {c}", ["Parâmetro", "Valor", "Unidade", "Base"], [
            ["Dab / Dbc / Dca", f"{f(v['Dab'], 3)} / {f(v['Dbc'], 3)} / {f(v['Dca'], 3)}", "m", "Calculado (geometria)"],
            ["Ds (feixe)", f(e["ds_eq"] * 1000, 3), "mm", e["base_ds"]],
            ["d (feixe)", f(e["d_eq"] * 1000, 3), "mm", "Catálogo"],
            ["R", f(e["R"], 4), "Ω/km", e["base_r"]],
            ["l", f(comp, 2), "km", "Fornecido"], ["f", f(fhz, 0), "Hz", "Fornecido"],
            ["Tensão nominal na fonte (fixa)", f(d["un"], 1), "kV", "Fornecido"], ["Carga", f(d["mva"], 2) + " MVA, fp " + f(d["fp"], 2), "—", "Fornecido"]],
            [4.0, 5.0, 2.0, 5.0])
        w = 2 * math.pi * fhz
        R.p(f"Deq = ({f(v['Dab'], 3)}·{f(v['Dbc'], 3)}·{f(v['Dca'], 3)})^(1/3) = {f(ce['Deq'], 4)} m.", "Substituição (Eq. 1):")
        R.p(f"L = 2·10⁻⁷·ln({f(ce['Deq'], 4)}/{f(e['ds_eq'], 5)})·1000 = {f(ce['L_mH_km'], 4)} mH/km.", "Substituição (Eq. 2):")
        R.p(f"C = 2π·{f(cp.EPS0 * 1e12, 4)}·10⁻¹²/ln(2·{f(ce['Deq'], 4)}/{f(e['d_eq'], 5)})·1000 = {f(ce['C_nF_km'], 4)} nF/km.", "Substituição (Eq. 3):")
        R.p(f"ZL = {f(e['R'], 4)} + j{f(w, 2)}·{f(ce['L_mH_km'] / 1000, 7)} = {fc(ce['ZL'], 4)} Ω/km;  "
            f"YL = j{f(w, 2)}·{f(ce['C_nF_km'], 4)}·10⁻⁹ = j{f(ce['YL'].imag * 1e6, 3)} µS/km.")
        R.p(f"Zo = {fp(ce['Zo'])} Ω;  γ = {f(ce['alfa_km'], 6)} + j{f(ce['beta_km'], 6)} km⁻¹;  Ro = √(L/C) = {f(ce['Ro'], 2)} Ω;  "
            f"v = {f(ce['v_ms'] / 1e8, 3)}·10⁸ m/s;  λ = {f(ce['lambda_km'], 0)} km.", "Resultado (Eq. 5):")
        R.h2(f"Modelo π – circuito {c}")
        gl = ce["gl"]
        R.p(f"γl = {f(gl.real, 5)} + j{f(gl.imag, 5)};  Zs = Zo·senh(γl) = {fc(pi['Zs'], 3)} Ω = {fp(pi['Zs'])} Ω;  "
            f"Yp = tanh(γl/2)/Zo = {fc(pi['Yp'], 7)} S.", "Substituição (Eq. 6 e 7):")
        R.tabela(f"Modelo π do circuito {c}", ["Grandeza", "Modelo π exato", "Modelo nominal", "Unidade"], [
            ["Zs", fc(pi["Zs"], 3), fc(pi["Zs_nominal"], 3), "Ω"],
            ["Yp (cada extremidade)", fc(pi["Yp"], 7), fc(pi["Yp_nominal"], 7), "S"],
            ["Yp total (2·Yp)", fc(pi["Y_total"], 7), fc(2 * pi["Yp_nominal"], 7), "S"],
            ["A = D", fc(pi["A"], 5), "—", "—"], ["B", fc(pi["B"], 3), "—", "Ω"], ["C", fc(pi["C"], 7), "—", "S"]],
            [4.0, 4.5, 4.5, 2.0], fonte="Cálculo próprio (método CELT2, abas PI-calc / Circuito PI)")
        R.figura(fig_pi(f"circuito {c}", pi["Zs"], pi["Yp"]), f"Esquema do modelo π do circuito {c}",
                 f"A Figura mostra o equivalente π: Zs em série e Yp em cada extremidade. A susceptância total 2·Im(Yp) = "
                 f"{f(pi['Y_total'].imag * 1e6, 1)} µS, equivalente a {f(pi['Y_total'].imag / w * 1e6, 3)} µF de capacitância total da linha.",
                 larg_cm=13.0)
        if "carga" in ce:
            k = ce["carga"]
            R.h2(f"Desempenho em regime permanente – circuito {c}")
            R.tabela(f"Fonte e carga do circuito {c} (linha longa exata)", ["Grandeza", "Fonte", "Carga", "Unidade"], [
                ["Tensão de linha", f"{f(k['Vo_kV'], 3)} ∠ 0,00°", f"{f(k['Vc_kV'], 3)} ∠ {f(k['Vc_ang'], 2)}°", "kV"],
                ["Corrente", f"{f(k['Io_A'], 2)} ∠ {f(k['Io_ang'], 2)}°", f"{f(k['Ic_abs'], 2)} ∠ {f(k['Ic_ang'], 2)}°", "A"],
                ["Potência ativa", f(k["Po_kW"], 2), f(k["Pc_kW"], 2), "kW"],
                ["Potência aparente", f(k["So_kVA"], 2), f(k["S_kVA"], 2), "kVA"]], [4.0, 4.5, 4.5, 2.0])
            R.p(f"Regulação = (V_vazio − V_carga)/V_carga = ({f(k['V_vazio_kV'], 3)} − {f(k['Vc_kV'], 3)})/{f(k['Vc_kV'], 3)} = {f(k['regulacao_pct'], 3)} %.  "
                f"Perdas = {f(k['Po_kW'], 2)} − {f(k['Pc_kW'], 2)} = {f(k['perdas_kW'], 2)} kW = {f(k['perdas_pct'], 3)} % da potência na fonte.  "
                f"SIL = V²/Ro = {f(k['SIL_kW'] / 1000, 2)} MW;  P/SIL = {f(k['Pc_SIL'], 3)}.", "Resultado:")
            R.p(f"a tensão na carga calculada, aplicada ao modelo π, reproduz a tensão fixa da fonte: {f(k['Vo_pi_kV'], 4)} kV (π) × {f(k['Vo_kV'], 4)} kV (fonte).",
                "Verificação:")
        R.h2(f"Método matricial – circuito {c}")
        sq = v["seq"]
        R.tabela(f"Sequências do circuito {c} (com retorno por terra e cabos guarda)", ["Grandeza", "Valor", "Unidade"], [
            ["Z1 (sequência positiva)", fc(sq["Z1"], 4), "Ω/km"], ["Z0 (sequência zero)", fc(sq["Z0"], 4), "Ω/km"],
            ["C1", f(sq["C1"] * 1e9, 4), "nF/km"], ["C0", f(sq["C0"] * 1e9, 4), "nF/km"],
            ["L1 = Im(Z1)/ω", f(sq["Z1"].imag / w * 1e3, 4), "mH/km"],
            ["Assimetria interna de Z (sem transposição)", f(sq["assim_Z"] * 100, 2), "%"],
            ["Assimetria interna de C (sem transposição)", f(sq["assim_C"] * 100, 2), "%"]], [6.5, 5.0, 3.0])
        pm = mt["pi"]
        R.tabela(f"Modelo π do circuito {c} com os parâmetros do método matricial", ["Grandeza", "Valor", "Unidade"], [
            ["Zs", fc(pm["Zs"], 3), "Ω"], ["Yp (cada extremidade)", fc(pm["Yp"], 7), "S"],
            ["Zo", fp(mt["Zo"]), "Ω"], ["Tensão na fonte (fixa)", f(mt["Vo_kV"], 3), "kV"], ["Tensão na carga (calculada)", f(mt["Vc_kV"], 3), "kV"],
            ["Regulação", f(mt["regulacao_pct"], 3), "%"], ["Perdas", f(mt["perdas_kW"], 2) + f"  ({f(mt['perdas_pct'], 3)} %)", "kW"],
            ["P/SIL", f(mt["Pc_SIL"], 3), "—"]], [6.5, 5.0, 3.0])
        dL = (mt["L_mH_km"] - ce["L_mH_km"]) / ce["L_mH_km"] * 100
        dC = (mt["C_nF_km"] - ce["C_nF_km"]) / ce["C_nF_km"] * 100
        R.p(f"Diferença matricial × CELT2: L {f(dL, 2)} %, C {f(dC, 2)} % (o retorno por terra, os cabos guarda e a falta de transposição explicam a diferença).",
            "Comparação:")
        if "carga" in ce:
            R.figura(fig_reg2d(f"Circuito {c}", v, comp, fhz), f"Regulação e perdas × carga – circuito {c}",
                     "A curva mostra a sensibilidade do desempenho à carga; o ponto de operação está marcado.")
            R.figura(fig_reg3d(f"Circuito {c}", v, comp, fhz), f"Regulação × carga × fator de potência – circuito {c} (3D)",
                     "A superfície mostra o efeito combinado de carga e fator de potência; a regulação cresce com a carga e diminui com fp mais próximo de 1.")
        R.p("método sem tensões induzidas e com carga equilibrada.", "Limitações:")
        resumo.append((c, v))

    if dup:
        R.h2("Interferência (acoplamento) entre os circuitos")
        m = res["mutua"]
        R.tabela("Impedâncias e capacitâncias mútuas entre circuitos", ["Grandeza", "Valor", "Unidade"], [
            ["Z1m (mútua de sequência positiva)", fc(m["Z1m"], 5), "Ω/km"], ["Z0m (mútua de sequência zero)", fc(m["Z0m"], 5), "Ω/km"],
            ["Z0m/Z0 (acoplamento de seq. zero)", f(m["acoplamento_Z0"] * 100, 1), "%"],
            ["Z1m/√(Z1·Z1') (acoplamento de seq. positiva)", f(m["acoplamento_Z1"] * 100, 2), "%"],
            ["C1m (capacitância mútua seq. +)", f(m["C1m"] * 1e9, 4), "nF/km"], ["C0m (capacitância mútua seq. 0)", f(m["C0m"] * 1e9, 4), "nF/km"]],
            [7.0, 4.5, 2.5])
        R.p(f"O acoplamento de sequência positiva é pequeno ({f(m['acoplamento_Z1'] * 100, 2)} %), portanto L1 e C1 de cada circuito mudam pouco; "
            f"o acoplamento de sequência zero é elevado ({f(m['acoplamento_Z0'] * 100, 1)} %), relevante para curto-circuito fase-terra, proteção e indução.",
            "Comentário:")
        R.p("estes valores de sequência zero e mútuas entram em estudos de curto-circuito e indução (Módulos 9 e 14); a verificação do efeito não é feita neste documento.",
            "PENDENTE —")

    # 7 ------------------------------------------------------------------ quantitativos
    R.h1("QUANTITATIVOS")
    R.p("Não aplicável a este documento.")

    # 8 ------------------------------------------------------------------ resultados
    R.h1("RESULTADOS OBTIDOS")
    linhas = []
    for c, v in resumo:
        ce, d = v["celt2"], v["dados"]
        k = ce.get("carga")
        if v["amp"]:
            st_ = "ATENDE" if v["i_nom"] <= v["amp"] else "NÃO ATENDE"
            linhas.append([f"C{c}: corrente nominal × ampacidade", f"Ampacidade ({v['amp_base']})", f"{f(v['i_nom'], 1)} A", f"{f(v['amp'], 0)} A", st_])
        else:
            linhas.append([f"C{c}: corrente nominal × ampacidade", "Ampacidade", f"{f(v['i_nom'], 1)} A", "não informada", "PENDENTE"])
        if v["densidade_A_mm2"] is not None:
            linhas.append([f"C{c}: densidade de corrente", "Faixa recomendada pela CELT2 (referência, não normativa)",
                           f"{f(v['densidade_A_mm2'], 3)} A/mm²", "0,6 a 0,8 A/mm²",
                           "ATENDE" if 0.6 <= v["densidade_A_mm2"] <= 0.8 else "NÃO ATENDE"])
        if k:
            linhas.append([f"C{c}: regulação de tensão", "Critério do cliente (não informado)", f"{f(k['regulacao_pct'], 3)} %", "não informado", "PENDENTE"])
            linhas.append([f"C{c}: perdas Joule", "Critério do cliente (não informado)", f"{f(k['perdas_pct'], 3)} %", "não informado", "PENDENTE"])
            linhas.append([f"C{c}: P/SIL", "Informativo", f(k["Pc_SIL"], 3), "—", "PENDENTE"])
    R.tabela("Resumo das verificações", ["Verificação", "Norma/critério", "Valor calculado", "Limite", "Status"], linhas, [4.5, 4.5, 2.7, 2.5, 2.0])
    R.p("a densidade de corrente usa a seção total do feixe; a faixa 0,6–0,8 A/mm² é a indicada na planilha CELT2 e deve ser confirmada pelo critério do cliente.",
        "NECESSITA VALIDAÇÃO TÉCNICA —")
    cab = ["Parâmetro (seq. positiva)"] + [f"Circuito {c}" for c in cs]
    tb = [["R (Ω/km)"] + [f(v["cabo"]["R"], 4) for v in cs.values()],
          ["L (mH/km) – CELT2"] + [f(v["celt2"]["L_mH_km"], 4) for v in cs.values()],
          ["C (nF/km) – CELT2"] + [f(v["celt2"]["C_nF_km"], 4) for v in cs.values()],
          ["Zo (Ω)"] + [fp(v["celt2"]["Zo"]) for v in cs.values()],
          ["Zs do modelo π (Ω)"] + [fc(v["celt2"]["pi"]["Zs"], 3) for v in cs.values()],
          ["Yp do modelo π (S)"] + [fc(v["celt2"]["pi"]["Yp"], 7) for v in cs.values()],
          ["Zs do modelo π – matricial (Ω)"] + [fc(v["matricial"]["pi"]["Zs"], 3) for v in cs.values()],
          ["Yp do modelo π – matricial (S)"] + [fc(v["matricial"]["pi"]["Yp"], 7) for v in cs.values()],
          ["SIL (MW)"] + [f(v["celt2"]["carga"]["SIL_kW"] / 1000, 2) if "carga" in v["celt2"] else "—" for v in cs.values()]]
    R.tabela("Parâmetros finais e modelo π por circuito", cab, tb)

    # 9 ------------------------------------------------------------------ conclusões
    R.h1("CONCLUSÕES")
    R.p("Resultados calculados:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    itens = []
    for c, v in resumo:
        ce = v["celt2"]
        itens.append(f"Circuito {c}: L = {f(ce['L_mH_km'], 4)} mH/km, C = {f(ce['C_nF_km'], 3)} nF/km, Zo = {fp(ce['Zo'])} Ω; "
                     f"modelo π com Zs = {fc(ce['pi']['Zs'], 2)} Ω e Yp = {fc(ce['pi']['Yp'], 6)} S.")
        if "carga" in ce:
            itens.append(f"Circuito {c}: regulação {f(ce['carga']['regulacao_pct'], 2)} % e perdas {f(ce['carga']['perdas_pct'], 2)} % na carga informada.")
    if dup:
        itens.append(f"Acoplamento entre circuitos: {f(res['mutua']['acoplamento_Z1'] * 100, 2)} % (seq. +) e {f(res['mutua']['acoplamento_Z0'] * 100, 1)} % (seq. 0).")
    R.lista(itens)
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Cadastrar o RMG de cada cabo no catálogo (hoje usa-se Ds = 0,7788·r).",
             "Informar os limites de regulação e perdas do cliente para fechar as verificações PENDENTES.",
             "Confirmar a resistividade do solo no Módulo 6.", "Validar o layout contra o arquivo-modelo DOCUMENTO_PADRAO_BK.docx."])

    # 10 ----------------------------------------------------------------- referências
    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["ABNT NBR 5422 – Projeto de linhas aéreas de transmissão de energia elétrica (edição a confirmar).",
             "CARSON, J. R. Wave propagation in overhead wires with ground return. Bell System Technical Journal, v. 5, 1926.",
             "CHECA, L. M. Líneas de transporte de energía. Marcombo (acervo do projeto; edição e páginas a confirmar).",
             "Cálculos Elétricos de Linhas de Transmissão (acervo do projeto; autor, edição e páginas a confirmar).",
             "Teoria das Linhas de Transmissão (acervo do projeto; autor, edição e páginas a confirmar).",
             "Planilha CELT2-IPOG – cálculo elétrico de LTs (fornecida pelo cliente interno)."])

    R.salvar(caminho)
    return caminho


def docx_para_pdf(caminho_docx):
    """Converte o .docx em PDF (LibreOffice). Retorna os bytes do PDF ou None se não houver conversor."""
    import shutil
    import subprocess
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        return None
    pasta = os.path.dirname(caminho_docx)
    try:
        subprocess.run([exe, "--headless", "--convert-to", "pdf", "--outdir", pasta, caminho_docx],
                       check=True, capture_output=True, timeout=180)
        with open(os.path.splitext(caminho_docx)[0] + ".pdf", "rb") as fh:
            return fh.read()
    except Exception:
        return None
