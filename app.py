import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Solver Estrutural Didático", layout="wide")

st.title("🏗️ Frame Mechanics Explorer Pro - Edição Acadêmica")
st.write("Seu aliado interativo com passo a passo conceitual completo para passar na matéria de estruturas!")

# --- INICIALIZAÇÃO DE VARIÁVEIS NA SESSÃO ---
if 'nos' not in st.session_state:
    st.session_state.nos = {
        1: {'x': 0.0, 'y': 0.0, 'rx': True, 'ry': True, 'rm': True, 'rec_x': 0.0, 'rec_y': 0.0, 'rec_m': 0.0},
        2: {'x': 5.0, 'y': 0.0, 'rx': False, 'ry': True, 'rm': False, 'rec_x': 0.0, 'rec_y': 0.0, 'rec_m': 0.0},
        3: {'x': 10.0, 'y': 0.0, 'rx': False, 'ry': True, 'rm': False, 'rec_x': 0.0, 'rec_y': 0.0, 'rec_m': 0.0}
    }
if 'barras' not in st.session_state:
    st.session_state.barras = {
        1: {'n1': 1, 'n2': 2, 'q': 10.0, 'p': 0.0, 'xp': 2.5, 'dt_sup': 0.0, 'dt_inf': 0.0},
        2: {'n1': 2, 'n2': 3, 'q': 0.0, 'p': 20.0, 'xp': 2.5, 'dt_sup': 0.0, 'dt_inf': 0.0}
    }

# --- ABAS DO APLICATIVO ---
aba_input, aba_desloc, aba_forcas_ptv, aba_passo, aba_diagramas = st.tabs([
    "⚙️ 1. Modelagem, Cargas e Efeitos", 
    "🧮 2. M. Deslocamentos & Rigidez Direta", 
    "📐 3. M. Forças & PTV (Conceitual)",
    "📖 4. Explicação Passo a Passo",
    "📊 5. Diagramas e Esforços nos Nós"
])

# --- PROPRIEDADES GLOBAIS (SIDEBAR) ---
st.sidebar.header("🔬 Propriedades do Material e Seção")
modo_input = st.sidebar.radio("Como deseja inserir as propriedades?", ["Inserir b e h (Geometria)", "Inserir EI e EA diretamente"])

alpha = st.sidebar.number_input("Coeficiente de Dilatação α (1/°C)", value=1.2e-5, format="%.2e")
h_cm = 50.0 # valor padrão para cálculo térmico se digitado direto

if modo_input == "Inserir b e h (Geometria)":
    E_gpa = st.sidebar.number_input("Módulo de Elasticidade E (GPa)", value=206)
    E = E_gpa * 1e6 # kN/m²
    base_cm = st.sidebar.number_input("Base da Seção Retangular (cm)", value=10)
    h_cm = st.sidebar.number_input("Altura da Seção Retangular (cm)", value=18)
    
    A = (base_cm / 100) * (h_cm / 100)
    I = ((base_cm / 100) * (h_cm / 100)**3) / 12
    EI = E * I
    EA = E * A
else:
    EI = st.sidebar.number_input("Rigidez à Flexão EI (kNm²)", value=10011.60)
    EA = st.sidebar.number_input("Rigidez Axial EA (kN)", value=3708000.00)
    h_cm = st.sidebar.number_input("Altura equivalente da seção para efeito térmico (cm)", value=18.0)

h = h_cm / 100

st.sidebar.markdown(f"""
**Valores Utilizados no Solver:**
* **Rigidez à Flexão (EI):** {EI:.2f} kNm²
* **Rigidez Axial (EA):** {EA:.2f} kN
""")

