import sqlite3
import json
import os
import requests
from urllib.parse import urlparse

DB_NAME = "mydb.db"


# ------------------------------------------------------------------------------
# A) Conexão e (Re)Criação da Tabela
# ------------------------------------------------------------------------------
def create_connection():
    """Cria ou conecta ao banco de dados SQLite."""
    return sqlite3.connect(DB_NAME)


def create_table():
    conn = create_connection()
    c = conn.cursor()

    # Cria a tabela com 'item_name' como PRIMARY KEY somente se não existir
    c.execute("""
    CREATE TABLE IF NOT EXISTS itens (
        item_name TEXT PRIMARY KEY,
        category TEXT,
        image_path TEXT,
        data_json TEXT
    )
    """)

    # Cria a tabela com 'creature_name' como PRIMARY KEY somente se não existir
    c.execute("""
    CREATE TABLE IF NOT EXISTS criaturas (
        creature_name TEXT PRIMARY KEY,
        category TEXT,
        subcategory TEXT,
        image_path TEXT,
        data_json TEXT
    )
    """)

    conn.commit()
    conn.close()


# ------------------------------------------------------------------------------
# B) CRUD (Create, Read, Update, Delete)
# ------------------------------------------------------------------------------
def create_item(item_name, category, image_path, data_dict):
    """
    Insere um novo item na tabela 'itens'.
    - item_name: Nome do item (PK).
    - category: ex. "Helmets", "Armors", etc.
    - image_path: caminho local da imagem.
    - data_dict: dicionário com outros dados do item (será armazenado em JSON).
      ex.: {"Def": "2", "Arm": "1", "Weight": "42.0"}
    """
    conn = create_connection()
    c = conn.cursor()

    data_json = json.dumps(data_dict, ensure_ascii=False)

    # INSERT simples. Caso o item_name já exista, gera erro de chave primária.
    c.execute("""
        INSERT OR IGNORE INTO itens (item_name, category, image_path, data_json)
        VALUES (?, ?, ?, ?)
    """, (item_name, category, image_path, data_json))

    conn.commit()
    conn.close()


def read_item(item_name):
    """
    Lê e retorna um registro com item_name específico.
    Retorna um dicionário: {"item_name", "category", "image_path", "data_json"}
    ou None se não existir.
    """
    conn = create_connection()
    c = conn.cursor()

    c.execute("SELECT item_name, category, image_path, data_json FROM itens WHERE item_name = ?", (item_name,))
    row = c.fetchone()
    conn.close()

    if row:
        return {
            "item_name": row[0],
            "category":  row[1],
            "image_path": row[2],
            "data_json": row[3],
        }
    return None


def update_item(item_name, category=None, image_path=None, data_dict=None):
    """
    Atualiza os campos de um item existente, exceto o nome, que é a PK.
    Se algum parâmetro for None, não atualiza aquele campo.
    Retorna o número de linhas afetadas (0 se não encontrado).
    """
    fields = []
    values = []

    if category is not None:
        fields.append("category = ?")
        values.append(category)

    if image_path is not None:
        fields.append("image_path = ?")
        values.append(image_path)

    if data_dict is not None:
        data_json = json.dumps(data_dict, ensure_ascii=False)
        fields.append("data_json = ?")
        values.append(data_json)

    if not fields:
        return 0  # Nada a atualizar

    query_set = ", ".join(fields)
    query = f"UPDATE itens SET {query_set} WHERE item_name = ?"
    values.append(item_name)

    conn = create_connection()
    c = conn.cursor()
    c.execute(query, tuple(values))
    conn.commit()
    affected = c.rowcount
    conn.close()

    return affected


def upsert_item(item_name, category, image_path, data_dict):
    """
    upsert_item: insere (create) se não existir, ou atualiza (update) se já existir
    e tiver diferenças.
    """
    # Verificação de segurança: não permite itens com nome inválido
    if not item_name or not item_name.strip() or item_name.lower() == "none":
        print(f"[IGNORADO] Item com nome inválido: '{item_name}'")
        return
    
    existing = read_item(item_name)  # lê do banco pela PK (item_name)

    if existing is None:
        # Se não existe, faz CREATE
        create_item(item_name, category, image_path, data_dict)
        print(f"[CREATE] Novo item criado: {item_name}")
    else:
        # Já existe. Vamos verificar se houve alteração.
        # Compare 'existing' com os novos valores.
        
        # existing["category"], existing["image_path"], e existing["data_json"]
        # lembre que data_json é string, converta p/ dict (se não for já).
        from json import loads
        existing_data_dict = loads(existing["data_json"]) if isinstance(existing["data_json"], str) else existing["data_json"]

        # Checa se algo mudou:
        need_update = False
        
        # 1) Se a categoria for diferente
        if existing["category"] != category:
            need_update = True
        
        # 2) Se o caminho da imagem for diferente
        if existing["image_path"] != image_path:
            need_update = True
        
        # 3) Se o conteúdo do data_dict for diferente
        if existing_data_dict != data_dict:
            need_update = True
        
        if need_update:
            update_item(item_name, category, image_path, data_dict)
            print(f"[UPDATE] Item '{item_name}' foi modificado e atualizado.")
        else:
            print(f"[NO CHANGE] Item '{item_name}' está igual. Não foi atualizado.")


