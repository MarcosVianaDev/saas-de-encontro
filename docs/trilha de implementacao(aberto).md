Nesse nível de detalhe, a trilha deixa de ser apenas um roadmap e passa a funcionar como **backlog funcional de implementação**, em que cada item abaixo pode virar um card/issue independente para outro programador.

Vou manter a ordem da trilha anterior, mas quebrando cada etapa em **cards implementáveis**, incluindo telas, componentes, botões, estados, mensagens, automações Celery, integrações e critérios de aceite. Onde ainda existe decisão de produto pendente, marco explicitamente em vez de inventar uma regra.

# Padrão para todos os cards

Cada card deve conter, no mínimo:

**Objetivo → Interface → Backend/regra → Celery/eventos → Mensagens → Critérios de aceite.**

As telas devem seguir três contextos visuais já definidos:

- **Participante:** mobile-first, identidade roxa/lilás.
- **Administração do Evento:** responsiva, identidade roxa/lilás.
- **Administração Global:** responsiva, identidade vermelha.
- **Django Admin:** somente ferramenta técnica/interna.

Mensagens devem seguir um padrão:

- **Sucesso:** confirmar objetivamente o que aconteceu.
- **Aviso:** explicar consequência antes da ação.
- **Erro:** dizer o que falhou e, quando possível, o que fazer.
- **Bloqueio:** explicar por que a ação não está disponível.
- Nunca expor stack trace, ID interno, exceção ou informação privada de outro participante.

---

# ETAPA 1 — Consolidar domínio, banco e regras fundamentais

Esta etapa deve acontecer antes de expandir telas. O objetivo é impedir que os programadores construam funcionalidades sobre estruturas que depois precisarão ser refeitas.

## Card 1.1 — Máquina de estados do evento

### Backend

Implementar formalmente:

**Rascunho → Agendado → Aberto → Em andamento ⇄ Pausado → Encerrado → Arquivado**

Cada transição deve passar por serviço de domínio único, independentemente de ter sido solicitada pela API, Celery ou Administração Global.

Registrar em auditoria:

- estado anterior;
- novo estado;
- data/hora;
- automático ou manual;
- usuário responsável, quando manual;
- justificativa quando aplicável.

### Interface

Na tela **Evento**, colocar no topo:

**Nome do evento**  
`Status: Em andamento`

Logo abaixo, uma linha temporal simplificada do ciclo.

A ação principal fica no canto superior direito em desktop e abaixo do cabeçalho em mobile.

Exemplos:

`Abrir evento`  
`Iniciar evento`  
`Pausar evento`  
`Retomar evento`  
`Encerrar evento`

Não mostrar ações impossíveis no estado atual.

### Confirmações

**Pausar**

Título:
> Pausar evento?

Texto:
> Novas descobertas e interações serão temporariamente interrompidas. Matches e conversas existentes continuarão disponíveis. O horário de encerramento do evento não será alterado.

Botões:

`Cancelar` | `Pausar evento`

**Encerrar antecipadamente**

Título:
> Encerrar evento antes do horário?

Texto:
> Esta ação encerra novas descobertas, likes, matches e mensagens. Os participantes serão notificados. O evento não poderá voltar para “Em andamento”.

Campo:

`Motivo do encerramento`

Depois, CAPTCHA simples conforme escopo.

Botões:

`Cancelar` | `Encerrar evento`

### Celery

Criar tarefas conceituais:

- verificar eventos que devem iniciar;
- encerrar eventos que chegaram ao horário final;
- arquivar eventos 15 dias depois do encerramento.

Toda tarefa deve chamar o mesmo serviço de transição utilizado pela interface.

**Nunca duplicar regra de negócio dentro da task.**

### Aceite

Uma transição executada manualmente e uma executada pelo Celery devem produzir exatamente os mesmos efeitos colaterais, exceto identificação do ator.

---

## Card 1.2 — Configurações e bloqueio progressivo do evento

Criar estrutura de configuração com campos classificados por momento em que ainda podem ser alterados.

