# Administração e ingresso no evento

> Este guia registra a implementação existente. As definições posteriores de permissões delegáveis, alertas por denúncias e ciclo completo do evento estão nos [requisitos consolidados](<Escopo Técnico.md>); consulte o [índice e análise](README.md) para as diferenças. A consolidação documental não altera os comportamentos descritos abaixo.

Implementado em 04/10/2026, com base nos [fluxos e mockups administrativos](<Telas administrativas.md>).

## Executar e acessar

O ambiente está configurado com `FRONTEND_DATA_MODE=mock`, incluindo as telas administrativas. Abra http://192.168.1.32:8080/#admin-dashboard ou use **Explorar administração** na prévia do participante. Não é necessário fazer login.

A demonstração administrativa contém 12 participantes com situações distintas, quatro ocorrências com relato/notas/histórico/evidências fictícios, indicadores de bloqueios, quatro membros da equipe e métricas agregadas. O seletor apresenta eventos em andamento, agendados e encerrados; o controle de papel permite simular Administrador, Moderador e Operador. Suspensão, reativação, banimento, notas, resolução/reabertura e criação de ocorrências alteram apenas dados em memória. **Restaurar demonstração** ou recarregar a página restaura os exemplos.

No modo mock, o QR Code aponta para `/?demoEvent=<identificador>#login`, abrindo a prévia do participante com o nome do evento. Não cria contas nem participações no banco. As telas administrativas não consultam a API neste modo. O modo definido no `.env` vale também para URLs com convite; o ingresso real exige `FRONTEND_DATA_MODE=debug`.

Para conectar o frontend ao Django, altere para `FRONTEND_DATA_MODE=debug` e recrie o frontend. As instruções seguintes de login, autorização, cadastro e API referem-se ao modo conectado. Após atualizar o código:

```powershell
docker compose up -d --build --wait
```

O backend aplica as migrações ao iniciar. O frontend agora utiliza `qrcode`, instalado a partir do `package-lock.json`. Acesse http://localhost:8080 e entre com uma conta vinculada a `EventAdministrator`. A conta local `admin-demo@eventconnect.local` já possui vínculo com o evento principal; sua senha está em `.tools/demo-credentials.json`, ignorado pelo Git. Contas de participantes continuam usando a navegação de perfil, filtros, descoberta, mensagens e participantes.

No Django Admin, cadastre o vínculo em **Events → Event administrators** e escolha o papel:

| Papel | Participantes | Moderação e suspensão | Banimento e reabertura |
|---|---|---|---|
| `ADMIN` — Administrador | Sim | Sim | Sim |
| `MODERATOR` — Moderador | Sim | Sim | Não |
| `OPERATOR` — Operador | Sim | Não | Não |

Vínculos administrativos existentes recebem `ADMIN` na migração. O papel depende do evento, não de um tipo global fixo de conta. `is_staff` e `is_superuser` continuam controlando o Django Admin; não substituem o vínculo necessário para acessar o painel React de um evento.

## Login e seleção de navegação

Login e restauração de sessão retornam `navigation: administration|participant`. Sem convite, uma conta com vínculos administrativos entra no painel do primeiro vínculo cadastrado. O seletor permite trocar entre seus eventos autorizados. Contas sem vínculo administrativo seguem para sua participação no evento demo, quando existente, ou para sua primeira participação.

Com convite válido, login prioriza o evento do convite e a navegação do participante, inclusive para contas que também tenham vínculos administrativos. O token nunca concede papel administrativo. A participação é criada uma única vez e começa com cadastro incompleto; o participante precisa completar os requisitos de perfil e fotos para ativá-la. Contas existentes reutilizam sua identidade, sem criar uma segunda conta.

Consultas e ações verificam vínculo, evento e papel no backend. Conhecer um UUID ou alterar o hash do navegador não concede acesso. O painel não dá acesso irrestrito a mensagens, likes, matches individuais, passes nem fotos posteriores ao match.

## Telas e endereços

| Área | Hash | Operação |
|---|---|---|
| Dashboard | `#admin-dashboard` | Totais, atividade recente, pendências e atalho para QR Code |
| Participantes | `#admin-participants` | Busca nome/e-mail, filtros, ordenação, ficha, ocorrências e sanções |
| Moderação | `#admin-moderation` | Busca, filtros por tipo/status/motivo/período, prioridade, investigação, notas e decisões |
| Evento | `#admin-event` | Dados somente leitura, responsáveis, status e acesso ao QR Code |
| QR Code | `#admin-qr` | Exibição, tela cheia, cópia, compartilhamento e download PNG |
| Mais | `#admin-more` | Equipe, relatório e saída da conta |
| Equipe | `#admin-team` | Consulta dos vínculos e papéis |
| Relatório | `#admin-report` | Resultados agregados parciais ou consolidados |

A navegação inferior aparece no mobile, com menu lateral no desktop. Fichas e ocorrências são estados internos dessas áreas. Equipe é consultiva no React; alterações de vínculos e papéis ficam no Django Admin. Os relatórios apresentam totais, sem gráficos nem exportação de resultados nesta etapa.

Ativos agora significa participação ativa, sem banimento/suspensão no evento, com acesso autenticado à API nos últimos cinco minutos. `last_seen_at` registra essa atividade, no máximo uma atualização por minuto. A ausência de atividade recente é independente de cadastro incompleto, suspensão e banimento. Novos significa cadastro na última hora. O painel consulta a API a cada 15 segundos quando visível; não utiliza WebSocket.

## Participantes e moderação

A ficha identifica `EventParticipant` e apresenta apenas informações operacionais permitidas. Operadores não recebem relatos, contagens de denúncias/bloqueios, justificativas sensíveis nem detalhes de evidências. Fotografias reais exibidas no painel usam uma rota autenticada limitada à foto principal anterior ao match no evento autorizado.

