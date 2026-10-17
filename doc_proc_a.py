"""Procedimentos – capítulos introdutórios e Módulos 1 a 3."""
import cmath
import math

from doc_proc_base import (EQ, IN_A, REF, V, T, app_tab, checklist, comparacao, dif, f, mfrac, mi, mpar, msqrt, msub, msup, mu, passos)
from relatorio_m2 import fc

EPS0_CELT2 = 1e-9 / (36 * math.pi)      # valor usado na planilha CELT2 (F/m)


# ============================================================================= introdução
def intro(R):
    R.h1("OBJETIVO E COMO USAR ESTE DOCUMENTO")
    R.p("Este documento ensina a elaborar, manualmente e no software BK | Cálculos de LT, cada um dos 16 estudos elétricos de linhas de transmissão "
        "executados pela BK Engenharia. O objetivo é que o novo engenheiro (1) entenda a metodologia e as equações de cada estudo, "
        "(2) saiba refazer um exemplo à mão (calculadora, Excel ou Python) e (3) preencha o mesmo estudo no app e confira o resultado. "
        "Quem sabe fazer manualmente consegue criticar o resultado do software; quem só preenche o software não percebe quando um dado está errado.")
    R.h2("Como cada capítulo está organizado")
    R.tabela("Estrutura de cada capítulo de estudo", ["Bloco", "O que contém", "Para que serve"], [
        ["Objetivo e quando fazer", "Finalidade do estudo e quando o cliente/edital o exige", "Saber se o estudo é necessário"],
        ["Normas e referências", "Norma com item/seção e livro/capítulo usados", "Rastrear a origem de cada critério"],
        ["Metodologia (manual)", "Passos de cálculo com as equações numeradas e as variáveis", "Entender o método"],
        ["Exemplo resolvido", "Cálculo passo a passo com o caso de referência (LT 138 kV Exemplo) e comparação com o app", "Treinar e validar"],
        ["Como preencher no app", "Aba, campo e valor, na ordem de preenchimento", "Reproduzir o exemplo no software"],
        ["Conferência", "Checklist e erros comuns", "Revisar antes de emitir o relatório"]], [4.0, 7.5, 5.5])
    R.h2("Roteiro de aprendizado sugerido")
    R.lista(["Ler os capítulos 2 a 4 (convenções, caso de referência e fluxo entre estudos).",
             "Para cada estudo: ler a metodologia, refazer o exemplo à mão e só depois preencher o app com os mesmos dados.",
             "Comparar manual × app; diferenças acima de 1 % exigem explicação (arredondamento, premissa distinta ou erro de dado).",
             "Repetir o estudo com o projeto real e emitir o relatório (.docx e PDF) pelo botão do módulo."])

    R.h1("CONVENÇÕES ADOTADAS")
    R.h2("Unidades e sinais")
    R.lista(["Tensões de linha em kV (valor eficaz) salvo indicação de \"crista\"; correntes em A; comprimentos em m (distâncias) ou km (linha); "
             "resistividade do solo em Ω·m; ângulos em graus.",
             "Decimal com vírgula nos textos e relatórios (3,5); no app digita-se com ponto ou vírgula conforme o campo aceita.",
             "Coordenadas da seção transversal: x horizontal (positivo à direita do eixo) e y altura acima do solo; fases A, B, C da esquerda para a direita (arranjo horizontal)."])
    R.h2("Etiquetas de rastreabilidade")
    R.tabela("Etiquetas obrigatórias nos relatórios BK", ["Etiqueta", "Significado", "O que fazer"], [
        ["DADO NÃO INFORMADO", "O estudo precisa do dado e ele não foi fornecido (cliente, catálogo, medição)", "Solicitar; nunca inventar o valor"],
        ["PREMISSA", "Valor adotado pelo projetista na ausência de dado; deve ser justificado", "Registrar a justificativa e submeter à aprovação"],
        ["NECESSITA VALIDAÇÃO", "Fórmula/valor sem fonte conferida no acervo ou com leitura duvidosa", "Conferir com a norma/edital antes de emitir"],
        ["ATENDE / NÃO ATENDE", "Resultado da verificação contra o critério", "NÃO ATENDE exige ação: mudar o projeto ou justificar"]], [4.0, 8.0, 5.0])
    R.h2("Boas práticas de entrada de dados")
    R.lista(["Preencher na ordem das abas; as abas seguintes herdam dados das anteriores.",
             "Salvar o projeto (botão \"Salvar\") depois de cada módulo concluído; usar \"Salvar como novo\" para uma nova revisão.",
             "Não alterar valores padrão do app sem justificativa; a cada alteração, registrar a fonte (norma, edital, medição).",
             "Conferir unidades no rótulo do campo (kV × V, m × mm, Ω/km × Ω)."])

    R.h1("CASO DE REFERÊNCIA DOS EXEMPLOS")
    R.p("Todos os exemplos usam a mesma linha fictícia, \"LT 138 kV Exemplo\", de modo que o resultado de um estudo alimenta o seguinte e o "
        "treinamento tem continuidade. Os dados de vento, temperatura, solo e linhas vizinhas são ilustrativos e foram escolhidos apenas para "
        "o treinamento; num projeto real devem vir de medições do INMET, de sondagem de solo e do cliente.")
    R.tabela("Dados do caso de referência", ["Grandeza", "Valor", "Origem / observação"], [
        ["Cliente / projeto", "Energisa · LT 138 kV Exemplo · BK-EX-001 · R0", "Cadastro do projeto"],
        ["Tensão nominal Un / máxima Um", "138 kV / 145 kV", "Sistema"],
        ["Frequência", "60 Hz", "Sistema"],
        ["Comprimento", "80 km", "Sistema"],
        ["Potência na carga / fator de potência", "60 MVA / 0,95 indutivo", "Circuito 1"],
        ["Corrente nominal", f"{f(IN_A, 1)} A", "I = S/(√3·Un)"],
        ["Circuitos / feixe", "1 circuito · 1 condutor por fase", "Configuração"],
        ["Condutor", "HAWK 477 MCM (CAA 26/7): Ø 21,78 mm; 280,8 mm²; 0,9764 kg/m; RTC 87,06 kN; R20 0,1196 Ω/km; R75 0,1435 Ω/km", "Catálogo de cabos"],
        ["Cabos guarda", "CG1 OPGW 12,4 mm 36FO (x = 0; y = 30 m) · CG2 EHS 7/16\" (x = 6 m; y = 30 m)", "Configuração"],
        ["Fases (arranjo horizontal)", "A (−4,5; 24) · B (0; 24) · C (4,5; 24) m", "Geometria na estrutura"],
        ["Altitude / latitude / longitude", "870 m / −27,6° / −48,5°", "Local (SC)"],
        ["Resistividade do solo", "1000 Ω·m (estudos de campo, interferência e blindagem) · 500 Ω·m (aterramento)", "Premissa de treinamento"],
        ["Altura das fases nos estudos pontuais", "24 m (sem abater flecha, como no app com flecha = 0)", "Geometria"],
        ["Linha vizinha (estudos pontuais)", "LT 69 kV · 200 A · espaçamento horizontal 3 m · altura 12 m · a 25 m do eixo, paralelismo de 1 km", "Biblioteca de linhas"],
        ["Casa (edificação)", "20 m do eixo; altura de referência 1,5 m", "Ponto de estudo"]], [4.4, 8.4, 4.2])
    R.p("Seção transversal: três fases em arranjo horizontal, espaçadas de 4,5 m, 6 m abaixo dos cabos guarda (30 m), e guardas separados de 6 m. "
        "Esse desenho é montado no app na aba \"Geometria da LT\" do Módulo 2 (ver capítulo M2).")

    R.h1("FLUXO ENTRE OS ESTUDOS")
    R.p("Os módulos compartilham dados: preencher o Módulo 1 primeiro e respeitar a ordem de dependência evita retrabalho. A tabela mostra de onde cada módulo "
        "tira seus dados e para quem entrega resultados.")
    R.tabela("Dependências entre os módulos", ["Módulo", "Recebe de", "Entrega para"], [
        ["M1 Dados do Projeto e Sistema", "Cliente / edital", "Todos"],
        ["M2 Parâmetros Elétricos", "M1 (geometria, cabos, sistema)", "M14, M15 (Z1, C1); M16 (ângulos); M7 (X')"],
        ["M3 Estudo dos Ventos", "INMET; altura média das fases (M2)", "M4 (V30, q0); M5 (V_freq, V_manobra)"],
        ["M4 Faixa de Domínio", "M1, M3, M5 (Fsfl)", "M8, M9, M10 (largura da faixa)"],
        ["M5 Coordenação e Isolamento", "M1, M2, M3", "M12, M16 (CFO), M4"],
        ["M6 Aterramento", "Solo (sondagem), curto-circuito", "M16 (R0), M9 (R de pé)"],
        ["M7 Condutor e Cabo Guarda", "M1, M2", "M13 (corrente), M2 (cabo escolhido)"],
        ["M8 Campos E e B", "M1, M4 (faixa)", "Relatório de exposição"],
        ["M9 Interferência", "M1, M8 (premissas de geometria e correntes)", "Relatório de interferência"],
        ["M10 RI e RA", "M1, M4", "Relatório de RI/RA"],
        ["M11 Efeito Corona", "M1, M2", "Relatório de corona (pode ser emitido sozinho)"],
        ["M12 Tensão Máxima Operativa", "M1, M5", "Verificação do isolamento"],
        ["M13 Ampacidade e Flecha", "M1, M7", "Folgas ao solo, limite térmico"],
        ["M14 Rejeição de Carga", "M2 (Z1, C1), M1", "Compensação reativa (triagem)"],
        ["M15 Religamento Tripolar", "M2, M1", "Resistor de pré-inserção (triagem)"],
        ["M16 Blindagem", "M1, M2, M5, M6", "Taxa de desligamentos por descargas"]], [5.0, 6.0, 6.0])

    R.h1("OPERAÇÃO GERAL DO APP")
    R.h2("Passos gerais")
    R.lista(["Abrir o app e escolher o projeto em \"Projetos salvos\" (ou criar um novo preenchendo o Módulo 1 e clicando em \"Salvar\").",
             "Escolher o módulo no menu lateral (\"1. Dados do Projeto e Sistema\" ... \"16. Blindagem contra Descargas Atmosféricas\").",
             "Preencher as abas na ordem apresentada; campos com valor padrão só devem ser alterados com justificativa.",
             "Ler os avisos amarelos (pendências, premissas) e os vermelhos (erros): o relatório só é liberado quando as pendências são resolvidas.",
             "Na aba \"Resultados e relatório\": conferir métricas e tabelas, clicar em \"Gerar relatório (.docx, padrão BK)\" e, se necessário, em \"Gerar PDF para impressão\".",
             "Salvar o projeto novamente (\"Salvar\" ou \"Salvar como novo\" para nova revisão)."])
    R.h2("Relatório gerado")
    R.p("Todo relatório sai no formato do documento padrão BK (capa com carimbo, cabeçalho, rodapé, sumário, equações no Word) e traz, em anexo, o "
        "SCRIPT DE CÁLCULO utilizado, o que torna o estudo reprodutível e auditável.")


