TSQMI
characteristics
SubCharacteristics:
Measures
Metrics


## Endpoints que retorna o catálogo de entidades suportadas pelo sistema atualmente

#### Lista todas as métricas conhecidas pelo repositório
GET /api/v1/metrics/ OK

#### Lista todas as medidas suportadas pelo repositório
GET /api/v1/measures/ OK

#### Lista todas as subcharacteristics suportadas pelo repositório
GET /api/v1/subcharacteristics/ OK

#### Lista todas as characteristics suportadas pelo repositório
GET /api/v1/characteristics/ OK

#### Lista a matrix de balanceamento para todas as características suportadas

GET api/v1/balance-matrix/ OK

## Endpoints que cadastram ou solicitam o cálculo de uma entidade

#### Registra uma nova **métrica** em um repositório
POST /api/v1/orgs/1/repositories/1/create/metrics/ OK

#### Endpoint que salva todas as métricas contidas no json do sonarqube
POST /api/v1/orgs/1/repositories/1/create/metrics/sonarqube/ OK

#### Endpoint que salva todas as métricas contidas no json do github
POST /api/v1/orgs/1/repositories/1/create/metrics/github/ OK
/api/v1/orgs/1/repositories/1/create/metrics/gitlab/

#### Calcula e retorna o valor de uma **medida** em um repositório
POST /api/v1/orgs/1/repositories/1/calculate/measures/ OK

#### Calcula e retorna o valor atual de uma **subcharacteristics** em um repositório
POST /api/v1/orgs/1/repositories/1/calculate/subcharacteristics/ OK

#### Calcula e retorna o valor atual de uma **characteristics** em um repositório
POST /api/v1/orgs/1/repositories/1/calculate/characteristics/ OK

#### Calcula e retorna o valor atual do **tsqmi** do repositório
POST /api/v1/orgs/1/repositories/1/create/tsqmi/


## Endpoints para leitura de dados já calculados/cadastrados (READ-ONLY)

### Métrics

#### Endpoint que retorna uma lista com o valor atual de todas as métricas associadas com um projeto
GET /api/v1/orgs/1/repositories/1/metrics/ OK

#### Endpoint que retorna o valor atual de uma métrica associada a um projeto
GET /api/v1/orgs/1/repositories/1/metrics/1/ OK

#### Endpoint que retorna uma lista com o histórico de valores de uma métrica de um projeto
GET /api/v1/orgs/1/repositories/1/history/metrics/1/ OK

O histórico de métricas aceita `?qualifier=TRK` para trazer só o valor do repositório, sem os valores por arquivo (`FIL`, `UTS`), e `?start_at=`/`?end_at=` para filtrar por data.

Em todos os históricos (métricas, medidas, subcaracterísticas, características e TSQMI) vêm os `MAXIMUM_NUMBER_OF_HISTORICAL_RECORDS` registros **mais recentes** (padrão 100), ordenados do mais antigo para o mais novo.

#### Endpoint que retorna o valor atual das metrics e de seus componentes
GET /api/v1/orgs/1/repositories/1/tree/metrics/

#### Endpoint que retorna o valor atual de uma metric e de seus componentes
GET /api/v1/orgs/1/repositories/1/tree/metrics/1/


### Medidas

#### Endpoint que retorna uma lista com o valor atual de todas as medidas associadas com um projeto
GET /api/v1/orgs/1/repositories/1/measures/ OK

#### Endpoint que retorna o valor atual de uma medida associada a um projeto
GET /api/v1/orgs/1/repositories/1/measures/1/ OK

#### Endpoint que retorna uma lista com o histórico de valores de uma medida de um projeto
GET /api/v1/orgs/1/repositories/1/history/measures/1/ OK

#### Endpoint que retorna o valor atual das measures e de seus componentes
GET /api/v1/orgs/1/repositories/1/tree/measures/

#### Endpoint que retorna o valor atual de uma measure e de seus componentes
GET /api/v1/orgs/1/repositories/1/tree/measures/1/


### subcharacteristics

#### Endpoint que retorna uma lista com o valor atual de todas as subcharacteristics associadas com um projeto
GET /api/v1/orgs/1/repositories/1/subcharacteristics/ OK

