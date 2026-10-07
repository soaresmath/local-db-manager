# Local Database Manager

Uma ferramenta em Python para gerenciamento de ambientes de bancos de dados locais no Windows.

O LDM (Local Database Manager) foi criado para facilitar o controle de bancos de dados instalados localmente, permitindo identificar seus serviços, consultar seus estados e iniciar ou parar seus ambientes conforme a necessidade.

---

## Sobre o projeto

O Local Database Manager nasceu de uma necessidade prática durante o desenvolvimento e estudo de bancos de dados.

Ao trabalhar com diferentes SGBDs instalados na mesma máquina, como MySQL, SQL Server, Oracle e PostgreSQL, é comum que alguns de seus serviços sejam iniciados automaticamente junto com o Windows.

Mesmo quando não estão sendo utilizados, esses serviços podem permanecer ativos e consumir recursos da máquina, principalmente memória e processamento.

A ideia do LDM surgiu para transformar esse problema em uma ferramenta simples:

> **Se eu não estou utilizando um banco de dados, por que ele precisa permanecer executando?**

A partir disso, o projeto começou como uma pequena ferramenta para iniciar e parar serviços de bancos de dados e evoluiu para um estudo mais amplo sobre:

- desenvolvimento de aplicações Python;
- automação no Windows;
- gerenciamento de serviços;
- descoberta de softwares instalados;
- arquitetura e organização de projetos;
- tratamento de erros;
- testes automatizados;
- empacotamento de aplicações Python;
- construção de ferramentas de linha de comando.

O projeto também serve como um laboratório para transformar conhecimentos de Python e administração de bancos de dados em uma aplicação prática.

---

## Motivação

O projeto possui duas motivações principais.

### Problema prático

Manter diversos bancos de dados instalados para estudos e projetos pode deixar a máquina com vários serviços executando simultaneamente.

O LDM busca tornar esse gerenciamento mais simples, permitindo que o usuário mantenha seus ambientes disponíveis sem precisar abrir manualmente ferramentas administrativas do Windows ou memorizar os nomes dos serviços de cada SGBD.

### Aprendizado

O LDM também foi criado como um projeto de aprendizado.

Em vez de estudar Python, Git, testes, arquitetura e automação de forma isolada, a proposta é aprender esses conceitos enquanto uma ferramenta real é construída.

Por isso, algumas decisões do projeto são deliberadamente incrementais. A aplicação começou simples e está sendo evoluída conforme novos problemas aparecem.

---

## Objetivos

Os principais objetivos do projeto são:

- facilitar o gerenciamento de bancos de dados locais;
- reduzir a necessidade de manter serviços desnecessários em execução;
- automatizar operações comuns sobre serviços de banco de dados;
- estudar integração entre Python e o sistema operacional;
- praticar organização e arquitetura de projetos Python;
- aplicar testes automatizados;
- aprender a estruturar e distribuir uma aplicação Python.

---

## Funcionalidades atuais

Atualmente, o LDM é capaz de:

- detectar bancos de dados instalados na máquina;
- identificar serviços associados aos bancos;
- identificar processos relacionados aos bancos;
- consultar o estado dos serviços;
- listar os bancos encontrados e seus respectivos status;
- iniciar bancos que estejam parados;
- parar bancos que estejam em execução;
- gerenciar bancos compostos por múltiplos serviços;
- detectar falhas durante operações sobre os serviços;
- controlar operações com limite de tempo;
- apresentar as informações através de uma CLI utilizando Rich.

### Bancos atualmente reconhecidos

O catálogo atual possui suporte para:

- MySQL
- SQL Server
- Oracle
- PostgreSQL

O sistema foi projetado para que novos bancos possam ser adicionados ao catálogo sem precisar alterar toda a lógica de gerenciamento.

---

## Demonstração

Ao executar o comando:

```bash
ldm
```

o LDM analisa os serviços e processos disponíveis na máquina e apresenta a interface de gerenciamento.

Exemplo:

```text
╭─ LOCAL DATABASE MANAGER ─╮
│ Database Service Manager │
╰──────────────────────────╯

✓ Análise da máquina concluída.

Menu principal

 1  Listar bancos
 2  Iniciar banco
 3  Parar banco
 4  Sair
```

