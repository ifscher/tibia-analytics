import streamlit as st
import pandas as pd
import json
import requests
from bs4 import BeautifulSoup
import re
from mydb import read_all_items
from utils.menu import menu_with_redirect
from utils.favicon import set_config
from utils.vocation import extract_vocations


def extract_level(data):
    """Extrai o level do item."""
    if isinstance(data, dict):
        if 'Lvl' in data:
            try:
                # Remover qualquer texto não numérico e converter para inteiro
                level_str = str(data['Lvl'])
                level_str = ''.join(c for c in level_str if c.isdigit())
                if level_str:
                    return int(level_str)
            except (ValueError, TypeError):
                return 0
    return 0


def get_character_info(character_name):
    """Obtém informações do personagem do site do Tibia."""
    url = f"https://www.tibia.com/community/?subtopic=characters&name={character_name}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
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
                vocation_match = re.search(r'Vocation:(Master Sorcerer|Elder Druid|Elite Knight|Royal Paladin|Exalted Monk|Sorcerer|Druid|Knight|Paladin|Monk)', info_table.get_text())
                if vocation_match:
                    vocation = vocation_match.group(1).strip()
                else:
                    vocation = None
                
                # Verificar se encontrou as informações
                if level == 0 or vocation is None:
                    st.error("Não foi possível encontrar o level ou a vocação do personagem.")
                    return None
                
                return {
                    'level': level,
                    'vocation': vocation
                }
            else:
                st.error("Não foi possível encontrar as informações do personagem.")
                return None
    except Exception as e:
        st.error(f"Erro ao buscar informações do personagem: {str(e)}")
    
    return None


def standardize_vocation(vocation):
    """Padroniza o nome da vocação."""
    if not vocation:
        return None
    
    # Converter para minúsculo e remover espaços extras
    vocation = vocation.lower().strip()
    
    # Mapeamento de vocações do site para vocações do banco
    vocation_mapping = {
        'master sorcerer': 'sorcerers',
        'elder druid': 'druids',
        'elite knight': 'knights',
        'royal paladin': 'paladins',
        'exalted monk': 'monks',
        'sorcerer': 'sorcerers',
        'druid': 'druids',
        'knight': 'knights',
        'paladin': 'paladins',
        'monk': 'monks'
    }
    
    # Verificar se a vocação está exatamente no mapeamento
    if vocation in vocation_mapping:
        return vocation_mapping[vocation]
    
    # Se não encontrou exatamente, procurar por partes do nome
    for key, value in vocation_mapping.items():
        if key in vocation:
            return value
    
    return None


def extract_vocations_from_json(data):
    """Extrai as vocações do item."""
    if isinstance(data, dict):
        # Primeiro tenta o campo 'Vocation' (singular)
        if 'Vocation' in data and data['Vocation']:
            vocations = data['Vocation'].split(',')
            vocations = [v.strip() for v in vocations if v.strip()]
            if vocations:  # Se encontrou vocações no campo 'Vocation'
                # Se a vocação contém "and", separa em múltiplas vocações
                result = []
                for v in vocations:
                    if ' and ' in v.lower():
                        # Divide a string em vocações individuais
                        parts = v.lower().split(' and ')
                        for part in parts:
                            part = part.strip()
                            if part in VOCATION_MAPPING:
                                result.append(VOCATION_MAPPING[part])
                    else:
                        if v.lower() in VOCATION_MAPPING:
                            result.append(VOCATION_MAPPING[v.lower()])
                return result
        # Se não tem vocação definida, retorna todas as vocações
        return ['sorcerers', 'druids', 'knights', 'paladins', 'monks']
    return []


# Mapeamento de vocações para padronização
VOCATION_MAPPING = {
    'sorcerer': 'sorcerers',
    'sorcerers': 'sorcerers',
    'druid': 'druids',
    'druids': 'druids',
    'knight': 'knights',
    'knights': 'knights',
    'paladin': 'paladins',
    'paladins': 'paladins',
    'monk': 'monks',
    'monks': 'monks'
}

set_config(title="Itens por Level")

# Redireciona se não estiver logado
menu_with_redirect()

st.title("Itens por Level")

# Inicializar o session_state se necessário
if 'character_info' not in st.session_state:
    st.session_state.character_info = None
if 'min_level' not in st.session_state:
    st.session_state.min_level = 0
if 'max_level' not in st.session_state:
    st.session_state.max_level = 0

# Campo para inserir o nome do personagem
character_name = st.text_input("Nome do Personagem")

# Botão para buscar informações do personagem
if st.button("Buscar Personagem"):
    if character_name:
        with st.spinner("Buscando informações do personagem..."):
            character_info = get_character_info(character_name)
            
            if character_info:
                st.session_state.character_info = character_info
                st.session_state.min_level = 0
                st.session_state.max_level = character_info['level']
            else:
                st.session_state.character_info = None
                st.session_state.min_level = 0
                st.session_state.max_level = 0

