import streamlit as st
from utils.menu import menu
from utils.favicon import set_config
import pandas as pd


set_config(title="Custos de Boost")

# Exibe o menu de navegação
menu()

st.title("Cálculadora de TC, Boost e Prey")

# Entrada do usuário em centavos
valor_reais = st.number_input(
    "Insira o valor da Tibia Coin em Reais(R$ 0,01 - R$ 0,99):",
    min_value=0.001,
    max_value=0.999,
    value=0.2443,
    step=0.001,
    format="%.4f"
)

# Entrada para GC$ 1
valor_tc_sell = st.number_input(
    "Insira o valor da TC para venda em GP (0,00 - 100,00 GP$):",
    min_value=1,
    max_value=99999,
    value=41000,  # Valor padrão
    step=100,
    format="%d"  # Formatação para inteiro
)

# Entrada para GC$ 2
valor_tc_buy = st.number_input(
    "Insira o valor da TC para compra GP (0,00 - 100,00 GP$):",
    min_value=1,
    max_value=99999,
    value=40000,  # Valor padrão
    step=100,
    format="%d"  # Formatação para inteiro
)

valor_slider = st.slider(
    "Selecione um valor",
    min_value=0,
    max_value=10000,
    value=0,
    step=25
)

resultado = valor_reais * valor_slider

# Validação adicional (opcional)
if not (1 <= valor_tc_sell <= 99999):
    st.error("Por favor, insira um valor de GP 1 entre 1 e 99.999.")
elif not (1 <= valor_tc_buy <= 99999):
    st.error("Por favor, insira um valor de GP 2 entre 1 e 99.999.")
else:
    # Processamento dos valores
    qtds = [25, 30, 250, valor_slider]  # Lista de quantidades
    sell = [x * valor_tc_sell for x in qtds]  # mutiplica pelo valor de venda e gera nova lista
    buy = [x * valor_tc_buy for x in qtds]  # multiplica pelo valor de compra e gera nova lista
    diferenca = [a - b for a, b in zip(sell, buy)]
    custo = [x * valor_reais for x in qtds]

    dados = {
        "Quantidade": qtds,
        "Preço GP (Venda)": sell,
        "Preço GP (Compra)": buy,
        "Diferença": diferenca,
        "Custo (R$)": custo
    }
    df = pd.DataFrame(dados)

    # Converter o DataFrame para HTML sem o índice
    html_table = df.to_html(index=False, formatters={
        "Preço GP (Venda)": lambda x: f"GP {x:,.0f}".replace(",", "."),
        "Preço GP (Compra)": lambda x: f"GP {x:,.0f}".replace(",", "."),
        "Diferença": lambda x: f"GP {x:,.0f}".replace(",", "."),
        "Custo (R$)": lambda x: f"R$ {x:.2f}"
    })

    # Exibir a tabela usando st.markdown com o argumento 'unsafe_allow_html=True'
    st.markdown(html_table, unsafe_allow_html=True)

st.title("Calcular preço de item")

# Entrada do usuário em centavos
item_value = st.number_input(
    "Insira o valor do item em GP:",
    min_value=1,
    max_value=9999999999,
    value=10000,  # Valor padrão
    step=1000,
    format="%d"  # Formatação para inteiro
)

item_value_sell = item_value * valor_reais / valor_tc_sell
item_value_buy = item_value * valor_reais / valor_tc_buy

st.write(f"Valor vendendo TC para compradores: R$ {item_value_buy:.2f}, valor vendendo TC diretamente: R$ {item_value_sell:.2f}")


# TABELA DE PREÇOS
st.title("Tabela de preços")

prices_qty = [30, 45, 10, 50, 100]
prices_rs = [x * valor_reais for x in prices_qty]
prices_gp_seller = [x * valor_tc_sell for x in prices_qty]
prices_gp_buyer = [x * valor_tc_buy for x in prices_qty]
diferenca = [a - b for a, b in zip(prices_gp_seller, prices_gp_buyer)]