A listagem apresenta o estado atual dos bancos encontrados:

```text
    Bancos detectados

┏━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Banco      ┃  Status   ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ PostgreSQL │ ● RUNNING │
│ MySQL      │ ● RUNNING │
│ SQL Server │ ● STOPPED │
│ Oracle     │ ● STOPPED │
└────────────┴───────────┘
```

---

## Tecnologias

O projeto utiliza principalmente:

- **Python**
- **subprocess** — comunicação com comandos e serviços do Windows
- **Rich** — interface de terminal
- **pytest** — testes automatizados
- **Git** — controle de versão
- **setuptools** — empacotamento e instalação do projeto

---

## Arquitetura

O projeto utiliza uma estrutura baseada em separação de responsabilidades:

```text
local-db-manager/
│
├── src/
│   └── ldm/
│       ├── cli/
│       │   └── main.py
│       │
│       ├── config/
│       │   └── databases.py
│       │
│       └── core/
│           └── database_manager.py
│
├── tests/
│   ├── unit/
│   │   └── test_database_manager.py
│   │
│   └── integration/
│       └── test_integration_database_manager.py
│
├── pyproject.toml
├── README.md
└── .gitignore
```

### CLI

`cli/main.py`

Responsável pela interface de linha de comando, interação com o usuário e apresentação das informações.

### Core

`core/database_manager.py`

Contém a lógica responsável por comunicação com o Windows, descoberta de serviços e processos e gerenciamento dos bancos.

### Configuração

`config/databases.py`

Mantém o catálogo de bancos conhecidos e os termos utilizados para identificar seus serviços e processos.

Essa separação permite que a interface, as regras de gerenciamento e o conhecimento sobre os bancos evoluam de forma independente.

---

## Como funciona

O LDM realiza inicialmente uma análise do ambiente local.

De forma simplificada:

```text
                 Windows
                    │
          ┌─────────┴─────────┐
          │                   │
      Serviços            Processos
          │                   │
          └─────────┬─────────┘
                    │
             descobrir_bancos()
                    │
                    ▼
             Bancos encontrados
                    │
                    ▼
              Interface CLI
                    │
          ┌─────────┴─────────┐
          │                   │
       Iniciar              Parar
          │                   │
          └─────────┬─────────┘
                    ▼
             Serviços Windows
```

A descoberta utiliza informações dos serviços e processos disponíveis na máquina para identificar quais bancos conhecidos estão presentes.

Depois da descoberta, as operações de gerenciamento utilizam os serviços encontrados para consultar, iniciar ou parar os bancos.

---

## Tratamento de erros

O LDM utiliza `subprocess` para executar comandos do sistema operacional, como consultas e operações sobre serviços do Windows.

Essas operações podem falhar por diferentes motivos, como:

- serviço inexistente;
- falta de permissões;
- falha durante a execução do comando;
- serviço que não responde dentro do tempo esperado;
- erro na comunicação com o sistema operacional.

Os erros são tratados nas camadas responsáveis pelas operações e propagados quando necessário para que possam ser apresentados pela interface.

O fluxo geral é:

```text
Windows / subprocess
        ↓
função de serviço
        ↓
gerenciamento do banco
        ↓
CLI
        ↓
usuário
```

O projeto utiliza `try`, `except`, `raise` e limites de tempo para evitar que uma operação fique aguardando indefinidamente.

---

## Testes

O projeto possui testes unitários e testes de integração.

### Testes unitários

Os testes unitários verificam a lógica do sistema de forma isolada, utilizando mocks para simular chamadas ao sistema operacional.

Entre os comportamentos testados estão:

- busca de bancos;
- tratamento de exceções;
- consulta de status;
- inicialização de serviços;
- parada de serviços;
- inicialização de bancos;
- parada de bancos;
- tratamento de bancos inexistentes;
- tratamento de falhas durante operações.

### Testes de integração

Os testes de integração executam operações reais no ambiente Windows para verificar a comunicação com os serviços do sistema.

São testados, por exemplo:

- consulta de um serviço real;
- obtenção da configuração de um serviço;
- descoberta de bancos presentes na máquina.

