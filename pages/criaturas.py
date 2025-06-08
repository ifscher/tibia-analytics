import streamlit as st
from utils.menu import menu_with_redirect
from utils.favicon import set_config
from utils.config import is_development
from mydb import read_all_creatures, read_creature, create_table
from services.creature_scraping import scrap_all_creatures_from_subcategory, update_creature_details
import json
import pandas as pd
import os
import sqlite3

# Mapeamento de categorias de criaturas e suas sub-categorias com links na wiki
CREATURE_CATEGORIES = {
    "Amphibians": {
        "link": "https://tibia.fandom.com/wiki/Creatures#Amphibians",
        "subcategories": {
            "Deeplings": "https://tibia.fandom.com/wiki/Deeplings",
            "Frogs": "https://tibia.fandom.com/wiki/Frogs",
            "Quara": "https://tibia.fandom.com/wiki/Quara",
            "Salamanders": "https://tibia.fandom.com/wiki/Salamanders"
        }
    },
    "Demons": {
        "link": "https://tibia.fandom.com/wiki/Creatures#Demons",
        "subcategories": {
            "Arak Demons": "https://tibia.fandom.com/wiki/Arak_Demons",
            "Archdemons": "https://tibia.fandom.com/wiki/Archdemons",
            "Asuri": "https://tibia.fandom.com/wiki/Asuri",
            "Demon Lords": "https://tibia.fandom.com/wiki/Demon_Lords",
            "Demons": "https://tibia.fandom.com/wiki/Demons",
            "Dreamhaunters": "https://tibia.fandom.com/wiki/Dreamhaunters",
            "Hands": "https://tibia.fandom.com/wiki/Hands",
            "Imps": "https://tibia.fandom.com/wiki/Imps",
            "The Ruthless Seven": "https://tibia.fandom.com/wiki/The_Ruthless_Seven",
            "The Ruthless Seven Minions": "https://tibia.fandom.com/wiki/The_Ruthless_Seven_Minions",
            "Triangle of Terror": "https://tibia.fandom.com/wiki/Triangle_of_Terror",
            "Pit Demons": "https://tibia.fandom.com/wiki/Pit_Demons",
            "Possessed Objects": "https://tibia.fandom.com/wiki/Possessed_Objects"
        }
    },
    "Elementals": {
        "link": "https://tibia.fandom.com/wiki/Creatures#Elementals",
        "subcategories": {
            "Bio-Elementals": "https://tibia.fandom.com/wiki/Bio-Elementals",
            "Blobs": "https://tibia.fandom.com/wiki/Blobs",
            "Cryo-Elementals": "https://tibia.fandom.com/wiki/Cryo-Elementals",
            "Electro-Elementals": "https://tibia.fandom.com/wiki/Electro-Elementals",
            "Elemental Lords": "https://tibia.fandom.com/wiki/Elemental_Lords",
            "Geo-Elementals": "https://tibia.fandom.com/wiki/Geo-Elementals",
            "Hydro-Elementals": "https://tibia.fandom.com/wiki/Hydro-Elementals",
            "Magma-Elementals": "https://tibia.fandom.com/wiki/Magma-Elementals",
            "Pyro-Elementals": "https://tibia.fandom.com/wiki/Pyro-Elementals"
        }
    },
    "Humanoids": {
        "link": "https://tibia.fandom.com/wiki/Creatures#Humanoids",
        "subcategories": {
            "Astral Shapers": "https://tibia.fandom.com/wiki/Astral_Shapers",
            "Chakoyas": "https://tibia.fandom.com/wiki/Chakoyas",
            "Corym": "https://tibia.fandom.com/wiki/Corym",
            "Djinn": "https://tibia.fandom.com/wiki/Djinn",
            "Dwarves": "https://tibia.fandom.com/wiki/Dwarves",
            "Dworcs": "https://tibia.fandom.com/wiki/Dworcs",
            "Elves": "https://tibia.fandom.com/wiki/Elves",
            "Fae": "https://tibia.fandom.com/wiki/Fae",
            "Fungi": "https://tibia.fandom.com/wiki/Fungi",
            "Giants": "https://tibia.fandom.com/wiki/Giants",
            "Gnomes": "https://tibia.fandom.com/wiki/Gnomes",
            "Goblins": "https://tibia.fandom.com/wiki/Goblins",
            "Minotaurs": "https://tibia.fandom.com/wiki/Minotaurs",
            "Orclopses": "https://tibia.fandom.com/wiki/Orclopses",
            "Orcs": "https://tibia.fandom.com/wiki/Orcs",
            "Pirats": "https://tibia.fandom.com/wiki/Pirats",
            "Trolls": "https://tibia.fandom.com/wiki/Trolls"
        }
    },
    "Humans": {
        "link": "https://tibia.fandom.com/wiki/Creatures#Humans",
        "subcategories": {
            "Amazons": "https://tibia.fandom.com/wiki/Amazons",
            "Barbarians": "https://tibia.fandom.com/wiki/Barbarians",
            "Monks": "https://tibia.fandom.com/wiki/Monks",
            "Necromancers": "https://tibia.fandom.com/wiki/Necromancers",
            "Outlaws": "https://tibia.fandom.com/wiki/Outlaws",
            "Pirates": "https://tibia.fandom.com/wiki/Pirates",
            "Sorcerers": "https://tibia.fandom.com/wiki/Sorcerers",
            "Voodoo Cultists": "https://tibia.fandom.com/wiki/Voodoo_Cultists",
            "Lycanthropes": "https://tibia.fandom.com/wiki/Lycanthropes",
            "Fafnar Cultists": "https://tibia.fandom.com/wiki/Fafnar_Cultists"
        }
    },
    "Invertebrates": {
        "link": "https://tibia.fandom.com/wiki/Creatures#Invertebrates",
        "subcategories": {
            "Annelids": "https://tibia.fandom.com/wiki/Annelids",
            "Arachnids": "https://tibia.fandom.com/wiki/Arachnids",
            "Bonelords": "https://tibia.fandom.com/wiki/Bonelords",
            "Cnidarians": "https://tibia.fandom.com/wiki/Cnidarians",
            "Crustaceans": "https://tibia.fandom.com/wiki/Crustaceans",
            "Hive Born": "https://tibia.fandom.com/wiki/Hive_Born",
            "Insects": "https://tibia.fandom.com/wiki/Insects",
            "Mollusks": "https://tibia.fandom.com/wiki/Mollusks",
            "Myriapods": "https://tibia.fandom.com/wiki/Myriapods"
        }
    },
    "Mammals": {
        "link": "https://tibia.fandom.com/wiki/Creatures#Mammals",
        "subcategories": {
            "Apes": "https://tibia.fandom.com/wiki/Apes",
            "Bats": "https://tibia.fandom.com/wiki/Bats",
            "Bears": "https://tibia.fandom.com/wiki/Bears",
            "Canines": "https://tibia.fandom.com/wiki/Canines",
            "Felines": "https://tibia.fandom.com/wiki/Felines",
            "Glires": "https://tibia.fandom.com/wiki/Glires",
            "Hyaenids": "https://tibia.fandom.com/wiki/Hyaenids",
            "Mustelids": "https://tibia.fandom.com/wiki/Mustelids",
            "Mutated Mammals": "https://tibia.fandom.com/wiki/Mutated_Mammals",
            "Ungulates": "https://tibia.fandom.com/wiki/Ungulates"
        }
    },
    "Misc": {
        "link": "https://tibia.fandom.com/wiki/Creatures#Misc",
        "subcategories": {
            "Birds": "https://tibia.fandom.com/wiki/Birds",
            "Fishes": "https://tibia.fandom.com/wiki/Fishes",
            "Machines": "https://tibia.fandom.com/wiki/Machines",
            "Anuma": "https://tibia.fandom.com/wiki/Anuma",
            "Hybrids": "https://tibia.fandom.com/wiki/Hybrids"
        }
    },
    "Reptiles": {
        "link": "https://tibia.fandom.com/wiki/Creatures#Reptiles",
        "subcategories": {
            "Crocodilians": "https://tibia.fandom.com/wiki/Crocodilians",
            "Dragons": "https://tibia.fandom.com/wiki/Dragons",
            "Draken": "https://tibia.fandom.com/wiki/Draken",
            "Hydras": "https://tibia.fandom.com/wiki/Hydras",
            "Lizards": "https://tibia.fandom.com/wiki/Lizards",
            "Serpents": "https://tibia.fandom.com/wiki/Serpents",
            "Tortoises": "https://tibia.fandom.com/wiki/Tortoises",
            "Varanidae": "https://tibia.fandom.com/wiki/Varanidae",
            "Wyrms": "https://tibia.fandom.com/wiki/Wyrms",
            "Wyverns": "https://tibia.fandom.com/wiki/Wyverns"
        }
    },
    "Special Creatures": {
        "link": "https://tibia.fandom.com/wiki/Creatures#Special_Creatures",
        "subcategories": {
            "Arena Bosses": "https://tibia.fandom.com/wiki/Arena_Bosses",
            "Bosses": "https://tibia.fandom.com/wiki/Bosses",
            "Deprecated Creatures": "https://tibia.fandom.com/wiki/Deprecated_Creatures",
            "Event Creatures": "https://tibia.fandom.com/wiki/Event_Creatures",
            "Shapeshifters": "https://tibia.fandom.com/wiki/Shapeshifters",
            "Traps": "https://tibia.fandom.com/wiki/Traps"
        }
    },
    "The Undead": {
        "link": "https://tibia.fandom.com/wiki/Creatures#The_Undead",
        "subcategories": {
            "Ghosts": "https://tibia.fandom.com/wiki/Ghosts",
            "Pharaohs": "https://tibia.fandom.com/wiki/Pharaohs",
            "Skeletons": "https://tibia.fandom.com/wiki/Skeletons",
            "Undead Humanoids": "https://tibia.fandom.com/wiki/Undead_Humanoids",
            "Vampires": "https://tibia.fandom.com/wiki/Vampires"
        }
    }
}

