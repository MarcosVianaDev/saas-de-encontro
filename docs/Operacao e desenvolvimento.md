# Operação e desenvolvimento

Referência operacional consolidada em **12/10/2026**. Para as regras implementadas, consulte [Estado atual](<Estado atual do sistema.md>); para requisitos futuros, [backlog aberto](<trilha de implementacao(aberto).md>).

## Ambiente e inicialização

Os comandos sem `-f` desta referência usam o **desenvolvimento**. `docker-compose.dev.yml` é uma entrada explícita equivalente. Para **produção**, use `.env.prod` e `docker-compose.prod.yml`, com build estático, Nginx, HTTPS e persistência separados. Comandos de implantação, localização dos backups e verificação em [Docker: desenvolvimento e produção](<Docker - desenvolvimento e producao.md>).

Dependências e serviços são definidos em `docker-compose.yml`, `requirements.txt`, `requirements.lock` e `frontend/package.json`. Use `.env.example` como base de configuração; credenciais reais pertencem ao `.env` local ou ao mecanismo de secrets do ambiente, nunca à documentação.

Desde **16/10/2026**, as dependências antes declaradas como `latest` no frontend usam versões exatas já resolvidas no lockfile: React/React DOM e suas tipagens **19.3.0**, TypeScript **7.0.2** e Vite **8.3.2**. Para instalações reproduzíveis, use `npm --prefix frontend ci`, também utilizado no Dockerfile. O `package-lock.json` fixa as dependências transitivas; atualizações devem manter manifesto e lockfile sincronizados e passar pelo build.

```powershell
docker compose up -d --build
docker compose ps
docker compose exec -T backend python manage.py check
```

O endereço local padrão é `http://localhost:8080/`; o Django Admin fica em `/admin/`. Portas e origens CSRF devem acompanhar a configuração efetiva do ambiente.

`backend/start.py` aplica migrações e coleta estáticos. A carga demonstrativa depende de DEBUG e `DJANGO_SEED_DEMO`; não deve ser usada como carga de dados reais. `FRONTEND_DATA_MODE=mock` é simulação no navegador, enquanto `django` usa a API. Recrie o serviço frontend após mudar variáveis de ambiente do Compose. Para abrir o mock a partir do acesso global, use **Ações rápidas → Demonstração**: `?demo=1` seleciona a simulação somente nessa aba, sem alterar o `.env`. O fluxo e os 50 perfis estão descritos em [Demonstração do frontend](<Demonstracao do frontend.md>).

Os estáticos Django/Admin coletados em `backend/staticfiles` são montados somente para leitura no Nginx, em `/srv/static`, e servidos diretamente por `/static/`, inclusive com `DJANGO_DEBUG=0`. O Nginx carrega os tipos MIME de CSS, JavaScript, SVG e demais assets. O backend não usa a view de desenvolvimento para servir estáticos em produção. O healthcheck do backend usa host permitido e esquema do proxy HTTPS confiável; o Nginx verifica o CSS coletado do Admin. Após atualizar esses arquivos, recrie os serviços para aplicar mounts/configuração. Verificação isolada: `python scripts/verify_production_static.py`; detalhes em [Verificação das prioridades](<Verificacao das prioridades.md>).

```powershell
docker compose exec -T backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose up -d --force-recreate frontend
```

Os scripts [full-clean.ps1](../full-clean.ps1) e [full-clean.sh](../full-clean.sh) são destrutivos: apagam dados do PostgreSQL/Redis do projeto e **todo o conteúdo de `backend/backups`**, incluindo ZIPs e termos PDF. Preservam a pasta de backups vazia e as fotos em `backend/media`. A limpeza acontece com backend/worker/Beat parados e não segue links para diretórios externos. Pedem `ZERAR`; `-Force` (PowerShell) ou `--force` (Bash) dispensam a confirmação. Usam a pasta do próprio script mesmo quando chamados de outro diretório. Não fazem parte da inicialização comum. Consulte o README da raiz para as demais condições.

```powershell
.\full-clean.ps1
```

```bash
bash full-clean.sh
```

## Validação

