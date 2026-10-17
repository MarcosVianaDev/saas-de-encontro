# Verificação da implementação

## Presente inicial em lotes em 16/10/2026

A distribuição periódica foi separada da fila operacional. O Beat despacha uma varredura com concessão exclusiva no PostgreSQL; `celery_gifts` entrega em lotes de até 25 participantes, com cursor e uma continuação por lote. A migração `passes.0006_initialgiftsweep` mantém a concessão renovável por 120 segundos. Tarefas antigas, ciclos sobrepostos e continuações repetidas são rejeitados; a unicidade do passe continua protegida por lock e constraint. Dev/prod, modelos de ambiente, scripts `full-clean` e verificador dos ambientes incluem o novo worker. [Contrato e implantação](<Operacao e desenvolvimento.md#processamento-assíncrono>).

| Verificação | Resultado |
|---|---|
| Suíte completa `manage.py test tests api --noinput --verbosity 1` | **304 testes aprovados**, sem falhas, erros ou skips |
| Seleção/continuação com 5.000 participantes no PostgreSQL de teste | **200 lotes de 25**, consulta limitada a 26 IDs, sem repetição/perda de IDs; entrega pesada substituída para verificar o loteamento |
| Entregas reais em múltiplos lotes | Passes, ativações, notificações e auditoria criados uma única vez; elegibilidade e horário revalidados |
| Falha individual e publicação interrompida | Rollback da entrega, avanço dos demais e recuperação por nova varredura |
| Concorrência e perda de worker | Dois dispatchers simultâneos publicam uma varredura; duas entregas concorrentes geram um presente; concessão expirada permite recuperação e rejeita token antigo |
| `scripts/verify_celery_queues.py` | **Aprovado com Redis e três workers prefork reais**: fila operacional responde enquanto `exports` e `gifts` estão ocupadas |
| Composes padrão/dev/prod | Dez serviços, três filas exclusivas, concorrência/prefetch 1 e healthchecks do worker de presentes |
| Migrações, scripts e revisão do diff | `makemigrations --check --dry-run` sem alterações adicionais; verificador dos dois `full-clean` aprovado em diretórios temporários; `git diff --check` aprovado |

O cenário de 5.000 participantes verifica limites e paginação; não mede o tempo de gerar 5.000 presentes com likes, arquivos e notificações reais. O orçamento de cinco segundos é verificado entre participantes, sem interromper uma entrega individual. A distribuição preserva a regra de não conceder após o término do evento, mesmo se ainda houver participantes na fila. Logs: `.tools/gift-batches-backend.log` e `.tools/gift-batches-queues.log`. Os testes usam banco descartável e namespace Redis próprio; os serviços em uso foram preservados.

## Docker de desenvolvimento e produção em 16/10/2026

`frontend/Dockerfile` passou a ter estágios de dependências, desenvolvimento, build e produção. A imagem final contém somente Nginx/assets compilados. `docker-compose.dev.yml` preserva o ambiente padrão e `docker-compose.prod.yml` separa imagens, ambientes e persistência, com DEBUG/carga automática desativados, HTTPS no Traefik e workers em filas próprias. As rotas sensíveis do gateway foram consolidadas em `infra/app-routes.conf`. Guia: [Docker: desenvolvimento e produção](<Docker - desenvolvimento e producao.md>).

| Verificação | Resultado |
|---|---|
| Docker build do frontend, target `production`, modo `django` | Aprovado com Node 24.22.0 no build; imagem final Nginx, sem Node/npm |
| Docker build do frontend, target `development` | Aprovado; Vite/HMR preservado |
| Docker build do backend sem bind do código | Aprovado; arquivos locais de mídia, backups, estáticos e ambientes excluídos do contexto |
| `python scripts/verify_docker_environments.py --skip-build` | **Aprovado**: nove serviços de produção saudáveis, projeto/dados isolados, ausência de seed, HTTPS, assets/cache/404/imagens, login/cookies Secure, Admin CSS, aviso entre processos por WSS, demonstração e HMR real na imagem dev |
| Runner com `check-media-delivery.cjs` e `check-realtime.cjs` | **2 cenários e 3 auxiliares aprovados**, preservando mídia autorizada e comunicação em tempo real após compartilhar as rotas Nginx |
| Composes padrão/dev/prod e `git diff --check` | Aprovados; a entrada dev mantém serviços, volumes e rede do Compose padrão |

Os builds Linux iniciais identificaram dependência nativa ausente após falhas TLS de download. A etapa de instalação agora verifica `tsc --version`; os builds finais completos foram aprovados, mantendo as versões do lockfile. As imagens de desenvolvimento/build usam a versão LTS do Node fixada no Dockerfile.

Logs: `.tools/docker-{backend-production-build,frontend-production-build-final,frontend-development-build-final,environments-verification,gateway-browser-regression}.log`. Verificação dos ambientes em `.tools/docker-environments/cf4db59e467e/`; regressão em `.tools/browser-tests/1b3a05c87310/`. Os projetos/volumes de teste e seus arquivos de credenciais foram removidos. O teste HTTPS usa certificado local do Traefik e desativa ACME; a emissão pública depende de domínio/DNS na implantação. Os serviços em uso foram preservados.

## Auditoria das prioridades em 16/10/2026

Os oito itens da lista de prioridade alta/média/estrutural foram conferidos. Foram corrigidas a entrega de estáticos Django/Admin com `DJANGO_DEBUG=0` (Nginx, montagem somente para leitura, MIME e healthchecks) e a ausência de limite específico de denúncias (`DRF_THROTTLE_REPORTS`, 10/min por conta). Os demais itens já estavam implementados e foram verificados novamente. Matriz e contratos em [Verificação das prioridades](<Verificacao das prioridades.md>).

| Verificação | Resultado |
|---|---|
| Suíte completa de backend | **285 testes aprovados**, sem falhas, erros ou skips |
| `python scripts/verify_production_static.py` | **Aprovado com DEBUG=0**: oito assets reais, CSS/JS/SVG, HTTPS encaminhado, erros de arquivo e healthchecks |
| `scripts/verify_celery_queues.py` via shell Django | **Aprovado**: Redis e dois workers reais; operação concluída durante ocupação da fila de exportação |
| Runner com `check-admin.cjs`, `check-realtime.cjs`, `check-media-delivery.cjs`, `check-real.cjs` | **4 cenários e 3 auxiliares aprovados** |
| Compose, montagem de estáticos, filas e sintaxe dos scripts | Aprovados |

Logs em `.tools/audit-{priorities-backend,production-static,celery-queues,priorities-browser}.log`. Os verificadores de produção e navegador usam bancos/containers descartáveis; a prova de Celery usa namespace Redis próprio. Os serviços e dados em uso foram preservados. As alterações de Compose/Nginx requerem recriação dos serviços na implantação.

## Manutenibilidade e validação em 16/10/2026

Os itens 4.1–4.3 foram implementados: entrada React reduzida à montagem da aplicação; seis páginas do participante e componentes compartilhados separados; hooks para sessão, rotas por hash, perfil, ações sociais e sincronização; estado local de buscas/formulários; biografia completa padronizada em 50–200 caracteres; erros Django por campo preservados na API e apresentados pelo cliente. Organização e limites em [Arquitetura do frontend](<Arquitetura do frontend.md>).

| Verificação | Resultado |
|---|---|
| `docker compose run --rm --no-deps -T backend python manage.py test api.test_profile_validation api.test_exceptions --noinput --verbosity 1` | **13 testes novos aprovados** |
| `docker compose run --rm --no-deps -T backend python manage.py test tests api --noinput --verbosity 1` | **283 testes aprovados**, sem falhas, erros ou skips |
| `npm run build --prefix frontend` | TypeScript e Vite aprovados; permanecem os avisos de React Bootstrap/tamanho do bundle |
| `manage.py makemigrations --check --dry-run` | Nenhuma migração adicional; `profiles.0008_alter_participantprofile_bio` incluída |
| `python scripts/run-browser-tests.py` | **23 de 24 cenários e 3 auxiliares aprovados**; identificada interferência de fixtures de mídia no cenário real |
| `python scripts/run-browser-tests.py check-media-delivery.cjs check-real.cjs` | **2 cenários e 3 auxiliares aprovados** após a correção, completando os **24 cenários distintos** |

Logs finais: `.tools/quality-backend-suite-final.log`, `quality-frontend-build-final.log`, `quality-migrations-check.log`, `quality-browser-suite.log` e `quality-browser-regression.log`. Resultados detalhados dos navegadores em `.tools/browser-tests/7dd0b256a4e7/` e `d9a64387f016/`. A migração registra validadores/tamanho do campo e preserva os dados existentes. Os testes usam banco descartável e cache isolado.

A rodada completa revelou que `check-media-delivery.cjs` deixava três fotos públicas extras no ator compartilhado: o teste real seguinte recebia HTTP 400 ao tentar salvar um perfil com seis fotos públicas. O cenário de mídia agora remove somente as fotos, denúncia e evidência que criou, restaura a foto de outfit anterior e o estado original do match, mesmo em caso de falha. A limpeza exige banco com prefixo `test_browser_`. A execução sequencial mídia → perfil real confirmou a correção, incluindo gravação de perfil/filtros, descoberta, mensagem e persistência após reload. Nenhuma validação da aplicação foi relaxada.

## Validação de segurança em 16/10/2026

### Dependências do frontend sem `latest`

`frontend/package.json` e `package-lock.json` passaram a declarar versões exatas para React/React DOM e suas tipagens (**19.3.0**), TypeScript (**7.0.2**) e Vite (**8.3.2**). Foram utilizadas as versões já presentes no lockfile; a comparação das versões resolvidas confirmou que nenhuma dependência direta ou transitiva foi atualizada.

Validação: `npm install --package-lock-only --ignore-scripts --no-audit --no-fund`, instalação limpa com `npm ci --no-audit --no-fund`, `npm run build` (TypeScript/Vite), `npm ls --depth=0` e `git diff --check` aprovados. O build conserva os avisos existentes de diretivas React Bootstrap/tamanho do bundle. Logs: `.tools/frontend-pin-{lock,ci,build,installed}.log`. Os testes de backend/navegador não foram repetidos nesta alteração de manifesto sem atualização das versões instaladas; as últimas execuções permanecem registradas abaixo.

### Mídia protegida entregue pelo Nginx

Fotos de perfil, outfits, fotos administrativas e evidências usam o helper `protected_media_response` após a autorização existente. No Compose, `MEDIA_USE_X_ACCEL_REDIRECT=1` e o Nginx monta mídia somente para leitura, com `internal`, `disable_symlinks` e `sendfile`. Django retorna cabeçalhos e corpo vazio; não abre os arquivos da mídia. Configuração e contrato em [Mídia protegida](<Midia protegida.md>).

| Verificação | Resultado |
|---|---|
| `docker compose run --rm --no-deps -T backend python manage.py test tests api --noinput --verbosity 1` | **270 testes aprovados**, sem falhas, erros ou skips |
| `manage.py check` / `makemigrations --check --dry-run` | Aprovados; nenhuma migração adicional |
| `docker compose config --format json` | Aprovado; entrega acelerada ativa e montagem de mídia somente para leitura |
| Runner com `check-media-delivery.cjs`, `check-admin.cjs`, `check-onboarding.cjs`, `check-realtime.cjs` | **3 cenários e 3 auxiliares aprovados** na primeira rodada; cenário novo reexecutado abaixo |
| `python scripts/run-browser-tests.py check-media-delivery.cjs` | **Cenário de mídia e 3 auxiliares aprovados**, completando os **4 cenários distintos** |

Os **13 novos testes** em `api.test_protected_media` verificam que a resposta acelerada não abre mídia, cabeçalhos, corpo vazio, anexo com nome Unicode, caminhos inválidos, diretórios/arquivos ausentes, symlinks, fallback explícito sem proxy e storage incompatível. Os testes HTTP preservam autorização para fotos próprias/públicas/pós-match, outfits, bloqueios, outros eventos, contas anônimas, remoções, placeholders, vínculo administrativo revogado, evidências e falha de auditoria. O runner Django mantém streaming direto para os testes anteriores; as classes novas habilitam X-Accel explicitamente.

O runner de navegador agora usa **Nginx real** temporário na porta 18080, com a configuração de uso e mídia isolada; backend direto em 18000 e frontends em 18081/18082. `check-media-delivery.cjs` confirmou bytes corretos e imagem renderizada, MIME, cache privado, `nosniff`, nomes com Unicode/caracteres reservados e `%2e%2e` literal, HEAD, Range, negação de acesso direto à pasta/rota interna, match encerrado, evidência como anexo com auditoria e negação após logout. A chamada direta a Daphne retornou somente cabeçalhos e zero bytes. O novo verificador precisou corrigir o uso de URL relativa no cliente HTTP Playwright; sua reexecução passou. Os cenários de painel, onboarding com upload/fotos e WebSocket passaram através do Nginx.

Logs: `.tools/test-protected-media-full.log`, `.tools/protected-media-{check,migrations}.log`, `.tools/browser-tests/8a7d9fed0711/` e `.tools/browser-tests/0f547f41ca96/`. Nenhum ensaio de carga com centenas de downloads simultâneos foi realizado. Recrie o Nginx para incorporar o novo volume e a configuração, além de carregar o código no backend.

### Consultas administrativas e filas Celery separadas

O painel carrega participantes, suspensões, foto primária, contagens, sinais de bloqueio e dados das ocorrências em lote. As contagens usam agregações em subqueries independentes para evitar multiplicar denúncias por bloqueios. A tarefa de exportação e seus retries usam `exports`, consumida por `celery_exports`; `celery_worker` atende somente `celery`, preservando as automações. Os scripts `full-clean` param e recriam ambos os workers.

| Verificação | Resultado |
|---|---|
| `docker compose run --rm --no-deps -T backend python manage.py test tests api --noinput --verbosity 1` | **257 testes aprovados**, sem falhas, erros ou skips |
| `manage.py check` / `makemigrations --check --dry-run` | Aprovados; nenhuma migração adicional |
| `docker compose config --format json` | Configuração válida; comandos dos workers consomem filas distintas |
| `scripts/verify_celery_queues.py` via `manage.py shell` em container separado | Redis e dois workers prefork reais: tarefa operacional concluiu com o worker de exportação ainda ocupado |
| `python scripts/run-browser-tests.py check-admin.cjs check-export-button.cjs check-event-tabs.cjs check-realtime.cjs` | **4 cenários e 3 auxiliares aprovados** |
| Parser PowerShell / `bash -n` para `full-clean` | Sintaxe válida |
| `scripts/verify_full_clean.py` em diretórios temporários | Ambos os blocos de limpeza aprovados; sem reset do banco real |

Os **7 novos testes** são 4 em `api.test_admin_query_efficiency` e 3 em `api.test_celery_queues`. Verificam cards sem consultas adicionais, contagens não multiplicadas, filtros de fotos/suspensões, precedência dos status, motivos e restrições de operador. O painel completo manteve o mesmo número de consultas ao passar de **2 para 100 participantes**, com **99 ocorrências e 99 sinais de bloqueio**, incluindo notas, histórico e evidências. O orçamento nesse cenário é de até 25 queries como administrador e 20 como operador. A resposta ainda contém todos os participantes: o teste não mede paginação, latência, memória nem concorrência de cem usuários.

Os testes de filas verificam publicação por `apply_async` e `send_task`, roteamento das quatro tarefas do Beat para `celery` e preservação da fila `exports` no retry. A verificação real usa prefixo Redis exclusivo e substitui apenas o gerador da tarefa de exportação por uma espera limitada; não cria `ExportJob` nem artefatos e não altera dados da aplicação. Após confirmar a conclusão de uma tarefa operacional, libera a exportação, encerra os workers temporários e remove apenas suas chaves.

Logs: `.tools/test-admin-queues-full.log`, `.tools/verify-celery-queues.log`, `.tools/admin-queues-{check,migrations}.log`, `.tools/verify-full-clean-queues.log` e `.tools/browser-tests/60c397520bfd/`. A versão da aplicação exige recriar backend, workers e Beat para carregar o novo roteamento e iniciar `celery_exports`; mensagens antigas não são transferidas ou apagadas automaticamente. Consulte [Operação e desenvolvimento](<Operacao e desenvolvimento.md#processamento-assíncrono>).

### WebSocket autenticado e recuperação HTTP

ASGI atende WebSocket com sessão, validação de Host/Origin e evento explícito na rota. Avisos de mensagens, notificações e status são publicados após commit pelo Redis Channel Layer. A interface compartilha uma conexão por aba, atualiza por delta ao receber avisos e conserva recuperação HTTP e reconexão. Contrato em [WebSocket e tempo real](<WebSocket e tempo real.md>).

| Verificação | Resultado |
|---|---|
| `docker compose run --rm --no-deps -T backend python manage.py test tests api --noinput --verbosity 1` | **250 testes aprovados**, sem falhas, erros ou skips |
| `npm --prefix frontend run build` | TypeScript/Vite aprovados; avisos existentes de React Bootstrap e bundle |
| `manage.py check` / `makemigrations --check --dry-run` | Aprovados; nenhuma migração adicional exigida pelo WebSocket |
| `nginx -t` com a configuração atual e upstreams locais | Aprovado |
| `python scripts/run-browser-tests.py check-realtime.cjs check-participant-sync.cjs check-event-tabs.cjs check-navigation-logout.cjs check-toast-theme.cjs` | **5 cenários e 3 auxiliares aprovados** |

Os **12 novos testes** de `api.test_realtime` verificam autenticação, Host/Origin, HTTPS em produção, autorização por evento/contexto, destinatários de mensagens e notificações em lote, rollback sem publicação, transição real do evento, revogação de sessão/vínculo, indisponibilidade do Redis e limites do protocolo/conexões. Usam transações reais no PostgreSQL e Channel Layer em memória isolado; os guards de auditoria permanecem ativos durante as operações e só o banco descartável pode ser limpo entre testes.

`check-realtime.cjs` confirmou entrega por **Redis real entre processos**: mensagem e aviso inseridos por outro processo foram exibidos pela interface sem aguardar o polling. Componentes compartilharam uma conexão, não houve consulta de mensagens durante 19 segundos de transporte saudável e a queda forçada ativou recuperação HTTP. A reconexão não duplicou mensagens. Também verificou alertas globais publicados por `bulk_create` e conexão na administração de evento. Os testes de delta, isolamento entre abas, navegação/logout e tema das notificações continuaram aprovados.

Logs: `.tools/test-websocket-full.log`, `.tools/websocket-{check,migrations,build}.log` e `.tools/browser-tests/37fdb4d469c4/`. As 12 verificações novas estão incluídas nos 250 testes. Esta rodada executou os 5 cenários relacionados; a rodada anterior dos 21 cenários permanece registrada abaixo. Não houve ensaio de carga com centenas de sockets simultâneos.

### Sincronização incremental e limite de heartbeat

Removido o polling de `bootstrap/` a cada 5 segundos. `sync/` entrega mensagens paginadas/status a cada 15–18 segundos; o catálogo tem consulta separada nas telas sociais. `current()` limita a gravação a 60 segundos também em Online e revalida a condição no UPDATE. A migração `messaging.0003_message_sync_index` cria os índices de delta e mensagens não lidas. Contrato e limites em [Sincronização de participantes](<Sincronizacao de participantes.md>).

| Verificação | Resultado |
|---|---|
| `docker compose run --rm --no-deps -T backend python manage.py test tests api --noinput --verbosity 1` | **238 testes aprovados**, sem falhas, erros ou skips; banco de testes criado com a migração nova |
| `npm --prefix frontend run build` | TypeScript/Vite aprovados; avisos de React Bootstrap e tamanho do bundle |
| `manage.py check` / `makemigrations --check --dry-run` | Aprovados, sem problemas / alterações de modelos sem migração |
| `python scripts/run-browser-tests.py` | **20 de 21 cenários aprovados**, mais 3 auxiliares concluídos |
| `python scripts/run-browser-tests.py check-admin-mock.cjs check-admin.cjs` | **2 cenários aprovados**, mais 3 auxiliares concluídos; completa aprovação dos **21 cenários distintos** |

Os **16 novos testes** em `api.test_participant_sync` cobrem: isolamento de mensagens e leituras, autorização, assinatura/escopo de cursor, páginas de 100 com timestamps empatados, mensagens entre páginas, sobreposição para alterações visíveis com atraso, confirmação apenas dos IDs entregues, leitura idempotente sem UPDATE, novos estados de match/evento, anonimização de bloqueios, desativação/suspensão, heartbeat no limite de 60 segundos e snapshots concorrentes antigos. A consulta ociosa manteve o mesmo número de queries após acrescentar **500 participantes**, sem serializar perfis inalterados. O teste de catálogo confirma prefetch de fotos sem uma consulta por perfil. O teste anterior de presença foi atualizado para exigir que um contato após 5 segundos preserve o timestamp gravado.

O novo cenário `check-participant-sync.cjs` passou: recebeu mensagem e match sem recarregar o histórico, confirmou a leitura da mensagem entregue, conservou uma única bolha por ID, manteve bloqueios ao mesclar dados e pausou/retomou as consultas com a visibilidade da aba. Durante o cenário não houve polling de `bootstrap/` nem GET periódico do histórico de mensagens.

Na rodada completa, `check-admin.cjs` não encontrou o formulário de login no primeiro carregamento. Os caches Vite dos servidores Django/mock foram separados e o cenário foi reexecutado com sucesso após o mock administrativo. O log inicial não determina sozinho a causa da falha. Logs: `.tools/browser-tests/c428f76642f1/` e `.tools/browser-tests/57507f8f31c6/`. Não houve ensaio de carga com 500 clientes simultâneos: a verificação de 500 participantes mede constância de queries, não latência ou capacidade de produção. Os índices devem ser aplicados na atualização do ambiente.

### Evento explícito por aba e configurações de produção

Entrega dos itens 1.3/1.4: resolvedor `api/event_scope.py`, evento obrigatório por cabeçalho/URL nas operações administrativas, contexto persistido por aba e links privados com evento. Produção rejeita hosts vazios/com `*` e ativa cookies Secure e HTTPS. O protocolo original do proxy é encaminhado pelo Nginx. Sem migrações.

| Verificação | Resultado |
|---|---|
| `docker compose run --rm --no-deps -T backend python manage.py test tests api --noinput --verbosity 1` | **222 testes aprovados**, sem falhas, erros ou skips |
| `npm --prefix frontend run build` | TypeScript/Vite aprovados; avisos de diretivas React Bootstrap e tamanho do bundle |
| `manage.py check` e `makemigrations --check --dry-run` no backend | Aprovados, sem problemas ou alterações pendentes |
| `manage.py check` com `DJANGO_DEBUG=0`, hosts e origem HTTPS explícitos | Aprovado |
| `nginx -t`, com o arquivo de configuração atual e resolução local dos upstreams | Aprovado |
| Navegador: `check-admin.cjs`, `check-onboarding.cjs`, `check-real.cjs`, `check-mvp.cjs`, `check-navigation-logout.cjs`, `check-export-button.cjs`, `check-demonstration.cjs` | **7 cenários aprovados**, com 3 auxiliares concluídos |
| Navegador: `check-event-tabs.cjs` | **Aprovado na reexecução**, com 3 auxiliares concluídos; corrigida a espera do teste para a página de configuração de rascunho |

Os **21 novos testes** (`api.test_event_scope` e `api.test_production_security`) cobrem ausência/erro/conflito de identificadores, sessão compartilhada com eventos diferentes, escrita e auditoria por evento, papéis/vínculos revogados, objetos de outro evento, retomada de delegação, notificações, bootstrap global/administrativo/participante, escopo de exportação e fotos privadas, validação de configuração de produção, redirecionamento e cookies Secure com CSRF. As fixtures anteriores passaram a enviar o evento explicitamente; o teste de exportação também verifica links ZIP/PDF após mudar o evento da sessão.

O cenário novo abre duas abas no mesmo contexto de navegador, altera a sessão para B e salva uma configuração pela interface de A. Confirma `X-Event-ID`, dados de A/B e persistência de ambas após reload. A primeira tentativa esperava o elemento do dashboard, mas rascunhos abrem a configuração; a espera foi corrigida e o cenário passou. Logs: `.tools/browser-tests/36afa8815131/` e `.tools/browser-tests/f9a0219a0699/`. Foram aprovados **8 cenários distintos**, sem reexecutar os outros 12 scripts de navegador. Isso não certifica terminação TLS real, certificados ou implantação de produção; parâmetros e contrato estão em [Operação e desenvolvimento](<Operacao e desenvolvimento.md>).

### Throttling da API

Após configurar limites globais por IP/conta e limites adicionais para login, cadastro, mensagens e interações, a suíte completa passou com **201 testes**, sem falhas, erros ou skips. Comandos com prefixo `docker compose run --rm --no-deps -T backend python manage.py`:

| Comando | Resultado |
|---|---|
| `test api.test_throttling --noinput --verbosity 2` | **11 testes aprovados** |
| `test tests api --noinput --verbosity 1` | **201 testes aprovados** |
| `check` | Sem problemas |
| `makemigrations --check --dry-run` | Sem alterações pendentes |

Os testes verificam HTTP 429 e `Retry-After`, expiração da janela, isolamento por IP/conta, continuidade do limite ao trocar sessão/IP, tentativas de login/cadastro válidas e inválidas, cabeçalhos encaminhados, orçamento de mensagens entre conversas, orçamento de interações entre alvos, leituras sem consumir limite específico de escrita e ausência de novos dados/notificações/auditoria quando bloqueado. As taxas são reduzidas nos testes; os throttles continuam ativos na suíte.

Verificação adicional com Redis real e processos Python independentes: mesmo IP recebeu **200 → 429**, e outro IP recebeu **200**. O segundo processo recebeu `Retry-After: 58`. Usado prefixo aleatório temporário e remoção somente das chaves geradas, sem limpeza do Redis do ambiente. Parâmetros e limites técnicos em [Operação e desenvolvimento](<Operacao e desenvolvimento.md>).

O runner de navegador foi ajustado para isolar o cache por rodada e limpar somente esse prefixo entre cenários e ao encerrar. `python scripts/run-browser-tests.py check-real.cjs check-onboarding.cjs check-lan.cjs` aprovou **3 cenários de navegador e 3 auxiliares**, com os limites ativos, cobrindo login, perfil, filtros, descoberta, mensagens, cadastro, convite e CSRF. Logs: `.tools/browser-tests/a075b8aaa6fa/`. Não houve alteração de comportamento do frontend nem reexecução dos outros 16 cenários de navegador nesta correção.

### Unicidade e contagem de denúncias

Correção do abuso de denúncias em `backend/api/social_safety.py`: duplicatas retornam HTTP 400 sob bloqueio transacional do denunciado. Contagem dos limites e prioridade por denunciantes distintos do mesmo evento; histórico e evidências preservados, sem migração.

| Comando (prefixo `docker compose run --rm --no-deps -T backend python manage.py`) | Resultado |
|---|---|
| `test api.test_report_abuse api.test_mvp_flows.MvpFlowTests.test_report_thresholds_ignore_unfounded_and_do_not_ban --noinput --verbosity 2` | **10 testes aprovados** no PostgreSQL, incluindo os dois cenários concorrentes, sem skips |
| `test tests api --noinput --verbosity 1` | **190 testes aprovados**, sem falhas ou erros |
| `check` | Sem problemas |
| `makemigrations --check --dry-run` | Sem alterações pendentes |

Os 9 novos testes verificam repetição sequencial e simultânea, preservação de evidências/auditoria, isolamento por evento/alvo, duplicatas históricas, exclusões da contagem, rollback por evidência inválida e chegada concorrente ao limite de 20 sem notificações duplicadas. O teste anterior de limites foi atualizado para usar denunciantes distintos. Os testes concorrentes desabilitam apenas o trigger de TRUNCATE da auditoria durante o reset do banco descartável `test_`; as proteções ficam habilitadas durante as requisições e são restauradas após a limpeza. Não houve alteração de frontend nem nova execução de navegador nesta correção.

> **Validação anterior em 12/10/2026:** a entrega da [demonstração do frontend](<Demonstracao do frontend.md>) aprovou o build e **19 scripts de navegador** (18 na rodada completa e MVP na reexecução após corrigir uma espera de contexto), além de concluir os 3 auxiliares. A execução de backend daquela etapa aprovou **181 testes**, system check e check de migrações. Detalhes e limites no [relatório de correção](<Correcao dos testes - 12-10-2026.md>). O [diagnóstico anterior](<Reexecucao de testes - 12-10-2026.md>) e os números abaixo foram preservados como histórico.

## Registro da execução anterior

> Atualização após a entrega de exportação: `api.test_exports` passou com 9 testes de geração, SQL/restauração, isolamento, autorização, mídia/hash/PDF, falhas, auditoria, expiração e registro de assinatura/encaminhamento. Build e checks atuais passaram; o check de migrações deixou de detectar pendência após aplicar `events.0008`. O Celery real concluiu uma exportação em `backend/backups`, e a consulta offline foi validada sem rede. A suíte completa abaixo é a execução anterior desta data, não foi declarada integralmente aprovada pela entrega de exportação.

Execução em **12/10/2026**. Fontes: código, [Estado atual](<Estado atual do sistema.md>) e [avaliação da etapa 10](<Etapa 10 - verificacao e pendencias.md>). A [verificação anterior](<historico/Verificacao da implementacao - 04-10-2026.md>) foi preservada.

## Comandos e resultados

| Comando | Resultado |
|---|---|
| `npm --prefix frontend run build` | Aprovado: TypeScript/Vite; avisos sobre diretivas `use client` de React Bootstrap |
| `docker compose exec -T backend python manage.py check` | Aprovado, sem problemas de system check |
| `docker compose exec -T backend python manage.py makemigrations --check --dry-run` | Não aprovado: mudanças pendentes em `Event.mode` e `Event.radius_m`; sugere `events.0008_alter_event_mode_alter_event_radius_m` |
| `docker compose exec -T backend python manage.py test tests api --noinput` | **171 testes: 9 falhas e 5 erros**, sem aprovação integral |
| `docker compose exec -T backend python manage.py test api.test_mvp api.test_mvp_flows api.tests --noinput` | Reprodução: **60 testes, 9 falhas e 5 erros** |

Esta revisão documental não gera a migração sugerida nem corrige regras/fixtures. O arquivo de migração sugerido não foi criado pelo check. Os demais 157 testes terminaram sem falha reportada; isso não certifica produção, segurança ou homologação integral. Não houve nova rodada de todos os fluxos no navegador nesta reorganização.

## Regressões reproduzidas

Os nomes abaixo se referem a métodos de teste dos módulos indicados.

| Módulo / testes | Resultado e diagnóstico |
|---|---|
| `api.test_mvp`: `test_transition_retries_do_not_duplicate_audit_or_notifications`, `test_celery_calls_same_service_and_observes_automatic_delay`, `test_audit_failure_rolls_back_domain_changes`, `test_early_closing_requires_confirmation_reason_and_session_challenge` | 4 erros: validação exige coordenadas de evento presencial antes das asserções. Revisar fixtures/modalidade. O teste de arquivamento não chega à asserção final. |
| `api.test_mvp`: `test_progressive_configuration_and_authorization` | 400 em vez de 200; reconciliar configuração/fixture com validações atuais. |
| `api.test_mvp_flows`: `test_create_online_event_with_auto_activation_and_reject_physical` | 400 em vez de 201; resposta exige responsável como membro ativo do cliente. |
| `api.test_mvp_flows`: `test_activation_requires_outfit_three_public_photos_and_event_fields`, `test_profile_removal_preserves_history_requires_origin_and_allows_replacement` | 400 em vez de 200; investigar motivo final de cada rejeição, perfil/estado/requisitos. |
| `api.test_mvp_flows`: `test_guided_client_draft_activation_is_atomic_and_idempotent` | 400 em vez de 200; revisar fluxo legado frente ao cadastro separado e validações atuais. |
| `api.test_mvp_flows`: `test_payment_instructions_are_global_only_and_freeze_at_start` | 400 em vez de 200; investigar configuração/fixture. |
| `api.test_mvp_flows`: `test_geolocation_presence_outside_and_technical_recovery` | `DISTANT` em vez de `OUTSIDE`; divergência entre limites e expectativa. |
| `api.test_mvp_flows`: `test_likes_hidden_and_reveal_oldest_consumes_once` | Erro `KeyError: hidden`; consulta anterior retorna 403 e o teste usa payload de sucesso. |
| `api.tests`: `test_profile_filters_and_event_isolation` | 403 em vez de 404; revisar pré-condições de acesso social e escopo. |
| `api.tests`: `test_reciprocal_match_message_and_readonly_end` | 403 em vez de 200; revisar estado/ativação/localização antes da reciprocidade. |

Não afrouxar regras de autorização, localização ou responsável para fazer testes antigos passarem. Corrigir fixtures quando a regra estiver comprovada; investigar defeitos reais onde a origem ainda não foi determinada.

## Cobertura atual

| Área | Evidência | Limite |
|---|---|---|
| Clientes/equipe global | `api.test_global_clients` | Não substitui matriz de conta/Django Admin |
| Solicitação/ciclo de evento | `api.test_event_requests`, `test_event_timeline`, `test_mvp` | Cenário de arquivamento de FoundationTests não passa atualmente |
| Tópicos e mínimos | `api.test_profile_topics`, `test_global_clients` | Catálogo global e regras por evento são distintos |
| Presente inicial | `api.test_initial_gifts`, `api.test_initial_gift_batches` | Hooks, prazo, unicidade, concorrência, recuperação e paginação de 5.000 participantes; não mede throughput de 5.000 entregas reais |
| Likes/passes | `api.test_auto_likes`, `test_mvp_flows` | Cenário legado de revelação falha por acesso |
| Avisos/notificações | `api.test_notification_contexts`, `test_message_notifications`, `test_announcements` | Não implica e-mail/push de produção |
| UF de residência | `api.test_profile_residence_state` | Cadastro/exibição, sem filtro por UF |
| Perfil/fotos administrativos | `api.test_admin_participant_profile`, `test_event_admin` | Storage definitivo continua pendente |
| Presença Online | `api.test_online_presence` | Sem GPS; presença física tem outro fluxo |
| Relatório pós-evento | `api.test_discovery_report` | Consulta agregada, sem pacote offline |
| Arquivamento/exportação | Lifecycle e revisão de endpoints | Leitura exclusiva parcial; sem job/ZIP/SPA/PDF |

## Próximos passos de verificação

1. Reconciliar migrações e fixtures com regras atuais.
2. Investigar os 14 resultados não aprovados e reexecutar a suíte inteira.
3. Cobrir escritas em Arquivado, incluindo suporte e retomada de delegação; distinguir exceções de conta/privacidade.
4. Implementar/testar consulta geral de auditoria e exportação da etapa 10.
5. Executar matrizes de papéis/estados e homologação ponta a ponta da etapa 11.

## Evidência histórica

[Implementação das etapas 1–8](<Implementacao - etapas 1 a 8.md>) registra 73 testes aprovados em 04/10/2026. Trabalhos posteriores aprovaram builds e conjuntos selecionados, incluindo cliente/equipe, tópicos e presente inicial. Esses números são históricos e não substituem o resultado completo de 12/10/2026.
