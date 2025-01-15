import streamlit as st
import hmac
from utils.favicon import LOGO_FULL_NEGATIVO


def center_content(content):
    return f"""
    <div style="display: flex; justify-content: center;">
        {content}
    </div>
    """


def _check_password():
    """Authenticate user and manage login state."""
    if st.session_state.get("authenticated"):
        return True

    with st.form("Credentials"):
        # ---------------------
        # Linha 1: 3 colunas para a imagem
        # ---------------------
        _, cent_col2, _ = st.columns([1, 1.5, 1])
        with cent_col2:
            st.image(LOGO_FULL_NEGATIVO)
        
        # ---------------------
        # Linha 2: 3 colunas com apenas a do meio contendo os inputs
        # ---------------------
        col4 = st.columns(1)[0]
        with col4:
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")

        # ---------------------
        # Linha 3: 3 colunas para o botão de login
        # ---------------------
        _, cent_col_button, _ = st.columns([3, 1, 3])
        with cent_col_button:
            submitted = st.form_submit_button("Log in")

    if submitted:
        if username in st.secrets["passwords"] and hmac.compare_digest(
            password,
            st.secrets.passwords[username],
        ):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.name = st.secrets.names.get(username, "name")
            st.session_state.role = st.secrets.roles.get(username, "user")  # Default to "user" if role not specified
            # st.rerun()
            st.switch_page("pages/home.py")
        else:
            st.error("Usuário desconhecido ou senha incorreta.")

    return False


def _authenticated_menu():
    # Show a navigation menu for authenticated users
    st.sidebar.caption('Dashboard')
    st.sidebar.page_link("pages/home.py", label="Home")
    st.sidebar.page_link("pages/boost.py", label="Custos de Boost")
    st.sidebar.page_link("pages/itens.py", label="Itens")
    st.sidebar.page_link("pages/home.py", label="Cálculo de XP Base", disabled=True)
    st.sidebar.page_link("pages/home.py", label="Hunts", disabled=True)
    st.sidebar.page_link("pages/home.py", label="Imbuements", disabled=True)
    st.sidebar.page_link("pages/home.py", label="Roteiro de acessos", disabled=True)
    st.sidebar.page_link("pages/home.py", label="Regeneração", disabled=True)
    st.sidebar.page_link("pages/home.py", label="Cálculo de treino", disabled=True)
    st.sidebar.page_link("pages/home.py", label="Itemização (crawler no wiki)", disabled=True)
    st.sidebar.page_link("pages/home.py", label="Cálculo de exp (previsão de level)", disabled=True)
    st.sidebar.page_link("pages/home.py", label="Cálculo de forja", disabled=True)
    
    st.sidebar.caption('Configurações')
    st.sidebar.page_link("pages/perfil.py", label="Perfil (lista de chars + equip)", disabled=True)
    
    # if st.session_state.role in ["admin", "super-admin"]:
    #     st.sidebar.page_link("pages/admin.py", label="Admin User Page")
    # st.sidebar.page_link(
    #     "pages/super-admin.py",
    #     label="Super Admin User Page",
    #     disabled=st.session_state.role != "super-admin",
    # )
    st.sidebar.divider()
    st.sidebar.write(f"{st.session_state.name}")
    # st.sidebar.write(f"Your role is: {st.session_state.role}")
    if st.sidebar.button("Logout"):
        _logout()


def _unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    # st.sidebar.page_link("home.py", label="Log in")
    pass


def _logout():
    """Log out the current user."""
    st.session_state.clear()
    st.success("You have been logged out successfully.")
    st.rerun()


def menu():
    # Determine if a user is logged in or not, then show the correct
    if not _check_password():
        _unauthenticated_menu()
        st.stop()
    else:
        _authenticated_menu()


def menu_with_redirect():
    # Redirect users to the main page if not logged in, otherwise continue to
    # render the navigation menu
    if not _check_password():
        st.switch_page("app.py")
    menu()
    