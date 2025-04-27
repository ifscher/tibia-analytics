import streamlit as st
from mydb import download_image_if_needed, create_table, upsert_item, read_item
import requests
from bs4 import BeautifulSoup
import time
import json
import os
from utils.core import to_data_url
import re

# Lista de categorias conhecidas
KNOWN_CATEGORIES = {
    "Helmets": "https://tibia.fandom.com/wiki/Helmets",
    "Armors": "https://tibia.fandom.com/wiki/Armors",
    "Legs": "https://tibia.fandom.com/wiki/Legs",
    "Boots": "https://tibia.fandom.com/wiki/Boots",
    "Shields": "https://tibia.fandom.com/wiki/Shields",
    "Spellbooks": "https://tibia.fandom.com/wiki/Spellbooks",
    "Amulets_and_Necklaces": (
        "https://tibia.fandom.com/wiki/Amulets_and_Necklaces"),
    "Rings": "https://tibia.fandom.com/wiki/Rings",
    "Quivers": "https://tibia.fandom.com/wiki/Quivers",
    "Wands": "https://tibia.fandom.com/wiki/Wands",
    "Rods": "https://tibia.fandom.com/wiki/Rods",
    "Axes": "https://tibia.fandom.com/wiki/Axes",
    "Clubs": "https://tibia.fandom.com/wiki/Clubs",
    "Swords": "https://tibia.fandom.com/wiki/Swords",
    "Fist_Fighting_Weapons": (
        "https://tibia.fandom.com/wiki/Fist_Fighting_Weapons"),
    "Throwing_Weapons": "https://tibia.fandom.com/wiki/Throwing_Weapons",
}


def image_exists(item_name, folder="utils/img"):
    """
    Verifica se a imagem já existe localmente.
    
    Args:
        item_name (str): Nome do item para verificar
        folder (str): Pasta onde as imagens são armazenadas
        
    Returns:
        str: Caminho da imagem se existir, None caso contrário
    """
    # Verificar no banco se já temos esta imagem
    existing_item = read_item(item_name)
    if existing_item and existing_item.get("image_path"):
        image_path = existing_item["image_path"]
        
        # Verificar se o caminho é um data URL ou um caminho de arquivo
        if image_path.startswith("data:"):
            return image_path  # Já é um data URL, não precisa baixar novamente
        
        # Se é um caminho de arquivo, verificar se o arquivo existe
        if os.path.exists(image_path):
            return image_path
            
    # Verificar possíveis nomes de arquivo na pasta de imagens
    # (útil caso o item exista mas o caminho no banco esteja incorreto)
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            name_without_ext = os.path.splitext(filename)[0]
            
            # Tentar diferentes formatos de nome: original, sem espaços, etc.
            clean_item_name = item_name.replace(" ", "_").lower()
            clean_filename = name_without_ext.replace(" ", "_").lower()
            
            if clean_item_name == clean_filename:
                return os.path.join(folder, filename)
    
    # Não encontrou imagem existente
    return None