# ============================================================================= M1
def m1(R):
    R.h1("M1 – DADOS DO PROJETO E SISTEMA")
    R.h2("Objetivo e quando fazer")
    R.p("O Módulo 1 é o ponto de partida: cadastra o projeto, o sistema elétrico, a configuração da LT e os circuitos. Todos os demais módulos leem esses dados. "
        "Não há cálculo de estudo neste módulo, apenas a corrente nominal derivada da potência e da tensão.")
    R.p("Em todo projeto, antes de qualquer outro estudo.", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["Diretrizes para Elaboração de Projetos Básicos (ONS/EPE) – dados de entrada do sistema.",
             "Edital / especificação técnica do cliente – tensão nominal, tensão máxima operativa, potência e número de circuitos."])
    R.h2("Metodologia – dados e grandezas derivadas")
    R.p("A corrente nominal de cada circuito é derivada da potência na carga e da tensão nominal (potência trifásica, fator de potência indutivo):")
    EQ(R, V("I", "n"), T("="), mfrac(V("S"), msqrt(T("3")) + V("U", "n")), T(" ;  "), V("S"), T("="), mfrac(V("P"), mi("cos φ")))
    R.simbolos([("In", "corrente nominal do circuito", "A"), ("S", "potência aparente na carga", "kVA"), ("Un", "tensão nominal de linha", "kV")])
    R.p("A relação Um/Un é um teste de sanidade: valores de 1,05 a 1,10 são usuais (145/138 = 1,051). Acima de 1,10, conferir o dado.")
    R.h2("Exemplo resolvido")
    passos(R, "Corrente nominal do circuito 1", [
        ("In = S / (√3·Un)", f"60.000 kVA / (1,7321 × 138 kV) = {f(IN_A, 1)} A"),
        ("Relação Um/Un", f"145 / 138 = {f(145 / 138, 3)}")])
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 1 – preenchimento do caso de referência", [
        ("Projeto", "Cliente", "Energisa", "O logotipo do cliente aparece no relatório se estiver cadastrado"),
        ("Projeto", "Nome do projeto", "LT 138 kV Exemplo", "Vai para a capa e o cabeçalho"),
        ("Projeto", "Número do projeto", "BK-EX-001", "Código BK do projeto"),
        ("Projeto", "Revisão", "R0", "Alterar a cada emissão"),
        ("Projeto", "Responsável técnico (CREA)", "Eng. Responsável – CREA", "Aparece na capa"),
        ("Sistema", "Frequência (Hz)", "60", "50 ou 60"),
        ("Sistema", "Tensão nominal (kV)", "138", "Un do sistema"),
        ("Sistema", "Tensão máxima operativa (kV)", "145", "Um; série normalizada IEC 60038"),
        ("Sistema", "Potência por circuito (MVA)", "60", "Padrão para os circuitos"),
        ("Sistema", "Comprimento (km)", "80", "Comprimento total da LT"),
        ("Configuração da LT", "Nº de circuitos", "1", "1 ou 2"),
        ("Configuração da LT", "Nº de cabos guarda", "2", "Mínimo de 2 em linhas de transmissão (edital/Diretrizes)"),
        ("Configuração da LT", "Cabo guarda 1 / Cabo guarda 2", "OPGW 12,4 mm 36FO / EHS 7/16\"", "Catálogo de cabos"),
        ("Circuitos", "Nome / alimentação", "SE Origem → SE Destino", "Texto do relatório"),
        ("Circuitos", "Arranjo das fases do circuito 1", "Horizontal", "Horizontal, vertical ou triangular/livre"),
        ("Circuitos", "Condutor de fase", "HAWK 477 MCM", "Catálogo (293 cabos)"),
        ("Circuitos", "Cabos por fase", "1", "Feixe: 1 a 4"),
        ("Circuitos", "Estado do circuito", "Energizado", "Desligado/aterrado afeta campos e acoplamentos"),
        ("Circuitos", "Tensão nominal / máxima (kV)", "138 / 145", "Por circuito"),
        ("Circuitos", "Potência na carga (MVA)", "60", "Define a corrente nominal"),
        ("Circuitos", "Fator de potência (indutivo)", "0,95", ""),
        ("Circuitos", "Limite de corrente / ampacidade (A)", "0", "0 = usar o catálogo; informar se o cliente limitar")])
    R.p("A geometria da seção (alturas e distâncias) é lançada na aba \"Geometria da LT\" do Módulo 2; as linhas vizinhas e os pontos de estudo "
        "são cadastrados na aba \"Pontos e vizinhas\" (compartilhada pelos módulos 4, 8, 9 e 10).")
    R.h2("Conferência")
    checklist(R, ["Un, Um, frequência, comprimento e potência conferem com o edital.",
                  "Condutor e cabos guarda escolhidos no catálogo (sem alerta de importação).",
                  "Corrente nominal exibida = S/(√3·Un).",
                  "Projeto salvo com número e revisão."])


