"""
Relatório genérico (padrão BK) para módulos cujo cálculo ainda não foi implementado (1, 5, 8 a 16) e para o Módulo 1.
Registra o escopo, a norma prevista, os dados de entrada informados e os itens PENDENTES, sem inventar resultados.
"""
import datetime as dt

from relatorio_m2 import Rel


def _fmt(v):
    if v is None or v == "":
        return "DADO NÃO INFORMADO"
    if isinstance(v, bool):
        return "sim" if v else "não"
    if isinstance(v, float):
        return f"{v:.6g}".replace(".", ",")
    if isinstance(v, (list, tuple)):
        return ", ".join(_fmt(x) for x in v) if v and not isinstance(v[0], dict) else f"{len(v)} registro(s)"
    if isinstance(v, dict):
        return f"{len(v)} item(ns)"
    if hasattr(v, "strftime"):
        return v.strftime("%d/%m/%Y")
    return str(v)


def gerar(caminho, proj, num_mod, titulo, norma, secoes, implementado=False, codigo="BK-LT-MC", rev="R0"):
    """secoes: lista de (título, [(parâmetro, valor), ...])."""
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    R = Rel(proj, titulo, codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS TÉCNICAS ADOTADAS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. DIMENSIONAMENTO E VERIFICAÇÕES", "7. QUANTITATIVOS",
               "8. RESULTADOS OBTIDOS", "9. CONCLUSÕES", "10. REFERÊNCIAS BIBLIOGRÁFICAS"])
    R.h1("OBJETIVO")
    R.p(f"Registrar os dados de entrada do módulo \"{titulo}\" da linha de transmissão {proj.get('nome') or ''} e o escopo previsto de cálculo.")
    if not implementado:
        R.p("o cálculo deste módulo ainda não foi implementado no aplicativo; este documento não apresenta resultados.", "PENDENTE —")
    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"],
             [[proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]]], [3.5, 8.0, 1.5, 3.0])
    R.h1("NORMAS TÉCNICAS ADOTADAS")
    R.p("Normas previstas para este módulo: " + norma + ".")
    R.p("os itens específicos de cada norma serão citados quando o cálculo for implementado e conferido.", "PENDENTE —")
    R.h1("METODOLOGIA DE CÁLCULO")
    R.p("Metodologia ainda não definida neste aplicativo para este módulo." if not implementado else "Ver os relatórios dos módulos de cálculo correspondentes.")
    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    for tit, linhas in secoes:
        R.h2(tit)
        if linhas:
            R.tabela(tit, ["Parâmetro", "Valor"], [[a, _fmt(b)] for a, b in linhas], [8.0, 7.0])
        else:
            R.p("nenhum dado informado nesta seção.", "DADO NÃO INFORMADO —")
    R.p("os valores acima são os digitados no aplicativo e não foram validados contra documentos de projeto.", "NECESSITA VALIDAÇÃO TÉCNICA —")
    R.h1("DIMENSIONAMENTO E VERIFICAÇÕES")
    R.p("Sem cálculo implementado." if not implementado else "Não aplicável a este documento.", "PENDENTE —" if not implementado else None)
    R.h1("QUANTITATIVOS")
    R.p("Não aplicável a este documento.")
    R.h1("RESULTADOS OBTIDOS")
    R.tabela("Resumo das verificações", ["Verificação", "Norma/critério", "Valor", "Limite", "Status"],
             [["Cálculo do módulo", norma[:40], "não calculado", "—", "PENDENTE"]] if not implementado else
             [["Dados de entrada", "—", "registrados", "—", "ATENDE"]], [3.5, 4.0, 3.0, 2.5, 3.0])
    R.h1("CONCLUSÕES")
    R.p("Este documento registra apenas os dados de entrada informados." if not implementado else "Dados de entrada registrados.")
    R.p("Grau de confiança: não aplicável (sem cálculo). Faltam: implementação do cálculo do módulo, conferência das normas e validação dos dados de entrada.",
        "O que falta para eu informar com certeza:")
    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista([norma])
    R.salvar(caminho)
    return caminho
