import streamlit as st
from utils.menu import menu
from utils.favicon import set_config


set_config(title="Login", show_logo=False)

menu()

# Here goes your normal streamlit app
st.title("This page is available to all users")
st.markdown(f"You are currently logged with the role of {st.session_state.role}.")