#### Endpoint que retorna o valor atual de uma subcharacteristic associada a um projeto
GET /api/v1/orgs/1/repositories/1/subcharacteristics/1/ OK

#### Endpoint que retorna uma lista com o histórico de valores de uma subcharacteristic de um projeto
GET /api/v1/orgs/1/repositories/1/history/subcharacteristics/1/ OK

#### Endpoint que retorna o valor atual das subcharacteristics e de seus componentes
GET /api/v1/orgs/1/repositories/1/tree/subcharacteristics/

#### Endpoint que retorna o valor atual da subcharacteristic e de seus componentes
GET /api/v1/orgs/1/repositories/1/tree/subcharacteristics/1/


### characteristics

#### Endpoint que retorna uma lista com o valor atual de todas as characteristics associadas com um projeto
GET /api/v1/orgs/1/repositories/1/characteristics/ OK

#### Endpoint que retorna o valor atual de uma characteristic associada a um projeto
GET /api/v1/orgs/1/repositories/1/characteristics/1/ OK

#### Endpoint que retorna uma lista com o histórico de valores de uma characteristic de um projeto
GET /api/v1/orgs/1/repositories/1/history/characteristics/1/

#### Endpoint que retorna o valor atual das characteristics e de seus componentes
GET /api/v1/orgs/1/repositories/1/tree/characteristics/

#### Endpoint que retorna o valor atual da characteristic e de seus componentes
GET /api/v1/orgs/1/repositories/1/tree/characteristics/1/


### tsqmi

#### Endpoint que retorna o valor atual do tsqmi de um projeto
GET /api/v1/orgs/1/repositories/1/tsqmi/

#### Endpoint que retorna o histórico do tsqmi de um projeto
GET /api/v1/orgs/1/repositories/1/tsqmi/history


#### Endpoint que retorna o valor atual do tsqmi e de seus componentes
GET /api/v1/orgs/1/repositories/1/tsqmi/tree/


## Endpoints da árvore do modelo de qualidade (Metamodelo)

#### Retorna a árvore hierárquica do modelo de qualidade por release (ou atual)
Retorna a árvore TSQMI → características → subcaracterísticas → medidas → métricas da release especificada com pesos, descrições e valores de referência das medidas (`min_threshold` e `max_threshold`).
Caso o parâmetro `release_id` não seja informado via query string, retorna a árvore da configuração atual do produto.

- **URL:** `GET /api/v1/organizations/{organization_id}/products/{product_id}/quality-model-tree/`
- **Query Params:**
  - `release_id` *(opcional, inteiro)*: ID da release da qual se deseja obter a árvore do modelo. Caso ausente, utiliza a configuração vigente do produto.
- **Regra de resolução da configuração:**
  1. Se `release_id` informado: seleciona a `ReleaseConfiguration` mais recente do produto com `created_at <= release.end_at`.
  2. Fallback: caso nenhuma configuração satisfaça a condição (ex: release com datas anteriores), seleciona a configuração mais antiga do produto.
  3. Se `release_id` omitido: seleciona a configuração atual (`product.release_configuration.first()`).
- **Respostas:**
  - `200 OK`: Lista com o nó raiz `tsqmi` e seus descendentes. Caso o produto não possua configuração cadastrada, retorna lista vazia `[]`.
  - `400 Bad Request`: `release_id` informado não é um número inteiro válido.
  - `401 Unauthorized`: Usuário não autenticado.
  - `404 Not Found`: Organização/produto não encontrado, usuário não é membro da organização, ou `release_id` não pertence ao produto.

## Análise por entidade (US21.02)

#### Valor de uma entidade em cada repositório do produto, numa release
GET /api/v1/organizations/1/products/1/entity-analysis/?release_id=1&level=characteristic&key=maintainability

Parâmetros:
- `release_id`: release do produto (obrigatório).
- `level`: `characteristic`, `subcharacteristic`, `measure` ou `metric`.
- `key`: chave da entidade. Precisa fazer parte da pré-configuração vigente na release, senão responde 404. Vale a mesma regra da árvore do modelo (TASK21.01.01): a mais recente criada até o `end_at` ou, se nenhuma foi criada até lá, a mais antiga do produto.

