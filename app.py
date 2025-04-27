import streamlit as st
from utils.favicon import set_config
from utils.menu import menu

# Configurar a página inicial
set_config(title="Home")

# Inicializar variáveis de sessão (para compatibilidade com código existente)
if "role" not in st.session_state:
    st.session_state.role = "user"
if "name" not in st.session_state:
    st.session_state.name = "Visitante"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = True

# Exibir o menu de navegação
menu()

# Página inicial
st.title("Tibia Analytics")
st.markdown(
    "Bem-vindo ao Tibia Analytics! Use o menu lateral para navegar pelas "
    "diferentes funcionalidades."
)

# Mostrar conteúdo principal da página
st.header("Recursos Disponíveis")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Itens e Equipamentos")
    st.write("• Consulta de itens por categoria")
    st.write("• Comparação de itens")
    st.write("• Detalhes completos de cada item")
    st.write("• Seleção de itens por level")

with col2:
    st.subheader("Análises")
    st.write("• Custos de boost para diferentes vocações")
    st.write("• Mais análises serão adicionadas em breve!")

# st.info("Este é um aplicativo sem login para facilitar o acesso às informações.")