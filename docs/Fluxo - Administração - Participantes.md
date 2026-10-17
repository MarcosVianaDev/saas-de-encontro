# Fluxo - Administração - Participantes

> **Atualização de 16/10/2026:** os fluxos de captura de outfit, intervenção no perfil e exceção temporária de GPS (seções 11.1 a 11.3) foram conferidos no código e descrevem recursos implementados. As demais partes preservam requisitos ou registros anteriores. Consulte [Estado atual do sistema](<Estado atual do sistema.md>), [Verificação atual](<Verificacao da implementacao.md>) e [pendências da etapa 10](<Etapa 10 - verificacao e pendencias.md>) para o contexto das revisões anteriores.

> Documento de requisitos consolidado em 04/10/2026. Não é uma declaração de funcionalidades já implementadas; consulte [Verificação da implementação](<Verificacao da implementacao.md>). O texto preserva a evolução da fonte: as seções finais de definição/consolidação prevalecem sobre propostas anteriores do mesmo assunto. Consulte o [índice e análise](README.md) para divergências e precedência.

> Referência funcional preservada do DOCX. Cobertura implementada e limites atualizados em 04/10/2026: [Administração e ingresso](<Administracao e ingresso no evento.md>).

Fonte: [DOCX](<Fluxo - Administração - Participantes.md.docx>). Referência visual: [screen2.png](<Imagens - Telas e Protótipos/screen2.png>). Guia: [Telas administrativas](<Telas administrativas.md>).

## 1. Objetivo

Este documento define o fluxo funcional e as telas da área Participantes do painel administrativo de um evento.

A área Participantes funciona como visão operacional das pessoas vinculadas ao evento. Ela não é uma versão administrativa do Discovery.

Seu objetivo é permitir:
- localizar participantes;
- verificar situação no evento;
- consultar informações administrativas permitidas;
- acessar ocorrências;
- executar ações administrativas quando o funcionário possuir permissão.

A experiência permanece mobile-first e integrada à navegação administrativa do evento.

## 2. Fluxo principal

Fluxo conceitual:

Participantes
→ Detalhes do participante
→ Informações ou Ocorrências
→ Detalhes da ocorrência, quando necessário
→ Moderação

Fluxo de ação administrativa:

Detalhes do participante
→ Ação administrativa
→ Motivo + observação + confirmação
→ Suspensão ou banimento
→ Registro em auditoria

A área Participantes serve principalmente para localizar e administrar pessoas.

A área Moderação serve principalmente para investigar, acompanhar e decidir sobre ocorrências.

Para operações já implementadas, consultar os passos e formulários das seções **11.1 — Captura de outfit presencial e ativação**, **11.2 — Intervenções administrativas no perfil** e **11.3 — Exceção temporária de localização**. A intervenção em foto ou bio exige origem em denúncia/atendimento do participante, motivo justificado, confirmação e auditoria; a biografia deve manter 50 a 200 caracteres.

## 3. Tela Participantes

Ao selecionar Participantes no menu inferior administrativo, o usuário acessa a lista de pessoas vinculadas ao evento atual.

### 3.1 Cabeçalho

Exibir:
- título Participantes;
- quantidade total de participantes cadastrados;
- acesso aos filtros.

Exemplo:

Participantes
284 cadastrados

### 3.2 Busca

Campo de busca:

Buscar por nome ou e-mail

A busca deve atuar somente sobre participantes do evento que o usuário administrativo está autorizado a gerenciar.

### 3.3 Filtros rápidos

Filtros iniciais:

- Todos;
- Ativos;
- Novos.

Exemplo:

Todos 284 | Ativos 173 | Novos 38

### 3.4 Item da lista

Cada participante poderá exibir:

- foto;
- nome;
- idade, quando aplicável;
- informação profissional ou campo principal do perfil;
- estado de atividade;
- indicadores administrativos relevantes;
- acesso à ficha administrativa.

Exemplo:

