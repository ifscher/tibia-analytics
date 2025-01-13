from streamlit import logo, set_page_config


PROJECT_NAME = "Tibia Analytics"
LOGO_FULL = "utils/favicon/logo_full.png"
LOGO_SHORT = "utils/favicon/logo_short.png"
LOGO_FULL_NEGATIVO = "utils/favicon/logo_full_negativo.png"
LOGO_SHORT_NEGATIVO = "utils/favicon/logo_short_negativo.png"


def set_config(title, project=PROJECT_NAME, show_logo=True):
    """Set logo."""

    if show_logo:
        logo(image=LOGO_FULL_NEGATIVO, size='large', icon_image=LOGO_SHORT_NEGATIVO)
    set_page_config(
        page_title=f"{project} | {title}",
        page_icon="utils/favicon/favicon.ico"
    )