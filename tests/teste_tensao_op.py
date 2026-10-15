import sys; sys.path.insert(0, "/home/claude/bk_lt")
import calc_tensao_operativa as to, calc_isolamento as ci
# Um máximo por distância: distância requerida de Um=145 deve devolver Um≈145
import math
d = ci.d_ft_ff(145.0, 0.9, 1.45)
assert abs(to.um_max_por_distancia(d, 0.9, 1.45) - 145.0) < 0.01
print("tensao_op OK")
