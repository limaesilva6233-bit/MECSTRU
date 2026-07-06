import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.patches as patches

st.set_page_config(page_title="Solver Estrutural Universitário Pro", layout="wide")

st.title("🏗️ Frame Mechanics Explorer Pro - Versão Visual Completa")
st.write("Simulador flexível com suporte a EI/EA distintos, cargas de Momento Concentrado e representação gráfica da estrutura.")

# --- ATALHO DE CALIBRAÇÃO (CARREGA O SEU EXERCÍCIO COMO MODELO) ---
if st.button("🚀 Carregar Cenário de Teste (Questão da Prova)"):
    st.session_state.nos = {
        1: {'x': 0.0, 'y': 0.0, 'rx': True, 'ry': True, 'rm': True, 'rec_x': 0.0, 'rec_y': 0.0, 'rec_m': 0.0},
        2: {'x': 10.0, 'y': 0.0, 'rx': False, 'ry': True, 'rm': False, 'rec_x': 0.0, 'rec_y': 0.0, 'rec_m': 0.0},
        3: {'x': 20.0, 'y': 0.0, 'rx': True, 'ry': True, 'rm': True, 'rec_x': 0.0, 'rec_y': -0.04, 'rec_m': 0.0}
    }
    st.session_state.barras = {
        1: {'n1': 1, 'n2': 2, 'q': 0.0, 'p': 80.0, 'xp': 5.0, 'mc': 0.0, 'xmc': 0.0, 'dt_sup': 0.0, 'dt_inf': 0.0, 'ei': 10000.0, 'ea': 3708000.0, 'h': 0.18},
        2: {'n1': 2, 'n2': 3, 'q': 24.0, 'p': 0.0, 'xp': 0.0, 'mc': 0.0, 'xmc': 0.0, 'dt_sup': 0.0, 'dt_inf': 0.0, 'ei': 10000.0, 'ea': 3708000.0, 'h': 0.18}
    }
    st.sidebar.info("Dados da prova carregados com sucesso!")
    st.rerun()

# --- INICIALIZAÇÃO DE VARIÁVEIS NA SESSÃO ---
if 'nos' not in st.session_state:
    st.session_state.nos = {
        1: {'x': 0.0, 'y': 0.0, 'rx': True, 'ry': True, 'rm': True, 'rec_x': 0.0, 'rec_y': 0.0, 'rec_m': 0.0},
        2: {'x': 5.0, 'y': 0.0, 'rx': False, 'ry': True, 'rm': False, 'rec_x': 0.0, 'rec_y': 0.0, 'rec_m': 0.0},
        3: {'x': 10.0, 'y': 0.0, 'rx': False, 'ry': True, 'rm': False, 'rec_x': 0.0, 'rec_y': 0.0, 'rec_m': 0.0}
    }
if 'barras' not in st.session_state:
    st.session_state.barras = {
        1: {'n1': 1, 'n2': 2, 'q': 10.0, 'p': 0.0, 'xp': 2.5, 'mc': 0.0, 'xmc': 0.0, 'dt_sup': 0.0, 'dt_inf': 0.0, 'ei': 10000.0, 'ea': 3708000.0, 'h': 0.18},
        2: {'n1': 2, 'n2': 3, 'q': 0.0, 'p': 20.0, 'xp': 2.5, 'mc': 0.0, 'xmc': 0.0, 'dt_sup': 0.0, 'dt_inf': 0.0, 'ei': 10000.0, 'ea': 3708000.0, 'h': 0.18}
    }

# --- ABAS DO APLICATIVO ---
aba_input, aba_modelo, aba_desloc, aba_forcas_ptv, aba_passo, aba_diagramas = st.tabs([
    "⚙️ 1. Modelagem, Cargas e Seções", 
    "👁️ 2. Visualização do Modelo",
    "🧮 3. M. Deslocamentos & Rigidez Direta", 
    "📐 4. M. Forças & PTV (Conceitual)",
    "📖 5. Explicação Passo a Passo",
    "📊 6. Diagramas e Esforços nos Nós"
])

st.sidebar.header("🔬 Parâmetros Globais do Material")
alpha = st.sidebar.number_input("Coeficiente de Dilatação α (1/°C)", value=1.2e-5, format="%.2e")

