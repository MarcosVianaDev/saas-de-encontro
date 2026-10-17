# Estado atual do sistema

> Atualização de 12/10/2026: a exportação assíncrona dos itens 10.3/10.4 passou a existir. Veja [Exportação de eventos](<Exportacao de eventos.md>): geração e download global, `ExportJob`, Celery, SQL/consulta offline, manifesto e termo PDF. As observações de ausência de exportação na revisão original abaixo são históricas; não significam ausência na versão atual.

Revisão do código em **12/10/2026**. Este documento consolida a implementação atual. Documentos de escopo descrevem requisitos; os relatórios de 03 e 04/10 registram verificações anteriores. Consulte [o índice](README.md), [operação e desenvolvimento](<Operacao e desenvolvimento.md>) e [a avaliação da etapa 10](<Etapa 10 - verificacao e pendencias.md>).

## Arquitetura e contextos

O Docker tem ambientes separados: `docker-compose.dev.yml` preserva o desenvolvimento padrão com Vite/HMR, enquanto `docker-compose.prod.yml` usa frontend multi-stage servido por Nginx, backend sem montagem do código-fonte, DEBUG/carga automática desativados, HTTPS no Traefik e persistência própria. Guia e comandos em [Docker: desenvolvimento e produção](<Docker - desenvolvimento e producao.md>).

A auditoria de **16/10/2026** confirmou os oito itens de prioridade alta, média e estrutural. Corrigiu a entrega de estáticos Django/Admin com DEBUG desativado (Nginx com pasta coletada somente para leitura e tipos MIME) e adicionou limite específico de denúncias de **10/min por conta**. Healthchecks foram ajustados para o ambiente atrás do proxy HTTPS. Resultados e evidências em [Verificação das prioridades](<Verificacao das prioridades.md>).

Desde **16/10/2026**, `frontend/main.tsx` é apenas a entrada da aplicação. As páginas do participante, ícones, navegação, alertas e modais estão separados, com hooks para sessão, rotas por hash, perfil, ações sociais e sincronização. Buscas e rascunhos ficam nas próprias páginas. A biografia completa tem limite uniforme de **50 a 200 caracteres**, inclusive na intervenção administrativa e ativação. Erros de validação dos modelos preservam os campos e todas as mensagens na resposta HTTP 400. Organização e contratos em [Arquitetura do frontend](<Arquitetura do frontend.md>).

Backend Django/DRF, autenticação por sessão e CSRF, PostgreSQL, Daphne, Redis, Celery e Celery Beat. Frontend React/TypeScript/Vite, React Bootstrap e CSS próprio. Docker Compose integra backend, frontend, worker, beat, banco, Redis, Nginx e Traefik.

| Acesso | Autorização | Identidade visual |
|---|---|---|
| Participante | Conta e participação no evento selecionado | Roxo/lilás |
| Administração do evento | Vínculo ativo, papel e permissões operacionais | Roxo/lilás |
| Administração global | Conta ativa com `is_superuser` | Azul no painel global; vermelho ao administrar um evento |
| Django Admin | Acesso técnico com permissões nativas do Django | Interface técnica separada |

`is_staff` sozinho não concede administração global. A sessão autentica a conta e conserva uma seleção inicial. Desde **16/10/2026**, cada operação administrativa de evento exige um escopo explícito em `X-Event-ID` ou `/api/events/<uuid>/...`, sempre revalidando vínculo ativo, papel e permissões. O frontend persiste a escolha em `sessionStorage` por aba e envia `X-App-Context` para distinguir participante, administração do evento e global. Trocar o evento em outra aba não redireciona as operações da aba original. Fotos privadas, evidências e downloads de exportação incluem o evento na URL. Login e seleção de contexto são tratados por `backend/api/contexts.py` e `event_admin.py`; resolução do escopo em `event_scope.py`.

Com `DJANGO_DEBUG=0`, hosts explícitos são obrigatórios, `*` impede a inicialização e os cookies de sessão/CSRF usam `Secure`; HTTP é redirecionado para HTTPS. O Nginx encaminha o protocolo original do proxy confiável. O Compose local permanece em desenvolvimento HTTP; produção exige configurar hosts, origens e terminação TLS. Contratos e parâmetros em [Operação e desenvolvimento](<Operacao e desenvolvimento.md>).