def process_special_values(value):
    """
    Processa valores especiais, convertendo símbolos para valores booleanos.
    
    Args:
        value: Valor a ser processado (string ou lista)
        
    Returns:
        Valor processado
    """
    if isinstance(value, str):
        # Substituir símbolos por valores booleanos
        if value == "✓":
            return True
        elif value == "✗":
            return False
        # Processar strings de resistências (ex: "ice +12%, fire -6%")
        elif any(element in value.lower() for element in [
                "ice", "fire", "earth", "energy", "physical", "holy", "death"
                ]) and "%" in value:
            resistances = {}
            # Dividir por vírgula ou espaço se não houver vírgula
            parts = value.split(",") if "," in value else value.split()
            
            for part in parts:
                part = part.strip()
                # Procurar padrões como "ice +12%" ou "fire -6%"
                for element in ["ice", "fire", "earth", "energy", 
                                "physical", "holy", "death"]:
                    if element.lower() in part.lower():
                        # Extrair o valor numérico (com sinal)
                        match = re.search(r'([+-]?\d+)', part)
                        if match:
                            # Converter para inteiro e remover o símbolo de %
                            value_str = match.group(1)
                            resistances[element.lower()] = int(value_str)
            
            # Retornar um dicionário vazio se não encontrou nenhuma resistência
            return resistances if resistances else value
        # Processar strings de atributos (ex: "distance fighting +3")
        elif " +" in value or " -" in value:
            # Verificar se parece com um atributo
            match = re.search(r'(.*?)\s+([+-]?\d+)$', value.lower().strip())
            if match:
                attr_name = match.group(1).strip()
                attr_value = int(match.group(2))
                return {attr_name: attr_value}
        return value
    elif isinstance(value, list):
        # Tratamento especial para o campo Version - manter como string
        if len(value) > 0 and any("update" in item.lower() for item in value):
            # É provável que seja uma lista de informações de versão
            return " ".join(value)
        
        # Verificar se é uma lista de atributos (como "magic level +3")
        if all(isinstance(item, str) for item in value):
            # Verificar se parece com uma lista de atributos
            attr_pattern = r'(.*?)\s+([+-]?\d+)$'
            
            attributes = {}
            is_attribute_list = False
            
            for item in value:
                match = re.search(attr_pattern, item.lower().strip())
                if match:
                    is_attribute_list = True
                    attr_name = match.group(1).strip()
                    attr_value = int(match.group(2))
                    attributes[attr_name] = attr_value
            
            # Se todos ou a maioria dos itens são atributos, retornar como dicionário
            if is_attribute_list and attributes:
                return attributes
        
        # Processar cada item da lista normalmente
        return [process_special_values(item) for item in value]
    else:
        return value


def process_numeric_fields(key, value):
    """
    Processa campos que devem ser convertidos para números.
    
    Args:
        key: Nome do campo
        value: Valor a ser processado
        
    Returns:
        Valor processado (convertido para número quando aplicável)
    """
    # Campos que devem ser inteiros
    int_fields = [
        "Imbuing Slots", "Upgrade Classification", "Armor", "Defense",
        "Attack", "Level", "Capacity"
    ]
    
    # Campos que devem ser floats
    float_fields = ["Weight", "Speed"]
    
    # Campos que podem ter ranges (ex: "50-60" ou "50 (45-55)")
    range_fields = ["Damage", "Range", "Attack"]
    
    if isinstance(value, str):
        # Processar campos de range
        if key in range_fields and (
                "-" in value or "(" in value and ")" in value):
            range_pattern = r'(\d+)\s*-\s*(\d+)'
            paren_pattern = r'(\d+)\s*\((\d+)\s*-\s*(\d+)\)'
            
            # Verificar padrão de parênteses primeiro (mais específico)
            paren_match = re.search(paren_pattern, value)
            if paren_match:
                base = int(paren_match.group(1))
                min_val = int(paren_match.group(2))
                max_val = int(paren_match.group(3))
                return {
                    "base": base,
                    "min": min_val,
                    "max": max_val
                }
            
            # Verificar padrão de intervalo simples
            range_match = re.search(range_pattern, value)
            if range_match:
                min_val = int(range_match.group(1))
                max_val = int(range_match.group(2))
                return {"min": min_val, "max": max_val}
        
        # Tentar converter para número se for um dos campos numéricos
        if key in int_fields:
            try:
                # Extrair apenas os dígitos se houver outros caracteres
                num_match = re.search(r'(\d+)', value)
                if num_match:
                    return int(num_match.group(1))
                return value
            except (ValueError, TypeError):
                return value
        
        if key in float_fields:
            try:
                # Converter usando regex para lidar com formatos diferentes
                num_match = re.search(r'([\d.]+)', value)
                if num_match:
                    return float(num_match.group(1))
                return value
            except (ValueError, TypeError):
                return value
    
    return value


