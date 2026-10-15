"""
Relatório do Módulo 8 – Estudo de campos elétrico e magnético ao nível do solo, padrão BK.
Estrutura: objetivo, documentos, normas, metodologia (com equações), dados, resultados por ponto (2D e 3D), conclusões, referências.
"""
import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
from docx.enum.text import WD_ALIGN_PARAGRAPH

import calc_campos as cc
from relatorio_m2 import AZUL, CINZA, LARANJA, VERM, Rel, estilo_ax, f, mi, mu, mfrac, mpar, msqrt, msub, msup


def _st(ok):
    return "ATENDE" if ok else "NÃO ATENDE"


def fig_perfil(p, cen, semi):
    c = p["cenarios"][cen]
    fig, axs = plt.subplots(2, 1, figsize=(6.2, 5.6), sharex=True)
    for ax, k, ke, lim, un, tit in ((axs[0], "E", "E_est", p["lim_e"], "kV/m", "Campo elétrico"),
                                    (axs[1], "B", "B_est", p["lim_b"], "µT", "Densidade de fluxo magnético")):
        estilo_ax(ax)
        ax.plot(c["x"], c[k], color=AZUL, lw=2, label="Total (pior caso de defasagem)" if p["vizinhas"] else "LT em estudo")
        if p["vizinhas"]:
            ax.plot(c["x"], c[ke], color=CINZA, lw=1.2, ls="--", label="Somente LT em estudo")
        ax.axhline(lim, color=VERM, ls=":", lw=1.5, label=f"{p['publico']}: {lim:g} {un}")
        if semi:
            for s in (-semi, semi):
                ax.axvline(s, color=LARANJA, ls=":", lw=1)
        ax.set_ylabel(f"{tit} ({un})")
        ax.legend(fontsize=7, loc="upper right")
    axs[1].set_xlabel("Distância ao eixo da LT (m)")
    axs[0].set_title(f"{p['nome']} – cenário {cen} – h = {p['h_obs']:g} m", fontsize=10)
    return fig


def fig_3d(p, c):
    fig = plt.figure(figsize=(6.4, 3.4))
    for j, (g, un, tit) in enumerate((("E", "kV/m", "Campo elétrico"), ("B", "µT", "Fluxo magnético"))):
        ax = fig.add_subplot(1, 2, j + 1, projection="3d")
        s = c["s3d_" + g]
        X, Y = np.meshgrid(s["x"], s["y"])
        ax.plot_surface(X, Y, np.array(s["z"]), cmap="viridis", linewidth=0, antialiased=True)
        ax.set_xlabel("x (m)", fontsize=7)
        ax.set_ylabel("altura (m)", fontsize=7)
        ax.set_zlabel(un, fontsize=7)
        ax.set_title(tit, fontsize=9)
        ax.tick_params(labelsize=6)
    fig.tight_layout()
    return fig


