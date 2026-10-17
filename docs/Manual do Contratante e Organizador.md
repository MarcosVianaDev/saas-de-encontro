# SaaS de Encontro — Manual do Contratante e Organizador

> **Atualização de 16/10/2026:** as descrições de Presente Inicial (seção 7), funções e delegação da equipe (seção 10) e exportação auditável (seção 18) foram conferidas no código e documentam recursos implementados. As demais partes ainda preservam requisitos ou registros anteriores. Consulte [Estado atual do sistema](<Estado atual do sistema.md>), [Verificação atual](<Verificacao da implementacao.md>) e [pendências da etapa 10](<Etapa 10 - verificacao e pendencias.md>) para o contexto das revisões anteriores.

> Documento de requisitos consolidado em 04/10/2026. Não é uma declaração de funcionalidades já implementadas; consulte [Verificação da implementação](<Verificacao da implementacao.md>). O texto preserva a evolução da fonte: as seções finais de definição/consolidação prevalecem sobre propostas anteriores do mesmo assunto. Consulte o [índice e análise](README.md) para divergências e precedência.

## 1. Papel do contratante

O contratante utiliza a plataforma para oferecer a experiência de encontros dentro de um evento. A operação acontece dentro das regras contratadas com a administração da plataforma. Salas são roadmap futuro, sem fluxo operacional de subdivisão do evento na versão atual.

O organizador administra o contexto do seu evento, enquanto a administração geral mantém as regras estruturais, segurança, governança, recursos disponíveis e condições comerciais da plataforma.

## 2. Eventos, modalidades e roadmap de salas

Participantes, administradores, configurações e métricas ficam vinculados ao evento. **Salas são roadmap futuro**: não devem ser apresentadas ao contratante como recurso operacional disponível, mesmo existindo estruturas técnicas reservadas para essa evolução.

A plataforma separa a identidade global do usuário de sua participação em cada evento, evitando mistura indevida de informações entre eventos.

### Modalidades disponíveis

| Modalidade | Localização e presença | Ativação do participante |
| --- | --- | --- |
| **Presencial (`PHYSICAL`)** | Exige latitude/longitude de referência e validação por GPS. Raio padrão de **100 m**, limite adicional padrão de **1.000 m** e intervalo padrão de 15 minutos. | Validação pela equipe, 3 fotos públicas válidas (uma principal), bio de 50 a 200 caracteres, outfit e demais requisitos obrigatórios. |
| **Online (`ONLINE`)** | Dispensa coordenadas de referência e GPS do participante. A presença é determinada pela atividade recente no sistema; o intervalo configurado define quando ele passa a ser considerado ausente. | A organização pode habilitar **ativação automática**, que dispensa outfit e ativa o perfil ao completar os demais requisitos em Aberto ou Em andamento. Sem essa opção, permanece a ativação manual com outfit. |
| **Híbrida (`HYBRID`)** | Na implementação atual, segue as mesmas regras de GPS, coordenadas, raio e limite adicional do Presencial. | Segue a ativação manual com outfit. Não habilita ativação automática nem um regime separado de acesso remoto por participante. |

A modalidade é escolhida no cadastro ou solicitação do evento. A ativação automática só é aceita em eventos Online; os demais campos, fotos, termos e mínimos de tópicos obrigatórios continuam exigidos. As configurações de modalidade ficam bloqueadas após a abertura do evento.

## 3. Configuração do cadastro

A plataforma possui campos estruturais do perfil e poderá oferecer campos globais configurados pela administração do sistema.

O organizador poderá adicionar campos e opções que façam sentido especificamente para seu público ou evento e definir quais serão obrigatórios ou opcionais.

## 4. Perfil e fotos dos participantes

O perfil exige um conjunto mínimo de informações e pelo menos 3 fotos públicas, com uma foto principal. O participante poderá manter até 10 fotos, sendo as adicionais protegidas até o match.

A foto de outfit é vinculada ao evento e fica disponível apenas depois do match, ajudando os participantes a se reconhecerem presencialmente. É dispensada em eventos Online com ativação automática habilitada, conforme a seção 2.