def extract_item_details(item_url):
    """
    Extrai informações detalhadas de um item acessando sua página específica.
    
    Args:
        item_url (str): URL da página do item
        
    Returns:
        dict: Dicionário com os atributos detalhados do item
    """
    try:
        response = requests.get(item_url)
        if response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Procurar a tabela aside com as informações detalhadas
        aside = soup.find('aside', class_='portable-infobox')
        if not aside:
            return {}
        
        details = {}
        
        # 1. O primeiro h2 é geralmente o nome do item
        main_h2 = aside.find('h2', class_='pi-item pi-item-spacing pi-title')
        if main_h2:
            details["Name"] = main_h2.text.strip()
        
        # 2. Extrair sections (grupos de informações)
        sections = aside.find_all(
            'section', class_='pi-item pi-group pi-border-color')
        for section in sections:
            # Título do grupo é um h2
            group_title = section.find('h2')
            if not group_title:
                continue
                
            group_name = group_title.text.strip()
            group_data = {}
            
            # Dentro da section, encontrar todos os pares de h3 (chave) e div (valor)
            data_items = section.find_all('div', class_='pi-item')
            for item in data_items:
                # Chave: h3
                key_elem = item.find('h3')
                if not key_elem:
                    continue
                    
                key = key_elem.text.strip()
                
                # Valor: div (geralmente logo após o h3)
                value_elem = item.find('div', class_='pi-data-value')
                if not value_elem:
                    continue
                    
                # Tratar o valor - pode ser uma lista se houver quebras de linha
                value_text = value_elem.get_text(separator="\n").strip()
                
                # Tratamento especial para o campo Version
                if key == "Version":
                    group_data[key] = value_text
                    continue
                
                # Se houver quebras de linha ou vírgulas, tratar como lista
                if "\n" in value_text:
                    # Quebras de linha indicam múltiplos valores
                    value = [v.strip() for v in value_text.split("\n") 
                             if v.strip()]
                elif "," in value_text and any(kw in key.lower() for kw in [
                        "attributes", "resistances", "protection", "elements"]):
                    # Vírgulas para atributos específicos
                    value = [v.strip() for v in value_text.split(",") 
                             if v.strip()]
                else:
                    value = value_text
                
                # Processar valores especiais (✓, ✗)
                value = process_special_values(value)
                
                # Processar campos numéricos
                value = process_numeric_fields(key, value)
                
                group_data[key] = value
            
            # Adicionar o grupo ao dicionário principal
            if group_data:  # Só adiciona se tiver dados
                details[group_name] = group_data
            
        # 3. Extrair atributos fora de sections (nível mais alto do aside)
        standalone_items = aside.find_all(
            'div', class_='pi-item', recursive=False)
        for item in standalone_items:
            # Pular items que são sections (já processados acima)
            if item.name == 'section':
                continue
                
            # Extrair o mesmo padrão h3 (chave) e div (valor)
            key_elem = item.find('h3')
            if not key_elem:
                continue
                
            key = key_elem.text.strip()
            
            value_elem = item.find('div', class_='pi-data-value')
            if not value_elem:
                continue
                
            value_text = value_elem.get_text(separator="\n").strip()
            
            # Tratamento especial para o campo Version
            if key == "Version":
                details[key] = value_text
                continue
                
            # Mesmo tratamento para quebras de linha
            if "\n" in value_text:
                value = [v.strip() for v in value_text.split("\n") 
                         if v.strip()]
            elif "," in value_text and any(kw in key.lower() for kw in [
                    "attributes", "resistances", "protection", "elements"]):
                value = [v.strip() for v in value_text.split(",") 
                         if v.strip()]
            else:
                value = value_text
            
            # Processar valores especiais (✓, ✗)
            value = process_special_values(value)
            
            # Processar campos numéricos
            value = process_numeric_fields(key, value)
                
            details[key] = value
        
        return details
    
    except Exception as e:
        st.warning(f"Erro ao extrair detalhes do item: {str(e)}")
        return {}