def delete_item(item_name):
    """
    Deleta um item pelo nome.
    Retorna o número de linhas deletadas (0 ou 1).
    """
    conn = create_connection()
    c = conn.cursor()
    c.execute("DELETE FROM itens WHERE item_name = ?", (item_name,))
    conn.commit()
    deleted = c.rowcount
    conn.close()
    return deleted


def read_all_items():
    """
    Retorna todos os itens cadastrados, em forma de lista de dicionários.
    """
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT item_name, category, image_path, data_json FROM itens")
    rows = c.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "item_name": row[0],
            "category":  row[1],
            "image_path": row[2],
            "data_json": row[3],
        })
    return results


def delete_none_items():
    """
    Remove todos os itens com nome "None", vazio ou NULL do banco de dados.
    Retorna o número de itens removidos.
    """
    conn = create_connection()
    c = conn.cursor()
    c.execute("DELETE FROM itens WHERE item_name IS NULL")
    conn.commit()
    deleted = c.rowcount
    conn.close()
    return deleted


def delete_items_by_category(category):
    """
    Remove todos os itens de uma categoria específica do banco de dados.
    Preserva as imagens locais.
    Retorna o número de itens removidos.
    
    Args:
        category (str): A categoria de itens a ser removida.
    """
    conn = create_connection()
    c = conn.cursor()
    c.execute("DELETE FROM itens WHERE category = ?", (category,))
    conn.commit()
    deleted = c.rowcount
    conn.close()
    return deleted


def create_creature(creature_name, category, subcategory, image_path, data_dict):
    """
    Insere uma nova criatura na tabela 'criaturas'.
    - creature_name: Nome da criatura (PK).
    - category: Categoria principal da criatura.
    - subcategory: Subcategoria da criatura.
    - image_path: caminho local da imagem.
    - data_dict: dicionário com outros dados da criatura (será armazenado em JSON).
    """
    conn = create_connection()
    c = conn.cursor()

    data_json = json.dumps(data_dict, ensure_ascii=False)

    # INSERT simples. Caso o creature_name já exista, gera erro de chave primária.
    c.execute("""
        INSERT OR IGNORE INTO criaturas (creature_name, category, subcategory, image_path, data_json)
        VALUES (?, ?, ?, ?, ?)
    """, (creature_name, category, subcategory, image_path, data_json))

    conn.commit()
    conn.close()


def read_creature(creature_name):
    """
    Lê e retorna um registro com creature_name específico.
    Retorna um dicionário: {"creature_name", "category", "subcategory", "image_path", "data_json"}
    ou None se não existir.
    """
    conn = create_connection()
    c = conn.cursor()

    c.execute("""
        SELECT creature_name, category, subcategory, image_path, data_json 
        FROM criaturas 
        WHERE creature_name = ?
    """, (creature_name,))
    row = c.fetchone()
    conn.close()

    if row:
        return {
            "creature_name": row[0],
            "category": row[1],
            "subcategory": row[2],
            "image_path": row[3],
            "data_json": row[4],
        }
    return None


def update_creature(creature_name, category=None, subcategory=None, image_path=None, data_dict=None):
    """
    Atualiza os campos de uma criatura existente, exceto o nome, que é a PK.
    Se algum parâmetro for None, não atualiza aquele campo.
    Retorna o número de linhas afetadas (0 se não encontrado).
    """
    fields = []
    values = []

    if category is not None:
        fields.append("category = ?")
        values.append(category)

    if subcategory is not None:
        fields.append("subcategory = ?")
        values.append(subcategory)

    if image_path is not None:
        fields.append("image_path = ?")
        values.append(image_path)

    if data_dict is not None:
        data_json = json.dumps(data_dict, ensure_ascii=False)
        fields.append("data_json = ?")
        values.append(data_json)

    if not fields:
        return 0  # Nada a atualizar

    query_set = ", ".join(fields)
    query = f"UPDATE criaturas SET {query_set} WHERE creature_name = ?"
    values.append(creature_name)

    conn = create_connection()
    c = conn.cursor()
    c.execute(query, tuple(values))
    conn.commit()
    affected = c.rowcount
    conn.close()

    return affected