## 5. Descoberta e filtros

Os participantes configuram suas próprias preferências de descoberta. O sistema não relaxa filtros automaticamente.

Quando os perfis elegíveis se esgotam, o participante é informado e pode ajustar suas preferências. O organizador não deve substituir a decisão individual do participante sobre quem deseja conhecer.

## 6. Likes e matches

Participantes podem marcar perfis com LIKE ou PASS e revisar decisões anteriores em seu histórico.

O match ocorre quando existe interesse mútuo válido. Depois dele, são liberadas as fotos adicionais, a foto de outfit, quando houver, e a conversa.

## 7. Passes e benefícios

A plataforma permite estruturar passes e benefícios específicos para o evento. A definição das ofertas é feita conforme o acordo entre o contratante e a administração da plataforma.

Os passes podem funcionar por tempo, quantidade ou combinação. Exemplos incluem liberação por um dia, por vários dias ou por determinada quantidade de revelações de likes.

### Presente Inicial gratuito

No cadastro ou na solicitação de um evento, é possível habilitar o **Presente Inicial** e informar o nome do passe gratuito. Escolha uma das modalidades: duração em minutos **ou** quantidade de revelações. O presente usa apenas uma dessas modalidades, com valor maior que zero; não combina duração e quantidade no mesmo benefício.

A entrega pode ser configurada de duas formas:

- **Imediata:** atraso de zero minutos; o passe é concedido e ativado quando o perfil do participante é ativado, respeitando as condições do evento.
- **Agendada:** informe quantos minutos após o início cadastrado do evento o presente deverá ser liberado. Esse horário deve ser anterior ao término previsto. A entrega ocorre com o evento Em andamento; quem for ativado depois do horário programado pode receber o benefício assim que estiver elegível.

O participante precisa estar ativo, com ativação registrada, conta ativa e sem banimento no evento. A entrega não ocorre após o término previsto nem em eventos Encerrados ou Arquivados. Com atraso zero, a concessão também pode ocorrer em Aberto ou Pausado; presentes agendados aguardam o estado Em andamento.

O processamento em segundo plano usa um worker dedicado, em lotes de 25 participantes por padrão, com tamanho configurável entre 1 e 100. O agendador verifica as entregas devidas a cada 30 segundos; portanto, a entrega agendada depende do processamento da fila, sem promessa de execução no segundo exato. O worker também recupera entregas imediatas ainda pendentes quando o evento estiver Em andamento.

Cada participante recebe o Presente Inicial **uma única vez naquele evento**, mesmo se o processamento for repetido ou o perfil for reativado. A configuração e a concessão ficam na auditoria; o passe tem valor financeiro zero, já é ativado na entrega e gera notificação ao participante. Em passes por tempo, a validade começa na concessão. O presente não exige pagamento nem concessão manual pelo Operador.

## 8. Formas de pagamento e responsabilidade

O contrato poderá prever três modelos principais.

Pagamento direto ao estabelecimento ou organizador: o participante paga por meios externos à plataforma, como PIX, dinheiro ou maquininha do próprio estabelecimento. Um administrador autorizado confirma a operação e libera o benefício no sistema.

Pagamento processado pela plataforma com repasse: a plataforma processa o pagamento e o contrato define valores, taxas e eventual repasse ao contratante.

Pagamento destinado à própria plataforma: a plataforma comercializa o benefício diretamente e o evento não participa financeiramente daquela venda.

As modalidades disponíveis não são escolhidas unilateralmente no painel do evento; decorrem das condições contratadas com a administração do sistema.

## 9. Liberação administrativa de passes

Quando um pagamento for recebido externamente pelo contratante, usuários administrativos autorizados poderão liberar o passe correspondente.

Essas liberações deverão ser auditáveis, registrando responsável, momento da liberação, benefício, valor declarado e forma de pagamento.

## 10. Administração e permissões

A administração do evento poderá gerenciar as funções permitidas pelo contrato e pelas permissões atribuídas. A administração geral da plataforma mantém recursos e controles de nível sistêmico.

As ações administrativas sensíveis deverão ser registradas para auditoria.

