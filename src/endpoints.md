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

### Distribuição entre as análises (US21.03)

Cada análise é uma execução da coleta (Action ou CLI) no repositório: cada chamada de `calculate/math-model/` grava uma linha de TSQMI, característica, subcaracterística e medida, todas com o mesmo `created_at` das métricas da coleta.

#### Endpoint que retorna as análises e o resumo estatístico de uma entidade do modelo num repositório, na release
GET /api/v1/organizations/1/products/1/analysis-distribution/?release_id=1&repository_id=3&level=characteristic&key=reliability

Parâmetros:
- `release_id` (obrigatório): release do produto. Entram as análises entre o dia de `start_at` e o dia de `end_at`, inclusive.
- `repository_id` (obrigatório): repositório do produto.
- `level` (obrigatório): `tsqmi`, `characteristic`, `subcharacteristic`, `measure` ou `metric`.
- `key`: chave da entidade, obrigatória abaixo do TSQMI. Precisa fazer parte da pré-configuração vigente na release (mesma regra da Análise por Entidade). No nível `metric`, só as gravadas com `qualifier = TRK` (as do GitHub), que são as que têm um valor por análise.

Erros: parâmetro ausente, nível inválido, entidade fora da configuração da release ou métrica sem valor por análise (as do SonarQube, gravadas por arquivo) recebem 400; release ou repositório fora do produto, ou usuário que não é membro da organização, recebe 404.

`period`: quantidade de análises da entidade e as datas da primeira e da última (`null` sem análise).

`entity` e cada item de `children` trazem `analyses` (data, valor e `is_outlier`, em ordem de data) e `summary`. `metric_type` vem preenchido só no nível `metric`. As linhas de característica gravadas pelo fechamento da release (`release` preenchida) não são análises e ficam fora.

`children`: os filhos da entidade, na ordem da configuração da release. TSQMI → características, característica → subcaracterísticas, subcaracterística → medidas, medida → métricas `TRK`, métrica → lista vazia. Filhos sem análise na janela ficam fora (por exemplo, a `coverage` da `test_coverage`, que só tem valor por arquivo). A série de cada entidade é lida sozinha, sem casar as camadas pela data.

`summary`:
- `p10`, `q1`, `median`, `q3` e `p90` pelo método `inclusive`, o mesmo do `QUARTIL.INC` e do `PERCENTIL.INC` das planilhas.
- `iqr` = Q3 − Q1; `lower_limit` = Q1 − 1,5 × IQR; `upper_limit` = Q3 + 1,5 × IQR; `outliers` é a quantidade de análises fora dos limites.
- `skewness`: assimetria amostral ajustada, a mesma do `DISTORÇÃO`: n / ((n − 1)(n − 2)) · Σ((x − média) / s)³, com s amostral. `null` com menos de 3 análises ou com desvio zero.
- Sem análise, `count` e `outliers` vêm 0 e os demais campos `null`. Com uma análise, todos os quantis são o próprio valor e o IQR é 0.
- Os valores vêm sem arredondamento.

```json
{
  "release": {"id": 1, "release_name": "R2", "start_at": "2026-08-17T00:00:00-03:00", "end_at": "2026-10-16T00:00:00-03:00"},
  "repository": {"id": 3, "name": "2026.2-MeasureSoftGram-Service"},
  "level": "characteristic",
  "key": "reliability",
  "period": {"count": 60, "first": "2026-08-17T10:02:00-03:00", "last": "2026-10-16T18:40:00-03:00"},
  "entity": {
    "key": "reliability", "name": "Reliability", "level": "characteristic", "metric_type": null,
    "analyses": [{"date": "2026-08-17T10:02:00-03:00", "value": 0.55, "is_outlier": false}],
    "summary": {"count": 60, "min": 0.2, "p10": 0.43, "q1": 0.49, "median": 0.55, "q3": 0.62, "p90": 0.66,
                "max": 0.9, "iqr": 0.13, "lower_limit": 0.295, "upper_limit": 0.815, "outliers": 3,
                "mean": 0.55, "skewness": -0.16}
  },
  "children": [
    {"key": "testing_status", "name": "Testing Status", "level": "subcharacteristic", "metric_type": null, "analyses": [...], "summary": {...}}
  ]
}
```

### Relações e correlações (US21.04)

Correlação entre as características (ou subcaracterísticas) de um repositório ao longo das releases: a função f<sub>σ</sub> do modelo matemático (equação 9), calculada pelo Core (`core.transformations.correlation_function`). A matriz RD tem uma release por linha e uma entidade por coluna; RD_Corr usa **Pearson** se todas as colunas forem normais (Shapiro-Wilk, nível de 5%) e **Spearman** se não.

#### Endpoint que retorna a matriz de correlação de um repositório
GET /api/v1/organizations/1/products/1/correlation/?repository_id=3&level=characteristic

Parâmetros:
- `repository_id` (obrigatório): repositório do produto.
- `level` *(opcional)*: `characteristic` (padrão) ou `subcharacteristic`.

Erros: `repository_id` ausente ou `level` inválido recebem 400; repositório fora do produto, ou usuário que não é membro da organização, recebe 404.

Regras:
- `entities`: as entidades do nível na configuração da release mais recente do repositório, na ordem dela.
- `releases`: as linhas de RD, da mais antiga para a mais nova. Entram as releases do produto que incluem o repositório (mesma regra do `release-history`) em que ele tem valor para todas as entidades. O valor é o da última análise na janela da release; as linhas de característica gravadas pelo fechamento da release (`release` preenchida) não são análises e ficam fora. `excluded_releases` conta as releases deixadas de fora por falta de valor.
- `method`: `pearson` ou `spearman`. `non_normal`: quantidade de colunas sem distribuição normal (uma coluna constante conta como não normal).
- `critical_value`: \|r\| a partir do qual o coeficiente é significativo com o número de releases usadas (teste t bicaudal, nível de 5%). Com 20 releases, 0,44.
- `pairs`: o triângulo de baixo da matriz, cada entidade (`row`) com as que vêm antes dela (`column`), com `coefficient`, `p_value` e `significant` (p < 0,05). Um par com uma entidade sem variação vem com `coefficient` e `p_value` `null` e `significant: false`. Os valores vêm sem arredondamento.
- Com menos de 2 entidades ou menos de 3 releases com valor, `pairs` vem vazia, `method`, `non_normal` e `critical_value` vêm `null`, e `reason` diz o motivo: `insufficient_entities` ou `insufficient_releases`. Fora isso, `reason` é `null`.

```json
{
  "repository": {"id": 3, "name": "2026.2-MeasureSoftGram-Service"},
  "level": "characteristic",
  "entities": [
    {"key": "reliability", "name": "Reliability"},
    {"key": "maintainability", "name": "Maintainability"},
    {"key": "functional_suitability", "name": "Functional Suitability"}
  ],
  "releases": [{"id": 1, "release_name": "R1", "start_at": "...", "end_at": "..."}, "... (20 releases)"],
  "excluded_releases": 1,
  "method": "spearman",
  "non_normal": 3,
  "critical_value": 0.4438,
  "pairs": [
    {"row": "maintainability", "column": "reliability", "coefficient": 0.559, "p_value": 0.0104, "significant": true},
    {"row": "functional_suitability", "column": "reliability", "coefficient": 0.4862, "p_value": 0.0297, "significant": true},
    {"row": "functional_suitability", "column": "maintainability", "coefficient": 0.9282, "p_value": 3.7e-09, "significant": true}
  ],
  "reason": null
}
```
