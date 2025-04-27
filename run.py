#!/usr/bin/env python
import os
import subprocess
import sys

def main():
    """Inicia a aplicação Tibia Analytics."""
    print("Iniciando Tibia Analytics...")
    
    # Verifica se streamlit está instalado
    try:
        import streamlit
        print(f"Streamlit versão {streamlit.__version__} encontrado.")
    except ImportError:
        print("Streamlit não encontrado. Instalando dependências...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Inicia o aplicativo
    os.environ["STREAMLIT_SERVER_RUN_ON_SAVE"] = "true"
    subprocess.call([sys.executable, "-m", "streamlit", "run", "app.py"])

if __name__ == "__main__":
    main() 