Camila Souza, 28
Designer de Produto
Online agora
>

Indicadores visuais poderão representar:
- ativo/online;
- existência de ocorrência administrativa;
- informação relevante de bloqueios;
- suspensão;
- banimento.

Não devem ser apresentados na listagem geral:
- quantidade de likes;
- matches individuais;
- quantidade de conversas;
- perfis visitados;
- outras informações sociais que não sejam necessárias à operação.

## 4. Filtros avançados

Os filtros avançados poderão ser exibidos em painel inferior mobile.

### 4.1 Situação no evento

- Todos;
- Ativos;
- Inativos;
- Suspensos.

### 4.2 Cadastro

- Todos;
- Hoje;
- Última hora.

### 4.3 Moderação

- Sem ocorrências;
- Com denúncias;
- Com bloqueios;
- Sob análise.

Campos adicionais configurados especificamente pelo evento poderão ser considerados futuramente, mas não são requisito inicial.

### 4.4 Ações

- Limpar filtros;
- Aplicar.

## 5. Ordenação

Opções iniciais:

- Nome;
- Cadastro mais recente;
- Atividade recente.

Ordenações como “mais denunciados” não devem fazer parte da navegação operacional principal. Esse tipo de análise pertence à área de Moderação.

## 6. Detalhes do participante

Ao selecionar um participante, abrir a ficha administrativa correspondente à participação naquele evento.

Esta ficha é diferente do perfil social apresentado no Discovery.

### 6.1 Cabeçalho

Exibir:
- foto principal;
- nome;
- idade, quando aplicável;
- ocupação ou campo principal;
- status administrativo no evento;
- estado de atividade recente.

Exemplo:

Camila Souza, 28
Designer de Produto

Ativo no evento
Online agora

### 6.2 Abas

Inicialmente:

- Informações;
- Ocorrências.

## 7. Aba Informações

Apresentar somente dados necessários e autorizados para operação do evento.

Campos possíveis:
- nome completo;
- e-mail;
- telefone, quando coletado e permitido;
- data e hora do cadastro;
- última atividade;
- status no evento;
- identificador da participação.

### 7.1 Identificador operacional

A referência operacional preferencial deve ser o identificador de EventParticipant, e não necessariamente o UUID global do usuário.

Exemplo:

ID da participação
a81c…2f91
Copiar

Isso mantém a participação no evento como pivô operacional, conforme a arquitetura geral do projeto.

## 8. Aba Ocorrências

A aba apresenta informações administrativas pertinentes ao participante.

Resumo possível:

2 denúncias recebidas
3 bloqueios relacionados

Cada ocorrência poderá apresentar:

Denúncia — Pendente
Assédio ou comportamento inadequado
Hoje • 20:14
Ver ocorrência

ou:

Denúncia — Resolvida
Outro motivo
Hoje • 18:22
Ver ocorrência

A ação Ver ocorrência direciona para a área de Moderação.

## 9. Privacidade de informações sociais

O administrador do evento não deve obter acesso irrestrito à vida social do participante dentro da plataforma.

A ficha administrativa comum não deve apresentar:
- mensagens privadas;
- likes enviados;
- likes recebidos;
- passes;
- perfis rejeitados;
- matches individuais;
- conteúdo integral de conversas;
- preferências privadas desnecessárias à operação.

Quando determinada informação ou evidência fizer parte formal de uma denúncia, ela deverá ser tratada dentro do fluxo específico de Moderação e conforme as regras de acesso que forem definidas.

## 10. Bloqueios

Bloqueios entre participantes são diferentes de ações administrativas.

A ficha poderá apresentar um indicador agregado, por exemplo:

Bloqueios relacionados: 5

A ficha comum não precisa identificar automaticamente todas as relações individuais de bloqueio.

Detalhes dessas relações deverão permanecer na área de Moderação quando forem necessários para investigação.