### Matriz de funções da equipe

Os vínculos de equipe são específicos de cada evento e utilizam três papéis cadastrados:

| Papel | Funções padrão no evento | Limites e permissões adicionais |
| --- | --- | --- |
| **Administrador do Evento (`ADMIN`)** | Gestão do evento e da equipe; denúncias, bloqueios, passes, ativação, captura de outfit, remoção de fotos, edição de bio, exceções de localização e avisos. | A Administração Global define quem ocupa esse papel. O administrador local não pode nomear outro `ADMIN` nem revogar a gestão responsável. Configurações exclusivas da Administração Global continuam restritas. |
| **Moderador (`MODERATOR`)** | Denúncias, bloqueios, ativação, captura de outfit, remoção de fotos, edição de bio, exceções de localização e avisos. | Não recebe gestão da equipe nem concessão de passes por padrão. Permissões operacionais adicionais podem ser atribuídas; a gestão pode ser recebida por delegação temporária. |
| **Operador (`OPERATOR`)** | Ativação de participantes e captura de outfit. | Venda/concessão de passes exige a permissão adicional `passes`. Outras permissões operacionais podem ser atribuídas pela gestão autorizada. Não recebe gestão do evento ou da equipe apenas por ser Operador. |

A conta deve existir e estar ativa para ser incluída na equipe. Administradores autorizados podem cadastrar ou atualizar Moderadores e Operadores, atribuir permissões operacionais e ativar ou desativar vínculos. Somente a Administração Global pode atribuir ou alterar o papel `ADMIN`. As permissões adicionais complementam as funções padrão do papel; não são uma forma de retirar suas permissões padrão. Após o encerramento, a equipe fica em modo somente leitura para novas alterações.

### Delegação temporária da gestão

O Administrador do Evento pode delegar temporariamente sua gestão a um **Moderador ativo do mesmo evento**, mediante confirmação explícita. A Administração Global também pode realizar a delegação da gestão responsável. Operadores não são destinatários dessa ação.

Durante a delegação, o Moderador passa a exercer as funções de Administrador naquele evento, sem alteração definitiva de seu papel cadastrado. O administrador que delegou deixa de exercer a gestão enquanto a delegação estiver vigente e pode **retomar a administração**. A retomada encerra os poderes administrativos temporários do destinatário; ela não transforma o Moderador em administrador permanente. A delegação não altera o responsável cadastrado do evento nem concede acesso à Administração Global.

Não há prazo automático de expiração: a delegação permanece até a retomada. Novas delegações não são permitidas em eventos Encerrados ou Arquivados; a ação de retomada pelo administrador original permanece disponível. Delegação e retomada geram registros de auditoria e notificações à gestão.

## 11. Bloqueios

O bloqueio realizado por um participante é definitivo dentro daquele evento.

Depois do bloqueio, os dois usuários deixam de visualizar os perfis um do outro e não podem continuar a interação. O histórico de mensagens pode permanecer acessível de forma anonimizada conforme as regras do produto.

O bloqueio registra o motivo e a ação na auditoria do evento. Bloqueios isolados ou acumulados não geram automaticamente alerta, denúncia ou sanção; os limiares operacionais de segurança utilizam denúncias relevantes de participantes distintos. Salas permanecem no roadmap futuro e não constituem um escopo atual de moderação.

## 12. Bloqueios em eventos futuros

O bloqueio se limita ao evento em que foi realizado e não é aplicado automaticamente a eventos futuros. Não há aviso de bloqueio anterior nem confirmação adicional de LIKE baseada em bloqueios de outro evento.

A decisão de prosseguir em um novo evento pertence ao próprio participante.

## 13. Denúncias e moderação

Denúncia, análise de moderação e punição são etapas distintas.

Uma denúncia registra uma alegação. A administração responsável poderá analisá-la dentro de suas permissões, e ações posteriores ficam registradas separadamente. A administração geral também deverá ter visibilidade dos casos previstos no escopo.

## 14. Métricas administrativas

O contratante poderá acompanhar métricas previstas para seu evento, incluindo participação, interações e indicadores de moderação, como quantidade de denúncias e bloqueios.