set_config(title="Criaturas", layout="wide")

# Exibe o menu de navegação
menu_with_redirect()

# Verifica se está em modo desenvolvimento
if not is_development():
    st.error("Esta página só está disponível em modo desenvolvimento.")
    st.stop()

st.title("Criaturas")

# Função para formatar o nome da seção
def format_section_name(section_name):
    if not section_name:
        return "Geral"
    return section_name

# Função para verificar e corrigir caminhos de imagem
def verify_image_path(img_path):
    if not img_path:
        return ""
    
    # Se for uma data URL, retornar como está
    if img_path.startswith('data:'):
        return img_path
    
    # Se for um caminho local, verificar se existe
    if os.path.exists(img_path):
        return img_path
    
    # Se o caminho não existir mas parece ser um caminho para utils/creature_img
    if 'utils/creature_img' in img_path:
        # Tentar caminho alternativo na nova estrutura
        new_path = img_path.replace('utils/creature_img', 'utils/img/creatures')
        if os.path.exists(new_path):
            return new_path
    
    # Verificar se é uma URL absoluta
    if img_path.startswith(('http://', 'https://')):
        return img_path
    
    # Retornar vazio se não for possível resolver
    return ""

# Inicializa o estado da sessão para a mensagem de status
if 'scraping_status' not in st.session_state:
    st.session_state.scraping_status = ""