Um bloqueio entre participantes:
- afeta a relação entre aqueles participantes conforme as regras do evento;
- pode gerar indicador de segurança/moderação;
- não representa automaticamente punição administrativa;
- não deve automaticamente suspender ou expulsar o usuário bloqueado.

## 11. Menu de ações administrativas

A ficha poderá possuir um menu de ações no canto superior direito.

As opções apresentadas dependem das permissões do funcionário.

Possíveis ações:
- Ver ocorrências;
- Abrir ocorrência administrativa;
- Suspender do evento;
- Remover acesso ao evento.

Na ficha também existem os fluxos operacionais implementados de **Ativação e presença** e **Intervenção no perfil**, conforme as permissões da equipe. Eles não são sanções administrativas e estão detalhados a seguir.

A nomenclatura “bloquear participante” não deve ser usada para sanções administrativas, pois Block é reservado ao relacionamento participante-participante.

### 11.1 Captura de outfit presencial e ativação

O **Operador** é o responsável operacional pela captura presencial do outfit e pela ativação do participante. As ações exigem, respectivamente, as permissões `outfit` e `activation`, disponíveis por padrão para Operadores, Moderadores e Administradores do Evento. O vínculo da equipe e o participante devem pertencer ao evento em atendimento.

Fluxo na ficha do participante:

1. Localizar a pessoa na lista **Participantes** e abrir sua ficha.
2. Na seção **Ativação e presença**, selecionar **Capturar foto**. Em dispositivos compatíveis, a captura solicita a câmera traseira.
3. Fotografar o participante presencialmente e conferir a prévia do look. Usar **Tirar novamente** se a imagem não estiver adequada.
4. Selecionar **Usar esta foto** para enviar e registrar o outfit. São aceitas imagens JPEG, PNG ou WebP de até 10 MB.
5. Conferir os requisitos do cadastro e selecionar **Ativar perfil**. Salvar o outfit, isoladamente, não ativa o participante.

Na ativação manual, o sistema exige nome, sobrenome, nascimento, gênero, bio de **50 a 200 caracteres**, exatamente 3 fotos públicas válidas (uma principal), outfit e os tópicos, campos e termos obrigatórios do evento. Nos eventos Presenciais ou Híbridos, exige também validação de localização. Cadastro incompleto deve ser corrigido antes de tentar novamente.

A ativação manual é permitida com o evento **Aberto** ou **Em andamento**. Ela não remove suspensão de conta, suspensão no evento ou banimento: essas restrições precisam ser resolvidas antes. A captura registra o responsável, a data e o contexto na auditoria (`outfit.captured`); a ativação gera `profile.activated` e notifica o participante.

**Exceção de modalidade:** eventos Online não solicitam GPS. Quando a organização habilita a ativação automática de participantes em um evento Online, o outfit é dispensado e o perfil pode ser ativado ao completar os demais requisitos. Sem essa opção habilitada, o fluxo manual continua exigindo outfit. A equipe não deve solicitar captura presencial como requisito do fluxo Online com ativação automática.

### 11.2 Intervenções administrativas no perfil

A seção **Intervenção no perfil** permite à moderação tratar uma foto pública ou a biografia sem conceder edição irrestrita do perfil. Administradores e Moderadores possuem as permissões `remove_photo` e `edit_bio` por padrão; outros membros precisam de autorização operacional explícita. As permissões são validadas no backend para cada ação.

Toda intervenção exige uma **origem já registrada**, vinculada à pessoa atendida no mesmo evento:

- uma denúncia recebida por esse participante; ou
- um chamado/conversa de Suporte aberto pelo participante.

Não basta informar um motivo solto: a origem deve ser selecionada no formulário e validada pelo sistema. Se não existir denúncia ou atendimento relacionado, é necessário registrar o contexto adequado antes de intervir; não pode ser utilizada uma ocorrência de outra pessoa ou evento.

Fluxo operacional:

