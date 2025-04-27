from streamlit import set_page_config

def set_config(title, project="Tibia Analytics", show_logo=False, layout="centered"):
    """Configuração da página sem favicon."""
    set_page_config(
        page_title=f"{project} | {title}",
        layout=layout
    )