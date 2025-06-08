#!/usr/bin/env python
import os
import shutil
import sqlite3
from mydb import read_all_items, update_item

def create_connection():
    """Cria uma conexão com o banco de dados SQLite"""
    conn = None
    try:
        conn = sqlite3.connect('tibia.db')
        return conn
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
    return conn

def reorganize_item_images():
    """
    Reorganiza as imagens dos itens movendo-as das pastas antigas para as novas pastas
    categorizadas por tipo de item.
    """
    print("Iniciando reorganização de imagens...")
    
    # Obter todos os itens do banco de dados
    items = read_all_items()
    print(f"Encontrados {len(items)} itens no banco de dados.")
    
    # Contadores para estatísticas
    moved_count = 0
    failed_count = 0
    already_organized_count = 0
    
    # Processar cada item
    for item in items:
        item_name = item.get('item_name')
        category = item.get('category')
        current_path = item.get('image_path')
        
        if not current_path or not os.path.exists(current_path) or not category:
            failed_count += 1
            print(f"Pulando item '{item_name}': caminho não existe ou categoria ausente")
            continue
        
        # Verificar se a imagem já está na pasta correta
        target_folder = os.path.join("utils/img/itens", category)
        
        # Criar a pasta de destino se não existir
        os.makedirs(target_folder, exist_ok=True)
        
        # Se o caminho já contém a pasta de categoria, o item já está organizado
        if f"itens/{category}" in current_path:
            already_organized_count += 1
            continue
        
        # Pegar apenas o nome do arquivo da imagem
        filename = os.path.basename(current_path)
        target_path = os.path.join(target_folder, filename)
        
        try:
            # Copiar o arquivo para a nova localização
            shutil.copy2(current_path, target_path)
            
            # Atualizar o caminho no banco de dados
            update_item(item_name, image_path=target_path)
            
            print(f"Movida imagem de '{item_name}' para '{target_path}'")
            moved_count += 1
        except Exception as e:
            print(f"Erro ao mover imagem para '{item_name}': {e}")
            failed_count += 1
    
    print(f"\nReorganização concluída!")
    print(f"Total de itens: {len(items)}")
    print(f"Imagens movidas: {moved_count}")
    print(f"Imagens já organizadas: {already_organized_count}")
    print(f"Falhas: {failed_count}")

if __name__ == "__main__":
    reorganize_item_images() 