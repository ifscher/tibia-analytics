import streamlit as st
from utils.menu import menu_with_redirect
from utils.favicon import set_config


set_config(title="Home")

# Exibir o menu de navegação sem verificação de login
menu_with_redirect()

st.title("Tibia Analytics - Home")
st.markdown("""
Bem-vindo ao Tibia Analytics!

Esta plataforma oferece diversas ferramentas para análise de dados do jogo 
Tibia:

- **Itens e Equipamentos**: Visualize, compare e filtre itens do jogo
- **Custos de Boost**: Calcule o custo de boost para diferentes vocações
- **Comparador de Itens**: Compare características de diferentes itens
- **Itens por Level**: Descubra os melhores itens disponíveis para seu level

Utilize o menu lateral para navegar entre as diferentes funcionalidades.
""")

# Exibir imagem ou conteúdo adicional se necessário
# st.image("utils/favicon/logo_full_negativo.png", width=300)