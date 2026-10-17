"""Gerador do documento "Procedimentos para Estudos Elétricos" (padrão BK).

Uso:  python doc_procedimentos.py [pasta_saida]
Gera o .docx (equações editáveis no Word) e o PDF (equações em texto linear) com a metodologia manual, o exemplo resolvido e o
passo a passo de preenchimento no app para cada um dos 16 módulos.
"""
import datetime as dt
import os
import sys

import relatorio_m2 as rm
from relatorio_m2 import Rel, docx_para_pdf

import doc_proc_a as A
import doc_proc_b as B
import doc_proc_c as C
import doc_proc_d as D

CODIGO = "BK-LT-PR-0001"
TITULO = "Procedimentos para Estudos Elétricos"


def montar(caminho, rev="R0"):
    hoje = dt.date.today().strftime("%d/%m/%Y")
    proj = dict(cliente="BK Engenharia", nome="Procedimentos para Estudos Elétricos de LT", numero=CODIGO, revisao=rev, data_txt=hoje,
                resp="BK")
    R = Rel(proj, TITULO, CODIGO, rev, scripts=[])
    R.capa("Procedimento interno de engenharia", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", hoje, "", "", "")])
    R.sumario([])
    A.intro(R)
    A.m1(R)
    A.m2(R)
    A.m3(R)
    B.m4(R)
    B.m5(R)
    B.m6(R)
    B.m7(R)
    C.m8(R)
    C.m9(R)
    C.m10(R)
    C.m11(R)
    D.m12(R)
    D.m13(R)
    D.m14(R)
    D.m15(R)
    D.m16(R)
    D.final(R)
    R._toc = [t for t in R._toc if t[0] == 1]          # sumário só com os capítulos
    R.salvar(caminho)
    return caminho


def gerar(pasta):
    os.makedirs(pasta, exist_ok=True)
    rm.MODO_PDF = False
    docx = montar(os.path.join(pasta, "Procedimentos_Estudos_Eletricos_BK.docx"))
    rm.MODO_PDF = True
    pdf_src = montar(os.path.join(pasta, "_impressao.docx"))
    rm.MODO_PDF = False
    pdf = docx_para_pdf(pdf_src)
    if pdf:
        with open(os.path.join(pasta, "Procedimentos_Estudos_Eletricos_BK.pdf"), "wb") as fh:
            fh.write(pdf)
    for a in (pdf_src, os.path.splitext(pdf_src)[0] + ".pdf"):
        if os.path.exists(a):
            os.remove(a)
    return docx


if __name__ == "__main__":
    print(gerar(sys.argv[1] if len(sys.argv) > 1 else "."))
