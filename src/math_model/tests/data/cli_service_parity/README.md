# Referências de comparação CLI × Service

Geradas em 27/09/2026 usando msgram-core==1.5.4.

Os arquivos calc_msgram.json foram produzidos pelo comando real
msgram calculate da CLI. Os testes do Service chamam o endpoint
pelo cliente de testes do Django e comparam os valores persistidos
com essas referências, usando tolerância relativa de 1e-9 e
absoluta de 1e-12. A CI do Service não executa a CLI.

## Caso GitHub

Origem: fixture da CLI
tests/unit/data/github_fga-eps-mds-2024.1-MeasureSoftGram-DOC-28-07-2024-00-00-22-extracted.metrics.

Configuração: tests/unit/data/msgram.json da CLI.
TSQMI de referência: 0.6944329273822416.

## Caso completo (full/)

Origem: payload sintético _full_payload() de
src/math_model/tests/test_atomicity_smoke.py do Service.

O mesmo payload foi convertido para o formato extraído da CLI,
preservando os valores. A entrada da API, a entrada da CLI,
a configuração e o resultado estão armazenados em full/.

TSQMI de referência: 0.7527099982081088.

## Comportamento protegido

Medidas sem todas as métricas necessárias são omitidas.
Valores presentes iguais a zero continuam válidos.
Somente resultados disponíveis participam das agregações.
Entrada sem característica calculável retorna HTTP 400 no Service.

As referências não devem ser atualizadas apenas para eliminar
uma falha: mudanças exigem nova execução da CLI e análise humana
da diferença.