Regra do valor: o último calculado (ou coletado, para métricas) entre o dia de `start_at` e o dia de `end_at` da release, ambos inclusive, a mesma do gráfico de pulso do TSQMI. Repositório sem valor na janela vem com `value: null`. Métricas usam o valor bruto no nível do projeto (`qualifier = TRK`); uma métrica da configuração que não tem valor nesse nível (as do SonarQube, gravadas por arquivo) responde 400. Os repositórios são os da release, sempre restritos ao produto dela; se ela não tiver nenhum, todos os do produto.

`reference`: `{"goal": 0.7}` (meta da release, de 0 a 1) para características, `{"min_threshold": 60, "max_threshold": 100}` para medidas e `null` nos outros níveis.

`children`: os filhos da entidade naquele repositório, com o peso da pré-configuração e o valor pela mesma regra. Característica → subcaracterísticas, subcaracterística → medidas, medida → métricas (sem peso), métrica → lista vazia.

```json
{
  "release": {"id": 1, "release_name": "v1.0", "start_at": "...", "end_at": "..."},
  "level": "characteristic",
  "entity": {"key": "maintainability", "name": "Maintainability"},
  "reference": {"goal": 0.6},
  "repositories": [
    {
      "id": 3, "name": "parser", "value": 0.42, "created_at": "...",
      "children": [{"key": "modifiability", "name": "Modifiability", "weight": 100, "value": 0.42, "created_at": "..."}]
    },
    {"id": 4, "name": "web", "value": null, "created_at": null, "children": [...]}
  ]
}
```

#### Entidades da pré-configuração da release, por nível
GET /api/v1/organizations/1/products/1/entity-analysis/entities/?release_id=1

Responde `{"characteristic": [{"key", "name"}], "subcharacteristic": [...], "measure": [...], "metric": [...]}`. No nível `metric` entram só as métricas gravadas com `qualifier = TRK` em algum repositório da release (hoje, as do GitHub).

## Dashboards por release (US07.01)

Dados da Visão Geral de Qualidade, da Evolução Temporal e do gráfico da tela do repositório, para o Front desenhar sem o Grafana. Qualquer membro da organização tem acesso (não só o admin); quem não é membro recebe 404.

Regra do valor: a mesma da análise por entidade, o último calculado (ou coletado, para métricas) entre o dia de `start_at` e o dia de `end_at` da release, ambos inclusive. Por isso os valores podem ser diferentes dos do Grafana, que usava a média dos últimos 7 dias (planejado × realizado) e dos últimos 30 dias (radar). Os repositórios são os da release, restritos ao produto; se ela não tiver nenhum do produto, todos os do produto. A configuração da release segue a regra da árvore do modelo (TASK21.01.01).

#### Totais da Visão Geral na release
GET /api/v1/organizations/1/products/1/release-dashboard/summary/?release_id=1

Cada total conta entidades distintas, e não linhas do histórico:
- `characteristics`, `subcharacteristics`, `measures`, `metrics`: entidades da configuração da release (métricas são as das medidas configuradas).
- `repositories`: repositórios da release com TSQMI calculado na janela.
- `files`: arquivos distintos (`qualifier = FIL`) coletados na janela. O mesmo caminho em dois repositórios conta como dois arquivos.

```json
{
  "release": {"id": 1, "release_name": "v1.0", "start_at": "...", "end_at": "..."},
  "totals": {"characteristics": 3, "subcharacteristics": 5, "measures": 9, "metrics": 18, "repositories": 2, "files": 140}
}
```

#### Radar, planejado × realizado e TSQMI por repositório na release
GET /api/v1/organizations/1/products/1/release-dashboard/characteristics/?release_id=1

- `characteristics`: as características da configuração, na ordem dela. `planned` é a meta da release (de 0 a 1, `null` sem meta), `accomplished` é a média entre os repositórios com valor e `dispersion` o desvio padrão (populacional) entre eles. Sem nenhum valor, os dois vêm `null`.
- `repositories`: o TSQMI e o valor de cada característica no repositório (radar). Sem valor na janela, vem `value: null`.