Desde **16/10/2026**, a API DRF limita requisições por IP anônimo (60/min) e conta autenticada (300/min), com contadores compartilhados em Redis. Login (10/min), cadastro (5/min), envio de mensagens (30/min) e interações de likes/skips (60/min) têm limites adicionais. Excesso retorna HTTP 429 com `Retry-After`; leituras não consomem o limite específico de escrita. Taxas e cadeia de proxies são configuráveis por ambiente. Veja configuração e limites da proteção em [Operação e desenvolvimento](<Operacao e desenvolvimento.md>).

O frontend oferece modos `mock` e `django`. O mock simula interações locais e conserva seus catálogos estáticos. O modo real recebe catálogos, perfis, estados e permissões da API. O botão **Demonstração**, após **Novo evento** em Ações rápidas do acesso global, abre o mock em nova aba sem mudar o `.env`: login com credenciais fictícias preenchidas, cadastro do perfil/fotos, 50 perfis variados, likes, matches, mensagens, notificações e avisos. Veja [Demonstração do frontend](<Demonstracao do frontend.md>). Uma demonstração visual não comprova persistência nem autorização real.

O tema cobre os três acessos, formulários, navegação, cards, modais e componentes Bootstrap. `ThemeSelector` permite Claro, Escuro e Automático; a preferência é persistida localmente em `eventconnect-theme`, e Automático segue o sistema operacional. A identidade de acesso é preservada. A aplicação do tema usa `frontend/theme.ts` e `dark-theme.css`. Controles booleanos são apresentados como toggles com label à esquerda e controle à direita, salvo a organização específica dos toggles dos cards de tópico, com labels acima.

## Administração global, clientes e equipe

O dashboard apresenta indicadores, alertas, atividade administrativa e ações rápidas **Novo cliente** e **Novo evento**. Clientes e eventos possuem busca e filtros; é possível acessar a administração de um evento a partir do painel global.

O cadastro inicial do cliente exige nome, e-mail e telefone. Cria organização, conta de acesso, perfil global e vínculo de equipe em transação. A conta nasce sem senha utilizável; o Django Admin permite defini-la. O cadastro complementar inclui cargo/função, observações, nome e descrição da organização. E-mails e nomes são validados; colisões de conta impedem criação parcial.

Na ficha do cliente:

- **Dados do cliente:** botão Completar / editar cadastro e Alterar senha / Definir senha da conta vinculada.
- **Equipe:** cadastro no topo direito; cards de largura inteira com primeiro nome em maiúsculas/negrito, função e Redefinir senha; clique no card abre edição de nome, e-mail e função.
- **Eventos do cliente:** eventos vinculados e atalho para criar novo evento.

A antiga seção **Acesso ao sistema** foi removida. As funções de cliente são Responsável pelo evento (`ADMIN`), Moderador (`MODERATOR`) e Operador (`OPERATOR`), persistidas em `OrganizationMember.role`. O responsável de um novo evento é escolhido em select de membros ativos do cliente; a API rejeita contas fora desse vínculo. A criação do evento concede administração aos membros ativos conforme seus papéis, atribuindo `ADMIN` ao responsável escolhido. O vínculo de cliente e o vínculo de evento são entidades distintas; alterações na equipe do cliente não sincronizam automaticamente vínculos de eventos já criados.

Em **Mais**, as abas Bootstrap são **Eventos**, **Participantes** e **Conta**. Eventos contém a seção de configurações globais, ainda sem controles próprios implementados. Participantes contém o cadastro de tópicos e acompanhamento de segurança. Conta contém Sair da conta e o botão Acessar Django Admin, exibido conforme o acesso técnico informado pela API.

Fontes: `frontend/GlobalAdministration.tsx`, `backend/api/global_admin.py`, `backend/apps/organizations/models.py`, `backend/api/test_global_clients.py`.

## Cadastro e solicitação de eventos

O cadastro global cria o evento como Agendado (`SCHEDULED`). A administração de um evento pode solicitar outro evento da mesma organização; a solicitação permanece em Rascunho (`DRAFT`) e depende da aprovação global. Esse fluxo tem endpoint e formulário próprios.

No formulário global, Cliente e Modalidade aparecem na primeira linha. Nome e Descrição vêm a seguir; Início e Término aparecem lado a lado imediatamente após a descrição. Latitude/Longitude e Raio/Limite adicional também são pares. Modalidades: Online, Presencial e Híbrido. Coordenadas são exigidas para modalidades com presença física; o intervalo de localização/presença é configurável. A ativação automática ao completar o perfil está disponível somente em Online.

Ao final estão a configuração de Presente inicial e o acordeon **Tópicos do participante**, inicialmente fechado. Cancelamento de alterações do formulário global possui proteção para alterações não salvas.

