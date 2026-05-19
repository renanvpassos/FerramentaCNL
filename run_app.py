import streamlit.web.cli as stcli
import os
import sys

def resolve_path(path):
    """ Garante que o executável encontre o arquivo app.py mesmo em modo temporário """
    encoded_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(__file__)
    return os.path.join(encoded_path, path)

if __name__ == "__main__":
    # Configurações agressivas para rodar em computadores sem Python e sem internet
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("app.py"),
        "--global.developmentMode=false",
        "--server.port=8501",
        "--server.address=127.0.0.1",
        "--browser.gatherUsageStats=false",
        "--server.headless=true"
    ]
    sys.exit(stcli.main())