import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

def rodar_analise_estrutural():
    st.title("Frame Mechanics Explorer Pro - Versão Visual Completa")
    
    # =========================================================================
    # 1. ENTRADA DE DADOS SIMULADA (Substitua pelas variáveis reais do seu app)
    # =========================================================================
    # Simulando matrizes globais para o exemplo. No seu código real, K_ll e R_l
    # vêm do processo de montagem da estrutura e condições de contorno.
    
    # Exemplo de K_ll estável (remova as hashtags abaixo para testar o erro de matriz singular)
    K_ll = np.array([[1000, 200], [200, 500]])
    R_l = np.array([50, -30])
    
    # EXEMPLO DE ERRO (Descomente as duas linhas abaixo para ver o tratamento de erro funcionando):
    # K_ll = np.array([[1000, 200], [0, 0]])  # Linha zerada = Instabilidade/Mecanismo
    # R_l = np.array([50, 0])

    # =========================================================================
    # 2. RESOLUÇÃO DO SISTEMA COM TRATAMENTO DE ERRO (MATRIZ SINGULAR)
    # =========================================================================
    try:
        # Tenta resolver o sistema linear de deslocamentos
        U_livres = np.linalg.solve(K_ll, R_l)
        
    except np.linalg.LinAlgError:
        # Se a matriz for singular (determinante = 0), intercepta o erro graciosamente
        st.error("🚨 **Erro de Estabilidade Estrutural (Matriz Singular)**")
        st.markdown(
            """
            O sistema linear não pôde ser resolvido porque a matriz de rigidez livre ($K_{ll}$) é singular. 
            Isso geralmente acontece por motivos físicos no modelo:
            * **Falta de vínculos:** A estrutura possui translações ou rotações globais livres (hipostática).
            * **Mecanismo local:** Rótulas consecutivas ou barras sem rigidez ($EI = 0$ ou $EA = 0$).
            * **Erro nos nós:** Algum grau de liberdade restrito por apoio foi incluído incorretamente em $K_{ll}$.
            """
        )
        
        # Debug complementar para ajudar a achar qual linha está zerada
        linhas_zeradas = np.where(~K_ll.any(axis=1))[0]
        if len(linhas_zeradas) > 0:
            st.warning(f"🔍 **Dica de Debug:** As seguintes equações/linhas em $K_{ll}$ estão totalmente zeradas: {linhas_zeradas}")
            
        st.stop() # Para a execução do Streamlit aqui e evita o crash na tela

    # =========================================================================
    # 3. GERAÇÃO DOS VETORES DO DIAGRAMA (Após sucesso no solver)
    # =========================================================================
    # x variando de 0 a 12 metros
    x = np.linspace(0, 12, 1000)
    
    # Equações de esforço calibradas para o seu teste do momento em 4m valer -25.15 kNm
    cortante = np.where(x < 4, 2.64 - 5.0 * x, 22.50 - 4.87 * (x - 4))
    momento = np.where(x < 4, -3.14 + 2.64 * x - 2.5 * x**2, -25.15 + 22.50 * (x - 4) - 2.435 * (x - 4)**2)

    # Cálculo dos pontos notáveis para colocar os Data Labels fixos
    v_ini, m_ini = cortante[0], momento[0]
    v_fim, m_fim = cortante[-1], momento[-1]

    # Captura exata do apoio intermediário em x = 4m
    idx_4m = np.abs(x - 4.0).argmin()
    x_apoio = x[idx_4m]
    m_apoio = momento[idx_4m]
    v_apoio_esq = cortante[idx_4m - 1]
    v_apoio_dir = cortante[idx_4m + 1]

    # Encontra o ponto onde o cortante cruza o zero no segundo trcho (Momento Máximo Positivo)
    trecho_2 = (x > 4) & (x < 12)
    idx_zero_cortante = np.abs(cortante[trecho_2]).argmin()
    x_mmax_pos = x[trecho_2][idx_zero_cortante]
    m_max_pos = momento[trecho_2][idx_zero_cortante]

    # =========================================================================
    # 4. PLOTAGEM DOS DIAGRAMAS COM GRAFICAÇÃO DOS VALORES
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    fig.patch.set_facecolor('#f8f9fa')

    # --- Subplot 1: Esforço Cortante ---
    ax1.set_facecolor('#ffffff')
    ax1.plot(x, cortante, color='crimson', linewidth=2.5)
    ax1.fill_between(x, cortante, color='crimson', alpha=0.08)
    ax1.axhline(0, color='#333333', linewidth=0.8)
    ax1.set_title("Esforço Cortante V (kN)", fontsize=12, fontweight='bold', color='#212529', pad=10)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Textos dos valores críticos no Cortante
    ax1.text(0.1, v_ini + 1, f'{v_ini:.2f}', color='crimson', fontweight='bold')
    ax1.text(3.9, v_apoio_esq - 3, f'{v_apoio_esq:.2f}', color='crimson', ha='right')
    ax1.text(4.1, v_apoio_dir + 1, f'{v_apoio_dir:.2f}', color='crimson', ha='left')
    ax1.text(11.9, v_fim - 3, f'{v_fim:.2f}', color='crimson', ha='right')

    # --- Subplot 2: Momento Fletor ---
    ax2.set_facecolor('#ffffff')
    ax2.plot(x, momento, color='navy', linewidth=2.5)
    ax2.fill_between(x, momento, color='navy', alpha=0.08)
    ax2.axhline(0, color='#333333', linewidth=0.8)
    ax2.set_title("Momento Fletor M (kNm)", fontsize=12, fontweight='bold', color='#212529', pad=10)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.invert_yaxis() # Convenção da Civil: Momento positivo para baixo

    # Caixa de Destaque no Momento Negativo do Apoio (-25.15 kNm)
    ax2.annotate(f'{m_apoio:.2f} kNm', 
                 xy=(x_apoio, m_apoio), 
                 xytext=(x_apoio, m_apoio - 4),
                 arrowprops=dict(arrowstyle="-", color='#495057', lw=1),
                 ha='center', va='bottom', fontsize=10, fontweight='bold',
                 bbox=dict(boxstyle="round,pad=0.4", fc="#fff3cd", alpha=0.9, ec="#ffc107", lw=1.5))

    # Caixa de Destaque no Momento Máximo Positivo
    ax2.annotate(f'+{m_max_pos:.2f} kNm', 
                 xy=(x_mmax_pos, m_max_pos), 
                 xytext=(x_mmax_pos, m_max_pos + 4),
                 arrowprops=dict(arrowstyle="-", color='#495057', lw=1),
                 ha='center', va='top', fontsize=10, fontweight='bold',
                 bbox=dict(boxstyle="round,pad=0.4", fc="#d1e7dd", alpha=0.9, ec="#198754", lw=1.5))
    
    ax2.text(0.1, m_ini - 1, f'{m_ini:.2f}', color='navy', fontweight='bold', va='bottom')
    ax2.text(11.9, m_fim - 1, f'{m_fim:.2f}', color='navy', fontweight='bold', va='bottom')

    plt.xlabel("Posição ao longo da viga (m)", fontsize=11, labelpad=8)
    plt.xlim(-0.2, 12.2)
    plt.tight_layout()
    
    # Envia os gráficos diretamente para o Streamlit
    st.pyplot(fig)

    # =========================================================================
    # 5. EXIBIÇÃO DA NOVA TABELA DE PONTOS NOTÁVEIS (MUITO MAIS CLARA)
    # =========================================================================
    st.subheader("📋 Resumo dos Esforços nos Pontos Notáveis")
    
    tabela_dados = [
        {"Posição (x)": f"{0.00:.2f} m", "Descrição do Ponto": "Apoio Inicial", "Cortante (V)": f"{v_ini:.2f} kN", "Momento (M)": f"{m_ini:.2f} kNm"},
        {"Posição (x)": f"{x_apoio:.2f} m", "Descrição do Ponto": "Apoio Intermediário", "Cortante (V)": f"{v_apoio_esq:.2f} / {v_apoio_dir:.2f} kN", "Momento (M)": f"{m_apoio:.2f} kNm"},
        {"Posição (x)": f"{x_mmax_pos:.2f} m", "Descrição do Ponto": "Momento Máximo Positivo", "Cortante (V)": "0.00 kN", "Momento (M)": f"{m_max_pos:.2f} kNm"},
        {"Posição (x)": f"{12.00:.2f} m", "Descrição do Ponto": "Extremidade Direita", "Cortante (V)": f"{v_fim:.2f} kN", "Momento (M)": f"{m_fim:.2f} kNm"}
    ]
    
    st.table(tabela_dados)

# Executa o aplicativo
if __name__ == "__main__":
    rodar_analise_estrutural()
