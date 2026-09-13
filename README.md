# 🎲 Agentic Tabletop RPG

Sistema que simula uma mesa de RPG cooperativo: você é o mestre, e cada
jogador é conduzido por um agente de IA com ficha, personalidade e memória
próprias. Existe uma interface visual (Streamlit) para quem não quer mexer
em terminal, e uma versão de terminal (`main.py`) equivalente para quem
preferir.

---

## Índice

- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Configurando a chave de API (.env)](#configurando-a-chave-de-api-env)
- [Como rodar](#como-rodar)
- [Funcionalidades](#funcionalidades)
  - [Fichas dos personagens](#fichas-dos-personagens)
  - [Ações do mestre](#ações-do-mestre)
  - [Tags de resposta: \[acao\], \[duvida\] e \[pensamento\]](#tags-de-resposta-acao-duvida-e-pensamento)
  - [Fluxo de aprovação](#fluxo-de-aprovação)
  - [Sistema de memória (rodada → cena → mesa)](#sistema-de-memória-rodada--cena--mesa)
  - [Por que resumir um resumo pode "perder" informação (de propósito)](#por-que-resumir-um-resumo-pode-perder-informação-de-propósito)
  - [Balões de fala](#balões-de-fala)
  - [Fotos dos jogadores](#fotos-dos-jogadores)
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

Os comandos são os mesmos nos três sistemas a partir daqui — só muda o
comando de ativar o ambiente virtual.

1. Baixe/clone este repositório e entre na pasta:
   ```bash
   git clone https://github.com/nfekted/agentic-tabletop-rpg
   cd <pasta-do-projeto>
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

---

## Configurando a chave de API (.env)

O projeto usa o Gemini (Google) para gerar as respostas dos jogadores e do
historiador. Inicialmente foi escolhido o Gemini pela janela de contexto (1M tokens) e pela cota gratuita ser mais generosa que as demais, futuramente planejo incluir outras opções. Você precisa de uma chave de API gratuita:

1. Gere uma chave em <https://aistudio.google.com/apikey>.
2. Crie um arquivo chamado **`.env`** (sem nome antes do ponto) na mesma
   pasta onde estão `app.py`, `main.py`, `config.py` etc.
3. Coloque essa linha dentro dele:
   ```
   GOOGLE_API_KEY="sua_chave_aqui"
   ```
   Sem aspas em volta do valor, sem espaço antes/depois do `=`. O `.env`
   **não deve ser versionado no Git** — adicione `.env` ao seu
   `.gitignore` para não vazar sua chave sem querer.

Se a chave não for encontrada, o app avisa exatamente qual pasta ele
esperava encontrar o `.env`, em vez de travar com um erro genérico.

---

## Como rodar

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

### Regras da mesa

É possível determinar as regras da mesa que funcionam como a instrução base para o agente, o ideal é simplificar as instruções do seu manual para ações simples, em exemplo:

"Quando o jogador decide realizar uma ação ela terá base em um atributo, o jogador então rola o dado para verificar a somatória de pontuação e determinar a taxa de sucesso da ação, podendo somar os bonus da ficha[...]"

Como instrução de regras, determinamos apenas o "core" basico dessa explicação:

"Quando realizar uma ação ela será relacionada com um atributo (ex: mover uma pedra = força, correr = agilidade)"

### Fichas dos personagens

Cada jogador tem um arquivo de ficha em `fichas/{nome_do_jogador}.txt`, que
descreve personalidade, história e características do personagem — é isso
que molda como o agente de IA responde por ele. Pela interface, clique no
botão ✏️ no card do jogador para editar e salvar a ficha sem precisar abrir
nenhum arquivo manualmente. A primeira linha da ficha também guarda o
status do personagem (`vivo`, `morto` ou `inconsciente`), controlado pelo
seletor abaixo do card.

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
  jogadores da mesa.

### Tags de resposta: [acao], [duvida] e [pensamento]

O modelo é instruído a começar a resposta com uma dessas tags quando for o
caso:

| Tag | O que significa | O que acontece depois |
|---|---|---|
| `[acao]` | O personagem está realizando uma ação | A ação é considerada resolvida; ninguém reage automaticamente |
| `[duvida]` | O personagem quer perguntar algo a outro jogador presente | Você escolhe para quem redirecionar a pergunta; a resposta de quem foi escolhido também passa por aprovação |
| `[pensamento]` | Um pensamento interno que o personagem **não diz em voz alta** | Nunca é mostrado a outros jogadores nem entra no histórico compartilhado da cena — fica só na memória privada daquele personagem |
| *(nenhuma tag)* | Fala/reação social comum | Os demais jogadores presentes reagem automaticamente com uma opinião breve |

### Fluxo de aprovação

Sempre que um jogador responde a uma fala direcionada a ele (não no "Falar
com Todos"), a resposta aparece com dois botões: **✅ Aprovar/Espelhar** e
**❌ Descartar**. Só depois de aprovada ela entra de fato na história e na
memória — isso te dá controle para pedir uma nova resposta ou simplesmente
recusar algo que não fez sentido, antes que vire "fato" na campanha.

### Sistema de memória (rodada → cena → mesa)

Cada jogador tem sua própria pasta `memoria_{nome}/`, com uma hierarquia de
três níveis:

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
jogador pelo botão 🖼️ no card. A imagem fica salva dentro da própria pasta
de memória do personagem (`memoria_{nome}/avatar.<extensão>`).

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
├── config.py               # Lista de jogadores e modelos de IA
├── fichas.py                # Leitura/edição de fichas e regras
├── imagens.py                # Upload de imagens de contexto e fotos de jogador
├── memoria.py                 # Hierarquia de memória rodada → cena → mesa
├── agentes.py                  # Monta o prompt e gera as respostas dos jogadores
├── requirements.txt
├── .env                    # Sua chave de API (não versionar)
├── regras_rpg.txt          # Regras gerais da mesa (criado ao salvar pela tela)
├── fichas/
│   ├── jogadora.txt
│   ├── jogadorb.txt
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
O `.env` não foi encontrado ou a variável está com nome/formato errado.
Confira se o arquivo se chama exatamente `.env`, está na mesma pasta dos
`.py`, e contém `GOOGLE_API_KEY=sua_chave` sem aspas. Depois, reinicie o
Streamlit por completo (`Ctrl+C` e rode `streamlit run app.py` de novo) —
variáveis de ambiente só são lidas quando o processo sobe.

**Nenhum jogador aparece na tela**
Confira se `config.py` tem pelo menos um nome na lista `AGENTES`, ou
adicione um pela barra lateral.

**A ficha ou as regras aparecem vazias**
Isso é normal se ainda não foram salvas nenhuma vez pela interface — clique
em ✏️ Ficha (ou "📖 Editar Regras Gerais"), escreva o conteúdo e salve.