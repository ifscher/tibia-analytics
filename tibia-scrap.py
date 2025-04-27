import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

# Lista de URLs das páginas da wiki para scraping
urls = [
    "https://tibia.fandom.com/wiki/Helmets",
    # "https://tibia.fandom.com/wiki/Armors",
    # "https://tibia.fandom.com/wiki/Legs",
    # "https://tibia.fandom.com/wiki/Boots",
    # "https://tibia.fandom.com/wiki/Shields",
    # "https://tibia.fandom.com/wiki/Spellbooks",
    # "https://tibia.fandom.com/wiki/Amulets_and_Necklaces",
    # "https://tibia.fandom.com/wiki/Rings",
    # "https://tibia.fandom.com/wiki/Quivers",
]

# Lista para armazenar todos os dados coletados
all_data = []

# Processa cada URL da lista
for url in urls:
    # Extrai a categoria da URL (ex: "Helmets", "Armors", etc)
    category = url.split("wiki/")[-1]

    # Faz a requisição HTTP e parseia o HTML
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Localiza a tabela principal com os dados dos itens
    table = soup.find('table', class_='wikitable')
    if not table:
        st.warning(f"Tabela não encontrada em {url}")
        continue

    # Extrai os cabeçalhos da tabela
    ths = table.find_all('th')
    if len(ths) < 2:
        st.warning(f"Não encontrei cabeçalhos suficientes em {url}")
        continue

    # Coleta os nomes das colunas
    headers = []
    for header in ths:
        headers.append(header.text.strip())

    # Processa cada linha da tabela (pula o cabeçalho)
    rows = table.find_all('tr')[1:]

    for row in rows:
        cols = row.find_all('td')
        if not cols:
            continue

        # Extrai nome e imagem do item
        col_n = 1 if category == 'Quivers' else 0
        img_tag = cols[col_n].find('img')
        
        # O nome do item está no atributo title do link
        item_link = cols[col_n].find('a')
        if item_link:
            item_name = item_link.get('title', '').strip()
            if not item_name:  # fallback para o texto do link
                item_name = item_link.text.strip()
        else:
            continue

        # Processa a URL da imagem
        if img_tag:
            img_url = img_tag.get('data-src') or ""
            if img_url and 'format=original' not in img_url:
                img_url += '&format=original'
        else:
            img_url = ""

        # Coleta dados de todas as colunas
        col_data = []
        for col in cols:
            col_data.append(col.text.strip())

        # Monta o dicionário com os dados do item
        row_dict = {
            'Category': category,
            'Item': item_name,
            'image_path': img_url
        }
        
        # Processa os dados das outras colunas
        for idx_col, col_name in enumerate(headers[1:]):
            valor = col_data[idx_col + 1]
            if col_name == "":
                continue

            # Trata colunas especiais que contêm listas
            if col_name.lower() == "attributes" or col_name.lower() == "resist.":
                row_dict[col_name] = [v.strip() for v in valor.split(",") if v.strip()]
            else:
                row_dict[col_name] = valor

        all_data.append(row_dict)

# Cria o DataFrame com todos os dados coletados
df = pd.DataFrame(all_data)

# Exibe o DataFrame no Streamlit com configuração de colunas
st.dataframe(
    df,
    column_config={
        "image_path": st.column_config.ImageColumn(
            "Imagem",
            help="Imagem do item"
        ),
        "Item": "Nome do Item",
        "Category": "Categoria",
        "Def": "Defesa",
        "Arm": "Armadura",
        "Attributes": "Atributos",
        "Resist.": "Resistências"
    },
    hide_index=True
)

# Salva os dados em um arquivo CSV
df.to_csv('tibia_items.csv', index=False)