1. Abrir a ficha e acessar **Intervenção no perfil**.
2. Em **Origem**, selecionar a denúncia ou atendimento relacionado.
3. Em **Ação**, escolher **Remover foto pública** ou **Editar descrição**.
4. Para remoção, selecionar uma das fotos públicas atuais e conferir sua prévia. Para edição, preencher a descrição com **50 a 200 caracteres**; o backend valida o texto sem espaços nas extremidades.
5. Preencher **Motivo** com a justificativa da intervenção (até 4.000 caracteres).
6. Selecionar **Revisar intervenção**, conferir o aviso e então **Confirmar intervenção**.

Na **remoção de foto pública**, a imagem deixa de estar disponível no perfil, mas seu registro é preservado no histórico restrito. O participante é desativado para revisão, com situação Inativo e motivo `PHOTO_REVIEW`. Ele deve enviar uma foto substituta e obter nova ativação após cumprir os requisitos. Não é permitido reativar com menos de 3 fotos públicas válidas.

Na **edição da biografia**, o texto é atualizado após validação do limite de 50 a 200 caracteres; essa ação, por si só, não desativa nem reativa o perfil. Ambas as ações notificam o participante e registram responsável, momento, evento, motivo, tipo e identificador da origem, além do texto anterior ou da referência à foto. Os registros de auditoria são `profile.remove_photo` e `profile.edit_bio`.

Intervenções de escrita não são permitidas após o evento ser Encerrado ou Arquivado. A consulta à origem da intervenção não autoriza acesso geral às mensagens privadas do participante.

### 11.3 Exceção temporária de localização por falha técnica

Nos eventos Presenciais ou Híbridos, o gestor ou membro autorizado com a permissão `location_exception` pode conceder uma **exceção temporária de GPS**. Administradores e Moderadores possuem essa permissão por padrão; Operadores não a possuem por padrão. O recurso não é utilizado em eventos Online.

A exceção se aplica exclusivamente ao participante cujo motivo de desativação seja **`GPS_TECHNICAL`**, registrado pelo fluxo de falha técnica de localização. Ela não é um meio de contornar banimento, suspensão, remoção de foto ou outros requisitos de ativação, nem remove essas restrições.

Fluxo na seção **Ativação e presença**:

1. Localizar o participante com falha técnica e abrir sua ficha no evento correto.
2. Preencher **Motivo da intervenção ou consulta**, justificando a necessidade da exceção.
3. Selecionar **Ignorar verificação temporariamente** para abrir o diálogo **Exceção de localização**.
4. Em **Duração da exceção (minutos)**, informar **X minutos**, como número inteiro positivo. Não existe uma duração fixa para todos os atendimentos.
5. Conferir o aviso de que o participante ficará ativo durante esse período mesmo sem nova validação de localização e selecionar **Reativar temporariamente**, ou **Cancelar**.

O sistema valida o evento, a permissão, o motivo, a duração e a condição `GPS_TECHNICAL`. Em seguida, reativa temporariamente a participação, calcula o término da exceção a partir do momento da concessão e cria um registro de exceção com responsável, justificativa e expiração. A auditoria recebe `location.exception`, incluindo a duração, e o participante é notificado. Sua tentativa manual de validar o GPS permanece disponível.

Ao expirar o período, a rotina de manutenção encerra a exceção e registra `location.exception_expired`. Se o motivo continuar sendo `GPS_TECHNICAL`, o perfil volta a ficar Inativo e o participante é notificado para validar a localização ou procurar a equipe. Uma validação de GPS bem-sucedida pode resolver a falha técnica antes disso, sem exigir que a exceção se torne permanente.

A concessão da exceção não exige consultar o histórico individual de localização. Essa consulta tem regras próprias de acesso, estado do evento e auditoria; não se deve confundir a permissão de conceder exceção com a autorização para investigar o histórico. Não são concedidas novas exceções em eventos Encerrados ou Arquivados.

## 12. Suspensão

A suspensão é uma restrição administrativa temporária.

Fluxo:

