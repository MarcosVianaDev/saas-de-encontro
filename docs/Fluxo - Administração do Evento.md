# Fluxo de Administração do Evento

> Documento de requisitos consolidado em 04/10/2026. Não é uma declaração de funcionalidades já implementadas; consulte [Verificação da implementação](<Verificacao da implementacao.md>). O texto preserva a evolução da fonte: as seções finais de definição/consolidação prevalecem sobre propostas anteriores do mesmo assunto. Consulte o [índice e análise](README.md) para divergências e precedência.

> Referência funcional preservada do DOCX. Cobertura implementada e limites atualizados em 04/10/2026: [Administração e ingresso](<Administracao e ingresso no evento.md>).

Fonte: [DOCX](<Fluxo - Administração do Evento.md.docx>). Referência visual: [screen1.png](<Imagens - Telas e Protótipos/screen1.png>). Guia: [Telas administrativas](<Telas administrativas.md>).

## 1. Objetivo

Este documento define o fluxo funcional e a estrutura inicial das telas destinadas ao administrador de um evento e aos funcionários vinculados a ele.

A experiência é mobile-first e utiliza a mesma autenticação da área de participantes. Não existe um login administrativo separado.

## 2. Autenticação e direcionamento

A tela de login é compartilhada por todos os usuários.

Após a autenticação, o backend identifica:
- a conta autenticada;
- os vínculos da conta com eventos;
- o papel exercido no evento;
- as permissões associadas ao papel.

Quando o usuário possui vínculo administrativo com o evento, a navegação é direcionada para o Dashboard administrativo daquele evento.

Uma mesma conta poderá futuramente exercer papéis diferentes em eventos diferentes, por exemplo administrador em um evento e participante em outro.

A autorização deve ser validada no backend. A interface não deve ser a única responsável por restringir ações administrativas.

## 3. Escopo administrativo

A administração do evento é diferente da administração global da plataforma.

O administrador e os funcionários do evento atuam somente dentro dos eventos aos quais possuem vínculo e conforme suas permissões.

Configurações estruturais do SaaS, decisões globais, políticas gerais e administração entre eventos permanecem sob responsabilidade da administração global.

## 4. Navegação inferior

A navegação administrativa mobile terá inicialmente cinco áreas principais:

1. Dashboard
2. Participantes
3. Moderação
4. Evento
5. Mais

O item Moderação poderá exibir um badge com a quantidade de ocorrências pendentes.

A área Mais poderá concentrar:
- Equipe;
- Relatórios;
- configurações permitidas;
- conta do usuário.

## 5. Tela Evento

A tela Evento apresenta informações definidas pelo sistema geral.

Campos previstos:
- nome do evento;
- UUID do evento;
- data e hora de início;
- data e hora de término;
- responsável;
- status do evento.

Esses dados devem ser somente leitura quando sua definição pertencer à administração geral.

### 5.1 Status

Estados conceituais iniciais:
- Agendado;
- Em andamento;
- Encerrado.

### 5.2 QR Code de acesso

A tela terá um botão para exibir o QR Code de acesso ao evento.

O QR Code será utilizado por participantes comuns para iniciar o ingresso/cadastro vinculado ao evento, funcionando como mecanismo de associação do usuário ao contexto daquele evento.

O QR Code não deve depender da exposição direta do UUID como mecanismo de ingresso. A implementação deverá utilizar uma referência ou token seguro associado ao evento.

A interface poderá permitir:
- exibir o QR Code em tela cheia;
- compartilhar o acesso;
- utilizar o QR Code em materiais ou telas do evento.

Quando o evento estiver encerrado, novos ingressos por esse QR Code devem deixar de ser aceitos.

## 6. Dashboard administrativo

O Dashboard é a tela inicial do administrador ou funcionário após o login e identificação do vínculo administrativo.

Seu objetivo principal é responder:

> O que está acontecendo no evento agora e o que exige atenção?

O Dashboard deve ser operacional, evitando inicialmente gráficos complexos ou excesso de informações.

### 6.1 Cabeçalho

Exibir:
- nome do evento;
- status;
- horário de início e término;
- ação Ver evento.

Exemplo conceitual:

Evento Conexões 2026  
Em andamento  
18:00 — 23:00  
Ver evento

Caso futuramente um administrador gerencie vários eventos, poderá existir um seletor de evento nesse cabeçalho.

