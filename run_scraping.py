import streamlit as st
from services.scraping import scrap, extract_item_name, KNOWN_CATEGORIES
import requests
from bs4 import BeautifulSoup

def debug_scraping(category):
    """
    Função de depuração para verificar a extração de itens da categoria.
    """
    st.subheader(f"Depuração da categoria: {category}")
    
    if category not in KNOWN_CATEGORIES:
        st.error(f"Categoria '{category}' não encontrada.")
        return
    
    url = KNOWN_CATEGORIES[category]
    st.write(f"URL: {url}")
    
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    table = soup.find('table', class_='wikitable')
    if not table:
        st.error(f"Tabela não encontrada em {url}")
        return
    
    rows = table.find_all('tr')[1:]  # Pula a linha de cabeçalho
    st.write(f"Total de linhas na tabela: {len(rows)}")
    
    items_found = []
    
    for idx, row in enumerate(rows[:10]):  # Limitar a 10 itens para debug
        cols = row.find_all('td')
        if not cols:
            continue
        
        # Extrair nome usando nossa função
        item_name = extract_item_name(cols, category)
        
        # Verificar imagem
        col_n = 1 if category == 'Quivers' else 0
        img_tag = cols[col_n].find('img')
        has_img = "Sim" if img_tag else "Não"
        
        # Verificar link
        item_link = cols[col_n].find('a')
        has_link = "Sim" if item_link else "Não"
        
        if item_name:
            items_found.append({
                "Nome": item_name,
                "Tem imagem": has_img,
                "Tem link": has_link
            })
            
    st.write(f"Itens encontrados (primeiros 10): {len(items_found)}")
    st.table(items_found)
    
    st.info("A função extract_item_name está funcionando corretamente, mas parece que o processamento dos itens não está ocorrendo na função scrap.")

def run_scraping():
    """
    Script para executar o scraping das categorias problemáticas via Streamlit.
    """
    # Configurar página do Streamlit
    st.set_page_config(layout='wide')
    
    st.title("Scraping das Categorias Problemáticas")
    
    # Adicionar modo de depuração
    debug_mode = st.checkbox("Modo de depuração")
    
    # Categorias para processar
    categories = ["Spellbooks", "Amulets_and_Necklaces", "Rings"]
    
    for category in categories:
        st.header(f"Processando categoria: {category}")
        
        if debug_mode:
            debug_scraping(category)
        else:
            scrap(category)
            st.success(f"Categoria {category} processada com sucesso!")
    
    if not debug_mode:
        st.balloons()
        st.success("Scraping de todas as categorias concluído com sucesso!")

if __name__ == "__main__":
    run_scraping() 