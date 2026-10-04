# SaaS de Encontro — Escopo Técnico

> Documento de requisitos consolidado em 04/10/2026. Não é uma declaração de funcionalidades já implementadas; consulte [Verificação da implementação](<Verificacao da implementacao.md>). O texto preserva a evolução da fonte: as seções finais de definição/consolidação prevalecem sobre propostas anteriores do mesmo assunto. Consulte o [índice e análise](README.md) para divergências e precedência.

## 1. Diretriz arquitetural

O projeto será desenvolvido inicialmente como um monólito modular, evitando microserviços nesta fase. A separação será feita por domínios de negócio dentro do Django, permitindo evolução posterior sem introduzir complexidade operacional prematura.

A aplicação será composta por um frontend React/TypeScript e um backend Python/Django, comunicando-se por API HTTP/JSON.

## 2. Frontend

React com TypeScript será responsável pela experiência web dos participantes, organizadores e administradores. A interface deverá ser responsiva e preparada desde o início para uso em desktop e dispositivos móveis.

O frontend concentrará as experiências interativas do evento, incluindo perfis, navegação entre participantes, interações, matches, chat, notificações e dashboards personalizados.

## 3. Backend e API

Python com Django será a base do backend. Django REST Framework será utilizado para disponibilizar a API consumida pelo frontend React.

O backend concentrará autenticação, autorização, permissões, regras de negócio, eventos, salas, participantes, perfis, interações, matches, comunicação, denúncias, bloqueios, moderação, auditoria, consentimentos, retenção de dados e métricas.

Django Admin será utilizado como interface administrativa interna inicial, permitindo acelerar a operação e a moderação antes da necessidade de construir todos os painéis administrativos personalizados em React.

## 4. Banco de dados

PostgreSQL será o banco de dados relacional principal. O modelo de dados deverá considerar desde a primeira versão usuários, eventos, salas, participantes, perfis, interações, matches, bloqueios, denúncias, consentimentos, auditoria e ciclo de vida dos dados.

## 5. Tempo real

Django Channels com WebSockets será adotado para funcionalidades que realmente necessitem comunicação em tempo real, principalmente chat, notificações e atualizações ocorridas durante um evento.

## 6. Processamento assíncrono e cache

Celery será utilizado para tarefas executadas em segundo plano e Redis servirá como broker e camada de cache quando necessário.

Esse conjunto atenderá tarefas como notificações, rotinas pós-evento, expiração e exclusão de dados, processamento de métricas e outras operações que não devem bloquear requisições da aplicação.

## 7. Fotos e arquivos

Fotos e demais arquivos ficarão em armazenamento separado do banco de dados. Durante o desenvolvimento local poderá ser utilizado armazenamento local ou MinIO. Em produção, a arquitetura deverá utilizar storage compatível com S3.

O PostgreSQL armazenará referências, metadados e regras associadas aos arquivos, enquanto os objetos binários permanecerão no storage.

## 8. Ambiente de desenvolvimento

Docker e Docker Compose serão utilizados para tornar o ambiente local reproduzível. O ambiente deverá permitir subir de forma coordenada Django, React, PostgreSQL, Redis, workers Celery e o serviço de armazenamento necessário ao desenvolvimento.

## 9. Organização por domínios

A estrutura Django deverá ser modularizada por responsabilidade de negócio. Os principais domínios previstos são: contas e identidade; eventos; salas; participantes; perfis; interações; matches; comunicação; denúncias e bloqueios; moderação; consentimento e LGPD; retenção; auditoria; analytics.

## 10. Segurança, LGPD, denúncias e retenção

LGPD, denúncias, bloqueios, moderação, auditoria e retenção de dados são requisitos estruturais e não funcionalidades a serem adicionadas posteriormente.

O sistema deverá registrar bloqueios e denúncias com motivo e descrição do ocorrido, notificando a administração responsável pelo evento e a administração geral do sistema. Esses registros também deverão alimentar métricas administrativas.

Dados e arquivos relacionados aos eventos deverão seguir uma política explícita de ciclo de vida. Ao término do evento, os dados previstos pelo escopo serão arquivados pelo período legal aplicável e, encerrado esse período sem necessidade legítima de preservação, deverão ser eliminados conforme a política definida para o produto. O prazo jurídico exato deverá ser validado antes da implementação da política definitiva.

## 11. Stack consolidada

Frontend: React + TypeScript

Backend: Python + Django

API: Django REST Framework

Banco de dados: PostgreSQL

Tempo real: Django Channels + WebSockets

Tarefas assíncronas: Celery

Cache/broker: Redis

Storage local: armazenamento local ou MinIO

Storage de produção: compatível com S3

Ambiente local: Docker + Docker Compose

Arquitetura inicial: monólito modular

## 12. Modelagem lógica e regras funcionais consolidadas

### 12.1 Princípios do modelo de dados

As entidades principais utilizarão UUID como chave primária. User representa a identidade global na plataforma; EventParticipant representa a pessoa dentro de um evento; RoomParticipant representa sua participação em uma sala. EventParticipant será o pivô das operações do evento, evitando mistura de dados entre eventos.

Dados persistentes da conta serão separados dos dados vinculados ao ciclo de vida do evento. O perfil global poderá ser reutilizado em novos eventos, enquanto cada participação mantém seu próprio contexto. Estados e transições serão explícitos; não será adotado soft delete genérico. Auditoria será append-only.

### 12.2 Entidades centrais

