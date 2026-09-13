# Agentic Tabletop RPG

Projeto feito para aqueles que não tem uma galera para jogar aquele RPG de mesa, configure o resumo das regras, faça as fichas de personagens, conecte o agente, e deixe a mesa começar.

## Como rodar

1. Coloque todos os arquivos (`app.py`, `main.py`, `config.py`, `fichas.py`,
   `imagens.py`, `memoria.py`, `agentes.py`, `requirements.txt`) na mesma pasta
   do seu projeto atual (onde já ficam `regras_rpg.txt`, a pasta `fichas/` e a
   pasta `img/`).
2. Crie um arquivo `.env` na mesma pasta com sua chave do Google:
   ```
   GEMINI_API_KEY=sua_chave_aqui
   ```
3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
4. Rode a interface visual:
   ```
   streamlit run app.py
   ```