# ============================================================================= M2
def calc_m2():
    d = REF["d_mm"] / 1000
    r = d / 2
    Ds = 0.7788 * r
    R = REF["r75"]
    Dab, Dbc, Dca = 4.5, 4.5, 9.0
    Deq = (Dab * Dbc * Dca) ** (1 / 3)
    w = 2 * math.pi * REF["f"]
    L = 2e-7 * math.log(Deq / Ds) * 1000          # H/km
    C = 2 * math.pi * EPS0_CELT2 / math.log(2 * Deq / d) * 1000
    ZL, YL = complex(R, w * L), complex(0, w * C)
    Zo, gam = cmath.sqrt(ZL / YL), cmath.sqrt(ZL * YL)
    gl = gam * REF["km"]
    Zs, Yp = Zo * cmath.sinh(gl), cmath.tanh(gl / 2) / Zo
    A, B, Cc = 1 + Zs * Yp, Zs, 2 * Yp + Zs * Yp ** 2
    Vs = REF["un"] * 1e3 / math.sqrt(3)
    S = REF["mva"] * 1e6 * complex(REF["fp"], math.sqrt(1 - REF["fp"] ** 2))
    Vr = Vs
    for _ in range(200):
        Ir = (S / (3 * Vr)).conjugate()
        Vr = (Vs - B * Ir) / A
    Is = Cc * Vr + A * Ir
    Ro = math.sqrt(L / C)
    sil = REF["un"] ** 2 / Ro
    p_mw = REF["mva"] * REF["fp"]
    return dict(d=d, r=r, Ds=Ds, R=R, Deq=Deq, w=w, L=L, C=C, ZL=ZL, YL=YL, Zo=Zo, gam=gam, gl=gl, Zs=Zs, Yp=Yp, A=A, B=B, Cc=Cc, Vs=Vs, S=S,
                Vr=Vr, Ir=Ir, Is=Is, Ro=Ro, sil=sil, p_mw=p_mw, vr_kv=abs(Vr) * math.sqrt(3) / 1e3,
                reg=(abs(Vs / A) - abs(Vr)) / abs(Vr) * 100, perdas_kw=(3 * (Vs * Is.conjugate()).real - 3 * (Vr * Ir.conjugate()).real) / 1e3)


