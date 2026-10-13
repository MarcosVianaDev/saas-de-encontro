# Reexecução de testes — 12/10/2026

> Registro histórico anterior às correções. A [validação posterior](<Correcao dos testes - 12-10-2026.md>) aprovou 181 testes de backend e 18 scripts de navegador; use esse relatório para o estado atual.

Resultado: **a suíte completa não passou**. Esta execução substitui os números anteriores de 171 testes. Nenhuma correção de aplicação ou de asserções foi aplicada nesta rodada.

| Verificação | Resultado |
|---|---|
| Backend: `docker compose exec -T backend python manage.py test tests api --noinput --verbosity 2` | 180 testes em 22,520 s: **164 aprovados, 11 falhas e 5 erros** |
| Navegador: todos os 17 scripts `.tools/ui-check/*.cjs` | **4 aprovados, 13 não aprovados** |
| `npm run build` em `frontend` | Aprovado; avisos de diretivas `use client` de React Bootstrap |
| `manage.py check` | Aprovado |
| `manage.py makemigrations --check --dry-run` | Aprovado: nenhuma migração pendente |
| Verificadores auxiliares de concorrência, escopo e Admin HTTP | 2 aprovados, 1 interrompido por restrição do banco |
| `export-final-check/verify.py` e `export-offline-check/verify.py` | Ambos aprovados: hashes dos pacotes existentes |
| Sintaxe e validação isolada dos blocos de limpeza de `full-clean.ps1` / `.sh` | Aprovados |

## Falhas do backend

Os métodos abaixo usam os nomes originais dos testes. “Erro” significa que uma exceção interrompeu o cenário; não comprova as asserções posteriores.

| Módulo / método | Resultado e diagnóstico |
|---|---|
| `tests.test_admin.AdminTests.test_every_domain_model_is_registered` | Falha: `events.ExportJob` não está registrado no Django Admin. Lacuna de integração com a convenção testada pelo projeto. |
| `api.tests.DemoFlowTests.test_seed_populates_every_domain` | Falha: não há `ExportJob` na carga demo. A asserção genérica de que todo modelo tem registros precisa ser reconciliada com jobs criados sob demanda; não comprova defeito na exportação. |
| `api.test_mvp.FoundationTests.test_audit_failure_rolls_back_domain_changes` | Erro: fixture de evento presencial sem ponto de referência. |
| `api.test_mvp.FoundationTests.test_celery_calls_same_service_and_observes_automatic_delay` | Mesmo erro de coordenadas, antes das asserções do cenário. |
| `api.test_mvp.FoundationTests.test_early_closing_requires_confirmation_reason_and_session_challenge` | Mesmo erro de coordenadas. |
| `api.test_mvp.FoundationTests.test_transition_retries_do_not_duplicate_audit_or_notifications` | Mesmo erro de coordenadas. |
| `api.test_mvp.FoundationTests.test_progressive_configuration_and_authorization` | Falha: PUT 400, esperado 200. Resposta: “Verifique os valores das configurações e as datas do evento.” Causa específica ainda não determinada. |
| `api.test_mvp_flows.MvpFlowTests.test_activation_requires_outfit_three_public_photos_and_event_fields` | Falha: ativação 400, esperado 200. Diagnóstico reproduzido: “Valide a localização antes da ativação presencial.” |
| `api.test_mvp_flows.MvpFlowTests.test_profile_removal_preserves_history_requires_origin_and_allows_replacement` | Falha: ativação 400, esperado 200; mesma pré-condição de localização. |
| `api.test_mvp_flows.MvpFlowTests.test_create_online_event_with_auto_activation_and_reject_physical` | Falha: 400, esperado 201. Responsável deve ser membro ativo vinculado ao cliente. |
| `api.test_mvp_flows.MvpFlowTests.test_geolocation_presence_outside_and_technical_recovery` | Falha: `DISTANT`, esperado `OUTSIDE`. Divergência de limiar/expectativa ainda precisa ser reconciliada. |
| `api.test_mvp_flows.MvpFlowTests.test_guided_client_draft_activation_is_atomic_and_idempotent` | Falha: fluxo legado global retorna 400, esperado 200. Resposta genérica de campos inválidos; causa específica ainda não determinada. |
| `api.test_mvp_flows.MvpFlowTests.test_payment_instructions_are_global_only_and_freeze_at_start` | Falha: PUT global 400, esperado 200; mesma mensagem de configuração/datas inválidas. |
| `api.test_mvp_flows.MvpFlowTests.test_likes_hidden_and_reveal_oldest_consumes_once` | Erro `KeyError: hidden`: consulta retorna 403 e o teste tenta acessar payload de sucesso. |
| `api.tests.DemoFlowTests.test_profile_filters_and_event_isolation` | Falha: 403, esperado 404. Revisar pré-condições de acesso e isolamento. |
| `api.tests.DemoFlowTests.test_reciprocal_match_message_and_readonly_end` | Falha: 403, esperado 200. Revisar pré-condições de acesso social. |

Os 9 testes de `api.test_exports` passaram dentro da execução completa. Não afrouxar autorização, vínculo de responsável ou validação de localização para fazer fixtures antigas passarem.

