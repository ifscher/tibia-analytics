import streamlit as st
import pandas as pd
import json
from mydb import read_all_items, read_item
from utils.menu import menu_with_redirect
from utils.favicon import set_config
from utils.vocation import extract_vocations
from utils.config import extract_level

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

# Lista de todas as vocações possíveis
ALL_VOCATIONS = ['sorcerers', 'druids', 'knights', 'paladins', 'monks']

def standardize_vocation(vocation, verbose=False):
    """Padroniza o nome da vocação."""
    if not vocation:
        return None
    
    # Converter para minúsculo e remover espaços extras
    vocation = vocation.lower().strip()
    
    # Verificar se está no mapeamento
    if vocation in VOCATION_MAPPING:
        return VOCATION_MAPPING[vocation]
    
    # Se não estiver no mapeamento, retornar None
    if verbose:
        print(f"Vocação não reconhecida: {vocation}")
    return None

# A função extract_level agora é importada de utils.config
# e possui lógica avançada para encontrar o level dos itens em diferentes estruturas

# Função para extrair atributos importantes dos dados (formato novo)
def extract_attributes(data):
    """
    Extrai atributos importantes de um item no formato novo de dados.
    
    Args:
        data (dict): Dicionário de dados do item
        
    Returns:
        dict: Dicionário com atributos extraídos
    """
    result = {}
    
    if not isinstance(data, dict):
        return result
    
    # Level (já temos uma função específica)
    result["Level"] = extract_level(data)
    
    # Extrair vocações (verificar Requirements > Vocation)
    vocations = []
    
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
                if voc in VOCATION_MAPPING:
                    vocations.append(VOCATION_MAPPING[voc])
        elif isinstance(vocation_data, list):
            # Se for lista, processar cada item
            for voc in vocation_data:
                if isinstance(voc, str) and voc.lower() in VOCATION_MAPPING:
                    vocations.append(VOCATION_MAPPING[voc.lower()])
    
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
                if voc in VOCATION_MAPPING:
                    vocations.append(VOCATION_MAPPING[voc])
        elif isinstance(vocations_data, list):
            # Se for lista, processar cada item
            for voc in vocations_data:
                if isinstance(voc, str) and voc.lower() in VOCATION_MAPPING:
                    vocations.append(VOCATION_MAPPING[voc.lower()])
    
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
                if voc in VOCATION_MAPPING:
                    vocations.append(VOCATION_MAPPING[voc])
        elif isinstance(vocation_data, list):
            # Se for lista, processar cada item
            for voc in vocation_data:
                if isinstance(voc, str) and voc.lower() in VOCATION_MAPPING:
                    vocations.append(VOCATION_MAPPING[voc.lower()])
    
    # Se não encontrou vocações, considerar como "Todas"
    if not vocations:
        result["Vocações"] = "Todas"
    else:
        # Usar as vocações encontradas (remover duplicatas e ordenar)
        vocations = sorted(list(set(vocations)))
        result["Vocações"] = ", ".join(vocations)
    
    # Propriedades de Combate
    if "Combat Properties" in data and isinstance(data["Combat Properties"], dict):
        combat = data["Combat Properties"]
        
        # Attack
        if "Attack" in combat:
            result["Ataque"] = combat["Attack"]
        
        # Defense
        if "Defense" in combat:
            result["Defesa"] = combat["Defense"]
        
        # Armor
        if "Armor" in combat:
            result["Armadura"] = combat["Armor"]
        elif "Arm" in combat:
            result["Armadura"] = combat["Arm"]
    
    # Propriedades Gerais
    if "General Properties" in data and isinstance(data["General Properties"], dict):
        general = data["General Properties"]
        
        # Weight
        if "Weight" in general:
            result["Peso"] = general["Weight"]
    
    # Propriedades de Comércio
    if "Trade Properties" in data and isinstance(data["Trade Properties"], dict):
        trade = data["Trade Properties"]
        
        # Value (preço de venda)
        if "Value" in trade:
            result["Valor de Venda"] = trade["Value"]
        
        # Sell Value
        if "Sell Value" in trade:
            result["Valor de Venda"] = trade["Sell Value"]
        
        # Bought for / Sold for
        if "Bought For" in trade:
            result["Valor de Compra"] = trade["Bought For"]
        elif "Sold For" in trade:
            result["Valor de Compra"] = trade["Sold For"]
    
    # Atributos (bonuses)
    if "attributes" in data and isinstance(data["attributes"], dict):
        result["Atributos"] = data["attributes"]
    elif "Attributes" in data:
        result["Atributos"] = data["Attributes"]
    
    # Resistências
    if "resistances" in data and isinstance(data["resistances"], dict):
        result["Resistências"] = data["resistances"]
    elif "Resistances" in data:
        result["Resistências"] = data["Resistances"]
    
    # Peso (campo direto)
    if "Weight" in data:
        result["Peso"] = data["Weight"]
    
    return result