### Tela

**Evento → Configurações**

Separar em seções:

**Informações gerais**  
**Datas e horários**  
**Localização**  
**Participantes e ativação**  
**Passes**  
**Notificações**  
**Privacidade e retenção**

Botão principal:

`Salvar alterações`

Posição: canto inferior direito da área editável; em mobile, botão fixo inferior somente quando houver alteração não salva.

Campos bloqueados aparecem desabilitados, mas continuam visíveis.

Texto auxiliar:

> Esta configuração não pode mais ser alterada porque o evento já está em andamento.

### Confirmação de alterações sensíveis

> O evento já foi agendado. Alterar esta configuração pode afetar participantes já cadastrados.

Botões:

`Voltar` | `Confirmar alteração`

---

## Card 1.3 — Estrutura definitiva do participante no evento

Centralizar a operação em `EventParticipant`.

Estados mínimos:

- cadastro incompleto;
- aguardando ativação;
- ativo;
- desativado;
- suspenso;
- banido;
- evento encerrado.

Separar:

**estado da conta global ≠ estado da participação ≠ presença/localização ≠ sanção administrativa.**

Isso é crítico para as etapas seguintes.

---

## Card 1.4 — Serviço central de auditoria

Toda operação sensível deve utilizar um mecanismo único de auditoria.

Cobrir:

- mudanças de evento;
- permissões;
- moderação;
- fotos;
- perfil;
- passes;
- geolocalização administrativa;
- Legal Hold;
- retenção;
- exportações;
- intervenções de suporte;
- administração global.

O registro deve ser append-only.

Falha de auditoria em operação que obrigatoriamente precisa ser auditada deve impedir a operação.

Mensagem:

> Não foi possível concluir a operação com segurança. Tente novamente.

---

# ETAPA 2 — Identidade, permissões e Administração Global

## Card 2.1 — Roteamento após login

Após autenticação, o sistema determina os contextos disponíveis.

Exemplos:

Participante em um evento → experiência participante.

Administrador de evento → opção de administração daquele evento.

`is_superuser` → Administração Global.

Um usuário pode possuir vários contextos simultaneamente.

### Tela de seleção quando necessário

Título:

> Onde você deseja entrar?

Cards:

**Evento X**  
`Participar`

**Evento X — Administração**  
`Administrar`

**Administração Global**  
`Acessar`

Não criar contas diferentes por papel.

---

## Card 2.2 — Administração Global: estrutura principal

Menu inferior/mobile ou lateral/desktop:

**Início | Clientes | Eventos | Mais**

Identidade visual vermelha.

### Dashboard

Cards:

- eventos em andamento;
- eventos agendados;
- eventos pausados;
- denúncias críticas;
- clientes ativos;
- ocorrências que exigem atenção.

Abaixo:

**Eventos recentes**

**Alertas do sistema**

**Atividade administrativa**

Botão principal superior:

`+ Novo cliente`

---

## Card 2.3 — Cadastro guiado de cliente

Fluxo:

**Contato → Organização → Evento → Responsáveis → Revisão → Ativação**

Botões inferiores:

`Voltar` | `Salvar e continuar`

Na última etapa:

`Ativar cliente e evento`

Se sair:

> Existem alterações não salvas. Deseja sair mesmo assim?

`Continuar editando` | `Sair sem salvar`

---

## Card 2.4 — Administração Global entrando em um evento

Ao selecionar:

`Administrar evento`

Abrir exatamente a interface normal de Administração do Evento.

Diferença visual: elementos contextuais vermelhos em vez de lilás.

Topo:

`← Voltar à Administração Global`

Não escrever permanentemente “você é administrador global”.

---

## Card 2.5 — Equipe e permissões

Tela:

**Evento → Mais → Equipe e Permissões**

Lista:

Nome | Papel | Permissões adicionais | Status | Ações

Botão:

`+ Adicionar integrante`

### Modal

Campos:

- usuário;
- papel;
- permissões operacionais.

