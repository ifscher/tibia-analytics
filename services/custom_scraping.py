from services.scraping import extract_item_details, process_item_image
from mydb import read_item, update_item
import requests
from bs4 import BeautifulSoup


def process_trade_values(item_details):
    """
    Processa campos de valor no dicionário de dados do item,
    convertendo strings como "2,300 gp" para inteiros como 2300.
    
    Args:
        item_details (dict): Dicionário com dados do item
        
    Returns:
        dict: Dicionário com valores de comércio processados
    """
    # Verificar se existem Trade Properties
    if ("Trade Properties" in item_details and 
            isinstance(item_details["Trade Properties"], dict)):
        trade_props = item_details["Trade Properties"]
        
        # Processar campo Value
        if "Value" in trade_props:
            value = trade_props["Value"]
            if isinstance(value, str):
                # Verificar se contém dígitos antes de tentar converter
                if any(char.isdigit() for char in value):
                    # Remover "gp" e vírgulas, depois converter para inteiro
                    value = value.replace("gp", "").replace(",", "").strip()
                    try:
                        trade_props["Value"] = int(value)
                    except ValueError:
                        # Se não for possível converter, manter o valor original
                        pass
        
        # Lista de possíveis variantes do campo "Sold For"/"Bought For"
        price_variants = [
            "Sold For", "Sold for", "sold for", "SoldFor", "SOLD FOR",
            "Sell Value", "Sell value",
            "Bought For", "Bought for", "bought for", "BoughtFor",
            "Buy Value", "Buy value"
        ]
        
        # Processar campos de preço (verificando todas as variantes)
        for variant in price_variants:
            if variant in trade_props:
                price_value = trade_props[variant]
                if isinstance(price_value, str):
                    # Verificar se há dígitos no texto antes de processar
                    if any(char.isdigit() for char in price_value):
                        # Remover "gp" e vírgulas, depois converter para inteiro
                        clean_value = price_value.replace("gp", "")
                        clean_value = clean_value.replace(",", "").strip()
                        try:
                            trade_props[variant] = int(clean_value)
                        except ValueError:
                            # Se não for possível converter, manter o valor original
                            pass
    
    return item_details


def force_update_single_item(item_name, update_category=False):
    """
    Realiza o scraping de um único item do Tibia Wiki e força uma atualização
    deletando o conteúdo da coluna data (exceto para atualizações de categoria
    quando update_category=False).
    
    Args:
        item_name (str): Nome do item para scraping.
        update_category (bool): Se True, permite atualizar a categoria 
                               normalmente. Se False, preserva a categoria
                               existente.
        
    Returns:
        dict: Dados extraídos do item.
    """
    # Prepara a URL para a página do item
    base_url = f"https://tibia.fandom.com/wiki/{item_name.replace(' ', '_')}"
    
    # Busca os detalhes do item
    item_details = extract_item_details(base_url)
    
    # Processar os valores de comércio (Value e Sold For)
    item_details = process_trade_values(item_details)
    
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
    
    # Processar a imagem
    if img_url:
        image_data_url = process_item_image(item_name, img_url)
    else:
        image_data_url = ""
    
    # Ler item existente para manter a categoria se necessário
    existing_item = read_item(item_name)
    
    if existing_item:
        # Se update_category é False e existe uma categoria,
        # usamos a categoria existente em vez da nova
        category = None
        if not update_category and existing_item["category"]:
            category = existing_item["category"]
        else:
            # Inferir categoria do novo item
            from services.scraping import infer_category
            category = infer_category(item_details, item_name)
            
        # Atualizar o banco de dados com os novos dados
        update_item(item_name, category, image_data_url, item_details)
        return item_details
    else:
        # Se o item não existe, criar normalmente usando a função padrão
        from services.scraping import process_and_save_item
        return process_and_save_item(item_name, item_details, None, img_url) 