### 6.2 Indicadores principais

Cards compactos:

#### Participantes
Quantidade de contas/participações vinculadas ao evento.

#### Ativos agora
Quantidade de participantes com atividade recente, conforme critério operacional a ser definido.

#### Matches
Quantidade de matches produzidos no evento.

#### Conversas
Quantidade de conversas iniciadas no evento.

Participantes e Ativos devem ter prioridade visual por representarem a situação operacional do evento.

### 6.3 Requer atenção

Quando existirem ocorrências relevantes, o Dashboard deverá apresentar uma seção destacada Requer atenção.

Exemplos:
- denúncias pendentes;
- denúncias em análise;
- situações com múltiplos bloqueios ou outros indicadores de moderação.

A seção terá acesso direto a Ver moderação.

Quando não houver pendências, poderá exibir:

Nenhuma ocorrência pendente.

Uma denúncia ou bloqueio não representa automaticamente punição administrativa.

### 6.4 Atividade do evento

Apresentar inicialmente indicadores simples de atividade recente, sem gráficos complexos.

Exemplos:
- novos participantes na última hora;
- novos matches na última hora;
- novas conversas iniciadas na última hora.

O intervalo e os critérios definitivos poderão ser ajustados posteriormente.

### 6.5 Resumo de participantes

Exibir:
- total de participantes cadastrados;
- participantes ativos recentemente;
- participantes inativos;
- novos cadastros recentes.

A ação Ver participantes direciona para a tela administrativa de participantes.

### 6.6 Segurança

Resumo acumulado de segurança e moderação.

Exemplos:
- total de denúncias;
- denúncias pendentes;
- denúncias em análise;
- denúncias resolvidas;
- quantidade de bloqueios entre participantes.

Bloqueios entre participantes são indicadores comportamentais e não devem ser tratados automaticamente como sanção administrativa.

### 6.7 QR Code como ação rápida

Durante eventos agendados ou em andamento, o Dashboard também poderá oferecer acesso rápido:

Exibir QR Code

O objetivo é evitar que funcionários precisem navegar até a tela Evento sempre que precisarem apresentar o código aos participantes.

Após o encerramento do evento, essa ação deve ser removida ou desabilitada.

### 6.8 Equipe

Seção prevista para evolução do Dashboard:

- quantidade de funcionários ativos;
- nome;
- papel administrativo;
- acesso para Ver equipe.

Não é requisito obrigatório da primeira versão do Dashboard, mas a estrutura deve permitir sua inclusão.

## 7. Estados do Dashboard

O conteúdo do Dashboard muda de acordo com o ciclo de vida do evento.

### 7.1 Antes do evento

Priorizar:
- contagem regressiva ou informação de início;
- participantes já cadastrados;
- equipe;
- QR Code;
- preparação operacional.

Métricas de atividade sem dados não precisam ocupar espaço.

### 7.2 Durante o evento

Priorizar:
- participantes;
- ativos;
- matches;
- conversas;
- Requer atenção;
- atividade recente;
- segurança;
- acesso rápido ao QR Code.

Este é o estado operacional principal.

### 7.3 Depois do evento

O Dashboard assume caráter de consolidação.

Exibir:
- Evento encerrado;
- total de participantes;
- matches;
- conversas;
- denúncias;
- bloqueios;
- acesso ao relatório final.

O QR Code deixa de aceitar novos participantes.

Dados pessoais e operacionais passam a seguir o ciclo de retenção, arquivamento, LegalHold quando aplicável e posterior eliminação conforme a política e o prazo legal aplicável definidos pelo projeto.

## 8. Participantes

Tela administrativa prevista para:
- pesquisar participantes;
- filtrar participantes;
- visualizar situação no evento;
- acessar ficha administrativa do participante.

A ficha administrativa é diferente do perfil social exibido entre participantes.

Ela poderá apresentar dados básicos permitidos, situação no evento e informações de moderação autorizadas.

O organizador não deve obter acesso irrestrito às conversas privadas dos participantes. Moderação deve operar sobre ocorrências e evidências previstas pelo sistema.

## 9. Moderação

Área própria destinada a denúncias, bloqueios e ocorrências.

Estados iniciais:
- Pendentes;
- Em análise;
- Resolvidas.

Cada ocorrência poderá apresentar:
- denunciante;
- denunciado;
- motivo;
- descrição do ocorrido;
- data e hora;
- status;
- histórico das ações administrativas.

