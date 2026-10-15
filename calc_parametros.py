"""
Módulo 2 – Parâmetros elétricos de linhas de transmissão (funções puras, sem Streamlit).

Dois métodos, ambos por circuito:

1) MÉTODO CELT2 (referência; circuito simples, linha idealmente transposta, sem retorno por terra)
   Reproduz a planilha "CELT2-IPOG – cálculo elétrico de LTs":
     Deq = (Dab·Dbc·Dca)^(1/3)
     L   = 2e-7·ln(Deq/Ds)·1000                [H/km]
     C   = 2π·ε / ln(2·Deq/d) ·1000            [F/km],   ε = εr·1e-9/(36π)
     ZL = R + jωL ; YL = G + jωC ; Zo = √(ZL/YL) ; γ = √(ZL·YL)
     Modelo π equivalente:  Zs = Zo·senh(γl) ;  Yp = (1/Zo)·tanh(γl/2)   (em cada extremidade)
     SIL = V²/Ro, Ro = √(L/C);  Ec = Q/(2π·ε·r);  v = ω/β ;  λ = 2π/β

2) MÉTODO MATRICIAL COM ACOPLAMENTO (circuito simples ou duplo)
   - Impedâncias série por Carson (profundidade complexa de penetração, p = √(ρ/(jωμ0))):
        Zii = Ri + jωμ0/2π · ln(2(hi+p)/Dsi)
        Zij = jωμ0/2π · ln( √((hi+hj+2p)²+xij²) / dij )
   - Capacitâncias por coeficientes de potencial de Maxwell, com imagens:
        Pii = 1/(2πε0)·ln(2hi/req_i) ;  Pij = 1/(2πε0)·ln(Dij'/dij) ;  C = P⁻¹
   - Cabos guarda aterrados em todas as torres: eliminação de Kron (Schur) em Z e em P.
   - Componentes simétricas (A = [1 1 1; 1 a² a; 1 a a²]): Zseq = A⁻¹·Z·A.
     Z1, Z0 (próprio), Z1m, Z0m (mútua entre circuitos), C1, C0, C1m, C0m.
   O acoplamento entre circuitos aparece em Z1m/Z0m e nas assimetrias (termos fora da diagonal
   dentro do circuito, por falta de transposição).

Referências (acervo do projeto): Carson (1926); Stevenson, Elementos de Análise de Sistemas de Potência;
Fuchs/Labegalini, Linhas de Transmissão; Checa, Líneas de Transporte de Energía (caps. de parâmetros);
ABNT NBR 5422 (projeto de LT) para as premissas de projeto. Páginas a confirmar na edição do acervo.
"""
import cmath
import math

import numpy as np

MU0 = 4e-7 * math.pi
EPS0 = 1e-9 / (36 * math.pi)          # F/m (valor usado na CELT2)
A_OP = cmath.exp(2j * math.pi / 3)
A_MAT = np.array([[1, 1, 1], [1, A_OP ** 2, A_OP], [1, A_OP, A_OP ** 2]], dtype=complex)


# --------------------------------------------------------------------------- feixes
def feixe(r, ds, n, a):
    """Raio e Ds equivalentes de um feixe regular de n subcondutores espaçados de a (todas em m)."""
    if n <= 1:
        return r, ds
    R = a / (2 * math.sin(math.pi / n))
    return (n * r * R ** (n - 1)) ** (1 / n), (n * ds * R ** (n - 1)) ** (1 / n)


def resolver_carga(vs_kv, S_va, Zo, gl):
    """Tensão na carga (fase, V, complexa) para tensão FIXA na fonte (vs_kv, linha) e carga de potência constante S_va (trifásica).
    Resolve  Vs = Vr·cosh(γl) + Ir·Zo·senh(γl),  Ir = conj(S/(3·Vr)),  por ponto fixo (referência: Vs em 0°)."""
    vs = vs_kv * 1000 / math.sqrt(3)
    ch, sh = cmath.cosh(gl), cmath.sinh(gl)
    vr = vs / ch
    for _ in range(500):
        ir = (S_va / (3 * vr)).conjugate() if vr != 0 else 0j
        novo = (vs - ir * Zo * sh) / ch
        if abs(novo - vr) < 1e-9 * abs(vs):
            return novo
        vr = novo
    raise ValueError("A carga informada não tem solução com a tensão fixa na fonte (acima da capacidade da linha).")


