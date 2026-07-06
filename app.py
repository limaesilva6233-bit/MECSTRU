import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Solver Estrutural Didático", layout="wide")

st.title("🏗️ Frame Mechanics Explorer Pro")
st.write("Seu aliado interativo para o último semestre de Engenharia Civil. Domine Isostática, Hiperestática e Métodos Matriciais.")

# --- INICIALIZAÇÃO DE VARIÁVEIS NA SESSÃO ---
if 'nos' not in st.session_state:
    # Estrutura padrão: Uma viga contínua de 3 nós (2 barras de 5 metros)
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
aba_input, aba_desloc, aba_forcas_ptv, aba_diagramas = st.tabs([
    "⚙️ 1. Modelagem, Cargas e Efeitos", 
    "🧮 2. M. Deslocamentos & Rigidez Direta", 
    "📐 3. M. Forças & PTV (Conceitual)",
    "📊 4. Diagramas Finais (Sinais Civis)"
])

# --- PROPRIEDADES GLOBAIS (SIDEBAR) ---
st.sidebar.header("🔬 Propriedades do Material e Seção")
E_gpa = st.sidebar.number_input("Módulo de Elasticidade E (GPa)", value=210)
E = E_gpa * 1e6 # kN/m²
base_cm = st.sidebar.number_input("Base da Seção Retangular (cm)", value=20)
h_cm = st.sidebar.number_input("Altura da Seção Retangular (cm)", value=50)
alpha = st.sidebar.number_input("Coeficiente de Dilatação α (1/°C)", value=1.2e-5, format="%.2e")

# Cálculos geométricos da seção
A = (base_cm / 100) * (h_cm / 100)
I = ((base_cm / 100) * (h_cm / 100)**3) / 12
h = h_cm / 100

st.sidebar.markdown(f"""
**Propriedades Calculadas:**
*   **Área (A):** {A:.4f} m²
*   **Inércia (I):** {I:.6f} m⁴
*   **Rigidez à Flexão (EI):** {E*I:.2f} kNm²
*   **Rigidez Axial (EA):** {E*A:.2f} kN
""")

# ==========================================
# ABA 1: CONFIGURAÇÃO DA ESTRUTURA
# ==========================================
with aba_input:
    st.header("Configuração de Nós e Conectividade")
    
    col_nos, col_barras = st.columns(2)
    
    with col_nos:
        st.subheader("📌 Coordenadas e Apoios (Nós)")
        st.write("Marque as restrições (X, Y, M para Engaste total). Defina os recalques se houver.")
        
        for n, dados in list(st.session_state.nos.items()):
            with st.expander(f"Nó {n}", expanded=True):
                c1, c2, c3 = st.columns(3)
                dados['x'] = c1.number_input(f"X (m)", value=dados['x'], key=f"nx_{n}")
                dados['y'] = c2.number_input(f"Y (m)", value=dados['y'], key=f"ny_{n}")
                
                st.write("**Restrições de Apoio e Recalques:**")
                cx, cy, cm = st.columns(3)
                dados['rx'] = cx.checkbox("Restrito X", value=dados['rx'], key=f"rx_{n}")
                dados['ry'] = cy.checkbox("Restrito Y", value=dados['ry'], key=f"ry_{n}")
                dados['rm'] = cm.checkbox("Restrito Giro (M)", value=dados['rm'], key=f"rm_{n}")
                
                # Se houver restrição, abre campo de recalque
                if dados['rx']: dados['rec_x'] = cx.number_input("Recalque X (m)", value=dados['rec_x'], key=f"recx_{n}", step=0.001, format="%.3f")
                if dados['ry']: dados['rec_y'] = cy.number_input("Recalque Y (m)", value=dados['rec_y'], key=f"recy_{n}", step=0.001, format="%.3f")
                if dados['rm']: dados['rec_m'] = cm.number_input("Recalque Giro (rad)", value=dados['rec_m'], key=f"recm_{n}", step=0.001, format="%.3f")

    with col_barras:
        st.subheader("🔀 Elementos (Barras) e Cargas")
        st.write("Defina a conectividade das barras, carregamentos e variações de temperatura.")
        
        for b, dados in list(st.session_state.barras.items()):
            with st.expander(f"Barra {b}", expanded=True):
                c1, c2 = st.columns(2)
                dados['n1'] = c1.number_input("Nó Inicial", value=dados['n1'], min_value=1, max_value=len(st.session_state.nos), key=f"bn1_{b}")
                dados['n2'] = c2.number_input("Nó Final", value=dados['n2'], min_value=1, max_value=len(st.session_state.nos), key=f"bn2_{b}")
                
                st.write("**Cargas na Barra:**")
                cc1, cc2, cc3 = st.columns(3)
                dados['q'] = cc1.number_input("Carga Distr. q (kN/m)", value=dados['q'], key=f"bq_{b}")
                dados['p'] = cc2.number_input("Carga Pontual P (kN)", value=dados['p'], key=f"bp_{b}")
                dados['xp'] = cc3.number_input("Posição de P (m)", value=dados['xp'], key=f"bxp_{b}")
                
                st.write("**Gradiente Térmico:**")
                ct1, ct2 = st.columns(2)
                dados['dt_sup'] = ct1.number_input("ΔT Face Sup. (°C)", value=dados['dt_sup'], key=f"dts_{b}")
                dados['dt_inf'] = ct2.number_input("ΔT Face Inf. (°C)", value=dados['dt_inf'], key=f"dti_{b}")

    # Gerenciamento de Nós/Barras
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
ndof = num_nos * 3  # 3 graus de liberdade por nó (u, v, theta)

