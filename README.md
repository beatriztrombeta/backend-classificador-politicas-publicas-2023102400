# Classificador de Políticas Públicas – Backend

Este repositório contém o **sistema backend** para o classificador do projeto de pesquisa financiado pela **FAPESP (Concessão nº 2023/10240-0)** intitulado:
**“Políticas públicas e ações afirmativas na universidade pública: definição de um algoritmo para alertar sobre o risco de evasão entre os ingressantes na universidade por meio de sistemas de cotas e reservas.”**

---

## Pré-requisitos

Antes de começar, tenha instalado na sua máquina:

* Python 3.10 ou superior
* Docker
* Docker Compose
* Git

Para verificar:

```bash
python --version
docker --version
docker compose version
git --version
```

---

## Clonando o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd backend-classificador-politicas-publicas-2023102400
```
---

## Subindo o projeto com Docker

Na raiz do projeto, execute:

```bash
docker compose up --build
```

Esse comando irá:

* Criar a imagem do backend
* Subir o container do PostgreSQL
* Subir a API FastAPI
* Expor a aplicação na porta 8000

---

## Acessando a aplicação

Após subir os containers:

* API: [http://localhost:8000](http://localhost:8000)
* Documentação automática (Swagger):
  [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Parando os containers

Para desligar os serviços:

```bash
docker compose down
```

---

## Parar e remover volumes (reset completo)

Para parar os containers e remover os dados do banco:

```bash
docker compose down -v
```

Use esse comando apenas se quiser reiniciar o ambiente do zero.

---

## Observações

* O banco de dados PostgreSQL roda em container Docker.
* As variáveis de ambiente da aplicação são definidas no arquivo `.env`.
* A arquitetura do projeto segue o padrão MVC.
* A pasta `views` permanece vazia, pois o frontend será implementado separadamente.

## Licença e contexto da pesquisa

Este software faz parte de um projeto de pesquisa acadêmica financiado pela **FAPESP** e destina-se **exclusivamente a fins de pesquisa e educação**.
Todos os direitos reservados à equipe do projeto e às instituições afiliadas.