def infer_category(item_details, item_name):
    """
    Infere a categoria de um item com base em suas propriedades.
    
    Args:
        item_details (dict): Detalhes do item extraídos
        item_name (str): Nome do item
        
    Returns:
        str: Categoria inferida do item
    """
    # 1. Verificar se temos uma classificação explícita em General Properties
    if ("General Properties" in item_details and 
            isinstance(item_details["General Properties"], dict)):
        general_props = item_details["General Properties"]
        
        # Verificar campo Classification
        if "Classification" in general_props:
            classification = general_props["Classification"]
            
            # Pode ser uma string ou uma lista
            if isinstance(classification, list):
                # Verificar cada valor da lista contra categorias conhecidas
                for cls in classification:
                    cls_clean = cls.replace(" ", "_")
                    # Verificar correspondência direta
                    if cls_clean in KNOWN_CATEGORIES:
                        return cls_clean
                    # Verificar correspondência parcial
                    for cat in KNOWN_CATEGORIES:
                        if cls_clean in cat or cat in cls_clean:
                            return cat
            elif isinstance(classification, str):
                cls_clean = classification.replace(" ", "_")
                # Verificar correspondência direta
                if cls_clean in KNOWN_CATEGORIES:
                    return cls_clean
                # Verificar correspondência parcial
                for cat in KNOWN_CATEGORIES:
                    if cls_clean in cat or cat in cls_clean:
                        return cat
    
    # 2. Tentar inferir baseado em atributos
    if ("Combat Properties" in item_details and 
            isinstance(item_details["Combat Properties"], dict)):
        combat_props = item_details["Combat Properties"]
        
        # Shields geralmente têm Def ou Defense
        if (("Def" in combat_props or "Defense" in combat_props) and 
                "Shield" in item_name):
            return "Shields"
        
        # Armors têm Armor ou Arm
        if "Armor" in combat_props or "Arm" in combat_props:
            return "Armors"
        
        # Armas têm Attack
        if "Attack" in combat_props:
            if "Throwing" in item_name:
                return "Throwing_Weapons"
            elif "Axe" in item_name:
                return "Axes"
            elif "Club" in item_name or "Hammer" in item_name:
                return "Clubs"
            elif "Sword" in item_name or "Blade" in item_name:
                return "Swords"
            elif "Wand" in item_name:
                return "Wands"
            elif "Rod" in item_name:
                return "Rods"
    
    # 3. Tentar inferir pelo nome
    if "Helmet" in item_name or "Mask" in item_name:
        return "Helmets"
    elif "Leg" in item_name or "Shorts" in item_name or "Pants" in item_name:
        return "Legs"
    elif "Boots" in item_name or "Shoes" in item_name:
        return "Boots"
    elif "Amulet" in item_name or "Necklace" in item_name:
        return "Amulets_and_Necklaces"
    elif "Ring" in item_name:
        return "Rings"
    elif "Shield" in item_name:
        return "Shields"
    elif "Spellbook" in item_name or "Book" in item_name:
        return "Spellbooks"
    elif "Quiver" in item_name:
        return "Quivers"
    
    # 4. Caso não consiga inferir, retorna Unknown
    return "Unknown"


def process_item_image(item_name, img_url):
    """
    Processa a imagem de um item, verificando se já existe e baixando se necessário.
    
    Args:
        item_name (str): Nome do item
        img_url (str): URL da imagem
        
    Returns:
        str: URL de dados da imagem ou caminho local
    """
    # Verifica se a imagem já existe
    existing_image = image_exists(item_name)
    
    if existing_image:
        # Se a imagem já existe, usar o caminho existente
        image_path_local = existing_image
    else:
        # Se não existe, baixar a imagem
        image_path_local = download_image_if_needed(item_name, img_url)
        
    # Converter a imagem para data URL se não for um
    if not existing_image or not existing_image.startswith("data:"):
        image_data_url = to_data_url(image_path_local)
    else:
        image_data_url = existing_image
        
    return image_data_url


def process_and_save_item(item_name, item_details, category, image_url):
    """
    Processa os dados de um item e salva no banco de dados.
    
    Args:
        item_name (str): Nome do item
        item_details (dict): Detalhes do item
        category (str): Categoria do item (pode ser None para inferir)
        image_url (str): URL da imagem do item
        
    Returns:
        dict: Detalhes do item processados
    """
    # Processar a imagem
    if image_url:
        image_data_url = process_item_image(item_name, image_url)
    else:
        image_data_url = ""
    
    # Inferir categoria se não fornecida
    if not category or category == "Unknown":
        category = infer_category(item_details, item_name)
    
    # Atualizar o banco de dados
    upsert_item(item_name, category, image_data_url, item_details)
    
    return item_details