set_config(title="Comparador de Itens")

# Exibe o menu de navegação
menu_with_redirect()

st.title("Comparador de Itens")

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

# Extrair atributos importantes
df['attributes'] = df['data_dict'].apply(extract_attributes)

# Criar colunas para vocação e level
df['vocations'] = df['data_dict'].apply(
    lambda x: extract_vocations(x, verbose=False)
)

# Criar coluna de level
df['level'] = df['data_dict'].apply(extract_level)

# Atualizar vocações para categorias especiais apenas se não tiver vocações definidas
for idx, row in df.iterrows():
    # Verificar se vocações está vazio
    if not row['vocations'] or len(row['vocations']) == 0:
        category = row['category']
        
        # Atribuir vocações específicas para categorias
        if category == 'Quivers':
            # Quivers são exclusivos para paladins
            df.at[idx, 'vocations'] = ['paladins']
            # Atualizar também os atributos extraídos
            if 'attributes' in df.loc[idx] and isinstance(df.loc[idx]['attributes'], dict):
                df.loc[idx]['attributes']["Vocações"] = "paladins"
        elif category == 'Wands':
            # Wands são exclusivos para sorcerers
            df.at[idx, 'vocations'] = ['sorcerers']
            if 'attributes' in df.loc[idx] and isinstance(df.loc[idx]['attributes'], dict):
                df.loc[idx]['attributes']["Vocações"] = "sorcerers"
        elif category == 'Rods':
            # Rods são exclusivos para druids
            df.at[idx, 'vocations'] = ['druids']
            if 'attributes' in df.loc[idx] and isinstance(df.loc[idx]['attributes'], dict):
                df.loc[idx]['attributes']["Vocações"] = "druids"
        elif category in ['Clubs', 'Axes', 'Swords']:
            # Clubs, Axes e Swords são exclusivos para knights
            df.at[idx, 'vocations'] = ['knights']
            if 'attributes' in df.loc[idx] and isinstance(df.loc[idx]['attributes'], dict):
                df.loc[idx]['attributes']["Vocações"] = "knights"
        elif category == 'Fist_Fighting_Weapons':
            # Fist Fighting Weapons são exclusivos para monks
            df.at[idx, 'vocations'] = ['monks']
            if 'attributes' in df.loc[idx] and isinstance(df.loc[idx]['attributes'], dict):
                df.loc[idx]['attributes']["Vocações"] = "monks"
        else:
            # Para outras categorias, vocação vazia significa que pode ser usado por todas as vocações
            df.at[idx, 'vocations'] = ALL_VOCATIONS
            # Atualizar também nos atributos
            if 'attributes' in df.loc[idx] and isinstance(df.loc[idx]['attributes'], dict):
                df.loc[idx]['attributes']["Vocações"] = "Todas"

# Filtros
st.subheader("Filtros")

# Selecionar categoria
categories = sorted(df['category'].unique())
selected_category = st.selectbox(
    "Selecione a categoria dos itens:",
    categories
)

# Filtrar por categoria
filtered_df = df[df['category'] == selected_category]

# Selecionar vocação
all_vocations = set()
for vocations in filtered_df['vocations']:
    if vocations and len(vocations) > 0:  # Verificar se a lista não está vazia
        all_vocations.update(vocations)
vocations = sorted(all_vocations)

# Inicializar a variável para armazenar a vocação selecionada
selected_vocation = None