Detalhes do participante
→ Suspender do evento
→ Selecionar motivo
→ Inserir observação
→ Confirmar
→ Registrar ação em auditoria

Tela de confirmação conceitual:

Suspender participante?

Camila Souza perderá temporariamente o acesso às funcionalidades deste evento.

Motivo da suspensão
[Selecionar motivo]

Observação
[Descreva o ocorrido...]

Cancelar | Confirmar suspensão

Após a ação, a ficha deverá indicar:

Suspenso

Motivo: comportamento inadequado
Por: Ana Carolina — Moderadora
Hoje • 20:37

Quando permitido, poderá existir:

Reativar participante

Toda alteração deve ser auditável.

## 13. Banimento ou remoção do evento

Banimento/remoção é uma ação administrativa mais grave e não deve estar disponível para qualquer funcionário.

Fluxo:

Detalhes do participante
→ Remover acesso ao evento
→ Motivo
→ Observação
→ Confirmação explícita
→ EventBan
→ Auditoria

Após a ação:

Acesso removido

Este participante não pode mais utilizar este evento.

Motivo: assédio/comportamento inadequado
Decisão: Marcos Viana — Administrador
03/10/2026 • 21:03

Ação disponível:

Ver histórico da decisão

A decisão deve possuir contexto e rastreabilidade, não apenas um estado booleano sem histórico.

## 14. Papéis e permissões

Modelo conceitual inicial:

| Papel | Consultar participantes | Ocorrências | Suspender | Banir |
| --- | --- | --- | --- | --- |
| Operador | Sim | Não | Não | Não |
| Moderador | Sim | Sim | Sim | Não |
| Administrador | Sim | Sim | Sim | Sim |

Esta matriz é preliminar.

As permissões definitivas serão especificadas no fluxo de Equipe e Permissões.

Todas as permissões devem ser validadas no backend.

## 15. Estados administrativos do participante

Estados conceituais:

Cadastro incompleto
→ Ativo
→ Suspenso
→ Banido

### Cadastro incompleto

O participante iniciou o ingresso no evento, por exemplo pelo QR Code, mas ainda não cumpriu todos os requisitos necessários para ativação do perfil.

### Ativo

Participação válida e acesso normal às funcionalidades permitidas.

### Suspenso

Acesso temporariamente restringido por ação administrativa.

### Banido

Acesso ao evento removido por decisão administrativa.

“Offline” e “online” representam atividade e não devem ser confundidos com suspensão, banimento ou desativação operacional do perfil.

Nos fluxos implementados, a situação **Inativo** também pode indicar desativação operacional: `PHOTO_REVIEW` após remoção de foto pública ou `GPS_TECHNICAL` por falha técnica de localização. O motivo deve ser consultado antes de escolher a tratativa. Estar offline, por si só, não equivale a esses motivos nem justifica uma exceção de GPS.

## 16. Novos cadastros durante o evento

Durante o evento, novos participantes que ingressarem pelo QR Code e concluírem o cadastro devem aparecer rapidamente na lista.

O contador geral deve ser atualizado:

Participantes 284 → 285

A área Novos deve refletir os ingressos recentes.

Não é necessário gerar uma notificação ostensiva para cada novo cadastro, principalmente em eventos de grande porte.

Notificações de maior destaque devem ser reservadas para acontecimentos que exigem atenção, especialmente Moderação.

## 17. Privacidade e LGPD

Princípio funcional:

Ter acesso administrativo ao evento não significa ter acesso irrestrito aos dados pessoais e sociais dos participantes.

As telas devem exibir somente informações necessárias para:
- operação;
- atendimento;
- segurança;
- moderação;
- cumprimento das responsabilidades administrativas autorizadas.

O acesso deve respeitar:
- papel do funcionário;
- vínculo com o evento;
- finalidade da informação;
- política de retenção;
- auditoria;
- demais regras de proteção de dados definidas pelo projeto.

Isso também reduz o risco de abuso interno por funcionários do evento.

