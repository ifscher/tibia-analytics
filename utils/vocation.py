# Mapeamento de vocações para padronização
VOCATION_MAPPING = {
    'sorcerer': 'sorcerers',
    'druid': 'druids',
    'knight': 'knights',
    'paladin': 'paladins',
    'monk': 'monks'
}


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


def extract_vocations(data_dict, verbose=False):
    """
    Extrai vocações de um dicionário de dados.
    Retorna uma lista de vocações.
    """
    vocations = []
    
    # Se já temos vocações extraídas, retorna elas
    if 'vocations' in data_dict and data_dict['vocations']:
        return data_dict['vocations']
    
    # Lista de vocações válidas
    valid_vocations = {
        'sorcerer': 'sorcerers',
        'druid': 'druids',
        'knight': 'knights',
        'paladin': 'paladins',
        'monk': 'monks'
    }
    
    # Verifica se há requisitos de vocação no caminho "Requirements" > "Vocation"
    if isinstance(data_dict.get('Requirements'), dict) and data_dict['Requirements'].get('Vocation'):
        req_vocs = data_dict['Requirements']['Vocation']
        if isinstance(req_vocs, str):
            req_vocs = [req_vocs]
        
        for voc in req_vocs:
            if isinstance(voc, str):
                voc_lower = voc.lower().strip()
                for valid_voc, valid_plural in valid_vocations.items():
                    if valid_voc in voc_lower or valid_plural in voc_lower:
                        if valid_plural not in vocations:
                            vocations.append(valid_plural)
        
        # Se encontramos vocações no caminho de requisitos, retornamos elas
        if vocations:
            return vocations
    
    # Procura por vocações em todas as colunas
    for key, value in data_dict.items():
        if isinstance(value, str):
            # Converte para minúsculo para comparação
            value_lower = value.lower()
            
            # Procura por vocações válidas no texto
            for voc, voc_plural in valid_vocations.items():
                if voc in value_lower or voc_plural in value_lower:
                    if voc_plural not in vocations:
                        vocations.append(voc_plural)
        
        elif isinstance(value, list):
            # Se é uma lista, procura em cada item
            for item in value:
                if isinstance(item, str):
                    item_lower = item.lower()
                    for voc, voc_plural in valid_vocations.items():
                        if voc in item_lower or voc_plural in item_lower:
                            if voc_plural not in vocations:
                                vocations.append(voc_plural)
    
    # Se não encontrou vocações e é um escudo, assume que é para todas as vocações
    if not vocations and 'Shields' in str(data_dict.get('category', '')):
        vocations = ['sorcerers', 'druids', 'knights', 'paladins', 'monks']
    
    return vocations 