Fontes: `frontend/GlobalAdministration.tsx`, `EventRequestForm.tsx`, `backend/api/global_admin.py`, `event_requests.py`, `test_event_requests.py`.

## Tópicos cadastráveis e requisitos do evento

`ProfileTopic` armazena nome, chave estável, lista de opções e indicador de múltipla escolha. A administração global cadastra e edita tópicos em Mais → Participantes, com opções separadas por vírgula e toggle de múltipla escolha. As respostas por participante ficam em `ParticipantProfile.topic_answers`; interesses e finalidade também mantêm campos de compatibilidade para o perfil e filtros existentes.

| Tópico inicial | Opções sem “Outros” | Tipo inicial |
|---|---|---|
| Interesses | Música, Viagens, Tecnologia, Gastronomia, Esportes, Arte, Networking | Múltipla escolha |
| Finalidade no evento | Networking, Amizade, Relacionamento, Negócios, Troca de ideias | Escolha única |

A migração `profiles.0006_seed_profile_topics` cria esses tópicos e migra respostas existentes, removendo seleções fora das listas iniciais. As listas estáticas anteriores ficam no mock do frontend. No acesso real, opções do perfil e dos filtros vêm do banco.

O cadastro do evento salva as regras em `Event.settings.participant_topics`:

- Usar no evento habilita o tópico; desabilitá-lo também desmarca Obrigatório.
- As labels ficam acima dos toggles. Usar no evento fica à esquerda e Obrigatório à direita do nome.
- Clicar no card expande suas opções. Elas quebram em linhas à esquerda, reservando uma coluna à direita para o mínimo.
- Mínimo obrigatório aparece apenas quando o tópico é de múltipla escolha, obrigatório e o card está expandido. Recolher preserva o valor configurado.
- O mínimo é inteiro de 1 a 5, limitado também à quantidade de opções cadastradas. Escolha única obrigatória exige uma opção.

O backend rejeita tópicos inexistentes/duplicados, obrigatoriedade de tópico desabilitado e mínimos incompatíveis. Apenas os tópicos habilitados são expostos no perfil daquele evento. A validação do perfil e da ativação exige o mínimo de opções válidas e distintas. Eventos antigos sem `participant_topics` mantêm todos os tópicos disponíveis como opcionais.

Fontes: `frontend/ProfileTopicManagement.tsx`, `ProfileTopics.tsx`, `EventParticipantTopics.tsx`, `backend/apps/profiles/topics.py`, `backend/api/test_profile_topics.py`, `test_global_clients.py`.

## Equipe e operação do evento

O cabeçalho Equipe do evento tem Adicionar integrante à direita. Ao editar um integrante, os demais cards ficam ocultos. Editar vira Cancelar, que fecha o formulário e descarta as alterações; Salvar fica à direita. As permissões usam toggles à direita em linhas compactas.

O seletor de Papel inclui **Não participa deste evento**, que salva o vínculo de evento como inativo. Selecionar um papel ativo reativa o vínculo. Não há checkbox separado Vínculo ativo. A gestão global define administradores; a gestão de evento pode delegar temporariamente a um moderador e reassumir, conforme as regras da API.

Em Mais do evento, **Avisos do Evento**, **Suporte** e **Passes** usam acordeon Bootstrap inicialmente fechado; apenas uma seção pode estar aberta por vez. Equipe e relatório são áreas próprias acessíveis por Mais. A administração inclui lista/ficha de participantes, ativação, outfit, intervenções autorizadas em perfil, denúncias, evidências, notas, decisões e histórico de casos.

Relatórios financeiros são agregados de concessões declaradas; não existe confirmação externa de pagamento. Papéis e permissões são validados no servidor; ocultar um botão não substitui esse controle.

Correção de segurança em **16/10/2026**: a API rejeita denúncias repetidas do mesmo participante contra o mesmo alvo no evento com HTTP 400, inclusive após decisão de denúncia infundada. A validação usa a transação e o bloqueio do denunciado para serializar requisições simultâneas. Alertas de 10, análise automática em 20 e prioridade dos casos consideram denunciantes distintos do mesmo evento, excluindo denúncias administrativas, infundadas e sem denunciante. Duplicatas históricas não aumentam essa contagem e são preservadas com suas evidências. A proteção está na API, sem nova constraint ou migração. Cobertura: `backend/api/test_report_abuse.py` e teste de limiares em `test_mvp_flows.py`.