# Graus de liberdade globais e restrições
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
R_0 = np.zeros(ndof) # Vetor de reações de engastamento perfeito

# Loop para montagem da matriz global e vetor de carga equivalente
passo_a_passo_barras = {}

for b, dados in st.session_state.barras.items():
    n1, n2 = dados['n1'], dados['n2']
    x1, y1 = st.session_state.nos[n1]['x'], st.session_state.nos[n1]['y']
    x2, y2 = st.session_state.nos[n2]['x'], st.session_state.nos[n2]['y']
    
    L = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    cos = (x2 - x1) / L
    sin = (y2 - y1) / L
    
    # Matriz de Rigidez Local da Barra (Pórtico Plano)
    k_local = np.zeros((6, 6))
    k_local[0,0] = E*A/L;   k_local[0,3] = -E*A/L
    k_local[3,0] = -E*A/L;  k_local[3,3] = E*A/L
    
    k_local[1,1] = 12*E*I/L**3;  k_local[1,2] = 6*E*I/L**2;   k_local[1,4] = -12*E*I/L**3; k_local[1,5] = 6*E*I/L**2
    k_local[2,1] = 6*E*I/L**2;   k_local[2,2] = 4*E*I/L;      k_local[2,4] = -6*E*I/L**2;  k_local[2,5] = 2*E*I/L
    k_local[4,1] = -12*E*I/L**3; k_local[4,2] = -6*E*I/L**2;  k_local[4,4] = 12*E*I/L**3;  k_local[4,5] = -6*E*I/L**2
    k_local[5,1] = 6*E*I/L**2;   k_local[5,2] = 2*E*I/L;      k_local[5,4] = -6*E*I/L**2;  k_local[5,5] = 4*E*I/L

    # Matriz de Rotação T
    T = np.zeros((6, 6))
    T[0,0] = cos;  T[0,1] = sin;  T[3,3] = cos;  T[3,4] = sin
    T[1,0] = -sin; T[1,1] = cos;  T[4,3] = -sin; T[4,4] = cos
    T[2,2] = 1.0;  T[5,5] = 1.0
    
    k_global_barra = T.T @ k_local @ T
    
    # Graus de liberdade dessa barra
    dof_barra = [(n1-1)*3, (n1-1)*3+1, (n1-1)*3+2, (n2-1)*3, (n2-1)*3+1, (n2-1)*3+2]
    
    # Acumulação na Matriz Global
    for i in range(6):
        for j in range(6):
            K_global[dof_barra[i], dof_barra[j]] += k_global_barra[i, j]
            
    # --- CÁCULO DAS REAÇÕES DE ENGASTAMENTO PERFEITO (LOCAL) ---
    r0_local = np.zeros(6)
    
    # Carga Distribuída (q) perpendicular
    if dados['q'] != 0:
        r0_local[1] += dados['q'] * L / 2
        r0_local[2] += dados['q'] * L**2 / 12
        r0_local[4] += dados['q'] * L / 2
        r0_local[5] -= dados['q'] * L**2 / 12
        
    # Carga Pontual (P) perpendicular no vão
    if dados['p'] != 0:
        a = dados['xp']
        b_dist = L - a
        r0_local[1] += (dados['p'] * b_dist**2 * (3*a + b_dist)) / L**3
        r0_local[2] += (dados['p'] * a * b_dist**2) / L**2
        r0_local[4] += (dados['p'] * a**2 * (a + 3*b_dist)) / L**3
        r0_local[5] -= (dados['p'] * a**2 * b_dist) / L**2

    # Temperatura (Gradiente Térmico)
    if dados['dt_sup'] != 0 or dados['dt_inf'] != 0:
        dT_media = (dados['dt_sup'] + dados['dt_inf']) / 2
        dT_gradiente = dados['dt_inf'] - dados['dt_sup'] # inferior - superior traciona embaixo se inf > sup
        
        # Esforço axial térmico impedido
        N_termico = alpha * dT_media * E * A
        r0_local[0] += N_termico
        r0_local[3] -= N_termico
        
        # Momento térmico impedido
        M_termico = alpha * dT_gradiente * E * I / h
        r0_local[2] -= M_termico
        r0_local[5] += M_termico

    # Rotaciona o vetor de engastamento perfeito para coordenadas globais
    r0_global = T.T @ r0_local
    for i in range(6):
        R_0[dof_barra[i]] += r0_global[i]
        
    passo_a_passo_barras[b] = {
        'k_local': k_local,
        'r0_local': r0_local,
        'dof': dof_barra,
        'L': L
    }