O acesso participante está dividido em páginas, componentes e hooks, mantendo um roteador leve por hash. Veja [Arquitetura do frontend](<Arquitetura do frontend.md>) para os contratos, estado local, limites da biografia e respostas de validação. A migração `profiles.0008_alter_participantprofile_bio` registra a política de 50 a 200 caracteres sem truncar dados existentes; aplique as migrações pelo procedimento de inicialização acima.

```powershell
docker compose exec -T backend python manage.py check
docker compose exec -T backend python manage.py makemigrations --check --dry-run
docker compose exec -T backend python manage.py test tests api --noinput
npm --prefix frontend run build
npm --prefix frontend run test:browser
```

Execute testes no PostgreSQL: a auditoria possui migrações de triggers específicas desse banco. SQLite não reproduz essa proteção e não executa integralmente as migrações atuais.

Os testes de navegador estão versionados em `frontend/tests/browser`; `test:browser` usa banco, mídia e backups temporários, com cleanup automático. Pré-requisitos, execução de cenários individuais e limites em [Testes de navegador](<../frontend/tests/README.md>). Os auxiliares estão em `scripts/`; o diagnóstico de `full_clean` não substitui testes de regras dos serviços/API.

A aprovação do build não comprova autorização nem regras de domínio; a aprovação de testes selecionados não equivale à suíte inteira. Consulte [o registro de verificação](<Verificacao da implementacao.md>) antes de usar números antigos.

## Limites de requisições da API

Desde **16/10/2026**, as views DRF usam `AnonRateThrottle`, `UserRateThrottle` e `api.throttling.WriteScopedRateThrottle`. Os limites gerais se acumulam com o limite específico da operação. O excesso retorna **HTTP 429**, mensagem em `detail` e cabeçalho `Retry-After` em segundos, antes de executar a operação.

| Limite padrão | Identificação | Variável opcional |
|---|---|---|
| Anônimo: 60/min | IP, compartilhado entre endpoints | `DRF_THROTTLE_ANON` |
| Autenticado: 300/min | Conta, compartilhado entre endpoints, eventos e sessões | `DRF_THROTTLE_USER` |
| Login: 10/min | IP, incluindo falhas e sucessos | `DRF_THROTTLE_LOGIN` |
| Cadastro: 5/min | IP, incluindo tentativas inválidas | `DRF_THROTTLE_REGISTER` |
| Enviar mensagem: 30/min | Conta, compartilhado entre conversas | `DRF_THROTTLE_MESSAGES` |
| Interações (like/skip): 60/min | Conta, compartilhado entre alvos | `DRF_THROTTLE_INTERACTIONS` |
| Denúncias: 10/min | Conta, compartilhado entre alvos, eventos e sessões | `DRF_THROTTLE_REPORTS` |

Login e cadastro mantêm `authentication_classes = []`, portanto continuam sendo identificados pelo IP mesmo com cookie de sessão. Leituras, como GET de mensagens, não consomem o limite específico de escrita; continuam sujeitas ao limite geral. Permissões, CSRF e regras de domínio continuam sendo exigidos.

`CACHES.default` usa o Redis do projeto, banco lógico 2 por padrão, com prefixo `eventconnect`. `DJANGO_CACHE_URL` permite alterar a conexão e `DJANGO_CACHE_KEY_PREFIX` isola ambientes que compartilham o Redis; o serviço deve estar disponível para atender a API. Os contadores são compartilhados entre processos do backend. As variáveis estão em `.env.example`; após alterá-las, recrie os processos que usam as configurações Django.

`DRF_NUM_PROXIES=2` corresponde à cadeia exposta pelo Compose **Traefik → Nginx → backend**. O backend não publica porta diretamente. O DRF identifica o cliente pela posição correspondente em `X-Forwarded-For`, ignorando prefixos adicionais fornecidos pelo solicitante. Mantenha os proxies de borda configurados para aceitar cabeçalhos encaminhados apenas de proxies confiáveis. Ao mudar a infraestrutura, ajuste a contagem; em acesso direto use `DRF_NUM_PROXIES=0`, que identifica pelo `REMOTE_ADDR` e ignora `X-Forwarded-For`.

O runner `config.testing.IsolatedCacheTestRunner` substitui apenas durante os testes o Redis por cache local e o Channel Layer por memória e limpa os contadores antes de cada teste. Os throttles permanecem ativos; a suíte não limpa o cache Redis do ambiente. Os testes de limites usam janelas e taxas reduzidas para verificar bloqueio, recuperação e ausência de efeitos colaterais. O compartilhamento real entre processos foi verificado separadamente no Redis com prefixo temporário e remoção apenas das chaves dessa verificação.

