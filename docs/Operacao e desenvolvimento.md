# Operação e desenvolvimento

Referência operacional consolidada em **12/10/2026**. Para as regras implementadas, consulte [Estado atual](<Estado atual do sistema.md>); para requisitos futuros, [backlog aberto](<trilha de implementacao(aberto).md>).

## Ambiente e inicialização

Dependências e serviços são definidos em `docker-compose.yml`, `requirements.txt`, `requirements.lock` e `frontend/package.json`. Use `.env.example` como base de configuração; credenciais reais pertencem ao `.env` local ou ao mecanismo de secrets do ambiente, nunca à documentação.

```powershell
docker compose up -d --build
docker compose ps
docker compose exec -T backend python manage.py check
```

O endereço local padrão é `http://localhost:8080/`; o Django Admin fica em `/admin/`. Portas e origens CSRF devem acompanhar a configuração efetiva do ambiente.

`backend/start.py` aplica migrações e coleta estáticos. A carga demonstrativa depende de DEBUG e `DJANGO_SEED_DEMO`; não deve ser usada como carga de dados reais. `FRONTEND_DATA_MODE=mock` é simulação no navegador, enquanto `django` usa a API. Recrie o serviço frontend após mudar variáveis de ambiente do Compose.

```powershell
docker compose exec -T backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose up -d --force-recreate frontend
```

Os scripts `zerar-banco.ps1` e `zerar-banco.sh` são destrutivos: apagam dados do banco/Redis do projeto e preservam arquivos de mídia conforme a implementação. Não fazem parte da inicialização comum. Consulte o README da raiz para as condições e confirmações desses scripts.

## Validação

```powershell
docker compose exec -T backend python manage.py check
docker compose exec -T backend python manage.py makemigrations --check --dry-run
docker compose exec -T backend python manage.py test tests api --noinput
npm --prefix frontend run build
```

Execute testes no PostgreSQL: a auditoria possui migrações de triggers específicas desse banco. SQLite não reproduz essa proteção e não executa integralmente as migrações atuais.

A aprovação do build não comprova autorização nem regras de domínio; a aprovação de testes selecionados não equivale à suíte inteira. Consulte [o registro de verificação](<Verificacao da implementacao.md>) antes de usar números antigos.

## Processamento assíncrono

Worker e Beat devem estar disponíveis para ciclo do evento, avisos, expiração de passes e entrega agendada do presente inicial.

```powershell
docker compose exec -T celery_worker celery -A config inspect registered --timeout 5
docker compose logs --tail 80 celery_worker celery_beat
```

Alterações em tarefas ou agendamento exigem recarregar os processos correspondentes. Frequências atuais: 30 segundos. O prazo zero do presente inicial também possui execução direta ao ativar o perfil; prazos positivos dependem da execução elegível com o evento Em andamento.

## Mapa de manutenção

| Assunto | Código principal |
|---|---|
| Sessão, perfil, filtros e mensagens | `backend/api/views.py`, `services.py`, `serializers.py` |
| Contextos e papéis | `backend/api/contexts.py`, `event_admin.py`, `backend/apps/events/permissions.py` |
| Administração global | `frontend/GlobalAdministration.tsx`, `backend/api/global_admin.py` |
| Evento e equipe | `frontend/Administration.tsx`, `TeamManagement.tsx`, `backend/api/team.py`, `event_operations.py` |
| Criação/solicitação de evento | `frontend/EventRequestForm.tsx`, `backend/api/event_requests.py` |
| Tópicos e regras por evento | `frontend/ProfileTopicManagement.tsx`, `EventParticipantTopics.tsx`, `backend/apps/profiles/topics.py` |
| Passes e presente inicial | `frontend/InitialGiftFields.tsx`, `backend/api/passes.py`, `backend/apps/passes/gifts.py` |
| Avisos e notificações | `backend/api/notifications.py`, `backend/apps/notifications/announcements.py` |
| Tema e componentes | `frontend/styles.css`, `administration.css`, `toggles.css`; confira os imports vigentes de `main.tsx` |
| Auditoria | `backend/apps/audit/models.py`, `services.py`, migrações append-only |
| Exportação | Ainda sem módulo de implementação; seguir a avaliação da etapa 10 |

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
| `event-admin/participants/{id}/activate/` POST | Ativação e eventual presente imediato |
| `event-admin/passes/` GET/POST | Ofertas, concessão manual e revogação |
| `notifications/` GET/POST | Consulta por contexto e leitura de notificação |

`create_event` e a solicitação de evento aceitam `initial_gift`: `enabled`, `name`, `delay_minutes`, `duration_minutes`, `reveal_limit`. Com presente habilitado, definir duração **ou** revelações; o prazo deve vencer antes de `ends`. O servidor cria uma oferta de preço zero e grava sua referência nas configurações.

O cadastro global também aceita `participant_topics`: lista de `{topic, enabled, required, minimum}`. O mínimo é de 1 a 5 e compatível com as opções/tipo de escolha. Essas regras são configurações por evento; editar o catálogo global é outra operação.

## Produção e governança

Homologação, armazenamento privado definitivo, recuperação, segurança, observabilidade, e-mail transacional e políticas de privacidade/retenção são assuntos das etapas 9, 11 e 12. Esta documentação não certifica prontidão para produção nem valida legislação ou política jurídica. Exportação formal depende do escopo e controles descritos no [relatório da etapa 10](<Etapa 10 - verificacao e pendencias.md>).