Papéis:

- Administrador do Evento;
- Moderador;
- Operador.

O Administrador pode delegar somente permissões operacionais aprovadas.

### Transferência temporária

Botão no Administrador:

`Transferir administração`

Somente Moderadores existentes aparecem como destino.

Confirmação:

> Transferir temporariamente a administração deste evento para [nome]?

> Você continuará vinculado ao evento e poderá reassumir a administração posteriormente.

`Cancelar` | `Transferir`

Auditar e notificar Administração Global.

---

# ETAPA 3 — Ciclo operacional completo do evento

## Card 3.1 — Dashboard do evento

Pergunta que a tela precisa responder:

> O que está acontecendo no meu evento agora e o que exige minha atenção?

Topo:

Nome + status + horário.

Cards principais:

- participantes;
- ativos/recentes;
- matches;
- conversas;
- denúncias pendentes;
- denúncias em análise.

Se houver algo crítico:

**Atenção necessária**

Cards clicáveis levando diretamente ao contexto.

Bottom navigation:

**Dashboard | Participantes | Moderação | Evento | Mais**

---

## Card 3.2 — Estado Aberto

Participantes podem:

- entrar;
- concluir cadastro;
- ativar participação;
- validar requisitos.

Ainda não podem utilizar Discovery social.

Tela de Discovery:

> O evento ainda não começou

> Seu perfil está pronto. A descoberta de participantes será liberada quando o evento começar.

Botão:

`Ver meu perfil`

---

## Card 3.3 — Início automático

Celery verifica `starts_at`.

Quando alcançado:

`Aberto → Em andamento`

Efeitos:

- liberar Discovery;
- liberar interações;
- registrar auditoria;
- criar notificações.

Participante:

Título:
> O evento começou

Texto:
> A descoberta de participantes já está disponível.

Ação:

`Explorar participantes`

---

## Card 3.4 — Pausa operacional

Ao pausar:

- Discovery indisponível;
- lista normal de participantes indisponível;
- likes novos impedidos;
- matches/conversas existentes continuam;
- mensagens continuam;
- relógio do evento continua.

Banner persistente:

> Evento pausado pela organização

> Novas descobertas estão temporariamente indisponíveis. Suas conversas e matches continuam acessíveis.

Botão opcional:

`Ir para mensagens`

---

## Card 3.5 — Encerramento

Ao encerrar:

- Discovery bloqueado;
- filtros bloqueados;
- mensagens somente leitura;
- perfil somente leitura;
- novos likes/matches proibidos.

Banner:

> Este evento foi encerrado

Na área de perfil:

**O que deseja fazer com seu perfil?**

`Salvar perfil para futuros eventos`

`Excluir perfil deste evento`

Ao excluir:

> Seu perfil deixará de aparecer socialmente. Dados sujeitos a obrigações legais, segurança ou preservação poderão permanecer pelo período aplicável.

`Cancelar` | `Solicitar exclusão`

---

## Card 3.6 — Arquivamento automático

Celery agenda/identifica:

`closed_at + 15 dias`

Transição:

`Encerrado → Arquivado`

Notificar:

- Administrador Global;
- Administrador responsável.

Mensagem:

> O evento “[nome]” foi arquivado.

> Os dados operacionais passaram para modo somente leitura.

---

# ETAPA 4 — Experiência completa do participante

## Card 4.1 — Onboarding por evento

Cinco passos somente no primeiro ingresso daquele evento.

Barra:

`1 de 5`

Botões inferiores:

`Voltar` | `Continuar`

Último:

`Enviar para ativação`

Reutilizar dados globais elegíveis.

Nunca obrigar participante a refazer onboarding completo apenas para editar perfil.

---

## Card 4.2 — Fotos públicas obrigatórias

Tela:

**Suas fotos**

Três slots obrigatórios destacados:

`Foto pública 1`  
`Foto pública 2`  
`Foto pública 3`

Texto:

> Adicione 3 fotos públicas para ativar seu perfil.

