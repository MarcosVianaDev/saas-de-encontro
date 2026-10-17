# Verificação das prioridades

Auditoria do código e novas execuções em **16/10/2026**. Os oito itens da lista estão implementados. Esta rodada encontrou e corrigiu duas lacunas: estáticos do Django ainda eram enviados ao backend em produção, e denúncias tinham apenas o limite geral de requisições.

## Matriz de implementação

| Prioridade | Item | Implementação e evidência |
|---|---|---|
| Alta | Spam de denúncias e 20 denunciantes distintos | `api/social_safety.py`: bloqueio de denúncia repetida por par de participantes, lock/transação para requisições concorrentes e contagem `reporter_id` distinta. Desconsidera denúncias administrativas, infundadas, sem denunciante e de outro evento. `api.test_report_abuse` verifica repetição, histórico e concorrência. |
| Alta | Estáticos com `DJANGO_DEBUG=0` | **Corrigido nesta auditoria.** `collectstatic` grava em `/app/staticfiles`; Nginx monta a pasta somente para leitura em `/srv/static` e serve `/static/` diretamente, com tipos MIME e `nosniff`. O Django permanece sem rota de desenvolvimento para estáticos em produção. `scripts/verify_production_static.py` verificou oito assets reais do Admin, CSS/JS/SVG, 404 e ausência de listagem de diretório. |
| Alta | Escritas de `last_seen_at` | `api/services.current`: intervalo de 60 segundos com condição repetida no UPDATE SQL. Modalidade online não ignora o intervalo; snapshots concorrentes não sobrescrevem heartbeat recente. `api.test_participant_sync` confirma zero UPDATE em 0/5/30/59 segundos e um UPDATE aos 60 segundos. |
| Média | Exportações separadas das automações | Worker `celery_worker` consome `celery`; `celery_exports` consome `exports`, ambos com prefetch 1. Rota e tarefa de exportação fixam `exports`, inclusive em retries. Testes unitários e `scripts/verify_celery_queues.py` confirmam uma tarefa operacional concluída enquanto a exportação ocupa o outro worker. |
| Média | N+1 no painel | `api/event_admin.admin_participants`: `select_related`, prefetch filtrado de suspensão/foto, `Exists` e contagens por subqueries independentes. Ocorrências, notas, evidências e auditoria são carregadas em lote. `api.test_admin_query_efficiency` verifica custo constante de 2 para 100 participantes, até 25 queries administrativas/20 de operador e zero queries adicionais na serialização dos cards. |
| Média | Rate limiting crítico | Limites gerais por IP/conta e específicos de login, cadastro, mensagens, interações e **denúncias (10/min por conta, adicionado nesta auditoria)**. Redis compartilha contadores entre processos. Tentativas inválidas/repetidas também consomem o orçamento; GET não consome o limite específico de escrita. `api.test_throttling` verifica HTTP 429/Retry-After, sessões/IPs diferentes, isolamento entre contas e ausência de efeitos após o bloqueio. |
| Estrutural | Modularização do participante | `frontend/main.tsx` contém apenas montagem/estilos; seis páginas em `views/`, componentes em `components/` e hooks de sessão, perfil, ações sociais, sincronização e roteador por hash. [Arquitetura do frontend](<Arquitetura do frontend.md>). |
| Estrutural | WebSockets | `config/asgi.py` registra HTTP e WebSocket, com sessão, validação de origem/host e autorização de contexto/evento. Mensagens/notificações/status geram avisos após commit. O frontend usa esses avisos para sincronizar; não há polling de bootstrap a cada 5 segundos. Testes de backend e navegador cobrem autorização, Redis, transporte entre processos, queda e retomada. [WebSocket e tempo real](<WebSocket e tempo real.md>). |

O HTTP permanece como recuperação: delta a cada 60–63 segundos com WebSocket conectado, 15–18 segundos durante indisponibilidade, e catálogo separado a cada minuto nas telas pertinentes. A conexão em tempo real reduz o polling, sem eliminar os mecanismos de recuperação e leitura dos dados autorizados.

## Correções de produção

O healthcheck do backend informa um host permitido e o esquema HTTPS do proxy confiável, evitando redirecionamento para um endpoint TLS inexistente na conexão interna. O healthcheck do Nginx verifica o CSS coletado do Admin. A verificação de produção confirmou ambos com DEBUG desativado e hosts sem `localhost`. Isso testa o encaminhamento HTTPS confiável; não provisiona certificados nem termina TLS público.

Para aplicar as alterações de configuração a uma instalação existente, use o procedimento de implantação: coletar estáticos e recriar backend/Nginx com as configurações de produção corretas. A auditoria executou containers e bancos descartáveis; não recriou os serviços em uso.

## Resultados

- Suíte `manage.py test tests api --noinput --verbosity 1`: **285 testes aprovados**.
- `python scripts/verify_production_static.py`: **aprovado com DEBUG=0**, oito assets coletados e healthchecks válidos; banco temporário removido.
- `scripts/verify_celery_queues.py` via shell Django: **aprovado com Redis e dois workers reais**, sem criar exportação ou alterar dados de uso.
- `python scripts/run-browser-tests.py check-admin.cjs check-realtime.cjs check-media-delivery.cjs check-real.cjs`: **4 cenários e 3 auxiliares aprovados**, usando a configuração atual do Nginx e estáticos exclusivos da rodada.
- Configuração Compose, montagem somente para leitura, filas e sintaxe dos scripts: **aprovadas**.

Logs desta auditoria: `.tools/audit-priorities-backend.log`, `audit-production-static.log`, `audit-celery-queues.log` e `audit-priorities-browser.log`. Assets e log do teste de produção: `.tools/production-static/5a9ccdfbb086/`. Resultados do navegador: `.tools/browser-tests/15c8c7452a42/`. As execuções anteriores de build e dos 24 cenários distintos de navegador permanecem registradas em [Verificação da implementação](<Verificacao da implementacao.md>).