def scrap_single_item(item_name):
    """
    Realiza o scraping de um único item do Tibia Wiki.
    
    Args:
        item_name (str): Nome do item para scraping.
        
    Returns:
        dict: Dados extraídos do item.
    """
    # Prepara a URL para a página do item
    base_url = f"https://tibia.fandom.com/wiki/{item_name.replace(' ', '_')}"
    
    # Busca os detalhes do item
    item_details = extract_item_details(base_url)
    
    # Busca a imagem do item
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Tenta encontrar a imagem na página
    img_tag = soup.find('img', class_='pi-image-thumbnail')
    img_url = None
    if img_tag and img_tag.get('src'):
        img_url = img_tag.get('src')
        if 'format=original' not in img_url:
            img_url += '&format=original'
    
    # Processar e salvar o item
    result = process_and_save_item(item_name, item_details, None, img_url)
    
    return result


def scrap(category=None):
    """
    Realiza o scraping de itens do Tibia Wiki.
    
    Args:
        category (str, optional): Categoria específica para scraping. 
                                 Se None, faz scraping de todas as categorias.
    """
    # Se uma categoria específica foi fornecida, filtra as URLs
    if category:
        if category in KNOWN_CATEGORIES:
            urls = {category: KNOWN_CATEGORIES[category]}
        else:
            st.error(f"Categoria '{category}' não encontrada.")
            return
    else:
        urls = KNOWN_CATEGORIES

    # Garante que a tabela exista
    create_table()

    # Contador para mostrar progresso
    total_items = 0
    processed_items = 0
    images_skipped = 0

    # Scraping + Inserção no Banco
    for cat, url in urls.items():
        cat_processed_items = 0
        # Pega a página
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find('table', class_='wikitable')
        if not table:
            st.warning(f"Tabela não encontrada em {url}")
            continue

        # Captura cabeçalhos (2º <th> em diante)
        ths = table.find_all('th')
        if len(ths) < 2:
            st.warning(f"Não encontrei cabeçalhos suficientes em {url}")
            continue

        # Por exemplo, headers = ["Image", "Item", "Def", "Arm", etc...]
        headers = ["Image"]
        for header in ths[1:]:
            headers.append(header.text.strip())
        
        # Captura linhas
        rows = table.find_all('tr')[1:]
        total_items += len(rows)
        
        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Log de depuração
        st.write(f"Encontrado {len(rows)} linhas na tabela de {cat}")

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
            # Fallback se não detectar automaticamente
            img_col_index = 1 if cat == 'Quivers' else 0
            st.warning(f"Usando coluna padrão de imagem: {img_col_index+1}")
        
        # Categoria com estrutura diferente?
        special_categories = [
            'Wands', 'Rods', 'Throwing_Weapons', 'Shields'
        ]
        is_special_category = cat in special_categories

        for idx, row in enumerate(rows):
            cols = row.find_all('td')
            if not cols:
                continue

            # Log de depuração
            if idx < 3:  # Mostrar apenas os primeiros 3 itens para debug
                st.write(f"Processando linha {idx+1} com {len(cols)} colunas")

            # Lógica especial para categorias com estrutura diferente
            if is_special_category:
                # Para essas categorias, o nome está na coluna 0 e a imagem na 1
                item_name = cols[0].text.strip()
                
                img_tag = cols[1].find('img')
                if img_tag:
                    img_url = img_tag.get('data-src') or ""
                    if img_url and 'format=original' not in img_url:
                        img_url += '&format=original'
                else:
                    img_url = ""
                    
                # Verificar se há um link para a página do item
                item_link = cols[0].find('a')
                item_url = (
                    f"https://tibia.fandom.com{item_link.get('href')}" 
                    if item_link and item_link.get('href') else None
                )
            else:
                # Para categorias comuns, usar a coluna detectada para a imagem
                img_tag = None
                if img_col_index < len(cols):
                    img_tag = cols[img_col_index].find('img')
                
                # Se não encontrou na coluna detectada, procurar em todas as colunas
                if not img_tag:
                    for i, col in enumerate(cols):
                        if i == img_col_index:
                            continue  # Já verificamos esta coluna
                        img_tag = col.find('img')
                        if img_tag:
                            if idx < 3:
                                st.write(f"Imagem encontrada na coluna {i+1} (alternativa)")
                            break
                
                if img_tag:
                    img_url = img_tag.get('data-src') or img_tag.get('src') or ""
                    if img_url and 'format=original' not in img_url:
                        img_url += '&format=original'
                
                    item_name = extract_item_name(cols, cat)
                    
                    # Log de depuração
                    if idx < 3:
                        st.write(f"Item {idx+1}: Nome extraído: '{item_name}'")
                    
                    # Verificar se há link para a página do item
                    item_link = None
                    for td in cols:
                        link = td.find('a')
                        if link and link.get('href'):
                            item_link = link
                            break
                    
                    item_url = (
                        f"https://tibia.fandom.com{item_link.get('href')}" 
                        if item_link and item_link.get('href') else 
                        f"https://tibia.fandom.com/wiki/{item_name.replace(' ', '_')}"
                    )
                else:
                    if idx < 3:
                        st.write(f"Item {idx+1}: Pulando item sem imagem")
                    continue

            # 2) Exibir status
            status_text.text(
                f"Processando '{item_name}' da categoria '{cat}'...")

            # Log de depuração
            if idx < 3:
                st.write(f"Item {idx+1}: Nome: '{item_name}', URL imagem: {img_url[:30]}... URL item: {item_url}")
            
            # 3) Verificar se o item já existe no banco
            existing_item = read_item(item_name)
            existing_data = {}
            if existing_item and existing_item["data_json"]:
                try:
                    existing_data = json.loads(existing_item["data_json"])
                    if idx < 3:
                        st.write(f"Item {idx+1}: Já existe no banco")
                except Exception as e:
                    st.warning(f"Erro ao interpretar JSON: {str(e)}")
                    existing_data = {}

            # 4) Extrair detalhes da página do item
            item_details = {}
            if item_url:
                if idx < 3:
                    st.write(f"Item {idx+1}: Extraindo detalhes de {item_url}")
                item_details = extract_item_details(item_url)
                # Pausa breve para não sobrecarregar o servidor
                time.sleep(0.5)

            # 5) Juntar os dados existentes com os novos detalhes
            row_dict = {**existing_data, **item_details}

            # 6) Processar e salvar o item
            if item_name:
                process_and_save_item(item_name, row_dict, cat, img_url)
                processed_items += 1
                cat_processed_items += 1
                if idx < 3:
                    st.write(f"Item {idx+1}: Processado e salvo com sucesso!")
                
                # Contar imagens reutilizadas
                if image_exists(item_name):
                    images_skipped += 1
            else:
                if idx < 3:
                    st.write(f"Item {idx+1}: Ignorado - nome inválido ou vazio")
                st.warning("Item ignorado: nome inválido ou vazio")
                
            # Atualizar progresso
            progress_bar.progress(processed_items / total_items)

        # Resumo da categoria
        st.success(f"Categoria {cat} processada: {cat_processed_items} itens")

    # Atualizar status final
    if category:
        msg = (
            f"Scraping detalhado da categoria '{category}' concluído. "
            f"{processed_items} itens processados, "
            f"{images_skipped} imagens reutilizadas."
        )
        st.success(msg)
    else:
        msg = (
            f"Scraping detalhado de todas as categorias concluído. "
            f"{processed_items} itens processados, "
            f"{images_skipped} imagens reutilizadas."
        )
        st.success(msg)


