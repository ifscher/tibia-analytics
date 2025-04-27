import streamlit as st
import json
from mydb import read_all_items, read_item
from utils.menu import menu_with_redirect
from utils.favicon import set_config
from utils.vocation import extract_vocations
import os

def render_resistances(resistances_dict):
    """Renderiza resistências com formatação de cores"""
    if not resistances_dict or not isinstance(resistances_dict, dict):
        return str(resistances_dict)
    
    resistance_html = "<div style='margin-top: 5px;'>"
    for element, value in resistances_dict.items():
        color = "green" if value > 0 else "red"
        sign = "+" if value > 0 else ""
        resistance_html += f"""
        <div style='display: inline-block; margin-right: 10px; margin-bottom: 5px;'>
            <span style='font-weight: bold; text-transform: capitalize;'>
                {element}:
            </span> 
            <span style='color: {color};'>{sign}{value}%</span>
        </div>"""
    resistance_html += "</div>"
    return resistance_html


def process_magic_attributes(attributes):
    """
    Processa atributos mágicos como "magic level +3" e retorna um dicionário estruturado.
    
    Args:
        attributes: Lista ou string de atributos
        
    Returns:
        dict: Dicionário com atributos processados
    """
    result = {}
    
    if isinstance(attributes, list):
        for attr in attributes:
            if isinstance(attr, str):
                # Procurar padrões como "magic level +3" ou qualquer "atributo +/-N"
                import re
                
                # Tenta encontrar padrão "alguma coisa +/-N"
                match = re.search(r'(.*?)\s+([+-]?\d+)$', attr.lower().strip())
                if match:
                    attr_name = match.group(1).strip()
                    value = int(match.group(2))
                    result[attr_name] = value
    
    return result


def render_attribute_dict(attr_dict):
    """
    Renderiza um dicionário de atributos como distance fighting, magic level etc.
    com formatação de cores.
    
    Args:
        attr_dict (dict): Dicionário com atributos e seus valores
        
    Returns:
        str: HTML formatado com os atributos
    """
    if not attr_dict or not isinstance(attr_dict, dict):
        return str(attr_dict)
    
    attr_html = "<div style='margin-top: 5px;'>"
    for attr_name, value in attr_dict.items():
        # Define a cor com base no valor (positivo=verde, negativo=vermelho)
        color = "green" if value > 0 else "red"
        sign = "+" if value > 0 else ""
        
        attr_html += f"""
        <div style='margin-bottom: 5px;'>
            <span style='font-weight: bold; text-transform: capitalize;'>
                {attr_name}:
            </span> 
            <span style='color: {color};'>{sign}{value}</span>
        </div>"""
    attr_html += "</div>"
    return attr_html


set_config(title="Detalhes do Item")

# Redireciona se não estiver logado
menu_with_redirect()

st.title("Detalhes do Item")

# Carregar todos os itens do banco
items = read_all_items()
if not items:
    st.warning("Nenhum item encontrado no banco de dados.")
    st.stop()

# Extrair nomes dos itens e categorias
item_names = []
categories = set()
categories_dict = {}

for item in items:
    item_names.append(item["item_name"])
    categories.add(item["category"])
    categories_dict[item["item_name"]] = item["category"]

# Ordenar as listas
item_names.sort()
categories = sorted(categories)

# Interface para selecionar o item
col1, col2 = st.columns([1, 2])

with col1:
    # Primeiro seleciona a categoria
    selected_category = st.selectbox(
        "Selecione a categoria:",
        ["Todas"] + categories
    )

# Filtrar itens pela categoria selecionada
if selected_category != "Todas":
    filtered_items = [name for name in item_names if categories_dict[name] == selected_category]
else:
    filtered_items = item_names

with col2:
    # Depois seleciona o item
    selected_item = st.selectbox(
        "Selecione o item:",
        filtered_items
    )

