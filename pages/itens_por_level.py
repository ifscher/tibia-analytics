import streamlit as st
import pandas as pd
import json
import requests
from bs4 import BeautifulSoup
import re
from mydb import read_all_items
from utils.menu import menu_with_redirect
from utils.favicon import set_config
from utils.vocation import standardize_vocation, VOCATION_MAPPING
from utils.config import extract_level
import base64
import time

# Função que usa serviço proxy para acessar o site do Tibia
def get_character_info_via_proxy(character_name):
    """Usa um serviço proxy para buscar informações do personagem do Tibia."""
    # Usando o serviço API pública gratuita Allorigins como proxy
    encoded_url = base64.b64encode(f"https://www.tibia.com/community/?subtopic=characters&name={character_name}".encode()).decode()
    proxy_url = f"https://api.allorigins.win/raw?url=https://www.tibia.com/community/?subtopic=characters%26name={character_name}"
    
    try:
        st.info(f"Buscando personagem {character_name} via proxy...")
        
        # Headers para simular um navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # Fazer a requisição com timeout
        response = requests.get(proxy_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            st.error(f"Erro ao acessar o proxy. Status code: {response.status_code}")
            return None
            
        # Processar o HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Verificar se o personagem existe
        if "Could not find character" in soup.get_text():
            st.error(f"O site do Tibia informou que não encontrou o personagem '{character_name}'.")
            return None
            
        st.info("Personagem encontrado via proxy, extraindo informações...")
        
        # Procurar pela tabela de informações do personagem
        info_table = soup.find('table', {'class': 'Table3'})
        if info_table:
            # Extrair level usando uma expressão regular mais específica
            level_match = re.search(r'Level:(\d+)', info_table.get_text())
            if level_match:
                level = int(level_match.group(1))
            else:
                level = 0
            
            # Extrair vocação usando uma expressão regular mais específica
            vocation_match = re.search(
                r'Vocation:(Master Sorcerer|Elder Druid|Elite Knight|Royal Paladin|Exalted Monk|Sorcerer|Druid|Knight|Paladin|Monk)', 
                info_table.get_text()
            )
            if vocation_match:
                vocation = vocation_match.group(1).strip()
            else:
                vocation = None
            
            # Verificar se encontrou as informações
            if level == 0 or vocation is None:
                st.error("Não foi possível encontrar o level ou a vocação do personagem via proxy.")
                return None
            
            return {
                'level': level,
                'vocation': vocation
            }
        else:
            st.error("Não foi possível encontrar as informações do personagem via proxy.")
            return None
    except Exception as e:
        st.error(f"Erro ao buscar informações via proxy: {str(e)}")
        return None

def get_character_info(character_name):
    """Obtém informações do personagem do site GuildStats.eu com fallback para o site do Tibia."""
    # Mostrar mensagem de diagnóstico
    st.info(f"Buscando personagem {character_name}...")
    
    # Headers para simular um navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    # Primeiro tentamos com o GuildStats
    try:
        # URL do GuildStats
        url = f"https://guildstats.eu/character?nick={character_name}"
        
        # Fazer a requisição com timeout aumentado
        response = requests.get(url, headers=headers, timeout=30)
        
        # Verificar o status da resposta
        if response.status_code == 200:
            # Processar o HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Verificar se o personagem existe
            if "Guild or character does not exsists" in soup.get_text():
                st.warning(f"O personagem '{character_name}' não foi encontrado no GuildStats.")
            else:
                # Verificar se estamos na página correta
                if "Players online" in soup.get_text():
                    # Extrair informações do personagem
                    
                    # Buscar o nível do personagem
                    level_info = soup.find(text=re.compile("Level:"))
                    if level_info:
                        level_match = re.search(r'Level: *(\d+)', level_info.parent.get_text())
                        if level_match:
                            level = int(level_match.group(1))
                            
                            # Buscar a vocação do personagem
                            vocation_info = soup.find(text=re.compile("Vocation:"))
                            if vocation_info:
                                vocation_match = re.search(r'Vocation: *(Master Sorcerer|Elder Druid|Elite Knight|Royal Paladin|Exalted Monk|Sorcerer|Druid|Knight|Paladin|Monk)', vocation_info.parent.get_text())
                                if vocation_match:
                                    vocation = vocation_match.group(1).strip()
                                    
                                    st.success(f"Personagem {character_name} encontrado no GuildStats! Level: {level}, Vocação: {vocation}")
                                    
                                    return {
                                        'level': level,
                                        'vocation': vocation
                                    }
        
        st.warning("Não foi possível obter informações do GuildStats. Tentando pelo site oficial do Tibia...")
    except requests.exceptions.Timeout:
        st.warning(f"Timeout ao conectar ao GuildStats.eu. Tentando pelo site oficial do Tibia...")
    except requests.exceptions.ConnectionError:
        st.warning(f"Erro de conexão com GuildStats.eu. Tentando pelo site oficial do Tibia...")
    except Exception as e:
        st.warning(f"Erro ao acessar GuildStats.eu: {str(e)}. Tentando pelo site oficial do Tibia...")
    
    # Fallback para o site oficial do Tibia
    try:
        # URL do site oficial do Tibia
        url = f"https://www.tibia.com/community/?subtopic=characters&name={character_name}"
        
        # Fazer a requisição com timeout aumentado
        response = requests.get(url, headers=headers, timeout=30)
        
        # Verificar o status da resposta
        if response.status_code == 200:
            # Processar o HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Verificar se o personagem existe
            if "Character not found" in soup.get_text() or "Could not find character" in soup.get_text():
                st.error(f"O personagem '{character_name}' não foi encontrado.")
                return None
            
            # Procurar pela tabela de informações do personagem
            info_table = soup.find('table', {'class': 'TableContent'})
            if info_table:
                info_text = info_table.get_text()
                
                # Extrair level usando uma expressão regular mais específica
                level_match = re.search(r'Level:?\s*(\d+)', info_text)
                if level_match:
                    level = int(level_match.group(1))
                else:
                    st.error("Não foi possível encontrar o level do personagem.")
                    return None
                
                # Extrair vocação usando uma expressão regular mais específica
                vocation_match = re.search(
                    r'Vocation:?\s*(Master Sorcerer|Elder Druid|Elite Knight|Royal Paladin|Exalted Monk|Sorcerer|Druid|Knight|Paladin|Monk)',
                    info_text
                )
                if vocation_match:
                    vocation = vocation_match.group(1).strip()
                else:
                    st.error("Não foi possível encontrar a vocação do personagem.")
                    return None
                
                st.success(f"Personagem {character_name} encontrado no site oficial do Tibia! Level: {level}, Vocação: {vocation}")
                
                return {
                    'level': level,
                    'vocation': vocation
                }
            else:
                st.error("Não foi possível encontrar as informações do personagem.")
        elif response.status_code == 403:
            st.error("Acesso ao site do Tibia foi bloqueado (Erro 403). Tente novamente mais tarde.")
        else:
            st.error(f"Erro ao acessar o site do Tibia. Status code: {response.status_code}")
    except requests.exceptions.Timeout:
        st.error("Timeout ao conectar ao site do Tibia. Verifique sua conexão e tente novamente.")
    except requests.exceptions.ConnectionError:
        st.error("Erro de conexão com o site do Tibia. Verifique sua conexão e tente novamente.")
    except Exception as e:
        st.error(f"Erro ao buscar informações do personagem: {str(e)}")
    
    return None


# Lista de todas as vocações possíveis
ALL_VOCATIONS = ['sorcerers', 'druids', 'knights', 'paladins', 'monks']


def extract_vocations_from_data(data):
    """
    Extrai vocações de um dicionário de dados.
    Retorna uma lista de vocações padronizadas ou lista vazia se não houver restrição.
    """
    vocations = []
    
    if not isinstance(data, dict):
        return []
        
    # Verificar no caminho Requirements > Vocation
    if "Requirements" in data and isinstance(data["Requirements"], dict) and "Vocation" in data["Requirements"]:
        vocation_data = data["Requirements"]["Vocation"]
        
        # Pode ser uma string ou lista
        if isinstance(vocation_data, str):
            # Separar vocações por vírgula ou "and"
            vocation_str = vocation_data.lower().replace(" and ", ", ")
            # Separar por vírgula
            vocation_list = [v.strip() for v in vocation_str.split(",") if v.strip()]
            # Padronizar cada vocação
            for voc in vocation_list:
                # Normalizar vocações para formato plural
                normalized_voc = normalize_vocation_to_plural(voc)
                if normalized_voc:
                    vocations.append(normalized_voc)
        elif isinstance(vocation_data, list):
            # Se for lista, processar cada item
            for voc in vocation_data:
                if isinstance(voc, str):
                    normalized_voc = normalize_vocation_to_plural(voc.lower())
                    if normalized_voc:
                        vocations.append(normalized_voc)
    
    # Verificar também no campo Vocations (retrocompatibilidade)
    if not vocations and "Vocations" in data:
        vocations_data = data["Vocations"]
        
        if isinstance(vocations_data, str):
            # Separar vocações por vírgula ou "and"
            vocations_str = vocations_data.lower().replace(" and ", ", ")
            # Separar por vírgula
            vocations_list = [v.strip() for v in vocations_str.split(",") if v.strip()]
            # Padronizar cada vocação
            for voc in vocations_list:
                normalized_voc = normalize_vocation_to_plural(voc)
                if normalized_voc:
                    vocations.append(normalized_voc)
        elif isinstance(vocations_data, list):
            # Se for lista, processar cada item
            for voc in vocations_data:
                if isinstance(voc, str):
                    normalized_voc = normalize_vocation_to_plural(voc.lower())
                    if normalized_voc:
                        vocations.append(normalized_voc)
    
    # Verificar também no campo Vocation (retrocompatibilidade)
    if not vocations and "Vocation" in data:
        vocation_data = data["Vocation"]
        
        if isinstance(vocation_data, str):
            # Separar vocações por vírgula ou "and"
            vocation_str = vocation_data.lower().replace(" and ", ", ")
            # Separar por vírgula
            vocation_list = [v.strip() for v in vocation_str.split(",") if v.strip()]
            # Padronizar cada vocação
            for voc in vocation_list:
                normalized_voc = normalize_vocation_to_plural(voc)
                if normalized_voc:
                    vocations.append(normalized_voc)
        elif isinstance(vocation_data, list):
            # Se for lista, processar cada item
            for voc in vocation_data:
                if isinstance(voc, str):
                    normalized_voc = normalize_vocation_to_plural(voc.lower())
                    if normalized_voc:
                        vocations.append(normalized_voc)
    
    # Garantir que as vocações estão no formato esperado (lista de strings)
    if not isinstance(vocations, list):
        vocations = []
    
    # Filtrar vocações inválidas ou None
    vocations = [voc for voc in vocations if isinstance(voc, str) and voc in ALL_VOCATIONS]
    
    # Retorna a lista de vocações (pode ser vazia se não houver restrições)
    return sorted(list(set(vocations)))


def normalize_vocation_to_plural(voc):
    """Normaliza vocação para formato plural padrão."""
    voc = voc.lower().strip()
    
    # Se já estiver no VOCATION_MAPPING, usamos diretamente
    if voc in VOCATION_MAPPING:
        return VOCATION_MAPPING[voc]
    
    # Verificações adicionais para casos específicos
    if voc == "sorcerer":
        return "sorcerers"
    elif voc == "druid":
        return "druids"
    elif voc == "knight":
        return "knights"
    elif voc == "paladin":
        return "paladins"
    elif voc == "monk":
        return "monks"
    
    # Se já for plural, retornar como está
    if voc.endswith("s") and voc in ALL_VOCATIONS:
        return voc
    
    # Se for singular mas não estiver nos casos acima, tentar adicionar 's'
    voc_plural = voc + "s"
    if voc_plural in ALL_VOCATIONS:
        return voc_plural
    
    # Se chegou aqui, não conseguimos normalizar
    return None


def get_vocations_display(vocations_list):
    """Formata a lista de vocações para exibição na tabela."""
    if not vocations_list or len(vocations_list) == 0:
        return ""
    
    # Mapeamento para nomes mais amigáveis
    friendly_names = {
        'sorcerers': 'Sorcerers',
        'druids': 'Druids',
        'knights': 'Knights',
        'paladins': 'Paladins',
        'monks': 'Monks'
    }
    
    # Formatar cada vocação
    formatted = []
    for voc in vocations_list:
        if voc in friendly_names:
            formatted.append(friendly_names[voc])
        else:
            formatted.append(voc.capitalize())
    
    return ", ".join(formatted)


def get_category_config(category):
    """
    Obtém a configuração de colunas para uma categoria específica.
    
    Args:
        category (str): Nome da categoria do item.
        
    Returns:
        dict: Configuração com colunas a exibir e funções extratoras.
    """
    # CONFIGURAÇÃO DE PROPRIEDADES DE COMBATE POR TIPO DE ITEM
    # Para adicionar ou remover colunas, basta editar estas listas
    
    # Propriedades para armaduras (peças de torso)
    combat_properties_armors = [
        "Armor",              # Valor de armadura
        "Attributes",         # Atributos mágicos
        "Resistances",        # Proteções elementais
        "Imbuing Slots",      # Slots de imbuement
        "Augments",           # Augmentos
        "Hands",              # Mãos
        "Mantra",             # Mantra
        "Resists",            # Proteções elementais
        "Upgrade Classification"  # Classificação de upgrade
    ]
    
    # Propriedades para capacetes
    combat_properties_helmets = [
        "Armor",              # Valor de armadura
        "Attributes",         # Atributos mágicos
        "Augments",           # Augmentos
        "Hands",              # Mãos
        "Imbuing Slots",      # Slots de imbuement
        "Mantra",             # Mantra
        "Resists",            # Proteções elementais
        "Upgrade Classification"  # Classificação de upgrade
    ]
    
    # Propriedades para perneiras
    combat_properties_legs = [
        "Armor",              # Valor de armadura
        "Attributes",         # Atributos mágicos
        "Augments",           # Augmentos
        "Imbuing Slots",      # Slots de imbuement
        "Mantra",             # Mantra
        "Resists",            # Proteções elementais
        "Upgrade Classification"  # Classificação de upgrade
    ]
    
    # Propriedades para botas
    combat_properties_boots = [
        "Armor",              # Valor de armadura
        "Attributes",         # Atributos mágicos
        "Augments",           # Augmentos
        "Hands",              # Mãos
        "Imbuing Slots",      # Slots de imbuement
        "Mantra",             # Mantra
        "Resists",            # Proteções elementais
        "Upgrade Classification"  # Classificação de upgrade
    ]
    
    # Propriedades para amuletos e colares
    combat_properties_amulets = [
        "Resists",            # Proteções elementais
        "Charges",            # Cargas
        "Armor",              # Valor de armadura
        "Attributes",         # Atributos mágicos
        "Mantra",             # Mantra
    ]
    
    # Propriedades para escudos
    combat_properties_shields = [
        "Attributes",         # Atributos mágicos
        "Augments",           # Augmentos
        "Defense",            # Valor de defesa
        "Imbuing Slots",      # Slots de imbuement
        "Resists",            # Proteções elementais
    ]
    
    # Propriedades para armas físicas
    combat_properties_weapons = [
        "Hands",              # Mãos
        "Defense",            # Valor de defesa
        "Upgrade Classification",  # Classificação de upgrade
        "Attack",             # Valor de ataque
        "Imbuing Slots",      # Slots de imbuement
        "Defense Modifier",   # Modificador de defesa
        "Attributes",         # Atributos mágicos
        "Fire Attack",        # Ataque de fogo
        "Augments",           # Augmentos
        "Life Leech",         # Life Leech
        "Critical Hit",       # Critical Hit
        "Mana Leech",         # Mana Leech
        "Ice Attack",         # Ataque de gelo
        "Earth Attack",       # Ataque de terra
        "Death Attack",       # Ataque de morte
        "Energy Attack",      # Ataque de energia
        "Resists",            # Proteções elementais
    ]
    
    # Propriedades para armas mágicas (Wands, Rods)
    combat_properties_magic_weapons = [
        "Attributes",         # Atributos mágicos
        "Augments",           # Augmentos
        "Charges",            # Cargas
        "Critical Hit",       # Critical Hit
        "Damage",             # Dano
        "Element",            # Elemento
        "Imbuing Slots",      # Slots de imbuement
        "Life Leech",         # Life Leech
        "Mana",              # Mana
        "Mana Leech",         # Mana Leech
        "Range",             # Alcance
        "Resists",            # Proteções elementais
        "Upgrade Classification"  # Classificação de upgrade
    ]
    
    # Propriedades para anéis
    combat_properties_rings = [
        "Attributes",         # Atributos mágicos
        "Resists",            # Proteções elementais
        "Armor",              # Valor de armadura
        "Mana Leech",         # Mana Leech
        "Charges",            # Cargas
        "Mantra",             # Mantra
    ]

    # Propriedades para Quivers
    combat_properties_quivers = [
        "Attributes",         # Atributos mágicos
        "Resistances"         # Proteções elementais
    ]

    # Propriedades para Throwing Weapons
    combat_properties_throwing_weapons = [
        "Hands",
        "Attack",             # Valor de ataque
        "Defense",            # Valor de defesa
        "Range",              # Alcance
        "Earth Attack",       # Ataque de terra
        "Fire Attack",        # Ataque de fogo
    ]
        
    # Propriedades para Spellbooks
    combat_properties_spellbooks = [
        "Defense",            # Valor de defesa
        "Attributes",         # Atributos mágicos
        "Imbuing Slots",      # Slots de imbuement
        "Resists",            # Proteções elementais
        "Augments",           # Augmentos
    ]



    # FUNÇÕES EXTRATORAS - Não é necessário editar essa parte
    
    # Dicionário de funções extratoras para cada propriedade de combate
    property_extractors = {
        "Armor": lambda data: _extract_simple_property(data, "Armor"),
        "Defense": lambda data: _extract_simple_property(data, "Defense"),
        "Attack": lambda data: _extract_simple_property(data, "Attack"),
        "Defense Modifier": lambda data: _extract_defense_modifier(data),
        "Attributes": lambda data: _extract_attributes(data),
        "Imbuing Slots": lambda data: _extract_imbuing_slots(data),
        "Range": lambda data: _extract_simple_property(data, "Range"),
        "Element": lambda data: _extract_element(data),
        "Damage": lambda data: _extract_damage(data),
        "Life Leech": lambda data: _extract_leech(data, "Life Leech", "life leech"),
        "Mana Leech": lambda data: _extract_leech(data, "Mana Leech", "mana leech"),
        "Mana": lambda data: _extract_mana(data),
        "Resistances": lambda data: _extract_resistances(data),
        "Charges": lambda data: _extract_charges(data),
        "Resists": lambda data: _extract_resists(data),
        "Hands": lambda data: _extract_simple_property(data, "Hands"),
        "Augments": lambda data: _extract_simple_property(data, "Augments"),
        "Critical Hit": lambda data: _extract_critical_hit(data),
        "Mantra": lambda data: _extract_simple_property(data, "Mantra"),
        "Upgrade Classification": lambda data: _extract_simple_property(data, "Upgrade Classification"),
        "Fire Attack": lambda data: _extract_simple_property(data, "Fire Attack"),
        "Ice Attack": lambda data: _extract_simple_property(data, "Ice Attack"),
        "Energy Attack": lambda data: _extract_simple_property(data, "Energy Attack"),
        "Earth Attack": lambda data: _extract_simple_property(data, "Earth Attack"),
        "Death Attack": lambda data: _extract_simple_property(data, "Death Attack")
    }
    
    # Dicionário de nomes de exibição para cada propriedade
    property_display_names = {
        "Armor": "Armadura",
        "Defense": "Defesa",
        "Attack": "Ataque",
        "Defense Modifier": "Mod. Defesa",
        "Attributes": "Atributos",
        "Imbuing Slots": "Slots de Imbuement",
        "Range": "Alcance",
        "Element": "Elemento",
        "Damage": "Dano",
        "Life Leech": "Life Leech",
        "Mana Leech": "Mana Leech",
        "Mana": "Mana",
        "Resistances": "Proteções Elementais",
        "Charges": "Cargas",
        "Resists": "Proteções",
        "Hands": "Mãos",
        "Augments": "Augmentos",
        "Critical Hit": "Crítico",
        "Mantra": "Mantra",
        "Upgrade Classification": "Classificação de Upgrade",
        "Fire Attack": "Ataque de Fogo",
        "Ice Attack": "Ataque de Gelo",
        "Energy Attack": "Ataque de Energia",
        "Earth Attack": "Ataque de Terra",
        "Death Attack": "Ataque de Morte"
    }
    
    # Configuração base para todas as categorias
    config = {
        'extractors': {},
        'column_config': {
            "image_path": st.column_config.ImageColumn(
                "Imagem",
                help="Sprite do item",
                width="small"
            ),
            "item_name": st.column_config.TextColumn(
                "Item",
                help="Nome do item",
                width="medium"
            ),
            "url": st.column_config.LinkColumn(
                "Wiki",
                help="Link para a wiki do Tibia",
                width="small",
                display_text="Wiki"
            ),
            "Level": "Level",
            "Vocações": "Vocações"
        }
    }
    
    # Selecionar as propriedades corretas conforme a categoria
    selected_properties = []
    
    # Detectar qual tipo de item é com base no nome da categoria
    if category == 'Armors':
        selected_properties = combat_properties_armors
    elif category == 'Helmets':
        selected_properties = combat_properties_helmets
    elif category == 'Legs':
        selected_properties = combat_properties_legs
    elif category == 'Boots':
        selected_properties = combat_properties_boots
    elif category == 'Amulets_and_Necklaces':
        selected_properties = combat_properties_amulets
    elif category == 'Shields':
        selected_properties = combat_properties_shields
    elif category in ['Axes', 'Clubs', 'Swords', 'Distance_Weapons', 'Throwing_Weapons']:
        selected_properties = combat_properties_weapons
    elif category in ['Wands', 'Rods']:
        selected_properties = combat_properties_magic_weapons
    elif category == 'Rings':
        selected_properties = combat_properties_rings
    
    # Adicionar as propriedades selecionadas à configuração
    for prop in selected_properties:
        if prop in property_extractors:
            # Usar o nome da propriedade como chave para acessar na tabela
            config['extractors'][prop] = property_extractors[prop]
            # Usar o nome de exibição para o cabeçalho da coluna
            config['column_config'][prop] = property_display_names.get(prop, prop)
    
    return config

# Funções auxiliares de extração - chamadas pelas funções extratoras

def _extract_simple_property(data, property_name):
    """Extrai uma propriedade simples das Combat Properties"""
    if isinstance(data, dict):
        if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
            if property_name in data['Combat Properties']:
                value = data['Combat Properties'][property_name]
                
                # Tratar diferentes tipos de valores
                if isinstance(value, (int, float)):
                    # Para valores numéricos, mostrar com + para valores positivos
                    if value > 0:
                        return f"+{value}"
                    return str(value)
                elif isinstance(value, bool):
                    # Para valores booleanos, mostrar "Sim" ou "Não"
                    return "Sim" if value else "Não"
                elif isinstance(value, list):
                    # Para listas, juntar os valores com vírgula
                    return ", ".join(str(v) for v in value)
                else:
                    # Para outros tipos, converter para string
                    return str(value)
    return ""

def _extract_defense_modifier(data):
    """Extrai modificador de defesa para armas"""
    if isinstance(data, dict):
        if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
            if 'Defense Modifier' in data['Combat Properties']:
                value = data['Combat Properties']['Defense Modifier']
                if isinstance(value, int) or isinstance(value, float):
                    # Se for positivo, adicionar o sinal de +
                    if value > 0:
                        return f"+{value}"
                    return str(value)
                return str(value)
    return ""

def _extract_attributes(data):
    """Extrai atributos mágicos diretamente"""
    result = ""
    if isinstance(data, dict):
        if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
            if 'Attributes' in data['Combat Properties']:
                attributes = data['Combat Properties']['Attributes']
                if attributes:
                    if isinstance(attributes, dict):
                        # Iterar por todos os atributos disponíveis
                        attr_parts = []
                        for attr_key, attr_value in attributes.items():
                            # Converter para CamelCase
                            attr_display = ' '.join(word.capitalize() for word in attr_key.split())
                            attr_parts.append(f"{attr_display} +{attr_value}")
                        result = ", ".join(attr_parts)
                    else:
                        # Se for um valor simples, exibir de forma genérica
                        result = f"Atributos +{attributes}"
    return result

def _extract_imbuing_slots(data):
    """Extrai os slots de imbuement de um item"""
    if isinstance(data, dict):
        if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
            if 'Imbuing Slots' in data['Combat Properties']:
                slots = data['Combat Properties']['Imbuing Slots']
                if isinstance(slots, int):
                    return str(slots)
                return str(slots)
    return "0"

def _extract_element(data):
    """Extrai elemento de armas mágicas"""
    if isinstance(data, dict):
        if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
            if 'Element' in data['Combat Properties']:
                return str(data['Combat Properties']['Element']).capitalize()
    return ""

def _extract_damage(data):
    """Extrai dano de armas mágicas de forma amigável"""
    if isinstance(data, dict):
        if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
            if 'Damage' in data['Combat Properties']:
                damage_value = data['Combat Properties']['Damage']
                
                # Se for uma string, retornar diretamente
                if isinstance(damage_value, str):
                    return damage_value
                
                # Se for um número simples, formatar com + se necessário
                if isinstance(damage_value, (int, float)):
                    if damage_value > 0:
                        return f"+{damage_value}"
                    return str(damage_value)
                
                # Se for um range/lista, formatar como "X~Y"
                if isinstance(damage_value, list) and len(damage_value) == 2:
                    return f"{damage_value[0]}~{damage_value[1]}"
                
                # Se for um dicionário (normalmente elemento + dano)
                if isinstance(damage_value, dict):
                    result_parts = []
                    for element, value in damage_value.items():
                        # Capitalizar o elemento (ex: fire -> Fire)
                        element_display = element.capitalize()
                        
                        # Formatar o valor, que pode ser um número ou um range
                        if isinstance(value, (int, float)):
                            result_parts.append(f"{element_display}: {value}")
                        elif isinstance(value, list) and len(value) == 2:
                            result_parts.append(f"{element_display}: {value[0]}~{value[1]}")
                        else:
                            result_parts.append(f"{element_display}: {value}")
                    
                    return ", ".join(result_parts)
                
                # Fallback para qualquer outro formato
                return str(damage_value)
    return ""

def _extract_leech(data, property_name, attribute_name):
    """Extrai valores de leech (life ou mana)"""
    if isinstance(data, dict):
        if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
            if property_name in data['Combat Properties']:
                value = data['Combat Properties'][property_name]
                if isinstance(value, (int, float)):
                    return f"{value}%"
                return str(value)
            # Verificar também em Attributes para compatibilidade
            elif 'Attributes' in data['Combat Properties']:
                attr = data['Combat Properties']['Attributes']
                if isinstance(attr, dict) and attribute_name in attr:
                    return f"{attr[attribute_name]}%"
    return ""

def _extract_mana(data):
    """Extrai valor de Mana diretamente das Combat Properties"""
    if isinstance(data, dict):
        if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
            if 'Mana' in data['Combat Properties']:
                value = data['Combat Properties']['Mana']
                if isinstance(value, (int, float)) and value > 0:
                    return f"+{value}"
                return str(value)
    return ""

def _extract_resistances(data):
    """Extrai proteções elementais diretamente"""
    results = []
    if isinstance(data, dict):
        # Elementos possíveis
        elementos = {
            'physical': 'Físico',
            'earth': 'Terra',
            'fire': 'Fogo',
            'energy': 'Energia',
            'ice': 'Gelo',
            'holy': 'Sagrado',
            'death': 'Morte'
        }
        
        # Verificar diretamente nos dados (primeira verificação - case sensitive)
        for eng, ptbr in elementos.items():
            if eng in data:
                results.append(f"{ptbr}: {data[eng]}%")
        
        # Verificar também com primeira letra maiúscula (segunda verificação)
        for eng, ptbr in elementos.items():
            capitalized = eng.capitalize()
            if capitalized in data:
                results.append(f"{ptbr}: {data[capitalized]}%")
                
        # Verificar em "Protection" (terceira verificação)
        if "Protection" in data and isinstance(data["Protection"], dict):
            for eng, ptbr in elementos.items():
                if eng in data["Protection"]:
                    results.append(f"{ptbr}: {data['Protection'][eng]}%")
                # Verificar também com primeira letra maiúscula
                capitalized = eng.capitalize()
                if capitalized in data["Protection"]:
                    results.append(f"{ptbr}: {data['Protection'][capitalized]}%")
        
        # Verificar em Combat Properties > Resists (quarta verificação)
        if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
            # Verificar diretamente em Combat Properties (caso raro)
            for eng, ptbr in elementos.items():
                if eng in data['Combat Properties']:
                    results.append(f"{ptbr}: {data['Combat Properties'][eng]}%")
                # Verificar também com primeira letra maiúscula
                capitalized = eng.capitalize()
                if capitalized in data['Combat Properties']:
                    results.append(f"{ptbr}: {data['Combat Properties'][capitalized]}%")
            
            # Verificar em Combat Properties > Resists
            if 'Resists' in data['Combat Properties'] and isinstance(data['Combat Properties']['Resists'], dict):
                resists = data['Combat Properties']['Resists']
                for eng, ptbr in elementos.items():
                    if eng in resists:
                        results.append(f"{ptbr}: {resists[eng]}%")
                    # Verificar também com primeira letra maiúscula
                    capitalized = eng.capitalize()
                    if capitalized in resists:
                        results.append(f"{ptbr}: {resists[capitalized]}%")
    
    # Remover possíveis duplicatas
    unique_results = []
    seen = set()
    for item in results:
        element = item.split(':')[0].strip()
        if element not in seen:
            seen.add(element)
            unique_results.append(item)
    
    return ", ".join(unique_results)

def _extract_resists(data):
    """Extrai valores de resistências específicas do campo 'Resists'"""
    if not isinstance(data, dict):
        return ""
        
    if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
        # Se o campo Resists existir diretamente
        if 'Resists' in data['Combat Properties']:
            resists = data['Combat Properties']['Resists']
            
            # Se for um dicionário, processar cada elemento
            if isinstance(resists, dict):
                resist_parts = []
                
                # Mapear nomes de elementos em inglês para português
                elem_map = {
                    'physical': 'Físico',
                    'earth': 'Terra',
                    'fire': 'Fogo',
                    'ice': 'Gelo',
                    'energy': 'Energia',
                    'holy': 'Sagrado',
                    'death': 'Morte'
                }
                
                # Processar cada resistência
                for elem, value in resists.items():
                    # Verificar se é um elemento conhecido (caso sensível)
                    elem_lower = elem.lower()
                    if elem_lower in elem_map:
                        display_name = elem_map[elem_lower]
                    else:
                        # Se não for um dos elementos conhecidos, usar o nome como está
                        display_name = elem.capitalize()
                    
                    # Formatar o valor, adicionando % se for um número
                    if isinstance(value, (int, float)):
                        resist_parts.append(f"{display_name}: {value}%")
                    else:
                        resist_parts.append(f"{display_name}: {value}")
                
                return ", ".join(resist_parts)
            elif isinstance(resists, str):
                # Se for uma string, retornar diretamente
                return resists
            else:
                # Outros casos, converter para string
                return str(resists)
    
    # Se não encontrarmos o campo Resists, tentar usar a função de resistências gerais
    return _extract_resistances(data)

def _extract_charges(data):
    """Extrai as cargas de um item (especialmente amuletos)"""
    if isinstance(data, dict):
        # Verificar em diversas estruturas possíveis
        
        # 1. Verificar diretamente no campo Charges do nível superior
        if "Charges" in data and (isinstance(data["Charges"], int) or isinstance(data["Charges"], str)):
            return str(data["Charges"])
            
        # 2. Verificar em Combat Properties > Charges
        if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
            if 'Charges' in data['Combat Properties']:
                charges = data['Combat Properties']['Charges']
                return str(charges)
                
        # 3. Verificar em General Properties > Charges
        if 'General Properties' in data and isinstance(data['General Properties'], dict):
            if 'Charges' in data['General Properties']:
                charges = data['General Properties']['Charges']
                return str(charges)
                
        # 4. Procurar em qualquer campo que contenha informações de carga
        for section_name, section_data in data.items():
            if isinstance(section_data, dict):
                if 'Charges' in section_data:
                    return str(section_data['Charges'])
                    
                # Verificar também versões alternativas do nome
                # (ex: "charge", "max charges", etc.)
                for key in section_data.keys():
                    if 'charg' in key.lower():
                        return str(section_data[key])
    
    # Se não encontrou em nenhum lugar
    return ""

def _extract_critical_hit(data):
    """Extrai o valor de Critical Hit e formata como porcentagem se necessário"""
    if isinstance(data, dict):
        if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
            if 'Critical Hit' in data['Combat Properties']:
                value = data['Combat Properties']['Critical Hit']
                
                # Se for numérico, formatar como porcentagem
                if isinstance(value, (int, float)):
                    return f"{value}%"
                # Se for booleano, converter para "Sim/Não"
                elif isinstance(value, bool):
                    return "Sim" if value else "Não"
                # Outros formatos, retornar como estão
                return str(value)
    return ""

def reset_character_info():
    """Reset character information."""
    return None


set_config(title="Itens por Level", layout="wide")

# Exibe o menu de navegação
menu_with_redirect()

st.title("Itens por Level")

st.write("Encontre itens disponíveis para seu personagem com base no level e vocação.")

# Dropdown para selecionar/alterar a vocação
VOCATIONS_DISPLAY = {
    'sorcerers': 'Sorcerers',
    'druids': 'Druids',
    'knights': 'Knights',
    'paladins': 'Paladins',
    'monks': 'Monks'
}

# Obter a vocação da URL, se disponível
selected_vocation = st.query_params.get('vocation', 'sorcerers')
if selected_vocation not in ALL_VOCATIONS:
    selected_vocation = 'sorcerers'  # Valor padrão seguro

# Dropdown para selecionar/alterar a vocação
selected_vocation = st.selectbox(
    "Vocação:",
    options=ALL_VOCATIONS,
    format_func=lambda x: VOCATIONS_DISPLAY.get(x, x.capitalize()),
    index=ALL_VOCATIONS.index(selected_vocation),
    help="Selecione a vocação para filtrar os itens"
)

# Inputs para selecionar range de level
col1, col2 = st.columns(2)
with col1:
    min_level = st.number_input(
        "Level mínimo",
        min_value=0,
        max_value=599,
        value=0,
        step=1,
        help="Itens com requisito igual ou maior que este level serão mostrados"
    )
with col2:
    max_level = st.number_input(
        "Level máximo",
        min_value=min_level + 1,
        max_value=600,
        value=max(300, min_level + 1),
        step=1,
        help="Itens com requisito até este level serão mostrados"
    )

# Verificação do level mínimo e máximo
if min_level >= max_level:
    st.warning("O level mínimo deve ser menor que o level máximo. Ajustando valores...")
    min_level = max_level - 1

# Campo para inserir o nome do personagem e um botão de submissão
character_info = None
with st.expander("Buscar personagem (opcional)"):
    character_name = st.text_input(
        "Nome do Personagem", 
        help="Digite o nome exato do personagem no Tibia"
    )

    # Botão abaixo do campo do nome
    submit_button = st.button(
        "Buscar Personagem", 
        use_container_width=True
    )
    
    # Função para buscar personagem
    if submit_button and character_name:
        with st.spinner("Buscando informações do personagem..."):
            character_info = get_character_info(character_name)
            
            if character_info:
                # Primeiro padroniza a vocação
                character_vocation = standardize_vocation(character_info['vocation'])
                
                # Verificar se a vocação foi reconhecida
                if character_vocation:
                    # Atualizar o level máximo para o level do personagem
                    max_level = character_info['level']
                    
                    # Atualizar a vocação selecionada
                    selected_vocation = character_vocation
                    
                    # Atualizar URL para preservar a vocação
                    st.query_params['vocation'] = character_vocation
                    
                    # Formatar o nome do personagem
                    formatted_name = ' '.join(word.capitalize() for word in character_name.split())
                    
                    # Exibir o personagem encontrado
                    st.success(f"Personagem: **{formatted_name}** (Level {max_level}, {character_info['vocation']})")
                else:
                    st.error(f"Não foi possível reconhecer a vocação: {character_info['vocation']}")
                    character_info = None
            else:
                st.error(f"Personagem {character_name} não foi encontrado ou ocorreu um erro na consulta.")
                character_info = None

# Carregar e mostrar os itens automaticamente
try:
    # Carregar todos os itens do banco
    items = read_all_items()
    if not items:
        st.warning("Nenhum item encontrado no banco de dados.")
    else:
        # Converter para DataFrame
        df = pd.DataFrame(items)

        # Converter a coluna data_json para dicionário
        df['data_dict'] = df['data_json'].apply(
            lambda x: json.loads(x) if isinstance(x, str) else x
        )

        # Criar coluna de level
        df['level'] = df['data_dict'].apply(extract_level)

        # Criar coluna de vocações
        df['vocations'] = df['data_dict'].apply(extract_vocations_from_data)
        
        # Atualizar vocações para categorias especiais
        for idx, row in df.iterrows():
            category = row['category']
            item_name = row['item_name'].lower()
            
            # Se vocações já tem valores, pular esta linha
            if row['vocations'] and len(row['vocations']) > 0:
                continue
            
            # Primeiro verifica se é um quiver
            if 'quiver' in item_name:
                # Quivers são exclusivos para paladins
                df.loc[idx, 'vocations'] = ['paladins']
            # Depois verifica se é uma categoria de arma específica
            elif category in ['Clubs', 'Axes', 'Swords']:
                # Clubs, Axes e Swords são exclusivos para knights
                df.loc[idx, 'vocations'] = ['knights']
            elif category == 'Rods':
                # Rods são exclusivas para druids
                df.loc[idx, 'vocations'] = ['druids']
            elif category == 'Wands':
                # Wands são exclusivas para sorcerers
                df.loc[idx, 'vocations'] = ['sorcerers']
            elif category == 'Throwing_Weapons':
                # Throwing_Weapons são exclusivas para paladins
                df.loc[idx, 'vocations'] = ['paladins']
            # Se não é uma categoria específica e não tem vocação definida, mantém vazio
            # para indicar "Todas as vocações"
        
        # Filtrar por level
        filtered_df = df[
            (df['level'].notna()) &  # Remover itens sem level
            (df['level'] >= min_level) & 
            (df['level'] <= max_level)
        ]
        
        # Função robusta para verificar se um item é permitido para a vocação
        def is_allowed_for_vocation(vocations_list, vocation):
            """Verifica se um item é permitido para a vocação especificada."""
            # Se a lista estiver vazia, o item é para todas as vocações
            if not vocations_list or len(vocations_list) == 0:
                return True
            
            # Verifica se a vocação está na lista, considerando possíveis variações singulares
            try:
                # Verifica diretamente
                if vocation in vocations_list:
                    return True
                
                # Verifica normalização singular -> plural
                vocation_singular = vocation[:-1] if vocation.endswith('s') else vocation
                for voc in vocations_list:
                    # Verifica se a vocação na lista é igual à nossa vocação
                    if voc == vocation:
                        return True
                    # Verifica se a vocação na lista é uma versão singular da nossa vocação
                    if voc == vocation_singular:
                        return True
                    # Verifica se a versão plural da vocação na lista é igual à nossa vocação
                    if voc + 's' == vocation:
                        return True
                
                return False
            except Exception as e:
                # Em caso de erro, registrar para debug e retornar True para não filtrar o item incorretamente
                print(f"Erro ao verificar vocação: {e}")
                return True

        # Aplicar a filtragem por vocação usando a função robusta
        filtered_df = filtered_df[
            filtered_df['vocations'].apply(
                lambda x: is_allowed_for_vocation(x, selected_vocation)
            )
        ]

        # Verificar se há itens encontrados
        if filtered_df.empty:
            st.warning(f"Nenhum item encontrado para a vocação {selected_vocation.capitalize()} na faixa de level {min_level} a {max_level}.")
        else:
            # Agrupar itens por categoria
            categories = sorted(filtered_df['category'].unique())
            
            # Verificar se há categorias para mostrar
            if not categories:
                st.warning(f"Nenhum item encontrado para a vocação {selected_vocation.capitalize()} na faixa de level {min_level} a {max_level}.")
            else:
                # Exibir cada categoria com checkbox para controlar visibilidade
                st.write("Selecione as categorias que deseja visualizar:")

                # Organizar checkboxes em colunas
                num_cols = 3  # Número de colunas para os checkboxes
                cols = st.columns(num_cols)

                # Criar dicionário para armazenar estado dos checkboxes
                category_visible = {}

                # Distribuir checkboxes nas colunas
                for i, category in enumerate(categories):
                    col_idx = i % num_cols
                    with cols[col_idx]:
                        # Criar um checkbox para cada categoria
                        category_visible[category] = st.checkbox(
                            f"{category}",
                            value=False  # Todas as categorias começam DESMARCADAS
                        )
                
                # Mostrar tabelas apenas para categorias selecionadas
                for category in categories:
                    if category_visible[category]:
                        category_items = filtered_df[filtered_df['category'] == category]
                        
                        if not category_items.empty:
                            st.subheader(category)
                            
                            # Preparar o DataFrame para exibição
                            display_df = pd.DataFrame()
                            display_df['image_path'] = category_items['image_path']
                            display_df['item_name'] = category_items['item_name']  # Nome do item
                            display_df['Level'] = category_items['level']
                            
                            # Adicionar vocações como coluna
                            display_df['Vocações'] = category_items['vocations'].apply(get_vocations_display)
                            
                            # Verificar se há atributos para exibir
                            if not category_items.empty and 'data_dict' in category_items.columns:
                                # Garantir que todas as linhas tenham o data_dict como dicionário
                                category_items_copy = category_items.copy()
                                category_items_copy['data_dict'] = category_items_copy['data_dict'].apply(
                                    lambda x: json.loads(x) if isinstance(x, str) else x
                                )
                                
                                # Obter a configuração específica para esta categoria
                                category_config = get_category_config(category)
                                
                                # Adicionar colunas com base na configuração
                                for col_name, extractor_func in category_config['extractors'].items():
                                    display_df[col_name] = category_items_copy['data_dict'].apply(extractor_func)
                                
                                # Configuração para exibição
                                column_config = category_config['column_config']
                                
                                # Remover colunas vazias do dataframe (todas as linhas são vazias, None ou "")
                                cols_to_remove = []
                                for col in display_df.columns:
                                    # Pular colunas essenciais
                                    if col in ['image_path', 'item_name', 'Level', 'Vocações', 'url']:
                                        continue
                                    
                                    # Verificar se a coluna está vazia
                                    is_empty = display_df[col].apply(
                                        lambda x: (x is None or 
                                                x == "" or 
                                                x == "0" or 
                                                x == "0%" or 
                                                x == "-" or
                                                x == "Não" or 
                                                pd.isna(x))
                                    ).all()
                                    
                                    # Marcar a coluna para remoção se estiver vazia
                                    if is_empty:
                                        cols_to_remove.append(col)
                                
                                # Remover as colunas vazias
                                if cols_to_remove:
                                    # Remover do dataframe
                                    display_df = display_df.drop(columns=cols_to_remove)
                                    # Também remover da configuração de colunas
                                    for col in cols_to_remove:
                                        if col in column_config:
                                            del column_config[col]
                            else:
                                # Configuração básica se não houver dados adicionais
                                column_config = {
                                    "image_path": st.column_config.ImageColumn(
                                        "Imagem",
                                        help="Sprite do item",
                                        width="small"
                                    ),
                                    "item_name": st.column_config.TextColumn(
                                        "Item",
                                        help="Nome do item",
                                        width="medium"
                                    ),
                                    "Level": "Level",
                                    "Vocações": "Vocações"
                                }

                            # Criar links para a wiki do Tibia
                            display_df['url'] = category_items['item_name'].apply(
                                lambda x: f"https://tibia.fandom.com/wiki/{x.replace(' ', '_')}"
                            )
                            
                            # Exibir o DataFrame
                            st.dataframe(
                                display_df,
                                column_config=column_config,
                                use_container_width=True,
                                hide_index=True
                            )
except Exception as e:
    st.error(f"Erro ao processar itens: {str(e)}")
    # Adicionar informação mais detalhada para depuração
    import traceback
    st.error(traceback.format_exc()) 