Administração global: User, UserProfile, Organization, OrganizationMember, Event, EventAdministrator, AuditLog, SystemNotification, ConsentRecord, DataRetentionRecord e PrivacyRequest.

Evento e salas: Room, RoomConfiguration, RoomAdministrator, EventParticipant, RoomParticipant e métricas por evento/sala.

Perfil e descoberta: ParticipantProfile, ParticipantPhoto, EventOutfitPhoto, ProfileField, ProfileFieldOption, ParticipantFieldValue, ParticipantPreference, ProfileDiscovery, Interaction e InteractionHistory.

Relacionamento: Match, Conversation e Message.

Segurança e moderação: Block, Report, ReportEvidence, ModerationCase, ModerationAction, ModerationNote, UserSuspension, EventBan e RoomBan.

Benefícios e comercialização: PassType, EventPassOffer, ParticipantPass, PassUsage, PassPurchase, Payment, PassActivation e, quando aplicável, Payout/Settlement.

Governança: ConsentRecord, DataRetentionRecord, LegalHold, PrivacyRequest e AuditLog.

### 12.3 Perfil do participante

Campos fixos obrigatórios: nome, sobrenome, mês e ano de nascimento, gênero e bio com no mínimo 50 caracteres. A idade será calculada. O modelo também suportará atributos opcionais e configuráveis, além de altura, hábitos e demais informações previstas pelo produto.

A plataforma terá campos e tags globais cadastrados pela administração do sistema e campos específicos criados pela administração do evento. Cada campo poderá ter opções próprias e ser definido como obrigatório ou opcional e, quando aplicável, utilizável em filtros.

O perfil persistente da conta poderá ser reaproveitado em novos eventos. Ao entrar em um evento, os dados serão pré-preenchidos e poderão ser revisados conforme as exigências daquele evento.

### 12.4 Fotos

O participante poderá cadastrar no máximo 10 fotos de perfil. Para ativação, serão exigidas pelo menos 3 fotos, sendo uma definida como principal. Antes do match, somente as 3 fotos públicas obrigatórias serão exibidas. Até 7 fotos adicionais ficarão disponíveis somente após match ativo.

A foto de outfit será separada da galeria e vinculada ao EventParticipant. Ela representa como a pessoa está vestida naquele evento e somente será revelada após o match.

### 12.5 Ativação do perfil

O participante somente ficará apto à descoberta quando cumprir os requisitos do evento: campos obrigatórios, bio mínima, quantidade mínima de fotos, foto principal e demais campos configuráveis exigidos.

### 12.6 Filtros e preferências

Atributo do perfil e preferência de busca serão conceitos separados. Cada preferência poderá ser marcada pelo usuário como restritiva ou preferencial, além de ser ativada, desativada e alterada.

O sistema não flexibilizará filtros automaticamente. Quando não existirem mais perfis elegíveis, a descoberta será interrompida e o usuário será orientado a revisar seus filtros. Alterações posteriores recalculam a elegibilidade sem apagar o histórico de perfis já apresentados.

### 12.7 Histórico de descoberta

ProfileDiscovery registrará quais participantes foram apresentados e quando. Interaction manterá a decisão atual, inicialmente LIKE ou PASS. InteractionHistory preservará mudanças de decisão.

A interface permitirá consultar históricos de “Gostei” e “Não gostei”. Uma decisão anterior poderá ser alterada. Um PASS poderá se tornar LIKE e, caso exista interesse recíproco, gerar match.

### 12.8 Likes e revelação

Sem benefício adicional, o destinatário saberá que recebeu um like, mas não receberá informações suficientes para identificar quem enviou. Poderão ser exibidos atributos genéricos conforme a política de privacidade do produto.

A identidade de quem enviou o like poderá ser revelada por passes configurados para o evento. A política de visibilidade será aplicada no momento da consulta.

### 12.9 Passes e benefícios

O sistema suportará passes configuráveis. A administração da plataforma define as capacidades de benefício; a oferta específica é negociada/configurada para o evento; e o passe adquirido pertence ao participante.

Passes poderão ser baseados em tempo, quantidade ou combinação dos dois. Exemplos: acesso por um dia, dois dias, evento inteiro ou saldo de 5 revelações. Cada utilização será registrada para controle e auditoria.

### 12.10 Pagamentos e liberação

A oferta poderá utilizar três modelos comerciais: pagamento externo ao evento/estabelecimento com liberação administrativa; pagamento processado pela plataforma com eventual repasse ao evento; ou pagamento destinado diretamente à plataforma sem participação financeira do evento.

O contrato entre plataforma e organizador determina quais modalidades estarão disponíveis. Liberações manuais deverão registrar responsável, data/hora, passe, valor declarado e forma de pagamento.

### 12.11 Match e pós-match

O match ocorre quando existir interesse mútuo válido. O match libera todas as fotos adicionais dos participantes e a foto de outfit. Também será criada ou liberada uma Conversation. A conversa não terá limite de mensagens e não expirará automaticamente enquanto o relacionamento estiver ativo, observadas as regras de retenção.

### 12.12 Desfazer match

Desfazer match não apagará o relacionamento. O Match passará para estado encerrado, registrando responsável e data/hora. A conversa se tornará somente leitura: nenhuma das partes poderá enviar novas mensagens, mas ambas continuarão acessando o histórico.

A interface informará que o match foi desfeito. Fotos pós-match e outfit deixam de ser acessíveis após o encerramento.

### 12.13 Bloqueio no evento

O bloqueio é definitivo e irreversível dentro do evento em que foi realizado. Antes da confirmação, a interface deverá informar explicitamente essa irreversibilidade.

