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


# Adicionar vocações como coluna
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


def reset_character_info():
    """Reset character information in session state."""
    st.session_state.character_info = None


set_config(title="Itens por Level")

# Exibe o menu de navegação
menu_with_redirect()

st.title("Itens por Level")

st.write("Encontre itens disponíveis para seu personagem com base no level e vocação.")

# Se não já está definido no session_state, inicializar as variáveis
if 'min_level' not in st.session_state:
    st.session_state.min_level = 0
if 'max_level' not in st.session_state:
    st.session_state.max_level = 200
if 'character_info' not in st.session_state:
    st.session_state.character_info = None

# Função para mostrar os itens filtrados
def show_filtered_items(min_level, max_level, current_vocation):
    """Mostra os itens filtrados pela faixa de level e vocação."""
    try:
        # Carregar todos os itens do banco
        items = read_all_items()
        if not items:
            st.warning("Nenhum item encontrado no banco de dados.")
            return

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
        
        # Filtrar itens por level
        filtered_df = df.copy()
        
        # Filtrar por level
        filtered_df = filtered_df[
            (filtered_df['level'].notna()) &  # Remover itens sem level
            (filtered_df['level'] >= min_level) & 
            (filtered_df['level'] <= max_level)
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
                lambda x: is_allowed_for_vocation(x, current_vocation)
            )
        ]

        # Verificar se há itens encontrados
        if filtered_df.empty:
            st.warning(f"Nenhum item encontrado para a vocação {current_vocation.capitalize()} na faixa de level {min_level} a {max_level}.")
            return

        # Agrupar itens por categoria
        categories = sorted(filtered_df['category'].unique())
        
        # Verificar se há categorias para mostrar
        if not categories:
            st.warning(f"Nenhum item encontrado para a vocação {current_vocation.capitalize()} na faixa de level {min_level} a {max_level}.")
            return
        
        # Exibir cada categoria
        for category in categories:
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
                    
                    # Funções simples para extrair valores específicos
                    def get_armor(data):
                        """Extrai valor de armadura diretamente"""
                        if isinstance(data, dict):
                            # Verificar em Combat Properties
                            if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
                                if 'Armor' in data['Combat Properties']:
                                    return str(data['Combat Properties']['Armor'])
                        return ""
                    
                    def get_attributes(data):
                        """Extrai atributos mágicos diretamente"""
                        result = ""
                        if isinstance(data, dict):
                            # Procurar magic level
                            if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
                                if 'Attributes' in data['Combat Properties']:
                                    attributes = data['Combat Properties']['Attributes']
                                    if attributes:
                                        if isinstance(attributes, dict):
                                            # Se for um dicionário, extrair cada atributo
                                            attr_parts = []
                                            if 'magic level' in attributes:
                                                attr_parts.append(f"Magic Level +{attributes['magic level']}")
                                            if 'skills' in attributes:
                                                attr_parts.append(f"Skills +{attributes['skills']}")
                                            if 'distance skills' in attributes:
                                                attr_parts.append(f"Distance +{attributes['distance skills']}")
                                            if 'shield' in attributes:
                                                attr_parts.append(f"Shield +{attributes['shield']}")
                                            if 'melee' in attributes:
                                                attr_parts.append(f"Melee +{attributes['melee']}")
                                            result = ", ".join(attr_parts)
                                        else:
                                            # Se for um valor simples, exibir de forma genérica
                                            result = f"Atributos +{attributes}"
                        return result
                    
                    def get_resistances(data):
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
                            
                            # Verificar diretamente nos dados
                            for eng, ptbr in elementos.items():
                                if eng in data:
                                    results.append(f"{ptbr}: {data[eng]}%")
                            
                            # Verificar em Combat Properties > Resists
                            if 'Combat Properties' in data and isinstance(data['Combat Properties'], dict):
                                if 'Resists' in data['Combat Properties'] and isinstance(data['Combat Properties']['Resists'], dict):
                                    for eng, ptbr in elementos.items():
                                        if eng in data['Combat Properties']['Resists']:
                                            results.append(f"{ptbr}: {data['Combat Properties']['Resists'][eng]}%")
                        
                        return ", ".join(results)
                    
                    # Adicionar colunas diretamente
                    display_df['Arm'] = category_items_copy['data_dict'].apply(get_armor)
                    display_df['Attributes'] = category_items_copy['data_dict'].apply(get_attributes)
                    display_df['Proteções'] = category_items_copy['data_dict'].apply(get_resistances)
                
                # Criar links para a wiki do Tibia
                display_df['url'] = category_items['item_name'].apply(
                    lambda x: f"https://tibia.fandom.com/wiki/{x.replace(' ', '_')}"
                )
                
                # Exibir o DataFrame
                st.dataframe(
                    display_df,
                    column_config={
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
                        "Vocações": "Vocações",
                        "Arm": "Armadura",
                        "Attributes": "Atributos",
                        "Proteções": "Proteções Elementais"
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # Adicionar um separador entre categorias
                st.divider()
    except Exception as e:
        st.error(f"Erro ao processar itens: {str(e)}")
        # Adicionar informação mais detalhada para depuração
        import traceback
        st.error(traceback.format_exc())

# Usar parâmetros de URL para manter a vocação entre recarregamentos
if 'vocation' in st.query_params and st.query_params['vocation'] in ALL_VOCATIONS:
    st.session_state.selected_vocation = st.query_params['vocation']
elif 'selected_vocation' not in st.session_state:
    st.session_state.selected_vocation = 'sorcerers'  # Valor padrão

# Dropdown para selecionar/alterar a vocação
VOCATIONS_DISPLAY = {
    'sorcerers': 'Sorcerers',
    'druids': 'Druids',
    'knights': 'Knights',
    'paladins': 'Paladins',
    'monks': 'Monks'
}

# Criar opções para o dropdown de vocação
vocation_options = []
for voc in ALL_VOCATIONS:
    vocation_options.append({
        'label': VOCATIONS_DISPLAY.get(voc, voc.capitalize()),
        'value': voc
    })

# Garantir que a vocação selecionada seja um valor válido
if st.session_state.selected_vocation not in ALL_VOCATIONS:
    st.session_state.selected_vocation = ALL_VOCATIONS[0]  # Valor padrão seguro

# Encontrar o índice da vocação selecionada no dropdown
selected_index = 0
for i, opt in enumerate(vocation_options):
    if opt['value'] == st.session_state.selected_vocation:
        selected_index = i
        break

# Dropdown para selecionar/alterar a vocação
selected_vocation_value = st.selectbox(
    "Vocação:",
    options=ALL_VOCATIONS,
    format_func=lambda x: VOCATIONS_DISPLAY.get(x, x.capitalize()),
    index=selected_index,
    help="Selecione a vocação para filtrar os itens",
    key="pure_vocation_selector"
)

# Se a vocação foi alterada, atualizar a URL
if selected_vocation_value != st.session_state.selected_vocation:
    st.session_state.selected_vocation = selected_vocation_value
    # Atualizar os parâmetros de URL
    st.query_params['vocation'] = selected_vocation_value
    # Recarregar a página para mostrar os novos itens
    st.rerun()

# Inputs para selecionar range de level
col1, col2 = st.columns(2)
with col1:
    min_level = st.number_input(
        "Level mínimo",
        min_value=0,
        max_value=st.session_state.max_level - 1 if st.session_state.max_level > 0 else 599,
        value=st.session_state.min_level,
        step=1,
        key="min_level_input",
        help="Itens com requisito igual ou maior que este level serão mostrados"
    )
with col2:
    max_level = st.number_input(
        "Level máximo",
        min_value=min_level + 1,
        max_value=600,
        value=max(st.session_state.max_level, min_level + 1),
        step=1,
        key="max_level_input",
        help="Itens com requisito até este level serão mostrados"
    )

# Garantir que o level mínimo não ultrapasse o máximo
if min_level >= max_level:
    st.warning("O level mínimo deve ser menor que o level máximo. Ajustando valores...")
    min_level = max_level - 1
    st.session_state.min_level = min_level

# Atualizar o session_state se os valores mudaram
if min_level != st.session_state.min_level or max_level != st.session_state.max_level:
    st.session_state.min_level = min_level
    st.session_state.max_level = max_level
    # Carrega os itens automaticamente quando os valores são alterados
    st.rerun()

# Campo para inserir o nome do personagem e um botão de submissão
with st.expander("Buscar personagem (opcional)"):
    character_name = st.text_input(
        "Nome do Personagem", 
        help="Digite o nome exato do personagem no Tibia",
        key="submitted_character_name"
    )

    # Botão abaixo do campo do nome
    submit_button = st.button(
        "Buscar Personagem", 
        key="visible_submit", 
        use_container_width=True
    )
    
    # Verificar se o Enter foi pressionado no campo de texto
    submit_by_enter = character_name != "" and character_name != st.session_state.get("last_character_name", "")

    # Função para buscar personagem
    def buscar_personagem():
        if character_name:
            # Armazenar o nome atual para comparação futura
            st.session_state["last_character_name"] = character_name
            
            with st.spinner("Buscando informações do personagem..."):
                character_info = get_character_info(character_name)
                
                if character_info:
                    # Primeiro padroniza a vocação
                    character_vocation = standardize_vocation(character_info['vocation'])
                    
                    # Verificar se a vocação foi reconhecida
                    if character_vocation:
                        # Atualiza as informações na session_state
                        st.session_state.character_info = character_info
                        st.session_state.max_level = character_info['level']
                        
                        # Se a vocação mudou, atualizar parâmetros de URL e forçar recarga
                        if st.session_state.selected_vocation != character_vocation:
                            # Atualizar URL para preservar a vocação entre recarregamentos
                            st.query_params['vocation'] = character_vocation
                            st.session_state.selected_vocation = character_vocation
                        
                        # Definir que devemos mostrar os itens
                        st.session_state.show_items = True
                        st.rerun()
                    else:
                        st.error(f"Não foi possível reconhecer a vocação: {character_info['vocation']}")
                        st.session_state.character_info = None
                else:
                    st.error(f"Personagem {character_name} não foi encontrado ou ocorreu um erro na consulta.")
                    st.session_state.character_info = None

    # Processar a submissão
    if submit_button or submit_by_enter:
        buscar_personagem()

# Linha divisória para separar configuração e resultados
st.markdown("---")

# Se temos informações do personagem, mostrar detalhes
if st.session_state.character_info:
    character_info = st.session_state.character_info
    character_level = character_info['level']
    character_vocation = character_info['vocation']
    
    # Formatar o nome do personagem com a mesma capitalização do site oficial
    # Para isso, vamos usar a primeira letra maiúscula e o resto minúsculo para cada palavra
    formatted_name = ' '.join(word.capitalize() for word in character_name.split())
    
    # Exibir o personagem encontrado em um formato mais amigável
    st.success(f"Personagem: **{formatted_name}** (Level {character_level}, {character_vocation})")

# Mostrar itens automaticamente ou se o botão foi pressionado
if 'show_items' in st.session_state and st.session_state.show_items:
    # Usar o valor do session_state para a filtragem
    show_filtered_items(min_level, max_level, selected_vocation_value)
    # Resetar o estado para não mostrar os itens automaticamente na próxima vez
    st.session_state.show_items = False
else:
    # Mostrar itens por padrão ao abrir a página
    show_filtered_items(min_level, max_level, selected_vocation_value) 