O runner de navegador define um prefixo exclusivo por rodada e reinicia somente essas chaves entre cenários e auxiliares. O cleanup remove as chaves do prefixo antes de destruir o container temporário; não usa `FLUSHDB`. Os limites continuam ativos durante cada cenário. Consulte [Testes de navegador](../frontend/tests/README.md).

Os throttles nativos usam operações de cache não atômicas e podem permitir algumas requisições extras sob concorrência. São controle de uso da aplicação; não certificam proteção completa contra ataques distribuídos ou negação de serviço. Referência: [documentação de throttling do DRF](https://www.django-rest-framework.org/api-guide/throttling/).

## Evento explícito e abas independentes

Desde **16/10/2026**, chamadas administrativas de evento devem informar `X-Event-ID: <uuid>` ou usar a URL `/api/events/<uuid>/<caminho atual>/`. Exemplos: `/api/events/<uuid>/event-admin/configuration/` e `/api/events/<uuid>/event-admin/exports/`. Sem escopo explícito, a sessão não é usada como fallback para essas operações: a API retorna HTTP 400. UUID inválido ou divergência entre URL e cabeçalho também retornam 400. O identificador não concede acesso: a conta, o vínculo ativo, o papel, as permissões e os objetos daquele evento continuam sendo validados.

O resolvedor comum em `backend/api/event_scope.py` atende `access()`, configurações/transições, solicitação de novo evento a partir de um evento existente, exportações e retomada de delegação. Fotos administrativas, evidências, fotos de participantes/outfits e links ZIP/PDF trazem o evento no path, inclusive para acessos por `<img>` ou `<a>` sem cabeçalhos customizados. URLs de um evento não permitem acessar objetos de outro evento.

O frontend mantém `{navigation, eventId}` em `sessionStorage`, chave `eventconnect-tab-context`, e envia `X-App-Context` e, quando aplicável, `X-Event-ID` nas requisições daquela aba. O contexto global não tem evento. A leitura inicial de `bootstrap/` pode descobrir a seleção da sessão quando a aba ainda não tem contexto; a interface passa a usar a escolha explícita e a conserva após reload. Login, cadastro, ingresso e seletores retornam a identidade do contexto; `eventId` integra as respostas administrativas. Logout limpa a escolha local. A autenticação por cookie continua compartilhada entre abas.

`X-App-Context` aceita `participant`, `administration`, `global` ou `selection`. Esse cabeçalho distingue especialmente `bootstrap/` e `notifications/`, usados pelos três acessos; não concede privilégios. APIs de participante aceitam evento explícito e preservam o fallback de sessão para clientes antigos. Chamadas novas do frontend enviam o evento da própria aba.

As operações de seleção (`contexts/`, `global/event/` e POST `event-admin/`) continuam recebendo a escolha no corpo e validando a autorização. Elas podem atualizar a seleção inicial da sessão, mas as chamadas administrativas seguintes usam seu próprio escopo. Consumidores externos dos endpoints administrativos anteriores precisam acrescentar o cabeçalho ou adotar a URL com evento. Fixtures e o helper de navegador foram atualizados para esse contrato.

## Segurança de produção

Com `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS` é obrigatório e não pode conter `*`. Entradas são separadas por vírgulas e têm os espaços removidos; não existe fallback permissivo em produção. Exemplo: `DJANGO_ALLOWED_HOSTS=app.exemplo.com,api.exemplo.com`. Em desenvolvimento, o fallback limita-se a localhost/loopback; `.env.example` permite `*` explicitamente para os testes locais/LAN com DEBUG habilitado.

`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` e `SECURE_SSL_REDIRECT` são ativados quando DEBUG está desabilitado. A sessão também conserva `HttpOnly`. As origens CSRF de localhost deixam de ser o padrão de produção; configure `DJANGO_CSRF_TRUSTED_ORIGINS` com as origens HTTPS necessárias. CSRF e autenticação continuam obrigatórios.

Na cadeia **Traefik → Nginx → Django**, o Nginx encaminha `X-Forwarded-Proto` normalizado a partir do proxy de borda e Django reconhece `https` por `SECURE_PROXY_SSL_HEADER`. Isso exige que o backend e o Nginx sejam alcançáveis somente pela cadeia de proxies confiável, e que a borda remova cabeçalhos encaminhados não confiáveis. `DJANGO_TRUST_PROXY_SSL_HEADER=0` desabilita essa confiança para uma implantação direta com HTTPS. O Compose local publica HTTP e usa DEBUG; a alteração não provisiona certificados/TLS de produção. Hosts e verificações de saúde do ambiente de produção também precisam acompanhar a implantação HTTPS.

Referências: [configurações do Django](https://docs.djangoproject.com/en/5.2/ref/settings/#secure-proxy-ssl-header) e [checklist de implantação](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/).

## Processamento assíncrono

`celery_worker` e Beat devem estar disponíveis para ciclo do evento, avisos, expiração de passes e despacho do presente inicial. `celery_exports` gera ZIP/PDF e `celery_gifts` entrega os presentes em lotes.

| Serviço | Fila consumida | Concorrência / prefetch |
|---|---|---|
| `celery_worker` | `celery` (nome padrão anterior, preservado) | 1 / 1 |
| `celery_exports` | `exports` | 1 / 1 |
| `celery_gifts` | `gifts` | 1 / 1 |
| `celery_beat` | Publica as quatro rotinas periódicas em `celery` | Uma instância por aplicação |

`CELERY_TASK_ROUTES` envia `apps.events.export_tasks.generate` para `exports` e `apps.passes.tasks.initial_gift_batch` para `gifts`. As tarefas também declaram suas filas e os retries conservam o destino. Os três workers compartilham banco, mídia e backups pelos volumes existentes. Os healthchecks usam nomes distintos (`default@<hostname>`, `exports@<hostname>` e `gifts@<hostname>`). O worker de exportação tem até 10 minutos para encerrar no Compose antes de uma parada forçada. Filas separadas impedem que exportações ou entregas em massa reservem o processo das rotinas; CPU, disco e PostgreSQL continuam compartilhados.

Ao atualizar um ambiente existente, recrie os produtores, os workers e o Beat:

```powershell
docker compose up -d --build --force-recreate --wait backend celery_worker celery_exports celery_gifts celery_beat nginx traefik
```

Tarefas publicadas antes da atualização permanecem na fila original; o roteamento vale para novas publicações e retries. O worker operacional ainda consome `celery` para drenar mensagens antigas. Uma exportação antiga já publicada ali pode ocupar esse worker uma última vez. Não há purge ou transferência automática de mensagens. Evite manter produtores antigos publicando durante a atualização. Os scripts `full-clean` param e recriam os três workers antes/depois da limpeza destrutiva.

```powershell
docker compose exec -T celery_worker celery -A config inspect registered --timeout 5
docker compose exec -T celery_worker celery -A config inspect active_queues --timeout 5
docker compose logs --tail 80 celery_worker celery_exports celery_gifts celery_beat
```

Alterações em tarefas ou agendamento exigem recarregar os processos correspondentes. Frequências atuais: 30 segundos. O prazo zero do presente inicial também possui execução direta ao ativar o perfil; prazos positivos dependem da execução elegível com o evento Em andamento.

### Presente inicial em grandes eventos

O Beat adquire uma concessão exclusiva no PostgreSQL (`InitialGiftSweep`, migração `passes.0006`) e publica somente o primeiro lote. Cada tarefa em `gifts` seleciona até `INITIAL_GIFT_BATCH_SIZE + 1` identificadores por cursor, entrega no máximo `INITIAL_GIFT_BATCH_SIZE` presentes e publica uma única continuação. O padrão é **25 participantes**; a configuração aceita **1 a 100** nos dois ambientes. A seleção filtra eventos em andamento, prazo vencido, evento ainda válido, conta/participação ativas e ausência de presente anterior antes das transações de entrega.

Após aproximadamente cinco segundos, o lote pode ceder antes do limite de participantes. O limite de tempo é verificado entre entregas: uma entrega individual demorada não é interrompida. O próximo lote continua imediatamente pela fila, sem esperar os 30 segundos do Beat. A concessão é renovada a cada lote e impede que ciclos sobrepostos acumulem distribuições. Tokens e cursor rejeitam tarefas antigas e continuações repetidas. Se o worker desaparecer, o Beat pode reiniciar a varredura após a concessão expirar em **120 segundos**; os presentes já entregues são excluídos.

Cada entrega continua atômica, verifica novamente elegibilidade e horário após adquirir o lock e mantém a constraint de um presente por participação. Falhas individuais são registradas com o identificador do participante, não impedem a continuação e são tentadas novamente na próxima varredura. Falhas de banco/publicação têm retries limitados; falha ao publicar libera a concessão para recuperação pelo Beat. Não existe uma transação que englobe o lote inteiro. O helper síncrono `grant_due_initial_gifts()` também se limita a um lote; não é mais responsável por uma distribuição completa.

`scripts/verify_celery_queues.py` verifica o isolamento com Redis e três workers prefork reais. Substitui temporariamente o trabalho de exportação e do lote por esperas limitadas; confirma que uma tarefa operacional termina com ambos ocupados. Usa prefixo Redis aleatório, remove somente suas chaves e encerra seus workers; não cria passes, `ExportJob` ou arquivos de exportação e não altera dados da aplicação. Execute em um processo separado:

```powershell
Get-Content -Raw scripts/verify_celery_queues.py | docker compose run --rm --no-deps -T backend python manage.py shell
```

## Consultas do painel administrativo

`admin_participants()` faz `select_related` de conta, perfil, evento e banimento. Usa `Exists` para suspensão global, `Prefetch` filtrado para suspensões/foto primária e contagens `Count` em `Subquery` independentes para denúncias relevantes e bloqueios, com `Coalesce` para retornar zero. As duas contagens integram a mesma consulta SQL de participantes, sem multiplicar linhas por um join entre denúncias e bloqueios. Operadores não recebem contagens ou motivos de moderação.

`participant_payload()` e `operational_status` aproveitam esses resultados; notas, evidências e auditoria das ocorrências também são carregadas em lote. Os mesmos payloads alimentam lista, ocorrências e sinais de bloqueio. `api.test_admin_query_efficiency` verifica cards sem queries adicionais, contagens corretas e constância do painel de 2 para 100 participantes, com 99 ocorrências e sinais de bloqueio: orçamento de até 25 queries como administrador e 20 como operador no cenário do teste. Mede chamadas SQL, não latência ou consumo de memória; o painel ainda serializa a lista integral.

## Mapa de manutenção

| Assunto | Código principal |
|---|---|
| Sessão, perfil, filtros e mensagens | `backend/api/views.py`, `services.py`, `serializers.py` |
| Interface e navegação do participante | `frontend/App.tsx`, `views/`, `components/`, `hooks/`; ver [Arquitetura do frontend](<Arquitetura do frontend.md>) |
| Biografia e erros de validação | `backend/apps/profiles/constants.py`, `api/exceptions.py`, `frontend/profile-validation.ts`, `backend-client.ts` |
| Contextos e papéis | `backend/api/contexts.py`, `event_admin.py`, `backend/apps/events/permissions.py` |
| Administração global | `frontend/GlobalAdministration.tsx`, `backend/api/global_admin.py` |
| Evento e equipe | `frontend/Administration.tsx`, `TeamManagement.tsx`, `backend/api/team.py`, `event_operations.py` |
| Criação/solicitação de evento | `frontend/EventRequestForm.tsx`, `backend/api/event_requests.py` |
| Tópicos e regras por evento | `frontend/ProfileTopicManagement.tsx`, `EventParticipantTopics.tsx`, `backend/apps/profiles/topics.py` |
| Passes e presente inicial | `frontend/InitialGiftFields.tsx`, `backend/api/passes.py`, `backend/apps/passes/gifts.py` |
| Avisos e notificações | `backend/api/notifications.py`, `backend/apps/notifications/announcements.py` |
| Tema e componentes | `frontend/styles.css`, `administration.css`, `toggles.css`; confira os imports vigentes de `main.tsx` |
| Auditoria | `backend/apps/audit/models.py`, `services.py`, migrações append-only |
| Exportação | `backend/api/exports.py`, `backend/apps/events/export_service.py`, `export_snapshot.py`, `export_tasks.py`; ver [Exportação de eventos](<Exportacao de eventos.md>) |

## Contratos recentes da API

Todos os caminhos abaixo são relativos a `/api/` e sujeitos à sessão, CSRF e autorização pertinentes.

| Recurso | Contrato |
|---|---|
| `global/` GET | Indicadores, clientes/equipes, eventos, tópicos, atividade e alertas |
| `global/` POST | `create_client`, `update_client`, `create_team_member`, `update_team_member`, `save_topic`, `create_event`, acompanhamento de segurança |
| `global/event/` POST | Seleção de contexto administrativo de evento pelo superuser |
| `event-admin/requests/` POST | Solicitação de evento da organização em Rascunho |
| `event-admin/team/` GET/POST | Vínculos, papéis, permissões, delegação e retomada |
| `profile/` PUT | Perfil, UF, interesses/finalidade compatíveis e `topicAnswers` |
| `bootstrap/` GET | Perfil, tópicos habilitados/regras, estado do evento e dados autorizados |
| `sync/` GET | Cursor assinado, lote de até 100 mensagens, status e estados das próprias conversas; substitui polling de bootstrap |
| `catalog/` GET | Perfis visíveis e descoberta, consultados separadamente nas telas sociais |
| `conversations/{id}/read/` POST | Confirma até 100 IDs recebidos no chat aberto; evita UPDATE sem novas leituras |
| `event-admin/participants/{id}/activate/` POST | Ativação e eventual presente imediato |
| `event-admin/passes/` GET/POST | Ofertas, concessão manual e revogação |
| `notifications/` GET/POST | Consulta por contexto e leitura de notificação |

`create_event` e a solicitação de evento aceitam `initial_gift`: `enabled`, `name`, `delay_minutes`, `duration_minutes`, `reveal_limit`. Com presente habilitado, definir duração **ou** revelações; o prazo deve vencer antes de `ends`. O servidor cria uma oferta de preço zero e grava sua referência nas configurações.

O cadastro global também aceita `participant_topics`: lista de `{topic, enabled, required, minimum}`. O mínimo é de 1 a 5 e compatível com as opções/tipo de escolha. Essas regras são configurações por evento; editar o catálogo global é outra operação.

A sincronização periódica do participante e o limite de gravação de presença estão em [Sincronização de participantes](<Sincronizacao de participantes.md>). A atualização exige a migração `messaging.0003_message_sync_index`, que cria os índices de delta e mensagens não lidas. Não confundir as páginas de sincronização com o snapshot inicial, que ainda contém o histórico.

## Produção e governança

Homologação, armazenamento privado definitivo, recuperação, segurança, observabilidade, e-mail transacional e políticas de privacidade/retenção são assuntos das etapas 9, 11 e 12. Esta documentação não certifica prontidão para produção nem valida legislação ou política jurídica. Exportação formal depende do escopo e controles descritos no [relatório da etapa 10](<Etapa 10 - verificacao e pendencias.md>).

## WebSocket

Daphne atende `/ws/global/` e `/ws/events/<uuid>/{participant,administration}/`, autenticados pela sessão e com validação de Origin. Nginx/Vite encaminham o upgrade. Redis distribui avisos após commit, isolados por evento e conta; `CHANNEL_REDIS_PREFIX` permite separar ambientes. A interface compartilha uma conexão por aba e retoma consultas HTTP quando desconectada. Veja [WebSocket e tempo real](<WebSocket e tempo real.md>) para protocolo, limites, frequências, segurança e operação. Após atualizar o código/configuração, reinicie Daphne, workers e o proxy para carregar rotas e sinais.

## Mídia protegida

Fotos de perfil, outfits, fotos administrativas e evidências autorizadas são entregues pelo Nginx com `X-Accel-Redirect`. O Compose ativa `MEDIA_USE_X_ACCEL_REDIRECT=1` por padrão e monta `backend/media` em `/srv/private-media:ro`; Django retorna somente cabeçalhos após verificar permissões/caminho e auditoria quando exigida. A rota interna não aceita acesso direto. Recrie backend, frontend e Nginx ao atualizar; o novo bind mount exige recriar o container do proxy. Desenvolvimento direto sem Nginx pode usar `MEDIA_USE_X_ACCEL_REDIRECT=0`. Configuração, segurança e testes em [Mídia protegida](<Midia protegida.md>).
