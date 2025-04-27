import streamlit as st
from utils.menu import menu_with_redirect
from utils.favicon import set_config
import pandas as pd

# Importa as funções do nosso arquivo de banco
from mydb import read_all_items, delete_items_by_category
from services.scraping import scrap

set_config(title="Itens")

# Redireciona se não estiver logado, etc.
menu_with_redirect()

st.title("Itens")

# Adicionar opções de atualização por categoria
st.header("Gerenciar Categorias de Itens")

# Lista de todas as categorias disponíveis
categories = [
    "Helmets", "Armors", "Legs", "Boots", "Shields", "Spellbooks",
    "Amulets_and_Necklaces", "Rings", "Quivers", "Wands", "Rods",
    "Axes", "Clubs", "Swords", "Fist_Fighting_Weapons", "Throwing_Weapons"
]

# Botões para operações com todas as categorias
st.subheader("Operações em Massa")

col1, col2 = st.columns(2)
with col1:
    if st.button("Atualizar Todas", type="primary", use_container_width=True):
        with st.spinner("Atualizando todas as categorias..."):
            scrap()
        st.success("Todas as categorias foram atualizadas com sucesso!")
        st.rerun()

with col2:
    if st.button("Deletar Todas", type="secondary", use_container_width=True):
        # Confirmação antes de deletar
        if st.checkbox("Confirmar deleção?", key="confirm_all_delete"):
            with st.spinner("Deletando todos os itens do banco de dados..."):
                total_deleted = 0
                for category in categories:
                    deleted = delete_items_by_category(category)
                    total_deleted += deleted
            
            if total_deleted > 0:
                st.success(f"{total_deleted} itens foram removidos.")
            else:
                st.info("Não foram encontrados itens para remover.")
            st.rerun()

# Interface para gerenciar categorias individuais
st.subheader("Gerenciar Categorias Individuais")

# Criar colunas de cabeçalho para a tabela
tab = st.container()
header_col1, header_col2, header_col3 = tab.columns([2, 1, 1])
with header_col1:
    st.write("**Categoria**")
with header_col2:
    st.write("**Atualizar**")
with header_col3:
    st.write("**Deletar**")

# Adicionar linha divisória
st.divider()

# Exibir cada categoria com seus botões
for category in categories:
    display_name = category.replace("_", " ")
    
    # Criar uma linha para cada categoria
    col1, col2, col3 = st.columns([2, 1, 1])
    
    # Nome da categoria
    with col1:
        st.write(f"{display_name}")
    
    # Botão de atualizar
    with col2:
        update_btn = st.button("Atualizar", key=f"update_{category}")
        
    # Botão de deletar
    with col3:
        delete_btn = st.button("🗑️", key=f"delete_{category}")
    
    # Processar ações dos botões
    if update_btn:
        with st.spinner(f"Atualizando {display_name}..."):
            scrap(category)
        st.success(f"Categoria {display_name} atualizada com sucesso!")
        st.rerun()
    
    if delete_btn:
        with st.spinner(f"Deletando itens da categoria {display_name}..."):
            deleted = delete_items_by_category(category)
        st.success(f"{deleted} itens da categoria {display_name} foram deletados.")
        st.rerun()

st.divider()

# ----- CONTINUA DO scraping.py

# 4) Agora, LER DO BANCO e montar DataFrame para exibir
st.header("Dados do Banco")

# Link para a página de detalhes
st.info("Para visualizar detalhes completos de um item, acesse a página "
        "[Detalhes do Item](/Detalhes_Item)")

# Exemplo: ler tudo e agrupar por categoria
all_items = read_all_items()
if not all_items:
    st.write("Sem itens no banco!")
else:
    # Vamos converter para DataFrame
    df = pd.DataFrame(all_items)
    df = df[['image_path', 'item_name', 'category', 'data_json']]

    # Exibe o DataFrame original
    st.write("### Itens Registrados")
    st.dataframe(
        df,
        column_config={
            "image_path": st.column_config.ImageColumn(
                "Imagem",
                help="Sprite do item"
            ),
            "item_name": "Item Name",
            "category": "Category",
            "data_json": "Data",
        },
        hide_index=True,
    )

    # Mostra estatísticas
    st.subheader("Estatísticas")
    st.write(f"Total de itens: {len(df)}")
    
    # Agrupar por categoria
    category_counts = df['category'].value_counts().reset_index()
    category_counts.columns = ['Categoria', 'Quantidade']
    
    # Exibir como gráfico de barras e tabela
    st.bar_chart(category_counts, x='Categoria', y='Quantidade')
    st.dataframe(category_counts)

st.write("TODO: separar adequadamente as informações da Data para que possam ser utilizadas nos cálculos")