def m2(R):
    x = calc_m2()
    R.h1("M2 – PARÂMETROS ELÉTRICOS DA LINHA")
    R.h2("Objetivo e quando fazer")
    R.p("Calcular os parâmetros longitudinais e transversais da LT (resistência, indutância, capacitância, impedância característica, constante de propagação), "
        "o modelo π equivalente e o desempenho em regime permanente (tensão na carga, regulação, perdas, relação P/SIL). Também fornece as componentes "
        "de sequência (Z1, Z0, C1, C0) usadas nos estudos de rejeição de carga e religamento.")
    R.p("Em todo projeto de LT; é a base dos módulos 14, 15 e dos estudos de desempenho.", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["Planilha CELT2-IPOG (método de referência BK) e Livro 3 – Cálculos Elétricos de Linhas de Transmissão.",
             "Livro 2 – Projeto Elétrico de Linhas de Transmissão (parâmetros e modelo π).",
             "Método matricial: Carson (retorno pelo solo), coeficientes de Maxwell (capacitância), redução de Kron (cabos guarda) e componentes simétricas."])

    R.h2("Metodologia manual (método CELT2)")
    R.p("Passo 1 – Distância média geométrica entre fases e raio do condutor. O Ds (raio médio geométrico) vem do catálogo; quando o RMG não está cadastrado, "
        "adota-se Ds = 0,7788·r como premissa (condutor sólido), sempre sinalizada no relatório.")
    EQ(R, V("D", "eq"), T("="), msup(mpar(V("D", "AB") + T("·") + V("D", "BC") + T("·") + V("D", "CA")), T("1/3")), T(" ;  "), V("D", "s"), T("="), T("0,7788·"), V("r"))
    R.p("Passo 2 – Indutância e capacitância por fase (por km):")
    EQ(R, V("L"), T("=2·10"), msup(T(""), T("−7")), T("·ln"), mpar(mfrac(V("D", "eq"), V("D", "s"))), T("·1000  [H/km]"))
    EQ(R, V("C"), T("="), mfrac(T("2π") + msub(mi("ε"), mu("0")), T("ln") + mpar(mfrac(T("2") + V("D", "eq"), V("d")))), T("·1000  [F/km]"))
    R.simbolos([("Deq", "distância média geométrica entre fases", "m"), ("Ds", "raio médio geométrico do condutor", "m"), ("d", "diâmetro do condutor", "m"),
                ("ε0", "permissividade do vácuo (CELT2: 10⁻⁹/36π)", "F/m")])
    R.p("Passo 3 – Impedância e admitância longitudinal/transversal, impedância característica e constante de propagação:")
    EQ(R, V("Z", "L"), T("="), V("R"), T("+j2π"), V("f"), V("L"), T(" ;  "), V("Y", "L"), T("=j2π"), V("f"), V("C"))
    EQ(R, V("Z", "0"), T("="), msqrt(mfrac(V("Z", "L"), V("Y", "L"))), T(" ;  "), mi("γ"), T("="), msqrt(V("Z", "L") + V("Y", "L")))
    R.p("Passo 4 – Modelo π equivalente (ℓ = comprimento da linha) e matriz ABCD:")
    EQ(R, V("Z", "s"), T("="), V("Z", "0"), T("senh"), mpar(mi("γ") + mi("ℓ")), T(" ;  "), V("Y", "p"), T("="), mfrac(T("tanh") + mpar(mfrac(mi("γ") + mi("ℓ"), T("2"))), V("Z", "0")))
    EQ(R, V("A"), T("="), V("D"), T("=1+"), V("Z", "s"), V("Y", "p"), T(" ;  "), V("B"), T("="), V("Z", "s"), T(" ;  "), V("C"), T("=2"), V("Y", "p"), T("+"), V("Z", "s"), msup(V("Y", "p"), T("2")))
    R.p("Passo 5 – Desempenho com tensão fixa na fonte (Un) e carga S com fator de potência indutivo. Resolve-se, por iteração, Vs = A·Vr + B·Ir, com Ir = (S/3Vr)*; "
        "a regulação é a variação entre a tensão a vazio (Vs/A) e a tensão com carga; as perdas são a diferença entre as potências de entrada e saída.")
    EQ(R, V("Reg"), T("="), mfrac(T("|Vs/A|−|Vr|"), T("|Vr|")), T("·100  [%]"), T(" ;  SIL="), mfrac(msup(V("U", "n"), T("2")), V("R", "o")), T(" ;  "),
       V("R", "o"), T("="), msqrt(mfrac(V("L"), V("C"))))
    R.p("O método matricial (usado em paralelo pelo app) monta as matrizes de impedância de Carson e de potencial de Maxwell com todos os condutores (fases e guardas), "
        "elimina os guardas por redução de Kron e aplica a matriz de transformação de Fortescue para obter Z1, Z0, C1 e C0. As duas abordagens devem coincidir "
        "dentro de poucos décimos de por cento; a diferença vem do efeito dos guardas e do solo.")

    R.h2("Exemplo resolvido – LT 138 kV Exemplo")
    passos(R, "Parâmetros CELT2 do circuito 1", [
        ("Deq = (D_AB·D_BC·D_CA)^(1/3)", f"(4,5 × 4,5 × 9,0)^(1/3) = {f(x['Deq'], 3)} m"),
        ("Ds = 0,7788·r (RMG não cadastrado)", f"0,7788 × {f(x['r'] * 1000, 3)} mm = {f(x['Ds'] * 1000, 3)} mm"),
        ("R (HAWK a 75 °C)", f"{f(x['R'], 4)} Ω/km"),
        ("L = 2·10⁻⁷·ln(Deq/Ds)·1000", f"2e-7 × ln({f(x['Deq'], 3)}/{f(x['Ds'], 6)}) × 1000 = {f(x['L'] * 1e3, 4)} mH/km"),
        ("C = 2π·ε0 / ln(2·Deq/d)·1000", f"2π × 8,842e-12 / ln(2 × {f(x['Deq'], 3)}/{f(x['d'], 5)}) × 1000 = {f(x['C'] * 1e9, 4)} nF/km"),
        ("ZL = R + j2πfL", f"{fc(x['ZL'], 4)} Ω/km"),
        ("YL = j2πfC", f"j {f(x['YL'].imag * 1e6, 3)} µS/km"),
        ("Zo = √(ZL/YL)", f"{fc(x['Zo'], 2)} Ω → |Zo| = {f(abs(x['Zo']), 2)} Ω"),
        ("γℓ = √(ZL·YL)·ℓ", f"{fc(x['gl'], 5)}"),
        ("Zs = Zo·senh(γℓ)", f"{fc(x['Zs'], 3)} Ω"),
        ("Yp = tanh(γℓ/2)/Zo", f"{x['Yp'].real:.4e} + j{x['Yp'].imag:.4e} S"),
        ("Ro = √(L/C); SIL = Un²/Ro", f"{f(x['Ro'], 2)} Ω; {f(x['sil'], 2)} MW"),
        ("P = S·cosφ; P/SIL", f"{f(x['p_mw'], 1)} MW; {f(x['p_mw'] / x['sil'], 3)}")])
    passos(R, "Desempenho em regime permanente (tensão fixa na fonte)", [
        ("Vs (fase-neutro)", f"138/√3 = {f(x['Vs'] / 1e3, 3)} kV"),
        ("Resolver Vs = A·Vr + B·Ir (iteração)", f"Vr = {f(abs(x['Vr']) / 1e3, 3)} kV (fase-neutro)"),
        ("Tensão de linha na carga", f"√3 × {f(abs(x['Vr']) / 1e3, 3)} = {f(x['vr_kv'], 3)} kV"),
        ("Regulação = (|Vs/A| − |Vr|)/|Vr|", f"{f(x['reg'], 3)} %"),
        ("Perdas = Pentrada − Psaída", f"{f(x['perdas_kw'], 1)} kW")])
    comparacao(R, "Manual × app (Módulo 2, método CELT2)", [
        ("L (mH/km)", f(x["L"] * 1e3, 4), "1,3010", dif(x["L"] * 1e3, 1.3010)),
        ("C (nF/km)", f(x["C"] * 1e9, 4), "8,8817", dif(x["C"] * 1e9, 8.8817)),
        ("|Zo| (Ω)", f(abs(x["Zo"]), 2), "390,67", dif(abs(x["Zo"]), 390.67)),
        ("Tensão na carga (kV)", f(x["vr_kv"], 3), "126,790", dif(x["vr_kv"], 126.790)),
        ("Regulação (%)", f(x["reg"], 3), "9,416", dif(x["reg"], 9.416)),
        ("Perdas (kW)", f(x["perdas_kw"], 1), "2.508,93", dif(x["perdas_kw"], 2508.93)),
        ("P/SIL", f(x["p_mw"] / x["sil"], 3), "1,146", dif(x["p_mw"] / x["sil"], 1.146))])
    R.p("Resultados do método matricial (app): Z1 = 0,1437 + j0,4904 Ω/km; C1 = 8,9655 nF/km; Z0 = 0,5443 + j1,3462 Ω/km; C0 = 5,2009 nF/km. "
        "Como Z1 e C1 incluem o efeito do solo (ρ = 1000 Ω·m) e dos guardas, são os valores usados nos módulos 14 e 15.")
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 2 – preenchimento do caso de referência", [
        ("Geometria da LT", "Altura do cabo guarda 1 (m)", "30", "Altura na estrutura do guarda mais alto"),
        ("Geometria da LT", "Distância horizontal entre guardas (m)", "6", "Aparece com 2 guardas"),
        ("Geometria da LT", "Guarda 2 abaixo do guarda 1 (m)", "0", "Diferença de cota"),
        ("Geometria da LT", "Distância horizontal (m) (+ direita / − esquerda)", "−4,5", "Fase A em relação ao guarda 1"),
        ("Geometria da LT", "Distância vertical abaixo do guarda (m)", "6", "A fica a 24 m"),
        ("Geometria da LT", "Distância horizontal A–B / B–C (m)", "4,5 / 4,5", "Arranjo horizontal"),
        ("Geometria da LT", "Flecha do condutor / do cabo guarda (m)", "0 / 0", "0 = altura na estrutura (premissa do treinamento)"),
        ("Geometria da LT", "Resistividade do solo (Ω·m)", "1000", "Retorno pelo solo (Carson)"),
        ("Catálogo de cabos", "Condutor de fase (catálogo)", "HAWK 477 MCM", "Conferir RMG, R_ca 75 °C e alertas"),
        ("Cálculo e relatório", "Comprimento da linha (km)", "80", "Herda do Módulo 1"),
        ("Cálculo e relatório", "Tensão nominal (kV) / Potência na carga (MVA) / FP", "138 / 60 / 0,95", "Herda do Módulo 1"),
        ("Circuito 1", "Linha transposta", "marcado", "Transposição afeta o método matricial"),
        ("Cálculo e relatório", "Botão \"Gerar relatório\"", "—", "Relatório com todas as equações e o script")])
    R.p("Resultado esperado: L = 1,3010 mH/km; C = 8,8817 nF/km; |Zo| = 390,67 Ω; tensão na carga 126,790 kV; regulação 9,416 %; perdas 2.508,93 kW; P/SIL = 1,146.")
    R.h2("Conferência")
    checklist(R, ["Altura das fases e distâncias conferem com o desenho da estrutura.",
                  "RMG do cabo cadastrado (senão o relatório registra a premissa Ds = 0,7788·r).",
                  "Alertas de importação do catálogo resolvidos (R_ca 75 °C ausente ou menor que R_cc 20 °C).",
                  "CELT2 × matricial dentro de 1 %; se maior, revisar altura média e solo.",
                  "P/SIL coerente com o comprimento (linhas curtas têm P/SIL alto; limites típicos do Livro 3)."])
    R.obs("O SIL e o P/SIL usam Ro = √(L/C); a impedância característica complexa Zo inclui a resistência.")