dados = {
    "Itens": ['XP Boost', '2nd XP Boost', "Prey Wildcard", "Prey 5 Wildcards", "Prey 10 Wildcards"],
    "Horas": [1, 1, 2, 2, 2],
    "TC": prices_qty,
    "Custo (R$)": prices_rs,
    "Custo GP (TC venda)": prices_gp_seller,
    "Custo GP (TC compra)": prices_gp_buyer,
    "Diferença": diferenca,
}
df = pd.DataFrame(dados)

# Converter o DataFrame para HTML sem o índice
html_table = df.to_html(index=False, formatters={
    "Custo (R$)": lambda x: f"R$ {x:.2f}",
    "Preço GP (Venda)": lambda x: f"GP {x:,.0f}".replace(",", "."),
    "Custo GP (TC venda)": lambda x: f"GP {x:,.0f}".replace(",", "."),
    "Custo GP (TC compra)": lambda x: f"GP {x:,.0f}".replace(",", "."),
    "Diferença": lambda x: f"GP {x:,.0f}".replace(",", "."),
})

# Exibir a tabela usando st.markdown com o argumento 'unsafe_allow_html=True'
st.markdown(html_table, unsafe_allow_html=True)

# TABELA DE CUSTOS POR HORA (XP BOOST + PREY)
st.title("Custos por Hora (XP Boost + Prey)")
st.markdown("""
Esta tabela mostra o custo por hora combinando XP Boost com Prey Wildcards.
- XP Boost custa 30 TC e dura 1 hora
- Prey Wildcards duram 2 horas (5 ou 10 wildcards por criatura)
- Os valores de Prey foram divididos por 2 para representar o custo por hora
""")

# XP Boost = 30 TC por hora
# 5 Prey Wildcards = 50 TC por 2 horas → 25 TC por hora
# 10 Prey Wildcards = 100 TC por 2 horas → 50 TC por hora

combo_names = [
    "Somente XP Boost (sem prey)",
    "XP Boost + 5 Wildcards (1 criatura/hora)",
    "XP Boost + 10 Wildcards (2 criaturas/hora)"
]

# Calcular total de TC por hora para cada combo
combo_tc = [
    30,          # Apenas XP Boost
    30 + 50/2,   # XP Boost + 5 Wildcards/hora
    30 + 100/2   # XP Boost + 10 Wildcards/hora
]

combo_rs = [x * valor_reais for x in combo_tc]
combo_gp_seller = [x * valor_tc_sell for x in combo_tc]
combo_gp_buyer = [x * valor_tc_buy for x in combo_tc]
combo_diferenca = [a - b for a, b in zip(combo_gp_seller, combo_gp_buyer)]

combo_dados = {
    "Combo": combo_names,
    "TC por Hora": combo_tc,
    "Custo por Hora (R$)": combo_rs,
    "Custo GP por Hora (TC venda)": combo_gp_seller,
    "Custo GP por Hora (TC compra)": combo_gp_buyer,
    "Diferença": combo_diferenca
}

combo_df = pd.DataFrame(combo_dados)

# Converter o DataFrame para HTML sem o índice
combo_html_table = combo_df.to_html(index=False, formatters={
    "TC por Hora": lambda x: f"{x:.1f}",
    "Custo por Hora (R$)": lambda x: f"R$ {x:.2f}",
    "Custo GP por Hora (TC venda)": lambda x: f"GP {x:,.0f}".replace(",", "."),
    "Custo GP por Hora (TC compra)": lambda x: f"GP {x:,.0f}".replace(",", "."),
    "Diferença": lambda x: f"GP {x:,.0f}".replace(",", ".")
})

# Exibir a tabela usando st.markdown com o argumento 'unsafe_allow_html=True'
st.markdown(combo_html_table, unsafe_allow_html=True)