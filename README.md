# 🏋️ Controle de Treinos - MVP

🎓 Este projeto foi criado como atividade obrigatória do curso de pós-graduação em Engenharia de Software: Automação e Inovação com IA da Universidade Federal de Goiás (UFG).

📌 Módulo: "Laboratório Introdutório: Construindo um Mini-projeto com Inteligência Artificial Generativa [ESP T2 ES C4]"

## 📖 Sobre o Projeto

O Controle de Treinos é uma aplicação Full-Stack (MVP) desenvolvida para auxiliar praticantes de musculação, crossfit e outros esportes de força a registrarem e acompanharem sua evolução diária.

A aplicação permite a criação de treinos dinâmicos, registro de séries, repetições e cargas, além de oferecer um rico histórico e gráficos para visualização da sobrecarga progressiva (evolução de cargas ao longo do tempo).

## 🛠️ Tecnologias Utilizadas

A arquitetura do projeto foi dividida de forma clara entre Backend e Frontend, utilizando as seguintes ferramentas:

- Backend: FastAPI (API REST rápida e moderna)

- Banco de Dados: SQLite com ORM SQLAlchemy

- Validação de Dados: Pydantic

- Frontend: Streamlit (Interface web interativa em Python)

- Visualização de Dados: Pandas e Altair

- Testes Automatizados: Pytest

## 📂 Estrutura do Projeto

- `backend.py`: Contém a configuração do banco de dados, modelos do SQLAlchemy, esquemas Pydantic e as rotas da API REST.

- `frontend.py`: Aplicação Streamlit que consome a API e renderiza a interface do usuário.

- `popular_banco.py`: Script utilitário para popular o banco com dados fictícios ou limpá-lo completamente.

- `test_backend.py`: Suíte de testes unitários e de integração utilizando Pytest e banco de dados em memória.

- `.env`: Arquivo de exemplo para configuração das variáveis de ambiente.

- `requirements.txt`: Lista de dependências do projeto.


# 🚀 Como Executar o Projeto Localmente

## 1. Pré-requisitos

Certifique-se de ter o Python 3.9+ instalado em sua máquina.

## 2. Configuração do Ambiente Virtual

É altamente recomendado utilizar um ambiente virtual para isolar as dependências do projeto.

### Crie o ambiente virtual
`python -m venv venv`

### Ative o ambiente (Windows)
`.\venv\Scripts\activate`

### Ative o ambiente (Linux/Mac)
`source venv/bin/activate`


## 3. Instalação das Dependências

Com o ambiente ativado, instale as bibliotecas necessárias:

`pip install -r requirements.txt`

## 4. Variáveis de Ambiente

Crie um arquivo chamado `.env` na raiz do projeto e configure as URLs (você pode se basear no arquivo `.env` atual, se houver):

- `DATABASE_URL=sqlite:///./treinos.db`
- `API_URL=http://127.0.0.1:8000`

## 5. Executando a Aplicação

Para que a aplicação funcione, você precisará iniciar o servidor Backend e a interface Frontend em dois terminais separados (lembre-se de ativar o venv em ambos).

### Terminal 1 (Backend):

`uvicorn backend:app --reload`

A API estará rodando em http://127.0.0.1:8000.

### Terminal 2 (Frontend):

`streamlit run frontend.py`


O painel web abrirá automaticamente no seu navegador em http://localhost:8501.

# 📱 Como Utilizar a Aplicação na Prática

A interface é dividida em três abas principais:

## 1. Treino Atual

- **Iniciar**: Clique em "Iniciar Novo Treino" para começar.

- **Adicionar Exercício**: Você pode selecionar um exercício já realizado no passado na lista disponível ou clicar em "➕" para criar um exercício pela primeira vez.

- **Gravar Séries**: Para cada exercício, insira a Carga e as Repetições e clique em "Gravar Série".

- **✨ Dica Mágica**: O sistema preenche automaticamente os campos com o peso e repetições que você usou na sua última série ou no seu último treino deste exercício!

- **Correções**: Errou algo? Você pode excluir séries individuais ou o exercício inteiro utilizando os botões de lixeira 🗑️.

- **Finalizar**: Quando terminar, clique em "✅ Finalizar e Salvar Treino" para gravá-lo no seu histórico. Após isso, o treino não poderá mais ser editado.

## 2. Histórico

Nesta aba, você visualiza a linha do tempo de todos os treinos que já finalizou. Expanda os blocos de data para ver os detalhes (exercícios, séries, repetições e cargas) do que foi realizado em cada dia.

## 3. Evolução de Carga

Aqui está o coração do seu progresso!

Selecione um exercício no menu suspenso.

O sistema gerará um gráfico temporal mostrando a evolução da sua carga.

Se você progrediu a carga dentro do mesmo dia (ex: começou com 10kg e terminou com 30kg), o gráfico mostrará essa escalada de forma visual!

# 🧪 Executando os Testes Automatizados

O projeto conta com uma suíte de testes que cria um banco de dados temporário na memória RAM para não interferir nos seus treinos reais. Para rodar os testes, abra um terminal (com o venv ativado) e execute:

`python -m pytest test_backend.py -v`


# 🛠️ Script Utilitário (Popular / Limpar Banco)

Para testar os gráficos ou resetar o aplicativo, você pode usar o script auxiliar `popular_banco.py`.

Para inserir dados fictícios de exercícios no passado:

`python popular_banco.py popular`


Para apagar absolutamente todos os dados e começar do zero:

`python popular_banco.py limpar`


Desenvolvido com dedicação e muito código Python! 🐍