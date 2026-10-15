import sys, math; sys.path.insert(0,"/home/claude/bk_lt")
import calc_parametros as cp
r = cp.celt2(0.0169,0.0064,0.206,3.310966626228661,1.7,3.310966626228661,100,vc_kv=72,sc_kva=1000,fp=1.0)
c=r["carga"]
print(r["L_mH_km"], r["C_nF_km"], abs(r["Zo"]), math.degrees(__import__("cmath").phase(r["Zo"])))
print(r["alfa_km"]*100, r["beta_km"]*100, r["Ro"])
print(c["Vo_kV"], c["Vo_pi_kV"], c["Io_A"], c["Io_ang"], c["Po_kW"], c["perdas_kW"], c["perdas_pct"], c["regulacao_pct"], c["Pc_SIL"], r["Ec_kV_cm"], r["v_ms"])
print("pi", r["pi"]["Zs"], r["pi"]["Yp"])
assert abs(r["L_mH_km"]-1.2052987)<1e-6 and abs(r["C_nF_km"]-9.664147)<1e-5
assert abs(abs(r["Zo"])-370.05)<0.01 and abs(c["regulacao_pct"]-0.40566)<1e-3
assert abs(c["perdas_kW"]-8.6706)<1e-3 and abs(r["Ec_kV_cm"]-8.5576)<1e-3
assert abs(r["pi"]["Zs"]-complex(20.4865,45.3391))<1e-3 and abs(r["pi"]["Yp"].imag-0.000182)<1e-6
assert abs(c["Vo_kV"]-c["Vo_pi_kV"])<1e-6
print("CELT2 OK")
# matricial: mesmo circuito (A,B,C) com distâncias reais; compara com CELT2
x=[-1.655,1.655,1.655]; 
def ph(nome,c,f,x,h): return dict(nome=nome,circuito=c,fase=f,x=x,h=h,r=0.00845,ds=0.00685,req=0.00845,R=0.2032)
def gd(n,x,h): return dict(nome=n,x=x,h=h,r=0.0055,ds=0.0043,req=0.0055,R=2.79)
# circuito duplo vertical, lados opostos (x=-3 e +3), alturas 26/23/20, guardas h=30 em x=-2.5 e 2.5
F=[ph("A1",1,"A",-3,26),ph("B1",1,"B",-3,23),ph("C1",1,"C",-3,20),
   ph("A2",2,"A",3,26),ph("B2",2,"B",3,23),ph("C2",2,"C",3,20)]
G=[gd("G1",-2.5,30),gd("G2",2.5,30)]
Z,C=cp.matrizes(F,G,rho=1000)
Zs,Cs,r=cp.sequencias(Z,C,[[0,1,2],[3,4,5]])
for k,v in r.items(): print(k,{a:(complex(round(b.real,5),round(b.imag,5)) if isinstance(b,complex) else round(b,5)) for a,b in v.items()})
# simples (circuito 1 só) para comparar com CELT2
Z1,C1=cp.matrizes(F[:3],G,rho=1000); _,_,r1=cp.sequencias(Z1,C1,[[0,1,2]])
print("simples",r1["c1"]["Z1"], r1["c1"]["C1"]*1e9)
Deq=(3*3*6)**(1/3); import math
print("CELT2 L=",2e-7*math.log(Deq/0.00685)*1000*1e3, "C=",2*math.pi*cp.EPS0/math.log(Deq/0.00845)*1e9*1000)
d=cp.desempenho_pi(r["c1"]["Z1"],r["c1"]["C1"],80,138,60000,0.95)
print(d["pi"]["Zs"], d["pi"]["Yp"], d["regulacao_pct"], d["perdas_pct"])
