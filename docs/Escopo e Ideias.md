# SaaS de Encontro

> Documento de requisitos consolidado em 04/10/2026. Não é uma declaração de funcionalidades já implementadas; consulte [Verificação da implementação](<Verificacao da implementacao.md>). O texto preserva a evolução da fonte: as seções finais de definição/consolidação prevalecem sobre propostas anteriores do mesmo assunto. Consulte o [índice e análise](README.md) para divergências e precedência.

## Objetivo

Organizar o escopo, decisões e ideias do projeto desenvolvidas durante as conversas.

## Princípio atual

Neste momento, o foco é estruturação e organização conceitual. Nada de código.

Como este documento será usado

- Registrar ideias novas.
- Consolidar decisões tomadas.
- Separar hipóteses de decisões confirmadas.
- Manter dúvidas e pontos em aberto visíveis.
- Evoluir o escopo antes de entrar em implementação.

## Estrutura inicial
1. Visão do produto
2. Problema que queremos resolver
3. Público-alvo
4. Proposta de valor
5. Fluxos principais
6. Funcionalidades e escopo
7. Regras de negócio
8. Hipóteses e validações
9. Decisões tomadas
10. Questões em aberto
11. Próximos passos

## Experiência do participante — navegação principal

A experiência do participante será organizada como um web app mobile-first, com navegação principal no rodapé. O fluxo de descoberta é apenas uma das áreas do produto.

## 1. Descoberta

Área principal, possivelmente com o botão central em maior destaque. Exibe perfis sequencialmente, com fotos e informações do participante. O usuário manifesta interesse ou desinteresse por gestos de deslizar ou controles equivalentes. Os gestos exatos permanecem em aberto. Antes do match, poderá existir uma mensagem curta de apresentação. O chat completo somente é liberado quando houver interesse recíproco (match).

## 2. Mensagens

Caixa de conversas com participantes com quem houve match. Reúne os chats privados liberados pela reciprocidade de interesse.

## 3. Meu perfil

Área para visualizar e editar dados, fotos, preferências pessoais e demais informações do próprio perfil permitidas durante o evento.

## 4. Filtros

Área dedicada aos critérios utilizados na descoberta de pessoas, incluindo faixa etária, hobbies, escolaridade, preferências e outros atributos que ainda serão definidos.

## 5. Pessoas do evento

Visão geral de todos os participantes que passaram e foram validados naquele evento, independentemente dos filtros configurados na descoberta. Deve permitir visualizar a quantidade total de participantes e navegar por representações compactas, como foto e/ou nome.

## Personalização de interface

A visão geral de participantes poderá oferecer controles de densidade visual, permitindo ao usuário alterar o tamanho das miniaturas e/ou outros elementos de interface. Os detalhes dessa personalização permanecem em aberto.

## Fluxo social principal

Participante validado → configura filtros → descobre perfis → demonstra interesse/desinteresse → apresentação opcional → reciprocidade → match → chat privado → possível encontro presencial

## Decisões consolidadas — experiência, fotos, navegação e presença física

### Identidade e navegação

- Uma identidade global pode assumir papéis diferentes por evento, sem duplicação de conta.
- Após autenticação, Voltar não retorna ao login. Participante retorna à Descoberta; administração do evento ao Dashboard do evento; administração global ao Dashboard global. Login volta apenas por logout explícito ou perda de autenticação.
- Onboarding é fluxo de primeira entrada. Depois de concluído, Perfil e Filtros são fluxos independentes de edição. Aplicar filtros retorna diretamente à Descoberta.

### Descoberta, perfil e favoritos

- A Descoberta possui apenas PASS e LIKE como decisões principais. Favoritar não é uma terceira interação de descoberta.
- O botão “i” expande o card/perfil do participante analisado e permite consultar informações e as fotos públicas, mesmo sem match.
- O perfil pode ser aberto antes do match. O match controla a visibilidade do conteúdo adicional, não o direito de abrir o perfil.
- Favoritar pertence ao contexto pós-match, associado à conversa/pessoa. Em mensagens, o menu contextual permite Favoritar/Desfavoritar e Ver perfil; a conversa também oferece acesso visível ao perfil.

### Fotos

- Para ativação do perfil no evento são exigidas três fotos públicas.
- Antes do match, somente essas fotos públicas são exibidas. Após match ativo, liberam-se as fotos adicionais e a foto de outfit conforme as regras do produto.
- Após a ativação do perfil naquele evento, as três fotos públicas obrigatórias não podem ser removidas. Fotos adicionais continuam editáveis. A restrição deve existir na interface e nas regras de negócio.

### Configuração posterior do evento

- A criação inicial do evento permanece simples. Posteriormente, a administração poderá configurar logo/imagem, localização geográfica de referência e raio presencial.
- O raio é configurável para acomodar desde locais pequenos até grandes áreas de convenção.
- Em eventos online, presença geográfica não se aplica; em híbridos, aplica-se ao componente presencial.
- Alterações de ponto ou raio durante evento em andamento são ações administrativas sensíveis e devem ser auditadas.

### Presença física

- Em eventos presenciais, o Web App revalida periodicamente a localização para determinar se o participante está fisicamente dentro do perímetro configurado.
- A finalidade é validar presença, não rastrear continuamente o trajeto do participante.
- Presença física e estado online são independentes. Um participante pode estar online e não presencial.
- Dentro do raio, o participante recebe indicador de presença física confirmada; fora do raio, indicador de não presencial. As cores definitivas ficam para o design.
- Sair do raio não desconecta, não remove a participação e não bloqueia Descoberta, Likes, matches ou mensagens. O participante pode sair temporariamente e retornar depois, com o estado evoluindo Presencial → Não presencial → Presencial.
- A participação no evento representa vínculo com aquele evento; a presença física representa somente a situação naquele instante.

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

