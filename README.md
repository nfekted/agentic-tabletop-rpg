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
- ⚔️ Modo por Turnos: gestão de cenas e combate com áreas, ordem de iniciativa e tokens
- 🧠 Controle de contexto: barra por personagem e compressão de memória com roleplay
- 💾 Salvar / Restaurar Mesa: backup completo da campanha em um `.zip`
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
  - [Conjunto de tokens](#conjunto-de-tokens)
  - [Modo por Turnos](#modo-por-turnos)
  - [Ações do mestre](#ações-do-mestre)
  - [Tags de resposta: \[acao\], \[duvida\] e \[pensamento\]](#tags-de-resposta-acao-duvida-e-pensamento)
  - [Fluxo de aprovação](#fluxo-de-aprovação)
  - [Sistema de memória (rodada → cena → mesa)](#sistema-de-memória-rodada--cena--mesa)
  - [Por que resumir um resumo pode "perder" informação (de propósito)](#por-que-resumir-um-resumo-pode-perder-informação-de-propósito)
  - [Controle de contexto e compressão de memória](#controle-de-contexto-e-compressão-de-memória)
  - [Balões de fala](#balões-de-fala)
  - [Fotos dos jogadores](#fotos-dos-jogadores)
  - [Imagens de contexto](#imagens-de-contexto)
  - [Escolha do modelo de IA](#escolha-do-modelo-de-ia)
  - [Cache de prompt (economia de tokens)](#cache-de-prompt-economia-de-tokens)
  - [Adicionando jogadores](#adicionando-jogadores)
  - [Salvar / Restaurar Mesa](#salvar--restaurar-mesa)
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
  "provedor": "Omniroute local",   (ou "Gemini 3.5-flash", "GPT-luna", "Ollama local")
  "api_key": "",                   (sua chave, se o provedor exigir)
  "base_url": "http://localhost:8000/v1",   (ou "")
  "limite_contexto_tokens": 0,     (0 = controle de contexto desligado)
  "gatilho_compressao_pct": 85,
  "alvo_reducao_pct": 50
}
```
Tudo isso também pode ser editado pela barra lateral, em **⚙️ Configurações da
LLM** — não é preciso mexer no arquivo na mão. Os três últimos campos são
explicados em [Controle de contexto](#controle-de-contexto-e-compressão-de-memória).
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

Cada jogador tem uma **ficha modular** em `arquivos/fichas/`, dividida em
seis arquivos por personagem: `{nome}_base.txt`, `{nome}_geral.txt`,
`{nome}_habilidades.txt`, `{nome}_itens.txt`, `{nome}_personalidade.txt` e
`{nome}_status.json`. É isso que molda como o agente de IA responde por
ele. Pela interface, clique em ✏️ no card do jogador para editar cada
seção sem abrir arquivo nenhum; o botão 👁️ mostra a ficha consolidada em
modo somente leitura. Fichas antigas (um único `{nome}.txt`) são migradas
automaticamente.

- **Status dinâmicos** (vida, mana, estamina, ...): você cria quantos quiser,
  com valor atual, máximo e cor. Aparecem como barras no card e entram no
  prompt do agente.
- **Modificadores**: um campo de texto livre exibido no card ("modificadores:
  ...").

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

### Conjunto de tokens

É possível registrar anotações de inimigos, NPCs e itens em `tokens/`
(subpastas `inimigo/`, `npc/` e `item/`), pelo botão **👾 Gerenciar Inimigos,
Itens e NPCs** da barra lateral. Ajuda a ter tudo à mão sem buscar em
blocos de notas, e dá para deixar já em formato de prompt, para apenas
copiar e colar na mensagem ou na ficha do personagem. Os tokens também são
usados no [Modo por Turnos](#modo-por-turnos).

### Modo por Turnos

Pelo botão **⚔️ Iniciar Modo por Turnos** (abaixo dos cards de jogadores) a
tela vira um painel de gestão de cenas e combate. O estado fica em
`arquivos/turno.json`.

- **Personagens e Tokens** soltos aparecem em duas colunas; tokens são
  adicionados de `tokens/` como **cópias isoladas** para o combate (editar a
  ficha do token ali não altera o arquivo original).
- **Áreas da Cena**: crie zonas (Entrada, Salão, ...) e vincule participantes
  a elas. Dentro da área, cada personagem aparece em formato compacto
  (inline), com status, barra de contexto e balão de fala logo acima.
- **Ordem de iniciativa**: defina a ordem de cada participante; o painel
  avisa empates e trava a ordem durante a rodada.
- **Iniciar Combate / Próxima Ação**: destaca de quem é a vez (🔥) e avança
  pela fila.
- **Encerrar Modo por Turnos** volta para a tela normal.

### Ações do mestre

- **Iniciar Rodada** — abre uma rodada de jogo; a partir daqui, tudo que
  acontece é registrado na memória temporária de cada jogador envolvido.
- **Cancelar Rodada** - Rever a rodada iniciada, movendo todas memórias para uma pasta de logs junto a um motivo.
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

Esse ciclo automático continua valendo; além dele, existe a
[compressão manual](#controle-de-contexto-e-compressão-de-memória), oferecida
quando o prompt do personagem se aproxima do limite da LLM.

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

### Controle de contexto e compressão de memória

Como a memória só cresce e é reenviada em todo prompt, dá para dizer ao jogo
o tamanho da janela da sua LLM e deixá-lo avisar quando um personagem está
perto do limite. Em **⚙️ Configurações da LLM** (cada campo tem um "?" com a
explicação):

| Campo | O que faz |
|---|---|
| **Contexto máx. (tokens)** | Limite da LLM (consulte a documentação do modelo). **0 desliga** o controle. |
| **Gatilho de compressão (%)** | Quanto do contexto pode estar ocupado antes de o jogo oferecer a compressão (padrão 85%). |
| **Tamanho alvo (% de redução)** | Quanto do `mesa.txt` será cortado ao comprimir (padrão 50%). |

**Medição.** A cada resposta, o jogo grava em
`arquivos/memoria_{nome}/metricas.json` quantos tokens o último prompt usou
(valor real do provedor quando informado; senão, estimado por caracteres) e
quanto cada parte pesou (prompt base, regras, memória, ficha, histórico).
Nada disso entra no prompt.

**Barra 🧠 Contexto.** Aparece nos cards (completo, compacto e inline no
Modo por Turnos): verde abaixo de 60%, âmbar até o gatilho e vermelho depois,
com um traço marcando o gatilho. Passe o mouse para ver o detalhamento.

**Compressão.** Ao passar do gatilho, abre um diálogo em roleplay
("*{personagem} está com muitas coisas na cabeça…*") perguntando se deseja
comprimir. Você decide: **Não** apenas fecha (pergunta de novo no próximo
input); **Sim** executa, na ordem:

1. as rodadas pendentes viram uma cena;
2. o `mesa.txt` atual é reduzido pelo percentual alvo (o prompt do resumo
   recebe "o limite máximo de caracteres é N");
3. o resumo das cenas é anexado ao `mesa.txt` reduzido.

A memória antiga perde detalhe (aceitável), e a recente fica mais completa.
Antes de reduzir, o `mesa.txt` é copiado para `mesa.bak` e restaurado se algo
falhar. Se o peso do contexto estiver em regras/ficha/histórico e não na
memória, o diálogo apenas avisa, sem oferecer compressão.

### Balões de fala

Cada card de jogador (na tela principal e no Modo por Turnos) mostra um
balão com a última fala dele:
- **Cinza sólido** — fala já aprovada e registrada na história.
- **Amarelo tracejado** — resposta gerada, ainda aguardando sua aprovação.
- **Roxo em itálico (💭)** — um `[pensamento]` privado; só o mestre vê esse
  balão, e ele nunca é compartilhado com os outros personagens.

O balão **cresce conforme o tamanho da resposta** (com rolagem para textos
muito longos). No Modo por Turnos, cards inline mostram o balão **logo acima**
do card. O **✖** fecha o balão só visualmente — a fala continua guardada — e
o botão **💬 Restaurar última fala** a traz de volta. Uma fala nova reabre o
balão sozinha.

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

Os provedores são definidos em `config.py`; o escolhido fica em
`arquivos/config.json` e pode ser trocado pela barra lateral:

| Provedor | Onde roda | O que precisa |
|---|---|---|
| **Gemini 3.5** (Google) | Nuvem | API Key (pela barra lateral, ou a variável `GEMINI_API_KEY`) |
| **OpenAI Luna** | Nuvem | API Key (pela barra lateral, ou a variável `OPENAI_API_KEY`) |
| **Ollama** | Local (seu computador) | Ollama instalado e rodando, com o modelo já baixado |
| **Omniroute** | Local | Servidor Omniroute rodando e acessível |

Modelos locais não cobram por token e mantêm tudo no seu computador, mas a
qualidade e a velocidade dependem do seu hardware e do modelo escolhido.

### Cache de prompt (economia de tokens)

O prompt de cada jogador é **separado em blocos, do mais estável ao mais
volátil**: instruções gerais, regras ativas, memória e ficha vêm primeiro;
o que muda a cada mensagem (histórico da rodada e a fala do mestre) vem por
último. Provedores com cache automático de prefixo conseguem reaproveitar a
parte estável em vez de reprocessá-la inteira, reduzindo custo e latência.
(O projeto não marca blocos de cache explicitamente; o ganho depende do
provedor.)

Isso também é um dos motivos de existir o conjunto de regras ativo
([veja acima](#conjuntos-de-regras-arquivosregras)): mandar só as regras
relevantes deixa o prompt menor e mais estável.

### Adicionando jogadores

A lista de jogadores não é fixa. Pela barra lateral, em "➕ Adicionar
Jogador", digite um nome (sem espaços) e clique em Adicionar — o card dele
já aparece na fila junto com os demais, sem precisar reiniciar o app.

### Salvar / Restaurar Mesa

O botão **💾 Salvar / Restaurar Mesa** da barra lateral abre um modal com
duas partes:

- **Salvar mesa** (direita): digite um nome e clique em Salvar. O jogo gera
  `mesas/{nome}.zip` com `arquivos/` e `tokens/` (fichas, regras, cenas,
  imagens, memórias, jogadores e o estado do combate).
- **Restaurar mesa** (esquerda): escolha um `.zip` de `mesas/`, clique em
  Restaurar e confirme. `arquivos/` e `tokens/` atuais são **substituídos**
  pelo conteúdo do zip e a tela recarrega sozinha.

Detalhes importantes:
- O `config.json` **não entra no zip** (ele guarda a API Key). Ao restaurar,
  a configuração atual da LLM é mantida; se mudar de máquina, reconfigure a
  chave. Guarde-a em local seguro.
- Rodadas em andamento (`rodada_atual_temp.txt`) não são salvas, e o estado da
  sessão (histórico da rodada, falas, pendências de aprovação) é limpo ao
  restaurar.
- O zip é validado antes de qualquer alteração e a troca é feita com
  rollback: se algo falhar, os dados atuais permanecem.

---

## Estrutura de pastas

```
.
├── app.py                  # Interface visual (Streamlit)
├── main.py                 # Interface de terminal (menu por texto)
├── config.py               # Provedores de IA, configurações e jogadores
├── fichas.py               # Fichas modulares e conjuntos de regras
├── imagens.py              # Upload de imagens de contexto e fotos de jogador
├── memoria.py              # Memória rodada → cena → mesa e compressão manual
├── metricas.py             # Tokens/contexto do último prompt por personagem
├── agentes.py              # Monta o prompt e gera as respostas dos jogadores
├── tags.py                 # Extração de [fala], [acao], [duvida], [pensamento]
├── cenas.py                # Cenas pré-cadastradas
├── tokens_manager.py       # Inimigos, NPCs e itens (pasta tokens/)
├── turno.py                # Regras e persistência do Modo por Turnos
├── mesas_manager.py        # Salvar/restaurar mesa em .zip
├── ui/                     # Partes da interface Streamlit
│   ├── sidebar.py          # Barra lateral (LLM, rodada, regras, mesa)
│   ├── jogadores.py        # Cards de jogadores
│   ├── turno_panel.py      # Painel do Modo por Turnos
│   ├── balao.py            # Balão de fala reutilizável (com ✖)
│   ├── contexto_barra.py   # Barra 🧠 Contexto
│   ├── compressao_panel.py # Diálogo de compressão de memória
│   ├── mesas_panel.py      # Modal Salvar / Restaurar Mesa
│   └── ...                 # fichas, regras, memória, avatar, tokens, ações
├── requirements.txt
├── .venv/                  # Ambiente virtual (não versionar)
├── .env                    # Suas chaves de API (não versionar)
├── mesas/                  # Backups .zip gerados por "Salvar mesa"
├── tokens/                 # Anotações de inimigos, NPCs e itens
│   ├── inimigo/
│   ├── npc/
│   └── item/
└── arquivos/               # Pasta centralizadora de dados e mídias
    ├── config.json             # Provedor, chave, limites de contexto
    ├── jogadores.json          # Lista centralizada de jogadores da mesa
    ├── turno.json              # Estado do Modo por Turnos (se ativo)
    ├── regras/                 # Conjuntos de regras (um arquivo por cenário)
    │   ├── .ativa               # Marca qual arquivo está em uso agora
    │   ├── geral.txt
    │   └── combate.txt
    ├── fichas/                 # Seis arquivos modulares por personagem
    │   ├── jogadora_base.txt
    │   ├── jogadora_status.json
    │   └── ...
    ├── cenas/                  # Cenas pré-cadastradas
    ├── img/
    │   └── ...
    └── memoria_JogadorA/
        ├── rodada_atual_temp.txt
        ├── rodada_1.txt
        ├── cena_1.txt
        ├── mesa.txt
        ├── mesa.bak            # Cópia antes da última compressão
        ├── metricas.json       # Medição de contexto (não vai no prompt)
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

**A barra 🧠 Contexto não aparece**
O controle fica desligado com **Contexto máx. = 0**. Defina o limite em
⚙️ Configurações da LLM e faça uma chamada a um jogador: a barra só existe
depois da primeira medição daquele personagem.

**O valor da barra está marcado como "estimado"**
O provedor não informou `usage_metadata`; o jogo estima tokens pelo número
de caracteres (≈3 por token) e recalibra quando o provedor informa o valor
real.

**Restaurei uma mesa e a IA parou de responder**
O `config.json` não vai no backup. Confira em ⚙️ Configurações da LLM se a
API Key e o provedor estão preenchidos.

**A ficha ou as regras aparecem vazias**
Isso é normal se ainda não foram salvas nenhuma vez pela interface — clique
em ✏️ Ficha (para a ficha) ou em "✏️ Gerenciar / Criar Regras" na barra
lateral (para as regras), escreva o conteúdo e salve.

**Criei um novo conjunto de regras e ele não afeta as respostas dos jogadores**
Criar um arquivo em `arquivos/regras/` não o torna automaticamente ativo. Depois de
escrever o conteúdo, clique em "⭐ Usar agora" (no painel) ou selecione-o no
seletor rápido da barra lateral — só o conjunto marcado como ativo é
enviado no prompt dos jogadores.