Esses dados ajudam a compreender o comportamento do público e a operação do evento, respeitando as regras de acesso e privacidade.

## 15. Dados, LGPD e retenção

LGPD, auditoria e retenção são requisitos estruturais da plataforma.

Dados vinculados ao evento seguem um ciclo de vida. Após o encerramento, os dados previstos são mantidos somente pelo período aplicável. Existindo fundamento válido de preservação, poderá haver retenção específica. Encerrado o período aplicável e inexistindo motivo legítimo para preservação, os dados correspondentes deverão ser eliminados.

O prazo jurídico definitivo e as responsabilidades específicas deverão estar alinhados à política da plataforma e aos instrumentos contratuais aplicáveis.

## 16. Relação com a administração da plataforma

A administração geral define os recursos sistêmicos disponíveis, mantém controles de segurança e governança e acorda com o contratante as condições comerciais e operacionais.

O organizador administra seu evento dentro desse perímetro. Alterações que afetem condições comerciais, meios de pagamento, benefícios contratados ou controles sistêmicos dependem da relação contratual com a administração da plataforma.

## 17. Exclusão dos dados ao fim do evento e métricas consolidadas

O contratante deve considerar como regra de operação que os dados pessoais e operacionais individualizados do evento não constituem uma base permanente do organizador. Ao término do evento, esses dados serão excluídos conforme o ciclo de encerramento da plataforma, ressalvadas apenas hipóteses em que exista obrigação ou fundamento jurídico válido de preservação.

Após o encerramento, poderão permanecer métricas consolidadas e agregadas necessárias para histórico administrativo, estatísticas e análise da operação, sem que essas métricas sejam utilizadas como substituto para conservar os perfis individuais dos participantes.

O perfil persistente que um participante optar por manter na plataforma é uma relação entre o usuário e a plataforma e deve ser tratado separadamente dos dados daquele evento. O contratante não passa a deter permanentemente esse perfil pelo fato de o usuário ter participado de seu evento.

A plataforma deverá disponibilizar ao usuário mecanismo para solicitar a exclusão de sua conta e de seu perfil persistente, observadas eventuais obrigações legais de conservação. Também permanecem disponíveis ao titular os direitos e meios legais previstos na legislação aplicável.

## 18. Exportação auditável de dados — Etapa 10

A exportação de dados do evento **está implementada**. O contratante ou organizador deve tratar a solicitação com a **Administração Global**, responsável pelo acesso à geração, consulta de andamento, download e registro da entrega. Ser Administrador, Moderador, Operador ou gestor temporário de um evento não concede esse acesso global.

### Solicitação e acompanhamento

A Administração Global seleciona o evento, informa a referência da solicitação e escolhe os módulos da exportação. É possível exportar o conjunto completo ou um recorte; a auditoria é sempre incluída. Os módulos disponíveis abrangem participantes, moderação, mensagens, localização, passes, notificações, métricas, consentimentos e auditoria. O catálogo técnico inclui ainda o módulo de salas para registros eventualmente existentes; isso não torna disponível a operação de salas, que permanece no roadmap futuro.

A geração ocorre **assincronamente em um worker dedicado**. O painel apresenta os estados Pendente, Em processamento, Concluída ou Falhou, com progresso e etapa atual. Uma solicitação em andamento é reutilizada para evitar gerações concorrentes no mesmo evento. Em caso de falha, há opção de nova tentativa; o download só é liberado após a conclusão e a verificação de integridade.

### Conteúdo e integridade

O resultado inclui dois artefatos principais, baixados separadamente:

- **Pacote ZIP:** contém a fotografia dos dados selecionados, as mídias disponíveis, `snapshot.json`, o SQL `event.sql`, a interface de consulta `index.html`, instruções em `README.txt`, o verificador `verify.py` e o manifesto `manifest.json`.
- **Termo em PDF:** identifica a exportação, o evento, a organização, o solicitante, a referência, o momento da geração, os módulos e o hash SHA-256 do ZIP. O termo é externo ao ZIP, evitando dependência circular entre arquivo e hash.