# ==========================================
# ABA 1: CONFIGURAÇÃO DE MODELAGEM E ENTRADAS
# ==========================================
with aba_input:
    st.header("Configuração Dinâmica de Nós, Conectividade e Ações Atuantes")
    col_nos, col_barras = st.columns(2)
    
    with col_nos:
        st.subheader("📌 Coordenadas e Apoios (Nós)")
        for n, dados in list(st.session_state.nos.items()):
            with st.expander(f"Nó {n}", expanded=True):
                c1, c2 = st.columns(2)
                dados['x'] = c1.number_input(f"X (m)", value=dados['x'], key=f"nx_{n}")
                dados['y'] = c2.number_input(f"Y (m)", value=dados['y'], key=f"ny_{n}")
                
                cx, cy, cm = st.columns(3)
                dados['rx'] = cx.checkbox("Restrito X", value=dados['rx'], key=f"rx_{n}")
                dados['ry'] = cy.checkbox("Restrito Y", value=dados['ry'], key=f"ry_{n}")
                dados['rm'] = cm.checkbox("Restrito Giro", value=dados['rm'], key=f"rm_{n}")
                
                if dados['rx']: dados['rec_x'] = cx.number_input("Recalque X (m)", value=dados['rec_x'], key=f"recx_{n}", format="%.3f")
                if dados['ry']: dados['rec_y'] = cy.number_input("Recalque Y (m)", value=dados['rec_y'], key=f"recy_{n}", format="%.3f")
                if dados['rm']: dados['rec_m'] = cm.number_input("Recalque Giro (rad)", value=dados['rec_m'], key=f"recm_{n}", format="%.3f")

    with col_barras:
        st.subheader("🔀 Elementos (Barras) e Carregamentos")
        for b, dados in list(st.session_state.barras.items()):
            with st.expander(f"Barra {b}", expanded=True):
                c1, c2 = st.columns(2)
                dados['n1'] = c1.number_input("Nó Inicial", value=dados['n1'], min_value=1, max_value=len(st.session_state.nos), key=f"bn1_{b}")
                dados['n2'] = c2.number_input("Nó Final", value=dados['n2'], min_value=1, max_value=len(st.session_state.nos), key=f"bn2_{b}")
                
                st.write("**📐 Seção:**")
                cs1, cs2, cs3 = st.columns(3)
                dados['ei'] = cs1.number_input("Rigidez EI (kNm²)", value=dados.get('ei', 10000.0), key=f"bei_{b}")
                dados['ea'] = cs2.number_input("Rigidez EA (kN)", value=dados.get('ea', 3708000.0), key=f"bea_{b}")
                dados['h'] = cs3.number_input("Altura h (m)", value=dados.get('h', 0.18), key=f"bh_{b}")
                
                st.write("**📥 Cargas de Força (Distribuída e Pontual):**")
                cc1, cc2, cc3 = st.columns(3)
                dados['q'] = cc1.number_input("Carga q (kN/m)", value=dados['q'], key=f"bq_{b}")
                dados['p'] = cc2.number_input("Força P (kN)", value=dados['p'], key=f"bp_{b}")
                dados['xp'] = cc3.number_input("Posição de P (m)", value=dados['xp'], key=f"bxp_{b}")
                
                st.write("**🔄 Carga de Momento Concentrado no Vão:**")
                cm1, cm2 = st.columns(2)
                dados['mc'] = cm1.number_input("Momento M (kNm) [+: Anti-horário]", value=dados.get('mc', 0.0), key=f"bmc_{b}")
                dados['xmc'] = cm2.number_input("Posição de M (m)", value=dados.get('xmc', 0.0), key=f"bxmc_{b}")
                
                st.write("**🌡️ Gradiente Térmico:**")
                ct1, ct2 = st.columns(2)
                dados['dt_sup'] = ct1.number_input("ΔT Sup (°C)", value=dados['dt_sup'], key=f"dts_{b}")
                dados['dt_inf'] = ct2.number_input("ΔT Inf (°C)", value=dados['dt_inf'], key=f"dti_{b}")

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
        st.session_state.barras[novo_id] = {'n1': novo_id, 'n2': novo_id+1, 'q': 0.0, 'p': 0.0, 'xp': 0.0, 'mc': 0.0, 'xmc': 0.0, 'dt_sup': 0.0, 'dt_inf': 0.0, 'ei': 10000.0, 'ea': 3708000.0, 'h': 0.18}
        st.rerun()
    if cb4.button("❌ Remover Última Barra") and len(st.session_state.barras) > 1:
        st.session_state.barras.pop(max(st.session_state.barras.keys()))
        st.rerun()

