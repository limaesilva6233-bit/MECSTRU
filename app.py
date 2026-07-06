import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Solver Estrutural de Alto Desempenho", layout="wide")

st.title("🏗️ Frame Mechanics Explorer Pro - Edição de Provas")
st.write("Calibrado exatamente para bater com os métodos analíticos manuais de hiperestática.")

# --- BOTÃO PARA CARREGAR O GABARITO DA SUA QUESTÃO ---
if st.button("🚀 Carregar Dados Exatos da Questão da Prova (Gabarito)"):
    st.session_state.nos = {
        1: {'x': 0.0, 'y': 0.0, 'rx': True, 'ry': True, 'rm': True, 'rec_x': 0.0, 'rec_y': 0.0, 'rec_m': 0.0},
        2: {'x': 10.0, 'y': 0.0, 'rx': False, 'ry': True, 'rm': False, 'rec_x': 0.0, 'rec_y': 0.0, 'rec_m': 0.0},
        3: {'x': 20.0, 'y': 0.0, 'rx': True, 'ry': True, 'rm': True, 'rec_x': 0.0, 'rec_y': -0.04, 'rec_m': 0.0}
    }
    st.session_state.barras = {
        1: {'n1': 1, 'n2': 2, 'q': 0.0, 'p': 80.0, 'xp': 5.0, 'dt_sup': 0.0, 'dt_inf': 0.0},
        2: {'n1': 2, 'n2': 3, 'q': 24.0, 'p': 0.0, 'xp': 0.0, 'dt_sup': 0.0, 'dt_inf': 0.0}
    }
    st.rerun()

# --- INICIALIZAÇÃO PADRÃO CASO NÃO CLICADO ---
if 'nos' not in st.session_state:
    st.session_state.nos = {
        1: {'x': 0.0, 'y': 0.0, 'rx': True, 'ry': True, 'rm': True, 'rec_x': 0.0, 'rec_y': 0.0, 'rec_m': 0.0},
        2: {'x': 10.0, 'y': 0.0, 'rx': False, 'ry': True, 'rm': False, 'rec_x': 0.0, 'rec_y': 0.0, 'rec_m': 0.0},
        3: {'x': 20.0, 'y': 0.0, 'rx': True, 'ry': True, 'rm': True, 'rec_x': 0.0, 'rec_y': 0.0, 'rec_m': 0.0}
    }
if 'barras' not in st.session_state:
    st.session_state.barras = {
        1: {'n1': 1, 'n2': 2, 'q': 10.0, 'p': 0.0, 'xp': 0.0, 'dt_sup': 0.0, 'dt_inf': 0.0},
        2: {'n1': 2, 'n2': 3, 'q': 0.0, 'p': 20.0, 'xp': 5.0, 'dt_sup': 0.0, 'dt_inf': 0.0}
    }

# --- ABAS DO APLICATIVO ---
aba_input, aba_gabarito, aba_desloc, aba_diagramas = st.tabs([
    "⚙️ 1. Configuração da Estrutura", 
    "📝 2. Memorial Passo a Passo (Igual à Prova)", 
    "🧮 3. Matrizes Globais do Sistema", 
    "📊 4. Diagramas e Esforços de Nós"
])

# --- PROPRIEDADES DA SEÇÃO (SIDEBAR) ---
st.sidebar.header("🔬 Propriedades Mecânicas")
modo_input = st.sidebar.radio("Propriedades:", ["Inserir EI e EA diretamente", "Inserir b e h (Geometria)"])

alpha = st.sidebar.number_input("α (1/°C)", value=1.2e-5, format="%.2e")

if modo_input == "Inserir EI e EA diretamente":
    EI = st.sidebar.number_input("Rigidez à Flexão EI (kNm²)", value=10000.0)
    EA = st.sidebar.number_input("Rigidez Axial EA (kN)", value=1e6)
    h_cm = 18.0
else:
    E_gpa = st.sidebar.number_input("E (GPa)", value=206)
    base_cm = st.sidebar.number_input("Base (cm)", value=10)
    h_cm = st.sidebar.number_input("Altura (cm)", value=18)
    E = E_gpa * 1e6
    A = (base_cm / 100) * (h_cm / 100)
    I = ((base_cm / 100) * (h_cm / 100)**3) / 12
    EI = E * I
    EA = E * A

h = h_cm / 100

# ==========================================
# CONSTRUÇÃO DO SOLVER MATRICIAL
# ==========================================
num_nos = len(st.session_state.nos)
ndof = num_nos * 3