Antes da ativação:

`Trocar foto`

Depois da ativação, participante não pode alterá-las.

Texto:

> Esta foto faz parte do perfil aprovado para este evento e não pode ser alterada diretamente.

Intervenção administrativa fica auditada.

---

## Card 4.3 — Outfit

Área administrativa/operacional.

Participante não envia a própria foto de outfit.

Operador:

**Participante → Ativação → Foto do look**

Botão:

`Capturar foto`

Depois:

`Usar esta foto` | `Tirar novamente`

Após Match, outfit aparece primeiro para o outro participante.

---

## Card 4.4 — Discovery

Card central:

foto → nome → informações públicas essenciais.

Topo esquerdo do perfil:

`Denunciar`

Topo direito:

`ⓘ`

Parte inferior:

`Passar` | `Curtir`

O botão de informações expande o perfil, mas `Denunciar` continua acessível.

Não colocar Favoritar aqui.

---

## Card 4.5 — Match

Modal:

> É um Match!

> Você e [nome] curtiram um ao outro.

Botões:

`Continuar explorando`

`Enviar mensagem`

Após Match, liberar informações/fotos definidas para pós-match.

---

## Card 4.6 — Conversa

Topo:

foto + nome + menu `⋮`.

Menu:

`Ver perfil`  
`Favoritar`  
`Bloquear`  
`Denunciar`

Campo inferior:

`Escreva uma mensagem...`

Botão à direita:

`Enviar`

Evento encerrado:

campo desaparece.

Texto:

> Este evento terminou. A conversa está disponível somente para consulta.

---

# ETAPA 5 — Denúncias, bloqueios e moderação

## Card 5.1 — Bloquear participante

Confirmação:

> Bloquear [nome]?

> Vocês deixarão de aparecer um para o outro neste evento. O bloqueio não poderá ser desfeito pelo participante.

Campo:

`Motivo`

Botões:

`Cancelar` | `Bloquear`

Após:

> Participante bloqueado.

Nenhum alerta automático deve ser criado apenas por acumulação de bloqueios.

---

## Card 5.2 — Denunciar participante

Tela/modal:

**Denunciar participante**

`Selecione um ou mais motivos`

Motivos aprovados no escopo.

Depois:

`Conte o que aconteceu`

Campo obrigatório.

Se houver conteúdo relacionado:

**Adicionar evidência**

- selecionar foto;
- selecionar mensagem;
- outro contexto.

Checkbox:

`A foto relacionada já foi alterada ou removida`

Texto:

> Nesse caso, procure também a moderação do evento. O histórico poderá ser analisado pela equipe autorizada.

Botões:

`Cancelar` | `Enviar denúncia`

Sucesso:

> Denúncia enviada.

> A equipe responsável poderá analisar o caso. Você não receberá automaticamente detalhes de medidas tomadas contra outra pessoa.

---

## Card 5.3 — Fila de moderação

Abas:

**Pendentes | Em análise | Resolvidas**

Cada card:

- participante denunciado;
- motivos;
- quantidade de denúncias relevantes;
- horário;
- responsável atual;
- prioridade.

Clique → detalhes.

---

## Card 5.4 — Investigação

Tela:

**Resumo**  
**Denúncias**  
**Evidências**  
**Histórico**  
**Notas**

Botão:

`Assumir caso`

Depois:

`Adicionar nota`

Ações:

`Arquivar sem ação`  
`Suspender participante`  
`Banir do evento`

Todas exigem confirmação.

---

## Card 5.5 — Limite de 10 denúncias

Somente denúncias ainda consideradas relevantes.

Gerar alerta:

> Participante [identificação] recebeu 10 denúncias relevantes. Clique para revisar.

Botão:

`Revisar participante`

Não desativar automaticamente.

---

## Card 5.6 — Limite de 20 denúncias

Ao alcançar 20:

- desativar perfil automaticamente para análise;
- abrir/sinalizar caso;
- notificar Administração Global.

Participante:

> Seu perfil está temporariamente em análise

> Algumas funções foram desativadas enquanto a equipe responsável analisa uma ocorrência.

Botão:

`Falar com o suporte`

---

# ETAPA 6 — Passes e operação financeira do MVP

## Card 6.1 — Likes recebidos

Filtro:

`Likes recebidos`

Sem passe:

mostrar quantidade, mas não identidades.

Card bloqueado:

🔒 visual, sem fotografia identificável.

Texto:

> Você recebeu 8 likes.

> Adquira um passe para revelar quem curtiu você.

Botão:

`Adquirir novo passe`

---

## Card 6.2 — Seleção de passe

Tela:

**Passes disponíveis**

Cards:

**10 revelações**  
`Revela até 10 pessoas`

ou:

**Passe por tempo**  
`Revela likes durante o período de validade`

Botão:

`Selecionar`

Se aquisição for no balcão:

> Procure o atendimento do evento para ativar este passe.

---

## Card 6.3 — Concessão pelo Operador

Ficha do participante:

**Passes**

Botão:

`Conceder passe`

Modal:

- oferta;
- origem;
- observação/referência.

Botão:

`Confirmar concessão`

Sucesso:

> Passe ativado para o participante.

Auditar operador, participante, oferta, horário e origem.

---

## Card 6.4 — Consumo por quantidade

Ao revelar:

sempre selecionar o **Like oculto mais antigo**.

Confirmação opcional antes de consumir:

> Revelar esta pessoa utilizará 1 revelação do seu passe.

`Cancelar` | `Revelar`

Após:

> Pessoa revelada. Restam 7 revelações.

Operação precisa ser atômica.

---

## Card 6.5 — Expiração

Celery verifica passes temporais vencidos.

Ao expirar:

- não apagar likes;
- apenas voltar a ocultar o que não estiver permanentemente revelado conforme regra do passe;
- gerar notificação.

> Seu passe expirou

> Seus likes continuam salvos. Você pode adquirir outro passe para revelar os que permanecem ocultos.

Botão:

`Ver passes`

---

# ETAPA 7 — Geolocalização

## Card 7.1 — Solicitação inicial

Tela:

**Permitir localização**

Texto:

> A localização é usada para validar sua presença no evento e aplicar regras de segurança. O sistema não precisa exibir sua posição exata para outros participantes.

Botão principal:

`Permitir localização`

Secundário:

`Agora não`

Se negar, Discovery permanece indisponível.

---

## Card 7.2 — Classificação de presença

Três zonas internas:

1. dentro do raio → presente;
2. fora do raio, dentro da tolerância → temporariamente fora;
3. além do limite máximo → possível anomalia.

Não mostrar distância exata para outros participantes.

---

## Card 7.3 — Falha técnica

Primeira falha inicia cinco retentativas.

Celery não é adequado para comandar cada leitura GPS do navegador; a leitura depende do cliente. O backend registra os resultados e controla o estado. Celery pode supervisionar prazos e identificar participantes que não recuperaram validação.

Retentativas do cliente:

5 × intervalo de 1 minuto.

Banner:

> Não foi possível confirmar sua localização.

> Verifique sua conexão e as permissões de localização.

Botão:

`Verificar agora`

---

## Card 7.4 — Falha persistente

Depois das cinco tentativas, manter banner e tentativa manual.

Se chegar a próxima verificação periódica e continuar impossível:

desativação técnica.

Mensagem:

> Não conseguimos validar sua localização

> Seu perfil foi temporariamente desativado. Você pode tentar novamente ou procurar a equipe do evento.

Botões:

`Tentar novamente`  
`Falar com a equipe`

Não registrar como punição.

---

## Card 7.5 — Exceção pelo Moderador

Na ficha operacional:

`Ignorar verificação temporariamente`

Modal:

**Duração da exceção**

`___ minutos`

**Motivo**

Botão:

`Reativar temporariamente`

Confirmação:

> O participante permanecerá ativo durante o período definido mesmo sem uma nova validação de localização.

