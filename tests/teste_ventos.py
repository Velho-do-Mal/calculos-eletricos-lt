import sys; sys.path.insert(0,"/home/claude/bk_lt")
import calc_ventos as cv
vm=62.53/3.6; s=vm*0.13
casos=[dict(nome="max",TR=50,integracao="10 min"),dict(nome="50/30",TR=50,integracao="30 s"),dict(nome="rajada150",TR=150,integracao="3 s"),
       dict(nome="freq30",TR=30,integracao="30 s"),dict(nome="manobra",TR=2,integracao="30 s"),dict(nome="ext250",TR=250,integracao="10 min")]
r=cv.estudo(dict(v_med=vm,s=s,n=18,regiao="Sudeste",cat="B",h_cabo=10,alt=870,t_coinc=10,casos=casos))
esp={"max":27.608,"50/30":33.68176,"rajada150":49.10135,"freq30":32.165056,"manobra":23.2821,"ext250":31.5168}
for c in r["casos"]:
    print(c["nome"], round(c["VP"],3), esp[c["nome"]]); assert abs(c["VP"]-esp[c["nome"]])<0.06, c["nome"]
print("mu",r["mu"]); assert abs(r["mu"]-1.1231)<0.001
print("C1,C2 n=18",r["c1"],r["c2"]); assert abs(r["c1"]-1.0481)<1e-4 and abs(r["c2"]-0.5198)<1e-4
# Tabela A.2 da norma (n=10)
for T,ex in ((2,-0.136),(10,1.848),(30,3.042),(50,3.587),(150,4.751),(250,5.291)):
    k=cv.fator_freq(T,10); print(T,round(k,3),ex); assert abs(k-ex)<0.003
print("ventos OK")
