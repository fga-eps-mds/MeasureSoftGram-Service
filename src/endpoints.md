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
