import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from mydb import upsert_creature, create_table, read_creature, update_creature, download_image_if_needed
import json
import os

def extract_creatures_from_table(table_soup, category, subcategory, section_name):
    """
    Extrai as informações das criaturas de uma tabela específica
    
    Args:
        table_soup: Objeto BeautifulSoup contendo a tabela
        category: Categoria principal (ex: "Humanoids")
        subcategory: Subcategoria (ex: "Elves")
        section_name: Nome da seção/divisão (ex: "Archers", "Scouts", etc.)
        
    Returns:
        Lista de dicionários com as informações das criaturas
    """
    creatures = []
    
    # Verificar se a tabela tem os cabeçalhos esperados
    headers = [th.text.strip() for th in table_soup.find_all('th')]
    required_headers = ["Name", "Exp", "HP"]
    
    # Verificar se todos os cabeçalhos requeridos estão presentes
    if not all(header in headers for header in required_headers):
        return []
    
    # Encontrar o índice da coluna que contém o nome e a imagem
    name_index = next((i for i, header in enumerate(headers) if header == "Name"), None)
    
    if name_index is None:
        return []
    
    # Iterar por todas as linhas da tabela (exceto o cabeçalho)
    for row in table_soup.find_all('tr')[1:]:
        cells = row.find_all(['td', 'th'])
        
        # Verificar se temos células suficientes
        if len(cells) <= name_index:
            continue
        
        # Extrair o nome e a imagem da criatura
        name_cell = cells[name_index]
        
        # Obter o nome da criatura
        name_link = name_cell.find('a')
        if not name_link or not name_link.get('title'):
            continue
        
        creature_name = name_link.get('title')
        
        # Obter a imagem
        img_tag = name_cell.find('img')
        img_url = None
        if img_tag and img_tag.get('src'):
            img_url = img_tag.get('src')
            if not img_url.startswith('http'):
                img_url = 'https:' + img_url
            
            # Extract creature image name from the URL or alt text
            img_name = None
            if img_tag.get('alt'):
                img_name = img_tag.get('alt').strip()
            
            # If we have the image name, use FilePath to get a direct URL
            if img_name:
                # Ensure we only have the filename by removing path elements
                img_name = os.path.basename(img_name)
                # Create a Special:FilePath URL which will directly redirect to the image
                img_url = f"https://tibia.fandom.com/wiki/Special:FilePath/{img_name}"
                print(f"[DEBUG] Created FilePath URL: {img_url}")
        
        # Criar dicionário com os dados da criatura
        creature_data = {
            "Name": creature_name,
            "Section": section_name
        }
        
        # Adicionar outras informações disponíveis na tabela
        for i, header in enumerate(headers):
            if i != name_index and i < len(cells):
                creature_data[header] = cells[i].text.strip()
        
        # Adicionar à lista de criaturas
        creatures.append({
            "name": creature_name,
            "image_url": img_url,
            "category": category,
            "subcategory": subcategory,
            "data": creature_data
        })
    
    return creatures