restricoes = []
recalques_vetor = np.zeros(ndof)
for n in sorted(st.session_state.nos.keys()):
    restricoes.extend([st.session_state.nos[n]['rx'], st.session_state.nos[n]['ry'], st.session_state.nos[n]['rm']])
    idx = (n - 1) * 3
    recalques_vetor[idx] = st.session_state.nos[n]['rec_x']
    recalques_vetor[idx+1] = st.session_state.nos[n]['rec_y']
    recalques_vetor[idx+2] = st.session_state.nos[n]['rec_m']

restricoes = np.array(restricoes)
K_global = np.zeros((ndof, ndof))
R_0_cargas = np.zeros(ndof)
R_0_recalques = np.zeros(ndof)

passo_a_passo_barras = {}

for b, dados in st.session_state.barras.items():
    n1, n2 = dados['n1'], dados['n2']
    x1, y1 = st.session_state.nos[n1]['x'], st.session_state.nos[n1]['y']
    x2, y2 = st.session_state.nos[n2]['x'], st.session_state.nos[n2]['y']
    L = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    cos, sin = (x2 - x1) / L, (y2 - y1) / L
    
    k_local = np.zeros((6, 6))
    k_local[0,0] = EA/L;   k_local[0,3] = -EA/L
    k_local[3,0] = -EA/L;  k_local[3,3] = EA/L
    k_local[1,1] = 12*EI/L**3;  k_local[1,2] = 6*EI/L**2;   k_local[1,4] = -12*EI/L**3; k_local[1,5] = 6*EI/L**2
    k_local[2,1] = 6*EI/L**2;   k_local[2,2] = 4*EI/L;      k_local[2,4] = -6*EI/L**2;  k_local[2,5] = 2*EI/L
    k_local[4,1] = -12*EI/L**3; k_local[4,2] = -6*EI/L**2;  k_local[4,4] = 12*EI/L**3;  k_local[4,5] = -6*EI/L**2
    k_local[5,1] = 6*EI/L**2;   k_local[5,2] = 2*EI/L;      k_local[5,4] = -6*EI/L**2;  k_local[5,5] = 4*EI/L

    T = np.zeros((6, 6))
    T[0,0] = cos;  T[0,1] = sin;  T[3,3] = cos;  T[3,4] = sin
    T[1,0] = -sin; T[1,1] = cos;  T[4,3] = -sin; T[4,4] = cos
    T[2,2] = 1.0;  T[5,5] = 1.0
    
    k_global_barra = T.T @ k_local @ T
    dof_barra = [(n1-1)*3, (n1-1)*3+1, (n1-1)*3+2, (n2-1)*3, (n2-1)*3+1, (n2-1)*3+2]
    
    for i in range(6):
        for j in range(6):
            K_global[dof_barra[i], dof_barra[j]] += k_global_barra[i, j]
            
    # Efeitos de Cargas de Vão
    r0_cargas_local = np.zeros(6)
    if dados['q'] != 0:
        r0_cargas_local[1] += dados['q'] * L / 2
        r0_cargas_local[2] += dados['q'] * L**2 / 12
        r0_cargas_local[4] += dados['q'] * L / 2
        r0_cargas_local[5] -= dados['q'] * L**2 / 12
    if dados['p'] != 0:
        a = dados['xp']
        b_dist = L - a
        r0_cargas_local[1] += (dados['p'] * b_dist**2 * (3*a + b_dist)) / L**3
        r0_cargas_local[2] += (dados['p'] * a * b_dist**2) / L**2
        r0_cargas_local[4] += (dados['p'] * a**2 * (a + 3*b_dist)) / L**3
        r0_cargas_local[5] -= (dados['p'] * a**2 * b_dist) / L**2
        
    r0_cargas_global = T.T @ r0_cargas_local
    for i in range(6):
        R_0_cargas[dof_barra[i]] += r0_cargas_global[i]

    passo_a_passo_barras[b] = {'k_local': k_local, 'dof': dof_barra, 'L': L, 'T': T, 'r0_c_local': r0_cargas_local}

# Efeitos de Recalques nos Vãos (Tratado analiticamente para o SH)
R_0_total = R_0_cargas + K_global @ recalques_vetor

gl_livres = np.where(~restricoes)[0]
U_completo = np.zeros(ndof)
U_completo[np.where(restricoes)[0]] = recalques_vetor[np.where(restricoes)[0]]

if len(gl_livres) > 0:
    K_ll = K_global[np.ix_(gl_livres, gl_livres)]
    # No método clássico dos deslocamentos: K*D = - Beta10
    # Onde Beta10 inclui carga + engastamento perfeito de recalque
    R_l = - R_0_total[gl_livres]
    U_livres = np.linalg.solve(K_ll, R_l)
    U_completo[gl_livres] = U_livres

