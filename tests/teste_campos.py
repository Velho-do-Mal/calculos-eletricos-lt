"""Testes do motor de campos (M8): casos analíticos."""
import math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import calc_campos as cc

# 1) E de um condutor único sobre solo: E(0,y) = q/(2πε0)·(1/(y-h) − 1/(y+h)); q = V/(ln(2h/r)/(2πε0))
h, r, V = 10.0, 0.01, 10000.0
s = cc.Sistema([dict(x=0, y=h, req=r, V=V, I=0)], [], rho=100)
(e, b), = s.campos_fontes(np.array([0.0]), np.array([0.0]))
E_ref = V / math.log(2*h/r) * (2/ (2*h))  # solo: E = q/(2πε0)·2/(2h)... conferência abaixo
q = V*2*math.pi*cc.EPS0/math.log(2*h/r)
E_ana = q/(2*math.pi*cc.EPS0)*(1/h+1/h)
assert abs(abs(e[1][0]) - E_ana)/E_ana < 1e-9, (e[1][0], E_ana)

# 2) B de condutor único com solo perfeito (p=0): em x=0, y=0: B = μ0 I/(2π)·(1/h)·2 ... (imagem oposta dobra componente horizontal)
I = 100.0
s = cc.Sistema([dict(x=0, y=h, req=r, V=0, I=I)], [], rho=0)
(e, b), = s.campos_fontes(np.array([0.0]), np.array([0.0]))
B_ana = cc.MU0*I/(2*math.pi)*(2/h)
assert abs(abs(b[0][0]) - B_ana)/B_ana < 1e-9, (b, B_ana)

# 3) solo ρ=100: imagem profunda -> B próximo de μ0 I/(2π h) (condutor isolado no ar) a poucos %, com p≈ 41 m·(1-j)
s = cc.Sistema([dict(x=0, y=h, req=r, V=0, I=I)], [], rho=100)
(e, b), = s.campos_fontes(np.array([0.0]), np.array([0.0]))
B_ar = cc.MU0*I/(2*math.pi*h)
assert 0.7*B_ar < abs(b[0][0]) < 1.6*B_ar

# 4) Linha trifásica 138 kV horizontal 3 m, h=12 m, 500 A: B ~ pico central coerente (ordem de µT)
fases=[(-3,'A'),(0,'B'),(3,'C')]
est=[dict(x=x,y=12.0,req=0.011,V=cc.tensao_fase(138,f),I=cc.corrente_fase(500,f),tipo='fase',fase=f) for x,f in fases]
r_ = cc.calcular_ponto(est, [], -50, 50, 1.0, 1.5, rho=100, semi_faixa=15)
print("E_max kV/m", round(r_['E_max'],3), "B_max µT", round(r_['B_max'],3), "borda", r_['E_borda'], r_['B_borda'])
assert 0.5 < r_['E_max'] < 3.0 and 2 < r_['B_max'] < 15
# 5) vizinha paralela em pior caso >= isolada
viz=[dict(nome="V1", modo="paralelo", x0=25.0, conds=[dict(x=x,y=14.0,req=0.011,V=cc.tensao_fase(138,f),I=cc.corrente_fase(300,f),fase=f) for x,f in fases])]
r2 = cc.calcular_ponto(est, viz, -50, 50, 1.0, 1.5, rho=100)
assert r2['B_max'] >= r_['B_max']*0.99 and r2['E_max'] >= r_['E_max']*0.99
print("com vizinha:", round(r2['E_max'],3), round(r2['B_max'],3), r2['B_theta'])
print("OK")

# 6) estudo completo
import pontos as PT
fases=[dict(nome=f"{f}1",x=x,y=24.0,circuito=1,fase=f,req=0.0135) for x,f in [(-3.5,'A'),(0,'B'),(3.5,'C')]]
viz=dict(nome="LT vizinha", tensao=138.0, corrente_normal=300.0, corrente_emergencia=400.0, relacao="Paralelismo", lado="Direito",
         dist_eixos=30.0, disp="Horizontal", n_circ=1, esp_h=3.5, esp_v=0, h_min=20.0, seq="ABC", sentido="Mesmo sentido da LT em estudo", defas_modo="Pior caso (automático)", defas=0)
viz2=dict(viz, nome="Cruz", relacao="Travessia", ang_trav=60.0, dist_v=8.0, pos_rel="LT em estudo cruza por cima")
e=dict(fases=fases,guardas=[dict(x=0,y=30,req=0.005)],incluir_guardas_e=False,circs={"1":dict(un_kv=138,umax_kv=145,i_normal=420,i_emerg=500,fp=0.95,status="Energizado")},
 tensao_modo="Nominal",h_min=12.0,h_obs=1.5,x_min=-50,x_max=50,dx=1.0,rho=100,freq=60,semi_faixa=15.0,req_viz=0.012,
 pontos=[dict(nome="Livre",tipo=PT.T_LIVRE,cen_i="Normal",dist_h=0,alt_ref=1.5,publico="Público em geral",vizinhas=[]),
         dict(nome="Par",tipo=PT.T_PAR,cen_i="Emergência",dist_h=0,alt_ref=1.5,publico="Público em geral",vizinhas=[viz]),
         dict(nome="Trav",tipo=PT.T_TRAV,cen_i="Normal",dist_h=0,alt_ref=1.5,publico="Público em geral",vizinhas=[viz2]),
         dict(nome="Casa",tipo=PT.T_EDIF,cen_i="Normal",dist_h=20,alt_ref=1.5,publico="Público em geral",vizinhas=[])])
import json; json.dumps(e)
R = cc.calcular_estudo(e)
assert not R["erros"]
for p in R["pontos"]:
    for cn, d in p["cenarios"].items():
        print(p["nome"], cn, round(d["E_max"],2), round(d["B_max"],2), d["E_ref"] and round(d["E_ref"],3), d["B_ref"] and round(d["B_ref"],3), d["ok_E"], d["ok_B"])
    assert "s3d_E" in p["cenarios"][p["cen_i"]]
json.dumps(R)
print("OK estudo")