Suspender cria `EventSuspension`, com autor e justificativa, restringindo apenas aquele evento. Nesta versão a suspensão permanece até reativação explícita; `ends_at` também permite prazo quando configurado no Admin. Reativação registra `revoked_at`, preservando o registro anterior. Banimento cria `EventBan` e exige confirmação explícita. Essas restrições são verificadas na API do participante e na elegibilidade de descoberta.

Ocorrências administrativas podem ser abertas pela ficha. O registro separa motivo de descrição, cria `Report`/`ModerationCase` e registra notificações internas para administradores/moderadores do evento e superusuários globais ativos. A autoria usa `Report.created_by`, sem criar uma participação fictícia para o funcionário. Não envia e-mail ou push. Denúncias e ocorrências administrativas são diferenciadas na fila; prioridade é configurável no Django Admin.

É possível assumir um caso sem responsável, adicionar notas internas, aplicar sanções, resolver e reabrir. Uma atribuição existente não pode ser tomada por outro moderador. Casos resolvidos exigem reabertura antes de novas alterações. Reabertura é restrita ao administrador. Sanções mantêm o caso em acompanhamento; a resolução é uma ação separada, com justificativa. O histórico apresentado é derivado de `AuditLog` append-only. Registros antigos de `ModerationAction` permanecem no Admin e não são retroativamente convertidos em auditoria.

Bloqueios são consultados como indicadores agregados e linha do tempo. A consulta não gera caso, denúncia nem punição automaticamente; não há limiar de alerta definido. Evidências cadastradas podem ser consultadas/baixadas somente por moderadores e administradores no evento correto, com auditoria de download. Tipos permitidos, coleta/upload de novas evidências e catálogo formal de motivos continuam dependendo de especificação. O motivo é informado em texto livre, sem catálogo rígido na interface.

## QR Code e cadastro vinculado

Evento e Dashboard oferecem QR Code enquanto o evento estiver aberto para ingresso. A imagem é gerada no navegador com [node-qrcode](https://github.com/soldair/node-qrcode), sem enviar a URL a um serviço externo.

A URL tem o formato `/?invite=<token-assinado>`. O backend valida assinatura com salt exclusivo de ingresso, validade de 30 dias e término do evento. O encerramento recusa novos ingressos mesmo que o token ainda esteja dentro do prazo. O QR Code representa um convite compartilhável, não uma credencial administrativa.

Ao abrir o link, o usuário vê o evento de destino e pode entrar ou criar uma conta. Cadastro com convite válido funciona também fora de DEBUG. Cadastro sem convite continua limitado à demonstração em DEBUG. Usuários já autenticados são associados pelo endpoint de ingresso com CSRF. O token é retirado da URL após a associação; o evento escolhido fica na sessão.

A URL utiliza a origem pela qual o painel foi aberto. Para leitura em outro dispositivo, abra o painel em **http://192.168.1.32:8080** neste ambiente; o QR Code utilizará esse endereço. O Compose publica a porta em `0.0.0.0` e o Django aceita todos os hosts, mantendo CSRF para login e escritas. A regra `EventConnect-HTTP-8080` libera a porta para a sub-rede local no Firewall do Windows. O endereço `localhost:8080` continua funcionando no próprio computador, mas não representa este servidor em outro dispositivo.

## Endpoints adicionados

Todos usam `/api/`. Escritas autenticadas exigem sessão e CSRF. Login e cadastro também mantêm proteção CSRF.

| Caminho | Método | Comportamento |
|---|---|---|
| `event-admin/` | GET | Dados do painel restritos ao evento/papel da sessão |
| `event-admin/` | POST | Selecionar outro vínculo administrativo, enviando `event` |
| `event-admin/participants/<uuid>/action/` | POST | `report`, `suspend`, `reactivate`, `ban`; `reason`, `category` para ocorrência e `confirmed` para banimento |
| `event-admin/cases/<uuid>/action/` | POST | `assume`, `note`, `resolve`, `suspend`, `ban`, `reopen`; justificativa e confirmação conforme ação |
| `event-admin/evidence/<uuid>/content/` | GET | Download autorizado e auditado de evidência |
| `event-admin/photos/<uuid>/content/` | GET | Foto principal anterior ao match, restrita ao evento |
| `join/<token>/` | GET | Validação pública do convite e informações do evento |
| `join/<token>/` | POST | Associação idempotente da conta autenticada ao evento |

`auth/login/` e `auth/register/` aceitam `invite` opcional. `bootstrap/` retorna o estado do participante ou o discriminador da navegação administrativa. O frontend carrega o painel em `event-admin/` após identificar a navegação.

## Validação

Testes Django cobrem login sem participação para administradores, restauração de sessão, papéis, isolamento entre eventos, privacidade, suspensão/reativação, banimento, notas, resolução/reabertura, atribuição, indicadores de bloqueio, evidências e convite/cadastro com DEBUG desativado. Também verificam CSRF, validade, expiração e recusa de ingresso após encerramento.

Playwright/Edge verifica login administrativo, filtros, fichas, navegação, restauração, ingresso de conta existente e layouts de 320, 375, 768 e 1440 pixels. O teste decodifica a imagem do QR Code com um leitor independente e compara o resultado com a URL de convite.

```powershell
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend python manage.py test tests api --noinput
docker compose exec frontend npm run build
```

Retenção automatizada, critérios de alertas, WebSocket, upload de evidências, equipe editável no React e relatório avançado permanecem fora desta implementação. Não foram estabelecidos prazos legais nem regras de eliminação de dados.