## Testes de navegador

Os scripts originais foram executados com asserções preservadas. Um harness adaptou apenas URLs/target Docker em memória para usar banco, mídia e backups temporários; frontends Django e mock usaram as portas 18081/18082. Falhas de timeout interrompem o script: os passos posteriores continuam sem validação nesta rodada.

| Script em `.tools/ui-check` | Resultado / ponto de interrupção |
|---|---|
| `check-onboarding-topics.cjs` | Aprovado: tópicos opcionais omitidos e cadastro em duas etapas. |
| `check-profile-fix.cjs` | Aprovado: perfil real e payload legado, campos e opções. |
| `check-theme.cjs` | Aprovado: Claro/Escuro/Automático, persistência, sistema, posição e Escape. |
| `check-toast-theme.cjs` | Aprovado: cores do popup de notificações acompanham o tema. |
| `check-event-requests.cjs` | Falha: espera role `checkbox`; controle atual usa `switch`. |
| `check-admin-mock.cjs` | Falha: espera menu `.adm-sidebar`, substituído pela navegação inferior. |
| `check-global-clients.cjs` | Falha após cadastro. Diagnóstico adicional reproduziu `Cannot read properties of undefined (reading 'map')`: fixture de cliente não fornece a equipe exigida pelo contrato atual. Também contém fluxo antigo de responsável por e-mail. |
| `check-mock.cjs` | Falha: imagem quebrada na rota de perfil do mock. Diagnóstico encontrou `<img alt="Foto pública selecionada">` sem `src`. |
| `check.cjs` | Falha na mesma asserção de imagens. |
| `check-mode.cjs` | Falha: espera o título antigo “Backend conectado”. |
| `check-navigation-logout.cjs` | **Defeito de interface reproduzido no participante:** após logout retornar 503, o aviso existe no DOM, mas `.toast` tem `display: none`. A mensagem de erro fica invisível. Não chegou aos outros modos. |
| `check-qr-event-uuid.cjs` | Falha: espera botão “Criar uma conta” no fluxo de entrada atual. |
| `check-admin.cjs` | Falha: espera `.adm-hero` após login de superusuário, que agora entra no painel global. |
| `check-lan.cjs` | Mesma expectativa de `.adm-hero`; executado com URL local adaptada, sem validar conectividade LAN. |
| `check-mvp.cjs` | Falha: espera heading “Suporte” na rota de mensagens; conteúdo atual não oferece esse heading. |
| `check-onboarding.cjs` | Falha: API global retorna 400 no fluxo legado de ativação de cliente. |
| `check-real.cjs` | Falha: após login e rota de perfil, espera botão “Continuar” inexistente no estado atual. |

O defeito do aviso de erro é distinto dos popups de notificações testados por `check-toast-theme.cjs`. Há evidência de mensagem invisível; a correção de CSS/componente ainda não foi aplicada. A imagem sem `src` foi reproduzida no acesso direto ao perfil do mock, sem atribuir o problema ao backend real.

## Verificações auxiliares e limites

- `verify_mvp_concurrency.py`: aprovado, duas conexões PostgreSQL consumiram exatamente um crédito e revelaram o like oculto mais antigo.
- `verify_admin_http.py`: aprovado, login HTTP/CSRF e 19 apps no Django Admin. Isso não contradiz a ausência do modelo `ExportJob` detectada pelo teste de registro.
- `verify_scope_gaps.py`: interrompido por `IntegrityError` de `matches_pair_ordered`. O utilitário tenta salvar par de participantes em ordem inválida após registrar rejeição no `full_clean`. A proteção funcionou; os demais probes não foram executados.
- Os dois `verify.py` de exportação validaram manifesto, existência dos arquivos e SHA-256 dos pacotes já extraídos. Não representam uma nova geração ponta a ponta pelo Celery.
- `full-clean`: sintaxe PowerShell/Bash aprovada; blocos de remoção validados em diretórios temporários, incluindo conteúdo oculto, subdiretórios, repetição, pasta ausente e links externos. Os comandos completos de reset não foram executados sobre o ambiente de uso.

Banco e container temporários foram usados nos checks que alteram dados. O ambiente temporário foi removido ao final; logs ficaram em `.tools/test-backend-full.log`, `.tools/test-backend-diagnostics.log`, `.tools/test-frontend-build.log` e `.tools/test-isolation/logs/`, com resultados JSON em `.tools/test-isolation/`. Esses artefatos locais não são versionados. Os logs PowerShell de backend/build usam UTF-16; os logs de navegador usam UTF-8.

## Pendências identificadas

1. Corrigir a exibição do aviso de erro e a imagem sem fonte no mock.
2. Registrar `ExportJob` no Admin conforme a convenção do projeto; definir a expectativa de seed para jobs sob demanda.
3. Atualizar fixtures e seletores frente às regras atuais, preservando as proteções do produto.
4. Investigar rejeições de configuração/cadastro e diferenças de presença/acesso ainda sem causa específica.
5. Reexecutar os cenários interrompidos após correções; conectividade LAN continua sem confirmação nesta rodada.