Auditar tudo.

---

## Card 7.6 — Anomalias

Calcular:

distância entre medições ÷ tempo.

Acima de 60 km/h → sinal de anomalia.

Duas medições válidas além de:

`raio + tolerância`

→ sinal confirmado pelo critério de afastamento.

**Não aplicar punição automática.**

Permanece uma decisão pendente do produto: se um único par acima de 60 km/h deve gerar imediatamente alerta visível aos gestores ou somente sinal interno para posterior confirmação.

---

## Card 7.7 — Histórico restrito

Somente:

- Administrador Global;
- Administrador responsável pelo evento.

E somente quando permitido pelo estado:

- Pausado;
- Encerrado;
- Arquivado.

Em andamento:

> O histórico de localização não pode ser consultado enquanto o evento está em andamento. Pause o evento para iniciar uma investigação que exija esse acesso.

Toda consulta exige motivo e auditoria.

---

# ETAPA 8 — Mensagens, notificações, avisos e Celery

## Card 8.1 — Central unificada

Tela:

**Mensagens | Notificações**

Toggle no topo.

O ícone/menu de Mensagens deve sinalizar existência de qualquer item não lido das duas categorias.

---

## Card 8.2 — Notificações internas

Criar eventos de domínio para:

- Like recebido;
- Match;
- suporte;
- passe expirado;
- aviso do evento;
- perfil em análise;
- reativação;
- alterações relevantes do evento.

Notificações devem ser persistidas, não somente enviadas via WebSocket.

WebSocket apenas entrega atualização em tempo real.

---

## Card 8.3 — Avisos do Evento

Área de Moderador:

**Avisos do Evento**

Abas:

`Todos | Rascunhos | Agendados | Enviados`

Botão superior:

`+ Novo aviso`

Editor:

**Título**

**Mensagem**

**Link opcional**

Escolha:

`Enviar agora`  
`Agendar`

Botões:

`Salvar rascunho` | `Continuar`

---

## Card 8.4 — Confirmação de envio

> Enviar este aviso para os participantes do evento?

Mostrar prévia.

`Voltar` | `Enviar aviso`

Sucesso:

> Aviso enviado.

---

## Card 8.5 — Agendamento

Se horário estiver nos últimos 30 minutos do evento:

> Este aviso está agendado próximo ao encerramento do evento. Ele poderá não ser enviado caso o evento seja encerrado ou esteja em um estado que impeça o disparo.

`Voltar` | `Agendar mesmo assim`

Não permitir depois de `ends_at`.

---

## Card 8.6 — Celery para aviso agendado

No momento previsto:

**Aberto** → enviar.  
**Em andamento** → enviar.  
**Pausado** → não enviar automaticamente; notificar responsável.  
**Encerrado** → não enviar.  
**Arquivado** → não enviar.

Pausado:

> O aviso “[título]” não foi enviado porque o evento está pausado.

Botão administrativo:

`Enviar manualmente`

Encerrado:

> O aviso “[título]” não foi enviado porque o evento foi encerrado.

Sem botão de envio.

---

# ETAPA 9 — LGPD operacional

## Card 9.1 — Privacidade e Dados

Área independente de evento ativo.

Menu do usuário:

`Privacidade e Dados`

Opções:

- acessar dados;
- corrigir dados;
- solicitar exclusão;
- revogar consentimento;
- informações sobre compartilhamento;
- demais direitos aplicáveis.

Botão:

`Nova solicitação`

---

## Card 9.2 — Solicitação de privacidade

Wizard curto:

**O que você deseja solicitar?**

Depois:

**Detalhes da solicitação**

Botão:

`Enviar solicitação`

Sucesso:

> Solicitação recebida.

> Protocolo: [código]

> Você poderá acompanhar o andamento nesta página.

---

## Card 9.3 — Consentimentos

Registrar:

- versão;
- finalidade;
- texto/documento;
- manifestação;
- data;
- revogação.