# ==========================================
# MOTOR MATRICIAL AVANÇADO
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
R_0 = np.zeros(ndof)
passo_a_passo_barras = {}

for b, dados in st.session_state.barras.items():
    n1, n2 = dados['n1'], dados['n2']
    x1, y1 = st.session_state.nos[n1]['x'], st.session_state.nos[n1]['y']
    x2, y2 = st.session_state.nos[n2]['x'], st.session_state.nos[n2]['y']
    L = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    cos, sin = (x2 - x1) / L, (y2 - y1) / L
    
    barra_EI = dados.get('ei', 10000.0)
    barra_EA = dados.get('ea', 3708000.0)
    barra_h = dados.get('h', 0.18)
    
    k_local = np.zeros((6, 6))
    k_local[0,0] = barra_EA/L;   k_local[0,3] = -barra_EA/L
    k_local[3,0] = -barra_EA/L;  k_local[3,3] = barra_EA/L
    k_local[1,1] = 12*barra_EI/L**3;  k_local[1,2] = 6*barra_EI/L**2;   k_local[1,4] = -12*barra_EI/L**3; k_local[1,5] = 6*barra_EI/L**2
    k_local[2,1] = 6*barra_EI/L**2;   k_local[2,2] = 4*barra_EI/L;      k_local[2,4] = -6*barra_EI/L**2;  k_local[2,5] = 2*barra_EI/L
    k_local[4,1] = -12*barra_EI/L**3; k_local[4,2] = -6*barra_EI/L**2;  k_local[4,4] = 12*barra_EI/L**3;  k_local[4,5] = -6*barra_EI/L**2
    k_local[5,1] = 6*barra_EI/L**2;   k_local[5,2] = 2*barra_EI/L;      k_local[5,4] = -6*barra_EI/L**2;  k_local[5,5] = 4*barra_EI/L

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
    if dados.get('mc', 0.0) != 0:
        a = dados['xmc']
        b_dist = L - a
        r0_local[1] += (-6 * dados['mc'] * a * b_dist) / L**3
        r0_local[2] += (dados['mc'] * b_dist * (b_dist - 2*a)) / L**2
        r0_local[4] += (6 * dados['mc'] * a * b_dist) / L**3
        r0_local[5] += (dados['mc'] * a * (a - 2*b_dist)) / L**2
    if dados['dt_sup'] != 0 or dados['dt_inf'] != 0:
        dT_media = (dados['dt_sup'] + dados['dt_inf']) / 2
        dT_gradiente = dados['dt_inf'] - dados['dt_sup']
        N_termico = alpha * dT_media * barra_EA
        r0_local[0] += N_termico; r0_local[3] -= N_termico
        M_termico = alpha * dT_gradiente * barra_EI / barra_h
        r0_local[2] -= M_termico; r0_local[5] += M_termico

    r0_global = T.T @ r0_local
    for i in range(6):
        R_0[dof_barra[i]] += r0_global[i]
        
    passo_a_passo_barras[b] = {'k_local': k_local, 'r0_local': r0_local, 'dof': dof_barra, 'L': L, 'T': T}

R_0_total_acumulado = R_0 + K_global @ recalques_vetor
gl_livres = np.where(~restricoes)[0]

U_completo = recalques_vetor.copy()