Atualmente:

```text
19 testes
19 passando
```

Os testes de integração dependem de um ambiente Windows com os serviços necessários disponíveis.

---

## Requisitos

Atualmente o LDM é direcionado para **Windows**, pois utiliza recursos específicos do sistema operacional, como:

- `sc.exe`
- `tasklist`
- PowerShell / CIM

Também é necessário:

- Python 3.10 ou superior;
- permissões adequadas para iniciar e parar serviços;
- pelo menos um banco de dados reconhecido pelo catálogo para utilizar a descoberta.

---

## Instalação

Clone o repositório:

```bash
git clone <URL_DO_REPOSITORIO>
cd local-db-manager
```

Instale o projeto em modo editável:

```bash
python -m pip install -e .
```

Após a instalação, o comando `ldm` ficará disponível no terminal.

Execute:

```bash
ldm
```

---

## Uso

Ao iniciar o LDM, a aplicação realiza a análise inicial do ambiente e apresenta o menu principal.

As opções disponíveis atualmente são:

```text
1 - Listar bancos
2 - Iniciar banco
3 - Parar banco
4 - Sair
```

O usuário pode consultar os bancos encontrados e executar operações de inicialização ou parada conforme a necessidade.

---

## Aprendizados

O LDM está sendo utilizado como um projeto prático para consolidar conhecimentos de desenvolvimento de software.

Durante sua construção estão sendo praticados:

### Python

- organização de módulos;
- funções;
- listas e dicionários;
- tratamento de exceções;
- `subprocess`;
- manipulação de dados;
- interação com o sistema operacional.

### Engenharia de software

- separação de responsabilidades;
- organização de projetos;
- arquitetura em camadas;
- tratamento de erros;
- testes unitários;
- testes de integração;
- manutenção de código.

### Ferramentas

- Git e GitHub;
- pytest;
- Rich;
- `pyproject.toml`;
- empacotamento e instalação de aplicações Python.

Mais importante do que apenas aprender a sintaxe dessas ferramentas é entender **quando utilizá-las e qual problema elas resolvem**.

---

## O que este projeto representa

O LDM não foi criado apenas como um exercício de Python.

A proposta é construir uma ferramenta útil enquanto os conceitos necessários para desenvolver software de forma mais estruturada são aprendidos.

O projeto começou com uma necessidade simples — controlar bancos de dados locais — e foi evoluindo para envolver:

```text
Python
   ↓
Automação
   ↓
Sistema operacional
   ↓
Arquitetura
   ↓
Testes
   ↓
Empacotamento
   ↓
Ferramenta de linha de comando
```

Esse processo faz parte do objetivo principal do projeto: transformar conhecimento teórico em uma aplicação que possa ser utilizada, testada e evoluída.

---

## Roadmap

Algumas ideias estão planejadas para versões futuras, mas não fazem parte do MVP atual.

### Próximas possibilidades

- atualização da descoberta sem reiniciar a aplicação;
- visualização das evidências encontradas para cada banco;
- diagnóstico do ambiente;
- informações de CPU e memória;
- histórico e logs das operações;
- comandos específicos pela CLI, como:

```bash
ldm status
ldm start mysql
ldm stop mysql
```

- suporte a ambientes de banco executando através do Docker;
- configuração personalizada de ambientes;
- testes mais abrangentes.

A prioridade é manter o núcleo simples e confiável antes de adicionar novas funcionalidades.

---

## Limitações atuais

O LDM atualmente:

- é direcionado ao Windows;
- depende dos serviços do sistema operacional;
- possui um catálogo definido de bancos reconhecidos;
- ainda não gerencia bancos executados através do Docker;
- não monitora continuamente consumo de CPU ou memória.

Essas limitações são intencionais neste momento, pois o objetivo atual é consolidar o núcleo da ferramenta.

---

## Status do projeto

**MVP em fase final de desenvolvimento.**

O núcleo de descoberta e gerenciamento já está funcionando em um ambiente Windows real, com testes unitários e de integração automatizados.

O próximo objetivo é finalizar a documentação, revisar o MVP e avaliar quais funcionalidades realmente fazem sentido para uma futura versão 2.