Denúncias devem ser notificadas ao responsável administrativo do evento e à administração global, conforme o escopo geral.

## 10. Bloqueios e sanções

Bloqueio entre participantes e sanção administrativa são conceitos independentes.

Um bloqueio realizado por um participante:
- afeta a relação entre aqueles participantes conforme as regras do evento;
- pode gerar indicador de segurança/moderação;
- não deve automaticamente expulsar ou suspender o usuário bloqueado.

Sanções administrativas dependem das permissões e regras específicas de moderação.

## 11. Equipe e permissões

A estrutura deverá permitir diferentes papéis administrativos.

Papéis conceituais iniciais:

### Administrador do evento
Acesso amplo às funções administrativas permitidas para aquele evento.

### Moderador
Acesso principalmente a participantes, denúncias, bloqueios e moderação.

### Operador / Funcionário
Acesso às funções operacionais necessárias ao atendimento do evento.

As permissões definitivas de cada papel deverão ser detalhadas antes da implementação correspondente.

A administração global da plataforma permanece um nível separado.

## 12. Relatório do evento

Área prevista para consolidação de resultados.

Durante o evento, poderá apresentar dados parciais.

Depois do encerramento, passa a funcionar como relatório final.

Indicadores previstos:
- total de participantes;
- adesão/atividade;
- interações;
- matches;
- conversas;
- denúncias;
- bloqueios;
- motivos de denúncias;
- períodos de maior atividade;
- outros indicadores consolidados permitidos pela política de dados.

## 13. Estrutura visual inicial do Dashboard

Representação conceitual mobile:

    ┌──────────────────────────────┐
    │ Evento Conexões 2026         │
    │ ● Em andamento     Ver evento│
    │ 18:00 — 23:00                │
    │                              │
    │ PARTICIPANTES     ATIVOS     │
    │     284             173      │
    │                              │
    │ MATCHES          CONVERSAS   │
    │      96              71      │
    │                              │
    │ ┌──────────────────────────┐ │
    │ │ Requer atenção        3  │ │
    │ │ 2 denúncias pendentes   │ │
    │ │ 1 alerta de bloqueios   │ │
    │ │        Ver moderação →  │ │
    │ └──────────────────────────┘ │
    │                              │
    │ Atividade                    │
    │ +42 participantes   última h │
    │ +18 matches         última h │
    │ +11 conversas       última h │
    │                              │
    │ Segurança                    │
    │ 4 denúncias • 12 bloqueios   │
    │                              │
    │ ┌──────────────────────────┐ │
    │ │      Exibir QR Code      │ │
    │ └──────────────────────────┘ │
    │                              │
    ├──────────────────────────────┤
    │ Início Pessoas Mod. Evento   │
    │                       Mais   │
    └──────────────────────────────┘

## 14. Diretrizes de UX

- Mobile-first.
- Manter a identidade visual lilás/roxa definida para a experiência do participante.
- Diferenciar claramente o modo administrativo por navegação e densidade de informação.
- Priorizar informações acionáveis.
- Não sobrecarregar o MVP com gráficos complexos.
- Ações críticas devem respeitar permissões verificadas pelo backend.
- Pendências de moderação devem permanecer visíveis e fáceis de acessar.
- Estados antes, durante e depois do evento devem alterar a prioridade das informações.

## 15. Próximas telas a detalhar

A especificação deverá ser expandida, na sequência, para:

1. Participantes;
2. ficha administrativa do participante;
3. Moderação;
4. detalhes de uma denúncia/ocorrência;
5. Evento e QR Code;
6. Equipe e permissões;
7. Relatório final;
8. área Mais/configurações permitidas.

Este documento deve permanecer como referência funcional para o desenvolvimento das telas administrativas do evento.

## Arquivamento automático e exportação

O evento é arquivado automaticamente 15 dias após seu encerramento. A mudança notifica o Administrador Global e o Administrador responsável pelo evento. O estado Arquivado é somente leitura.

Na Administração Global, o evento arquivado deve oferecer uma ação para exportar seus dados em arquivo ZIP. A exportação será destinada à consulta offline e deverá conter um HTML navegável com os dados auditáveis do evento. Poderá ser utilizada para auditoria, revisão administrativa e, quando legalmente cabível, fornecimento às autoridades competentes.