## 18. Estrutura visual conceitual

    ┌────────────────────────────┐
    │ Participantes          ⚙   │
    │ 284 cadastrados            │
    │                            │
    │ Buscar participantes       │
    │                            │
    │ [Todos 284] [Ativos 173]   │
    │ [Novos 38]                 │
    │                            │
    │ ● Camila Souza, 28         │
    │   Designer de Produto      │
    │   Online agora           > │
    │                            │
    │ ● Lucas Oliveira, 32       │
    │   Desenvolvedor            │
    │   Há 5 min               > │
    │                            │
    │ ! Rafael Costa, 30         │
    │   Empresário               │
    │   Ocorrência pendente    > │
    │                            │
    │ ○ Aline Martins, 27        │
    │   Consultora               │
    │   Há 18 min              > │
    ├────────────────────────────┤
    │ Início Pessoas Mod. Evento │
    │                      Mais  │
    └────────────────────────────┘

## 19. Telas previstas

O fluxo Participantes deverá resultar inicialmente nas seguintes telas/estados:

1. Lista de participantes;
2. filtros de participantes;
3. detalhes do participante — Informações;
4. detalhes do participante — Ocorrências;
5. confirmação de suspensão;
6. participante suspenso;
7. confirmação de banimento/remoção;
8. participante banido;
9. cadastro incompleto;
10. estados vazios e ausência de resultados;
11. captura de outfit com prévia, nova captura e envio;
12. intervenção no perfil com origem, ação, motivo e confirmação;
13. exceção temporária de localização com justificativa e duração em minutos.

Detalhes de denúncias e investigação pertencem ao documento específico de Moderação.

## 20. Diretrizes para desenvolvimento

- Mobile-first.
- Reutilizar a identidade visual da área administrativa.
- Manter EventParticipant como referência operacional do evento.
- Separar estado administrativo de estado de atividade.
- Separar Block de Suspension/EventBan.
- Não expor informações sociais desnecessárias.
- Não permitir ações administrativas apenas por controle visual do frontend.
- Registrar ações sensíveis em auditoria.
- Exigir motivo e contexto para sanções.
- Direcionar investigação detalhada para Moderação.
- Preparar a estrutura para permissões diferentes entre Administrador, Moderador e Operador.

Este documento deve permanecer como referência funcional para o desenvolvimento das telas administrativas de Participantes.

## Matriz de permissões — definição atual

Administrador Global é o usuário com Status de superusuário ativo no Django. O acesso ao Django Admin usa a flag Membro da equipe; essa flag não equivale a Administrador Global. Papéis do evento não concedem automaticamente essas flags globais.

Administrador do Evento pode gerenciar Moderadores e Operadores do próprio evento, conceder ou revogar permissões operacionais, acessar métricas e relatórios e delegar temporariamente a administração somente a um Moderador, podendo retomá-la depois. Delegação e retomada são auditadas e notificadas ao Administrador Global.

As permissões delegáveis se limitam a tratativas do evento: denúncias, bloqueios e desbloqueios; venda, concessão e revogação de passes; ativação/desativação de perfil; captura de foto de ativação; remoção de foto; e edição de bio quando necessária à tratativa. Não abrangem administração global ou funções técnicas.

Moderador possui praticamente o mesmo domínio operacional de tratativas do Administrador do Evento, conforme permissões recebidas, mas não altera equipe/permissões e não acessa métricas ou relatórios. Pode receber a administração temporária.

Operador é o principal responsável pela captura da foto de outfit e ativação operacional do perfil, pode disponibilizar o QR Code do evento e abrir ocorrência administrativa ligada ao participante, como passe que não vigorou ou ajuda/falha ao editar o próprio perfil. Abrir ocorrência não concede poderes de moderação.

Intervenções em foto, bio ou conteúdo do perfil precisam de origem auditável. Quando decorrentes de denúncia, devem ser vinculadas à denúncia. O participante também poderá solicitar suporte dentro da tela de Mensagens; intervenções decorrentes desse atendimento devem ser vinculadas à solicitação/conversa de suporte.

