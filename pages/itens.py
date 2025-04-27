import streamlit as st
from utils.menu import menu_with_redirect
from utils.favicon import set_config
import pandas as pd

# Importa as funções do nosso arquivo de banco
from mydb import read_all_items, delete_items_by_category
from services.scraping import scrap, scrap_missing_items

set_config(title="Itens")

# Exibe o menu de navegação
menu_with_redirect()

st.title("Itens")

# ----- EXIBIR DADOS DO BANCO PRIMEIRO
st.header("Dados do Banco")

# Link para a página de detalhes
st.info("Para visualizar detalhes completos de um item, acesse a página "
        "[Detalhes do Item](/Detalhes_Item)")

# Exemplo: ler tudo e agrupar por categoria
all_items = read_all_items()
if not all_items:
    st.warning("Sem itens no banco! Use os controles de atualização abaixo para adicionar itens.")
else:
    # Converter para DataFrame
    df = pd.DataFrame(all_items)
    df = df[['image_path', 'item_name', 'category', 'data_json']]

    # Mostra estatísticas
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de itens", f"{len(df)}")
    
    # Agrupar por categoria
    category_counts = df['category'].value_counts().reset_index()
    category_counts.columns = ['Categoria', 'Quantidade']
    
    # Exibir como gráfico de barras
    st.bar_chart(category_counts, x='Categoria', y='Quantidade')
    
    with st.expander("Ver detalhes de contagem por categoria", expanded=False):
        st.dataframe(category_counts)
    
    # Exibe o DataFrame original em um expander
    with st.expander("Ver todos os itens registrados", expanded=False):
        st.dataframe(
            df,
            column_config={
                "image_path": st.column_config.ImageColumn(
                    "Imagem",
                    help="Sprite do item"
                ),
                "item_name": "Item Name",
                "category": "Category",
                "data_json": "Data",
            },
            hide_index=True,
        )

# Adicionar opções de atualização por categoria dentro de um expander
with st.expander("🔄 Gerenciar Banco de Dados de Itens", expanded=False):
    st.header("Gerenciar Categorias de Itens")
    
    # Lista de todas as categorias disponíveis
    categories = [
        "Helmets", "Armors", "Legs", "Boots", "Shields", "Spellbooks",
        "Amulets_and_Necklaces", "Rings", "Quivers", "Wands", "Rods",
        "Axes", "Clubs", "Swords", "Fist_Fighting_Weapons", "Throwing_Weapons"
    ]
    
    # Botões para operações com todas as categorias
    st.subheader("Operações em Massa")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Atualizar Todas", type="primary", use_container_width=True):
            with st.spinner("Atualizando todas as categorias..."):
                scrap()
            st.success("Todas as categorias foram atualizadas com sucesso!")
            st.rerun()
    with col2:
        if st.button("Atualizar Somente Faltantes", type="primary", use_container_width=True):
            with st.spinner("Atualizando apenas itens faltantes..."):
                scrap_missing_items()
            st.success("Itens faltantes foram atualizados!")
            st.rerun()
    with col3:
        if st.button("Deletar Todas", type="secondary", use_container_width=True):
            # Confirmação antes de deletar
            if st.checkbox("Confirmar deleção?", key="confirm_all_delete"):
                with st.spinner("Deletando todos os itens do banco de dados..."):
                    total_deleted = 0
                    for category in categories:
                        deleted = delete_items_by_category(category)
                        total_deleted += deleted
                if total_deleted > 0:
                    st.success(f"{total_deleted} itens foram removidos.")
                else:
                    st.info("Não foram encontrados itens para remover.")
                st.rerun()
    
    # Interface para gerenciar categorias individuais
    st.subheader("Gerenciar Categorias Individuais")
    
    # Usar uma tabela para exibir as categorias de forma mais organizada
    st.write("Selecione uma categoria para atualizar ou deletar:")
    
    # Criar uma tabela com colunas de largura equilibrada
    cols = st.columns([3, 1, 1])
    with cols[0]:
        st.markdown("**Categoria**")
    with cols[1]:
        st.markdown("**Atualizar**")
    with cols[2]:
        st.markdown("**Deletar**")
    
    # Exibir cada categoria em formato de tabela
    for category in categories:
        display_name = category.replace("_", " ")
        cols = st.columns([3, 1, 1])
        
        # Nome da categoria
        with cols[0]:
            st.write(display_name)
        
        # Botão de atualizar
        with cols[1]:
            update_btn = st.button("🔄", key=f"update_{category}")
        
        # Botão de deletar
        with cols[2]:
            delete_btn = st.button("🗑️", key=f"delete_{category}")
        
        # Processar ações dos botões
        if update_btn:
            with st.spinner(f"Atualizando {display_name}..."):
                scrap(category)
            st.success(f"Categoria {display_name} atualizada com sucesso!")
            st.rerun()
        
        if delete_btn:
            with st.spinner(f"Deletando itens da categoria {display_name}..."):
                deleted = delete_items_by_category(category)
            st.success(f"{deleted} itens da categoria {display_name} foram deletados.")
            st.rerun()