O manifesto registra os hashes **SHA-256** dos arquivos componentes, seus tamanhos, as contagens de registros, os módulos omitidos e eventuais mídias ausentes. O sistema também registra os hashes do ZIP e do PDF e os confere antes do download. Após extrair o ZIP, o destinatário pode executar `verify.py` com Python para conferir os arquivos listados no manifesto.

O pacote é limitado ao evento solicitado e às dependências necessárias para interpretar seus registros. Não inclui senhas, sessões, tokens nem dados de outros eventos. Exporta somente os registros ainda existentes na fotografia: dados já eliminados ou anonimizados não são reconstruídos. Mídias ausentes são indicadas no manifesto.

### Consulta offline e entrega

Depois de extrair o ZIP, abra `index.html` no navegador para consultar o conteúdo **offline e em modo somente leitura**, sem servidor e sem conexão com a plataforma. O arquivo SQL permite consulta técnica em um banco PostgreSQL vazio, separado do ambiente operacional; o pacote não deve ser restaurado sobre produção.

A Administração Global pode anexar o termo assinado em PDF e registrar a referência da assinatura e da entrega. Esse registro é manual; não equivale a uma integração automática com um provedor de assinatura. Solicitação, processamento, conclusão ou falha, downloads, assinatura e entrega possuem trilha de auditoria.

O prazo padrão para download é de **168 horas (7 dias)** após a conclusão, configurável pela operação. Depois da expiração, pode ser solicitada nova geração. Esse prazo de disponibilidade não define a retenção dos dados do evento, e a exportação não substitui nem executa sua eliminação.

## LGPD, retenção e eliminação

As regras detalhadas de categorias de dados, temporalidade, anonimização, exclusão, direitos do titular e preservação judicial estão centralizadas no documento **LGPD - Retenção, Eliminação e Direitos do Titular**. Não existe prazo único para todos os dados: cada categoria deve seguir finalidade, base legal e matriz de retenção próprias. Os 15 dias para arquivamento do evento são regra operacional, não prazo jurídico. O projeto deve aplicar ConsentRecord, DataRetentionRecord, LegalHold, PrivacyRequest e AuditLog conforme essa política. Antes da produção, os prazos específicos ainda não fixados devem passar por validação jurídica.

Documento: https://docs.google.com/document/d/1iVfUgkg_0EBERID5z9ZA-WnRu9e6bIDECgBTFW0pmM0/edit

## Geolocalização - regras operacionais

Estas regras se aplicam às modalidades Presencial e Híbrida; Online não utiliza GPS. O raio padrão do evento é **100 metros** e determina presença atual. O limite adicional padrão é **1.000 metros** e pode ser alterado somente antes do evento entrar em andamento. Com os valores padrão, o limite máximo é de 1.100 metros a partir do ponto de referência. Fora do raio, mas dentro do limite máximo, o participante é considerado temporariamente fora e pode retornar. Além do limite máximo há possível anomalia, sem punição automática por uma leitura isolada.

Se a checagem periódica falhar, são feitas 5 novas tentativas com intervalo de 1 minuto. Persistindo a falha, o participante recebe tarja e notificação fixa para tentar novamente. Se a próxima checagem periódica também falhar, o perfil é desativado por motivo técnico, mas a tentativa manual continua disponível. O Moderador pode reativar o perfil e conceder exceção temporária de X minutos sem verificação, com a intervenção auditada.

São sinais de anomalia: velocidade média estimada superior a 60 km/h entre duas medições válidas consecutivas; ou duas medições válidas além do raio somado ao limite adicional. O sinal não constitui fraude nem punição automática.

O histórico individual de localização só pode ser consultado pelo Administrador Global e pelo Administrador/Gestor responsável pelo evento. A consulta é permitida com o evento Pausado, para investigação, e após Encerramento/Arquivamento enquanto houver retenção legítima. Não é permitida nos estados Aberto ou Em andamento. Toda consulta é auditada.

O prazo de retenção dos dados de geolocalização permanece pendente de validação LGPD antes do lançamento em produção e deverá seguir a matriz específica de retenção, eliminação, anonimização e Legal Hold.

