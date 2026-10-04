# Fluxo - Administração - Participantes

> Status: especificação funcional prevista, ainda não implementada. Atualizado em 03/10/2026.

Fonte: [DOCX](<Fluxo - Administração - Participantes.md.docx>). Referência visual: [screen2.png](screen2.png). Guia: [Telas administrativas](<Telas administrativas.md>).

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

A nomenclatura “bloquear participante” não deve ser usada para sanções administrativas, pois Block é reservado ao relacionamento participante-participante.

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

“Inativo”, “offline” ou “online” representam atividade e não devem ser confundidos com estados administrativos.

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
10. estados vazios e ausência de resultados.

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
