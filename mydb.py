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


# ------------------------------------------------------------------------------
# C) Função para baixar imagem, atualizando o registro se mudar o caminho
# ------------------------------------------------------------------------------
def get_original_filename(img_url: str) -> str:
    """
    Recupera o nome original do arquivo contido na URL, ignorando
    '/revision/latest' etc. Ex.: retorna "War_Horn_Helmet.gif".
    """
    if not img_url:
        return ""
    parsed = urlparse(img_url)
    segments = parsed.path.split('/')  
    # normal/esperado: ["", "tibia", "images", "e", "e4", "War_Horn_Helmet.gif", "revision", "latest"]

    # Procurar algum segmento que tenha extensão .gif, .png, .jpg, etc.
    exts = {'.gif', '.png', '.jpg', '.jpeg', '.webp'}
    for seg in reversed(segments):
        nome, ext = os.path.splitext(seg)
        if ext.lower() in exts:
            return seg  # "War_Horn_Helmet.gif"
    return "img_unknown.gif"


def download_image_if_needed(item_name: str, img_url: str, folder: str = "utils/img") -> None:
    """
    Faz download da imagem usando o nome original extraído
    e salva em 'folder'. Depois, se o arquivo local_path for diferente
    do que está salvo em 'itens.image_path', atualiza a tabela.
    - item_name: PK do item no banco. Precisamos disso para atualizar.
    - img_url: link da imagem no Fandom (ou outro local).
    - folder: pasta local onde salvar.
    Retorna o caminho local (local_path).
    """
    if not img_url:
        return ""

    os.makedirs(folder, exist_ok=True)
    filename = get_original_filename(img_url)
    local_path = os.path.join(folder, filename)

    # Se ainda não existe, faz o download
    if not os.path.exists(local_path):
        try:
            resp = requests.get(img_url, timeout=10)
            if resp.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(resp.content)
                    print(f"Downloaded: {filename}")
            else:
                print(f"ERRO: Status {resp.status_code} ao baixar {img_url}")
                return ""
        except Exception as e:
            print(f"ERRO: {e} ao baixar {img_url}")
            return ""

    # Verifica se o que está no banco é diferente do local_path
    item = read_item(item_name)
    if item:
        # Se diferir, atualiza:
        if item["image_path"] != local_path:
            update_item(item_name, image_path=local_path)
            print(f"Atualizado image_path do item '{item_name}' para '{local_path}'")
    else:
        # Se o item não existir ainda, significa que não foi criado,
        # ou você pode criar agora ou apenas ignorar.
        # print(f"Item '{item_name}' não encontrado no banco para atualizar image_path.")
        pass

    return local_path