def process_creature_image(creature_name, img_url):
    """
    Processa a imagem da criatura, baixando-a se necessário.
    
    Args:
        creature_name: Nome da criatura
        img_url: URL da imagem
        
    Returns:
        Caminho para a imagem local ou data URL
    """
    print(f"[DEBUG] Processando imagem para {creature_name}, URL: {img_url}")
    
    if not img_url:
        print(f"[DEBUG] URL vazia para {creature_name}")
        return ""
    
    # Corrigir URLs malformadas
    # 1. Se a URL começa com "https:data:" é uma data URL incorreta
    if img_url.startswith("https:data:") or img_url.startswith("http:data:"):
        # Remover o prefixo incorreto
        img_url = img_url.replace("https:", "", 1).replace("http:", "", 1)
        print(f"[DEBUG] URL corrigida: {img_url}")
    
    # 2. Se já for um data URL válido, retornar como está
    if img_url.startswith("data:"):
        print(f"[DEBUG] Retornando data URL para {creature_name}")
        return img_url
    
    # 3. Certificar que a URL comece com https: se for relativa
    if img_url.startswith("//"):
        img_url = "https:" + img_url
        print(f"[DEBUG] URL ajustada com https: {img_url}")
    elif not img_url.startswith(("http:", "https:")):
        img_url = "https:" + img_url if not img_url.startswith("/") else "https:" + img_url
        print(f"[DEBUG] URL completa: {img_url}")
    
    # Normalizar URL para formato original
    if '&format=original' not in img_url and '?format=original' not in img_url:
        if '?' in img_url:
            img_url += '&format=original'
        else:
            img_url += '?format=original'
        print(f"[DEBUG] URL normalizada: {img_url}")
    
    # Garantir que a pasta de destino existe
    creature_img_folder = "utils/img/creatures"
    if not os.path.exists(creature_img_folder):
        os.makedirs(creature_img_folder, exist_ok=True)
        print(f"[DEBUG] Criada pasta: {creature_img_folder}")
    
    try:
        # Usar a mesma função de download que usamos para itens
        print(f"[DEBUG] Tentando baixar imagem para {creature_name}")
        image_path = download_image_if_needed(creature_name, img_url, folder=creature_img_folder)
        print(f"[DEBUG] Resultado do download: {image_path}")
        
        # Verificar se o download funcionou
        if image_path and os.path.exists(image_path):
            print(f"[DEBUG] Imagem baixada com sucesso: {image_path}")
        else:
            print(f"[DEBUG] Falha no download da imagem. Path: {image_path}")
        
        return image_path
    except Exception as e:
        print(f"ERRO ao processar imagem para {creature_name}: {str(e)}")
        return ""

def extract_section_name(section_soup):
    """
    Extrai o nome da seção/divisão de uma parte da página
    
    Args:
        section_soup: Objeto BeautifulSoup contendo a seção
        
    Returns:
        Nome da seção ou None se não encontrado
    """
    # Procurar o header (h2, h3, etc) mais próximo antes da tabela
    for header_tag in ['h2', 'h3', 'h4']:
        header = section_soup.find_previous(header_tag)
        if header:
            # Limpar qualquer ID de seção ou link de edição
            header_text = header.text.strip()
            # Remover [edit] e outros textos auxiliares
            header_text = re.sub(r'\[.*?\]', '', header_text).strip()
            return header_text
    
    return None

def scrap_creatures_from_subcategory(category, subcategory, url):
    """
    Realiza o scraping de todas as criaturas de uma subcategoria
    
    Args:
        category: Categoria principal (ex: "Humanoids")
        subcategory: Subcategoria (ex: "Elves")
        url: URL da página da subcategoria
        
    Returns:
        Lista de criaturas extraídas
    """
    try:
        # Fazer requisição HTTP
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            st.error(f"Erro ao acessar a página {url}: HTTP {response.status_code}")
            return []
        
        # Parsear o HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encontrar todas as tabelas que podem conter criaturas
        tables = soup.find_all('table', class_='wikitable')
        
        all_creatures = []
        
        # Para cada tabela, verificar se é uma tabela de criaturas
        for table in tables:
            # Verificar headers para confirmar que é uma tabela de criaturas
            headers = [th.text.strip() for th in table.find_all('th')]
            
            # Verificar se a tabela tem pelo menos os cabeçalhos Nome, Exp e HP
            required_headers = ["Name", "Exp", "HP"]
            if all(header in headers for header in required_headers):
                # Extrair o nome da seção desta tabela
                section_name = extract_section_name(table)
                
                # Extrair as criaturas desta tabela
                creatures = extract_creatures_from_table(table, category, subcategory, section_name)
                all_creatures.extend(creatures)
        
        return all_creatures
    
    except Exception as e:
        st.error(f"Erro ao processar a subcategoria {subcategory}: {str(e)}")
        return []

def save_creatures_to_db(creatures):
    """
    Salva as criaturas no banco de dados
    
    Args:
        creatures: Lista de dicionários com as informações das criaturas
        
    Returns:
        Número de criaturas salvas
    """
    create_table()  # Garantir que a tabela existe
    
    saved_count = 0
    for creature in creatures:
        try:
            # Processar a imagem
            image_path = process_creature_image(creature["name"], creature["image_url"])
            
            # Salvar no banco de dados
            upsert_creature(
                creature["name"],
                creature["category"],
                creature["subcategory"],
                image_path,
                creature["data"]
            )
            saved_count += 1
        except Exception as e:
            print(f"Erro ao salvar criatura {creature['name']}: {str(e)}")
    
    return saved_count