Após o bloqueio, os participantes deixam de visualizar os perfis um do outro, deixam de aparecer mutuamente na descoberta e não podem trocar likes, gerar novo match ou enviar mensagens.

O histórico da conversa continuará disponível, porém anonimizado na interface: nome, foto e elementos identificáveis deixam de ser exibidos e são substituídos por identificação neutra, como “Usuário bloqueado”. Internamente, vínculos necessários para moderação, auditoria e obrigações legais permanecem durante o período de retenção aplicável.

O bloqueio registra motivo e descrição e notifica a administração do evento/sala e a administração geral da plataforma.

### 12.14 Histórico de bloqueios entre eventos

O bloqueio não é automaticamente transportado para outro evento. Usuários que se bloquearam anteriormente podem voltar a se encontrar em evento futuro. A plataforma, entretanto, manterá o histórico de bloqueios anteriores.

O alerta não será exibido ao simplesmente visualizar o perfil nem ao escolher PASS. Se o usuário tentar dar LIKE em alguém que bloqueou anteriormente e cujo alerta ainda esteja ativo, será apresentada confirmação informando sobre o bloqueio anterior e perguntando se deseja prosseguir.

Se confirmar o LIKE, o bloqueio histórico permanece registrado para auditoria, mas o estado de alerta entre aquele par é encerrado para eventos futuros. O aviso somente voltará a existir se ocorrer novo bloqueio manual posterior. Se escolher PASS ou não confirmar, o estado de alerta permanece.

O alerta é unilateral: somente quem realizou o bloqueio anterior recebe essa informação.

### 12.15 Denúncias e moderação

Denúncia, bloqueio e punição serão conceitos separados. Report registra a alegação; ModerationCase representa a análise; ModerationAction registra decisões e providências. Uma denúncia não implica automaticamente constatação de infração.

Denúncias poderão possuir evidências e deverão notificar os responsáveis administrativos definidos. Suspensões e banimentos poderão existir nos níveis global, evento e sala.

### 12.16 Retenção, preservação e auditoria

A retenção será modelada por categoria de dado. O sistema não fixará um prazo jurídico arbitrário na arquitetura. DataRetentionRecord controlará arquivamento, previsão de eliminação, motivo e status. LegalHold impedirá a eliminação automática quando houver fundamento válido de preservação.

Ao final do prazo aplicável, ausente motivo legítimo de preservação, os dados correspondentes deverão ser eliminados definitivamente conforme a política do produto.

AuditLog será append-only e registrará ações administrativas e operações sensíveis, incluindo moderação, liberações de passes, alterações relevantes e eventos de segurança.

### 12.17 Decisões ainda pendentes

Permanecem para detalhamento posterior: catálogos definitivos dos campos de perfil; opções exatas dos hábitos configuráveis; regras detalhadas de campos personalizados; limites e políticas de anexos em mensagens; regras comerciais e fiscais de repasses; prazo jurídico definitivo de retenção; e estados/transições formais de cada entidade

### 12.15 Regras consolidadas de navegação, descoberta, fotos e presença geográfica

Roteamento e onboarding

A identidade permanece global e os papéis são contextuais ao evento. O roteamento deve priorizar administração global, papel administrativo no evento atual, participação existente e, por último, onboarding necessário. Após autenticação, navegação de retorno não deve levar ao login; login somente reaparece por logout explícito ou perda da autenticação. Onboarding concluído não deve ser retomado por Perfil ou Filtros. Alterações posteriores são operações de edição.

Descoberta e favoritos

As decisões de descoberta permanecem estritamente LIKE e PASS. Favorito não integra Interaction de descoberta e deve ser tratado como preferência pós-match vinculada ao contexto de conversa/match. O perfil de outro participante pode ser consultado durante a descoberta, inclusive pelo controle “i” do card. A autorização deve limitar o conteúdo conforme o relacionamento: fotos públicas antes do match; conteúdo pós-match somente com match ativo.

Imutabilidade das fotos públicas após ativação

A ativação do ParticipantProfile no evento exige três fotos públicas. Depois da ativação, essas três fotos obrigatórias não podem ser removidas. Fotos adicionais permanecem editáveis. A invariável deve ser aplicada no backend e não depender apenas de controles do frontend. O encerramento do match volta a impedir acesso às fotos pós-match e outfit, conforme a regra já existente.

Configuração geográfica do evento

Eventos presenciais devem admitir configuração posterior de imagem/logo, ponto geográfico de referência e raio de presença. O raio deve ser configurável. Eventos online não utilizam presença geográfica; eventos híbridos utilizam a regra apenas no componente presencial. Alterações de ponto ou raio durante evento em andamento devem gerar auditoria.

Estado de presença

O sistema deve distinguir atividade online de presença física. A geolocalização do Web App deve ser revalidada periodicamente e em momentos relevantes para classificar a presença dentro ou fora do perímetro, considerando indisponibilidade, permissão negada e precisão insuficiente. A implementação deve evitar interpretar uma leitura isolada e imprecisa como confirmação definitiva de saída.

A finalidade da geolocalização é validar presença no perímetro, não armazenar rastreamento contínuo de deslocamento. O princípio de minimização deve orientar a persistência dos dados de localização.

Sair do raio não suspende EventParticipant, não encerra sessão e não restringe Descoberta, LIKE, match ou mensagens. O estado presencial pode alternar durante o evento sem alterar o vínculo de participação. A API e o frontend devem representar separadamente, no mínimo, estado de atividade e estado de presença física.

