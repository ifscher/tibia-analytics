import streamlit as st
from utils.menu import menu_with_redirect
from utils.favicon import set_config

import pandas as pd

# Importa as funções do nosso arquivo de banco
from mydb import read_all_items
from services.scraping import scrap


set_config(title="Itens")


# Redireciona se não estiver logado, etc.
menu_with_redirect()

st.title("Itens")

# ----- CONTINUA DO scraping.py

# 4) Agora, LER DO BANCO e montar DataFrame para exibir
st.header("Exibindo dados do banco")

# Exemplo: ler tudo e agrupar por categoria
all_items = read_all_items()
if not all_items:
    st.write("Sem itens no banco!")
else:
    # Vamos converter para DataFrame
    df = pd.DataFrame(all_items)
    # Exemplo: se 'image_path' quiser virar URL, use "file://..." ou data URL.
    # Mas se for local e seu Streamlit não serve estáticos, tente colunas base64 ou
    # outro meio (ou apenas exiba 'image_path' como texto).
    
    # Se você quiser exibir a coluna 'image_path' como imagem no st.dataframe,
    # precisaria transformá-la em URL acessível ou data URL, pois st.column_config.ImageColumn
    # requer algo que o front-end possa carregar (URL pública ou data url).
    # Exemplo rápido de URL local (não funciona em Streamlit Cloud sem servir estáticos):
    # df["Image"] = df["image_path"]  # renomear a col p/ "Image" e ver se streamlit exibe
    df = df[['image_path', 'item_name', 'category', 'data_json']]

    # for item in all_items:
    #     st.write(item)
    
    # Exibe
    st.dataframe(
        df,
        column_config={
            "image_path": st.column_config.ImageColumn(
                "Imagem",
                help="Carregada localmente (pode não aparecer se não for URL pública)"
            ),
            "item_name": "Item Name",
            "category": "Category",
            "data_json": "Data",
        },
        hide_index=True,
    )

if st.button("Recarregar Tabela"):
    scrap()

st.write("TODO: separar adequadamente as informações da Data para que possam ser utilizadas nos cálculos")