Lembrete para detalhamento posterior: definir conteúdo do ZIP, estrutura do HTML, anexos e evidências incluídos, mecanismos de integridade e autenticidade, controle de acesso, auditoria da própria exportação e procedimento formal de fornecimento. A exportação não substitui a base oficial, a trilha de auditoria nem eventual LegalHold.

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

## Matriz de permissões — definição atual

Administrador Global é o usuário com Status de superusuário ativo no Django. O acesso ao Django Admin usa a flag Membro da equipe; essa flag não equivale a Administrador Global. Papéis do evento não concedem automaticamente essas flags globais.

Administrador do Evento pode gerenciar Moderadores e Operadores do próprio evento, conceder ou revogar permissões operacionais, acessar métricas e relatórios e delegar temporariamente a administração somente a um Moderador, podendo retomá-la depois. Delegação e retomada são auditadas e notificadas ao Administrador Global.

As permissões delegáveis se limitam a tratativas do evento: denúncias, bloqueios e desbloqueios; venda, concessão e revogação de passes; ativação/desativação de perfil; captura de foto de ativação; remoção de foto; e edição de bio quando necessária à tratativa. Não abrangem administração global ou funções técnicas.

Moderador possui praticamente o mesmo domínio operacional de tratativas do Administrador do Evento, conforme permissões recebidas, mas não altera equipe/permissões e não acessa métricas ou relatórios. Pode receber a administração temporária.

Operador é o principal responsável pela captura da foto de outfit e ativação operacional do perfil, pode disponibilizar o QR Code do evento e abrir ocorrência administrativa ligada ao participante, como passe que não vigorou ou ajuda/falha ao editar o próprio perfil. Abrir ocorrência não concede poderes de moderação.

Intervenções em foto, bio ou conteúdo do perfil precisam de origem auditável. Quando decorrentes de denúncia, devem ser vinculadas à denúncia. O participante também poderá solicitar suporte dentro da tela de Mensagens; intervenções decorrentes desse atendimento devem ser vinculadas à solicitação/conversa de suporte.

Mudanças de equipe, grupos, permissões, delegação/retomada, decisões de moderação e intervenções sobre perfil devem ser auditáveis.

## Passes e revelação de Likes recebidos

Na tela Participantes deve existir, além do filtro de Matches, o filtro Likes recebidos. Ele reúne Likes recebidos que ainda não resultaram em Match.

Sem passe válido, o filtro permanece visível, mas o conteúdo fica bloqueado. Ao acioná-lo, um popup informa que a revelação é paga e apresenta as instruções definidas pela organização do evento. O evento pode operar com pagamento e ativação em balcão de atendimento ou com pagamento pelo próprio sistema.

Com passe válido, o participante pode revelar quem já lhe deu Like. Se der Like de volta, ocorre o Match normal. O passe concede somente o direito de revelação; não cria Match nem altera a decisão de outro participante.

Passes podem ser definidos por quantidade de revelações ou por tempo. No passe por quantidade, as revelações são consumidas individualmente e obedecem à ordem cronológica dos Likes recebidos, do mais antigo para o mais recente. Exemplo: um passe de 10 revelações revela no máximo os 10 primeiros Likes elegíveis.

No passe por tempo, Likes elegíveis podem ser revelados durante a vigência. Likes que permanecerem ocultos ou forem recebidos após a expiração não são revelados sem novo passe.

Likes não revelados não são descartados quando o passe termina. Permanecem registrados e podem ser revelados por um passe posterior, preservando a ordem cronológica dos Likes ainda ocultos.

Quando não houver saldo ou vigência suficiente, a interface não mostra a identidade dos Likes ocultos. Exibe somente a quantidade de Likes ocultos, uma mensagem explicativa e o botão Adquirir novo passe.

A concessão, venda e revogação manual de passes integra as permissões operacionais já definidas para a equipe do evento e deve ser auditável.

## Notificações

Participantes recebem notificações dentro do sistema, usando o mesmo ícone de Mensagens. A tela alterna Mensagens e Notificações, incluindo Likes, Matches, suporte, passe expirado e avisos do evento.

O Moderador possui Avisos do Evento em lista/cards: rascunho, envio imediato ou agendado, texto com formatação simples e URL opcional em nova aba. Podem ser criados/editados em Aberto, Em andamento e Pausado. Agendados enviam em Aberto/Em andamento; em Pausado geram alerta administrativo e admitem envio manual; em Encerrado não podem ser enviados.