Pendências deliberadas desta regra

Permanecem para definição posterior: periodicidade exata da revalidação; tolerância/precisão mínima; quantidade de confirmações para mudança de estado; raio padrão; cores definitivas dos indicadores; e política técnica exata de retenção de eventuais registros derivados de presença.

.

## Ciclo de vida do evento — arquivamento e exportação

- O evento passa automaticamente de Encerrado para Arquivado 15 dias após o encerramento.
- A transição para Arquivado dispara notificação para o Administrador Global e para o Administrador responsável pelo evento.
- Arquivado é um estado administrativo somente leitura: não reabre a experiência social nem permite alteração dos dados operacionais do evento.
- Na Administração Global, o evento deve disponibilizar uma ação de exportação dos dados do evento em arquivo ZIP.
- A exportação deverá ser preparada para consulta offline e conter um HTML navegável com os dados auditáveis do evento, incluindo os registros necessários para auditoria, revisão administrativa e eventual apresentação às autoridades competentes quando legalmente cabível.
- Esta exportação não deve ser tratada como substituta da base oficial, da trilha de auditoria ou de eventual LegalHold.
- O conteúdo exato do ZIP, estrutura do HTML, integridade/autenticidade, anexos/evidências, controle de acesso, registro da própria exportação e procedimento formal de fornecimento permanecem deliberadamente pendentes e serão especificados em etapa posterior.

## Consolidação funcional — decisões de 04/10/2026

### Identidade, navegação e onboarding

- A conta é global, mas papéis e autorizações são contextuais ao evento. A mesma pessoa pode administrar um evento e participar normalmente de outro.
- Depois da autenticação, voltar nunca deve retornar à tela de login. Login somente volta a ser exibido após logout ou término de sessão.
- O onboarding completo é executado na configuração inicial da participação. Editar Perfil ou Filtros posteriormente não reinicia o onboarding.
- Ao entrar em novo evento, reutilizam-se dados globais elegíveis e solicitam-se somente dados ausentes ou específicos daquele evento.

### Discovery, perfil, fotos e mensagens

- Discovery exibe somente as ações Passar e Like. Favoritar não existe antes do match.
- O botão informativo do Discovery expande o perfil e permite consultar as fotos públicas disponíveis antes do match.
- Após o match, as demais fotos permitidas pelas regras do perfil tornam-se visíveis.
- Favoritar é uma ação pós-match vinculada à conversa e ao perfil da pessoa, disponível no menu de contexto das mensagens/conversas.
- O mesmo menu oferece Ver perfil, e a conversa possui também ação visível para abrir o perfil do interlocutor.
- Após a ativação do perfil no evento, as três fotos públicas obrigatórias não podem ser removidas pelo participante. Fotos adicionais continuam gerenciáveis. Exceções administrativas/moderação ainda precisam ser definidas.

### Geolocalização e presença

- Eventos físicos/híbridos possuem ponto de referência, raio e frequência de validação configuráveis no cadastro/edição.
- A primeira validação ocorre na ativação; as seguintes respeitam a frequência configurada.
- Sair do raio não restringe o sistema. Afastamento progressivo é comportamento normal.
- Revogar/desligar intencionalmente a localização bloqueia Discovery e a navegação funcional da lista de participantes, mas mantém matches e mensagens existentes.
- Na lista de participantes sem localização ativa, pode permanecer uma visão visualmente desabilitada do último conteúdo carregado, sem exibir estados atuais de presença/localização.
- O princípio de reciprocidade se aplica aos indicadores: quem não disponibiliza sua localização não consulta o estado de localização dos demais, inclusive nos contextos de mensagens e lista de participantes.
- Falha técnica temporária recebe tolerância e retries mais frequentes; referência inicial: nova tentativa a cada 1 minuto. O limite total de tolerância/retries ainda será definido.
- Leituras abruptamente incompatíveis com tempo/distância podem gerar anomalia. Leitura isolada não confirma fraude; persistência muito distante após salto anômalo reforça o sinal.
- Anomalias relevantes são notificadas à administração do evento e à Administração Global para análise humana.
- Desfechos: Anomalia descartada; Tratado sem restrição; Banimento do evento.
- Banimento por esse motivo vale somente naquele evento e é reversível por gestor autorizado, preservando justificativas e auditoria.
- Não se exige rastreamento preciso dentro do evento. O objetivo é registrar presença dentro/fora do raio e dados mínimos necessários para detectar/analisar anomalias. Logs permanecem durante o evento e depois seguem a política de retenção aplicável.

### Ciclo de vida do evento

Estados: Rascunho → Agendado → Aberto → Em andamento ⇄ Pausado → Encerrado → Arquivado.

