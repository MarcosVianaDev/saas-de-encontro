# Implementação das etapas 1 a 8

Atualizado em 04/10/2026. Os 45 cards das etapas 1 a 8 da [trilha](<trilha de implementacao.md>) foram implementados. O conteúdo de cada card e seu registro de conclusão estão em [cards concluídos](<trilha de implementacao(fechado).md>). As etapas 9 a 12 permanecem em [cards abertos](<trilha de implementacao(aberto).md>).

## Cobertura

| Etapa | Resultado | Implementação principal |
|---|---|---|
| 1 — Domínio e auditoria | Estados explícitos, configuração com bloqueio progressivo, participação independente de presença/sanções e auditoria transacional. Falha de auditoria desfaz a operação. | `apps/events/services.py`, `apps/participants/models.py`, `apps/audit/services.py`, `common/admin.py` |
| 2 — Identidade e administração | Seleção de contextos da mesma conta; superuser na Administração Global; cadastro guiado; entrada contextual em eventos; equipe, permissões, delegação e retomada. | `api/contexts.py`, `api/global_admin.py`, `api/team.py`, `GlobalAdministration.tsx`, `TeamManagement.tsx` |
| 3 — Ciclo do evento | Abertura manual a partir de duas horas antes; automática cinco minutos antes; início dez minutos depois quando a abertura foi automática; pausa, retomada, encerramento e arquivamento após quinze dias. Encerramento antecipado exige confirmação, justificativa e CAPTCHA de sessão. | `apps/events/services.py`, `apps/events/tasks.py`, `EventOperations.tsx`, `EventConfiguration.tsx` |
| 4 — Participante | Onboarding em cinco passos, reaproveitamento elegível do perfil global, três fotos públicas, imutabilidade após ativação, outfit capturado pela equipe, descoberta, match e conversas. Outfit é exibido primeiro após match e servido com autorização. | `api/profile_operations.py`, `api/views.py`, `ParticipantOnboarding.tsx`, `main.tsx` |
| 5 — Segurança | Bloqueio definitivo por evento; denúncias com motivos, relato e evidências; investigação; alertas aos dez e desativação para análise aos vinte; suporte e intervenções vinculadas à origem. Recorrência é marcada pela gestão global e não bane automaticamente em outros eventos. | `api/social_safety.py`, `api/event_admin.py`, `api/support.py`, `SocialSafety.tsx`, `AdminOperations.tsx` |
| 6 — Passes e financeiro | Identidades protegidas, revelação cronológica por quantidade ou tempo, concessão por Operador autorizado, preço e condições preservados na concessão, expiração, revogação e relatório de vendas declaradas. | `apps/passes/services.py`, `api/passes.py`, `ParticipantExtras.tsx`, `AdminOperations.tsx` |
| 7 — Localização | Consentimento, três zonas, cinco retentativas, recuperação manual, desativação técnica, exceção temporária com expiração e anomalias. Histórico exige motivo, auditoria, gestor e estado permitido. Decisões operacionais exigem evento pausado; banimento local pode ser revogado preservando o registro. | `apps/participants/location.py`, `api/location.py`, `LocationControl.tsx`, `AdminOperations.tsx` |
| 8 — Mensagens e automações | Central de mensagens, notificações e suporte; leitura persistida e indicador de não lidos; avisos com prévia, confirmação, agendamento e validação do estado no envio. Avisos automáticos pausados ficam retidos para envio manual; encerrados são cancelados. | `apps/notifications/announcements.py`, `api/notifications.py`, `ParticipantExtras.tsx`, `AdminOperations.tsx` |

Os caminhos Python são relativos a `backend/`; os componentes são relativos a `frontend/`. As migrações preservam registros existentes e preenchem os estados anteriores dos eventos e indicadores de ativação das participações.

## Executar o MVP conectado

Configure `FRONTEND_DATA_MODE=django` no `.env` e execute:

```powershell
docker compose up -d --build
```

O modo `mock` mantém a demonstração sem gravação no backend. O backend aplica migrações ao iniciar. `celery_worker` executa as tarefas e `celery_beat` dispara verificações de ciclo do evento, avisos e expiração de passes a cada trinta segundos. Utilize uma instância do Beat por aplicação.

Entre com uma conta superuser para a Administração Global. Contas com vários contextos escolhem onde entrar. `is_staff` habilita o Django Admin segundo as permissões do Django e não concede acesso à Administração Global.

No evento aberto, participantes concluem o cadastro; a equipe captura a foto do look e ativa o perfil. A descoberta social fica disponível no evento em andamento. Eventos presenciais também exigem consentimento e validação de localização. A concessão de passes exige papel de Operador e permissão adicional de operação de passes.

## Validação realizada

- **73 testes Django aprovados**, com PostgreSQL: autenticação, isolamento por evento e usuário, permissões, transições, auditoria com rollback, fotos, ativação, bloqueios, denúncias, passes, GPS, suporte, notificações, avisos e histórico.
- **Build TypeScript/Vite aprovado** e **nenhuma alteração de modelos sem migração**.
- **Concorrência real no PostgreSQL:** duas requisições simultâneas para um passe com um crédito produziram uma revelação, uma recusa por falta de saldo e uma única utilização. Foi revelado o like oculto mais antigo.
- **Navegador:** mensagens e suporte em mobile sem overflow horizontal, contexto global, entrada e retorno da administração do evento, cadastro guiado em seis passos, ativação do cliente, abertura manual e logout, sem erros JavaScript.
- **Participantes novos no navegador:** onboarding completo, três fotos autenticadas, captura do look e ativação por Operador, proteção de like recebido, concessão/revelação de passe, match, acesso autorizado ao outfit e conversa persistida.
- **Celery:** Beat e Worker executaram as três rotinas agendadas com sucesso no ambiente local.

As verificações de navegador e concorrência criaram novos registros fictícios identificados como validação. Os dados anteriores foram preservados.

Testes principais: [`test_mvp.py`](../backend/api/test_mvp.py), [`test_mvp_flows.py`](../backend/api/test_mvp_flows.py) e [`test_event_admin.py`](../backend/api/test_event_admin.py). Para reproduzir as verificações automatizadas:

```powershell
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend python manage.py test
docker compose exec frontend npm run build
```

## Decisões e etapas seguintes

Um único par de leituras acima de 60 km/h é registrado como sinal interno. O alerta visível imediato para esse caso continua sendo uma decisão pendente do produto, conforme o card 7.6. Duas leituras além de raio mais tolerância geram alerta aos gestores. Nenhum sinal aplica sanção automaticamente.

LGPD operacional completa, retenção final por categoria, exportação auditável, homologação integrada da etapa 11 e preparação para produção continuam nas etapas 9 a 12. O relatório financeiro registra vendas declaradas e não comprova recebimento nem integra gateway de pagamentos.