Fontes: `frontend/TeamManagement.tsx`, `Administration.tsx`, `AdminOperations.tsx`, `backend/api/team.py`, `event_admin.py`, `passes.py`, `profile_operations.py`.

## Participante, presença, notificações e passes

O participante possui ingresso por convite, cadastro/perfil, fotos, tópicos, filtros, descoberta, likes, matches, mensagens, suporte, notificações e consulta de passes. O estado de residência opcional utiliza UF brasileira, validada no backend e apresentada nos cards/ficha; isso não constitui filtro por UF implementado. A apresentação de participantes limita os interesses visíveis nos cards e preserva consulta de perfil autorizada.

O cadastro utiliza primeiro/sobrenome, mês/ano de nascimento, gênero e bio validada. A ativação exige três fotos públicas e uma principal, requisitos do evento e, no fluxo convencional, outfit capturado pela equipe. A ativação automática Online dispensa outfit e aprovação presencial; mantém fotos, bio e requisitos obrigatórios. Fotos públicas e substituições após intervenções obedecem às regras do backend.

Desde **16/10/2026**, fotos de perfil, outfits, fotos administrativas e evidências locais usam `X-Accel-Redirect` no fluxo padrão pelo Compose: Django autoriza e Nginx transmite os bytes pela rota interna, com o diretório montado somente para leitura. Permanecem as verificações de evento, match, bloqueio, papel e auditoria. Caminhos e links simbólicos são validados; não há acesso público direto à pasta. Configuração e testes em [Mídia protegida](<Midia protegida.md>).

Presença Online decorre da interação recente com o servidor, conforme intervalo do evento, sem GPS. Presencial/Híbrido possuem consentimento/localização, retries, exceções e investigação de anomalias. Consulta de histórico depende de papel, estado e auditoria. Favoritos pertencem ao pós-match. Likes revelados por passes são processados cronologicamente, dentro do saldo ou da duração, com proteção transacional.

Desde **16/10/2026**, `current()` limita a gravação de atividade a uma vez por minuto também em Online, com revalidação da condição no UPDATE. O participante recebe avisos por [WebSocket autenticado](<WebSocket e tempo real.md>) e consulta `sync/` para mensagens incrementais e status, em páginas de até 100 mensagens. Mantém recuperação a cada 60–63 segundos conectado e 15–18 segundos sem WebSocket; não executa mais polling de `bootstrap/` nem recarrega todo o histórico da conversa. O catálogo é atualizado separadamente nas telas sociais, a cada minuto. Leituras são confirmadas somente para mensagens recebidas no chat aberto. Cursor assinado, paginação, índices e limites de consistência estão em [Sincronização de participantes](<Sincronizacao de participantes.md>).

As notificações internas são persistidas e filtradas por conta, contexto e evento, incluindo eventos sociais, mensagens, avisos e passes. Notificações não devem revelar a identidade de likes sem passe ou match autorizado. Avisos podem ser rascunhos, enviados ou agendados; envio e agendamento são validados e auditados. Não há serviço transacional de e-mail/push de produção implementado apenas por existir notificação interna.

Fontes: `frontend/main.tsx`, `ParticipantOnboarding.tsx`, `ParticipantExtras.tsx`, `SocialSafety.tsx`, `backend/api/services.py`, `notifications.py`, `views.py`, `location.py`, `backend/apps/passes/services.py` e testes dos respectivos recursos.

## Presente inicial

O cadastro global e a solicitação de evento permitem habilitar **Presente inicial**, informar nome e cadastrar um passe gratuito por quantidade de revelações ou duração em minutos. Essas duas modalidades do passe são alternativas. O recurso funciona em Online, Presencial e Híbrido.

| Prazo | Comportamento |
|---|---|
| 0 minutos | Ao ativar o perfil, o participante recebe o passe concedido e ativado. |
| Maior que 0 | O vencimento do prazo é calculado a partir de `starts_at`; a rotina entrega quando o evento está `RUNNING` e o participante está ativo. |
| Perfil ativado após o prazo | Recebe o presente na ativação, se o evento ainda permite a entrega. |

O horário da entrega deve ser **anterior** ao término; igualdade ao término também é rejeitada. A interface limita o valor e a API valida novamente. A validação do modelo impede encurtar as datas deixando o presente além do evento. A duração de um passe temporal conta a partir da concessão; a restrição de agendamento trata o horário de entrega, não redefine essa duração.