def scrap_missing_items(category=None):
    """
    Realiza o scraping de itens do Tibia Wiki, mas só adiciona os que não existem no banco.
    Args:
        category (str, optional): Categoria específica para scraping. 
                                 Se None, faz scraping de todas as categorias.
    """
    if category:
        if category in KNOWN_CATEGORIES:
            urls = {category: KNOWN_CATEGORIES[category]}
        else:
            st.error(f"Categoria '{category}' não encontrada.")
            return
    else:
        urls = KNOWN_CATEGORIES

    create_table()

    total_items = 0
    processed_items = 0
    skipped_items = 0

    for cat, url in urls.items():
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='wikitable')
        if not table:
            st.warning(f"Tabela não encontrada em {url}")
            continue
        ths = table.find_all('th')
        if len(ths) < 2:
            st.warning(f"Não encontrei cabeçalhos suficientes em {url}")
            continue
        headers = ["Image"]
        for header in ths[1:]:
            headers.append(header.text.strip())
        rows = table.find_all('tr')[1:]
        total_items += len(rows)
        progress_bar = st.progress(0)
        status_text = st.empty()
        for row in rows:
            cols = row.find_all('td')
            if not cols:
                continue
            col_n = 1 if cat == 'Quivers' else 0
            special_categories = [
                'Wands', 'Rods', 'Throwing_Weapons', 'Shields'
            ]
            is_special_category = cat in special_categories
            if is_special_category:
                item_name = cols[0].text.strip()
                item_link = cols[0].find('a')
                item_url = (
                    f"https://tibia.fandom.com{item_link.get('href')}" 
                    if item_link and item_link.get('href') else None
                )
                img_tag = cols[1].find('img')
                if img_tag:
                    img_url = img_tag.get('data-src') or ""
                    if img_url and 'format=original' not in img_url:
                        img_url += '&format=original'
                else:
                    img_url = ""
            else:
                img_tag = cols[col_n].find('img')
                if img_tag:
                    img_url = img_tag.get('data-src') or ""
                    if img_url and 'format=original' not in img_url:
                        img_url += '&format=original'
                    
                    item_name = extract_item_name(cols, cat)
                    item_link = cols[col_n].find('a')
                    item_url = (
                        f"https://tibia.fandom.com{item_link.get('href')}" 
                        if item_link and item_link.get('href') else None
                    )
                else:
                    continue
            status_text.text(
                f"Verificando '{item_name}' da categoria '{cat}'...")
            # Só processa se não existir no banco
            if read_item(item_name):
                skipped_items += 1
                continue
            # 4) Extrair detalhes da página do item
            item_details = {}
            if item_url:
                item_details = extract_item_details(item_url)
                time.sleep(0.5)
            row_dict = item_details
            if item_name:
                process_and_save_item(item_name, row_dict, cat, img_url)
            processed_items += 1
            progress_bar.progress((processed_items + skipped_items) / total_items)
    st.success(f"Processo concluído: {processed_items} novos itens adicionados, {skipped_items} já existiam.")

# Adicionando função auxiliar para extração do nome do item
def extract_item_name(cols, cat):
    """
    Extrai o nome do item de forma robusta, considerando diferentes estruturas de tabela.
    Para categorias problemáticas (Spellbooks, Amulets_and_Necklaces, Rings), tenta extrair o nome do <a> e, se não houver, extrai o texto da <td>.
    Para as demais categorias, mantém o comportamento atual.
    """
    special_categories = ['Wands', 'Rods', 'Throwing_Weapons', 'Shields']
    problematic_categories = ['Spellbooks', 'Amulets_and_Necklaces', 'Rings']
    col_n = 1 if cat == 'Quivers' else 0
    if cat in special_categories:
        item_name = cols[0].text.strip()
    elif cat in problematic_categories:
        item_link = cols[col_n].find('a')
        if item_link:
            item_name = item_link.get('title', '').strip()
            if not item_name:
                item_name = item_link.text.strip()
        else:
            item_name = cols[col_n].text.strip()
    else:
        item_link = cols[col_n].find('a')
        if item_link:
            item_name = item_link.get('title', '').strip()
            if not item_name:
                item_name = item_link.text.strip()
        else:
            item_name = cols[col_n].text.strip()
    return item_name