# Função para atualizar o status do scraping
def update_scraping_status(status):
    st.session_state.scraping_status = status
    st.session_state.rerun_requested = True

# Função para executar o scraping de uma subcategoria
def scrape_subcategory(category, subcategory, url):
    with st.spinner(f'Realizando scraping de {subcategory}...'):
        results = scrap_all_creatures_from_subcategory(
            category, subcategory, url, update_scraping_status
        )
        st.success(f'Scraping concluído! Encontradas {results} criaturas em {subcategory}.')
        st.session_state.rerun_page = True

# Tabs para Visualização e Scraping
tab1, tab2 = st.tabs(["Visualização de Criaturas", "Gerenciamento de Scraping"])

with tab1:
    st.header("Criaturas no Banco de Dados")
    
    # Inicializar estados de sessão para visualização de detalhes
    if 'selected_creature' not in st.session_state:
        st.session_state.selected_creature = None
    
    # Adicionar opção de visualização
    view_option = st.radio(
        "Modo de visualização:",
        ["Tabela", "Grid de imagens"],
        horizontal=True
    )
    
    # Garantir que a tabela existe antes de tentar lê-la
    create_table()
    
    # Buscar todas as criaturas do banco
    creatures = read_all_creatures()
    
    # Debug: Exibir informações sobre as primeiras criaturas para diagnóstico
    st.write("### Debug: Informações de imagens")
    
    # Buscar todas as criaturas do banco para debug
    all_creatures = read_all_creatures()
    
    if all_creatures:
        st.write(f"Total de criaturas no banco: {len(all_creatures)}")
        
        # Exibir as primeiras 5 criaturas com suas imagens
        st.write("### Exibindo primeiras 5 criaturas do banco:")
        
        for i, creature in enumerate(all_creatures[:5]):
            creature_name = creature.get('creature_name', 'Desconhecido')
            img_path = creature.get('image_path', '')
            
            st.write(f"**Criatura {i+1}:** {creature_name}")
            st.write(f"Caminho da imagem: `{img_path}`")
            
            # Verificar e exibir a imagem
            if img_path:
                # Verificar o tipo de imagem
                if img_path.startswith('data:'):
                    st.write(f"Tipo: Data URL (tamanho: {len(img_path)} caracteres)")
                    try:
                        st.image(img_path, width=100, caption=f"Imagem de {creature_name} (data URL)")
                    except Exception as e:
                        st.error(f"Erro ao exibir imagem data URL: {str(e)}")
                else:
                    # Caminho de arquivo local
                    st.write(f"Tipo: Caminho de arquivo local")
                    if os.path.exists(img_path):
                        st.write(f"Arquivo existe: Sim - Tamanho: {os.path.getsize(img_path)} bytes")
                        try:
                            with open(img_path, "rb") as f:
                                image_bytes = f.read()
                            st.image(image_bytes, width=100, caption=f"Imagem de {creature_name} (arquivo local)")
                        except Exception as e:
                            st.error(f"Erro ao ler arquivo de imagem: {str(e)}")
                    else:
                        st.error(f"Arquivo não existe: {img_path}")
            else:
                st.write("Sem imagem")
            
            st.markdown("---")
    else:
        st.warning("Nenhuma criatura encontrada no banco para debug.")
    
    # Exibir detalhes sobre a estrutura da tabela para debug
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Estrutura da tabela no banco:")
        conn = sqlite3.connect("mydb.db")
        c = conn.cursor()
        c.execute("PRAGMA table_info(criaturas)")
        columns = c.fetchall()
        conn.close()
        
        # Mostrar estrutura da tabela
        st.table(pd.DataFrame(columns, columns=["cid", "name", "type", "notnull", "dflt_value", "pk"]))
    
    with col2:
        # Verificar pasta de imagens
        creature_img_folder = "utils/creature_img"
        if os.path.exists(creature_img_folder):
            img_files = os.listdir(creature_img_folder)
            st.write(f"### Arquivos na pasta de imagens ({len(img_files)}):")
            if img_files:
                st.write(", ".join(img_files[:10]) + ("..." if len(img_files) > 10 else ""))
            else:
                st.write("Pasta vazia")
        else:
            st.error(f"Pasta de imagens não existe: {creature_img_folder}")
    
    # Mostrar configuração da tabela
    st.write("### Comparação de configuração da tabela:")
    
    code_itens = """
    # Código da página de itens:
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
    """
    
    code_criaturas = """
    # Código atual da página de criaturas:
    st.dataframe(
        df,
        hide_index=True,
        column_config={
            "image_path": st.column_config.ImageColumn(
                "Imagem",
                help="Imagem da criatura"
            )
        },
        use_container_width=True,
        key=table_key,
        column_order=["image_path", "Nome", "Categoria", "Subcategoria", "Divisão"]
    )
    """
    
    col1, col2 = st.columns(2)
    with col1:
        st.code(code_itens, language="python")
    with col2:
        st.code(code_criaturas, language="python")
    
    # Criar DataFrame para exibição
    if creatures:
        # Preparar dados para o DataFrame
        df_data = []
        for creature in creatures:
            creature_name = creature.get('creature_name', 'Desconhecido')
            category = creature.get('category', 'Desconhecida')
            subcategory = creature.get('subcategory', 'Desconhecida')
            image_path = creature.get('image_path', '')
            
            # Verificar e possivelmente corrigir caminho da imagem
            image_path = verify_image_path(image_path)
            
            # Extrair a seção da criatura dos dados JSON
            data_json = creature.get('data_json', '{}')
            try:
                data_dict = json.loads(data_json) if isinstance(data_json, str) else data_json
                section = data_dict.get('Section', '')
            except json.JSONDecodeError:
                section = ''
            
            df_data.append({
                'Nome': creature_name,
                'Categoria': category,
                'Subcategoria': subcategory,
                'Divisão': format_section_name(section),
                'image_path': image_path  # Usar image_path, mesmo nome usado na página de itens
            })
        
        # Criar DataFrame
        df = pd.DataFrame(df_data)
        
        # Exibir dados processados para a tabela
        if len(df_data) > 0:
            st.write("### Dados processados para a tabela (primeiras 3 linhas):")
            df_sample = pd.DataFrame(df_data[:3])
            st.dataframe(df_sample)
            
            # Exibir a estrutura do DataFrame
            st.write("### Estrutura do DataFrame:")
            st.write(f"Colunas: {df.columns.tolist()}")
            st.write(f"Tipos de dados:")
            st.write(df.dtypes)
            
            # Debug de imagens para as primeiras criaturas
            st.write("### Debug de imagens para as primeiras criaturas")
            for i, creature in enumerate(creatures[:3]):  # Mostrar apenas as 3 primeiras para não poluir
                img_path = creature.get('image_path', '')
                st.write(f"Criatura: {creature.get('creature_name')} | Caminho da imagem: {img_path}")
                if img_path:
                    st.write(f"Tipo: {'Data URL' if img_path.startswith('data:') else 'Caminho de arquivo'}")
                    if os.path.exists(img_path):
                        st.write(f"Arquivo existe: Sim - Tamanho: {os.path.getsize(img_path)} bytes")
                        # Mostrar imagem para debug
                        if not img_path.startswith('data:'):
                            with open(img_path, "rb") as f:
                                image_bytes = f.read()
                            st.image(image_bytes, width=50, caption=f"Imagem de {creature.get('creature_name')}")
                    else:
                        st.write(f"Arquivo existe: Não")
        
        # Adicionar filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            categories = ['Todas'] + sorted(df['Categoria'].unique().tolist())
            selected_category = st.selectbox('Filtrar por Categoria:', categories)
        
        with col2:
            if selected_category != 'Todas':
                subcategories = ['Todas'] + sorted(df[df['Categoria'] == selected_category]['Subcategoria'].unique().tolist())
            else:
                subcategories = ['Todas'] + sorted(df['Subcategoria'].unique().tolist())
            selected_subcategory = st.selectbox('Filtrar por Subcategoria:', subcategories)
        
        with col3:
            if selected_subcategory != 'Todas':
                df_filtered = df[df['Subcategoria'] == selected_subcategory]
            elif selected_category != 'Todas':
                df_filtered = df[df['Categoria'] == selected_category]
            else:
                df_filtered = df
            
            sections = ['Todas'] + sorted(df_filtered['Divisão'].unique().tolist())
            selected_section = st.selectbox('Filtrar por Divisão:', sections)
        
        # Aplicar filtros
        if selected_category != 'Todas':
            df = df[df['Categoria'] == selected_category]
        
        if selected_subcategory != 'Todas':
            df = df[df['Subcategoria'] == selected_subcategory]
        
        if selected_section != 'Todas':
            df = df[df['Divisão'] == selected_section]
        
        # Exibir tabela estilizada
        st.write(f"Total de criaturas: {len(df)}")
        
        if view_option == "Tabela":
            # Exibir tabela com st.dataframe em vez de st.data_editor
            # Criar uma chave única que considere os filtros atuais
            table_key = f"creature_table_{selected_category}_{selected_subcategory}_{selected_section}"
            
            # Verificar para debug se a coluna image_path existe
            st.write(f"Colunas disponíveis no DataFrame: {df.columns.tolist()}")
            
            # Exibir tabela
            st.dataframe(
                df,
                hide_index=True,
                column_config={
                    "image_path": st.column_config.ImageColumn(
                        "Imagem",
                        help="Imagem da criatura"
                    )
                },
                use_container_width=True,
                key=table_key,
                column_order=["image_path", "Nome", "Categoria", "Subcategoria", "Divisão"]
            )
            
            # Debug output para verificar caminhos de imagem
            st.write("### Detalhes de caminhos de imagem:")
            for i, row in df.iloc[:3].iterrows():
                img_path = row['image_path']
                verified_path = verify_image_path(img_path)
                exists = os.path.exists(img_path) if not img_path.startswith(('data:', 'http://', 'https://')) else "URL"
                st.write(f"Imagem {i+1}: {row['Nome']}")
                st.write(f"- Caminho original: {img_path}")
                st.write(f"- Caminho verificado: {verified_path}")
                st.write(f"- Existe? {exists}")
            
            # Adicionar seleção por selectbox em vez de checkbox
            creature_options = ["Selecione uma criatura..."] + df["Nome"].tolist()
            selected_creature_name = st.selectbox(
                "Selecione uma criatura para ver detalhes:",
                creature_options,
                key=f"select_creature_{table_key}"
            )
            
            if selected_creature_name and selected_creature_name != "Selecione uma criatura...":
                st.session_state.selected_creature = selected_creature_name
        else:  # Grid de imagens
            # Exibir criaturas em formato de grade de imagens
            # Criar uma grade de 4 colunas
            cols = st.columns(4)
            
            # Iterar sobre as criaturas filtradas
            for idx, (i, row) in enumerate(df.iterrows()):
                col_idx = idx % 4
                with cols[col_idx]:
                    # Exibir a imagem
                    img_path = row['image_path']
                    # Verificar e possivelmente corrigir caminho da imagem
                    img_path = verify_image_path(img_path)
                    
                    if img_path:
                        if img_path.startswith('data:'):
                            # Se for um data URL, exibir diretamente
                            st.image(img_path, width=100)
                        elif os.path.exists(img_path):
                            # Se for um caminho de arquivo, abrir e exibir
                            with open(img_path, "rb") as f:
                                image_data = f.read()
                            st.image(image_data, width=100)
                        else:
                            st.image("https://via.placeholder.com/100x100?text=Sem+Imagem", width=100)
                    else:
                        st.image("https://via.placeholder.com/100x100?text=Sem+Imagem", width=100)
                    
                    # Exibir o nome como botão para seleção
                    if st.button(row['Nome'], key=f"btn_creature_{i}"):
                        st.session_state.selected_creature = row['Nome']
                        st.rerun()
        
        # Exibir detalhes da criatura selecionada
        if st.session_state.selected_creature:
            st.subheader(f"Detalhes de {st.session_state.selected_creature}")
            
            # Buscar dados da criatura
            creature_data = read_creature(st.session_state.selected_creature)
            
            if creature_data:
                # Organizar layout
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    # Exibir imagem
                    img_path = creature_data.get('image_path', '')
                    # Verificar e possivelmente corrigir caminho da imagem
                    img_path = verify_image_path(img_path)
                    
                    if img_path:
                        if img_path.startswith('data:'):
                            # Se for um data URL, exibir diretamente
                            st.image(img_path, width=150)
                        elif os.path.exists(img_path):
                            # Se for um caminho de arquivo, abrir e exibir
                            with open(img_path, "rb") as f:
                                image_data = f.read()
                            st.image(image_data, width=150)
                        else:
                            st.write("Imagem não disponível")
                    else:
                        st.write("Imagem não disponível")
                
                with col2:
                    # Exibir informações básicas
                    st.write(f"**Categoria:** {creature_data.get('category', 'Desconhecida')}")
                    st.write(f"**Subcategoria:** {creature_data.get('subcategory', 'Desconhecida')}")
                    
                    # Extrair e exibir informações detalhadas
                    try:
                        data_dict = json.loads(creature_data.get('data_json', '{}')) if isinstance(creature_data.get('data_json'), str) else creature_data.get('data_json', {})
                        
                        # Exibir seção
                        if 'Section' in data_dict:
                            st.write(f"**Divisão:** {format_section_name(data_dict['Section'])}")
                        
                        # Exibir comportamento se disponível
                        if 'Behaviour' in data_dict:
                            st.write("**Comportamento:**")
                            st.write(data_dict['Behaviour'])
                        
                        # Exibir resistências se disponíveis
                        if 'Resistances' in data_dict and isinstance(data_dict['Resistances'], dict):
                            st.write("**Resistências:**")
                            resistances = data_dict['Resistances']
                            
                            # Formatar como tabela
                            res_data = [{"Elemento": elem, "Valor": f"{val}%" if isinstance(val, (int, float)) else val} 
                                        for elem, val in resistances.items()]
                            st.table(pd.DataFrame(res_data))
                        
                        # Exibir loot se disponível
                        if 'Loot' in data_dict and isinstance(data_dict['Loot'], list):
                            st.write("**Loot:**")
                            
                            # Criar DataFrame com os itens de loot
                            loot_data = []
                            for loot_item in data_dict['Loot']:
                                if isinstance(loot_item, dict):
                                    loot_data.append({
                                        "Item": loot_item.get('item', ''),
                                        "Taxa de Drop": loot_item.get('rate', '')
                                    })
                            
                            if loot_data:
                                st.table(pd.DataFrame(loot_data))
                        
                        # Criar tabela com outros dados
                        info_data = []
                        for key, value in data_dict.items():
                            if key not in ['Section', 'Name', 'Behaviour', 'Resistances', 'Loot'] and not isinstance(value, (dict, list)):
                                info_data.append({"Atributo": key, "Valor": value})
                        
                        if info_data:
                            st.write("**Atributos Básicos:**")
                            st.table(pd.DataFrame(info_data))
                    except Exception as e:
                        st.error(f"Erro ao processar dados da criatura: {str(e)}")
            
            # Botão para obter detalhes adicionais
            if st.button("Coletar Detalhes Completos", key="get_details_btn"):
                with st.spinner(f"Coletando detalhes de {st.session_state.selected_creature}..."):
                    result = update_creature_details(st.session_state.selected_creature)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success("Detalhes atualizados com sucesso!")
                        # Atualizar dados na sessão para exibir imediatamente
                        creature_data = read_creature(st.session_state.selected_creature)
                        st.rerun()
            
            # Botão para limpar seleção
            if st.button("Limpar seleção"):
                st.session_state.selected_creature = None
                st.rerun()
    else:
        st.info("Não há criaturas no banco de dados. Use a aba de Gerenciamento de Scraping para buscar dados.")

    # Teste direto com DataFrame de imagens
    st.write("### Teste direto com DataFrame de imagens:")
    
    # Criar DataFrame de teste
    test_data = []
    
    if all_creatures and len(all_creatures) > 0:
        # Usar dados reais
        for i, creature in enumerate(all_creatures[:5]):
            test_data.append({
                "nome": creature.get('creature_name', 'Desconhecido'),
                "img_path": creature.get('image_path', ''),
                "categoria": creature.get('category', 'Desconhecida')
            })
            # Verificar se a imagem existe
            img_path = creature.get('image_path', '')
            if img_path and os.path.exists(img_path):
                st.write(f"Imagem existe para {creature.get('creature_name')}: {img_path}")
            else:
                st.write(f"Imagem não existe para {creature.get('creature_name')}: {img_path}")
    else:
        # Criar dados de exemplo
        test_data = [
            {"nome": "Teste 1", "img_path": "https://static.tibia.com/images/global/header/monsters.gif", "categoria": "Categoria 1"},
            {"nome": "Teste 2", "img_path": "https://static.tibia.com/images/creatures/arachnophobica.gif", "categoria": "Categoria 2"}
        ]
    
    # Criar DataFrame
    test_df = pd.DataFrame(test_data)
    
    # Exibir DataFrame com configuração de imagem
    st.write("DataFrame de teste com imagens:")
    st.dataframe(
        test_df,
        column_config={
            "img_path": st.column_config.ImageColumn(
                "Imagem",
                help="Imagem de teste"
            )
        },
        hide_index=True
    )
    
    # Mostrar os dados brutos para comparação
    st.write("Dados brutos do DataFrame de teste:")
    st.write(test_df)

    # Teste muito básico com URLs de imagem absolutas
    st.write("### Teste de ImageColumn com URLs absolutas:")
    
    # Criar dados de teste com URLs absolutas que sabemos que funcionam
    direct_test_data = [
        {"name": "Rat", "image": "https://static.tibia.com/images/library/rat.gif", "type": "URL absoluta"},
        {"name": "Dragon", "image": "https://static.tibia.com/images/library/dragon.gif", "type": "URL absoluta"},
        {"name": "Local", "image": "utils/img/creatures/Rat.gif", "type": "Caminho local (se existir)"}
    ]
    
    # Criar DataFrame
    direct_test_df = pd.DataFrame(direct_test_data)
    
    # Mostrar o DataFrame com configuração de imagem
    st.dataframe(
        direct_test_df,
        column_config={
            "image": st.column_config.ImageColumn(
                "Imagem",
                help="Imagem de teste"
            )
        },
        hide_index=True
    )
    
    # Mostrar as imagens individualmente com st.image para comparação
    st.write("### Imagens individuais com st.image:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("Rat")
        st.image("https://static.tibia.com/images/library/rat.gif")
        
    with col2:
        st.write("Dragon")
        st.image("https://static.tibia.com/images/library/dragon.gif")
        
    with col3:
        st.write("Local (se existir)")
        if os.path.exists("utils/img/creatures/Rat.gif"):
            with open("utils/img/creatures/Rat.gif", "rb") as f:
                st.image(f.read())
        else:
            st.write("Arquivo local não encontrado")

with tab2:
    st.header("Gerenciamento de Scraping")
    
    # Exibir status atual do scraping
    if st.session_state.scraping_status:
        st.info(st.session_state.scraping_status)
    
    # Expandir para mostrar todas as categorias
    with st.expander("Scraping de Subcategorias", expanded=True):
        for category, category_data in CREATURE_CATEGORIES.items():
            st.subheader(category)
            
            # Adicionar botão para scraping de toda a categoria
            if st.button(f"Scrape Todas as Subcategorias de {category}", key=f"btn_cat_{category}"):
                st.warning(f"Iniciando scraping de todas as subcategorias de {category}...")
                
                # Inicializar contadores
                total_count = 0
                progress_bar = st.progress(0)
                
                # Calcular total de subcategorias
                total_subcategories = len(category_data['subcategories'])
                
                # Contador de subcategorias processadas
                processed_subcategories = 0
                
                # Processar cada subcategoria
                for subcategory, url in category_data['subcategories'].items():
                    update_scraping_status(f"Processando {subcategory} de {category} ({processed_subcategories}/{total_subcategories})")
                    
                    results = scrap_all_creatures_from_subcategory(
                        category, subcategory, url, update_scraping_status
                    )
                    
                    total_count += results
                    processed_subcategories += 1
                    
                    # Atualizar barra de progresso
                    progress_bar.progress(processed_subcategories / total_subcategories)
                
                st.success(f"Scraping completo! Foram encontradas {total_count} criaturas em {category}.")
                st.session_state.rerun_page = True
            
            # Criar colunas para os botões
            cols = st.columns(3)
            
            # Adicionar botão para cada subcategoria
            for i, (subcategory, url) in enumerate(category_data['subcategories'].items()):
                col_idx = i % 3
                with cols[col_idx]:
                    if st.button(f"Scrape {subcategory}", key=f"btn_{category}_{subcategory}"):
                        scrape_subcategory(category, subcategory, url)
    
    # Opções avançadas de scraping
    with st.expander("Opções Avançadas de Scraping"):
        # Botão para scraping completo
        if st.button("Realizar Scraping Completo (Todas as Subcategorias)", key="btn_all"):
            st.warning("Atenção: Este processo pode levar muito tempo!")
            all_count = 0
            progress_bar = st.progress(0)
            
            # Calcular total de subcategorias
            total_subcategories = sum(len(cat_data['subcategories']) for cat_data in CREATURE_CATEGORIES.values())
            
            # Contador de subcategorias processadas
            processed_subcategories = 0
            
            for category, category_data in CREATURE_CATEGORIES.items():
                for subcategory, url in category_data['subcategories'].items():
                    update_scraping_status(f"Processando {subcategory} ({processed_subcategories}/{total_subcategories})")
                    
                    results = scrap_all_creatures_from_subcategory(
                        category, subcategory, url, update_scraping_status
                    )
                    
                    all_count += results
                    processed_subcategories += 1
                    
                    # Atualizar barra de progresso
                    progress_bar.progress(processed_subcategories / total_subcategories)
            
            st.success(f"Scraping completo! Foram encontradas {all_count} criaturas no total.")
            st.session_state.rerun_page = True
        
        # Opção para atualizar detalhes de todas as criaturas
        if st.button("Atualizar Detalhes de Todas as Criaturas no Banco", key="btn_update_all"):
            st.warning("Atenção: Este processo pode levar muito tempo!")
            
            # Buscar todas as criaturas do banco
            all_creatures = read_all_creatures()
            
            if not all_creatures:
                st.error("Não há criaturas no banco de dados!")
            else:
                # Inicializar contadores
                total_creatures = len(all_creatures)
                updated_count = 0
                error_count = 0
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Processar cada criatura
                for i, creature in enumerate(all_creatures):
                    creature_name = creature.get('creature_name')
                    
                    if not creature_name:
                        continue
                    
                    status_text.info(f"Atualizando {creature_name} ({i+1}/{total_creatures})")
                    
                    # Atualizar detalhes
                    result = update_creature_details(creature_name)
                    
                    if "error" in result:
                        error_count += 1
                    else:
                        updated_count += 1
                    
                    # Atualizar barra de progresso
                    progress_bar.progress((i + 1) / total_creatures)
                
                st.success(f"Atualização concluída! {updated_count} criaturas atualizadas com sucesso, {error_count} com erros.")
                
                if error_count > 0:
                    st.warning("Alguns erros ocorreram durante a atualização. Verifique o log para mais detalhes.")
                
                st.session_state.rerun_page = True

# Recarregar a página se necessário
if st.session_state.get('rerun_requested', False):
    st.session_state.rerun_requested = False
    st.rerun() 