# ==========================================
# ABA 1: CONFIGURAÇÃO DA ESTRUTURA
# ==========================================
with aba_input:
    st.header("Configuração de Nós e Conectividade")
    col_nos, col_barras = st.columns(2)
    
    with col_nos:
        st.subheader("📌 Coordenadas e Apoios (Nós)")
        for n, dados in list(st.session_state.nos.items()):
            with st.expander(f"Nó {n}", expanded=True):
                c1, c2, c3 = st.columns(3)
                dados['x'] = c1.number_input(f"X (m)", value=dados['x'], key=f"nx_{n}")
                dados['y'] = c2.number_input(f"Y (m)", value=dados['y'], key=f"ny_{n}")
                
                cx, cy, cm = st.columns(3)
                dados['rx'] = cx.checkbox("Restrito X", value=dados['rx'], key=f"rx_{n}")
                dados['ry'] = cy.checkbox("Restrito Y", value=dados['ry'], key=f"ry_{n}")
                dados['rm'] = cm.checkbox("Restrito Giro (M)", value=dados['rm'], key=f"rm_{n}")
                
                if dados['rx']: dados['rec_x'] = cx.number_input("Recalque X (m)", value=dados['rec_x'], key=f"recx_{n}", step=0.001, format="%.3f")
                if dados['ry']: dados['rec_y'] = cy.number_input("Recalque Y (m)", value=dados['rec_y'], key=f"recy_{n}", step=0.001, format="%.3f")
                if dados['rm']: dados['rec_m'] = cm.number_input("Recalque Giro (rad)", value=dados['rec_m'], key=f"recm_{n}", step=0.001, format="%.3f")

    with col_barras:
        st.subheader("🔀 Elementos (Barras) e Cargas")
        for b, dados in list(st.session_state.barras.items()):
            with st.expander(f"Barra {b}", expanded=True):
                c1, c2 = st.columns(2)
                dados['n1'] = c1.number_input("Nó Inicial", value=dados['n1'], min_value=1, max_value=len(st.session_state.nos), key=f"bn1_{b}")
                dados['n2'] = c2.number_input("Nó Final", value=dados['n2'], min_value=1, max_value=len(st.session_state.nos), key=f"bn2_{b}")
                
                cc1, cc2, cc3 = st.columns(3)
                dados['q'] = cc1.number_input("Carga Distr. q (kN/m)", value=dados['q'], key=f"bq_{b}")
                dados['p'] = cc2.number_input("Carga Pontual P (kN)", value=dados['p'], key=f"bp_{b}")
                dados['xp'] = cc3.number_input("Posição de P (m)", value=dados['xp'], key=f"bxp_{b}")
                
                st.write("**Gradiente Térmico:**")
                ct1, ct2 = st.columns(2)
                dados['dt_sup'] = ct1.number_input("ΔT Face Sup. (°C)", value=dados['dt_sup'], key=f"dts_{b}")
                dados['dt_inf'] = ct2.number_input("ΔT Face Inf. (°C)", value=dados['dt_inf'], key=f"dti_{b}")

    cb1, cb2, cb3, cb4 = st.columns(4)
    if cb1.button("➕ Adicionar Nó"):
        novo_id = max(st.session_state.nos.keys()) + 1
        st.session_state.nos[novo_id] = {'x': float(novo_id*5-5), 'y': 0.0, 'rx': False, 'ry': True, 'rm': False, 'rec_x': 0.0, 'rec_y': 0.0, 'rec_m': 0.0}
        st.rerun()
    if cb2.button("❌ Remover Último Nó") and len(st.session_state.nos) > 2:
        st.session_state.nos.pop(max(st.session_state.nos.keys()))
        st.rerun()
    if cb3.button("➕ Adicionar Barra"):
        novo_id = max(st.session_state.barras.keys()) + 1
        st.session_state.barras[novo_id] = {'n1': novo_id, 'n2': novo_id+1, 'q': 0.0, 'p': 0.0, 'xp': 0.0, 'dt_sup': 0.0, 'dt_inf': 0.0}
        st.rerun()
    if cb4.button("❌ Remover Última Barra") and len(st.session_state.barras) > 1:
        st.session_state.barras.pop(max(st.session_state.barras.keys()))
        st.rerun()

# ==========================================
# MOTOR MATRICIAL DE RIGIDEZ (SOLVER)
# ==========================================
num_nos = len(st.session_state.nos)
ndof = num_nos * 3

restricoes = []
recalques_vetor = np.zeros(ndof)
for n in sorted(st.session_state.nos.keys()):
    idx = (n - 1) * 3
    restricoes.extend([st.session_state.nos[n]['rx'], st.session_state.nos[n]['ry'], st.session_state.nos[n]['rm']])
    recalques_vetor[idx] = st.session_state.nos[n]['rec_x']
    recalques_vetor[idx+1] = st.session_state.nos[n]['rec_y']
    recalques_vetor[idx+2] = st.session_state.nos[n]['rec_m']

restricoes = np.array(restricoes)
K_global = np.zeros((ndof, ndof))
R_0 = np.zeros(ndof)
passo_a_passo_barras = {}

