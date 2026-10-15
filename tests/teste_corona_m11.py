import sys; sys.path.insert(0, "/home/claude/bk_lt")
import math, calc_efeito_corona as ce
# Referência: 500 kV, 4×ACSR (r=1,5 cm... ) apenas sanidade: δ=1, D=12 m, r=1.5 cm, n=1 -> Uc = 84*0.85*1.5*log10(1200/1.5)=311 kV
uc, vc, rp = ce.tensao_critica(1.0, 0.85, 1.0, 1, 1.5, 0, 12.0)
assert abs(uc - 84*0.85*1.5*math.log10(800)) < 1e-6, uc
assert ce.perda_peek(100, 120, 1, 60, 1.5, 12) == 0
p = ce.perda_peek(100, 90, 1, 60, 1.5, 12.0); assert p > 0, p
print("Uc", round(uc,1), "P", round(p,4)); 
# chuva reduz Vc
assert ce.tensao_critica(1.0, 0.85, 0.8, 1, 1.5, 0, 12.0)[1] < vc
# feixe 3x: r' > r
assert ce.r_equiv_feixe(3, 1.5, 40) > 1.5
print("corona M11 motor OK")
