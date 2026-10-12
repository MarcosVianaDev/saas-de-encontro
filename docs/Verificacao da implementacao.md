# Verificação da implementação

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
| Presente inicial | `api.test_initial_gifts` | Hooks, prazo, notificação e unicidade; não prova carga do worker |
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