if all_items:
    # Seção de análise avançada com abas em vez de expanders aninhados
    st.header("📊 Análise Avançada de Propriedades")
    
    # Converter strings JSON para dicionários
    import json
    df['data_dict'] = df['data_json'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
    
    # Função para extrair todas as propriedades de combate de forma recursiva
    def extract_combat_properties(data_dict):
        combat_props = {}
        if not isinstance(data_dict, dict):
            return combat_props
            
        # Verificar se existe Combat Properties no nível principal
        if 'Combat Properties' in data_dict and isinstance(data_dict['Combat Properties'], dict):
            return data_dict['Combat Properties']
            
        # Procurar em todas as seções
        for key, value in data_dict.items():
            if isinstance(value, dict):
                if key == 'Combat Properties':
                    return value
                # Procurar recursivamente
                sub_props = extract_combat_properties(value)
                if sub_props:
                    return sub_props
                    
        return combat_props
    
    # Função para analisar estrutura de propriedades e criar um mapa completo de todos os campos
    def analyze_property_structure(items_df):
        # Dicionário para armazenar todos os campos e subcampos encontrados
        all_fields = {}
        
        # Para cada item, extrair e analisar suas propriedades
        for idx, row in items_df.iterrows():
            item_data = row['data_dict']
            category = row['category']
            item_name = row['item_name']
            
            # Função recursiva para explorar campos e subcampos
            def explore_fields(data, path="", parent_key=""):
                if not isinstance(data, dict):
                    # Se não for um dicionário, registra o valor escalar
                    full_path = f"{path}.{parent_key}" if path else parent_key
                    if full_path not in all_fields:
                        all_fields[full_path] = {
                            'type': type(data).__name__,
                            'examples': [],
                            'categories': set(),
                            'items': set()
                        }
                    
                    # Limitar o número de exemplos para não sobrecarregar
                    if len(all_fields[full_path]['examples']) < 5:
                        all_fields[full_path]['examples'].append(str(data))
                    
                    all_fields[full_path]['categories'].add(category)
                    all_fields[full_path]['items'].add(item_name)
                    return
                
                # Se for um dicionário, explorar recursivamente
                for key, value in data.items():
                    new_path = f"{path}.{key}" if path else key
                    
                    # Registrar o próprio campo como existente
                    if new_path not in all_fields:
                        all_fields[new_path] = {
                            'type': 'dict' if isinstance(value, dict) else type(value).__name__,
                            'examples': [],
                            'categories': set(),
                            'items': set()
                        }
                    
                    all_fields[new_path]['categories'].add(category)
                    all_fields[new_path]['items'].add(item_name)
                    
                    # Se for um valor não-dicionário, registrar exemplo
                    if not isinstance(value, dict):
                        if len(all_fields[new_path]['examples']) < 5:
                            all_fields[new_path]['examples'].append(str(value))
                    
                    # Explorar recursivamente se for dicionário
                    if isinstance(value, dict):
                        explore_fields(value, new_path, "")
                    elif isinstance(value, list):
                        # Para listas, registrar como tipo lista
                        all_fields[new_path]['type'] = 'list'
                        if value and len(all_fields[new_path]['examples']) < 5:
                            all_fields[new_path]['examples'].append(str(value))
            
            # Iniciar exploração dos campos
            explore_fields(item_data)
        
        # Converter para formato mais adequado para exibição
        result = []
        for field_path, info in all_fields.items():
            result.append({
                'Campo': field_path,
                'Tipo': info['type'],
                'Exemplos': ', '.join(info['examples']),
                'Categorias': ', '.join(info['categories']),
                'Num_Items': len(info['items']),
                'Num_Categorias': len(info['categories'])
            })
        
        # Ordenar por frequência (campos mais comuns primeiro)
        return sorted(result, key=lambda x: x['Num_Items'], reverse=True)
    
    # Extrair todas as propriedades de combate de todos os itens
    all_props = {}
    category_props = {}
    
    # Para cada item, extrair suas propriedades de combate
    for idx, row in df.iterrows():
        item_data = row['data_dict']
        category = row['category']
        
        # Inicializar dicionário para a categoria se não existir
        if category not in category_props:
            category_props[category] = {}
            
        # Extrair propriedades de combate
        combat_props = extract_combat_properties(item_data)
        
        # Registrar todas as propriedades encontradas
        for prop_name in combat_props.keys():
            # Atualizar contagem global
            if prop_name not in all_props:
                all_props[prop_name] = 0
            all_props[prop_name] += 1
            
            # Atualizar contagem por categoria
            if prop_name not in category_props[category]:
                category_props[category][prop_name] = 0
            category_props[category][prop_name] += 1
    
    # Criar DataFrame com todas as propriedades e sua contagem
    props_df = pd.DataFrame({
        'Propriedade': list(all_props.keys()),
        'Contagem': list(all_props.values())
    })
    
    # Ordenar por frequência (mais comum primeiro)
    props_df = props_df.sort_values('Contagem', ascending=False).reset_index(drop=True)
    
    # Criar abas para as diferentes visualizações de análise
    tab1, tab2, tab3, tab4 = st.tabs([
        "Filtrar por Propriedade", 
        "Propriedades Globais", 
        "Propriedades por Categoria",
        "Mapa de Campos"
    ])
    
    with tab1:
        st.subheader("Filtrar Itens por Propriedade")
        
        # Criar lista de propriedades ordenadas por frequência
        properties_list = props_df['Propriedade'].tolist()
        
        # Dropdown para selecionar a propriedade
        selected_property = st.selectbox(
            "Selecione uma propriedade de combate:",
            options=properties_list,
            index=0 if properties_list else None
        )
        
        # Mostrar itens que têm a propriedade selecionada
        if selected_property:
            # Filtrar itens que têm a propriedade selecionada
            items_with_property = []
            
            for idx, row in df.iterrows():
                combat_props = extract_combat_properties(row['data_dict'])
                
                if selected_property in combat_props:
                    items_with_property.append({
                        'Item': row['item_name'],
                        'Categoria': row['category'],
                        'Imagem': row['image_path'],
                        'Valor': combat_props[selected_property],
                        'Wiki': f"https://tibia.fandom.com/wiki/{row['item_name'].replace(' ', '_')}"
                    })
            
            # Converter para DataFrame
            if items_with_property:
                items_df = pd.DataFrame(items_with_property)
                
                # Exibir quantidade
                st.write(f"{len(items_df)} itens encontrados com a propriedade '{selected_property}'")
                
                # Exibir tabela
                st.dataframe(
                    items_df,
                    column_config={
                        "Imagem": st.column_config.ImageColumn(
                            "Imagem",
                            help="Sprite do item"
                        ),
                        "Item": "Nome do Item",
                        "Categoria": "Categoria",
                        "Valor": f"Valor de {selected_property}",
                        "Wiki": st.column_config.LinkColumn(
                            "Link Wiki",
                            help="Link para a página do item na Wiki do Tibia"
                        )
                    },
                    hide_index=True,
                )
            else:
                st.info(f"Nenhum item encontrado com a propriedade '{selected_property}'")
    
    with tab2:
        st.subheader("Propriedades de Combate Encontradas em Todos os Itens")
        st.dataframe(props_df)
    
    with tab3:
        st.subheader("Propriedades de Combate por Categoria")
        # Criar tabs para cada categoria
        category_tabs = st.tabs(list(category_props.keys()))
        
        # Para cada categoria, exibir suas propriedades
        for i, category in enumerate(category_props.keys()):
            with category_tabs[i]:
                # Converter para DataFrame
                cat_props = pd.DataFrame({
                    'Propriedade': list(category_props[category].keys()),
                    'Contagem': list(category_props[category].values())
                })
                
                # Ordenar por frequência
                cat_props = cat_props.sort_values('Contagem', ascending=False).reset_index(drop=True)
                
                # Mostrar número de itens nesta categoria
                total_items = category_counts[category_counts['Categoria'] == category]['Quantidade'].values[0]
                st.write(f"Total de itens nesta categoria: {total_items}")
                
                # Mostrar tabela
                st.dataframe(cat_props)
                
                # Mostrar percentual de ocorrência
                if not cat_props.empty:
                    cat_props['Percentual'] = (cat_props['Contagem'] / total_items * 100).round(2).astype(str) + '%'
                    st.write("Percentual de ocorrência em itens desta categoria:")
                    st.dataframe(cat_props[['Propriedade', 'Percentual']])
    
    with tab4:
        st.subheader("Mapa Completo de Todos os Campos")
        st.write("Esta tabela mostra todos os campos encontrados em todos os itens, incluindo subcampos e propriedades aninhadas.")
        
        # Executar análise detalhada
        all_fields_df = pd.DataFrame(analyze_property_structure(df))
        
        # Exibir tabela completa
        st.dataframe(all_fields_df, use_container_width=True)
        
        # Adicionar filtros para campos específicos
        st.write("### Filtrar por Tipo de Campo")
        field_types = sorted(all_fields_df['Tipo'].unique())
        selected_type = st.selectbox("Selecione um tipo de campo:", options=field_types)
        
        # Filtrar e mostrar
        if selected_type:
            filtered_fields = all_fields_df[all_fields_df['Tipo'] == selected_type]
            st.dataframe(filtered_fields, use_container_width=True)

st.write("TODO: separar adequadamente as informações da Data para que possam ser utilizadas nos cálculos")