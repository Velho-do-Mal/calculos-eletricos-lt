import sys, cmath, math; sys.path.insert(0,"/home/claude/bk_lt")
import calc_parametros as cp
c=cp.celt2(0.0183,0.0072,0.2032,3.8,3.8,7.6,80.0,60.0,vs_kv=138.0,sc_kva=60000,fp=0.95)["carga"]
print("fonte",c["Vo_kV"],"carga",round(c["Vc_kV"],3),"reg",round(c["regulacao_pct"],3),"Vo_pi",round(c["Vo_pi_kV"],4))
assert c["Vo_kV"]==138.0 and c["Vc_kV"]<138.0 and abs(c["Vo_pi_kV"]-138.0)<1e-6
# volta: com a tensão calculada na carga no modo direto, a fonte tem de dar 138
d=cp.celt2(0.0183,0.0072,0.2032,3.8,3.8,7.6,80.0,60.0,vc_kv=c["Vc_kV"],sc_kva=60000,fp=0.95)["carga"]
assert abs(d["Vo_kV"]-138.0)<1e-6,d["Vo_kV"]
print("ida e volta OK")
