# Local Database Manager (LDM)

Uma ferramenta em Python para gerenciar serviços de bancos de dados
instalados localmente no Windows, com foco em controle, diagnóstico e
aprendizado prático de administração de bancos de dados, automação etc

O LDM nasceu de uma situação comum durante os estudos: instalar
diferentes SGBDs para praticar e perceber que vários serviços podem
permanecer ativos mesmo quando não estão sendo utilizados, consumindo
memória e processamento.

> "Se eu não estou utilizando um banco de dados, por que ele precisa
> permanecer executando?"

A ideia é oferecer uma forma simples de identificar esses serviços,
consultar seu estado e iniciar ou parar os que forem necessários,
mantendo o controle sobre o ambiente local.

**Status:** MVP funcional em evolução.

## Objetivos

-   Identificar serviços de bancos de dados conhecidos no Windows.
-   Consultar o estado dos serviços e processos associados.
-   Iniciar e parar serviços quando necessário.
-   Tratar estados intermediários, falhas e tempos limite.
-   Oferecer uma interface de terminal simples e legível.
-   Construir uma base para futuras funcionalidades de diagnóstico e
    gerenciamento de ambientes.

## Funcionalidades implementadas

-   Descoberta de serviços conhecidos a partir de um catálogo de
    configurações.
-   Consulta do estado de serviços e verificação de processos
    associados.
-   Listagem dos bancos identificados e de seus estados.
-   Inicialização e parada de serviços.
-   Tratamento de bancos associados a mais de um serviço.
-   Reconhecimento de estados mistos ou intermediários durante
    transições.
-   Mensagens para situações como serviço não encontrado, serviço já no
    estado solicitado, falha e timeout.
-   Elevação administrativa quando uma operação exige privilégios
    elevados.
-   Interface de terminal com tabelas e mensagens formatadas usando
    Rich.

### Bancos e serviços contemplados

O catálogo atual contém padrões para:

-   PostgreSQL
-   MySQL
-   Microsoft SQL Server
-   Oracle Database
-   Oracle Listener

A descoberta depende dos nomes de serviços e processos configurados no
catálogo. Portanto, instalações com nomes personalizados podem não ser
reconhecidas automaticamente.

## Demonstração

A interface atual é interativa: ao executar `ldm`, o usuário acessa um
menu para listar os bancos, iniciar um serviço, parar um serviço ou
sair.

O exemplo abaixo ilustra o tipo de informação apresentado; os nomes e
estados podem variar conforme os serviços instalados na máquina.

``` text
LOCAL DATABASE MANAGER
1. Listar bancos de dados
2. Iniciar banco de dados
3. Parar banco de dados
4. Sair

Status possíveis: RUNNING, STOPPED e estados intermediários
```

A interface utiliza tabelas e mensagens do Rich para tornar os
resultados mais legíveis. Durante uma transição, o LDM pode informar que
o serviço está em andamento, em vez de tratar imediatamente o estado
como concluído.

## Tecnologias

-   **Python** --- lógica da aplicação e organização dos módulos.
-   **subprocess** --- interação com utilitários e comandos do Windows.
-   **Rich** --- apresentação da interface no terminal.
-   **pytest** --- testes automatizados.
-   **Git e GitHub** --- versionamento e histórico de desenvolvimento.
-   **setuptools** --- configuração e instalação do pacote Python.

## Arquitetura

``` text
local-db-manager/
├── src/
│   └── ldm/
│       ├── cli/
│       │   └── main.py
│       ├── config/
│       │   └── databases.py
│       └── core/
│           ├── database_manager.py
│           └── windows.py
├── tests/
│   ├── unit/
│   │   ├── test_cli.py
│   │   ├── test_database_manager.py
│   │   └── test_windows.py
│   └── integration/
│       └── test_integration_database_manager.py
├── pyproject.toml
└── README.md
```

### Responsabilidade dos módulos

-   **`config/databases.py`** --- mantém o catálogo de padrões de nomes
    de serviços e processos reconhecidos.
-   **`core/database_manager.py`** --- concentra a descoberta, a
    consulta de estados e as operações de gerenciamento dos serviços.
-   **`core/windows.py`** --- trata o fluxo de elevação administrativa
    no Windows.
-   **`cli/main.py`** --- apresenta o menu, recebe escolhas e exibe
    resultados.
-   **`tests/`** --- contém testes unitários e de integração para os
    componentes do projeto.

## Como funciona

O fluxo geral pode ser resumido assim:

