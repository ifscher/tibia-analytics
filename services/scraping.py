import streamlit as st
from mydb import download_image_if_needed, create_table, upsert_item
import requests
from bs4 import BeautifulSoup
from utils.core import to_data_url


def scrap():
    # 1) Lista de URLs
    urls = [
        "https://tibia.fandom.com/wiki/Helmets",
        "https://tibia.fandom.com/wiki/Armors",
        "https://tibia.fandom.com/wiki/Legs",
        "https://tibia.fandom.com/wiki/Boots",
        "https://tibia.fandom.com/wiki/Shields",
        "https://tibia.fandom.com/wiki/Spellbooks",
        "https://tibia.fandom.com/wiki/Amulets_and_Necklaces",
        "https://tibia.fandom.com/wiki/Rings",
        "https://tibia.fandom.com/wiki/Quivers",
    ]

    # 2) Garante que a tabela exista
    create_table()

    # 3) Primeiro: Scraping + Inserção no Banco
    for url in urls:
        category = url.split("wiki/")[-1]  # "Helmets", "Armors", etc.
        # st.write(category)

        # Pega a página
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find('table', class_='wikitable')
        if not table:
            st.warning(f"Tabela não encontrada em {url}")
            continue
        # st.write(table)

        # Captura cabeçalhos (2º <th> em diante)
        ths = table.find_all('th')
        if len(ths) < 2:
            st.warning(f"Não encontrei cabeçalhos suficientes em {url}")
            continue
        # st.write(ths)

        # Por exemplo, headers = ["Image", "Item", "Def", "Arm", etc...]
        headers = ["Image"]
        for header in ths[1:]:
            headers.append(header.text.strip())
        # st.write(headers)
        
        # Captura linhas
        rows = table.find_all('tr')[1:]
        # st.write(rows)

        for row in rows:
            # st.write(row['Image'])
            cols = row.find_all('td')
            if not cols:
                continue

            # 1) Nome e Imagem
            col_n = 1 if category == 'Quivers' else 0
            # st.write(cols[col_n].find('img'))
            img_tag = cols[col_n].find('img')
            if img_tag:
                img_url = img_tag.get('data-src') or ""
                if img_url and 'format=original' not in img_url:
                    img_url += '&format=original'
                
                item_name = img_tag.get('alt')
                # st.write(item_name, img_url)
            else:
                # img_url, item_name = "", ""
                continue  # pular itens que não tem img_url nem nome pra não inserir "" no banco

            # 2) Outras colunas
            col_data = []
            for col in cols[1:]:
                # st.write(col)
                col_data.append(col.text.strip())

            # st.write(col_data)

            # Montar dict com base nos headers[1:]
            # Ex.: {"Item": "...", "Def": "...", "Arm": "...", ...}
            row_dict = {}
            for idx_col, col_name in enumerate(headers[1:]):
                valor = col_data[idx_col]
                # Se for "Attributes", separar por vírgula
                if col_name == "":
                    continue

                if col_name.lower() == "attributes" or col_name.lower() == "resist.":
                    row_dict[col_name] = [v.strip() for v in valor.split(",") if v.strip()]
                else:
                    row_dict[col_name] = valor
            # st.write(row_dict)

            # 3) Baixar a imagem local (retorna local_path)
            image_path_local = download_image_if_needed(item_name, img_url)

            # 4) Inserir no banco
            upsert_item(item_name, category, to_data_url(image_path_local), row_dict)

    st.success("Scraping + Inserção no banco concluídos.")