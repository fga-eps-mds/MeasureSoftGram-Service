# Segurança: issue #52

Esta contribuição cobre MSG-03 (privacidade), MSG-12 (tokens OAuth em repouso)
e MSG-13 (HTTPS). Issue: https://github.com/fga-eps-mds/2026.2-MeasureSoftGram-DOC/issues/52.

## Autenticação e privacidade

O DRF exige `IsAuthenticated` por padrão. A rota referida como `/users/` na
issue é **`/api/v1/accounts/users/`** neste Service. Acesso anônimo retorna
`401`; usuários autenticados recebem somente `id`, `username`, `first_name`
e `last_name`. O e-mail continua disponível no próprio perfil em
`/api/v1/accounts/`, mas não na listagem de membros.

Exceções públicas explícitas: criação de conta, login local, login GitHub,
validação pré-login do GitHub, Swagger e badges SVG de TSQMI/características.
`/health/` é uma view Django pública sem dados de usuários. Os catálogos de
entidades e a matriz de balanceamento passam a exigir autenticação; clientes
que os consultam devem enviar `Authorization: Token <token-da-api>`.

## Tokens cifrados

`EncryptedTokenField` usa Fernet, da biblioteca `cryptography`. Ao escrever
pelo ORM, cifra o token; ao ler, verifica a integridade e decifra. O código
que chama a API GitHub continua recebendo uma string. A coluna é `TEXT`, pois
a cifra ocupa mais espaço que o token original. O campo não aparece no Admin
nem nos serializers de usuários.

A cifra é reversível porque a aplicação precisa enviar o token ao GitHub.
Isso difere de senhas, que usam hashes. A chave não pode ficar no banco nem
no Git. `SOCIALACCOUNT_STORE_TOKENS=False` evita cópias em texto puro no
`django-allauth`. O adaptador trata o primeiro cadastro; os sinais tratam
conexões e atualizações de contas sociais.

Antes de executar migrations **em desenvolvimento e em produção**, gere uma
chave própria por ambiente:

