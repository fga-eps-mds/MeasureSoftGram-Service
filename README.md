# MeasureSoftGram-Service

## Badges

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=fga-eps-mds_2026.2-MeasureSoftGram-Service&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=fga-eps-mds_2026.2-MeasureSoftGram-Service)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=fga-eps-mds_2026.2-MeasureSoftGram-Service&metric=coverage)](https://sonarcloud.io/summary/new_code?id=fga-eps-mds_2026.2-MeasureSoftGram-Service)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=fga-eps-mds_2026.2-MeasureSoftGram-Service&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=fga-eps-mds_2026.2-MeasureSoftGram-Service)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=fga-eps-mds_2026.2-MeasureSoftGram-Service&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=fga-eps-mds_2026.2-MeasureSoftGram-Service)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=fga-eps-mds_2026.2-MeasureSoftGram-Service&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=fga-eps-mds_2026.2-MeasureSoftGram-Service)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=fga-eps-mds_2026.2-MeasureSoftGram-Service&metric=bugs)](https://sonarcloud.io/summary/new_code?id=fga-eps-mds_2026.2-MeasureSoftGram-Service)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=fga-eps-mds_2026.2-MeasureSoftGram-Service&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=fga-eps-mds_2026.2-MeasureSoftGram-Service)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=fga-eps-mds_2026.2-MeasureSoftGram-Service&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=fga-eps-mds_2026.2-MeasureSoftGram-Service)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=fga-eps-mds_2026.2-MeasureSoftGram-Service&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=fga-eps-mds_2026.2-MeasureSoftGram-Service)
[![Technical Debt](https://sonarcloud.io/api/project_badges/measure?project=fga-eps-mds_2026.2-MeasureSoftGram-Service&metric=sqale_index)](https://sonarcloud.io/summary/new_code?id=fga-eps-mds_2026.2-MeasureSoftGram-Service)
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=fga-eps-mds_2026.2-MeasureSoftGram-Service&metric=ncloc)](https://sonarcloud.io/summary/new_code?id=fga-eps-mds_2026.2-MeasureSoftGram-Service)


## O que é

O **MeasureSoftGram-Service** é a API backend responsável por conter e manipular os dados do MeasureSoftGram: métricas, metas de configuração, análises realizadas, etc. Utiliza a arquitetura MVC / Django REST Framework para estruturação e organização do serviço.

## Como Executar o Projeto

A forma oficial e recomendada de inicializar e interagir com o ambiente de desenvolvimento é através dos comandos do **`Makefile`**.

### 1. Configurar as variáveis de ambiente

A pasta `env-vars/` é **gitignored** (contém credenciais). O repositório traz uma pasta `env-vars-example/` com os templates dos arquivos de ambiente. Para criar a sua pasta de variáveis de ambiente:

```bash
make env
```

*(Copia `env-vars-example/` para `env-vars/` sem sobrescrever arquivos já existentes).*

Os arquivos esperados em `env-vars/` são:

- `.postgres.env` — credenciais do Postgres (`POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PORT`, `POSTGRES_PASSWORD`).
- `.service.env` — `DEBUG`, `SECRET_KEY`, `GITHUB_CLIENT_ID`, `GITHUB_SECRET`, `LOGIN_REDIRECT_URL`, etc.

Edite os valores que precisar (em desenvolvimento, os defaults do `env-vars-example` já funcionam para subir o backend).

#### 1.1. Configurar o GitHub OAuth App (login com GitHub em dev)

Os defaults de `GITHUB_CLIENT_ID` / `GITHUB_SECRET` no `env-vars-example/.service.env` são placeholders (`CL13NT1D` / `S3CR3T`): a API sobe, mas o **login real com GitHub** requer um OAuth App próprio:

1. Acesse **GitHub → Settings → Developer settings → OAuth Apps → New OAuth App** (<https://github.com/settings/developers>).
2. Preencha:
   - **Application name**: livre (ex: `MeasureSoftGram (dev)`).
   - **Homepage URL**: `http://127.0.0.1:3000`
   - **Authorization callback URL**: `http://127.0.0.1:3000` — precisa coincidir com o `LOGIN_REDIRECT_URL`. O backend usa esse valor como `callback_url` na troca do `code` (`src/accounts/views.py`); em dev o callback é o próprio frontend, que recebe o `?code=` do GitHub e o repassa ao backend.
3. Clique em **Register application** e gere um **client secret**.
4. Configure os valores em `env-vars/.service.env`:

   ```env
   GITHUB_CLIENT_ID=<client id do OAuth App>
   GITHUB_SECRET=<client secret gerado>
   LOGIN_REDIRECT_URL=http://127.0.0.1:3000
   ```

5. Reinicie o serviço (`make restart`).

> **Produção:** Use um OAuth App separado com a *Authorization callback URL* apontando para o domínio real de produção e as credenciais no `env-vars/.service.env` do servidor. Os placeholders de PROD estão comentados no `env-vars-example/.service.env`.

### 2. Setup Completo da Stack (Do zero ao ambiente pronto)

Para criar os arquivos de ambiente (se não existirem), construir as imagens Docker, subir os containers e aguardar o healthcheck da API:

```bash
make setup
```

A API estará disponível em [http://localhost:8080/](http://localhost:8080/) e o Grafana em [http://localhost:5000/](http://localhost:5000/).

### 3. Desenvolvimento com Hot-Reload

Para rodar a aplicação em desenvolvimento com sincronização de código e reinstalação automática de dependências em tempo real (`develop.watch` no `docker-compose.yml`):

```bash
make dev
```

### 4. Carga Inicial de Dados (Seed)

Para popular os dados iniciais de entidades suportadas e provisionar os dashboards do Grafana:

```bash
make seed
```

### 5. Configurar os Git Hooks (Pre-commit)

Para garantir a padronização do código e das mensagens de commit no repositório local (validação de Conventional Commits, formatação com Black/isort e linter com Flake8), instale os hooks do git:

```bash
make hooks
```

> O comando detecta automaticamente o gerenciador disponível (`pre-commit`, `uv`, `uvx` ou `pip3`) e instala os hooks de `pre-commit` e `commit-msg`.

---

## Principais Comandos do Makefile

O `Makefile` centraliza todos os comandos essenciais para a operação do projeto:

| Comando | Descrição |
|---|---|
| `make setup` | Setup completo: copia env-vars, builda imagens, sobe a stack e aguarda o healthcheck |
| `make dev` | Sobe a stack com **hot-reload** (`docker compose up --watch`) |
| `make up` | Sobe todos os containers em segundo plano (`docker compose up -d`) |
| `make down` | Para e remove os containers da stack (`docker compose down`) |
| `make restart` | Reinicia todos os containers |
| `make logs` | Exibe e acompanha os logs em tempo real (`docker compose logs -f`) |
| `make ps` | Mostra o status atual dos containers |
| `make build` | Realiza o build das imagens Docker sem cache |
| `make rebuild` | Recria a stack (`down` + `build` + `up`) |
| `make clear` | Remove containers, volumes e órfãos (`docker compose down -v --remove-orphans`) |
| `make seed` | Popula o banco com dados iniciais e dashboards do Grafana |
| `make hooks` | Instala os git hooks do pre-commit (Conventional Commits + Linters) |
| `make migrate` | Executa as migrações do banco de dados no container |
| `make migrations` | Cria novas migrações Django (`makemigrations`) |
| `make shell` | Abre o shell interativo do Django (`manage.py shell`) |
| `make superuser` | Cria um superusuário no Django |
| `make bash` | Abre um terminal interativo dentro do container do serviço |
| `make test` | Executa a suíte de testes com pytest (`pytest -v`) |
| `make test-cov` | Executa os testes com relatório de cobertura |
| `make test-smoke` | Executa os smoke tests do modelo matemático |
| `make lint` | Executa a verificação estática com `flake8` |
| `make format` | Formata o código com `black` e `isort` |
| `make migrations-check` | Verifica models sem migration gerada (checagem do CI) |
| `make check` | Executa todas as checagens do CI localmente (`lint` + `test` + `migrations-check`) |

> 📖 **documentação completa:** Para mais detalhes sobre a arquitetura do sistema, integração com outros módulos e guias de uso, acesse a [Documentação Oficial do MeasureSoftGram](https://fga-eps-mds.github.io/MeasureSoftGram-Docs/) e a seção específica do [Componente Service](https://fga-eps-mds.github.io/MeasureSoftGram-Docs/docs/componente-service).

---

## Endpoints

A documentação interativa das rotas da API (Swagger / OpenAPI) está disponível em:
- [http://localhost:8080/swagger/](http://localhost:8080/swagger/)

---

## Como Rodar os Testes

### Via Makefile (Recomendado)

```bash
# Executa todos os testes
make test

# Executa testes com relatório de cobertura
make test-cov

# Executa os smoke tests do modelo matemático
make test-smoke

# Validação completa (lint + testes + migrations)
make check
```

### Localmente com `uv` (Fora do Docker)

O gerenciamento de dependências utiliza [`uv`](https://github.com/astral-sh/uv) com `pyproject.toml` e `uv.lock`.

1. Instale o `uv` (caso ainda não tenha):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. Sincronize as dependências:
   ```bash
   uv sync
   ```
3. Execute os testes:
   ```bash
   uv run pytest src -v
   ```

---

## Informações Adicionais

- **Docker Hub:** [MeasureSoftGram Service](https://hub.docker.com/r/measuresoftgram/service)
- **Documentação:** [MeasureSoftGram Docs](https://fga-eps-mds.github.io/MeasureSoftGram-Docs/)
- **Guia de Contribuição:** Veja nosso [Guia de Contribuição](https://fga-eps-mds.github.io/MeasureSoftGram-Docs/docs/como-contribuir) e o arquivo [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

Este projeto está sob a licença AGPL-3.0.