- Rascunho: edição livre dos dados do evento, inclusive raio, organização e responsável.
- Agendado: alterações passam a exigir restrições/confirmação explícita.
- Aberto: janela operacional anterior ao início, configurável por evento. Permite cadastro de participantes e validação de acessos/permissões da equipe. Dados do evento ficam congelados; correção de raio é exceção para Administrador Global ou Administrador responsável, sempre auditada.
- Antes do início, push e e-mail avisam Administrador Global e Administrador responsável de que o evento está prestes a começar. Qualquer um deles pode alterar Agendado → Aberto.
- Em andamento: inicia automaticamente no horário cadastrado e habilita a experiência social completa.
- Próximo ao fim, uma tarja informa ao participante o horário de encerramento.
- Pausado: somente gestores podem pausar/retomar. Discovery e lista de participantes ficam indisponíveis; mensagens existentes continuam funcionando. Tarja informa a pausa. Não são oferecidas opções de persistir/excluir perfil. Pausa não prorroga o horário final e todas as transições são auditadas.
- Se o horário final ocorrer durante a pausa, o evento é encerrado automaticamente.
- Encerrado: ocorre automaticamente no horário final ou pode ser antecipado por Administrador Global/Administrador responsável. Encerramento antecipado exige confirmação, justificativa, CAPTCHA simples e auditoria; ambos os gestores são notificados.
- No Encerrado, Discovery e filtros são desativados; lista deixa de mostrar estados dos participantes; mensagens tornam-se somente leitura; perfil torna-se somente leitura.
- No perfil encerrado, o participante pode optar por persistir/reaproveitar o perfil globalmente ou excluir sua exposição social. A exclusão remove o perfil do acesso dos demais e anonimiza sua representação nas mensagens, sem eliminar imediatamente registros sujeitos a retenção, auditoria ou LegalHold.
- Arquivado: ocorre automaticamente 15 dias após o encerramento e notifica ambos os gestores. É somente leitura e acessível administrativamente para métricas, relatórios, denúncias, auditoria e pontos de atenção.
- Administração Global deve permitir exportar o evento em ZIP com HTML navegável e dados auditáveis para consulta offline e eventual fornecimento formal quando legalmente cabível. Detalhes do pacote serão definidos posteriormente.

### Princípios de auditoria

- Alterações administrativas sensíveis, mudanças de estado, pausa/retomada, encerramento antecipado, ajustes excepcionais de raio, decisões de geolocalização, banimento/reativação e exportações devem ser auditáveis.
- Arquivamento não significa eliminação. Retenção, LegalHold e eliminação são processos próprios.

## Principais pontos ainda pendentes de revisão/definição

1. LGPD, retenção e eliminação: prazos jurídicos aplicáveis por categoria, anonimização versus exclusão, solicitações do titular, preservação judicial e retenção específica de localização.
2. Matriz definitiva de permissões: Administrador Global, Administrador do evento, Moderador e Operador, incluindo consulta de evidências, geolocalização, sanções, equipe, relatórios, QR e configurações.
3. Administração Global versus Django Admin: formalizar a divisão definitiva entre interface operacional de negócio e administração técnica/interna.
4. Passes, revelações, pagamentos e regras comerciais: tipos, preços, duração, consumo, expiração, estorno, cobrança, repasse e regras fiscais.
5. Notificações: matriz completa de eventos, destinatários e canais; antecedências configuráveis para início/fim e comportamento de falha/reenvio.
6. Geolocalização: duração/quantidade de retries, precisão mínima, algoritmo/limiares de anomalia e permissões para consulta dos sinais.
7. Perfil e fotos: exceções para substituição das três fotos públicas após ativação, especialmente moderação/conteúdo inadequado.
8. Bloqueio, denúncia e segurança entre eventos: catálogo definitivo de motivos, evidências automáticas, limiares de sinais e critérios para intervenção global.
9. Produção, segurança e operação: cloud, storage S3, autenticação definitiva, recuperação de senha, Google/Apple, API, CI/CD, observabilidade, backup/restore e infraestrutura de produção.
10. Exportação do evento arquivado: conteúdo exato do ZIP/HTML, anexos/evidências, integridade/autenticidade, controle de acesso, auditoria da exportação e procedimento formal de fornecimento.
11. Ciclo de vida: antecedência configurável das notificações/tarjas e eventual regra extraordinária de reabertura de evento já Encerrado.

## Administração Global e Django Admin

A Administração Global é a interface operacional principal do sistema. No menu Mais haverá Admin do sistema, direcionando ao Django Admin. O Django Admin será usado para manutenção avançada, exceções e alterações pontuais. Seu acesso exige permissão específica e não decorre automaticamente de papéis administrativos de evento. Alterações relevantes devem ser auditadas. Operações recorrentes ou relevantes ao negócio devem possuir fluxo próprio na Administração Global. A permissão específica do Django Admin será definida na matriz definitiva de permissões.

## Matriz de permissões — definição atual

Administrador Global corresponde ao usuário com Status de superusuário ativo no Django. O acesso ao Django Admin utiliza a flag Membro da equipe; essa flag não equivale a Administrador Global. Papéis administrativos de evento não concedem automaticamente essas flags globais.

Administrador do Evento pode gerenciar Moderadores e Operadores do próprio evento, conceder e revogar permissões operacionais, acessar métricas e relatórios. Pode delegar temporariamente a administração somente a um membro da Moderação e retomá-la depois. Delegação e retomada são auditadas e notificadas ao Administrador Global.

As permissões que o Administrador do Evento pode conceder se limitam às tratativas operacionais do evento: denúncias; bloqueios e desbloqueios; venda, concessão e revogação de passes; ativação e desativação de perfil; captura de foto de ativação; remoção de foto; e edição de bio quando necessária à tratativa. Não abrangem administração global nem funções técnicas.

Moderador possui praticamente o mesmo domínio operacional de tratativas do Administrador do Evento, conforme permissões recebidas, mas não gerencia equipe ou permissões e não acessa métricas nem relatórios. Pode receber temporariamente a administração do evento.

Operador é o principal responsável pela captura da foto de outfit e ativação operacional do perfil. Pode disponibilizar o QR Code do evento e abrir ocorrência administrativa ligada ao participante, como passe que não vigorou ou ajuda/falha ao editar o próprio perfil. Abrir ocorrência não concede automaticamente poderes de moderação.

