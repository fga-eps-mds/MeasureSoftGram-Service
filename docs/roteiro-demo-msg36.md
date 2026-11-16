# Roteiro de execução e demonstração — MSG36

## Estado e pendências

- Branch: `feat/MSG36-quality-analysis`, com a implementação versionada para revisão.
- Base: PR #105, ainda não integrada na consulta feita durante a implementação.
- Backend validado com Python 3.12, lock do projeto e PostgreSQL 18 temporário.
- Falta executar a stack Docker real, conferir as telas com o Front e disparar a
  Action real. Os testes do backend não substituem essa validação integrada.
- Homologação não foi alterada. Sua atualização exige backup e parada dos
  escritores antigos antes das migrations finais.

## Antes de subir

Execute dentro de `2026.2-MeasureSoftGram-Service`:

```sh
git branch --show-current
git status --short
docker info
make env
```

Confirme a branch acima e preserve eventuais alterações locais antes de trocar de
branch. Para levar a implementação a outra máquina, atualize as referências remotas
e faça checkout desta branch. Apenas fazer checkout da develop não traz a implementação
enquanto a PR não for integrada.

Revise os arquivos reais em `env-vars/`. Não copie o template sobre arquivos já
configurados. O template deixa `GITHUB_TOKEN_ENCRYPTION_KEYS` vazio: configure uma
chave Fernet em ambiente novo antes de migrar. Em banco existente, preserve a chave
já utilizada; trocar sem manter a antiga impede ler tokens previamente criptografados.
Para gerar uma chave em ambiente novo sem depender do Python local:

```sh
docker compose build service
docker compose run --rm --no-deps service python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Copie o resultado para `GITHUB_TOKEN_ENCRYPTION_KEYS` no arquivo real
`env-vars/.service.env`. Para a demonstração local, mantenha `CREATE_FAKE_DATA=FALSE`
se quiser preparar a massa explicitamente em vez de gerá-la a cada inicialização.
Confira também o Postgres configurado nos envs. Dentro do Compose o host é `db` e
usa a porta interna 5432; a porta publicada no host tem outro valor.

## Subir e conferir

```sh
docker compose up -d db service
docker compose logs --tail=100 service
curl -fsS http://localhost:8080/health/
docker compose exec service python manage.py check
make migrations-check
```

O Compose atual executa `migrate` e `load_initial_data` antes do runserver.
Reconstrua a imagem com `docker compose build service` quando mudar dependências;
um restart sozinho não atualiza o ambiente da imagem.

Não use `make clear`/`docker compose down -v` em um banco que precisa preservar:
isso remove volumes. Não execute o roteiro sobre homologação como se fosse um banco descartável.

## Preparar a apresentação

Para contas e valores fixos de teste de interface:

```sh
docker compose exec service python manage.py seed_e2e
```

O seed usa, por padrão, usuário `e2e` e senha `e2e-senha`, configuráveis pelos envs
E2E. Ele cria produto, repositório e release próprios. Seus números são fixtures
fixas de interface, não evidência de coerência matemática do Core.

Para massa calculada das organizações locais de demonstração:

```sh
docker compose exec service python manage.py load_initial_data --reset-demo-analyses
```

Esse reset recria AQs somente no escopo de demonstração reconhecido pelo comando.
A massa calculada e as fixtures E2E têm objetivos diferentes; use a primeira para
explicar coerência das cinco camadas. As fixtures especiais de badges são parciais.

## Mostrar uma execução nova no backend

Abra:

```sh
docker compose exec service python manage.py shell
```

Cole o bloco abaixo. Ele chama a view real dentro do Django com autenticação de
teste; não é um disparo da Action no GitHub nem uma prova do caminho HTTP externo.

```python
from organizations.models import Repository
from rest_framework.test import APIClient
from utils.demo_payload import demo_payload

repo = Repository.objects.get(name="e2e-repo")
org = repo.product.organization
client = APIClient()
client.force_authenticate(org.admin)
url = f"/api/v1/organizations/{org.pk}/products/{repo.product_id}/repositories/{repo.pk}/calculate/math-model/"
before = repo.quality_analyses.count()
response = client.post(url, demo_payload(), format="json")
print(response.status_code, response.data.get("analysis"), response.data.get("release"))
print("Análises:", before, "->", repo.quality_analyses.count())
analysis = repo.quality_analyses.first()
print("Camadas:", [getattr(analysis, name).count() for name in (
    "collected_metrics", "calculated_measures", "calculated_subcharacteristics",
    "calculated_characteristics", "tsqmis",
)])
```

Esperado: HTTP 201, uma AQ a mais, release preenchida enquanto a release E2E
estiver ativa e contagens positivas nas cinco camadas. Repita o POST: outra AQ deve
ser criada sem substituir a anterior. Se vier 400, examine `response.data` antes
de afirmar que foi salvo.

## Validar os cenários de borda sem apagar dados da apresentação

```sh
make test
```

O Makefile usa settings de testes e um banco de testes separado. Os testes cobrem
exclusão de release, rollback, sobreposição, execução fora de release e consulta
sem misturar AQs. Excluir uma release manualmente para demonstrar é desnecessário.

## Explicação em um minuto

Uma AQ representa uma execução da coleta e do cálculo para um repositório.
Métricas, medidas, subcaracterísticas, características e TSQMI guardam a referência
para essa mesma AQ. A AQ guarda a release ativa e a configuração usada. Nova
execução cria nova AQ; a tela da release consulta a mais recente por repositório.
Fechar uma release não calcula nada. Alterar as datas não muda vínculos já salvos.

Fora de release ativa, a coleta continua válida (201), com release nula e aviso.
Entrada incompleta pode produzir AQ parcial; se nada for calculável, retorna 400.
Duas releases ativas para o mesmo repo retornam 400, sem escolha arbitrária.
Dados antigos preservados pelo backfill são marcados como legados/parciais: não
prometemos reconstruir a execução histórica que nunca teve identidade explícita.