Mudanças de equipe, grupos, permissões, delegação/retomada, decisões de moderação e intervenções sobre perfil devem ser auditáveis.

## Perfil, fotos e visibilidade

A ativação exige bio de 50 a 200 caracteres e 3 fotos públicas válidas, sendo uma principal. Após ativado, o participante não pode remover ou substituir essas fotos diretamente. No fluxo manual, a foto de outfit também é obrigatória e é capturada pela equipe autorizada, especialmente Operador/Moderador, antes de ativar o perfil. Eventos Online dispensam GPS; quando a ativação automática está habilitada, também dispensam outfit, conforme a seção 11.1.

Antes do Match, ficam visíveis as 3 fotos públicas. Após o Match, as demais fotos ficam disponíveis e a foto de outfit, quando houver, aparece destacada em primeiro lugar.

Se a moderação remover uma foto pública, o perfil é desativado por deixar de cumprir o mínimo de 3 fotos. O participante deve adicionar outra foto e solicitar reativação junto à moderação. A tratativa também pode ocorrer pelo chat de Suporte, vinculando solicitação, análise e reativação ao atendimento e à auditoria. Nenhum perfil pode ser reativado com menos de 3 fotos públicas válidas.

O evento pode definir campos adicionais do participante como obrigatórios ou opcionais para ativação. A configuração é escolha da organização e deve ser concluída antes da abertura do evento. Esses campos podem representar aceite de termos próprios do evento, consentimentos ou listas de itens/opções para marcação. Campos obrigatórios precisam estar satisfeitos para o participante ficar ativo; opcionais não impedem a ativação. Termos e consentimentos devem manter registro versionado e auditável do conteúdo/versão apresentado e da manifestação do participante.

## Bloqueio, denúncia e segurança entre eventos

O botão Denunciar permanece disponível no perfil da Descoberta, inclusive no perfil público expandido, e nas Mensagens mesmo quando o outro participante já estiver anonimizado. Toda denúncia exige relato textual e pode indicar uma ou mais fotos, mensagem ou outro contexto. Se a foto já tiver sido alterada, o denunciante pode informar isso e procurar a moderação para descrevê-la. Fotos removidas ou substituídas permanecem vinculadas historicamente ao perfil para auditoria, respeitando posteriormente as regras de retenção e eliminação.

Motivos pré-definidos incluem ofensa/ameaça/assédio, importunação ou comportamento sexual indesejado, nudez ou conteúdo sexual explícito, racismo/discriminação, discurso de ódio, violência/ameaça, fraude/golpe, uso indevido de imagem ou identidade, conteúdo ou comportamento possivelmente ilegal e Outro. O sistema não faz classificação jurídica definitiva.

Múltiplos bloqueios não geram alerta automático. Com denúncias relevantes de **10 denunciantes distintos no mesmo evento**, Administradores e Moderadores ativos recebem alerta com acesso à ficha do participante. Denúncias infundadas, ocorrências administrativas e duplicatas do mesmo denunciante não aumentam a contagem. O alerta não aplica sanção automática nesse primeiro limiar.

Com **20 denunciantes distintos** pelos mesmos critérios, o perfil é desativado automaticamente para análise com motivo `REPORT_REVIEW`; o participante e a Administração Global são notificados. Isso não equivale a banimento. Invalidar uma denúncia não reativa automaticamente o perfil: a moderação deve avaliar e executar a tratativa adequada. Consulte a seção 22 do [Fluxo de Moderação](<Fluxo - Administração - Moderação.md>).

O histórico de denúncias fica vinculado ao perfil global. A Administração Global pode marcar manualmente o perfil como Denunciado recorrente. Quando esse participante ingressar em outro evento, a Administração Global é notificada e decide caso a caso se comunica ou não a administração do novo evento. Histórico e marcação de recorrência não produzem banimento automático em eventos futuros.
