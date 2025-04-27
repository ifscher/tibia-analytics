import streamlit as st
from utils.menu import menu
from utils.favicon import set_config
import pandas as pd

set_config(title="Cálculo de XP Base")

# Exibe o menu de navegação
menu()

st.title("Calculadora de Taxa de Experiência")
st.markdown("""
Esta calculadora permite visualizar o ganho percentual de experiência com diferentes 
modificadores. Selecione os modificadores ativos para ver o impacto na taxa de experiência.
""")

# Definir colunas para os modificadores
col1, col2 = st.columns(2)

with col1:
    # Selecionar modificadores
    xp_boost = st.selectbox("XP Boost (50%)", ["sim", "não"], index=1)
    xp_double = st.selectbox("XP Double (100%)", ["sim", "não"], index=1)
    world_quest = st.selectbox("World Quest (50%)", ["sim", "não"], index=1)
    prey_bonus = st.selectbox("Prey Bonus (40%)", ["sim", "não"], index=1)

with col2:
    # Opções adicionais
    stamina = st.selectbox("Stamina Verde (150%)", ["sim", "não"], index=0)

# Calcular os bônus de experiência
base_xp = 100  # XP base é sempre 100%
boost_value = 50 if xp_boost == "sim" else 0
double_value = 100 if xp_double == "sim" else 0
quest_value = 50 if world_quest == "sim" else 0
prey_value = 40 if prey_bonus == "sim" else 0
stamina_multiplier = 1.5 if stamina == "sim" else 1.0

# Cálculo da taxa final de XP
base_rate = (base_xp + boost_value + double_value) / 100
quest_rate = (base_xp + boost_value + double_value + quest_value) / 100
prey_rate = (base_xp + boost_value + double_value + quest_value + prey_value) / 100

# Aplicar multiplicador de stamina
base_with_stamina = base_rate * stamina_multiplier
quest_with_stamina = quest_rate * stamina_multiplier
prey_with_stamina = prey_rate * stamina_multiplier

# Criar tabela com os resultados
st.subheader("Taxas de Experiência Calculadas")

# Criar duas colunas para as tabelas
col1, col2 = st.columns(2)

with col1:
    # Tabela de configurações
    st.caption("Configurações Ativas")
    
    # Função para formatar o valor com cor
    def format_value(value, is_active):
        if is_active:
            return f'<span style="color: green;">{value}</span>'
        return value

    config_data = {
        "Modificador": ["XP Boost", "XP Double", "World Quest", "Prey Bonus", 
                        "Stamina Verde"],
        "Status": [xp_boost, xp_double, world_quest, prey_bonus, stamina],
        "Valor": [
            format_value(f"+{boost_value}%" if boost_value else "0%", xp_boost == "sim"),
            format_value(f"+{double_value}%" if double_value else "0%", xp_double == "sim"),
            format_value(f"+{quest_value}%" if quest_value else "0%", world_quest == "sim"),
            format_value(f"+{prey_value}%" if prey_value else "0%", prey_bonus == "sim"),
            format_value(f"x{stamina_multiplier}" if stamina_multiplier > 1 else "x1.0", stamina == "sim")
        ]
    }
    config_df = pd.DataFrame(config_data)
    st.write(config_df.to_html(escape=False, index=False), unsafe_allow_html=True)

with col2:
    # Tabela de resultados
    st.caption("Taxas Finais")
    
    # Função para formatar a taxa com cor se tiver stamina verde ativa
    def format_taxa(value):
        if stamina == "sim":
            return f'<span style="color: green;">{value}%</span>'
        return f"{value}%"

    results_data = {
        "Cenário": ["Na Skill Bar", "Na Prey"],
        "Taxa de XP": [
            format_taxa(int(base_with_stamina * 100)),
            format_taxa(int(prey_with_stamina * 100))
        ]
    }
    results_df = pd.DataFrame(results_data)
    st.write(results_df.to_html(escape=False, index=False), unsafe_allow_html=True)

# Exibir fórmulas
st.subheader("Fórmulas de Cálculo")

# Componente para base
base_components = []
base_components.append("1<sub>base</sub>")
if boost_value > 0:
    base_components.append(f"{boost_value/100}<sub>boost</sub>")
if double_value > 0:
    base_components.append(f"{double_value/100}<sub>double</sub>")

base_formula = (f"({' + '.join(base_components)}) × {stamina_multiplier}"
               f"<sub>stamina</sub> × 100% = {int(base_with_stamina * 100)}%")
st.markdown(f"**Base:** {base_formula}", unsafe_allow_html=True)

# Componente para world quest
if world_quest == "sim":
    quest_components = base_components.copy()
    quest_components.append(f"{quest_value/100}<sub>worldquest</sub>")
    
    quest_formula = (f"({' + '.join(quest_components)}) × {stamina_multiplier}"
                    f"<sub>stamina</sub> × 100% = {int(quest_with_stamina * 100)}%")
    st.markdown(f"**Com World Quest:** {quest_formula}", unsafe_allow_html=True)

# Componente para prey
if prey_bonus == "sim":
    prey_components = []
    prey_components.append("1<sub>base</sub>")
    if boost_value > 0:
        prey_components.append(f"{boost_value/100}<sub>boost</sub>")
    if double_value > 0:
        prey_components.append(f"{double_value/100}<sub>double</sub>")
    prey_components.append(f"{prey_value/100}<sub>prey</sub>")
    
    prey_formula = (f"({' + '.join(prey_components)}) × {stamina_multiplier}"
                   f"<sub>stamina</sub> × 100% = {int(prey_with_stamina * 100)}%")
    st.markdown(f"**Com Prey Bonus:** {prey_formula}", unsafe_allow_html=True)

# TODO: adicionar scrapping da exp de monstros, cálculo de XP/hora baseado na qtd de criaturas mortas
# TODO: dmg calculator 