def upsert_creature(creature_name, category, subcategory, image_path, data_dict):
    """
    upsert_creature: insere (create) se não existir, ou atualiza (update) se já existir
    e tiver diferenças.
    """
    # Verificação de segurança: não permite criaturas com nome inválido
    if not creature_name or not creature_name.strip() or creature_name.lower() == "none":
        print(f"[IGNORADO] Criatura com nome inválido: '{creature_name}'")
        return
    
    existing = read_creature(creature_name)  # lê do banco pela PK (creature_name)

    if existing is None:
        # Se não existe, faz CREATE
        create_creature(creature_name, category, subcategory, image_path, data_dict)
        print(f"[CREATE] Nova criatura criada: {creature_name}")
    else:
        # Já existe. Vamos verificar se houve alteração.
        # Compare 'existing' com os novos valores.
        
        # existing["category"], existing["subcategory"], existing["image_path"], e existing["data_json"]
        # lembre que data_json é string, converta p/ dict (se não for já).
        from json import loads
        existing_data_dict = loads(existing["data_json"]) if isinstance(existing["data_json"], str) else existing["data_json"]

        # Checa se algo mudou:
        need_update = False
        
        # 1) Se a categoria for diferente
        if existing["category"] != category:
            need_update = True
        
        # 2) Se a subcategoria for diferente
        if existing["subcategory"] != subcategory:
            need_update = True
        
        # 3) Se o caminho da imagem for diferente
        if existing["image_path"] != image_path:
            need_update = True
        
        # 4) Se o conteúdo do data_dict for diferente
        if existing_data_dict != data_dict:
            need_update = True
        
        if need_update:
            update_creature(creature_name, category, subcategory, image_path, data_dict)
            print(f"[UPDATE] Criatura '{creature_name}' foi modificada e atualizada.")
        else:
            print(f"[NO CHANGE] Criatura '{creature_name}' está igual. Não foi atualizada.")


def delete_creature(creature_name):
    """
    Deleta uma criatura pelo nome.
    Retorna o número de linhas deletadas (0 ou 1).
    """
    conn = create_connection()
    c = conn.cursor()
    c.execute("DELETE FROM criaturas WHERE creature_name = ?", (creature_name,))
    conn.commit()
    deleted = c.rowcount
    conn.close()
    return deleted


def read_all_creatures():
    """
    Retorna todas as criaturas cadastradas, em forma de lista de dicionários.
    """
    conn = create_connection()
    c = conn.cursor()
    c.execute("""
        SELECT creature_name, category, subcategory, image_path, data_json 
        FROM criaturas
    """)
    rows = c.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "creature_name": row[0],
            "category": row[1],
            "subcategory": row[2],
            "image_path": row[3],
            "data_json": row[4],
        })
    return results


def delete_creatures_by_category(category):
    """
    Remove todas as criaturas de uma categoria específica do banco de dados.
    Preserva as imagens locais.
    Retorna o número de criaturas removidas.
    
    Args:
        category (str): A categoria de criaturas a ser removida.
    """
    conn = create_connection()
    c = conn.cursor()
    c.execute("DELETE FROM criaturas WHERE category = ?", (category,))
    conn.commit()
    deleted = c.rowcount
    conn.close()
    return deleted


# ------------------------------------------------------------------------------
# C) Função para baixar imagem, atualizando o registro se mudar o caminho
# ------------------------------------------------------------------------------
def get_original_filename(img_url: str) -> str:
    """
    Recupera o nome original do arquivo contido na URL, ignorando
    '/revision/latest' etc. Ex.: retorna "War_Horn_Helmet.gif".
    """
    print(f"[DEBUG] get_original_filename para URL: {img_url}")
    
    if not img_url:
        print("[DEBUG] URL vazia")
        return ""
    
    # Handle Special:FilePath URLs from Tibia wiki
    if "Special:FilePath" in img_url:
        # Extract the filename from the FilePath URL
        segments = img_url.split('/')
        filename = segments[-1]  # Last part is the filename
        
        # Add .gif extension if missing
        if not any(filename.lower().endswith(ext) for ext in ['.gif', '.png', '.jpg', '.jpeg']):
            filename += '.gif'  # Most Tibia images are GIFs
        
        print(f"[DEBUG] Extracted filename from FilePath: {filename}")
        return filename
        
    parsed = urlparse(img_url)
    segments = parsed.path.split('/')  
    print(f"[DEBUG] Segmentos de URL: {segments}")
    # normal/esperado: ["", "tibia", "images", "e", "e4", "War_Horn_Helmet.gif", "revision", "latest"]

    # Procurar algum segmento que tenha extensão .gif, .png, .jpg, etc.
    exts = {'.gif', '.png', '.jpg', '.jpeg', '.webp'}
    for seg in reversed(segments):
        nome, ext = os.path.splitext(seg)
        if ext.lower() in exts:
            print(f"[DEBUG] Encontrado filename: {seg}")
            return seg  # "War_Horn_Helmet.gif"
    print("[DEBUG] Não foi encontrado um nome de arquivo válido")
    return "img_unknown.gif"