O serviço não entrega a perfil inativo/sem ativação, conta inativa, participação banida ou evento terminado. A entrega com atraso aguarda `RUNNING`; pausa não prorroga o horário final. A tarefa roda a cada 30 segundos, portanto a entrega agendada ocorre na próxima execução elegível, sem garantia de precisão ao segundo. O fluxo de prazo zero também é chamado diretamente pela ativação manual/automática.

Uma configuração habilitada cria `PassType` e `EventPassOffer` de preço zero; `Event.settings.initial_gift` referencia a oferta e o atraso. A concessão cria `ParticipantPass`, `PassActivation`, registro de auditoria e notificação “Seu presente inicial foi ativado”. Locks e a constraint `participant_initial_gift_unique` limitam a um presente por participação; revogação não libera uma segunda entrega automática.

Fontes: `frontend/InitialGiftFields.tsx`, `backend/apps/passes/gifts.py`, `tasks.py`, `backend/api/test_initial_gifts.py`, migração `passes.0005_participantpass_participant_initial_gift_unique`.

## Ciclo de vida, auditoria e limites

Estados: Rascunho → Agendado → Aberto → Em andamento; pausa/retomada, Encerrado e Arquivado completam o ciclo. Abertura manual pode ocorrer desde duas horas antes; a automática ocorre cinco minutos antes. A abertura automática acrescenta dez minutos ao início; o encerramento pelo horário final prevalece inclusive em Pausado. O arquivamento ocorre automaticamente quinze dias após `closed_at`, com auditoria e notificações.

A API bloqueia diversas operações em Encerrado/Arquivado; o frontend utiliza `readOnly`. Isso ainda **não comprova leitura exclusiva integral**: suporte administrativo e retomada de delegação possuem caminhos de escrita sem a mesma barreira, detalhados na [avaliação da etapa 10](<Etapa 10 - verificacao e pendencias.md>). A gestão global conserva ações fora do contexto arquivado que exigem análise de escopo.

`AuditLog` possui proteção append-only e registro de ações do domínio. Históricos de casos e downloads autorizados de evidências são auditados. A consulta geral da auditoria no painel ainda está pendente; a exportação ZIP e a consulta offline dos registros de auditoria foram adicionadas, conforme o guia de exportação. Modelos de retenção, consentimento e Legal Hold não equivalem a um motor de retenção operacional concluído.

As etapas 1–8 têm registros históricos de conclusão; melhorias posteriores ampliaram esses recursos. A etapa 9 continua parcial; a etapa 10 é parcial somente quanto ao arquivamento/consulta, e a exportação técnica foi entregue e a homologação formal permanece pendente. Homologação integral e gate de produção permanecem no backlog.

## Automações registradas

| Tarefa | Frequência atual | Serviço de domínio |
|---|---|---|
| `apps.events.tasks.synchronize_events` | 30 s | Transições e arquivamento |
| `apps.notifications.tasks.dispatch_announcements` | 30 s | Avisos agendados |
| `apps.passes.tasks.expire` | 30 s | Expiração de passes |
| `apps.passes.tasks.initial_gifts` | 30 s | Presente inicial |

Exportação usa a tarefa sob demanda `apps.events.export_tasks.generate`, não Beat. Desde **16/10/2026**, ela é roteada para `exports`, consumida exclusivamente por `celery_exports`. `celery_worker` consome somente a fila operacional `celery`; ambos têm concorrência 1 e prefetch 1. Uma exportação longa não ocupa o processo que executa as automações. Retenção ainda não possui tarefa periódica registrada. Configuração, atualização e teste real de isolamento em [Operação e desenvolvimento](<Operacao e desenvolvimento.md>).

O bootstrap administrativo também carrega cards, suspensões, fotos, contagens de denúncias/bloqueios, sinais de bloqueio e dados das ocorrências em lote. `operational_status` aproveita os dados pré-carregados, mantendo as regras anteriores. Testes com 100 participantes e 99 ocorrências verificam quantidade constante de consultas SQL, incluindo notas, histórico e evidências. A resposta continua contendo a lista integral; esta correção não adiciona paginação.

## Migrações e validação

As migrações adicionais relevantes incluem `organizations.0003` (papel da equipe), `profiles.0004` (finalidade), `profiles.0005` (tópicos/respostas), `profiles.0006` (catálogos iniciais), `profiles.0007` (UF de residência), `passes.0004` (snapshot do nome) e `passes.0005` (unicidade do presente).

Resultados atuais e limitações ficam em [Verificação da implementação](<Verificacao da implementacao.md>). Contagens de testes de relatórios anteriores permanecem históricas; devem ser acompanhadas de data, comando e resultado.