Intervenções em foto, bio ou conteúdo do perfil precisam de origem justificável e auditável. Quando decorrerem de denúncia, devem ser vinculadas à denúncia. O participante também poderá solicitar suporte dentro da tela de Mensagens; intervenções decorrentes desse atendimento devem ser vinculadas à respectiva solicitação/conversa de suporte.

Mudanças de equipe, grupos, permissões, delegação e retomada, decisões de moderação e intervenções sobre perfil devem ser auditáveis.

## Passes e revelação de Likes

A tela Participantes inclui Likes recebidos ainda sem Match. Sem passe válido, as identidades ficam ocultas e a modalidade de aquisição segue a configuração do evento: balcão ou sistema.

O passe revela quem já deu Like e não cria Match. Pode funcionar por quantidade ou por tempo. Por quantidade, cada revelação consome uma unidade e segue ordem cronológica. Por tempo, a revelação vale durante a vigência e Likes posteriores à expiração ficam ocultos.

Likes não revelados permanecem registrados para passe posterior. Sem passe, saldo ou vigência, a interface mostra a quantidade oculta e a opção de adquirir novo passe. Venda, concessão e revogação manual seguem permissões da equipe e são auditáveis.

## Notificações

Participantes recebem notificações sempre dentro do sistema. O ícone de Mensagens também indica notificações não lidas e a tela permite alternar entre Mensagens e Notificações. Incluem Likes recebidos, Matches, suporte, passe expirado e avisos do evento.

O Moderador possui Avisos do Evento, em lista/cards. Um aviso pode ser rascunho, imediato ou agendado, com texto simples formatado e URL opcional aberta em nova aba.

Avisos podem ser criados/editados em Aberto, Em andamento e Pausado. Agendados disparam normalmente em Aberto/Em andamento. Em Pausado, não disparam automaticamente: geram alerta administrativo e podem ser enviados manualmente. Em Encerrado não podem ser enviados; pendências geram registro/notificação administrativa.

Não se agenda aviso após o encerramento previsto. Agendamentos nos 30 minutos finais exigem confirmação explícita. O estado do evento é sempre revalidado antes do disparo.

## Perfil, fotos e visibilidade

A ativação exige 3 fotos públicas válidas, que se tornam imutáveis para o participante após a ativação. A foto de outfit também é obrigatória e é adicionada pela equipe autorizada. Após o Match, as demais fotos são liberadas e a foto de outfit aparece primeiro, em destaque.

Se a moderação remover uma foto pública, o perfil é desativado até que o participante adicione uma substituta e obtenha nova validação. A reativação pode ser tratada presencialmente ou pelo Suporte, mantendo sempre o mínimo de 3 fotos públicas válidas e o vínculo auditável da intervenção.

Antes da abertura do evento, a organização pode configurar campos adicionais obrigatórios ou opcionais para ativação, incluindo aceite de termos próprios, consentimentos e listas de itens para marcação. Campos obrigatórios precisam ser satisfeitos para ativação; termos e consentimentos devem ser versionados e auditáveis.

## Denúncias e segurança entre eventos

Denúncias ficam disponíveis na Descoberta, perfil expandido e Mensagens, inclusive após anonimização. Exigem relato e podem apontar foto, mensagem ou foto já alterada; fotos substituídas permanecem no histórico para auditoria conforme retenção.

Motivos incluem assédio/ofensa, importunação sexual, conteúdo sexual explícito, racismo/discriminação, ódio, violência/ameaça, fraude, uso indevido de imagem/identidade, possível ilegalidade e Outro.

Bloqueios múltiplos não geram alerta. Com 10 denúncias válidas, a moderação do evento recebe alerta e acesso à fila filtrada pelo participante, podendo desativar o perfil para análise. Com 20 denúncias válidas, o perfil é desativado automaticamente para análise e a Administração Global é notificada. Denúncias consideradas infundadas não contam.

O histórico fica ligado ao perfil global. A Administração Global pode marcá-lo como Denunciado recorrente. Ao ingressar em novo evento, a Administração Global é notificada e decide se informa a administração local; não há banimento automático entre eventos.

## LGPD, retenção e eliminação

As regras detalhadas de categorias de dados, temporalidade, anonimização, exclusão, direitos do titular e preservação judicial estão centralizadas no documento **LGPD - Retenção, Eliminação e Direitos do Titular**. Não existe prazo único para todos os dados: cada categoria deve seguir finalidade, base legal e matriz de retenção próprias. Os 15 dias para arquivamento do evento são regra operacional, não prazo jurídico. O projeto deve aplicar ConsentRecord, DataRetentionRecord, LegalHold, PrivacyRequest e AuditLog conforme essa política. Antes da produção, os prazos específicos ainda não fixados devem passar por validação jurídica.

Documento: https://docs.google.com/document/d/1iVfUgkg_0EBERID5z9ZA-WnRu9e6bIDECgBTFW0pmM0/edit

## Geolocalização - definição consolidada

O evento define a frequência normal de verificação de localização. O raio do evento tem padrão de 1.000 metros e determina presença atual. O limite adicional também tem padrão de 1.000 metros, é informado no cadastro do evento e pode ser alterado somente antes de o evento entrar em andamento. Dentro do raio, o participante está presente; fora do raio e dentro do limite máximo, esteve no evento e pode retornar; além do limite máximo, entra em zona de possível anomalia.