def scrap_all_creatures_from_subcategory(category, subcategory, url, progress_callback=None):
    """
    Realiza o scraping de todas as criaturas de uma subcategoria e salva no banco
    
    Args:
        category: Categoria principal (ex: "Humanoids")
        subcategory: Subcategoria (ex: "Elves")
        url: URL da página da subcategoria
        progress_callback: Função de callback para atualizar o progresso
        
    Returns:
        Número de criaturas salvas
    """
    # Garantir que a tabela existe
    create_table()
    
    if progress_callback:
        progress_callback(f"Iniciando scraping de {subcategory}...")
    
    # Extrair criaturas da subcategoria
    creatures = scrap_creatures_from_subcategory(category, subcategory, url)
    
    if progress_callback:
        progress_callback(f"Encontradas {len(creatures)} criaturas em {subcategory}.")
    
    # Salvar no banco de dados
    saved_count = save_creatures_to_db(creatures)
    
    if progress_callback:
        progress_callback(f"Salvas {saved_count} criaturas de {subcategory}.")
    
    return saved_count

def extract_creature_details(creature_name):
    """
    Extrai detalhes completos de uma criatura específica a partir de sua página individual
    
    Args:
        creature_name: Nome da criatura
        
    Returns:
        Dicionário com os detalhes da criatura
    """
    # Formatar URL para a página da criatura
    url = f"https://tibia.fandom.com/wiki/{creature_name.replace(' ', '_')}"
    
    try:
        # Fazer requisição HTTP
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {"error": f"Erro ao acessar a página {url}: HTTP {response.status_code}"}
        
        # Parsear o HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extrair informações da infobox (tabela lateral)
        creature_data = {}
        
        # Buscar a infobox
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            # Extrair nome da criatura (mesmo que já tenhamos)
            name_tag = infobox.find(['h2', 'div'], class_='pi-item pi-item-spacing pi-title')
            if name_tag:
                creature_data["Name"] = name_tag.text.strip()
            
            # Extrair outros dados da infobox
            info_items = infobox.find_all('div', class_='pi-item')
            for item in info_items:
                # Extrair o rótulo/chave
                label_tag = item.find('h3', class_='pi-data-label')
                if not label_tag:
                    continue
                
                label = label_tag.text.strip()
                
                # Extrair o valor
                value_tag = item.find(['div', 'span'], class_='pi-data-value')
                if not value_tag:
                    continue
                
                value = value_tag.text.strip()
                
                # Adicionar ao dicionário de dados
                creature_data[label] = value
        
        # Extrair informações de resistências/imunidades
        resistances_section = soup.find(id='Damage_Taken_During_Combat')
        if not resistances_section:
            # Tentar outras variações
            resistances_section = soup.find(id='Susceptibility')
        
        if resistances_section:
            # Encontrar a tabela de resistências
            resistances_table = resistances_section.find_next('table', class_='wikitable')
            if resistances_table:
                resistances = {}
                
                # Extrair linhas da tabela
                rows = resistances_table.find_all('tr')
                for row in rows[1:]:  # Pular cabeçalho
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        element = cells[0].text.strip()
                        value = cells[1].text.strip()
                        # Remover símbolos de percentagem e converter para número
                        value = value.replace('%', '').strip()
                        try:
                            value = int(value)
                        except ValueError:
                            pass
                        resistances[element] = value
                
                if resistances:
                    creature_data["Resistances"] = resistances
        
        # Extrair informações de loot
        loot_section = soup.find(id='Loot')
        if loot_section:
            # Encontrar a tabela de loot
            loot_table = loot_section.find_next('table', class_='wikitable')
            if loot_table:
                loot_items = []
                
                # Extrair linhas da tabela
                rows = loot_table.find_all('tr')
                for row in rows[1:]:  # Pular cabeçalho
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        item_name = cells[0].text.strip()
                        drop_rate = cells[1].text.strip()
                        
                        loot_items.append({
                            "item": item_name,
                            "rate": drop_rate
                        })
                
                if loot_items:
                    creature_data["Loot"] = loot_items
        
        # Extrair informações de comportamento
        behavior_section = soup.find(id='Behaviour')
        if behavior_section:
            # Pegar o próximo parágrafo após o cabeçalho de comportamento
            behavior_text = []
            current = behavior_section.find_next()
            
            # Continuar até encontrar outro cabeçalho ou final da seção
            while current and current.name not in ['h1', 'h2', 'h3']:
                if current.name == 'p':
                    behavior_text.append(current.text.strip())
                current = current.find_next()
            
            if behavior_text:
                creature_data["Behaviour"] = " ".join(behavior_text)
        
        # Extrair a imagem da criatura
        img_url = None
        img_tag = soup.find('img', class_='pi-image-thumbnail')
        if img_tag and img_tag.get('src'):
            img_url = img_tag.get('src')
            
            # Extract image name from alt attribute or src
            img_name = None
            if img_tag.get('alt'):
                img_name = img_tag.get('alt').strip()
            else:
                # Try to extract from the src URL
                src = img_tag.get('src')
                parts = src.split('/')
                for part in reversed(parts):
                    if part.lower().endswith(('.gif', '.png', '.jpg', '.jpeg')):
                        img_name = part
                        break
            
            # Try using direct static URL for tibia images which are more reliable
            if creature_name:
                # Format creature name and try different image URLs
                clean_name = creature_name.replace(' ', '_')
                # Try direct URL to static Tibia library images
                img_url = f"https://static.tibia.com/images/library/{clean_name.lower()}.gif"
                print(f"[DEBUG] Created direct static URL: {img_url}")
            
            # If we have an image name, also try the FilePath option
            if img_name:
                # Add it as a backup option
                backup_url = f"https://tibia.fandom.com/wiki/Special:FilePath/{img_name}"
                print(f"[DEBUG] Created FilePath URL from details page: {backup_url}")
            
            # If direct URL doesn't work, we'll try the original URL with format
            if 'format=original' not in img_url:
                # Original URL formatting 
                original_url = img_tag.get('src')
                if '?' in original_url:
                    original_url += '&format=original'
                else:
                    original_url += '?format=original'
                print(f"[DEBUG] Created original URL with format: {original_url}")
        else:
            # If we couldn't find an image, try using the creature name directly
            clean_name = creature_name.replace(' ', '_')
            # Try direct URL to static Tibia library images
            img_url = f"https://static.tibia.com/images/library/{clean_name.lower()}.gif"
            print(f"[DEBUG] Created direct static URL from creature name: {img_url}")
        
        if img_url:
            creature_data["image_url"] = img_url
        
        return creature_data
    
    except Exception as e:
        return {"error": f"Erro ao processar detalhes da criatura: {str(e)}"}