if vocations:
    selected_vocation = st.selectbox(
        "Selecione a vocação:",
        ["Todas"] + vocations
    )
    
    if selected_vocation != "Todas":
        # Filtrar apenas itens que pertencem à vocação selecionada
        filtered_df = filtered_df[
            filtered_df['vocations'].apply(
                lambda x: selected_vocation in x if isinstance(x, list) else False
            )
        ]
else:
    st.info("Nenhuma vocação encontrada para esta categoria.")

# Selecionar range de level
st.subheader("Filtro por Level")

# Criar slider para selecionar range de level
level_range = st.slider(
    "Selecione o range de level:",
    min_value=0,
    max_value=600,
    value=(0, 600),
    step=1
)

# Filtrar por range de level
filtered_df = filtered_df[
    (filtered_df['level'].isna()) | 
    ((filtered_df['level'].astype(float) >= level_range[0]) & 
     (filtered_df['level'].astype(float) <= level_range[1]))
]

# Verificar se há itens após a filtragem
if filtered_df.empty:
    st.warning("Nenhum item encontrado com os filtros selecionados.")
    st.stop()

# Selecionar item principal
main_item = st.selectbox(
    "Selecione o item principal para comparação:",
    filtered_df['item_name'].tolist()
)

# Selecionar itens para comparar com o principal
other_items = st.multiselect(
    "Selecione os itens para comparar:",
    [item for item in filtered_df['item_name'].tolist() 
     if item != main_item],
    max_selections=5
)