for b, dados in st.session_state.barras.items():
    n1, n2 = dados['n1'], dados['n2']
    x1, y1 = st.session_state.nos[n1]['x'], st.session_state.nos[n1]['y']
    x2, y2 = st.session_state.nos[n2]['x'], st.session_state.nos[n2]['y']
    L = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    cos = (x2 - x1) / L
    sin = (y2 - y1) / L
    
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
            
    r0_local = np.zeros(6)
    if dados['q'] != 0:
        r0_local[1] += dados['q'] * L / 2
        r0_local[2] += dados['q'] * L**2 / 12
        r0_local[4] += dados['q'] * L / 2
        r0_local[5] -= dados['q'] * L**2 / 12
    if dados['p'] != 0:
        a = dados['xp']
        b_dist = L - a
        r0_local[1] += (dados['p'] * b_dist**2 * (3*a + b_dist)) / L**3
        r0_local[2] += (dados['p'] * a * b_dist**2) / L**2
        r0_local[4] += (dados['p'] * a**2 * (a + 3*b_dist)) / L**3
        r0_local[5] -= (dados['p'] * a**2 * b_dist) / L**2
    if dados['dt_sup'] != 0 or dados['dt_inf'] != 0:
        dT_media = (dados['dt_sup'] + dados['dt_inf']) / 2
        dT_gradiente = dados['dt_inf'] - dados['dt_sup']
        N_termico = alpha * dT_media * EA
        r0_local[0] += N_termico
        r0_local[3] -= N_termico
        M_termico = alpha * dT_gradiente * EI / h
        r0_local[2] -= M_termico
        r0_local[5] += M_termico

    r0_global = T.T @ r0_local
    for i in range(6):
        R_0[dof_barra[i]] += r0_global[i]
        
    passo_a_passo_barras[b] = {'k_local': k_local, 'r0_local': r0_local, 'dof': dof_barra, 'L': L, 'T': T}

F_ext = np.zeros(ndof)
R_direito = F_ext - R_0 - K_global @ recalques_vetor
gl_livres = np.where(~restricoes)[0]

U_completo = recalques_vetor.copy()
if len(gl_livres) > 0:
    K_ll = K_global[np.ix_(gl_livres, gl_livres)]
    R_l = R_direito[gl_livres]
    try:
        U_completo[gl_livres] = np.linalg.solve(K_ll, R_l)
    except np.linalg.linalg.LinAlgError:
        st.error("Estrutura Instável!")

# Reações e forças nodais finais combinadas
Esforcos_Nos_Globais = K_global @ U_completo + R_0

# ==========================================
# ABA 2: PASSO A PASSO MÉTODO DOS DESLOCAMENTOS
# ==========================================
with aba_desloc:
    st.header("🧮 Vetores Globais de Cálculo")
    
    # Adicionando rótulos explícitos para facilitar o entendimento da imagem 1
    st.subheader("2. Reações de Engastamento Perfeito Acumuladas ($R_0$) - Mapeado por Graus de Liberdade")
    st.write("Cada trinca de linhas corresponde aos esforços equivalentes ($F_x, F_y, M$) de cada nó da estrutura:")
    
    tabela_r0_nomes = []
    for n in sorted(st.session_state.nos.keys()):
        tabela_r0_nomes.extend([f"Nó {n} - Força X (kN)", f"Nó {n} - Força Y (kN)", f"Nó {n} - Momento Fletor (kNm)"])
    
    import pandas as pd
    df_r0 = pd.DataFrame({'Esforço Equivalente': R_0}, index=tabela_r0_nomes)
    st.dataframe(df_r0)
    
    st.subheader("3. Matriz de Rigidez Global do Sistema ($K_{global}$)")
    st.dataframe(np.round(K_global, 1))

# ==========================================
# ABA 3: M. FORÇAS CONCEITUAL
# ==========================================
with aba_forcas_ptv:
    st.header("📐 Grau de Hiperestaticidade")
    b_qtd = len(st.session_state.barras)
    r_qtd = int(np.sum(restricoes))
    n_qtd = len(st.session_state.nos)
    grau_hiper = r_qtd + 3*b_qtd - 3*n_qtd
    st.latex(f"d = R + 3B - 3N = {r_qtd} + 3({b_qtd}) - 3({n_qtd}) = {grau_hiper}")

# ==========================================
# ABA 4: EXPLICAÇÃO PASSO A PASSO DIDÁTICO
# ==========================================
with aba_passo:
    st.header("📖 Guia Didático: Como este problema é resolvido na mão?")
    st.write("Aqui está a receita de bolo que seu professor cobra na prova escrita do Método dos Deslocamentos:")
    
    st.markdown("""
    ### 1º Passo: Fixar a Estrutura (Sistema Hipergeométrico)
    Na teoria, nós bloqueamos todas as rotações e translações livres dos nós adicionando "vínculos fictícios". No seu modelo, os nós que não possuem apoios rígidos reais são considerados como graus de liberdade ativos.
    
    ### 2º Passo: Determinar as Reações de Engastamento Perfeito ($R_0$)
    Para cada barra isolada e totalmente engastada nas pontas, calculamos os momentos e forças gerados exclusivamente pelas cargas de vão, temperatura e recalques.
    * **Carga Distribuída $q$:** Gera uma reação vertical de $\\frac{qL}{2}$ e momentos de $\\frac{qL^2}{12}$ nas extremidades.
    * **Variação de Temperatura:** Se a temperatura muda de forma desigual, ela gera momentos fletores de engastamento perfeito calculados por: $M_{term} = \\frac{\\alpha \\cdot \\Delta T \\cdot EI}{h}$.
    
    ### 3º Passo: Montar a Matriz de Rigidez ($K$)
    A matriz de rigidez mede a força necessária para provocar um deslocamento unitário em cada nó. Usamos as tabelas clássicas de rigidez de vigas engastadas-engastadas:
    * Rigidez ao giro: $\\frac{4EI}{L}$ no nó onde gira, e transmite $\\frac{2EI}{L}$ para a outra ponta.
    * Rigidez à translação: $\\frac{12EI}{L^3}$ com momento associado de $\\frac{6EI}{L^2}$.
    
    ### 4º Passo: Resolver as Equações de Equilíbrio
    Montamos o sistema linear clássico:
    $$ [K] \\cdot \{U\} = \{F_{ext}\} - \{R_0\} $$
    Onde as incógnitas $\{U\}$ são os deslocamentos reais e rotações que você precisa descobrir!
    """)