Nunca sobrescrever consentimento antigo.

Novo termo gera nova versão.

---

## Card 9.4 — Legal Hold

Somente usuários autorizados.

Tela:

**Preservação legal**

Campos:

- motivo;
- fundamento;
- evento;
- participantes;
- categorias;
- referência documental/processual;
- condição de revisão.

Botão:

`Aplicar preservação`

Confirmação forte:

> Os dados selecionados deixarão de seguir a rotina normal de eliminação enquanto esta preservação estiver ativa.

`Cancelar` | `Aplicar Legal Hold`

---

## Card 9.5 — Motor de retenção

Celery periódico identifica registros cujo prazo terminou.

Fluxo:

**selecionar → verificar Legal Hold → determinar destino → excluir/anonimizar → registrar evidência**

Nunca eliminar automaticamente categoria cujo prazo ainda esteja marcado como **“a validar juridicamente”**.

Esse estado deve impedir execução:

> Política de retenção não definida. Nenhum dado foi eliminado.

---

## Card 9.6 — Geolocalização e LGPD

Manter categoria própria.

O prazo permanece **pendente de validação antes do lançamento**.

Portanto, desenvolver mecanismo e configuração, mas não fixar arbitrariamente um período definitivo.

---

# ETAPA 10 — Arquivamento e exportação

## Card 10.1 — Evento arquivado

Interface read-only.

Topo:

> Evento arquivado

Ações permitidas conforme papel:

`Consultar métricas`

`Consultar moderação`

`Consultar auditoria`

`Exportar evento`

---

## Card 10.2 — Solicitar exportação

Somente usuário autorizado.

Modal:

> Gerar pacote de exportação deste evento?

Texto:

> A geração poderá levar alguns minutos. O pacote ficará registrado na auditoria.

`Cancelar` | `Gerar exportação`

Não tentar produzir pacote pesado dentro da requisição HTTP.

---

## Card 10.3 — Celery de exportação

API cria `ExportJob`.

Estado:

`Pendente → Processando → Concluído/Falhou`

Celery gera pacote.

Interface mostra:

> Preparando exportação...

Quando pronto:

> Exportação concluída.

Botão:

`Baixar ZIP`

Falha:

> Não foi possível gerar a exportação.

Botão:

`Tentar novamente`

---

## Card 10.4 — Estrutura do pacote

A especificação definitiva ainda precisa ser fechada, mas a direção já definida é:

- conteúdo navegável offline;
- HTML read-only;
- dados auditáveis do evento;
- evidências autorizadas;
- manifesto;
- integridade verificável;
- escopo limitado ao evento.

Não implementar formato definitivo até fecharmos conteúdo, autenticidade e procedimento de entrega jurídica.

---

# ETAPA 11 — Homologação ponta a ponta

## Card 11.1 — Evento automatizado de teste

Criar cenário reproduzível:

cliente → organização → evento → equipe → participantes → ativação → início → Discovery → Like → Match → mensagem → denúncia → passe → pausa → retomada → encerramento → arquivamento.

O cenário deve provar que o operador não precisa editar banco manualmente.

---

## Card 11.2 — Matriz de papéis

Executar o mesmo cenário como:

- participante;
- Operador;
- Moderador;
- Administrador do Evento;
- Administrador Global;
- `is_staff` sem `is_superuser`.

Verificar tanto o que cada papel **consegue fazer** quanto aquilo que **não consegue sequer consultar**.

---

## Card 11.3 — Matriz de estados

Para cada recurso:

| Recurso | Aberto | Em andamento | Pausado | Encerrado | Arquivado |
|---|---|---|---|---|---|
| Discovery | Não | Sim | Não | Não | Não |
| Conversas existentes | Conforme regra | Sim | Sim | Leitura | Consulta |
| Novos likes | Não | Sim | Não | Não | Não |
| Histórico de localização pelos gestores | Não | Não | Sim | Sim* | Sim* |
| Configuração | Restrita | Bloqueada/restrita | Bloqueada | Não | Não |