if main_item and other_items:
    # Filtrar apenas os itens selecionados
    comparison_items = [main_item] + other_items
    comparison_df = filtered_df[
        filtered_df['item_name'].isin(comparison_items)
    ].copy()
    
    # Criar um novo DataFrame para comparação usando os atributos extraídos
    comparison_data = []
    for _, row in comparison_df.iterrows():
        item_data = {
            'Item': row['item_name'],
            'Imagem': row['image_path']
        }
        
        # Adicionar atributos extraídos
        if isinstance(row['attributes'], dict):
            for attr, value in row['attributes'].items():
                item_data[attr] = value
        
        comparison_data.append(item_data)
    
    # Criar DataFrame de comparação
    comparison_df = pd.DataFrame(comparison_data)
    
    # Separar o item principal dos outros
    main_item_df = comparison_df[comparison_df['Item'] == main_item]
    other_items_df = comparison_df[comparison_df['Item'] != main_item]
    
    # Função para adicionar cor e seta aos valores numéricos na comparação
    def format_comparison_value(value, main_value, attr):
        if pd.isna(value) or pd.isna(main_value):
            return str(value) if value is not None else ''
        
        # Se o atributo for "Vocações" e o valor for "Todas"
        if attr == "Vocações":
            return str(value)
        
        try:
            # Tentar converter para número
            if isinstance(value, (int, float)) and isinstance(main_value, (int, float)):
                val = float(value)
                main_val = float(main_value)
            else:
                val = float(str(value).replace(',', '.'))
                main_val = float(str(main_value).replace(',', '.'))
            
            # Decidir qual cor e seta usar com base no atributo
            # Para a maioria dos atributos, maior é melhor (verde)
            is_higher_better = True
            
            # Exceções: para peso, menor é melhor
            if attr.lower() in ["peso", "weight"]:
                is_higher_better = False
            
            if val > main_val:
                color = "green" if is_higher_better else "red"
                arrow = "▲" if is_higher_better else "▼"
                return f"<span style='color: {color};'>{val} {arrow}</span>"
            elif val < main_val:
                color = "red" if is_higher_better else "green"
                arrow = "▼" if is_higher_better else "▲"
                return f"<span style='color: {color};'>{val} {arrow}</span>"
            else:
                return str(val)
        except (ValueError, TypeError):
            # Se não for número, retornar valor original
            return str(value) if value is not None else ''

    # Exibir o item principal e os outros itens lado a lado
    st.subheader("Comparação de Itens")
    
    # Criar colunas para cada item
    cols = st.columns([1] + [1] * len(other_items))
    
    # Exibir cabeçalho com imagens
    with cols[0]:
        st.write("### Item Principal")
        st.image(main_item_df['Imagem'].iloc[0], width=100)
        st.write(f"**{main_item_df['Item'].iloc[0]}**")
    
    for i, (_, row) in enumerate(other_items_df.iterrows(), 1):
        with cols[i]:
            st.write(f"### Item {i}")
            st.image(row['Imagem'], width=100)
            st.write(f"**{row['Item']}**")
    
    # Exibir atributos
    st.write("### Atributos")
    
    # Lista de atributos para exibir (remover Item e Imagem)
    display_attrs = [col for col in comparison_df.columns if col not in ['Item', 'Imagem']]
    
    # Ordenar os atributos para exibir os mais importantes primeiro
    priority_attrs = ['Level', 'Vocações', 'Ataque', 'Defesa', 'Armadura', 'Peso', 'Valor de Venda', 'Valor de Compra', 'Atributos', 'Resistências']
    
    # Ordenar conforme prioridade
    display_attrs = sorted(display_attrs, key=lambda x: priority_attrs.index(x) if x in priority_attrs else 999)
    
    # Identificar atributos numéricos
    numeric_attrs = set()
    for attr in display_attrs:
        if attr not in comparison_df.columns:
            continue
            
        # Verificar se o atributo contém valores numéricos
        sample_values = comparison_df[attr].dropna().head()
        if not sample_values.empty:
            try:
                # Tentar converter alguns valores para ver se são numéricos
                for val in sample_values:
                    if isinstance(val, (int, float)):
                        numeric_attrs.add(attr)
                        break
                    elif isinstance(val, str):
                        float(val.replace(',', '.'))
                        numeric_attrs.add(attr)
                        break
            except (ValueError, TypeError, AttributeError):
                continue
    
    # Criar um container para a tabela de atributos
    with st.container():
        # Criar colunas para cada item
        cols = st.columns([1, 1] + [1] * len(other_items))
        
        # Cabeçalho da tabela
        with cols[0]:
            st.write("**Atributo**")
        with cols[1]:
            st.write("**Item Principal**")
        for i, (_, row) in enumerate(other_items_df.iterrows(), 1):
            with cols[i + 1]:
                st.write(f"**Item {i}**")
        
        # Separador após o cabeçalho
        st.divider()
        
        # Linhas de atributos
        for attr in display_attrs:
            if attr not in comparison_df.columns:
                continue
                
            # Criar colunas para cada item
            cols = st.columns([1, 1] + [1] * len(other_items))
            
            # Nome do atributo
            with cols[0]:
                st.write(f"**{attr}**")
            
            # Valor do item principal
            main_value = main_item_df[attr].iloc[0] if attr in main_item_df.columns else None
            with cols[1]:
                # Tratar atributos e resistências especiais
                if attr in ["Atributos", "Resistências"] and isinstance(main_value, dict):
                    for k, v in main_value.items():
                        st.write(f"- {k}: {v}")
                else:
                    st.write(str(main_value) if main_value is not None else '')
            
            # Valores dos outros itens
            for i, (_, row) in enumerate(other_items_df.iterrows(), 1):
                with cols[i + 1]:
                    value = row[attr] if attr in row else None
                    
                    # Tratar atributos e resistências especiais
                    if attr in ["Atributos", "Resistências"] and isinstance(value, dict):
                        # Comparar com o dicionário principal, se existir
                        if isinstance(main_value, dict):
                            for k, v in value.items():
                                if k in main_value:
                                    main_v = main_value[k]
                                    # Tentar formatação com cor
                                    try:
                                        if isinstance(v, (int, float)) and isinstance(main_v, (int, float)):
                                            formatted = format_comparison_value(v, main_v, k)
                                            st.markdown(f"- {k}: {formatted}", unsafe_allow_html=True)
                                        else:
                                            st.write(f"- {k}: {v}")
                                    except:
                                        st.write(f"- {k}: {v}")
                                else:
                                    st.write(f"- {k}: {v}")
                        else:
                            for k, v in value.items():
                                st.write(f"- {k}: {v}")
                    elif attr in numeric_attrs:
                        formatted = format_comparison_value(value, main_value, attr)
                        st.markdown(formatted, unsafe_allow_html=True)
                    else:
                        st.write(str(value) if value is not None else '')
            
            # Separador entre atributos
            st.divider()

else:
    if not main_item:
        st.info("Selecione um item principal.")
    elif not other_items:
        st.info("Selecione itens para comparar.") 