def _fonte_fixa(out, vs_kv, ang):
    """Reapresenta o resultado com a FONTE como referência (Vs fixa, 0°); a tensão na carga é o resultado calculado."""
    k = out["carga"] if "carga" in out else out
    k["Vs_kV"] = vs_kv
    k["Vc_ang"] = -ang
    for nome in ("Io_ang", "Ic_ang", "So_ang"):
        if nome in k:
            k[nome] = k[nome] - ang
    k["Vo_ang"] = 0.0
    k["Vo_kV"] = vs_kv


# --------------------------------------------------------------------------- método CELT2
def celt2(d_m, ds_m, R_km, D_ab, D_bc, D_ca, comp_km, f=60.0, er=1.0, g_km=0.0,
          vc_kv=None, sc_kva=None, fp=1.0, zc=None, fonte=None, vs_kv=None):
    """
    Parâmetros e desempenho de um circuito pelo método da planilha CELT2.
    d_m: diâmetro equivalente (m) ; ds_m: Ds equivalente (m) ; R_km: Ω/km (por fase, já com feixe).
    Carga: (vc_kv tensão de linha na carga, sc_kva potência trifásica, fp indutivo) OU zc (Ω/fase).
    vs_kv: tensão de linha FIXA na fonte (nominal); neste modo a tensão na carga é calculada (sc_kva e fp obrigatórios).
    """
    Deq = (D_ab * D_bc * D_ca) ** (1 / 3)
    w = 2 * math.pi * f
    eps = er * EPS0
    L = 2e-7 * math.log(Deq / ds_m) * 1000                    # H/km
    C = 2 * math.pi * eps / math.log(2 * Deq / d_m) * 1000    # F/km
    ZL = complex(R_km, w * L)
    YL = complex(g_km, w * C)
    Zo = cmath.sqrt(ZL / YL)
    gam = cmath.sqrt(ZL * YL)                                 # 1/km
    gl = gam * comp_km
    Ro = math.sqrt(L / C)
    out = dict(Deq=Deq, L_mH_km=L * 1e3, C_nF_km=C * 1e9, R_km=R_km, ZL=ZL, YL=YL, Zo=Zo, gamma=gam,
               alfa_km=gam.real, beta_km=gam.imag, gl=gl, Ro=Ro, comp_km=comp_km, f=f,
               v_ms=w / gam.imag * 1000, lambda_km=2 * math.pi / gam.imag)
    # Modelo π equivalente (obrigatório no relatório)
    Zs = Zo * cmath.sinh(gl)
    Yp = cmath.tanh(gl / 2) / Zo
    out["pi"] = dict(Zs=Zs, Yp=Yp, Y_total=2 * Yp,
                     Zs_nominal=ZL * comp_km, Yp_nominal=YL * comp_km / 2,
                     A=1 + Zs * Yp, B=Zs, C=2 * Yp + Zs * Yp ** 2, D=1 + Zs * Yp)
    # Linha curta (referência)
    out["curta"] = dict(Zs=ZL * comp_km)

    if vs_kv and sc_kva:
        S_va = sc_kva * 1000 * complex(fp, math.sqrt(max(0, 1 - fp * fp)))
        vc_c = resolver_carga(vs_kv, S_va, Zo, gl)
        vc_kv = abs(vc_c) * math.sqrt(3) / 1000
    if vc_kv:
        vc = vc_kv * 1000 / math.sqrt(3)
        if sc_kva:
            S = sc_kva * 1000 * complex(fp, math.sqrt(max(0, 1 - fp * fp)))
            Ic = (S / (3 * vc)).conjugate()
        elif zc:
            Ic = vc / zc
            S = 3 * vc * Ic.conjugate()
        else:
            Ic, S = 0j, 0j
        vo = vc * cmath.cosh(gl) + Ic * Zo * cmath.sinh(gl)
        io = vc * cmath.sinh(gl) / Zo + Ic * cmath.cosh(gl)
        So = 3 * vo * io.conjugate()
        v_vazio = vc / cmath.cosh(gl)                          # tensão na fonte para recepção em aberto → V∞ no extremo
        v_rec_vazio = abs(vo) / abs(cmath.cosh(gl))
        Pc, Po = S.real / 1000, So.real / 1000
        out["carga"] = dict(
            Vc_kV=vc_kv, Ic=Ic, Ic_abs=abs(Ic), Ic_ang=math.degrees(cmath.phase(Ic)), S_kVA=abs(S) / 1000,
            Sc=S, Pc_kW=Pc,
            Vo_kV=abs(vo) * math.sqrt(3) / 1000, Vo_ang=math.degrees(cmath.phase(vo)),
            Io_A=abs(io), Io_ang=math.degrees(cmath.phase(io)),
            So_kVA=abs(So) / 1000, So_ang=math.degrees(cmath.phase(So)), Po_kW=Po, Qo_kvar=So.imag / 1000,
            perdas_kW=Po - Pc, perdas_pct=(Po - Pc) / Po * 100 if Po else 0.0,
            V_vazio_kV=v_rec_vazio * math.sqrt(3) / 1000,
            regulacao_pct=(v_rec_vazio * math.sqrt(3) / 1000 - vc_kv) / vc_kv * 100,
            SIL_kW=(vc_kv * 1000) ** 2 / Ro / 1000, Pc_SIL=Pc / ((vc_kv * 1000) ** 2 / Ro / 1000),
        )
        # Verificação pelo modelo π (deve coincidir com a linha longa exata)
        Ir = Ic
        Vs_pi = vc * (1 + Zs * Yp) + Zs * Ir
        out["carga"]["Vo_pi_kV"] = abs(Vs_pi) * math.sqrt(3) / 1000
        if vs_kv and sc_kva:
            _fonte_fixa(out, vs_kv, out["carga"]["Vo_ang"])
            sil = (vs_kv * 1000) ** 2 / Ro / 1000
            out["carga"]["SIL_kW"], out["carga"]["Pc_SIL"] = sil, Pc / sil
    # Campo na superfície do condutor (feixe): Ec = Q / (2π ε r)
    v_nom = vs_kv or vc_kv
    if v_nom:
        Q = C / 1000 * v_nom * 1000 / math.sqrt(3)             # C/m
        out["Ec_kV_cm"] = Q / (2 * math.pi * eps * d_m / 2) * 1e-5
        out["Q_mC_km"] = C * (v_nom * 1000 / math.sqrt(3)) * 1e3
    return out