A Administração Global é a interface operacional principal e de negócio do sistema. O menu Mais deve oferecer Admin do sistema, direcionando ao Django Admin.

O Django Admin é reservado a manutenção avançada, exceções e alterações pontuais. Seu acesso exige permissão específica e não é concedido automaticamente por papéis administrativos de evento. Alterações relevantes feitas nele devem ser auditáveis, registrando responsável, data/hora, entidade e alteração.

O Django Admin não substitui fluxos recorrentes da Administração Global. Operações recorrentes ou relevantes ao negócio devem possuir interface própria. A matriz específica de acesso ao Django Admin será definida na matriz definitiva de permissões.

## Matriz de permissões — definição atual

Administrador Global corresponde ao usuário com Status de superusuário ativo no Django. O acesso ao Django Admin utiliza a flag Membro da equipe; essa flag não equivale a Administrador Global. Papéis administrativos de evento não concedem automaticamente essas flags globais.

Administrador do Evento pode gerenciar Moderadores e Operadores do próprio evento, conceder e revogar permissões operacionais, acessar métricas e relatórios. Pode delegar temporariamente a administração somente a um membro da Moderação e retomá-la depois. Delegação e retomada são auditadas e notificadas ao Administrador Global.

As permissões que o Administrador do Evento pode conceder se limitam às tratativas operacionais do evento: denúncias; bloqueios e desbloqueios; venda, concessão e revogação de passes; ativação e desativação de perfil; captura de foto de ativação; remoção de foto; e edição de bio quando necessária à tratativa. Não abrangem administração global nem funções técnicas.

Moderador possui praticamente o mesmo domínio operacional de tratativas do Administrador do Evento, conforme permissões recebidas, mas não gerencia equipe ou permissões e não acessa métricas nem relatórios. Pode receber temporariamente a administração do evento.

Operador é o principal responsável pela captura da foto de outfit e ativação operacional do perfil. Pode disponibilizar o QR Code do evento e abrir ocorrência administrativa ligada ao participante, como passe que não vigorou ou ajuda/falha ao editar o próprio perfil. Abrir ocorrência não concede automaticamente poderes de moderação.

Intervenções em foto, bio ou conteúdo do perfil precisam de origem justificável e auditável. Quando decorrerem de denúncia, devem ser vinculadas à denúncia. O participante também poderá solicitar suporte dentro da tela de Mensagens; intervenções decorrentes desse atendimento devem ser vinculadas à respectiva solicitação/conversa de suporte.

Mudanças de equipe, grupos, permissões, delegação e retomada, decisões de moderação e intervenções sobre perfil devem ser auditáveis.

## Passes e revelação de Likes

Na tela Participantes haverá o filtro Likes recebidos para Likes ainda sem Match. Sem passe válido, as identidades permanecem ocultas e a interface informa que a revelação é paga, apresentando a modalidade configurada pelo evento: aquisição no balcão de atendimento ou pelo próprio sistema.

O passe apenas revela quem já deu Like; não cria Match. Havendo Like de volta, o Match ocorre normalmente.

O passe poderá ser por quantidade de revelações ou por tempo. No modelo por quantidade, cada identidade revelada consome uma unidade e os Likes são revelados em ordem cronológica, do mais antigo para o mais recente. No modelo por tempo, a revelação ocorre durante a vigência; Likes recebidos depois da expiração permanecem ocultos.

Likes não revelados permanecem registrados para um passe posterior. Quando não houver passe, saldo ou vigência, a tela exibe a quantidade de Likes ocultos, uma mensagem explicativa e a opção de adquirir novo passe.

Venda, concessão e revogação manual de passes seguem as permissões da equipe do evento e são operações auditáveis.

## Notificações

As notificações do participante são internas e compartilham o ícone de Mensagens. A tela alterna entre Mensagens e Notificações, incluindo Likes recebidos, Matches, suporte, passe expirado e avisos do evento.

Moderadores possuem Avisos do Evento em lista/cards, com rascunho, envio imediato ou agendamento, formatação simples e URL opcional aberta em nova aba. Avisos podem ser criados e editados em Aberto, Em andamento e Pausado. Agendados disparam em Aberto ou Em andamento; em Pausado não disparam automaticamente, geram alerta administrativo e admitem envio manual; em Encerrado não podem ser enviados.

Não é permitido agendar após o encerramento previsto. Agendamentos nos 30 minutos finais exigem confirmação explícita. O estado do evento é revalidado antes do disparo.

## Perfil e visibilidade

A ativação exige três fotos públicas válidas e uma foto de outfit adicionada pela equipe. Após Match, as demais fotos são liberadas. Se uma foto pública for removida pela equipe, o perfil fica inativo até reposição e nova validação. Antes da abertura, a organização também pode definir campos obrigatórios ou opcionais para ativação, como termos, consentimentos e listas de marcação.

## Denúncias e segurança

A denúncia pode ser feita na Descoberta, perfil expandido e Mensagens, com relato obrigatório e indicação do conteúdo relacionado. Conteúdos substituídos permanecem historicamente vinculados para auditoria conforme retenção. Dez denúncias válidas geram alerta à moderação do evento; vinte geram desativação automática para análise e notificação à Administração Global. Denúncias consideradas infundadas não entram nesses limites. O histórico permanece ligado ao perfil global e pode fundamentar marcação de acompanhamento recorrente, sem bloqueio automático em eventos futuros.

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