def update_creature_details(creature_name):
    """
    Atualiza os detalhes de uma criatura no banco de dados
    
    Args:
        creature_name: Nome da criatura
        
    Returns:
        Dicionário com os detalhes atualizados da criatura ou mensagem de erro
    """
    # Garantir que a tabela existe
    create_table()
    
    # Verificar se a criatura existe no banco
    creature = read_creature(creature_name)
    if not creature:
        return {"error": f"Criatura '{creature_name}' não encontrada no banco de dados"}
    
    # Extrair detalhes atuais
    try:
        current_data = json.loads(creature.get('data_json', '{}')) if isinstance(creature.get('data_json'), str) else creature.get('data_json', {})
    except json.JSONDecodeError:
        current_data = {}
    
    # Extrair novos detalhes
    new_details = extract_creature_details(creature_name)
    
    # Se ocorreu erro, retornar
    if "error" in new_details:
        return new_details
    
    # Processar a imagem se existir
    image_path = creature.get('image_path', '')
    if "image_url" in new_details:
        img_url = new_details.pop("image_url")  # Remover do dicionário para não duplicar
        image_path = download_image_if_needed(creature_name, img_url, folder="utils/img/creatures")
    
    # Mesclar dados atuais com novos detalhes (novos detalhes têm prioridade)
    updated_data = {**current_data, **new_details}
    
    # Atualizar no banco de dados
    update_creature(
        creature_name,
        category=creature.get('category'),
        subcategory=creature.get('subcategory'),
        image_path=image_path,
        data_dict=updated_data
    )
    
    return updated_data 