Se uma verificação periódica falhar, ocorrem mais 5 tentativas, com intervalo de 1 minuto. Persistindo a falha, são exibidas tarja e notificação fixa que permite forçar nova tentativa. Se houver sucesso, os avisos desaparecem e o fluxo normal retorna. Se a próxima verificação periódica agendada também falhar, o perfil é desativado por motivo técnico e o participante é orientado a procurar a moderação. Mesmo desativado, a tentativa manual permanece disponível. O Moderador pode reativar o perfil e conceder exceção para ignorar a verificação por X minutos, com duração, motivo, responsável e expiração auditados. A exceção não é fraude, punição, denúncia ou bloqueio.

A anomalia de deslocamento possui dois critérios: velocidade média estimada superior a 60 km/h entre duas medições válidas consecutivas; ou duas medições válidas além do limite máximo, correspondente ao raio do evento somado ao limite adicional. Anomalia é sinal para investigação e não gera punição automática.

Dados e histórico individual de localização somente podem ser consultados pelo Administrador Global e pelo Administrador/Gestor responsável pelo evento. A consulta não é permitida nos estados Aberto e Em andamento. É permitida com o evento Pausado para investigação e após Encerramento/Arquivamento enquanto os dados estiverem legitimamente conservados. Toda consulta é auditada.

### Pendência LGPD para lançamento

O prazo de retenção dos dados de geolocalização permanece sem definição definitiva. Antes do lançamento em produção, deverá ser validado na matriz LGPD por categoria, incluindo finalidade, base legal, início da contagem, prazo, destino final, eliminação ou anonimização e exceções por Legal Hold. O histórico para investigação não autoriza retenção indefinida.

## Ciclo de vida do evento - consolidação

Estados: Rascunho → Agendado → Aberto → Em andamento ⇄ Pausado → Encerrado → Arquivado.

O Administrador Global define início, término e Administrador responsável. Esses campos só podem ser alterados antes de o evento ficar Aberto. O raio de presença e o limite adicional de anomalia podem ser alterados pelo Administrador Global ou pelo Administrador do Evento até antes de Em andamento.

O evento pode ser aberto manualmente a partir de 2 horas antes do início. Se ainda estiver Agendado, 5 minutos antes do início o sistema muda automaticamente para Aberto e notifica Gestão Global e Gestão do Evento. A origem da abertura, manual ou automática, fica registrada.

Se a abertura foi manual, no horário previsto ocorre automaticamente Aberto → Em andamento. Se a abertura foi automática, o início automático ocorre 10 minutos após o horário originalmente previsto. As transições automáticas são notificadas às duas gestões e auditadas.

A forma de pagamento dos passes é definida pelo Administrador Global até o início do evento. Os tipos de passes podem ser editados pelo Administrador do Evento enquanto o evento estiver Aberto e ficam bloqueados em Em andamento. Um passe pode ser por quantidade ou por tempo e pode ser pago ou gratuito, inclusive como brinde/cortesia.

A pausa não amplia a duração. Se o horário final chegar durante Pausado, o evento é encerrado automaticamente. Faltando 15 minutos para o término programado, é exibida aos participantes uma tarja persistente de encerramento próximo, inclusive se o evento estiver Pausado.

O encerramento ocorre automaticamente no horário previsto, salvo encerramento antecipado. O encerramento antecipado exige CAPTCHA e justificativa descritiva obrigatória, com responsável, justificativa e ação registrados em auditoria e notificação à Gestão Global e à Gestão do Evento.

Exatamente 15 dias após o encerramento, o evento passa automaticamente para Arquivado. Esse prazo é operacional e não representa prazo legal de retenção nem eliminação automática de dados.

## Exportação auditável do evento

A exportação auditável é destinada a atendimento formal, normalmente relacionado a ordem judicial ou solicitação de autoridade competente. A solicitação deve chegar formalmente ao suporte do sistema por e-mail e não dispara exportação automática.

Somente o Administrador Global do sistema, correspondente ao superuser, pode gerar, baixar e assinar a exportação. Administradores de Evento, Moderadores e Operadores não possuem essa permissão. O Administrador Global é também responsável pelo encaminhamento do material à autoridade competente.

### Escopo da exportação

No momento da geração, o Administrador Global escolhe entre fotografia completa de tudo que ainda esteja legalmente disponível para o evento ou exportação personalizada por módulos, conforme o escopo da solicitação. Entre os módulos selecionáveis podem estar participantes, moderação, auditoria, geolocalização, mensagens e outras categorias existentes. A exportação deve respeitar minimização, retenção LGPD e eventual Legal Hold. Os logs relacionados ao evento integram obrigatoriamente o arquivo auditável.

### Conteúdo do pacote

O pacote principal é um ZIP contendo um dump SQL restrito ao evento, com os dados selecionados e a estrutura necessária do banco para sua consulta ou restauração, sem incluir dados estranhos ao evento. O dump deve conter todos os logs do sistema relacionados ao evento.

O ZIP também contém uma SPA auditável, cópia fiel da experiência administrativa do evento, alimentada por dados estáticos/mockados da exportação. Ela deve reproduzir as telas, relações, históricos, filtros e navegação aplicáveis que o gestor teria no sistema original, mas funciona exclusivamente em modo de leitura: não edita dados, não executa ações administrativas, não cria registros, não gera novos logs e não se comunica com o ambiente de produção.

O pacote inclui manifesto interno com identificação da exportação, evento, data/hora, versão do sistema, modalidade completa ou personalizada, módulos incluídos/excluídos e hashes dos componentes internos, incluindo SQL, SPA, mídias e evidências quando existentes no escopo.

