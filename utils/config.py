import os
from dotenv import load_dotenv, find_dotenv

# Carrega as variáveis de ambiente do arquivo .env se existir
env_file = find_dotenv(usecwd=True)
if env_file:
    load_dotenv(env_file)

# Ambiente padrão é 'production' a menos que seja explicitamente definido como 'development'
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')


def is_development():
    """Verifica se está em ambiente de desenvolvimento."""
    return ENVIRONMENT.lower() == 'development'


def is_production():
    """Verifica se está em ambiente de produção."""
    return not is_development()


def extract_level(data):
    """
    Extrai o level do item a partir de diferentes estruturas de dados possíveis.
    
    Args:
        data (dict): Dicionário com os dados do item
        
    Returns:
        int: O level do item, ou 0 se não encontrado
    """
    if isinstance(data, dict):
        # Verificar no General Properties primeiro
        if "General Properties" in data and isinstance(data["General Properties"], dict):
            general_props = data["General Properties"]
            if "Level" in general_props:
                try:
                    level_str = str(general_props["Level"])
                    # Remover qualquer texto não numérico
                    level_str = ''.join(c for c in level_str if c.isdigit())
                    if level_str:
                        return int(level_str)
                except (ValueError, TypeError):
                    pass
        
        # Verificar Required Level
        if "Required Level" in data:
            try:
                level_str = str(data["Required Level"])
                # Remover qualquer texto não numérico
                level_str = ''.join(c for c in level_str if c.isdigit())
                if level_str:
                    return int(level_str)
            except (ValueError, TypeError):
                pass
        
        # Verificar em Requirements > Level
        if "Requirements" in data and isinstance(data["Requirements"], dict):
            if "Level" in data["Requirements"]:
                try:
                    level_str = str(data["Requirements"]["Level"])
                    level_str = ''.join(c for c in level_str if c.isdigit())
                    if level_str:
                        return int(level_str)
                except (ValueError, TypeError):
                    pass
                
        # Verificar campo Lvl (retrocompatibilidade)
        if 'Lvl' in data:
            try:
                level_str = str(data['Lvl'])
                level_str = ''.join(c for c in level_str if c.isdigit())
                if level_str:
                    return int(level_str)
            except (ValueError, TypeError):
                pass
                
        # Verificar em Campo Level direto
        if 'Level' in data:
            try:
                level_str = str(data['Level'])
                level_str = ''.join(c for c in level_str if c.isdigit())
                if level_str:
                    return int(level_str)
            except (ValueError, TypeError):
                pass
    return 0 