def download_image_if_needed(name: str, img_url: str, folder: str = "utils/img", category: str = None) -> None:
    """
    Faz download da imagem usando o nome original extraído
    e salva em 'folder'. Depois, se o arquivo local_path for diferente
    do que está salvo em 'image_path', atualiza a tabela.
    - name: PK do item/criatura no banco. Precisamos disso para atualizar.
    - img_url: link da imagem no Fandom (ou outro local).
    - folder: pasta local onde salvar.
    - category: categoria do item (para organizar em subpastas).
    Retorna o caminho local (local_path).
    """
    print(f"[DEBUG DOWNLOAD] Tentando download para {name} da URL: {img_url}")
    
    if not img_url:
        print(f"[DEBUG DOWNLOAD] URL vazia para {name}")
        return ""
        
    # Verificar se é uma URL malformada (corrigir URLs com prefixos duplicados)
    if img_url.startswith("https:data:") or img_url.startswith("http:data:"):
        print(f"AVISO: URL malformada detectada: {img_url}")
        return ""

    # Se temos uma categoria para itens, usar a pasta específica
    if category and folder == "utils/img":
        # Criar uma pasta específica para a categoria
        folder = os.path.join("utils/img/itens", category)
    
    print(f"[DEBUG DOWNLOAD] Criando pasta: {folder}")
    os.makedirs(folder, exist_ok=True)
    
    # Sanitize filename to ensure it works on Windows
    filename = get_original_filename(img_url)
    # Replace problematic characters in filename
    sanitized_name = name.replace(" ", "_").replace("'", "").replace('"', "").replace("/", "_").replace("\\", "_")
    
    # If no valid filename was extracted, create one from the creature/item name
    if not filename or filename == "img_unknown.gif":
        filename = f"{sanitized_name}.gif"
    
    print(f"[DEBUG DOWNLOAD] Nome de arquivo extraído: {filename}")
    
    local_path = os.path.join(folder, filename)
    print(f"[DEBUG DOWNLOAD] Caminho local: {local_path}")

    # Se ainda não existe, faz o download
    if not os.path.exists(local_path):
        print(f"[DEBUG DOWNLOAD] Arquivo não existe, tentando download...")
        
        # List of URLs to try
        urls_to_try = [img_url]
        
        # Add alternative URLs for creatures
        if "creatures" in folder:
            # Add static Tibia URLs for creatures
            clean_name = sanitized_name.lower()
            static_url = f"https://static.tibia.com/images/library/{clean_name}.gif"
            if static_url not in urls_to_try:
                urls_to_try.append(static_url)
                
            # Try fandom wiki URL
            wiki_url = f"https://tibia.fandom.com/wiki/Special:FilePath/{sanitized_name}.gif"
            if wiki_url not in urls_to_try:
                urls_to_try.append(wiki_url)
        
        # Try downloading from each URL
        for url in urls_to_try:
            try:
                print(f"[DEBUG DOWNLOAD] Tentando URL: {url}")
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    print(f"[DEBUG DOWNLOAD] Resposta com sucesso: {resp.status_code}")
                    with open(local_path, "wb") as f:
                        content = resp.content
                        print(f"[DEBUG DOWNLOAD] Tamanho do conteúdo: {len(content)} bytes")
                        f.write(content)
                        print(f"Downloaded: {filename}")
                    # Success, exit the loop
                    break
                else:
                    print(f"[DEBUG DOWNLOAD] Status {resp.status_code} ao tentar {url}")
            except Exception as e:
                print(f"[DEBUG DOWNLOAD] Erro: {e} ao tentar {url}")
        
        # Check if download succeeded
        if not os.path.exists(local_path):
            print(f"ERRO: Não foi possível baixar a imagem de nenhuma URL")
            return ""
    else:
        print(f"[DEBUG DOWNLOAD] Arquivo já existe: {local_path}")

    # Determinar se estamos lidando com um item ou uma criatura
    # e atualizar o respectivo registro
    item = read_item(name)
    if item:
        # Se diferir, atualiza:
        if item["image_path"] != local_path:
            print(f"[DEBUG DOWNLOAD] Atualizando image_path do item {name}")
            update_item(name, image_path=local_path)
            print(f"Atualizado image_path do item '{name}' para '{local_path}'")
    else:
        # Verificar se é uma criatura
        creature = read_creature(name)
        if creature:
            # Se diferir, atualiza:
            if creature["image_path"] != local_path:
                print(f"[DEBUG DOWNLOAD] Atualizando image_path da criatura {name}")
                update_creature(name, image_path=local_path)
                print(f"Atualizado image_path da criatura '{name}' para '{local_path}'")
        else:
            print(f"[DEBUG DOWNLOAD] Não encontrou nem item nem criatura com nome: {name}")

    return local_path