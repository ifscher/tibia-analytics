import streamlit as st


def center_content(content):
    return f"""
    <div style="display: flex; justify-content: center;">
        {content}
    </div>
    """


def menu():
    """Exibe o menu de navegação lateral sem requisito de login."""
    st.sidebar.caption('Dashboard')
    st.sidebar.page_link("pages/home.py", label="Home")
    st.sidebar.page_link("pages/boost.py", label="Custos de Boost")
    st.sidebar.page_link("pages/itens.py", label="Itens")
    st.sidebar.page_link("pages/detalhes_item.py", label="Detalhes do Item")
    st.sidebar.page_link("pages/comparador.py", label="Comparador de Itens")
    st.sidebar.page_link("pages/itens_por_level.py", label="Itens por Level")
    st.sidebar.page_link("pages/xp.py", label="Cálculo de XP Base")
    
    # Links para funcionalidades futuras (desabilitados)
    st.sidebar.page_link("pages/home.py", label="Hunts", disabled=True)
    st.sidebar.page_link("pages/home.py", label="Imbuements", disabled=True)
    st.sidebar.page_link("pages/home.py", 
                          label="Roteiro de acessos", 
                          disabled=True)
    st.sidebar.page_link("pages/home.py", label="Regeneração", disabled=True)
    st.sidebar.page_link("pages/home.py", 
                          label="Cálculo de treino", 
                          disabled=True)
    st.sidebar.page_link("pages/home.py", 
                          label="Itemização (crawler no wiki)", 
                          disabled=True)
    st.sidebar.page_link("pages/home.py", 
                          label="Cálculo de exp (previsão de level)", 
                          disabled=True)
    st.sidebar.page_link("pages/home.py", 
                          label="Cálculo de forja", 
                          disabled=True)
    
    st.sidebar.caption('Configurações')
    st.sidebar.page_link("pages/perfil.py", 
                          label="Perfil (lista de chars + equip)", 
                          disabled=True)
    
    st.sidebar.divider()
    st.sidebar.write("Usuário: Visitante")


def menu_with_redirect():
    """Versão simplificada para compatibilidade com páginas existentes."""
    # Configurar estado de sessão para compatibilidade
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = True
    if "role" not in st.session_state:
        st.session_state.role = "user" 
    if "name" not in st.session_state:
        st.session_state.name = "Visitante"
        
    menu()
    