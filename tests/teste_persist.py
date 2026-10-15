from streamlit.testing.v1 import AppTest
def kk(at,k):
    v=at.session_state["_ver"] if "_ver" in at.session_state else 0
    return k+(f"_v{v}" if v else "")

at = AppTest.from_file("/home/claude/bk_lt/app.py", default_timeout=60); at.run()
at.radio(key="modulo_sel").set_value("🌬️  3. Estudo dos Ventos").run()
at.number_input(key=kk(at,"k_3_t_max")).set_value(37.5).run()
at.radio(key="modulo_sel").set_value("📐  4. Faixa de Domínio").run()
at.radio(key="modulo_sel").set_value("🌬️  3. Estudo dos Ventos").run()
v = at.number_input(key=kk(at,"k_3_t_max")).value
assert v == 37.5, v
# Limpar restaura o padrão
at.button(key="clr3").click().run()
assert at.number_input(key=kk(at,"k_3_t_max")).value == 40.0
assert not at.exception
print("persistência OK")
