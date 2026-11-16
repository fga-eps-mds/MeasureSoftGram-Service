# Análises de qualidade por execução — MSG36

Implementação das issues #101, #102, #103 e #104, sobre a modelagem da PR #105.
Branch local: `feat/MSG36-quality-analysis`. A PR #105 ainda precisa ser integrada;
esta branch inclui sua base. A documentação central está na issue DOC #309.

## Contrato da Action

Cada POST válido em `calculate/math-model/` cria uma `QualityAnalysis` e associa
as cinco camadas ao mesmo `analysis_id`, numa transação. A configuração usada no
cálculo é guardada na AQ. A release ativa considera o dia local, inclusive o dia
final, o produto e os repositórios selecionados. Release sem seleção explícita
abrange os repositórios do produto. Duas candidatas ativas retornam 400 sem gravar.

A resposta preserva as cinco coleções existentes e acrescenta `analysis` (id),
`release` (id ou null), `is_partial` e `missing_inputs`. Fora de release ativa,
o status permanece 201 e a resposta contém `warning`; o histórico do repo continua
sendo gravado. Métricas nulas são omitidas e registradas nas entradas faltantes.
Se nenhuma característica puder ser calculada, permanece o erro 400 já existente.

O campo `release` foi removido de `CalculatedCharacteristic`; a navegação é
`record.analysis.release`. Excluir release/configuração deixa a referência da AQ
nula, preservando as camadas. Excluir AQ remove suas cinco camadas em cascata.

## Consultas

`releases/analyses.py` centraliza resolução, última AQ por repositório
(`DISTINCT ON`, desempate por id) e histórico cronológico. Os leitores de releases
usam as AQs vinculadas, sem associação por janela temporal. Uma AQ parcial recente
não recebe valores de uma execução anterior. Editar as datas não reatribui AQs.
A configuração já registrada numa AQ tem precedência sobre a inferência temporal
para exibir a árvore da release. Distribuição estatística consulta o histórico
completo das AQs, preservando o instante da execução em cada ponto.

O cron, os testes exclusivos dele e `django-apscheduler` foram removidos. O
`uv.lock` também foi atualizado. Nenhum cálculo de qualidade ocorre no fechamento
da release ou na inicialização dos workers.

## Migração de bancos existentes

Antes de alterar o ambiente, faça backup e interrompa os escritores antigos.
Aplique o código e as migrations como uma atualização coordenada: um processo
antigo não consegue escrever no esquema final com `analysis` obrigatório.

```sh
python manage.py migrate
python manage.py makemigrations --check --dry-run
```

A migration `math_model/0002_backfill_legacy_analyses.py` roda antes da retirada do
campo legado e da obrigatoriedade das cinco FKs. Não descarta resultados:

- Registros sem AQ são agrupados pelo repositório, instante exato e release
  explicitamente conhecida. Não se usa tolerância temporal nem uma AQ genérica.
- A release legada de uma característica é preservada na AQ. Para camadas sem
  vínculo explícito, a release permanece nula; não é inferida pelas datas.
- As AQs reconstruídas recebem `is_partial=True` e
  `missing_inputs=["legacy:execution_identity_unverified"]`. A correspondência
  com uma execução histórica completa não pode ser garantida.
- Registros que já tinham AQ permanecem com seu vínculo original.

Isso mantém o histórico do repositório e não apresenta resultados antigos como
execuções completas verificadas. Em bases grandes, reserve uma janela de
manutenção: o backfill percorre e atualiza os registros existentes. A reversão de
migrations não recria a informação removida do campo legado; para retorno exato
ao esquema/dados anteriores, restaure o backup.

## Massa de homologação

Os comandos abaixo são instruções de operação; não foram executados em homologação.
A limpeza validada em testes foi feita somente em bancos temporários.

```sh
python manage.py load_initial_data --reset-demo-analyses
```

Esse comando recria análises apenas nas organizações locais de demonstração já
reconhecidas pelo seed; organizações importadas do GitHub e organizações de usuários
fora desse escopo são preservadas. Gera 30 execuções em 90 dias, pelo pipeline real
da Action, com cinco camadas e configuração consistente. Sem a opção de reset,
`--fake-data` não duplica análises existentes. As fixtures especiais de badges
continuam com notas fixas para inspeção visual e são identificadas como parciais;
não representam uma execução completa do Core.

Para uma massa calculada no repositório selecionado:

```sh
python manage.py seed_demo_data --repos 'NOME-DO-REPOSITORIO-DE-DEMO' --days 90 --clean-all
```

`--clean-all` remove todas as AQs dos repositórios selecionados antes de gerar a
massa. O alias antigo `--clean-tsqmi` também recria a AQ inteira, para não deixar
camadas inconsistentes. O seed cria uma release de demonstração se o produto ainda
não tiver planejamento; caso contrário respeita as releases existentes. Sem
`--repos`, o comando mantém a seleção histórica de todos os repositórios.

`seed_e2e` preserva seus valores fixos de teste de interface, com uma AQ por data,
as cinco camadas associadas e a release explícita. Essas fixtures determinísticas
não substituem o seed calculado para avaliar coerência matemática em homologação.

## Validação

As verificações locais usam Python 3.12, dependências do `uv.lock` e PostgreSQL 18
isolado. Há cobertura de POSTs repetidos, parcialidade, rollback na persistência,
exclusão de release, AQ mais recente sem misturar execuções, desempate por id,
editar datas, instalação vazia e upgrade sobre as cinco camadas legadas.

Resultado em 15/11/2026: suíte completa com 686 casos registrados no JUnit,
zero falhas, erros ou skips; teste adicional de reset dos dados de demonstração
também aprovado. Lint, `manage.py check`, checagem de migrations, geração do
OpenAPI e `git diff --check` aprovados. Relatórios temporários:
`/tmp/msg36-final.xml` e `/tmp/msg36-reset.xml`.

```sh
pytest src
flake8 -j1 src/
python src/manage.py makemigrations --check --dry-run
```
