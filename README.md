# Tibia Analytics

Aplicação Streamlit para análise de dados do jogo Tibia, fornecendo informações sobre itens, equipamentos, custos e outras métricas do jogo.

## Funcionalidades

- **Itens e Equipamentos**: Visualização e comparação de itens do jogo
- **Custos de Boost**: Cálculo de custos para diferentes vocações
- **Itens por Level**: Filtragem de itens por nível
- **Comparador de Itens**: Comparação detalhada entre itens

## Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/seu-usuario/tibia-analytics.git
   cd tibia-analytics
   ```

2. Crie um ambiente virtual e instale as dependências:
   ```
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Execute a aplicação:
   ```
   streamlit run app.py
   ```

## Estrutura do Projeto

- `app.py`: Ponto de entrada da aplicação
- `pages/`: Contém as páginas individuais da aplicação
- `utils/`: Utilitários e funções auxiliares
- `services/`: Serviços de scraping e interação com APIs
- `mydb.py`: Interface de banco de dados

## Tecnologias Utilizadas

- Streamlit: Framework para criação de aplicações web em Python
- Pandas: Manipulação e análise de dados
- BeautifulSoup: Web scraping para obtenção de dados do jogo
- SQLite: Banco de dados local para armazenamento

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e enviar pull requests.
