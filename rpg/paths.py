# Caminhos absolutos dos dados, ancorados na raiz do projeto: não dependem do diretório atual.
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVOS = os.path.join(RAIZ, "arquivos")
TOKENS = os.path.join(RAIZ, "tokens")
MESAS = os.path.join(RAIZ, "mesas")