# Particionamento do Sistema Lineal (K*U = F_externa - R_0)
# Para fins didáticos, as forças externas nodais diretas estão nulas, focando em cargas de vão, temperatura e recalques.
F_ext = np.zeros(ndof)
R_direito = F_ext - R_0

# Ajuste do membro direito devido a recalques impostos nos apoios
R_direito -= K_global @ recalques_vetor

# Descobrir graus de liberdade livres (não restritos)
gl_livres = np.where(~restricoes)[0]
gl_restritos = np.where(restricoes)[0]

U_livres = np.zeros(len(gl_livres))
if len(gl_livres) > 0:
    K_ll = K_global[np.ix_(gl_livres, gl_livres)]
    R_l = R_direito[gl_livres]
    try:
        U_livres = np.linalg.solve(K_ll, R_l)
    except np.linalg.linalg.LinAlgError:
        st.error("⚠️ Estrutura Instável de forma cinemática! Adicione vínculos/apoios adequados.")

# Montar vetor completo de deslocamentos nodais (U)
U_completo = recalques_vetor.copy()
if len(gl_livres) > 0:
    U_completo[gl_livres] = U_livres

# Reações de Apoio Finais
Reacoes_Finais = K_global @ U_completo + R_0

# ==========================================
# ABA 2: PASSO A PASSO MÉTODO DOS DESLOCAMENTOS
# ==========================================
with aba_desloc:
    st.header("🧮 Formulação Matricial (Sistema Hipergeométrico)")
    
    st.subheader("1. Identificação do Sistema Hipergeométrico")
    st.write(f"Total de Graus de Liberdade do Pórtico: **{ndof}**")
    st.write(f"Graus de Liberdade Livres (Deslocabilidades Ativas): **{len(gl_livres)}**")
    st.write(f"Vetor de Deslocamentos Impostos por Recalque: `{list(np.round(recalques_vetor,4))}`")
    
    st.subheader("2. Reações de Engastamento Perfeito Acumuladas ($R_0$)")
    st.write("Forças equivalentes geradas nos nós pelas cargas internas das barras, recalques e temperatura:")
    st.dataframe(np.round(R_0, 2), column_config={"value": "Força/Momento Equivalente (kN ou kNm)"})
    
    st.subheader("3. Matriz de Rigidez Global do Sistema ($K_{global}$)")
    st.write("Acumulação direta das rigidezes das barras rotacionadas para o sistema global:")
    st.dataframe(np.round(K_global, 1))
    
    st.subheader("4. Resolução do Sistema Reduzido")
    st.latex(r" [K_{LL}] \cdot \{U_L\} = \{R_L\} - [K_{LR}] \cdot \{U_R\} - \{R_{0,L}\} ")
    
    if len(gl_livres) > 0:
        st.write("**Deslocamentos e Rotações Calculados nos Nós Livres ($U_L$):**")
        for idx_gl in gl_livres:
            no_associado = (idx_gl // 3) + 1
            tipo_gl = ["Translação X (m)", "Translação Y (m)", "Giro (rad)"][idx_gl % 3]
            st.write(f"• **Nó {no_associado}** - {tipo_gl}: `{U_completo[idx_gl]:.6f}`")
    else:
        st.write("Estrutura completamente restrita externamente.")

# ==========================================
# ABA 3: PASSO A PASSO CONCEITUAL (M. FORÇAS / PTV)
# ==========================================
with aba_forcas_ptv:
    st.header("📐 Paralelo Acadêmico com Métodos Clássicos")
    
    # Cálculo do grau de hiperestaticidade estático clássico
    # b = barras, r = restrições de apoio, n = nós. G = r + 3*b - 3*n (para pórtico plano)
    b_qtd = len(st.session_state.barras)
    r_qtd = int(np.sum(restricoes))
    n_qtd = len(st.session_state.nos)
    grau_hiper = r_qtd + 3*b_qtd - 3*n_qtd
    
    st.subheader("Grau de Hiperestaticidade Estática ($d$)")
    st.latex(f"d = R + 3B - 3N = {r_qtd} + 3({b_qtd}) - 3({n_qtd}) = {grau_hiper}")
    
    if grau_hiper > 0:
        st.info(f"Como $d = {grau_hiper} > 0$, a estrutura é **Hiperestática**. No **Método das Forças**, você precisaria liberar {grau_hiper} vínculos para obter um Sistema Principal (SP) Isostático estável.")
        st.write("**Equação de Compatibilidade Clássica:**")
        st.latex(r" \delta_{10} + \delta_{11}X_1 + \delta_{12}X_2 + \dots = \Delta_{recalque} ")
    elif grau_hiper == 0:
        st.success("A estrutura é **Isostática** ($d=0$). Os diagramas saem diretamente por equilíbrio estático.")
    else:
        st.warning("A estrutura é um **Mecanismo** ($d < 0$). Adicione restrições de apoio.")

    st.subheader("💡 Integração pelo PTV (Princípio dos Trabalhos Virtuais)")
    st.write("Se quisesse determinar um deslocamento específico manualmente usando o PTV, a equação computada em cada barra integraria os efeitos reais com o sistema virtual unitário:")
    st.latex(r" \delta = \sum \int_0^L \frac{M_0 M_1}{EI} dx + \sum \int_0^L \frac{N_0 N_1}{EA} dx + \sum \alpha \cdot \Delta T_{grad} \int_0^L M_1 dx ")

# ==========================================
# ABA 4: DIAGRAMAS E RESULTADOS FINAIS
# ==========================================
with aba_diagramas:
    st.header("📊 Diagramas de Esforços Solicitantes Finais")
    st.write("Plotados seguindo rigorosamente as convenções da engenharia civil (Momento Fletor tracionado para baixo).")
    
    # Reações de Apoio na tela
    st.subheader("⚙️ Reações de Apoio Finais nos Nós Restritos")
    for n in sorted(st.session_state.nos.keys()):
        idx = (n - 1) * 3
        if st.session_state.nos[n]['rx'] or st.session_state.nos[n]['ry'] or st.session_state.nos[n]['rm']:
            st.write(f"**Nó {n}:** "
                     f"Rx = `{Reacoes_Finais[idx]:.2f} kN` | "
                     f"Ry = `{Reacoes_Finais[idx+1]:.2f} kN` | "
                     f"Momento = `{Reacoes_Finais[idx+2]:.2f} kNm`")

    # Desenho dos diagramas usando Matplotlib
    fig, (ax_n, ax_v, ax_m) = plt.subplots(3, 1, figsize=(11, 10))
    
    # Processar os esforços internos ao longo de cada barra
    for b, dados in st.session_state.barras.items():
        n1, n2 = dados['n1'], dados['n2']
        x1, y1 = st.session_state.nos[n1]['x'], st.session_state.nos[n1]['y']
        x2, y2 = st.session_state.nos[n2]['x'], st.session_state.nos[n2]['y']
        
        L = passo_a_passo_barras[b]['L']
        cos = (x2 - x1) / L
        sin = (y2 - y1) / L
        
        # Resgatar deslocamentos globais da barra
        dof = passo_a_passo_barras[b]['dof']
        u_global = U_completo[dof]
        
        # Transformar deslocamentos nodais globais da barra para o sistema local
        T = np.zeros((6, 6))
        T[0,0] = cos;  T[0,1] = sin;  T[3,3] = cos;  T[3,4] = sin
        T[1,0] = -sin; T[1,1] = cos;  T[4,3] = -sin; T[4,4] = cos
        T[2,2] = 1.0;  T[5,5] = 1.0
        u_local = T @ u_global
        
        # Forças Nodais Locais na Barra: F_local = k_local * u_local + r0_local
        f_local = passo_a_passo_barras[b]['k_local'] @ u_local + passo_a_passo_barras[b]['r0_local']
        
        # Esforços nas extremidades da barra (Convenção de Sinais Local do Elemento)
        N1, V1, M1 = f_local[0], f_local[1], f_local[2]
        N2, V2, M2 = -f_local[3], -f_local[4], -f_local[5] # Reverter extremidade final para equilíbrio contínuo
        
        # Criar malha discreta ao longo da barra para desenhar diagramas parabólicos/rampas reais
        x_mesh = np.linspace(0, L, 50)
        N_plot = []
        V_plot = []
        M_plot = []
        
        for x_val in x_mesh:
            # Equações de equilíbrio ao longo da barra considerando as cargas de vão
            q = dados['q']
            P = dados['p']
            xp = dados['xp']
            
            # Termos da carga distribuída
            term_q_v = q * x_val
            term_q_m = 0.5 * q * x_val**2
            
            # Termos da carga pontual
            term_p_v = P if x_val > xp else 0.0
            term_p_m = P * (x_val - xp) if x_val > xp else 0.0
            
            # Esforços na coordenada x_val local
            N_atual = -N1 # simplificado (pórticos puros podem ter variação se houver carga axial de vão)
            V_atual = V1 - term_q_v - term_p_v
            M_atual = -M1 + V1*x_val - term_q_m - term_p_m
            
            N_plot.append(N_atual)
            V_plot.append(V_atual)
            M_plot.append(M_atual)
            
        # Converter coordenadas locais mapeadas para plotagem na tela global (apenas para geometria plana/vigas)
        # Se for pórtico, plota mapeado no eixo X global acumulado para melhor visualização didática
        x_global_plot = np.linspace(x1, x2, 50)
        
        # --- PLOT ESFORÇO NORMAL ---
        ax_n.plot(x_global_plot, N_plot, color='teal', lw=2)
        ax_n.fill_between(x_global_plot, 0, N_plot, color='teal', alpha=0.1)
        ax_n.axhline(0, color='black', lw=0.5)
        ax_n.set_title("Diagrama de Esforço Normal N (kN) [+ Tração, - Compressão]")
        
        # --- PLOT ESFORÇO CORTANTE ---
        ax_v.plot(x_global_plot, V_plot, color='crimson', lw=2)
        ax_v.fill_between(x_global_plot, 0, V_plot, color='crimson', alpha=0.1)
        ax_v.axhline(0, color='black', lw=0.5)
        ax_v.set_title("Diagrama de Esforço Cortante V (kN)")
        
        # --- PLOT MOMENTO FLETOR ---
        # ATENÇÃO: Invertendo o eixo Y do gráfico de momentos para o positivo ficar para baixo (Padrão da Engenharia Civil)
        ax_m.plot(x_global_plot, M_plot, color='navy', lw=2)
        ax_m.fill_between(x_global_plot, 0, M_plot, color='navy', alpha=0.1)
        ax_m.axhline(0, color='black', lw=0.5)
        ax_m.set_title("Diagrama de Momento Fletor M (kNm) [Desenhado do Lado Tracionado - Positivo para Baixo]")

    # Inverter os limites do eixo Y do momento fletor para seguir padrão técnico civil
    ax_m.invert_yaxis()
    
    st.pyplot(fig)