# Quando um item é selecionado, exibir seus detalhes
if selected_item:
    # Buscar informações detalhadas do item
    item_details = read_item(selected_item)
    
    if not item_details:
        st.error(f"Não foi possível encontrar detalhes para o item {selected_item}.")
        st.stop()
    
    # Extrair dados do JSON
    try:
        data_dict = json.loads(item_details["data_json"]) if isinstance(item_details["data_json"], str) else item_details["data_json"]
    except Exception as e:
        st.error(f"Erro ao interpretar os dados do item: {str(e)}")
        data_dict = {}
    
    # Layout de visualização do item - CARD PRINCIPAL
    st.markdown("---")
    
    # Criar um visual de "card" para o item
    card_col1, card_col2 = st.columns([1, 3])
    
    with card_col1:
        # Imagem com borda e sombra
        st.markdown(
            f"""
            <div style="
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                padding: 8px;
                background-color: rgb(38, 39, 48);
                width: fit-content;
                margin: 0 auto;
            ">
                <img src="{item_details["image_path"]}" width="128" 
                style="display: block; margin: 0 auto;">
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Link para a wiki
        item_link = f"https://tibia.fandom.com/wiki/{selected_item.replace(' ', '_')}"
        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 10px;">
                <a href="{item_link}" target="_blank" style="
                    display: inline-block;
                    padding: 5px 10px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-size: 0.8em;
                    margin-top: 10px;
                ">
                    Ver na Wiki
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with card_col2:
        # Nome e categoria com estilo
        st.markdown(f"<h2 style='margin-bottom: 0px; color: #1E3A8A;'>{selected_item}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #666; margin-top: 0px; font-style: italic;'>Categoria: {item_details['category']}</p>", unsafe_allow_html=True)
        
        # Extrair vocações
        vocations = extract_vocations(data_dict)
        if vocations:
            st.markdown("<p><b>Vocações:</b></p>", unsafe_allow_html=True)
            # Crie um indicador colorido para cada vocação
            voc_cols = st.columns(len(vocations))
            voc_colors = {
                "Knight": "#FF4500",  # Vermelho
                "Paladin": "#008000",  # Verde
                "Sorcerer": "#1E90FF",  # Azul
                "Druid": "#800080"  # Roxo
            }
            
            for i, voc in enumerate(vocations):
                with voc_cols[i]:
                    color = voc_colors.get(voc, "#888")
                    st.markdown(
                        f"""
                        <div style="
                            background-color: {color};
                            color: white;
                            border-radius: 5px;
                            padding: 5px;
                            text-align: center;
                            font-weight: bold;
                        ">
                            {voc}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        
        # Detalhes essenciais em cards pequenos na parte superior
        essential_stats = []
        
        # Level requerido
        if "Required Level" in data_dict:
            essential_stats.append(("Nível", data_dict["Required Level"], "🏆"))
        elif "General Properties" in data_dict and isinstance(data_dict["General Properties"], dict) and "Level" in data_dict["General Properties"]:
            essential_stats.append(("Nível", data_dict["General Properties"]["Level"], "🏆"))
        
        # Defesa/ataque
        if "Combat Properties" in data_dict and isinstance(data_dict["Combat Properties"], dict):
            combat = data_dict["Combat Properties"]
            if "Attack" in combat:
                essential_stats.append(("Ataque", combat["Attack"], "⚔️"))
            if "Defense" in combat:
                essential_stats.append(("Defesa", combat["Defense"], "🛡️"))
            if "Armor" in combat or "Arm" in combat:
                arm_value = combat.get("Armor", combat.get("Arm", ""))
                essential_stats.append(("Armadura", arm_value, "🧥"))
                
        # Peso
        if "Weight" in data_dict:
            essential_stats.append(("Peso", data_dict["Weight"], "⚖️"))
        elif "General Properties" in data_dict and isinstance(data_dict["General Properties"], dict) and "Weight" in data_dict["General Properties"]:
            essential_stats.append(("Peso", data_dict["General Properties"]["Weight"], "⚖️"))
        
        # Exibir stats essenciais como cards pequenos
        if essential_stats:
            stat_cols = st.columns(len(essential_stats))
            for i, (name, value, icon) in enumerate(essential_stats):
                with stat_cols[i]:
                    st.markdown(
                        f"""
                        <div style="
                            border: 1px solid #444;
                            border-radius: 8px;
                            padding: 8px;
                            text-align: center;
                            background-color: rgb(38, 39, 48);
                            color: white;
                        ">
                            <div style="font-size: 1.5em; margin-bottom: 5px;">{icon}</div>
                            <div style="font-weight: bold; color: #ddd;">{name}</div>
                            <div style="font-size: 1.2em; color: white;">{value}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
    
    # Mostrar abas para diferentes tipos de propriedades
    st.markdown("### Propriedades do Item")
    
    # Definir grupos de abas
    tab_groups = {
        "Combat Properties": "Combate",
        "General Properties": "Gerais",
        "Trade Properties": "Comércio",
        "Field Properties": "Campo",
        "Other Properties": "Outros"
    }
    
    # Verificar quais grupos existem nos dados
    existing_tabs = [tab for tab in tab_groups.keys() if tab in data_dict and isinstance(data_dict[tab], dict)]
    
    # Adicionar aba para atributos soltos
    if any(k for k in data_dict.keys() if k not in tab_groups.keys() and not isinstance(data_dict[k], dict)):
        existing_tabs.append("Atributos")
    
    # Criar abas
    if existing_tabs:
        tabs = st.tabs([tab_groups.get(tab, tab) for tab in existing_tabs])
        
        for i, tab_key in enumerate(existing_tabs):
            with tabs[i]:
                if tab_key == "Atributos":
                    # Exibir atributos soltos
                    atts = {}
                    for k, v in data_dict.items():
                        if k not in tab_groups.keys() and not isinstance(v, dict):
                            atts[k] = v
                    
                    if atts:
                        for key, value in atts.items():
                            if key in ["Vocations", "Name"]:  # Já exibidos em outro lugar
                                continue
                                
                            # Formatação de lista
                            if isinstance(value, list):
                                if len(value) > 0:
                                    st.markdown(f"**{key}:**")
                                    for item in value:
                                        st.markdown(f"- {item}")
                                    st.markdown("---")
                            # Tratamento para valores não listados acima
                            else:
                                # Tratamento especial para valores booleanos
                                if isinstance(value, bool):
                                    value_display = "Sim" if value else "Não"
                                    st.markdown(
                                        f"**{key}:** {value_display}", 
                                        unsafe_allow_html=True
                                    )
                                    st.markdown("---")
                                # Tratamento especial para resistências (dicionário)
                                elif isinstance(value, dict) and key.lower() in [
                                    "resistances", "resists", "resist", "protection"
                                ]:
                                    st.markdown(f"**{key}:**", unsafe_allow_html=True)
                                    resistance_html = render_resistances(value)
                                    st.markdown(
                                        resistance_html, 
                                        unsafe_allow_html=True
                                    )
                                    st.markdown("---")
                                # Tratamento especial para atributos mágicos
                                elif key.lower() == "attributes":
                                    st.markdown(f"**{key}:**", unsafe_allow_html=True)
                                    
                                    # Verificar se já é um dicionário
                                    if isinstance(value, dict):
                                        attr_html = render_attribute_dict(value)
                                        st.markdown(attr_html, unsafe_allow_html=True)
                                    else:
                                        # Processar atributos mágicos a partir de strings
                                        magic_attrs = process_magic_attributes(value)
                                        
                                        if magic_attrs:
                                            # Exibir atributos mágicos processados
                                            for attr_name, attr_value in magic_attrs.items():
                                                sign = "+" if attr_value > 0 else ""
                                                color = "green" if attr_value > 0 else "red"
                                                st.markdown(
                                                    f"- <span style='text-transform: capitalize;'>{attr_name}</span>: "
                                                    f"<span style='color: {color};'>{sign}{attr_value}</span>", 
                                                    unsafe_allow_html=True
                                                )
                                        else:
                                            # Exibir como lista normal
                                            if isinstance(value, list):
                                                for item in value:
                                                    st.markdown(f"- {item}")
                                            else:
                                                st.markdown(f"- {value}")
                                    st.markdown("---")
                                # Tratamento para valores normais
                                else:
                                    st.markdown(f"**{key}:** {value}")
                                    st.markdown("---")
                else:
                    # Exibir propriedades do grupo
                    group_data = data_dict[tab_key]
                    
                    # Criar colunas para exibir os dados em formato mais compacto
                    properties = list(group_data.items())
                    
                    # Definir número de propriedades por linha
                    props_per_row = 2  # Ajuste conforme necessário
                    
                    for i in range(0, len(properties), props_per_row):
                        cols = st.columns(props_per_row)
                        for j in range(props_per_row):
                            idx = i + j
                            if idx < len(properties):
                                key, value = properties[idx]
                                with cols[j]:
                                    # Tratamento especial para valores booleanos
                                    if isinstance(value, bool):
                                        value_display = "Sim" if value else "Não"
                                        st.markdown(
                                            f"**{key}:** {value_display}", 
                                            unsafe_allow_html=True
                                        )
                                    # Tratamento especial para resistências (dicionário)
                                    elif isinstance(value, dict) and key.lower() in [
                                        "resistances", "resists", "resist", "protection"
                                    ]:
                                        st.markdown(f"**{key}:**", unsafe_allow_html=True)
                                        resistance_html = render_resistances(value)
                                        st.markdown(
                                            resistance_html, 
                                            unsafe_allow_html=True
                                        )
                                    # Tratamento especial para atributos mágicos
                                    elif key.lower() == "attributes":
                                        st.markdown(f"**{key}:**", unsafe_allow_html=True)
                                        
                                        # Verificar se já é um dicionário
                                        if isinstance(value, dict):
                                            attr_html = render_attribute_dict(value)
                                            st.markdown(attr_html, unsafe_allow_html=True)
                                        else:
                                            # Processar atributos mágicos a partir de strings
                                            magic_attrs = process_magic_attributes(value)
                                            
                                            if magic_attrs:
                                                # Exibir atributos mágicos processados
                                                for attr_name, attr_value in magic_attrs.items():
                                                    sign = "+" if attr_value > 0 else ""
                                                    color = "green" if attr_value > 0 else "red"
                                                    st.markdown(
                                                        f"- <span style='text-transform: capitalize;'>{attr_name}</span>: "
                                                        f"<span style='color: {color};'>{sign}{attr_value}</span>", 
                                                        unsafe_allow_html=True
                                                    )
                                            else:
                                                # Exibir como lista normal
                                                if isinstance(value, list):
                                                    for item in value:
                                                        st.markdown(f"- {item}")
                                                else:
                                                    st.markdown(f"- {value}")
                                    # Tratamento especial para listas
                                    elif isinstance(value, list):
                                        st.markdown(f"**{key}:**")
                                        for item in value:
                                            st.markdown(f"- {item}")
                                    else:
                                        st.markdown(f"**{key}:** {value}")
                                    st.markdown("---")
    else:
        st.info("Não foram encontradas propriedades detalhadas para este item.")
    
    # Botão de scrape e dados brutos
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f'🔄 Atualizar {selected_item}', use_container_width=True):
            try:
                from services.custom_scraping import force_update_single_item
                with st.spinner(f"Atualizando {selected_item}..."):
                    scraped_data = force_update_single_item(selected_item)
                st.success(f'Item {selected_item} atualizado com sucesso!')
                st.rerun()
            except Exception as e:
                st.error(f'Erro ao atualizar item: {str(e)}')
    
    with col2:
        with st.expander("Ver dados brutos"):
            st.json(data_dict) 