``` text
┌─────────────────────────────┐
│       Interface CLI         │
└──────────────┬──────────────┘
               │ solicita operação
               ▼
┌─────────────────────────────┐
│     Database Manager        │
│ descoberta e gerenciamento │
└──────────────┬──────────────┘
               │ consulta / inicia / para
               ▼
┌─────────────────────────────┐
│   Serviços e processos      │
│       do Windows            │
└─────────────────────────────┘
```

O catálogo de configurações orienta quais nomes de serviços e processos
devem ser reconhecidos. A camada de gerenciamento consulta o Windows e
executa as operações solicitadas; a CLI apresenta os resultados ao
usuário.

## Tratamento de erros

O projeto considera situações como:

-   Banco ou serviço não encontrado.
-   Serviço já iniciado ou já parado.
-   Falha ao iniciar ou parar.
-   Tempo limite durante uma operação.
-   Necessidade de privilégios administrativos.
-   Serviços associados a um mesmo banco apresentando estados
    diferentes.

As mensagens e os códigos de saída ajudam a diferenciar sucesso, erro,
banco não encontrado e operação que não precisava ser executada. O
comportamento exato depende da operação e do estado encontrado.

## Instalação

### Requisitos

-   Windows.
-   Python 3.10 ou superior.
-   Utilitários do Windows necessários à consulta e ao controle de
    serviços, como `sc.exe` e `tasklist`.
-   Permissões administrativas para operações que exigem elevação.
-   Pelo menos um serviço de banco de dados compatível com os padrões do
    catálogo para observar resultados de descoberta.

### Instalar a partir do repositório

Clone o repositório e entre na pasta do projeto:

``` bash
git clone <URL_DO_REPOSITORIO>
cd local-db-manager
```

> Substitua `<URL_DO_REPOSITORIO>` pela URL real do repositório.

Crie e ative um ambiente virtual:

``` bash
python -m venv .venv
.venv\Scripts\activate
```

Instale o projeto em modo editável:

``` bash
python -m pip install -e .
```

## Como usar

Após a instalação, execute:

``` bash
ldm
```

Use o menu interativo para listar os bancos identificados, iniciar um
serviço, parar um serviço ou sair. Algumas operações podem solicitar
confirmação de elevação administrativa do Windows.

> **Importante:** comandos diretos como `ldm status`, `ldm start mysql`
> e `ldm stop mysql` são ideias para uma versão futura; não fazem parte
> da interface atual descrita neste README.

## Testes

O projeto possui testes unitários e de integração. Na última execução
compartilhada durante o desenvolvimento, o resultado foi:

``` text
59 passed in 20.30s
```

Esse número representa a execução registrada naquele momento; os
resultados podem mudar conforme alterações no código e no ambiente.

## Limitações atuais

-   Compatível com Windows.
-   A descoberta depende de padrões de nomes definidos no catálogo.
-   Não oferece gerenciamento de ambientes Docker nesta versão.
-   Ainda não apresenta métricas de consumo de CPU e memória dos bancos.
-   A interface atual é um menu interativo; comandos diretos por
    subcomando estão planejados, não implementados.

## Próximas etapas

As ideias para evolução incluem:

-   Atualizar a descoberta de serviços durante a execução.
-   Melhorar diagnósticos do ambiente e apresentar evidências úteis em
    caso de falha.
-   Registrar operações e erros em logs.
-   Adicionar métricas de CPU e memória.
-   Criar suporte a ambientes de banco de dados via Docker.
-   Permitir ambientes configuráveis.
-   Expandir os testes e a cobertura de cenários de falha.
-   Adicionar comandos diretos à CLI, como `status`, `start` e `stop`.

Esses itens são objetivos futuros, não funcionalidades garantidas na
versão atual.

## O que estou aprendendo com o projeto

O LDM é também um exercício de engenharia de software aplicada. Durante
seu desenvolvimento, pratico:

-   Separação de responsabilidades entre CLI, configuração e lógica de
    gerenciamento.
-   Uso do `subprocess` para integrar Python com ferramentas do sistema
    operacional.
-   Tratamento de erros, timeouts e estados intermediários.
-   Elevação de privilégios administrativos no Windows.
-   Testes unitários e de integração com `pytest`.
-   Organização de um pacote Python instalável.
-   Versionamento e evolução incremental com Git.

O projeto conecta Python e fundamentos de administração de bancos de
dados a problemas reais do ambiente de desenvolvimento local.

## Contribuição e evolução

O projeto está em desenvolvimento. Sugestões e relatos de comportamento
em diferentes instalações do Windows podem ajudar a ampliar o catálogo e
fortalecer o tratamento de falhas.

------------------------------------------------------------------------

**Local Database Manager** --- controle mais claro sobre os serviços de
banco de dados do ambiente local.