### Integridade e assinatura

Depois de concluído e congelado o ZIP, o sistema calcula o hash criptográfico do arquivo final. O algoritmo de referência definido para o produto é SHA-256. O sistema gera separadamente um Termo de Exportação e Integridade em PDF contendo, no mínimo: identificação única da exportação; evento e organização; início e encerramento do evento; data/hora da geração; solicitante/responsável; versão do sistema; modalidade e módulos exportados; resumo dos registros; identificação do dump SQL e da SPA; algoritmo utilizado; hash integral do ZIP; informação sobre dados eventualmente já eliminados ou anonimizados; eventual Legal Hold pertinente; e declaração de que a SPA é somente leitura.

O PDF fica externo ao ZIP para evitar dependência circular entre o hash do pacote e o próprio termo. O conjunto entregue é, portanto, o ZIP do evento e o respectivo Termo de Exportação e Integridade. O termo pode ser assinado eletronicamente pelo responsável, incluindo assinatura GOV.BR quando aplicável, mantendo a arquitetura preparada para outros mecanismos formais de assinatura digital quando necessários.

### Auditoria do procedimento

A geração da exportação é auditada. O registro deve identificar o superuser responsável, evento, data/hora, referência da solicitação ou ordem judicial, escopo solicitado, módulos efetivamente exportados, hash gerado, geração e assinatura do termo, download e registro do encaminhamento. Quando houver Legal Hold relacionado, ele deve ser associado ao procedimento. A exportação deve limitar-se ao escopo legitimamente solicitado e aos dados ainda legalmente disponíveis.

## Passes e pagamentos - escopo técnico-financeiro atual

O produto não terá, nesta versão, integração com plataforma de pagamento nem validação automática de recebimento. Não haverá gateway, PIX integrado, cartão ou confirmação financeira externa.

O fluxo operacional é: Participante solicita passe → Operador autorizado localiza o participante → seleciona o passe → concede o passe → sistema registra a concessão → passe fica disponível ao participante.

Somente Operadores com permissão específica de venda/concessão de passes podem executar a operação. Cada concessão deve registrar, para auditoria, operador, participante, evento, tipo de passe, data/hora e origem da operação.

Os passes podem ser por quantidade de revelações ou por tempo de validade. Cada tipo pode possuir valor monetário ou ser gratuito, inclusive como brinde/cortesia do evento. Se gratuito, a concessão é registrada sem valor financeiro. Se houver valor monetário configurado, a concessão é computada como venda no relatório financeiro pelo valor definido para o passe. Esse registro representa a operação declarada no sistema e não comprova o efetivo recebimento do dinheiro.

O relatório financeiro deve permitir identificar quantidade de passes concedidos/vendidos, tipo de passe, valor unitário configurado, valor total computado, operador responsável e data/hora. Passes gratuitos devem ser identificados separadamente ou com valor zero.

A revogação de um passe nunca apaga nem altera o lançamento original. Para passe com valor monetário, o valor permanece computado no relatório financeiro como venda registrada e a revogação aparece como evento posterior. A revogação deve registrar operador responsável, data/hora e motivo, preservando a trilha auditável.

### Evolução futura

Ficam explicitamente fora do escopo atual e anotados para implementação futura: integração com plataformas de pagamento; PIX e cartões; confirmação automática de pagamento; estados financeiros completos; conciliação; estorno e reembolso; idempotência de transações financeiras; tratamento de falhas de provedores; comprovantes; regras fiscais e tributárias; integração contábil; e demais mecanismos de processamento financeiro externo. A implementação futura não deve descaracterizar o histórico auditável das concessões, vendas e revogações.

## Produção e segurança - estágio MVP

O projeto permanece em fase de estruturação e validação de MVP. Nesta etapa, o sistema poderá executar em VPS ou homelab, mantendo aplicação, banco de dados, Redis, arquivos e mídias armazenados localmente na infraestrutura utilizada. A arquitetura atual deve ser tratada como ambiente de desenvolvimento, demonstração e validação, e não como arquitetura definitiva aprovada para produção.

Durante o MVP não é requisito definir armazenamento externo S3/MinIO ou equivalente, alta disponibilidade, escalabilidade horizontal, infraestrutura definitiva de produção ou arquitetura de recuperação de desastre. Essas decisões ficam deliberadamente adiadas para a preparação do lançamento.

Dados reais de participantes não devem ser utilizados para validação do MVP em ambiente de desenvolvimento/homelab. Até a preparação da infraestrutura de produção, os ambientes de validação devem utilizar dados fictícios ou mockados.

### Pendências obrigatórias antes do lançamento

Antes de disponibilizar o sistema para uso real, deverão ser definidos, implementados e validados: armazenamento definitivo de mídias e evidências; backups, restauração e testes de recuperação; criptografia e proteção de dados; gestão de secrets e credenciais; TLS, domínios, rede e firewall; segregação de ambientes; controle e revisão de acessos privilegiados; hardening de containers e servidores; atualização e gestão de vulnerabilidades; observabilidade, logs e alertas; disponibilidade e recuperação de desastre; processamento assíncrono e rotinas agendadas; retenção e eliminação de dados também em backups; proteção dos dumps e pacotes de exportação auditável; resposta a incidentes; e revisão final de segurança e LGPD.

Status deste tópico: requisitos mapeados, com implementação diferida para a preparação do lançamento. A definição de provedor, cloud, storage, backup, alta disponibilidade e demais componentes de produção não faz parte do fechamento estrutural do MVP.