# Se temos informações do personagem, mostrar os itens
if st.session_state.character_info:
    character_info = st.session_state.character_info
    character_level = character_info['level']
    character_vocation = character_info['vocation']
    
    st.success(f"Personagem encontrado: {character_name}")
    st.write(f"Level: {character_level}")
    st.write(f"Vocação: {character_vocation}")
    
    # Inputs para selecionar range de level
    col1, col2 = st.columns(2)
    with col1:
        min_level = st.number_input(
            "Level mínimo",
            min_value=0,
            max_value=st.session_state.max_level - 1,
            value=st.session_state.min_level,
            step=1,
            key="min_level"
        )
    with col2:
        max_level = st.number_input(
            "Level máximo",
            min_value=min_level + 1,
            max_value=600,
            value=min(st.session_state.max_level, character_level),
            step=1,
            key="max_level"
        )
    
    # Atualizar o session_state com os novos valores dos inputs
    if min_level != st.session_state.min_level or max_level != st.session_state.max_level:
        st.session_state.min_level = min_level
        st.session_state.max_level = max_level
        st.rerun()
    
    # Usar o valor do session_state para a filtragem
    try:
        min_level = int(st.session_state.min_level)
        max_level = int(st.session_state.max_level)
        
        # Carregar todos os itens do banco
        items = read_all_items()
        if not items:
            st.warning("Nenhum item encontrado no banco de dados.")
            st.stop()

        # Converter para DataFrame
        df = pd.DataFrame(items)

        # Converter a coluna data_json para dicionário
        df['data_dict'] = df['data_json'].apply(
            lambda x: json.loads(x) if isinstance(x, str) else x
        )

        # Criar colunas para vocação e level
        df['vocations'] = df['data_dict'].apply(extract_vocations_from_json)

        # Criar coluna de level
        df['level'] = df['data_dict'].apply(extract_level)

        # Adicionar vocações específicas para categorias especiais
        for idx, row in df.iterrows():
            category = row['category']
            item_name = row['item_name'].lower()
            
            # Primeiro verifica se é um quiver
            if 'quiver' in item_name:
                # Quivers são exclusivos para paladins
                df.at[idx, 'vocations'] = ['paladins']
            # Depois verifica se é uma categoria de arma específica
            elif category in ['Clubs', 'Axes', 'Swords']:
                # Clubs, Axes e Swords são exclusivos para knights
                df.at[idx, 'vocations'] = ['knights']
            elif category == 'Rods':
                # Rods são exclusivas para druids
                df.at[idx, 'vocations'] = ['druids']
            elif category == 'Wands':
                # Wands são exclusivas para sorcerers
                df.at[idx, 'vocations'] = ['sorcerers']
            elif category == 'Throwing_Weapons':
                # Throwing_Weapons são exclusivas para paladins
                df.at[idx, 'vocations'] = ['paladins']
            # Se não é uma categoria específica e não tem vocação definida
            elif not row['vocations']:
                # Para outras categorias sem vocação definida, atribuir a todas as vocações
                df.at[idx, 'vocations'] = ['sorcerers', 'druids', 'knights', 'paladins', 'monks']

        # Padronizar a vocação do personagem
        standardized_vocation = standardize_vocation(character_vocation)
        
        # Filtrar itens por level e vocação
        filtered_df = df.copy()
        
        # Filtrar por level
        filtered_df = filtered_df[
            (filtered_df['level'].notna()) &  # Remover itens sem level
            (filtered_df['level'] >= min_level) & 
            (filtered_df['level'] <= max_level)
        ]
        
        if standardized_vocation:
            filtered_df = filtered_df[
                filtered_df['vocations'].apply(
                    lambda x: standardized_vocation in x if isinstance(x, list) else False
                )
            ]

        # Agrupar itens por categoria
        categories = sorted(filtered_df['category'].unique())
        
        # Debug: mostrar todas as categorias disponíveis
        st.write("Categorias disponíveis:", categories)
        
        for category in categories:
            category_items = filtered_df[filtered_df['category'] == category]
            
            if not category_items.empty:
                st.subheader(category)
                
                # Preparar o DataFrame para exibição
                display_df = pd.DataFrame()
                display_df['image_path'] = category_items['image_path']
                display_df['item_name'] = category_items['item_name']  # Nome do item
                display_df['Level'] = category_items['level']
                display_df['Vocações'] = category_items['vocations'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
                
                # Adicionar atributos relevantes
                for attr in ['Attack', 'Defense', 'Arm', 'Weight', 'Requirements', 'Attributes']:
                    if attr in category_items['data_dict'].iloc[0]:
                        display_df[attr] = category_items['data_dict'].apply(
                            lambda x: x.get(attr, '')
                        )
                
                # Criar links para a wiki do Tibia
                display_df['url'] = display_df['item_name'].apply(
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
                        "Attack": "Ataque",
                        "Defense": "Defesa",
                        "Arm": "Armadura",
                        "Weight": "Peso",
                        "Requirements": "Requisitos",
                        "Attributes": "Atributos"
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # Adicionar um separador entre categorias
                st.divider()
    except Exception as e:
        st.error(f"Erro ao processar itens: {str(e)}")
else:
    st.info("Digite o nome do personagem e clique em 'Buscar Personagem' para ver os itens disponíveis.") 