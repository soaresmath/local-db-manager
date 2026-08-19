# Local Database Manager

## Sobre o projeto

O LDM (Local Database Manager) é uma ferramenta desenvolvida em Python para o gerenciamento de bancos de dados locais.

A ferramenta facilita o controle de instâncias de bancos de dados que podem ser iniciadas automaticamente junto com o sistema operacional. Essas instâncias podem consumir recursos como processamento e memória mesmo quando não estão sendo utilizadas.

O LDM permite iniciar e parar os serviços associados aos bancos de dados conforme a necessidade do usuário, facilitando o gerenciamento desses recursos durante o desenvolvimento.

## Objetivo

O objetivo do LDM é facilitar o gerenciamento de bancos de dados locais e o controle dos recursos computacionais utilizados por suas instâncias, permitindo que os serviços sejam iniciados ou encerrados conforme a necessidade do usuário.

## Funcionalidades

- Listar os bancos de dados disponíveis e seus respectivos status.
- Iniciar bancos de dados que estejam parados.
- Parar bancos de dados que estejam em execução, conforme a necessidade do usuário.
- Gerenciar bancos de dados compostos por múltiplos serviços.
- Identificar e reportar erros durante as operações sobre os serviços.

## Tecnologias utilizadas

- Python
- Biblioteca `subprocess`
- Git

## Estrutura do projeto

- `main.py` — responsável pela interface de linha de comando (CLI) e pelo tratamento inicial dos erros.
- `database_manager.py` — contém a lógica principal de gerenciamento dos bancos de dados e seus serviços.
- `config.py` — contém as configurações e os dados dos bancos de dados gerenciados pelo LDM.

## Requisitos

Para executar o LDM, é necessário:

- Windows, pois o gerenciamento dos serviços utiliza o comando `sc`.
- Python instalado.
- Pelo menos um dos bancos de dados configurados no projeto instalado na máquina.
- Permissões adequadas para iniciar e parar os serviços do sistema.

## Como executar

Clone o repositório e acesse a pasta do projeto:

```bash
git clone <URL_DO_REPOSITORIO>
cd local-db-manager
```

Execute o programa:

```bash
python main.py
```

## Como funciona

Ao selecionar a opção de listar os bancos, o LDM executa a função `verificar_status_banco()` para cada banco configurado.

A função percorre os serviços associados ao banco e utiliza `verificar_status_servico()` para consultar o estado de cada serviço no sistema operacional.

O banco é considerado `RUNNING` quando seus serviços estão em execução. Caso um dos serviços esteja `STOPPED`, o banco é considerado `STOPPED`. Caso ocorra uma falha durante a consulta de um serviço, o erro é propagado para a camada responsável pelo tratamento da operação.

Após a verificação, o LDM apresenta no terminal o status de cada banco configurado.

## Tratamento de erros

O LDM utiliza a biblioteca `subprocess` para executar comandos do sistema operacional e consultar ou controlar os serviços dos bancos de dados.

Quando ocorre uma falha durante essas operações, como um serviço inexistente ou uma operação que ultrapassa o tempo limite definido, o `subprocess` pode gerar uma exceção.

Essas exceções são tratadas inicialmente nas funções responsáveis pela comunicação com o sistema operacional. Quando necessário, utilizamos `raise Exception` para propagar o erro para a função que chamou a operação.

Dessa forma, o erro pode subir pelas diferentes camadas da aplicação até chegar ao ponto responsável por apresentá-lo ao usuário.

O fluxo pode ser representado como:

```text
subprocess
→ função de serviço
→ função de gerenciamento
→ interface CLI
→ usuário
```

## Próximos passos

- Monitoramento do consumo de CPU e memória.
- Análise dos recursos utilizados antes e depois das operações.
- Desenvolvimento de uma interface gráfica (GUI).

## Aprendizados

Durante o desenvolvimento do LDM, foram praticados conceitos como:

- Organização de projetos Python em diferentes módulos.
- Uso da biblioteca `subprocess` para interação com o sistema operacional.
- Tratamento e propagação de exceções com `try`, `except` e `raise`.
- Separação de responsabilidades entre interface, lógica e configuração.
- Estruturas de dados utilizando listas e dicionários.
- Controle de versão e organização do projeto utilizando Git.
