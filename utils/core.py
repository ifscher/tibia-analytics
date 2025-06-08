import os
import base64


def to_data_url(file_path: str) -> str:
    """Lê um arquivo local de imagem e retorna uma data URL (Base64 embutido)."""

    if not os.path.exists(file_path):
        return f"Arquivo não encontrado: {file_path}"

    # Descobre o formato da imagem pelo sufixo (ex.: .gif, .png, .jpg, etc.)
    ext = os.path.splitext(file_path)[1].lower().replace('.', '')

    # Leitura em binário
    with open(file_path, 'rb') as f:
        data = f.read()

    # Converte para base64 (bytes -> base64 -> str)
    base64_str = base64.b64encode(data).decode("utf-8")

    # Monta o data URL completo
    return f"data:image/{ext};base64,{base64_str}"


def binary_to_data_url(data: bytes, file_ext: str) -> str:
    """
    Converte dados binários de imagem em uma data URL.
    
    Args:
        data (bytes): Conteúdo binário da imagem
        file_ext (str): Extensão do arquivo de imagem (ex.: 'gif', 'png', 'jpg')
        
    Returns:
        str: Data URL da imagem
    """
    # Normaliza a extensão (remove o ponto se existir)
    ext = file_ext.lower().replace('.', '')
    
    # Converte para base64
    base64_str = base64.b64encode(data).decode("utf-8")
    
    # Monta o data URL completo
    return f"data:image/{ext};base64,{base64_str}"