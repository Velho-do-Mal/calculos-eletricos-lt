import sys, datetime as dt
sys.path.insert(0, "/home/claude/bk_lt")
import calc_ventos as cv, relatorio_m3 as r3
d = dict(modo="Estatísticas", unid="km/h", v_med=62.53, tipo_disp="Coeficiente de variação (%)", s=13, n=18, integ_med="10 min",
         cat_est="B", z_med=10, uf="SP", alt=870, eds_modo="Média das 12 médias mensais",
         meses=[{"t": x} for x in (22.5,23,22,20,17.5,16,15.5,17,18,19.5,20.5,22)], t_max=36.5, t_min=3.2, t_coinc=10.8, t_med_max=33.4,
         usar_h_geo=False, h_cabo=22, cat="B", est_nome="MIRANTE DE SANTANA", est_cod="A701", municipio="São Paulo", lat=-23.5, lon=-46.6,
         serie_ini=2005, serie_fim=2023)
res = cv.montar(d)
print(res["ok"], res["pendencias"], res["avisos"])
out = "/tmp/claude-0/-home-claude/9d4270f2-2b3e-52a5-b0a9-d0d02b207d6f/scratchpad/m3.docx"
r3.gerar(out, dict(nome="LT 138 kV Exemplo", data=dt.date.today(), resp="M. Knopp"), d, res)
print("ok", out)