Não é permitido agendar após o encerramento previsto. Agendamento nos 30 minutos finais exige confirmação. O estado do evento é revalidado no disparo.

## Perfil, fotos e visibilidade

A ativação exige três fotos públicas válidas e foto de outfit adicionada pela equipe. Após o Match, as demais fotos são liberadas. Se uma foto pública for removida administrativamente, o perfil fica desativado até reposição e nova validação.

Antes da abertura, a organização pode definir campos adicionais obrigatórios ou opcionais para ativação, incluindo termos, consentimentos e listas de marcação.

## LGPD, retenção e eliminação

As regras detalhadas de categorias de dados, temporalidade, anonimização, exclusão, direitos do titular e preservação judicial estão centralizadas no documento **LGPD - Retenção, Eliminação e Direitos do Titular**. Não existe prazo único para todos os dados: cada categoria deve seguir finalidade, base legal e matriz de retenção próprias. Os 15 dias para arquivamento do evento são regra operacional, não prazo jurídico. O projeto deve aplicar ConsentRecord, DataRetentionRecord, LegalHold, PrivacyRequest e AuditLog conforme essa política. Antes da produção, os prazos específicos ainda não fixados devem passar por validação jurídica.

Documento: https://docs.google.com/document/d/1iVfUgkg_0EBERID5z9ZA-WnRu9e6bIDECgBTFW0pmM0/edit

## Geolocalização - regras consolidadas

A geolocalização é usada para validar presença, apoiar a experiência do evento e gerar sinais de segurança, sem rastreamento exato contínuo e sem punição automática por anomalia.

O evento define a frequência normal das verificações. O raio do evento possui valor padrão de 1.000 metros e determina presença atual. Há também um limite adicional, igualmente com padrão de 1.000 metros, informado no cadastro do evento e alterável somente até antes de o evento entrar em andamento. Assim, dentro do raio o participante é considerado presente; fora do raio, mas dentro do limite máximo, considera-se que esteve no evento e pode retornar, sem caracterizar anomalia; além do limite máximo entra-se na zona de possível anomalia.

Quando uma verificação periódica falhar, o sistema realiza mais 5 tentativas, com intervalo de 1 minuto. Se todas falharem, o participante recebe tarja persistente de falha no GPS e notificação fixa acionável que força nova tentativa. Se uma tentativa manual obtiver localização válida, tarja e notificação desaparecem e o fluxo normal é retomado. Se o problema persistir e a próxima verificação periódica agendada também não conseguir determinar a localização, o perfil é desativado por falha técnica e o participante é orientado a comparecer à moderação.

Mesmo com o perfil desativado por falha técnica de GPS, a notificação de nova tentativa continua disponível para autorregularização. Obtida uma leitura válida, o perfil pode ser reativado e o fluxo normal retomado. Se o problema persistir, o Moderador pode reativar o perfil concedendo exceção temporária para ignorar a verificação de localização por X minutos. A duração é definida na intervenção. A operação registra participante, responsável, data/hora, duração, motivo e expiração. Durante a exceção, a tentativa manual permanece disponível. Ao expirar, sem localização válida, voltam a valer as regras normais de verificação. Essa situação é técnica e não constitui fraude, denúncia, bloqueio ou infração.

A detecção de movimentação anômala utiliza dois critérios complementares. Primeiro, entre duas medições válidas consecutivas, calcula-se a velocidade média estimada pela distância percorrida e pelo tempo transcorrido; deslocamentos que exijam velocidade média superior a 60 km/h geram sinal de anomalia. Segundo, duas medições válidas além do limite máximo definido pelo raio do evento mais o limite adicional caracterizam movimentação anômala. Uma anomalia é sinal para investigação, não prova automática de fraude nem punição automática.

O histórico e os dados individuais de localização somente podem ser consultados pelo Administrador Global e pelo Administrador/Gestor responsável pelo evento. Moderadores, Operadores e participantes não acessam esse histórico. A consulta é bloqueada durante os estados Aberto e Em andamento. É permitida quando o evento estiver Pausado, para possível investigação, e após o Encerramento/Arquivamento enquanto os dados ainda estiverem legitimamente conservados. Alertas podem ser gerados durante o evento, mas a investigação do histórico exige pausa ou encerramento. Toda consulta deve ser auditada.

