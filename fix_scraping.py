import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import json
import os
from services.scraping import create_table, process_and_save_item, extract_item_details, image_exists
from mydb import read_item

# Lista de categorias problemáticas
PROBLEM_CATEGORIES = {
    "Spellbooks": "https://tibia.fandom.com/wiki/Spellbooks",
    "Amulets_and_Necklaces": "https://tibia.fandom.com/wiki/Amulets_and_Necklaces",
    "Rings": "https://tibia.fandom.com/wiki/Rings"
}

def extract_item_name(cols, cat):
    """
    Versão simplificada da função extract_item_name para extração robusta de nomes.
    """
    col_n = 1 if cat == 'Quivers' else 0
    
    # Primeiro tentar extrair o nome do link (se existir)
    item_link = cols[col_n].find('a')
    if item_link:
        # Tentar primeiro o atributo title
        item_name = item_link.get('title', '').strip()
        # Se não tiver title, usar o texto do link
        if not item_name:
            item_name = item_link.text.strip()
    else:
        # Se não tiver link, extrair o texto da coluna
        item_name = cols[col_n].text.strip()
    
    return item_name

def fix_scraping():
    """
    Script para corrigir o scraping das categorias problemáticas.
    """
    st.set_page_config(layout='wide')
    st.title("Correção de Scraping para Categorias Problemáticas")
    
    # Garantir que a tabela exista
    create_table()
    
    # Contador para mostrar progresso
    total_items = 0
    processed_items = 0
    images_skipped = 0
    
    # Processar cada categoria problemática
    for cat, url in PROBLEM_CATEGORIES.items():
        cat_processed_items = 0
        st.header(f"Processando categoria: {cat}")
        
        # Log da URL
        st.write(f"URL: {url}")
        
        # Fazer a solicitação HTTP
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encontrar a tabela de itens
        table = soup.find('table', class_='wikitable')
        if not table:
            st.error(f"Tabela não encontrada em {url}")
            continue
        
        # Obter todas as linhas (pular o cabeçalho)
        rows = table.find_all('tr')[1:]
        total_items += len(rows)
        
        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        st.write(f"Encontrado {len(rows)} linhas na tabela")
        
        # Analisar a estrutura da tabela para determinar a coluna da imagem
        # Verificar a primeira linha para determinar onde estão as imagens
        first_row = rows[0] if rows else None
        img_col_index = None
        
        if first_row:
            cols = first_row.find_all('td')
            for i, col in enumerate(cols):
                if col.find('img'):
                    img_col_index = i
                    st.info(f"Detectada coluna de imagem: {i+1}")
                    break
        
        if img_col_index is None:
            st.warning("Não foi possível detectar automaticamente a coluna da imagem. Usando coluna 1.")
            img_col_index = 1
        
        # Processar cada linha
        for idx, row in enumerate(rows):
            # Obter todas as células da linha
            cols = row.find_all('td')
            if not cols:
                continue
            
            # Extrair o nome do item (usando nossa função robusta)
            item_name = extract_item_name(cols, cat)
            
            # Verificar se há imagem na coluna detectada
            img_tag = None
            if img_col_index < len(cols):
                img_tag = cols[img_col_index].find('img')
            
            # Se não encontrou na coluna detectada, procurar em todas as colunas
            if not img_tag:
                for i, col in enumerate(cols):
                    img_tag = col.find('img')
                    if img_tag:
                        if idx < 3:
                            st.write(f"  - Imagem encontrada na coluna {i+1} (alternativa)")
                        break
            
            # Se ainda não tiver imagem, continuar mesmo assim
            if img_tag:
                img_url = img_tag.get('data-src') or img_tag.get('src') or ""
                if img_url and 'format=original' not in img_url:
                    img_url += '&format=original'
            else:
                img_url = ""
            
            # Verificar se há link para a página do item
            item_link = None
            for td in cols:
                link = td.find('a')
                if link and link.get('href'):
                    item_link = link
                    break
            
            # Formar a URL da página do item
            if item_link and item_link.get('href'):
                item_url = f"https://tibia.fandom.com{item_link.get('href')}"
            else:
                # Se não tiver link, tentar criar a URL a partir do nome
                item_url = f"https://tibia.fandom.com/wiki/{item_name.replace(' ', '_')}"
            
            # Exibir status
            status_text.text(f"Processando '{item_name}' ({idx+1}/{len(rows)})")
            
            # Mostrar detalhes para os primeiros 3 itens
            if idx < 3:
                st.write(f"Item {idx+1}: '{item_name}'")
                if img_url:
                    st.write(f"  - URL imagem: {img_url[:50]}...")
                else:
                    st.write("  - Sem imagem")
                st.write(f"  - URL item: {item_url}")
            
            # Verificar se o item já existe
            existing_item = read_item(item_name)
            existing_data = {}
            if existing_item and existing_item.get("data_json"):
                try:
                    existing_data = json.loads(existing_item["data_json"])
                    if idx < 3:
                        st.write("  - Item já existe no banco")
                except Exception as e:
                    st.warning(f"Erro ao interpretar JSON: {str(e)}")
            
            # Extrair detalhes da página
            item_details = {}
            try:
                item_details = extract_item_details(item_url)
                if idx < 3 and item_details:
                    st.write("  - Detalhes extraídos com sucesso")
                elif idx < 3:
                    st.write("  - Nenhum detalhe extraído")
                # Pequena pausa para não sobrecarregar o servidor
                time.sleep(0.5)
            except Exception as e:
                st.warning(f"Erro ao extrair detalhes de {item_url}: {str(e)}")
            
            # Juntar os dados existentes com os novos
            row_dict = {**existing_data, **item_details}
            
            # Processar e salvar o item
            if item_name:
                try:
                    process_and_save_item(item_name, row_dict, cat, img_url)
                    processed_items += 1
                    cat_processed_items += 1
                    if idx < 3:
                        st.write("  - Processado e salvo com sucesso!")
                    
                    # Contar imagens reutilizadas
                    if image_exists(item_name):
                        images_skipped += 1
                except Exception as e:
                    st.error(f"Erro ao salvar {item_name}: {str(e)}")
            
            # Atualizar progresso
            progress_bar.progress((idx + 1) / len(rows))
        
        # Exibir resumo da categoria
        st.success(f"Categoria {cat} processada: {cat_processed_items} itens salvos")
    
    # Exibir resumo final
    st.success(f"Scraping concluído: {processed_items} itens processados, {images_skipped} imagens reutilizadas")
    st.balloons()

if __name__ == "__main__":
    fix_scraping() 