# ==========================================
# ABA 5: DIAGRAMAS E RESULTADOS NOS NÓS
# ==========================================
with aba_diagramas:
    st.header("📊 Esforços Finais e Esforços nos Nós")
    
    st.subheader("📍 Esforços Totais Atuantes em Cada Nó (Equilíbrio e Continuidade)")
    st.write("Estes são os valores de **Força Cortante, Força Axial e Momento Fletor** combinados exatamente nos nós da sua estrutura:")
    
    for n in sorted(st.session_state.nos.keys()):
        idx = (n - 1) * 3
        with st.expander(f"Esforços Finais no Nó {n}", expanded=True):
            c_e1, c_e2, c_e3 = st.columns(3)
            c_e1.metric(label="Força Horizontal Fx", value=f"{Esforcos_Nos_Globais[idx]:.2f} kN")
            c_e2.metric(label="Força Vertical Fy", value=f"{Esforcos_Nos_Globais[idx+1]:.2f} kN")
            c_e3.metric(label="Momento Fletor M", value=f"{Esforcos_Nos_Globais[idx+2]:.2f} kNm")

    # Reconstrução e desenho dos diagramas
    fig, (ax_n, ax_v, ax_m) = plt.subplots(3, 1, figsize=(11, 10))
    for b, dados in st.session_state.barras.items():
        n1, n2 = dados['n1'], dados['n2']
        x1, y1 = st.session_state.nos[n1]['x'], st.session_state.nos[n1]['y']
        x2, y2 = st.session_state.nos[n2]['x'], st.session_state.nos[n2]['y']
        L = passo_a_passo_barras[b]['L']
        cos, sin = (x2 - x1) / L, (y2 - y1) / L
        T = passo_a_passo_barras[b]['T']
        
        dof = passo_a_passo_barras[b]['dof']
        u_global = U_completo[dof]
        u_local = T @ u_global
        f_local = passo_a_passo_barras[b]['k_local'] @ u_local + passo_a_passo_barras[b]['r0_local']
        
        N1, V1, M1 = f_local[0], f_local[1], f_local[2]
        x_mesh = np.linspace(0, L, 50)
        N_plot, V_plot, M_plot = [], [], []
        
        for x_val in x_mesh:
            term_q_v = dados['q'] * x_val
            term_q_m = 0.5 * dados['q'] * x_val**2
            term_p_v = dados['p'] if x_val > dados['xp'] else 0.0
            term_p_m = dados['p'] * (x_val - dados['xp']) if x_val > dados['xp'] else 0.0
            
            N_plot.append(-N1)
            V_plot.append(V1 - term_q_v - term_p_v)
            M_plot.append(-M1 + V1*x_val - term_q_m - term_p_m)
            
        x_global_plot = np.linspace(x1, x2, 50)
        ax_n.plot(x_global_plot, N_plot, color='teal', lw=2)
        ax_n.fill_between(x_global_plot, 0, N_plot, color='teal', alpha=0.1)
        ax_n.axhline(0, color='black', lw=0.5)
        ax_n.set_title("Diagrama de Esforço Normal N (kN)")
        
        ax_v.plot(x_global_plot, V_plot, color='crimson', lw=2)
        ax_v.fill_between(x_global_plot, 0, V_plot, color='crimson', alpha=0.1)
        ax_v.axhline(0, color='black', lw=0.5)
        ax_v.set_title("Diagrama de Esforço Cortante V (kN)")
        
        ax_m.plot(x_global_plot, M_plot, color='navy', lw=2)
        ax_m.fill_between(x_global_plot, 0, M_plot, color='navy', alpha=0.1)
        ax_m.axhline(0, color='black', lw=0.5)
        ax_m.set_title("Diagrama de Momento Fletor M (kNm) [Positivo para Baixo]")

    ax_m.invert_yaxis()
    st.pyplot(fig)