### LGPD - pendência para lançamento

O prazo de retenção dos dados de geolocalização permanece deliberadamente sem definição definitiva. Antes do lançamento em produção, a categoria deve ser incluída na matriz final de retenção LGPD, com finalidade, base legal, início da contagem, prazo, destino final, regras de eliminação/anonymização e exceções por Legal Hold devidamente validados. A existência do histórico para investigação não autoriza conservação indefinida.

## Ciclo de vida do evento - consolidação

Estados: Rascunho → Agendado → Aberto → Em andamento ⇄ Pausado → Encerrado → Arquivado.

O Administrador Global define início, término e Administrador responsável. Esses campos só podem ser alterados antes de o evento ficar Aberto. O raio de presença e o limite adicional de anomalia podem ser alterados pelo Administrador Global ou pelo Administrador do Evento até antes de Em andamento.

O evento pode ser aberto manualmente a partir de 2 horas antes do início. Se ainda estiver Agendado, 5 minutos antes do início o sistema muda automaticamente para Aberto e notifica Gestão Global e Gestão do Evento. A origem da abertura, manual ou automática, fica registrada. Se a abertura foi manual, no horário previsto ocorre automaticamente Aberto → Em andamento. Se foi automática, o início automático ocorre 10 minutos após o horário originalmente previsto. Todas essas ações são notificadas às duas gestões e auditadas.

A forma de pagamento dos passes é definida pelo Administrador Global até o início do evento. Os tipos de passes podem ser editados pelo Administrador do Evento enquanto o evento estiver Aberto e ficam bloqueados em Em andamento. O passe pode ser por quantidade ou por tempo e pode ser pago ou gratuito, inclusive brinde/cortesia.

A pausa não amplia a duração. Se o horário final chegar durante Pausado, o evento é encerrado automaticamente. Faltando 15 minutos para o término programado, os participantes recebem tarja persistente de encerramento próximo.

O encerramento antecipado exige CAPTCHA e justificativa descritiva obrigatória. Responsável, justificativa e ação ficam auditados e as duas gestões são notificadas. Exatamente 15 dias após o encerramento, o evento passa automaticamente para Arquivado; esse prazo é operacional e não constitui prazo legal de retenção.

## Passes e pagamentos - escopo técnico-financeiro atual

O produto não terá, nesta versão, integração com plataforma de pagamento nem validação automática de recebimento. Não haverá gateway, PIX integrado, cartão ou confirmação financeira externa.

O fluxo operacional é: Participante solicita passe → Operador autorizado localiza o participante → seleciona o passe → concede o passe → sistema registra a concessão → passe fica disponível ao participante.

Somente Operadores com permissão específica de venda/concessão de passes podem executar a operação. Cada concessão deve registrar, para auditoria, operador, participante, evento, tipo de passe, data/hora e origem da operação.

Os passes podem ser por quantidade de revelações ou por tempo de validade. Cada tipo pode possuir valor monetário ou ser gratuito, inclusive como brinde/cortesia do evento. Se gratuito, a concessão é registrada sem valor financeiro. Se houver valor monetário configurado, a concessão é computada como venda no relatório financeiro pelo valor definido para o passe. Esse registro representa a operação declarada no sistema e não comprova o efetivo recebimento do dinheiro.

O relatório financeiro deve permitir identificar quantidade de passes concedidos/vendidos, tipo de passe, valor unitário configurado, valor total computado, operador responsável e data/hora. Passes gratuitos devem ser identificados separadamente ou com valor zero.

A revogação de um passe nunca apaga nem altera o lançamento original. Para passe com valor monetário, o valor permanece computado no relatório financeiro como venda registrada e a revogação aparece como evento posterior. A revogação deve registrar operador responsável, data/hora e motivo, preservando a trilha auditável.

### Evolução futura

Ficam explicitamente fora do escopo atual e anotados para implementação futura: integração com plataformas de pagamento; PIX e cartões; confirmação automática de pagamento; estados financeiros completos; conciliação; estorno e reembolso; idempotência de transações financeiras; tratamento de falhas de provedores; comprovantes; regras fiscais e tributárias; integração contábil; e demais mecanismos de processamento financeiro externo. A implementação futura não deve descaracterizar o histórico auditável das concessões, vendas e revogações.