```json
{
  "release": {"id": 1, "release_name": "v1.0", "start_at": "...", "end_at": "..."},
  "characteristics": [
    {"key": "reliability", "name": "Reliability", "planned": 0.7, "accomplished": 0.72, "dispersion": 0.04}
  ],
  "repositories": [
    {
      "id": 3, "name": "api",
      "tsqmi": {"value": 0.81, "created_at": "..."},
      "characteristics": [{"key": "reliability", "value": 0.76, "created_at": "..."}]
    }
  ]
}
```

Respostas: `400` sem `release_id` (ou com valor não numérico), `404` se a release não for do produto ou o usuário não for membro da organização.

#### Evolução de um nível do modelo no repositório, com um ponto por release
GET /api/v1/organizations/1/products/1/repositories/1/release-history/?level=characteristic&keys=reliability,maintainability

Parâmetros:
- `level`: `characteristic`, `subcharacteristic`, `measure` ou `metric` (obrigatório).
- `keys` *(opcional)*: chaves separadas por vírgula. Sem `keys`, vêm as entidades do nível na configuração atual do produto. Chaves que não existem são ignoradas.

Entram as releases do produto que incluem o repositório pela mesma regra (inclusive as que não escolheram repositórios do produto), da mais antiga para a mais nova. Cada entidade tem um ponto por release em `history`, na mesma ordem de `releases`, com `value: null` quando não há valor na janela. Métricas usam o valor no nível do projeto (`qualifier = TRK`).

```json
{
  "repository": {"id": 1, "name": "api"},
  "level": "characteristic",
  "releases": [{"id": 1, "release_name": "v1.0", "start_at": "...", "end_at": "..."}, {"id": 2, "release_name": "v2.0", "...": "..."}],
  "entities": [
    {"key": "reliability", "name": "Reliability", "history": [
      {"release_id": 1, "value": 0.5, "created_at": "..."},
      {"release_id": 2, "value": null, "created_at": null}
    ]}
  ]
}
```

Respostas: `400` com `level` inválido, `404` se o repositório não for do produto ou o usuário não for membro da organização.

### Distribuição das métricas por arquivo (US21.03)

#### Endpoint que retorna os valores por arquivo e o resumo estatístico de uma métrica na release
GET /api/v1/organizations/1/products/1/metrics-distribution/?release_id=1&metric=coverage&repository_id=1

Parâmetros:
- `release_id` (obrigatório): release do produto. Usa a última coleta de cada repositório entre o dia de `start_at` e o dia de `end_at`, inclusive.
- `metric` (obrigatório): `coverage`, `complexity`, `functions`, `comment_lines_density`, `duplicated_lines_density` ou `sqale_debt_ratio`. Outra métrica recebe 400.
- `repository_id` (opcional): com ele, a resposta traz os arquivos (`files`) daquele repositório. Sem ele, traz só o resumo de cada repositório da release (ou do produto, se a release não tiver repositórios), em ordem de nome.

Erros: parâmetro obrigatório ausente ou métrica inválida recebe 400; release ou repositório fora do produto, ou usuário que não é membro da organização, recebe 404.

Arquivos com `ncloc = 0` ficam fora; `excluded_files` diz quantos. `reference` traz o mínimo e o máximo da medida que usa a métrica, ou `null`. Repositório sem dados por arquivo na release vem com `files: []`, `summary: null` e `collected_at: null`. Se a última coleta da release não tiver a métrica pedida, vem com `files: []` e `summary: null`, mas com `collected_at` preenchido.

```json
{
  "release": {"id": 1, "release_name": "R1", "start_at": "2026-09-01T00:00:00-03:00", "end_at": "2026-10-15T00:00:00-03:00"},
  "metric": "coverage",
  "reference": {"measure": "test_coverage", "min_threshold": 60, "max_threshold": 100},
  "repositories": [
    {
      "repository_id": 1,
      "repository_name": "api",
      "collected_at": "2026-10-14T21:03:11.120000-03:00",
      "excluded_files": 1,
      "summary": {"count": 2, "min": 60.0, "q1": 65.0, "median": 70.0, "q3": 75.0, "max": 80.0, "mean": 70.0, "std_dev": 10.0},
      "files": [{"path": "src/a.py", "value": 80.0}, {"path": "src/b.py", "value": 60.0}]
    }
  ]
}
```
