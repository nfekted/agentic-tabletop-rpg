# 🎲 Mesa de RPG — Painel do Mestre

Sistema que simula uma mesa de RPG cooperativo com agentes de IA: você é o
mestre, e cada jogador é conduzido por um agente com ficha, personalidade e
memória próprias. Existe uma interface visual (Streamlit) para quem não quer
mexer em terminal, e uma versão de terminal (`main.py`) equivalente para quem
preferir.

**Destaques**

- 🎭 Agentes com ficha, regras e memória individualizadas por personagem
- 🧠 Memória em três níveis (rodada → cena → mesa) que simula o esquecimento humano
- 💬 Respostas com intenção: `[fala]`, `[acao]`, `[duvida]` e `[pensamento]`
- 🔀 Escolha do modelo: Gemini 3.5, OpenAI Luna, Ollama ou Omniroute (local)
- 🖼️ Fotos para os jogadores e envio de imagens para contextualizar os agentes
- 💸 Prompt dividido em partes fixas e variáveis, com cache, para economizar tokens
- 🖥️ Interface visual em Streamlit + versão de terminal

---

## Índice

- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Ambiente virtual (.venv)](#ambiente-virtual-venv)
- [Configurando o modelo de IA e as chaves](#configurando-o-modelo-de-ia-e-as-chaves)
- [Como rodar](#como-rodar)
- [Funcionalidades](#funcionalidades)
  - [Fichas dos personagens](#fichas-dos-personagens)
  - [Conjuntos de regras (arquivos/regras/)](#conjuntos-de-regras-arquivosregras)
  - [Conjuntos de cenas (arquivos/cenas/)](#conjuntos-de-cenas-arquivoscenas)
  - [Ações do mestre](#ações-do-mestre)
  - [Tags de resposta: \[acao\], \[duvida\] e \[pensamento\]](#tags-de-resposta-acao-duvida-e-pensamento)
  - [Fluxo de aprovação](#fluxo-de-aprovação)
  - [Sistema de memória (rodada → cena → mesa)](#sistema-de-memória-rodada--cena--mesa)
  - [Por que resumir um resumo pode "perder" informação (de propósito)](#por-que-resumir-um-resumo-pode-perder-informação-de-propósito)
  - [Balões de fala](#balões-de-fala)
  - [Fotos dos jogadores](#fotos-dos-jogadores)
  - [Imagens de contexto](#imagens-de-contexto)
  - [Escolha do modelo de IA](#escolha-do-modelo-de-ia)
  - [Cache de prompt (economia de tokens)](#cache-de-prompt-economia-de-tokens)
  - [Adicionando jogadores](#adicionando-jogadores)
- [Estrutura de pastas](#estrutura-de-pastas)
- [Solução de problemas](#solução-de-problemas)

---

## Pré-requisitos

Você precisa ter **Python 3.10 ou superior** instalado. Para verificar se já
tem:

```bash
python --version
# ou, em alguns sistemas:
python3 --version
```

Se aparecer algo como `Python 3.11.x`, já está pronto — pule para
[Instalação](#instalação). Se der erro de "comando não encontrado", siga o
passo de instalação do seu sistema abaixo.

### Windows

1. Baixe o instalador em <https://www.python.org/downloads/windows/>.
2. Ao instalar, **marque a caixa "Add Python to PATH"** na primeira tela do
   instalador — isso evita ter que configurar variáveis de ambiente na mão.
3. Confirme no PowerShell ou Prompt de Comando:
   ```powershell
   python --version
   ```

### macOS

O jeito mais simples é via [Homebrew](https://brew.sh/):

```bash
brew install python
```

Sem Homebrew, baixe o instalador em
<https://www.python.org/downloads/macos/>.

### Linux

Na maioria das distros o Python já vem instalado. Se precisar instalar (ou
atualizar), em distros baseadas em Debian/Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

Em Fedora:

```bash
sudo dnf install python3 python3-pip
```

---

## Instalação

1. Baixe/clone este repositório e entre na pasta:
   ```bash
   git clone https://github.com/nfekted/agentic-tabletop-rpg
   cd agentic-tabletop-rpg
   ```

2. Crie e ative um ambiente virtual (recomendado — veja a seção
   [Ambiente virtual (.venv)](#ambiente-virtual-venv) logo abaixo).

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

---

## Ambiente virtual (.venv)

Um ambiente virtual isola as bibliotecas do projeto do resto do seu
computador, evitando conflitos de versão. É opcional, mas recomendado.

### Criar (só na primeira vez)

```bash
python -m venv .venv        # Windows
python3 -m venv .venv       # macOS/Linux
```

### Ativar (toda vez que abrir um terminal novo)

| Sistema | Terminal | Comando |
|---|---|---|
| Windows | PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows | Prompt de Comando (cmd) | `.venv\Scripts\activate.bat` |
| macOS / Linux | bash / zsh | `source .venv/bin/activate` |

Quando estiver ativo, o terminal mostra `(.venv)` no começo da linha. Só
então rode `pip install -r requirements.txt` e os comandos de
[Como rodar](#como-rodar).

Para desativar: `deactivate`.

### Se a ativação der erro

**Windows — "a execução de scripts foi desabilitada neste sistema"**
O PowerShell bloqueia scripts por padrão. Libere só para o seu usuário
(sem precisar de administrador):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Confirme com `S` e rode o comando de ativação de novo. Se preferir não mexer
nessa configuração, use o **Prompt de Comando (cmd)** com o `activate.bat`.

**Linux (Debian/Ubuntu) — "ensurepip is not available" ou o `.venv` não é criado**
Falta o módulo de venv:

```bash
sudo apt install python3-venv
```

Apague a pasta `.venv` incompleta (`rm -rf .venv`) e crie de novo.

**"python: comando não encontrado" ao criar o venv**
Use `python3` em vez de `python` (macOS/Linux), ou reinstale o Python no
Windows marcando "Add Python to PATH".

**O ambiente ativou, mas o app diz que uma biblioteca não existe**
Você provavelmente instalou as dependências fora do venv. Com o `(.venv)`
ativo, rode `pip install -r requirements.txt` novamente.

---

## Configurando o modelo de IA e as chaves

O projeto suporta vários provedores de modelo (veja
[Escolha do modelo de IA](#escolha-do-modelo-de-ia)). Chaves e endereços
ficam num arquivo **`.json`**, que nunca deve ser versionado. Como é local
manter em .env ou em arquivo não impacta diretamente na segurança. Manualmente
fica em /arquivos/config.json, no formato:

```
{
  "provedor": "omniroute-local", (ou llama3, gpt-luna, gemini-3.5-flash)
  "api_key": "", <ou key>
  "base_url": "http://localhost:8000/v1" <ou "">
}
```
## Configurar seu modelo:

### Gemini 3.5-flash

1. Acesse o **[Google AI Studio](https://aistudio.google.com/)**.
2. Faça login com sua conta do Google.
3. No menu lateral ou no painel principal, clique em **Get API key** (Obter chave de API).
4. Clique em **Create API key** (Criar chave de API).
   - *Você pode associar a chave a um projeto existente do Google Cloud ou criar um novo automaticamente.*
5. Copie a chave gerada.

### OpenAI Luna

1. Acesse a plataforma de desenvolvedores no **[OpenAI Platform](https://platform.openai.com/)**.
2. Faça login com sua conta da OpenAI.
3. No painel de navegação, vá até a seção **API Keys** (ou acesse diretamente `platform.openai.com/api-keys`).
4. Clique em **Create new secret key** (Criar nova chave secreta).
5. Dê um nome para a chave (opcional) e clique em **Create secret key**.
6. Copie a chave gerada imediatamente (ela não será exibida novamente).

### Ollama (Modelo local)

O **Ollama** permite rodar modelos de linguagem (como Llama 3, Mistral, Gemma) diretamente na sua máquina local de forma simples e gratuita.

1. **Instalação:** Baixe e instale o executável para o seu sistema operacional diretamente do site oficial:
   - 🔗 **Guia Oficial e Downloads:** [ollama.com](https://ollama.com)
   - 💻 **Repositório GitHub:** [github.com/ollama/ollama](https://github.com/ollama/ollama)
2. **Baixar e Rodar um Modelo:** Abra o seu terminal e execute o comando abaixo para baixar e rodar um modelo (ex: Llama 3):
   ```bash
   ollama run llama3
   ```

### Omniroute

O **Omniroute** é um roteador/gateway de APIs de LLM que permite alternar e gerenciar chamadas entre múltiplos provedores (OpenAI, Anthropic, Gemini, Ollama local) através de uma interface ou endpoint unificado.
Acesse o repositório oficial do projeto no GitHub para o passo a passo completo de instalação e configuração de rotas: [omniroute](github.com/omniroute/omniroute)

---

## Como rodar

Com o ambiente virtual ativo (se estiver usando um):

**Interface visual (recomendada):**
```bash
streamlit run app.py
```
Isso abre a mesa automaticamente no navegador (geralmente em
`http://localhost:8501`).

**Modo terminal (menu por texto):**
```bash
python main.py      # Windows
python3 main.py     # macOS/Linux
```

Para encerrar qualquer um dos dois, use `Ctrl+C` no terminal.

---

## Funcionalidades

### Fichas dos personagens

Cada jogador tem um arquivo de ficha em `arquivos/fichas/{nome_do_jogador}.txt`, que
descreve personalidade, história e características do personagem — é isso
que molda como o agente de IA responde por ele. Pela interface, clique no
botão ✏️ no card do jogador para editar e salvar a ficha sem precisar abrir
nenhum arquivo manualmente. A primeira linha da ficha também guarda o
status do personagem (`vivo`, `morto` ou `inconsciente`), controlado pelo
seletor abaixo do card.

### Conjuntos de regras (arquivos/regras/)

É possível ter **vários conjuntos de regras** (por exemplo `geral.txt`,
`combate.txt`, `exploracao.txt`) — mas só o **conjunto marcado como ativo**
é enviado no prompt de cada jogador. Isso evita gastar tokens à toa
mandando regras de combate durante uma cena de exploração (ou vice-versa).

Pela barra lateral você pode:
- **Trocar rapidamente** o conjunto ativo num seletor direto, sem abrir
  nenhum painel — ideal para alternar entre "exploração" e "combate" no
  meio de uma cena.
- Clicar em **"✏️ Gerenciar / Criar Regras"** para abrir o painel completo,
  onde dá para editar o conteúdo de um conjunto existente, marcar outro
  como ativo, **criar** um conjunto novo (vazio, para você preencher) ou
  **excluir** um conjunto (não é possível excluir o único restante).

### Conjuntos de cenas (arquivos/cenas/)

É possível criar cenas pré-cadastradas para reutilizar em diversos agentes ou
agilizar um NPC, em exemplo: Lista de itens em uma loja.
Ao lado das [Ações do mestre](#ações-do-mestre) é possível selecionar, excluir,
ou criar uma nova cena.

As cenas são salvas em `arquivos/cenas/`.

### Ações do mestre

- **Iniciar Rodada** — abre uma rodada de jogo; a partir daqui, tudo que
  acontece é registrado na memória temporária de cada jogador envolvido.
- **Finalizar Rodada** — fecha a rodada atual e manda o conteúdo para o
  "historiador" resumir (ver [Sistema de memória](#sistema-de-memória-rodada--cena--mesa)).
- **Falar com Todos (Público)** — sua mensagem e a reação de cada jogador
  vivo ficam visíveis para todos, sem necessidade de aprovação individual.
- **Falar com Jogador(es) Específico(s) [Cena Pública]** — você se dirige a
  um ou mais jogadores; a resposta do primeiro selecionado passa por
  aprovação antes de ser considerada "dita" na cena.
- **Cena Privada** — igual à anterior, mas o registro na memória de longo
  prazo fica restrito só a quem está na cena, em vez de ir para todos os
  jogadores da mesa. É assim que segredos ficam guardados entre os
  personagens.

### Tags de resposta: [fala], [acao], [duvida] e [pensamento]

O modelo é instruído a começar a resposta com uma dessas tags quando for o
caso:

| Tag | O que significa | O que acontece depois |
|---|---|---|
| `[acao]` | O personagem está realizando uma ação | A ação é considerada resolvida; ninguém reage automaticamente |
| `[duvida]` | O personagem quer perguntar algo a outro jogador presente | Você escolhe para quem redirecionar a pergunta; a resposta de quem foi escolhido também passa por aprovação |
| `[pensamento]` | Um pensamento interno que o personagem **não diz em voz alta** | Nunca é mostrado a outros jogadores nem entra no histórico compartilhado da cena — fica só na memória privada daquele personagem |
| *(nenhuma tag)* ou `[fala]` | Fala/reação social comum | Os demais jogadores presentes reagem automaticamente com uma opinião breve |

### Fluxo de aprovação

Sempre que um jogador responde a uma fala direcionada a ele (não no "Falar
com Todos"), a resposta aparece com dois botões: **✅ Aprovar/Espelhar** e
**❌ Descartar**. Só depois de aprovada ela entra de fato na história e na
memória — isso te dá controle para pedir uma nova resposta ou simplesmente
recusar algo que não fez sentido, antes que vire "fato" na campanha.

### Sistema de memória (rodada → cena → mesa)

Cada jogador tem sua própria pasta `arquivos/memoria_{nome}/`, com uma hierarquia de
três níveis — a memória é **individual**: cada personagem só lembra do que
presenciou.

1. **Rodada** — enquanto a rodada está aberta, cada linha relevante é
   gravada em `rodada_atual_temp.txt`. Ao clicar em "Finalizar Rodada", o
   historiador (um modelo de IA à parte, com temperatura mais baixa e
   focado em resumir) lê esse arquivo e grava um resumo conciso em
   `rodada_N.txt`.
2. **Cena** — ao acumular **10 arquivos de rodada**, eles são sintetizados
   em uma narrativa fluida única: `cena_N.txt`. Os 10 arquivos de rodada
   que originaram essa cena são apagados depois da compilação.
3. **Mesa** — ao acumular **10 cenas**, elas são consolidadas em um novo
   "capítulo" append no `mesa.txt` — o histórico permanente daquele
   personagem. As 10 cenas usadas são apagadas depois.

Toda vez que um jogador é chamado a responder, o prompt dele é montado com
o conteúdo de `mesa.txt` + cenas ainda não compiladas + rodadas ainda não
compiladas — ou seja, ele "lembra" de tudo isso antes de agir.

Pela interface, o botão de leitura no card do jogador abre os arquivos de
rodadas, cenas e `mesa.txt` dele em modo somente leitura.

### Por que resumir um resumo pode "perder" informação (de propósito)

Repare que cada nível dessa hierarquia é um **resumo feito em cima de
resumos anteriores**, não do texto bruto original:

- a `cena_N.txt` é gerada a partir de 10 `rodada_N.txt` (que já são, cada
  uma, um resumo da rodada bruta);
- o capítulo do `mesa.txt` é gerado a partir de 10 `cena_N.txt` (que já são
  resumos de resumos).

Isso significa que, a cada nível, detalhes menores tendem a ser
comprimidos, generalizados ou até reinterpretados pelo modelo que resume —
exatamente como acontece com a memória humana: você lembra bem do que
aconteceu ontem, tem uma lembrança mais "editada" do mês passado e guarda
só os pontos marcantes de um evento de anos atrás. **Isso é um
comportamento intencional do design**, não um bug: dá aos personagens uma
memória falível, o que enriquece o roleplay (um jogador pode "esquecer" um
detalhe específico, lembrar errado de algo, ou reagir de forma diferente à
medida que a lembrança de um evento vai sendo reprocessada).

Na prática, isso quer dizer:
- Não espere que o `mesa.txt` funcione como um log literal e completo da
  campanha — para isso, o ideal é guardar os arquivos de `rodada_N.txt`
  originais em outro lugar antes que sejam apagados na compilação, se você
  quiser um registro fiel.
- Quanto mais rodadas/cenas se acumulam, mais "resumida" (e potencialmente
  imprecisa) fica a lembrança de acontecimentos antigos — é esperado, e faz
  parte da proposta do sistema simular como uma pessoa recorda o passado.

### Balões de fala

Cada card de jogador mostra um balão com a última fala dele:
- **Cinza sólido** — fala já aprovada e registrada na história.
- **Amarelo tracejado** — resposta gerada, ainda aguardando sua aprovação.
- **Roxo em itálico (💭)** — um `[pensamento]` privado; só o mestre vê esse
  balão, e ele nunca é compartilhado com os outros personagens.

### Fotos dos jogadores

No lugar do quadrado com as iniciais, você pode enviar uma foto para cada
jogador pelo botão 🖼️ no card, o que ajuda a identificar cada personagem
rapidamente na mesa. A imagem fica salva dentro da própria pasta de memória
do personagem (`arquivos/memoria_{nome}/avatar.<extensão>`).

### Imagens de contexto

Além das fotos de identificação, você pode **enviar imagens para
contextualizar os agentes** — um mapa, a foto de um monstro, a planta de uma
taverna, uma ilustração da cena. A imagem é enviada junto ao prompt, e os
jogadores passam a reagir ao que "estão vendo". Os arquivos ficam salvos em
`arquivos/img/`.

> ⚠️ Só modelos com suporte a imagem (visão) conseguem interpretá-las. Se
> você usar um modelo local (Ollama/Omniroute), confirme que o modelo
> escolhido aceita imagens.

### Escolha do modelo de IA

Os modelos são definidos em `config.py`, e você pode escolher qual usar:

| Provedor | Onde roda | O que precisa |
|---|---|---|
| **Gemini 3.5** (Google) | Nuvem | `GOOGLE_API_KEY` |
| **OpenAI Luna** | Nuvem | `OPENAI_API_KEY` |
| **Ollama** | Local (seu computador) | Ollama instalado e rodando, com o modelo já baixado |
| **Omniroute** | Local | Servidor Omniroute rodando e acessível |

Modelos locais não cobram por token e mantêm tudo no seu computador, mas a
qualidade e a velocidade dependem do seu hardware e do modelo escolhido.

### Cache de prompt (economia de tokens)

O prompt de cada jogador é **separado em blocos**: o que muda pouco (ficha,
regras ativas, instruções gerais, memória já consolidada) fica separado do
que muda a cada mensagem (a fala do mestre, o que acabou de acontecer na
cena). Como a parte estável se repete a cada chamada, os provedores que
suportam cache de prompt conseguem reaproveitá-la em vez de reprocessá-la
inteira, o que reduz o consumo de tokens e o custo.

Isso também é um dos motivos de existir o conjunto de regras ativo
([veja acima](#conjuntos-de-regras-arquivosregras)): mandar só as regras
relevantes deixa o prompt menor e mais estável.

### Adicionando jogadores

A lista de jogadores não é fixa. Pela barra lateral, em "➕ Adicionar
Jogador", digite um nome (sem espaços) e clique em Adicionar — o card dele
já aparece na fila junto com os demais, sem precisar reiniciar o app.

---

## Estrutura de pastas

```
.
├── app.py                 # Interface visual (Streamlit)
├── main.py                # Interface de terminal (menu por texto)
├── config.py               # Modelos de IA e configurações
├── fichas.py                # Leitura/edição de fichas e regras
├── imagens.py                # Upload de imagens de contexto e fotos de jogador
├── memoria.py                 # Hierarquia de memória rodada → cena → mesa
├── agentes.py                  # Monta o prompt e gera as respostas dos jogadores
├── ui/                          # Partes da interface Streamlit separadas por lógica
│   └── ...                        # (ex.: barra lateral em arquivo próprio)
├── requirements.txt
├── .venv/                  # Ambiente virtual (não versionar)
├── .env                    # Suas chaves de API (não versionar)
└── arquivos/               # Pasta centralizadora de dados e mídias
    ├── jogadores.json          # Lista centralizada de jogadores da mesa
    ├── regras/                 # Conjuntos de regras (um arquivo por cenário)
    │   ├── .ativa               # Marca qual arquivo está em uso agora
    │   ├── geral.txt
    │   └── combate.txt
    ├── fichas/
    │   ├── jogadora.txt
    │   ├── jogadorb.txt
    │   └── ...
    ├── img/
    │   └── ...
    └── memoria_JogadorA/
        ├── rodada_atual_temp.txt
        ├── rodada_1.txt
        ├── cena_1.txt
        ├── mesa.txt
        └── avatar.png
```

---

## Solução de problemas

**`ValidationError: API key required for Gemini Developer API`**
O `config.json` não foi encontrado ou a variável está com nome/formato errado.
Confira se o arquivo se chama exatamente `config.json`, está na mesma pasta 
, e contém `api_key` e o provedor. Depois, reinicie o
Streamlit por completo (`Ctrl+C` e rode `streamlit run app.py` de novo) 
Confirme o cadastro pelas configurações do painel.

**Erro de chave inválida ou ausente com OpenAI**
Mesma lógica para o gemini.

**Ollama/Omniroute: "connection refused" ou timeout**
O servidor local não está rodando (ou está em outra porta). Inicie o
Ollama/Omniroute antes do app, confirme o endereço configurado e, no caso do
Ollama, se o modelo já foi baixado (`ollama pull <modelo>`).

**O agente ignora a imagem que enviei**
O modelo escolhido pode não suportar imagens. Troque para um modelo com
visão ou descreva a cena em texto.

**`ModuleNotFoundError` ao rodar o app**
Provavelmente o ambiente virtual não está ativo, ou as dependências foram
instaladas fora dele. Ative o `.venv` e rode `pip install -r requirements.txt`
de novo (veja [Ambiente virtual](#ambiente-virtual-venv)).

**Nenhum jogador aparece na tela**
Confira se `arquivos/jogadores.json` tem pelo menos um nome na lista, ou
adicione um novo jogador pela barra lateral.

**A ficha ou as regras aparecem vazias**
Isso é normal se ainda não foram salvas nenhuma vez pela interface — clique
em ✏️ Ficha (para a ficha) ou em "✏️ Gerenciar / Criar Regras" na barra
lateral (para as regras), escreva o conteúdo e salve.

**Criei um novo conjunto de regras e ele não afeta as respostas dos jogadores**
Criar um arquivo em `arquivos/regras/` não o torna automaticamente ativo. Depois de
escrever o conteúdo, clique em "⭐ Usar agora" (no painel) ou selecione-o no
seletor rápido da barra lateral — só o conjunto marcado como ativo é
enviado no prompt dos jogadores.