# Fluxo de Administração do Evento

> Status: especificação funcional prevista, ainda não implementada. Atualizado em 03/10/2026.

Fonte: [DOCX](<Fluxo - Administração do Evento.md.docx>). Referência visual: [screen1.png](screen1.png). Guia: [Telas administrativas](<Telas administrativas.md>).

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