# --- SEGURANÇA CONTRA MATRIZ SINGULAR ---
if len(gl_livres) > 0:
    K_ll = K_global[np.ix_(gl_livres, gl_livres)]
    R_l = - R_0_total_acumulado[gl_livres]
    try:
        U_livres = np.linalg.solve(K_ll, R_l)
        U_completo[gl_livres] = U_livres
    except np.linalg.LinAlgError:
        st.error("🚨 **numpy.linalg.LinAlgError: Singular matrix nas Abas de Visualização!**")
        st.markdown(
            """
            A matriz de rigidez livre ($K_{ll}$) é singular. A estrutura está fisicamente instável ou há erros nos apoios.
            * Verifique se removeu apoios em excesso ou se criou um mecanismo de rotação livre.
            * Certifique-se de que as rigidezes $EI$ e $EA$ das seções não estão zeradas nas caixas de entrada.
            """
        )
        linhas_zeradas = np.where(~K_ll.any(axis=1))[0]
        if len(linhas_zeradas) > 0:
            st.warning(f"🔍 **Debug:** Graus de liberdade com linhas zeradas em $K_{ll}$: {linhas_zeradas}")
        st.stop()

Esforcos_Nos_Globais = K_global @ U_completo + R_0

# ==========================================
# ABA 2: VISUALIZAÇÃO GRÁFICA DO MODELO
# ==========================================
with aba_modelo:
    st.header("👁️ Representação Esquemática da Estrutura Lanço/Apoios/Cargas")
    
    fig_mod, ax_m = plt.subplots(figsize=(12, 5))
    
    for b, dados in st.session_state.barras.items():
        n1, n2 = dados['n1'], dados['n2']
        x1, y1 = st.session_state.nos[n1]['x'], st.session_state.nos[n1]['y']
        x2, y2 = st.session_state.nos[n2]['x'], st.session_state.nos[n2]['y']
        ax_m.plot([x1, x2], [y1, y2], color='#2c3e50', lw=4, zorder=2)
        ax_m.text((x1+x2)/2, (y1+y2)/2 + 0.3, f"B{b}\nEI={dados['ei']}", color='#2c3e50', weight='bold', ha='center')
        
        if dados['q'] > 0:
            x_vals = np.linspace(x1, x2, 11)
            for xv in x_vals:
                ax_m.annotate("", xy=(xv, y1), xytext=(xv, y1 + 1.0),
                            arrowprops=dict(arrowstyle="->", color="darkorange", lw=1.5))
            ax_m.plot([x1, x2], [y1+1.0, y2+1.0], color="darkorange", lw=1.5, ls='--')
            ax_m.text((x1+x2)/2, y1 + 1.2, f"q = {dados['q']} kN/m", color="darkorange", ha='center', weight='bold')
            
        if dados['p'] > 0:
            xp_glob = x1 + dados['xp']
            ax_m.annotate(f"P = {dados['p']} kN", xy=(xp_glob, y1), xytext=(xp_glob, y1 + 1.8),
                        arrowprops=dict(facecolor='crimson', shrink=0.05, width=2, headwidth=8),
                        color='crimson', weight='bold', ha='center')
                        
        if dados.get('mc', 0.0) != 0:
            xmc_glob = x1 + dados['xmc']
            ax_m.plot(xmc_glob, y1, 'o', color='purple', ms=8)
            ax_m.text(xmc_glob, y1 - 0.6, f"M = {dados['mc']} kNm", color='purple', weight='bold', ha='center')
            style = "Simple, tail_width=1, head_width=4, head_length=4"
            kw = dict(arrowstyle=style, color="purple")
            a_patch = patches.FancyArrowPatch((xmc_glob - 0.4, y1 + 0.4), (xmc_glob + 0.4, y1 + 0.4), connectionstyle="arc3,rad=.5", **kw)
            ax_m.add_patch(a_patch)
            
        if dados['dt_sup'] != 0 or dados['dt_inf'] != 0:
            ax_m.text((x1+x2)/2, (y1+y2)/2 - 0.4, f"ΔTs={dados['dt_sup']}°C / ΔTi={dados['dt_inf']}°C", color='teal', fontsize=9, ha='center')

    for n, dados in st.session_state.nos.items():
        x, y = dados['x'], dados['y']
        ax_m.plot(x, y, 'o', color='black', ms=10, zorder=5)
        ax_m.text(x, y + 0.3, f"Nó {n}", weight='bold', ha='center')
        
        if dados['rx'] and dados['ry'] and dados['rm']:
            ax_m.plot([x-0.2, x+0.2], [y-0.2, y-0.2], color='black', lw=3)
            for k in np.linspace(-0.2, 0.2, 5):
                ax_m.plot([x+k, x+k-0.1], [y-0.2, y-0.4], color='black', lw=1)
        elif dados['ry'] and not dados['rx']:
            poly = plt.Polygon([[x, y], [x-0.3, y-0.4], [x+0.3, y-0.4]], facecolor='gray', edgecolor='black')
            ax_m.add_patch(poly)
            ax_m.plot([x-0.4, x+0.4], [y-0.45, y-0.45], color='black', lw=1.5)
            
        if dados['rec_y'] != 0:
            ax_m.annotate(f"Rec={dados['rec_y']}m", xy=(x, y + dados['rec_y']), xytext=(x - 0.8, y - 1.0),
                        arrowprops=dict(arrowstyle="->", color="royalblue", linestyle="--", lw=2),
                        color="royalblue", weight='bold')

    ax_m.set_ylabel("Y (m)")
    ax_m.set_xlabel("X (m)")
    ax_m.grid(True, linestyle=':', alpha=0.6)
    ax_m.set_ylim(-2.0, 3.0)
    ax_m.axhline(0, color='black', lw=0.5, ls=':')
    st.pyplot(fig_mod)

