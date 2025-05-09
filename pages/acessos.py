import streamlit as st
from utils.menu import menu_with_redirect
from utils.favicon import set_logo


set_logo()
st.set_page_config(
    page_title="Quant Analytics | Acessos",
    page_icon="🕸"
)

# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

st.title("This page is available to all users")
st.markdown(f"You are currently logged with the role of {st.session_state.role}.")