# --------------------------------------------------------------------------- método matricial
def _profundidade_complexa(rho, f):
    return cmath.sqrt(rho / (1j * 2 * math.pi * f * MU0))


def matrizes(fases, guardas, f=60.0, rho=1000.0):
    """
    fases: lista de dicts {nome, circuito, fase, x, h, r, ds, R, req, n}  (m, m, m, m, Ω/km)
           r/ds/req já são os equivalentes do feixe; R em Ω/km por fase (feixe).
    guardas: lista de dicts {nome, x, h, r, ds, R}  (aterrados).
    Retorna Z (Ω/km, nxn), Cmat (F/km, nxn) já reduzidos pelos guardas, na ordem de 'fases'.
    """
    w = 2 * math.pi * f
    p = _profundidade_complexa(rho, f)
    k = 1j * w * MU0 / (2 * math.pi) * 1000                    # Ω/km por unidade de ln
    cond = list(fases) + list(guardas)
    n = len(cond)
    Z = np.zeros((n, n), dtype=complex)
    P = np.zeros((n, n))
    for i, a in enumerate(cond):
        for j, b in enumerate(cond):
            dx = a["x"] - b["x"]
            if i == j:
                Z[i, i] = a["R"] + k * cmath.log(2 * (a["h"] + p) / a["ds"])
                P[i, i] = math.log(2 * a["h"] / a["req"]) / (2 * math.pi * EPS0)
            else:
                d = math.hypot(dx, a["h"] - b["h"])
                Di = cmath.sqrt((a["h"] + b["h"] + 2 * p) ** 2 + dx * dx)
                Z[i, j] = k * cmath.log(Di / d)
                dimg = math.hypot(dx, a["h"] + b["h"])
                P[i, j] = math.log(dimg / d) / (2 * math.pi * EPS0)
    nf = len(fases)
    if guardas:
        Zpp, Zpg, Zgp, Zgg = Z[:nf, :nf], Z[:nf, nf:], Z[nf:, :nf], Z[nf:, nf:]
        Z = Zpp - Zpg @ np.linalg.solve(Zgg, Zgp)
        Ppp, Ppg, Pgp, Pgg = P[:nf, :nf], P[:nf, nf:], P[nf:, :nf], P[nf:, nf:]
        P = Ppp - Ppg @ np.linalg.solve(Pgg, Pgp)
    C = np.linalg.inv(P) * 1000                                # F/km (P em m/F → C em F/m → ×1000)
    return Z, C