## Ciclo de vida do evento - regras consolidadas

O Administrador Global define início, término e Administrador responsável, editáveis somente antes de Aberto. O raio de presença e o limite adicional de anomalia podem ser alterados pelo Administrador Global ou pelo Administrador do Evento até antes de Em andamento.

O evento pode ser aberto manualmente a partir de 2 horas antes do início. Se permanecer Agendado, 5 minutos antes do início será aberto automaticamente, com notificação à Gestão Global e à Gestão do Evento. Se aberto manualmente, inicia automaticamente no horário previsto; se aberto automaticamente, inicia 10 minutos após o horário originalmente previsto. A origem e as transições ficam auditadas.

A forma de pagamento dos passes é definida pelo Administrador Global até o início. Os tipos de passes podem ser editados pelo Administrador do Evento enquanto estiver Aberto. O passe pode ser por quantidade ou por tempo, pago ou gratuito, inclusive como brinde/cortesia.

A pausa não estende a duração. Faltando 15 minutos para o término, os participantes recebem tarja persistente. O encerramento antecipado exige CAPTCHA e justificativa descritiva obrigatória, com auditoria e notificação às duas gestões. O arquivamento automático ocorre 15 dias após o encerramento e não representa prazo legal de retenção de dados.

## Passes e pagamentos - escopo técnico-financeiro atual

O produto não terá, nesta versão, integração com plataforma de pagamento nem validação automática de recebimento. Não haverá gateway, PIX integrado, cartão ou confirmação financeira externa.

O fluxo operacional é: Participante solicita passe → Operador autorizado localiza o participante → seleciona o passe → concede o passe → sistema registra a concessão → passe fica disponível ao participante.

Membros da equipe com a permissão `passes` podem executar a operação: Administradores a possuem por padrão; Moderadores e Operadores precisam recebê-la explicitamente. Cada concessão deve registrar, para auditoria, o responsável pela operação, participante, evento, tipo de passe, data/hora e origem da operação. O Presente Inicial da seção 7 segue um fluxo automático próprio e dispensa concessão manual.

Os passes podem ser por quantidade de revelações ou por tempo de validade. Cada tipo pode possuir valor monetário ou ser gratuito, inclusive como brinde/cortesia do evento. Se gratuito, a concessão é registrada sem valor financeiro. Se houver valor monetário configurado, a concessão é computada como venda no relatório financeiro pelo valor definido para o passe. Esse registro representa a operação declarada no sistema e não comprova o efetivo recebimento do dinheiro.

O relatório financeiro deve permitir identificar quantidade de passes concedidos/vendidos, tipo de passe, valor unitário configurado, valor total computado, operador responsável e data/hora. Passes gratuitos devem ser identificados separadamente ou com valor zero.

A revogação de um passe nunca apaga nem altera o lançamento original. Para passe com valor monetário, o valor permanece computado no relatório financeiro como venda registrada e a revogação aparece como evento posterior. A revogação deve registrar operador responsável, data/hora e motivo, preservando a trilha auditável.

### Evolução futura

Ficam explicitamente fora do escopo atual e anotados para implementação futura: integração com plataformas de pagamento; PIX e cartões; confirmação automática de pagamento; estados financeiros completos; conciliação; estorno e reembolso; idempotência de transações financeiras; tratamento de falhas de provedores; comprovantes; regras fiscais e tributárias; integração contábil; e demais mecanismos de processamento financeiro externo. A implementação futura não deve descaracterizar o histórico auditável das concessões, vendas e revogações.

## Atualizações posteriores da especificação

As definições de geolocalização, ciclo de vida, concessão manual de passes e estágio MVP também estão em [Escopo Técnico](<Escopo Técnico.md>) e [Escopo e Ideias](<Escopo e Ideias.md>). A exportação auditável implementada está descrita na seção 18 deste manual; referências anteriores à funcionalidade como futura não representam seu estado atual. As modalidades de pagamento integrado descritas inicialmente neste manual são evolução futura; o escopo atual prevê concessão manual auditável e Presente Inicial automático, sem confirmação automática de recebimento financeiro.