def gerar(caminho, proj, e, r, d, resumo_pontos, codigo="BK-LT-MC-M8", rev="R0"):
    hoje = proj.get("data") or dt.date.today()
    proj = dict(proj, data_txt=hoje.strftime("%d/%m/%Y") if hasattr(hoje, "strftime") else str(hoje))
    R = Rel(proj, "Estudo de Campos Elétrico e Magnético", codigo, rev)
    R.capa(proj.get("nome") or "—", [("", "", "", "", "", ""), (rev.replace("R", ""), "EMISSÃO INICIAL", proj["data_txt"], "", "", "")])
    R.sumario(["1. OBJETIVO", "2. DOCUMENTOS DE REFERÊNCIA", "3. NORMAS TÉCNICAS ADOTADAS", "4. METODOLOGIA DE CÁLCULO",
               "5. DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS", "6. RESULTADOS OBTIDOS", "7. CONCLUSÕES", "8. REFERÊNCIAS BIBLIOGRÁFICAS"])
    semi = r.get("semi_faixa")

    R.h1("OBJETIVO")
    R.p("Determinar os campos elétrico (E) e magnético (B) de frequência industrial ao nível do solo (altura de referência de "
        f"{f(r['h_obs'], 1)} m) gerados pela linha de transmissão" + (" " + proj["nome"] if proj.get("nome") else "") + ", dentro e fora da faixa de servidão, "
        "incluindo a contribuição de linhas vizinhas cadastradas, e verificar os níveis de referência para exposição humana.")
    R.p("exposição de pessoas com marcapasso, correntes induzidas em estruturas metálicas, interferência em dutos e telecomunicações (Módulo 9) "
        "e rádio-interferência/ruído audível (Módulo 10).", "Escopo excluído:")

    R.h1("DOCUMENTOS DE REFERÊNCIA")
    R.tabela("Documentos de referência", ["Código", "Título", "Rev.", "Data"], [
        [proj.get("numero") or "DADO NÃO INFORMADO", proj.get("nome") or "—", proj.get("revisao") or "—", proj["data_txt"]],
        ["Diretrizes de projeto básico", "Diretrizes para projetos básicos de empreendimentos de transmissão (item 6.10)", "—", "—"],
        ["Cálculos Elétricos de LTs", "Livro do acervo, cap. 6 (campo elétrico: simulação de cargas)", "—", "—"],
        ["ESS-2ITA-595-87", "Efeitos eletromagnéticos (Energisa/IOSI): metodologia e limites", "R0A", "—"]], [3.5, 8.0, 1.5, 3.0])

    R.h1("NORMAS TÉCNICAS ADOTADAS")
    R.lista(["REN ANEEL nº 915/2021 – níveis de referência de campos a 60 Hz (revoga as RENs 398/2010, 413/2010 e 616/2014): "
             "público em geral 4,17 kV/m e 200 µT; ocupacional 8,33 kV/m e 1000 µT, ao nível de 1,5 m do solo. "
             "NECESSITA VALIDAÇÃO: valores transcritos do relatório ESS-2ITA-595-87; o texto oficial da REN 915 não consta no acervo.",
             "Diretrizes de projeto básico, item 6.10 – premissas do estudo: tensão, temperatura máxima, carregamento (operação e emergência), "
             "altura mínima à temperatura máxima, configuração e sequência de fases, altura de 1,5 m; campos dentro e fora da faixa.",
             "ICNIRP (1998/2010): referência dos limites adotados pela REN 915 (não consultada diretamente)."])

    R.h1("METODOLOGIA DE CÁLCULO")
    R.h2("Campo elétrico – simulação de cargas")
    R.p("Os condutores são substituídos por cargas lineares na posição do centro de cada feixe, com solo plano e equipotencial (imagens em −y). "
        "Os coeficientes de potencial de Maxwell dão as cargas a partir das tensões fase-terra fasoriais.")
    R.eq(msub(mi("P"), mi("ii")) + mu("=") + mfrac(mu("1"), mu("2π") + msub(mi("ε"), mu("0"))) + mu("ln") + mpar(mfrac(mu("2") + msub(mi("h"), mi("i")), msub(mi("r"), mu("eq")))) +
         mu(" ;  ") + msub(mi("P"), mi("ij")) + mu("=") + mfrac(mu("1"), mu("2π") + msub(mi("ε"), mu("0"))) + mu("ln") + mfrac(msub(mi("D"), mu("ij'")), msub(mi("D"), mi("ij"))))
    R.eq(mu("[") + mi("Q") + mu("]=") + msup(mu("[") + mi("P") + mu("]"), mu("−1")) + mu("[") + mi("V") + mu("]"))
    R.eq(msub(mi("E"), mi("y")) + mu("=") + mfrac(mu("1"), mu("2π") + msub(mi("ε"), mu("0"))) + mu("∑") + msub(mi("q"), mi("i")) + mpar(mfrac(mi("y") + mu("−") + msub(mi("y"), mi("i")), msubr := msup(msub(mi("r"), mi("i")), mu("2"))) +
         mu("−") + mfrac(mi("y") + mu("+") + msub(mi("y"), mi("i")), msup(msub(mi("r'"), mi("i")), mu("2")))))
    R.simbolos([("Pij", "coeficiente de potencial entre os condutores i e j", "m/F"), ("hi", "altura média do condutor i", "m"),
                ("req", "raio equivalente do feixe, r_eq = [n·r·R^(n−1)]^(1/n)", "m"), ("Dij, Dij'", "distância ao condutor j e à sua imagem", "m"),
                ("qi", "carga linear do condutor i (fasor)", "C/m"), ("V", "tensão fase-terra (fasor), Un/√3", "V")])
    R.p("O valor eficaz resultante em cada ponto é a soma fasorial das componentes: E = √(|Ex|² + |Ey|² + |Ez|²).")
    R.h2("Campo magnético – Biot-Savart com imagens complexas (Deri)")
    R.p("Cada condutor é tratado como filamento de corrente fasorial; o retorno pelo solo é representado por uma imagem a profundidade complexa "
        "p = √(ρ/(jωμ0)), com corrente de sentido oposto. Para ρ elevado o efeito do solo é pequeno; para p → 0 (solo condutor perfeito) a componente horizontal dobra.")
    R.eq(mi("p") + mu("=") + msqrt(mfrac(mi("ρ"), mi("j") + mi("ω") + msub(mi("μ"), mu("0")))) + mu(" ;  ") + msub(mi("y"), mu("imagem")) + mu("=−") + msub(mi("y"), mi("i")) + mu("−2") + mi("p") +
         mu(" ;  ") + msub(mi("B"), mi("x")) + mu("=−") + mfrac(msub(mi("μ"), mu("0")), mu("2π")) + mu("∑") + msub(mi("I"), mi("i")) + mpar(mfrac(mi("y") + mu("−") + msub(mi("y"), mi("i")), msup(msub(mi("r"), mi("i")), mu("2"))) +
         mu("−") + mfrac(mi("y") + mu("+") + msub(mi("y"), mi("i")) + mu("+2") + mi("p"), msup(msub(mi("r'"), mi("i")), mu("2")))))
    R.simbolos([("ρ", "resistividade do solo", "Ω·m"), ("ω", "2π·60 Hz", "rad/s"), ("μ0", "4π·10⁻⁷", "H/m"), ("Ii", "corrente fasorial do condutor i", "A")])
    R.h2("Linhas vizinhas")
    R.p("Linhas em paralelismo são incluídas na mesma seção (cargas e correntes juntas). Travessias têm seção própria, na altura relativa informada e "
        "no ângulo de cruzamento: o campo da vizinha é calculado na seção perpendicular ao seu eixo e projetado sobre os eixos do estudo. "
        "A defasagem entre as tensões da vizinha e da LT em estudo é, quando não informada, a de pior caso: varredura de 0° a 350° (passo 10°) "
        "que maximiza o campo no ponto de verificação, separadamente para E e para B.")

    R.h1("DADOS DE ENTRADA E CONSIDERAÇÕES GERAIS")
    lin = [["Frequência", f(r["freq"], 0), "Hz", "Módulo 1"],
           ["Altura do observador (livre/paralelo/travessia)", f(r["h_obs"], 2), "m", "REN 915 / Diretrizes 6.10"],
           ["Altura do condutor mais baixo", f(e["h_min"], 2), "m", "Altura na estrutura − flecha" if True else ""],
           ["Resistividade do solo", f(r["rho"], 0), "Ω·m", "Informado"],
           ["Tensão utilizada no campo elétrico", r["tensao_modo"], "—", "Informado"],
           ["Cabos guarda no campo elétrico", "incluídos (V = 0)" if r["incluir_guardas_e"] else "desprezados", "—", "PREMISSA conservadora"],
           ["Perfil lateral", f"{f(r['x_min'], 0)} a {f(r['x_max'], 0)}", "m", "Informado"],
           ["Semi-largura da faixa", f(semi, 1) if semi else "não avaliada", "m", "Módulo 4 / informado"],
           ["Raio equivalente dos cabos das vizinhas", f(r["req_viz"] * 1000, 1), "mm", "PREMISSA"]]
    R.tabela("Parâmetros do cálculo", ["Parâmetro", "Valor", "Unidade", "Origem"], lin, [6.0, 3.5, 2.0, 4.5])
    lin = []
    for k, c in sorted(e["circs"].items()):
        lin.append([f"Circuito {k}", f(c["un_kv"], 1), f(c["umax_kv"], 1), f(c["i_normal"], 0), f(c["i_emerg"], 0), f(c["fp"], 2)])
    R.tabela("Circuitos da LT em estudo", ["Circuito", "Un (kV)", "Umáx (kV)", "I normal (A)", "I emergência (A)", "Fator de potência"], lin,
             [2.5, 2.5, 2.5, 3.0, 3.5, 2.5])
    R.tabela("Coordenadas dos condutores (relativas ao eixo)", ["Condutor", "x (m)", "y estrutura (m)", "req (mm)"],
             [[c["nome"], f(c["x"], 2), f(c["y"], 2), f(c["req"] * 1000, 1)] for c in e["fases"]], [4.0, 3.0, 4.0, 3.0])
    if resumo_pontos:
        R.tabela("Pontos de estudo e vizinhas", ["Ponto", "Descrição"], [[a, b] for a, b in resumo_pontos], [4.5, 11.5])
    R.p("Premissas e limitações: torres e vegetação não distorcem o campo; solo plano; cargas uniformes ao longo do vão (altura mínima à temperatura máxima, "
        "condição mais desfavorável); cabos guarda desprezados no campo magnético; condutores das vizinhas representados por raio equivalente adotado; "
        "correntes em fase com a respectiva tensão, salvo fator de potência informado.", "Considerações:")

    R.h1("RESULTADOS OBTIDOS")
    if not semi:
        R.p("Largura da faixa não definida: o valor na borda não foi avaliado e a verificação adota o máximo do perfil (conservador).", italico=True)
    for p in r["pontos"]:
        R.h2(f"{p['nome']} ({p['tipo']})")
        R.p(f"Limite adotado: {p['publico']} – E ≤ {f(p['lim_e'], 2)} kV/m e B ≤ {f(p['lim_b'], 0)} µT. "
            + (("Vizinhas consideradas: " + ", ".join(p["vizinhas"]) + ".") if p["vizinhas"] else "Sem linhas vizinhas."))
        lin = []
        for cen, c in p["cenarios"].items():
            lin.append([cen + (" (cenário do ponto)" if cen == p["cen_i"] else ""),
                        f(c["E_ref"], 3) if c["E_ref"] is not None else "—", f(c["E_max"], 3), f(c["B_ref"], 2) if c["B_ref"] is not None else "—",
                        f(c["B_max"], 2), _st(c["ok_E"] and c["ok_B"])])
        R.tabela(f"Resultados – {p['nome']}", ["Cenário", "E borda/ponto (kV/m)", "E máx. (kV/m)", "B borda/ponto (µT)", "B máx. (µT)", "Situação"], lin,
                 [4.2, 2.6, 2.2, 2.6, 2.2, 2.2])
        c = p["cenarios"][p["cen_i"]]
        pior = [f"{n}: {f(t, 0)}°" for n, t in zip(c["fontes"][1:], c["theta_E"][1:])]
        if pior:
            R.p("Defasagem de pior caso para E – " + "; ".join(pior) + ". Para B – " + "; ".join(
                f"{n}: {f(t, 0)}°" for n, t in zip(c["fontes"][1:], c["theta_B"][1:])) + ".")
        R.figura(fig_perfil(p, p["cen_i"], semi), f"Perfil lateral de E e B – {p['nome']}.", larg_cm=14.0)
        if "s3d_E" in c:
            R.figura(fig_3d(p, c), f"Distribuição de E e B no plano transversal (x × altura) – {p['nome']}.", larg_cm=15.0)

    R.h1("CONCLUSÕES")
    ok_t = all(c["ok_E"] and c["ok_B"] for p in r["pontos"] for c in p["cenarios"].values())
    R.lista([f"Maior campo elétrico ao nível de {f(r['h_obs'], 1)} m: {f(max(c['E_max'] for p in r['pontos'] for c in p['cenarios'].values()), 3)} kV/m "
             f"(limite público {f(cc.LIMITES['Público em geral'][0], 2)} kV/m).",
             f"Maior densidade de fluxo magnético: {f(max(c['B_max'] for p in r['pontos'] for c in p['cenarios'].values()), 2)} µT "
             f"(limite público {f(cc.LIMITES['Público em geral'][1], 0)} µT).",
             "Todos os pontos verificados " + ("ATENDEM" if ok_t else "NÃO ATENDEM (ver Seção 6)") + " aos níveis de referência adotados."])
    R.p("Recomendações:", align=WD_ALIGN_PARAGRAPH.LEFT).runs[0].bold = True
    R.lista(["Validar os níveis de referência com o texto oficial da REN ANEEL 915/2021.",
             "Confirmar a altura mínima dos condutores à temperatura máxima no PLS-CADD e a sequência de fases dos circuitos vizinhos.",
             "Medir em campo (NBR/IEC 61786) após a energização, nos pontos críticos, para confirmação."])
    R.p("Grau de confiança: médio-alto para o perfil da LT em estudo (método consagrado, verificado contra solução analítica de condutor único). "
        "Dependem de premissas as correntes de emergência, o raio equivalente e as posições das vizinhas, a defasagem informada e os limites da REN 915, "
        "cujo texto oficial não consta no acervo.", "O que falta para eu informar com certeza:")

    R.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    R.lista(["Cálculos Elétricos de Linhas de Transmissão – cap. 6 (campo elétrico). Acervo do projeto.",
             "Diretrizes para a elaboração de projetos básicos para empreendimentos de transmissão – item 6.10.",
             "ESS-2ITA-595-87 – Efeitos eletromagnéticos (Energisa/IOSI): campos E e B, método de Deri e limites da REN 915.",
             "Deri, A. et al. – The complex ground return plane: a simplified model for homogeneous and multi-layer earth return (não consultado no acervo).",
             "REN ANEEL nº 915/2021 (não consultada diretamente)."])
    R.salvar(caminho)
    return caminho