def sequencias(Z, C, ordem):
    """
    ordem: lista de listas com os índices (em Z/C) de A, B, C de cada circuito: [[iA1,iB1,iC1],[iA2,iB2,iC2]].
    Devolve Zseq, Cseq (matrizes 3nc x 3nc) com blocos [circ][seq 0,1,2] e dicionário de grandezas.
    """
    nc = len(ordem)
    idx = [i for c in ordem for i in c]
    Zp = Z[np.ix_(idx, idx)]
    Cp = C[np.ix_(idx, idx)]
    T = np.zeros((3 * nc, 3 * nc), dtype=complex)
    for c in range(nc):
        T[3 * c:3 * c + 3, 3 * c:3 * c + 3] = A_MAT
    Ti = np.linalg.inv(T)
    Zs, Cs = Ti @ Zp @ T, Ti @ Cp @ T
    r = {}
    for c in range(nc):
        b = 3 * c
        r[f"c{c + 1}"] = dict(
            Z0=Zs[b, b], Z1=Zs[b + 1, b + 1], Z2=Zs[b + 2, b + 2],
            C0=Cs[b, b].real, C1=Cs[b + 1, b + 1].real, C2=Cs[b + 2, b + 2].real,
            # assimetria interna (falta de transposição): maior termo fora da diagonal / Z1
            assim_Z=max(abs(Zs[b + i, b + j]) for i in range(3) for j in range(3) if i != j) / abs(Zs[b + 1, b + 1]),
            assim_C=max(abs(Cs[b + i, b + j]) for i in range(3) for j in range(3) if i != j) / abs(Cs[b + 1, b + 1]))
    if nc == 2:
        r["mutua"] = dict(Z0m=Zs[0, 3], Z1m=Zs[1, 4], Z2m=Zs[2, 5], C0m=Cs[0, 3].real, C1m=Cs[1, 4].real,
                          acoplamento_Z1=abs(Zs[1, 4]) / math.sqrt(abs(Zs[1, 1]) * abs(Zs[4, 4])),
                          acoplamento_Z0=abs(Zs[0, 3]) / math.sqrt(abs(Zs[0, 0]) * abs(Zs[3, 3])))
    return Zs, Cs, r


def desempenho_pi(Z1, C1, comp_km, vs_kv, sc_kva, fp, f=60.0, g_km=0.0):
    """Linha longa e modelo π a partir de Z1 (Ω/km, complexo) e C1 (F/km).
    vs_kv é a tensão FIXA na fonte (nominal); a tensão na carga (Vc_kV) é calculada."""
    w = 2 * math.pi * f
    Y = complex(g_km, w * C1)
    Zo = cmath.sqrt(Z1 / Y)
    gam = cmath.sqrt(Z1 * Y)
    gl = gam * comp_km
    Zs, Yp = Zo * cmath.sinh(gl), cmath.tanh(gl / 2) / Zo
    S = sc_kva * 1000 * complex(fp, math.sqrt(max(0, 1 - fp * fp)))
    vc = resolver_carga(vs_kv, S, Zo, gl)
    vc_kv = abs(vc) * math.sqrt(3) / 1000
    vc = abs(vc)                                   # referência temporária: Vc em 0° (ângulos corrigidos ao final)
    Ic = (S / (3 * vc)).conjugate()
    vo = vc * cmath.cosh(gl) + Ic * Zo * cmath.sinh(gl)
    io = vc * cmath.sinh(gl) / Zo + Ic * cmath.cosh(gl)
    So = 3 * vo * io.conjugate()
    Ro = math.sqrt(abs(Z1.imag / w) / C1)
    vvz = abs(vo) / abs(cmath.cosh(gl)) * math.sqrt(3) / 1000
    Pc, Po = S.real / 1000, So.real / 1000
    sil = (vs_kv * 1000) ** 2 / Ro / 1000
    ang = math.degrees(cmath.phase(vo))
    return dict(Vc_kV=vc_kv, Vs_kV=vs_kv, Vc_ang=-ang, Zo=Zo, gamma=gam, gl=gl, alfa_km=gam.real, beta_km=gam.imag, Ro=Ro,
                L_mH_km=Z1.imag / w * 1e3, R_km=Z1.real, C_nF_km=C1 * 1e9,
                pi=dict(Zs=Zs, Yp=Yp, Y_total=2 * Yp, Zs_nominal=Z1 * comp_km, Yp_nominal=Y * comp_km / 2),
                Ic=Ic, Vo_kV=vs_kv, Vo_ang=0.0,
                Io_A=abs(io), Io_ang=math.degrees(cmath.phase(io)) - ang, So_kVA=abs(So) / 1000, Po_kW=Po,
                Pc_kW=Pc, perdas_kW=Po - Pc, perdas_pct=(Po - Pc) / Po * 100 if Po else 0.0,
                V_vazio_kV=vvz, regulacao_pct=(vvz - vc_kv) / vc_kv * 100, SIL_kW=sil, Pc_SIL=Pc / sil,
                v_ms=w / gam.imag * 1000, lambda_km=2 * math.pi / gam.imag)