`*` sujeito à retenção/Legal Hold.

Essa matriz deve virar teste de autorização, não somente documentação.

---

# ETAPA 12 — Gate de produção

Esta etapa não cria novas funcionalidades sociais. Ela transforma o MVP homologado em algo operacionalmente seguro.

## Cards principais

- storage S3 compatível;
- mídia privada;
- URLs temporárias;
- backups;
- teste de restauração;
- TLS;
- secrets;
- produção sem DEBUG;
- política de logs;
- monitoramento;
- health checks;
- métricas;
- alertas;
- filas Celery;
- Celery Beat;
- retry/backoff;
- dead-letter/registro de falhas;
- limites de upload;
- rate limiting;
- recuperação de senha;
- e-mail transacional;
- política LGPD aprovada;
- matriz de retenção aprovada;
- revisão jurídica;
- plano de incidente;
- teste de carga;
- teste de concorrência;
- teste de segurança;
- procedimento de deploy e rollback.

---

# Arquitetura das automações Celery

Para evitar um conjunto desorganizado de tarefas, eu separaria conceitualmente as filas em:

**`events`** — início, encerramento, arquivamento e estados.  
**`notifications`** — notificações e avisos.  
**`passes`** — expiração e processamento operacional.  
**`retention`** — retenção, anonimização e eliminação.  
**`exports`** — geração de pacotes.  
**`maintenance`** — rotinas técnicas.

A regra fundamental é:

> **Celery executa trabalho assíncrono; não é o proprietário da regra de negócio.**

Por exemplo:

`Celery detecta que chegou starts_at → chama serviço EventLifecycle.start(event) → serviço valida estado → altera → audita → dispara efeitos`.

Assim, se um administrador fizer a mesma operação manualmente, usa exatamente `EventLifecycle.start(event)`.

Para ações críticas, cada job precisa ser **idempotente**. Se o Celery executar duas vezes “encerrar evento”, a segunda execução não pode duplicar notificações, auditorias, cobranças, passes ou mudanças.

---

# Padrão visual de botões

Para manter consistência entre todos esses cards:

**Ação primária:** canto inferior direito do formulário/modal ou superior direito da página quando for ação global. Exemplos: `Salvar`, `Enviar denúncia`, `Ativar evento`.

**Cancelar/Voltar:** à esquerda da ação primária.

**Ação destrutiva:** visual destrutivo e nunca como primeira ação. Exemplos: `Banir`, `Encerrar evento`, `Solicitar exclusão`.

**Ações contextuais:** menu `⋮` no canto superior direito do objeto/card.

**Participante mobile:** ação principal deve permanecer alcançável com uma mão; ações recorrentes ficam próximas à parte inferior.

**Confirmação destrutiva:** nunca utilizar somente `Sim | Não`. Os botões devem declarar a ação: `Cancelar | Banir participante`.

---

# Ordem de distribuição dos cards

Eu não abriria os 50+ cards simultaneamente para desenvolvimento. A sequência de dependência deve ser:

**Fundação de domínio → permissões → ciclo do evento → participante → segurança/moderação → passes → geolocalização → notificações/Celery → LGPD → arquivamento → homologação → produção.**

Dentro de cada etapa, **backend/regra e contrato funcional vêm antes da tela que depende deles**.

Isso cria um marco importante: ao concluir **Etapas 1–4**, já devemos conseguir simular tecnicamente um evento social básico. Ao concluir **1–8**, teremos o primeiro MVP operacional sério. **9–11** transformam esse MVP em candidato a homologação. **12** é o gate para dados e operação reais.

O próximo documento que faz sentido produzir é um **Backlog Mestre de Implementação**, transformando exatamente essa estrutura em cards numerados (`IMP-001`, `IMP-002`...), cada um com dependências, prioridade, telas, regras, mensagens, automações e critérios de aceite. Esse documento pode então ser usado diretamente para distribuir o desenvolvimento sem exigir que cada programador reinterpretе o escopo.