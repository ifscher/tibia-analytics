import streamlit as st
from utils.config import is_development


def center_content(content):
    return f"""
    <div style="display: flex; justify-content: center;">
        {content}
    </div>
    """


def menu():
    """Exibe o menu de navegação lateral sem requisito de login."""
    is_dev = is_development()
    
    if is_dev:
        st.sidebar.caption('Dashboard (Development)')
    else:
        st.sidebar.caption('Dashboard')
    
    # st.sidebar.page_link("pages/home.py", label="Home")

    # 
    st.sidebar.caption('Itens')
    st.sidebar.page_link("pages/itens_por_level.py", label="Itens por Level")
    st.sidebar.page_link("pages/comparador.py", label="Comparador de Itens")
    st.sidebar.page_link("pages/detalhes_item.py", label="Detalhes do Item")

    # Exp, custos de boost e etc
    st.sidebar.caption('Exp, custos de boost e etc')
    st.sidebar.page_link("pages/boost.py", label="Custos de Boost")
    st.sidebar.page_link("pages/xp.py", label="Cálculo de XP Base")
    
    
    
    
    # Links para funcionalidades futuras (desabilitados)
    # st.sidebar.page_link("pages/home.py", label="Hunts", disabled=True)
    # st.sidebar.page_link("pages/home.py", label="Imbuements", disabled=True)
    # st.sidebar.page_link("pages/home.py", 
    #                     label="Roteiro de acessos", 
    #                     disabled=True)
    # st.sidebar.page_link("pages/home.py", label="Regeneração", disabled=True)
    # st.sidebar.page_link("pages/home.py", 
    #                     label="Cálculo de treino", 
    #                     disabled=True)
    # st.sidebar.page_link("pages/home.py", 
    #                     label="Itemização (crawler no wiki)", 
    #                     disabled=True)
    # st.sidebar.page_link("pages/home.py", 
    #                     label="Cálculo de exp (previsão de level)", 
    #                     disabled=True)
    # st.sidebar.page_link("pages/home.py", 
    #                     label="Cálculo de forja", 
    #                     disabled=True)
    
        
    # Menus que só aparecem em desenvolvimento
    if is_dev:
        st.sidebar.caption('Configurações')
        st.sidebar.page_link("pages/itens.py", label="Itens")
        st.sidebar.page_link("pages/perfil.py", 
                        label="Perfil (lista de chars + equip)", 
                        disabled=True)
    
    # st.sidebar.divider()
    # if is_dev:
    #     st.sidebar.write("Usuário: Visitante (Dev)")
    # else:
    #     st.sidebar.write("Usuário: Visitante")


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
    