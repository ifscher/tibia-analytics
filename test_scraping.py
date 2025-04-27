import requests
from bs4 import BeautifulSoup
import time
import json
import os

# Lista de categorias para testar
TEST_CATEGORIES = [
    "Spellbooks",
    "Amulets_and_Necklaces",
    "Rings"
]

# URLs das categorias
CATEGORY_URLS = {
    "Spellbooks": "https://tibia.fandom.com/wiki/Spellbooks",
    "Amulets_and_Necklaces": "https://tibia.fandom.com/wiki/Amulets_and_Necklaces",
    "Rings": "https://tibia.fandom.com/wiki/Rings"
}

# Função auxiliar para extrair nome do item, copiada de scraping.py
def extract_item_name(cols, cat):
    """
    Extrai o nome do item de forma robusta, considerando diferentes estruturas de tabela.
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

def test_extract_items():
    """
    Testa a extração de nomes de itens das categorias problemáticas.
    """
    results = {}
    
    for category in TEST_CATEGORIES:
        print(f"\nTESTANDO CATEGORIA: {category}")
        print("-" * 50)
        url = CATEGORY_URLS[category]
        
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            table = soup.find('table', class_='wikitable')
            if not table:
                print(f"[ERRO] Tabela não encontrada em {url}")
                continue
                
            rows = table.find_all('tr')[1:]  # Pula a linha de cabeçalho
            item_names = []
            
            for row in rows:
                cols = row.find_all('td')
                if not cols:
                    continue
                    
                # Extrair nome usando nossa função
                item_name = extract_item_name(cols, category)
                if item_name:
                    print(f"Item encontrado: {item_name}")
                    item_names.append(item_name)
                else:
                    print(f"[ALERTA] Item sem nome encontrado na linha: {row}")
            
            results[category] = {
                "total_rows": len(rows),
                "items_found": len(item_names),
                "items": item_names
            }
            
            print(f"\nResultado da categoria {category}:")
            print(f"Total de linhas: {len(rows)}")
            print(f"Total de itens encontrados: {len(item_names)}")
            
        except Exception as e:
            print(f"[ERRO] Erro ao processar categoria {category}: {str(e)}")
    
    print("\nRESUMO DOS RESULTADOS:")
    print("=" * 50)
    for category, data in results.items():
        print(f"{category}: {data['items_found']}/{data['total_rows']} itens encontrados")

# Executar teste
if __name__ == "__main__":
    test_extract_items() 