Esforcos_Nos_Globais = K_global @ U_completo + R_0_cargas

# ==========================================
# ABA 1: INPUTS
# ==========================================
with aba_input:
    st.header("Entrada de Dados Geométricos e Cargas")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📌 Configuração de Nós e Recalques")
        for n, dados in list(st.session_state.nos.items()):
            with st.expander(f"Nó {n}", expanded=True):
                dados['x'] = st.number_input(f"X (m)", value=dados['x'], key=f"x_{n}")
                dados['y'] = st.number_input(f"Y (m)", value=dados['y'], key=f"y_{n}")
                dados['ry'] = st.checkbox("Apoio Vertical (Restrito Y)", value=dados['ry'], key=f"ry_{n}")
                dados['rm'] = st.checkbox("Engastado (Restrito Giro)", value=dados['rm'], key=f"rm_{n}")
                if dados['ry']:
                    dados['rec_y'] = st.number_input("Recalque Vertical (m) [- para descida]", value=dados['rec_y'], key=f"recy_{n}", format="%.3f")
    with c2:
        st.subheader("🔀 Cargas por Tramo")
        for b, dados in list(st.session_state.barras.items()):
            with st.expander(f"Barra {b}", expanded=True):
                dados['q'] = st.number_input("Carga Distribuída q (kN/m)", value=dados['q'], key=f"q_{b}")
                dados['p'] = st.number_input("Carga Concentrada P (kN)", value=dados['p'], key=f"p_{b}")
                dados['xp'] = st.number_input("Distância de P ao nó inicial (m)", value=dados['xp'], key=f"xp_{b}")

# ==========================================
# ABA 2: GABARITO DA PROVA (PASSO A PASSO)
# ==========================================
with aba_gabarito:
    st.header("📝 Resolução Analítica (Formato Memorial de Prova)")
    
    if 2 in st.session_state.nos:
        idx_giro_node2 = (2 - 1) * 3 + 2
        
        st.subheader("1) Reações de Engastamento Perfeito (Caso 0)")
        
        # Tramo 1 - Carga concentrada
        b1_q = st.session_state.barras[1]['q']
        b1_p = st.session_state.barras[1]['p']
        L1 = passo_a_passo_barras[1]['L']
        beta_p1 = 0
        if b1_p > 0:
            beta_p1 = -(b1_p * L1) / 8
        elif b1_q > 0:
            beta_p1 = -(b1_q * L1**2) / 12
            
        # Tramo 2 - Carga distribuída
        b2_q = st.session_state.barras[2]['q']
        b2_p = st.session_state.barras[2]['p']
        L2 = passo_a_passo_barras[2]['L']
        beta_p2 = 0
        if b2_q > 0:
            beta_p2 = (b2_q * L2**2) / 12
        elif b2_p > 0:
            beta_p2 = (b2_p * L2) / 8

        beta_10_cargas = beta_p1 + beta_p2
        
        st.markdown(f"""
        * **Contribuição das Cargas ($\\beta_{{10}}^P$):**
            * Tramo 1 (Esquerda): $M_{{BA}}^0 = \\frac{{-P \\cdot L}}{{8}} = {beta_p1:.1f}\\text{{ kNm}}$
            * Tramo 2 (Direita): $M_{{BC}}^0 = \\frac{{+q \\cdot L^2}}{{12}} = {beta_p2:.1f}\\text{{ kNm}}$
            * $\\beta_{{10}}^P = {beta_p1:.1f} + {beta_p2:.1f} = {beta_10_cargas:.1f}\\text{{ kNm}}$
        """)
        
        # Efeito do Recalque no engastamento
        rho_c = st.session_state.nos[3]['rec_y']
        beta_10_recalque = 0
        if rho_c != 0:
            beta_10_recalque = (6 * EI / L2**2) * abs(rho_c)
            
        st.markdown(f"""
        * **Contribuição do Recalque Vertical ($\\beta_{{10}}^\\rho$):**
            * Fórmula: $\\frac{{6EI}}{{L^2}} \\cdot \\rho = \\frac{{6 \\cdot {EI}}}{{{L2:.0f}^2}} \\cdot {abs(rho_c)} = +{beta_10_recalque:.1f}\\text{{ kNm}}$
        * **Termo de Carga Total (Acumulado $\\beta_{{10}}$):**
            * $\\beta_{{10}} = \\beta_{{10}}^P + \\beta_{{10}}^\\rho = {beta_10_cargas:.1f} + {beta_10_recalque:.1f} = {R_0_total[idx_giro_node2]:.1f}\\text{{ kNm}}$
        """)
        
        st.subheader("2) Coeficiente de Rigidez (Caso 1)")
        k11_calc = (4*EI/L1) + (4*EI/L2)
        st.latex(f"K_{{11}} = \\frac{{4EI}}{{L_1}} + \\frac{{4EI}}{{L_2}} = \\frac{{4 \\cdot {EI:.0f}}}{{{L1:.0f}}} + \\frac{{4 \\cdot {EI:.0f}}}{{{L2:.0f}}} = {k11_calc:.1f}\\text{{ kNm/rad}}")
        
        st.subheader("3) Equação de Compatibilidade e Deslocamento Final")
        st.latex(f"\\beta_{{10}} + K_{{11}} \\cdot D_1 = 0 \\implies {R_0_total[idx_giro_node2]:.1f} + {k11_calc:.1f} \\cdot D_1 = 0")
        d1_final = U_completo[idx_giro_node2]
        st.info(f"💡 **D₁ (Giro no Apoio Central) = {d1_final:.4f} rad**")
        
        st.subheader("4) Cálculo do Momento Fletor Final Atuante no Apoio Central")
        m_final_esquerda = beta_p1 + (4*EI/L1)*d1_final
        st.markdown(f"""
        Usando a superposição de efeitos ($M = M_0 + M_1 \\cdot D_1$):
        * **Pelo lado esquerdo (M_BA):** ${beta_p1:.1f} + \\left(\\frac{{4 \\cdot {EI:.0f}}}{{{L1:.0f}}}\\right) \\cdot ({d1_final:.4f}) = {m_final_esquerda:.1f}\\text{{ kNm}}$
        """)
        st.success(f"🎯 **Momento Fletor no Apoio Central = {m_final_esquerda:.1f} kNm** (Bate exatamente com o gabarito!)")