```bash
uv sync --locked
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Grave o resultado em `GITHUB_TOKEN_ENCRYPTION_KEYS` no arquivo real
`env-vars/.service.env` (ou `deploy/env-vars/.service.env` no layout de deploy).
Não use a chave pública de `config.settings.test`, exclusiva dos testes.
Guarde uma cópia da chave em um gerenciador de segredos. Perdê-la impede
recuperar os tokens; nesse caso será necessário autorizar o GitHub novamente.
A variável aceita chaves separadas por vírgula: a primeira cifra; as demais
permitem ler dados antigos durante uma rotação.

A migration `accounts.0003`:

1. Amplia a coluna para `TEXT`.
2. Valida a chave antes de alterar dados.
3. Cifra tokens existentes; se o usuário não tiver token próprio, recupera
   uma cópia legada do `SocialToken` do GitHub.
4. Remove as cópias em texto puro de `SocialToken` do GitHub.
5. Ativa o campo cifrado no estado do ORM.

Em PostgreSQL, a migration é transacional: falhas desfazem as alterações.
Ela é **irreversível de propósito**, para não restaurar segredos em texto
puro por um rollback automático. Planeje uma janela de manutenção, pare
processos antigos que possam gravar tokens e faça backup restrito antes de
migrar. Após migrar, todas as instâncias precisam usar o código novo e a
mesma chave. Não execute uma versão anterior da aplicação sobre a coluna
cifrada. Para rollback, restaure código e backup anteriores juntos, em
ambiente restrito. Backups anteriores ainda contêm tokens em texto puro;
aplique a política de retenção e proteção da equipe.

Não use SQL direto para escrever tokens, nem exporte usuários por `dumpdata`
para arquivos desprotegidos: a leitura pelo ORM devolve o valor decifrado.
A proteção cobre uma cópia isolada do banco; não protege contra um invasor
que também obtenha a chave ou controle o processo da aplicação.

Para rotação planejada: distribua `nova,antiga`, regrave os tokens pelo ORM
em um processo controlado (sem logs dos valores), confira que todos podem
ser lidos com a nova chave e só então remova a antiga dos processos.
Retenha separadamente as chaves necessárias para restaurar backups antigos.

## HTTPS e implantação conjunta com infraestrutura

`production.py` exige redirecionamento HTTPS, cookies de sessão/CSRF seguros
e HSTS de 31536000 segundos. Variáveis antigas que desligavam essas flags
não têm mais efeito. HSTS não inclui subdomínios nem preload por padrão.
Apenas `/health/` está isento do redirecionamento, para o healthcheck interno.

Topologia prevista:

```text
cliente HTTPS → OpenResty/Nginx de borda → proxy interno → Django
```

A borda deve sobrescrever `X-Forwarded-Proto` com o protocolo real. O proxy
interno conserva apenas o valor exato `https`; demais valores viram `http`.
O Django confia nesse header, por isso a porta interna não pode ficar
acessível à internet. O compose publica **127.0.0.1:8088**, substituindo
`:80`. O arquivo `deploy/nginx/edge-tls.conf.example` é uma referência para
a borda no mesmo host; não é instalado automaticamente pelo workflow.

Se a borda estiver em outra máquina ou container, o responsável deve adaptar
o upstream e `PROXY_BIND_ADDRESS`/`PROXY_HTTP_PORT` no `.env` do compose,
usando rede privada com firewall que permita somente a borda. Tráfego entre
hosts também precisa de um canal protegido. Não configure `0.0.0.0` sem essa
restrição: um cliente poderia forjar o header de HTTPS.

Antes de integrar o PR, combine com o responsável pela infraestrutura:

1. Provisionar certificado válido para `msgram.lappis.rocks`, renovação
   automática e recarga do proxy após renovação; adaptar o desafio ACME.
2. Conferir o template com a topologia real, incluindo WebSockets do Grafana,
   liberar 443 e redirecionar 80 para HTTPS na borda.
3. Restringir a porta interna e ajustar o upstream para a nova publicação.
4. Provisionar a chave de cifragem e backup, sem registrá-los em logs.
5. Atualizar `CSRF_TRUSTED_ORIGINS`, `FRONTEND_PROD_URL`,
   `LOGIN_REDIRECT_URL`, URL da API no Front e callback do OAuth App para
   HTTPS. Confirmar que `ALLOWED_HOSTS` inclui o domínio e `localhost` para
   o healthcheck interno.
6. Implantar em janela coordenada: o entrypoint executa a migration antes
   de iniciar o serviço. Não manter instâncias antigas gravando em paralelo.
7. Executar os testes externos abaixo e anexar os resultados ao PR/issue.

```bash
# Deve redirecionar para HTTPS (301 ou 308), sem servir dados cadastrais.
curl -sS -D - -o /dev/null http://msgram.lappis.rocks/api/v1/accounts/users/
# Deve retornar 401, certificado válido e Strict-Transport-Security.
curl -sS -D - https://msgram.lappis.rocks/api/v1/accounts/users/
# Deve retornar 200 por HTTPS, sem ciclo de redirecionamentos.
curl -sS -D - -o /dev/null https://msgram.lappis.rocks/swagger/
```

Também valide login GitHub pelo Front, consulta das organizações, cookies
seguros no navegador e a renovação do certificado pelo mecanismo adotado.
Não use `curl -k`, pois isso esconderia falhas de certificado.

**Estado da infraestrutura:** a configuração real da borda e o deploy são
responsabilidade de outro integrante. Os arquivos deste PR preparam essa
etapa; não constituem evidência de TLS ativo no servidor. O critério MSG-13
só pode ser encerrado após a validação externa conjunta.

## Testes e revisão

```bash
uv sync --locked
uv run pytest src/accounts src/config/tests -v
uv run pytest src -v
DJANGO_SETTINGS_MODULE=config.settings.test uv run python src/manage.py makemigrations --check --dry-run
```

Os testes usam uma chave pública exclusiva de testes e um banco separado.
Cobrem acesso anônimo/autenticado, privacidade, primeiro cadastro OAuth,
sinais, cifragem vista por SQL, leitura pelo ORM, atualização em lote,
valores vazios, chave incorreta, adulteração, rotação, formulário do Admin,
migration de dados legados, redirecionamento, HSTS e cookies seguros. O teste
da migration usa bancos temporários isolados (SQLite e PostgreSQL) para
aplicar a sequência desde o estado antigo sem reverter a migration
irreversível do banco da suíte. O caso PostgreSQL usa as credenciais de
testes, que precisam de permissão para criar bancos, como a própria suíte.
A CI executa ambos os casos e a suíte principal em PostgreSQL.

A branch segue `fix/52-falhas-seguranca`, com PR para `develop` conforme
`CONTRIBUTING.md`. Use Conventional Commits, inclua a issue do repositório
DOC pelo endereço completo e solicite revisão de outro integrante. Não
marque a ativação TLS em produção como concluída antes das evidências acima.

Referências: [Fernet](https://cryptography.io/en/latest/fernet/),
[campos Django](https://docs.djangoproject.com/en/5.2/howto/custom-model-fields/),
[proxy HTTPS no Django](https://docs.djangoproject.com/en/5.2/ref/settings/#secure-proxy-ssl-header).