# ============================================================================= M3
def calc_m3():
    serie = [18.5, 21.0, 19.2, 22.4, 20.1, 23.0, 19.8, 21.7, 24.1, 20.6]
    n = len(serie)
    vm = sum(serie) / n
    s = math.sqrt(sum((v - vm) ** 2 for v in serie) / (n - 1))
    z = [-math.log(-math.log(i / (n + 1))) for i in range(1, n + 1)]
    c2 = sum(z) / n
    c1 = math.sqrt(sum((v - c2) ** 2 for v in z) / n)
    K = lambda T_: (-math.log(-math.log(1 - 1 / T_)) - c2) / c1
    ktur = 1.08                                 # Sul (SC), Tabela 8
    krug, kint30, alfa = 1.00, 1.22, 0.16        # categoria B (Tabelas 1, 9 e 3)
    h = 24.0
    kalt = (h / 10.0) ** alfa
    out = dict(serie=serie, n=n, vm=vm, s=s, c1=c1, c2=c2, ktur=ktur, kalt=kalt)
    casos = {}
    for nome, TR, integ in (("max", 50, "10 min"), ("v5030", 50, "30 s"), ("rajada", 150, "3 s"), ("freq", 10, "30 s"), ("manobra", 2, "30 s")):
        k = K(TR)
        vr = vm + k * s
        vp = ktur * vr
        if integ == "30 s":
            vp = kint30 * kalt * krug * vp
        elif integ == "3 s":
            vp = 1.15 * 1.41 * vp
        casos[nome] = dict(TR=TR, K=k, VR=vr, VP=vp)
    t_coinc, alt = 10.0, 870.0
    mu_ar = 1.225 * 288.15 / (t_coinc + 273.15) * math.exp(-1.2e-4 * alt)
    for c in casos.values():
        c["q0"] = 0.5 * mu_ar * c["VP"] ** 2
    out.update(casos=casos, mu=mu_ar)
    return out