# ==========================================
# ABA 3: MATRIZES E VETORES DO MÉTODO
# ==========================================
with aba_desloc:
    st.header("🧮 Vetores e Matrizes do Método dos Deslocamentos")
    st.dataframe(pd.DataFrame({'R0 Equivalente Total': R_0_total_acumulado}, index=[f"Dof {i}" for i in range(ndof)]))
    st.write("Matriz de Rigidez Global:")
    st.dataframe(np.round(K_global, 2))

# ==========================================
# ABA 4: CONCEITUAL MÉTODO DAS FORÇAS
# ==========================================
with aba_forcas_ptv:
    st.header("📐 Grau de Hiperestaticidade (Método das Forças)")
    grau_hiper = int(np.sum(restricoes)) + 3*len(st.session_state.barras) - 3*num_nos
    st.latex(f"d = R + 3B - 3N = {grau_hiper}")

# ==========================================
# ABA 5: EXPLICAÇÃO PASSO A PASSO
# ==========================================
with aba_passo:
    st.header("📖 Explicação do Processamento Mecânico")
    st.markdown("As cargas de momentos concentrados no vão alteram os termos de engastamento perfeito rotacionais e lineares locais de forma analítica contínua.")

# ==========================================
# ABA 6: DIAGRAMAS E VALORES CRÍTICOS (ATUALIZADA)
# ==========================================
with aba_diagramas:
    st.header("📊 Esforços Finais e Diagramas de Projeto")
    
    for n in sorted(st.session_state.nos.keys()):
        idx = (n - 1) * 3
        with st.expander(f"Esforços Atuantes no Nó {n}", expanded=True):
            c_e1, c_e2, c_e3 = st.columns(3)
            c_e1.metric("Axial Fx", f"{Esforcos_Nos_Globais[idx]:.2f} kN")
            c_e2.metric("Cortante Fy", f"{Esforcos_Nos_Globais[idx+1]:.2f} kN")
            c_e3.metric("Momento Fletor M", f"{Esforcos_Nos_Globais[idx+2]:.2f} kNm")

    # Listas agregadoras para o escaner de pontos máximos globais
    x_global_completo = []
    V_completo_plot = []
    M_completo_plot = []

    # Construção contínua dos dados dos gráficos
    for b, dados in st.session_state.barras.items():
        L = passo_a_passo_barras[b]['L']
        T = passo_a_passo_barras[b]['T']
        u_global = U_completo[passo_a_passo_barras[b]['dof']]
        f_local = passo_a_passo_barras[b]['k_local'] @ (T @ u_global) + passo_a_passo_barras[b]['r0_local']
        
        V1, M1 = f_local[1], f_local[2]
        x_mesh = np.linspace(0, L, 100)
        
        x_start = st.session_state.nos[dados['n1']]['x']
        x_end = st.session_state.nos[dados['n2']]['x']
        x_global = np.linspace(x_start, x_end, 100)
        
        for i, x_val in enumerate(x_mesh):
            term_q_v = dados['q'] * x_val
            term_q_m = 0.5 * dados['q'] * x_val**2
            term_p_v = dados['p'] if x_val > dados['xp'] else 0.0
            term_p_m = dados['p'] * (x_val - dados['xp']) if x_val > dados['xp'] else 0.0
            term_mc_m = dados.get('mc', 0.0) if x_val > dados.get('xmc', 0.0) else 0.0
            
            v_atual = V1 - term_q_v - term_p_v
            m_atual = -M1 + V1*x_val - term_q_m - term_p_m + term_mc_m
            
            x_global_completo.append(x_global[i])
            V_completo_plot.append(v_atual)
            M_completo_plot.append(m_atual)

    # Convertendo para arrays numéricos para busca de índices críticos
    x_arr = np.array(x_global_completo)
    V_arr = np.array(V_completo_plot)
    M_arr = np.array(M_completo_plot)

    # --- RENDERIZAÇÃO MATPLOTLIB DOS DIAGRAMAS CONTÍNUOS ---
    fig, (ax_v, ax_m) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    fig.patch.set_facecolor('#f8f9fa')

    # Plotagem Esforço Cortante V
    ax_v.set_facecolor('#ffffff')
    ax_v.plot(x_arr, V_arr, color='crimson', lw=2.5)
    ax_v.fill_between(x_arr, 0, V_arr, color='crimson', alpha=0.08)
    ax_v.axhline(0, color='#333333', lw=0.8)
    ax_v.set_title("Esforço Cortante V (kN)", fontsize=12, fontweight='bold', pad=10)
    ax_v.grid(True, linestyle='--', alpha=0.5)

    # Plotagem Momento Fletor M
    ax_m.set_facecolor('#ffffff')
    ax_m.plot(x_arr, M_arr, color='navy', lw=2.5)
    ax_m.fill_between(x_arr, 0, M_arr, color='navy', alpha=0.08)
    ax_m.axhline(0, color='#333333', lw=0.8)
    ax_m.set_title("Momento Fletor M (kNm)", fontsize=12, fontweight='bold', pad=10)
    ax_m.grid(True, linestyle='--', alpha=0.5)
    ax_m.invert_yaxis()  # Convenção clássica da engenharia civil: Positivo para Baixo

    # --- DATA LABELS INTELIGENTES NOS DIAGRAMAS ---
    # 1. Momento Negativo Máximo (Apoio Central Geralmente)
    idx_m_neg = M_arr.argmin()
    ax_m.annotate(f'{M_arr[idx_m_neg]:.2f} kNm', 
                 xy=(x_arr[idx_m_neg], M_arr[idx_m_neg]), 
                 xytext=(x_arr[idx_m_neg], M_arr[idx_m_neg] - 4),
                 arrowprops=dict(arrowstyle="-", color='#495057', lw=1),
                 ha='center', va='bottom', fontsize=9, fontweight='bold',
                 bbox=dict(boxstyle="round,pad=0.3", fc="#fff3cd", alpha=0.9, ec="#ffc107"))

    # 2. Momento Máximo Positivo (Onde o cortante zera ou cruza o vão)
    idx_m_pos = M_arr.argmax()
    ax_m.annotate(f'+{M_arr[idx_m_pos]:.2f} kNm', 
                 xy=(x_arr[idx_m_pos], M_arr[idx_m_pos]), 
                 xytext=(x_arr[idx_m_pos], M_arr[idx_m_pos] + 4),
                 arrowprops=dict(arrowstyle="-", color='#495057', lw=1),
                 ha='center', va='top', fontsize=9, fontweight='bold',
                 bbox=dict(boxstyle="round,pad=0.3", fc="#d1e7dd", alpha=0.9, ec="#198754"))

    # Labels de extremidade nos momentos
    ax_m.text(x_arr[0]+0.2, M_arr[0]-1, f'{M_arr[0]:.2f}', color='navy', fontweight='bold')
    ax_m.text(x_arr[-1]-0.5, M_arr[-1]-1, f'{M_arr[-1]:.2f}', color='navy', fontweight='bold')

    plt.xlabel("Posição Linear ao longo dos Vãos (m)", fontsize=10, labelpad=8)
    plt.tight_layout()
    st.pyplot(fig)