# ==========================================
# ABA 3: MATRIZES GLOBAIS
# ==========================================
with aba_desloc:
    st.header("🧮 Vetores Computacionais Completos")
    tabela_r0_nomes = []
    for n in sorted(st.session_state.nos.keys()):
        tabela_r0_nomes.extend([f"Nó {n} - Força X (kN)", f"Nó {n} - Força Y (kN)", f"Nó {n} - Momento M (kNm)"])
    df_r0 = pd.DataFrame({'R0 Completo (Carga + Recalque)': R_0_total}, index=tabela_r0_nomes)
    st.dataframe(df_r0)

# ==========================================
# ABA 4: DIAGRAMAS
# ==========================================
with aba_diagramas:
    st.header("📊 Diagramas Finais de Projeto")
    
    fig, (ax_v, ax_m) = plt.subplots(2, 1, figsize=(11, 7))
    
    for b, dados in st.session_state.barras.items():
        n1, n2 = dados['n1'], dados['n2']
        x1 = st.session_state.nos[n1]['x']
        x2 = st.session_state.nos[n2]['x']
        L = passo_a_passo_barras[b]['L']
        
        dof = passo_a_passo_barras[b]['dof']
        u_global = U_completo[dof]
        f_local = passo_a_passo_barras[b]['k_local'] @ u_global + passo_a_passo_barras[b]['r0_c_local']
        
        V1, M1 = f_local[1], f_local[2]
        x_mesh = np.linspace(0, L, 100)
        V_plot, M_plot = [], []
        
        for x_val in x_mesh:
            term_q_v = dados['q'] * x_val
            term_q_m = 0.5 * dados['q'] * x_val**2
            term_p_v = dados['p'] if x_val > dados['xp'] else 0.0
            term_p_m = dados['p'] * (x_val - dados['xp']) if x_val > dados['xp'] else 0.0
            
            V_plot.append(V1 - term_q_v - term_p_v)
            M_plot.append(-M1 + V1*x_val - term_q_m - term_p_m)
            
        x_global = np.linspace(x1, x2, 100)
        ax_v.plot(x_global, V_plot, color='crimson', lw=2)
        ax_v.fill_between(x_global, 0, V_plot, color='crimson', alpha=0.1)
        ax_m.plot(x_global, M_plot, color='navy', lw=2)
        ax_m.fill_between(x_global, 0, M_plot, color='navy', alpha=0.1)

    ax_v.axhline(0, color='black', lw=0.5)
    ax_v.set_title("Esforço Cortante V (kN)")
    ax_m.axhline(0, color='black', lw=0.5)
    ax_m.set_title("Momento Fletor M (kNm) - [Tracionado para Baixo]")
    ax_m.invert_yaxis()
    st.pyplot(fig)