def m3(R):
    x = calc_m3()
    c = x["casos"]
    R.h1("M3 – ESTUDO DOS VENTOS E TEMPERATURAS")
    R.h2("Objetivo e quando fazer")
    R.p("Determinar as velocidades de vento de projeto (máximo 10 min, vento 50/30 para a faixa, rajada de 3 s, frequência industrial e manobra), a pressão dinâmica "
        "de vento (q0) e as temperaturas de projeto (EDS, máxima, mínima e coincidente) a partir da série de máximos anuais do INMET, conforme a NBR 5422:2024.")
    R.p("Sempre que o projeto envolve balanço de cadeia, faixa de passagem, distâncias de segurança e cálculo mecânico. Os módulos 4 e 5 consomem este estudo.", "Quando é exigido:")
    R.h2("Normas e referências")
    R.lista(["ABNT NBR 5422:2024 – 4.9.4.1 (conversão da medição), A.2 e Tabela A.1 (Gumbel), 8.2.1.1 (V_P, Tabela 8 – Ktur), 8.2.2.1 (30 s, Tabela 9), "
             "8.2.3.4 (3 s, Tabela 2), 4.7 (massa específica do ar), 8.4.2 (pressão dinâmica); Tabelas 1 e 3 (Krug, α).",
             "Mínimo de 10 anos de série (NBR 5422:2024, 4.9.3.2.1). Períodos de retorno a definir pela transmissora (12.3.3.2)."])
    R.h2("Metodologia manual")
    R.p("Passo 1 – Série de máximos anuais. Converter a medição para vento de 10 min, 10 m, terreno categoria B (4.9.4.1) quando a estação mede em outra integração/altura/categoria; "
        "em seguida calcular média e desvio-padrão amostral (n−1).")
    EQ(R, V("V"), T("="), mfrac(V("V", "m"), V("K", "int") + V("K", "rug") + V("K", "alt")), T(" ;  "), V("K", "alt"), T("="), msup(mpar(mfrac(V("z", "med"), T("10"))), mi("α")))
    R.p("Passo 2 – Fator de frequência de Gumbel para n anos e período de retorno T:")
    EQ(R, V("z", "i"), T("=−ln"), mpar(T("−ln") + mpar(mfrac(V("i"), V("n") + T("+1")))), T(" ;  "), V("C", "2"), T("= média de "), V("z", "i"), T(" ;  "), V("C", "1"), T("= desv.-padrão de "), V("z", "i"))
    EQ(R, V("C", "T"), T("=−ln"), mpar(T("−ln") + mpar(T("1−") + mfrac(T("1"), V("T")))), T(" ;  "), V("K"), T("="), mfrac(V("C", "T") + T("−") + V("C", "2"), V("C", "1")), T(" ;  "), V("V", "R"), T("="), mi("v̄") + T("+") + V("K") + V("s"))
    R.p("Passo 3 – Vento de projeto (10 min) e conversões para 30 s e 3 s:")
    EQ(R, V("V", "P"), T("="), V("K", "tur"), V("V", "R"), T(" ;  "), V("V", "P30"), T("="), V("K", "int30"), V("K", "alt"), V("K", "rug"), V("V", "P"), T(" ;  "), V("V", "P3"), T("=1,15·"), V("K", "int3"), V("V", "P"))
    R.p("Passo 4 – Massa específica do ar (t = média das mínimas, alt = altitude média) e pressão dinâmica:")
    EQ(R, mi("μ"), T("="), T("1,225·"), mfrac(T("288,15"), V("t") + T("+273,15")), T("·exp"), mpar(T("−1,2·10") + msup(T(""), T("−4")) + T("·") + V("alt")), T(" ;  "), V("q", "0"), T("="), mfrac(T("1"), T("2")), mi("μ"), msup(V("V", "P"), T("2")))
    R.simbolos([("v̄, s", "média e desvio-padrão da série", "m/s"), ("K(T,n)", "fator de frequência de Gumbel", "—"), ("Ktur", "fator de turbulência regional (Tabela 8)", "—"),
                ("Kint, Krug, Kalt", "fatores de integração, rugosidade e altura", "—"), ("μ", "massa específica do ar", "kg/m³"), ("q0", "pressão dinâmica", "Pa")])
    R.p("Passo 5 – Temperaturas: EDS = média das 12 médias mensais (3.1.54, 4.3.1); T máx e T mín (2 % de excedência/ocorrência) e coincidente (média das mínimas) vêm do INMET.")
    R.h2("Exemplo resolvido – série ilustrativa (SC)")
    R.p("Série de máximos anuais (m/s, ilustrativa): " + "; ".join(f(v, 1) for v in x["serie"]) + ". Região Sul (Ktur = 1,08), terreno categoria B, estação já em 10 min/10 m, "
        "altura média das fases 24 m (Kalt = (24/10)^0,16), t coincidente = 10 °C e altitude 870 m. DADOS ILUSTRATIVOS: num projeto real usar a série do INMET.", italico=False)
    passos(R, "Estatísticas e Gumbel (n = 10)", [
        ("Média v̄ e desvio-padrão s (n−1)", f"v̄ = {f(x['vm'], 2)} m/s; s = {f(x['s'], 2)} m/s"),
        ("C1 e C2 (n = 10, Tabela A.1)", f"C1 = {f(x['c1'], 4)}; C2 = {f(x['c2'], 4)}"),
        ("K(50 anos)", f"{f(c['max']['K'], 3)}"),
        ("V_R(50) = v̄ + K·s", f"{f(x['vm'], 2)} + {f(c['max']['K'], 3)} × {f(x['s'], 2)} = {f(c['max']['VR'], 2)} m/s"),
        ("V_P (10 min) = Ktur·V_R", f"1,08 × {f(c['max']['VR'], 2)} = {f(c['max']['VP'], 2)} m/s"),
        ("Kalt = (24/10)^0,16", f"{f(x['kalt'], 4)}"),
        ("V_P30 = Kint30·Kalt·Krug·V_P", f"1,22 × {f(x['kalt'], 4)} × 1,00 × {f(c['max']['VP'], 2)} = {f(c['v5030']['VP'], 2)} m/s"),
        ("μ", f"1,225 × 288,15/283,15 × exp(−1,2e-4 × 870) = {f(x['mu'], 4)} kg/m³"),
        ("q0 = ½·μ·V_P30²", f"0,5 × {f(x['mu'], 4)} × {f(c['v5030']['VP'], 2)}² = {f(c['v5030']['q0'], 0)} Pa")])
    R.tabela("Casos de vento do exemplo", ["Caso", "TR (anos)", "K(T,n)", "V_R (m/s)", "V_P (m/s)", "q0 (Pa)"], [
        ["Vento máximo (10 min)", "50", f(c["max"]["K"], 3), f(c["max"]["VR"], 2), f(c["max"]["VP"], 2), f(c["max"]["q0"], 0)],
        ["Vento 50/30 (30 s)", "50", f(c["v5030"]["K"], 3), f(c["v5030"]["VR"], 2), f(c["v5030"]["VP"], 2), f(c["v5030"]["q0"], 0)],
        ["Rajada (3 s)", "150", f(c["rajada"]["K"], 3), f(c["rajada"]["VR"], 2), f(c["rajada"]["VP"], 2), f(c["rajada"]["q0"], 0)],
        ["Frequência industrial (30 s)", "10", f(c["freq"]["K"], 3), f(c["freq"]["VR"], 2), f(c["freq"]["VP"], 2), f(c["freq"]["q0"], 0)],
        ["Manobra (30 s)", "2", f(c["manobra"]["K"], 3), f(c["manobra"]["VR"], 2), f(c["manobra"]["VP"], 2), f(c["manobra"]["q0"], 0)]], [5.2, 2.0, 2.2, 2.4, 2.4, 2.8])
    comparacao(R, "Manual × app (Módulo 3)", [
        ("v̄ (m/s)", f(x["vm"], 2), "21,04", dif(x["vm"], 21.04)),
        ("s (m/s)", f(x["s"], 2), "1,76", dif(x["s"], 1.76)),
        ("μ (kg/m³)", f(x["mu"], 4), "1,1230", dif(x["mu"], 1.1230)),
        ("V_P (10 min) (m/s)", f(c["max"]["VP"], 2), "29,55", dif(c["max"]["VP"], 29.55)),
        ("V_P30 (m/s)", f(c["v5030"]["VP"], 2), "41,47", dif(c["v5030"]["VP"], 41.47)),
        ("q0 do vento 50/30 (Pa)", f(c["v5030"]["q0"], 0), "966", dif(c["v5030"]["q0"], 966)),
        ("V_P3 rajada 150 anos (m/s)", f(c["rajada"]["VP"], 2), "51,51", dif(c["rajada"]["VP"], 51.51))])
    R.p("O período de retorno do vento \"50/30\" pode ser alterado para 150 anos (campo TR do app) quando a transmissora ou a revisão da norma exigir; os demais fatores permanecem.")
    R.h2("Como preencher no app")
    app_tab(R, "Módulo 3 – preenchimento", [
        ("Estação INMET e local", "Estação INMET (nome) / Código da estação", "Florianópolis (ilustrativa) / A806", "Citado no relatório"),
        ("Estação INMET e local", "Município / UF do projeto", "Florianópolis / SC", "A UF define Ktur (Tabela 8): SC → Sul 1,08"),
        ("Estação INMET e local", "Latitude / Longitude (°)", "−27,6 / −48,5", "Sul e oeste negativos"),
        ("Estação INMET e local", "Altitude média do trecho (m)", "870", "Entra em μ"),
        ("Estação INMET e local", "Primeiro / último ano da série", "2015 / 2024", "Mínimo 10 anos"),
        ("Vento", "Como informar o vento do INMET", "Série de máximos anuais", "Ou \"Estatísticas\" (média e dispersão)"),
        ("Vento", "Unidade / Integração da medição / Categoria da estação / Altura de medição", "m/s / 10 min / B / 10 m", "Define Kint, Krug, Kalt da medição"),
        ("Vento", "Tabela de máximos anuais", "10 valores (ver acima)", "Um valor por ano"),
        ("Vento", "Categoria de terreno do projeto", "B", "Tabela 1"),
        ("Vento", "Usar altura média das fases da geometria (Módulo 2)", "marcado", "24 m"),
        ("Vento", "TR: máx. / 50/30 / rajada / freq. / manobra / extremo", "50 / 50 / 150 / 10 / 2 / 0", "Premissas da transmissora"),
        ("Temperaturas", "EDS a partir de", "Média das 12 médias mensais", "Digitar as 12 temperaturas"),
        ("Temperaturas", "T máx. / T mín. / T coincidente / média das máximas (°C)", "40 / 5 / 10 / 35", "INMET (2 %)"),
        ("Temperaturas", "CC máx. / emergência / PR máx. (°C)", "75 / 90 / 40", "Temperaturas de projeto de condutor e para-raios")])
    R.p("Resultado esperado: v̄ = 21,04 m/s; s = 1,76 m/s; V_P30 = 41,47 m/s; q0 (50/30) = 966 Pa; EDS = 20,85 °C.")
    R.h2("Conferência")
    checklist(R, ["Série com no mínimo 10 anos e mesma estação/período citado.",
                  "Integração e categoria da estação conferidas (altera Kint/Krug/Kalt).",
                  "UF correta (define Ktur).",
                  "TR por caso aprovado pela transmissora (50/30 ou 150/30).",
                  "Altura média das fases = altura usada no balanço (Módulo 2).",
                  "Nenhum aviso \"DADO NÃO INFORMADO\" restante antes de emitir o relatório."])
