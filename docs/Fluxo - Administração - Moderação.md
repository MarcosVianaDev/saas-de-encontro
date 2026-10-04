# Fluxo - Administração - Moderação

> Documento de requisitos consolidado em 04/10/2026. Não é uma declaração de funcionalidades já implementadas; consulte [Verificação da implementação](<Verificacao da implementacao.md>). O texto preserva a evolução da fonte: as seções finais de definição/consolidação prevalecem sobre propostas anteriores do mesmo assunto. Consulte o [índice e análise](README.md) para divergências e precedência.

> Referência funcional preservada do DOCX. Cobertura implementada e limites atualizados em 04/10/2026: [Administração e ingresso](<Administracao e ingresso no evento.md>).

Fonte: [DOCX](<Fluxo - Administração - Moderação.md.docx>). Referência visual: [screen3.png](<Imagens - Telas e Protótipos/screen3.png>). Guia: [Telas administrativas](<Telas administrativas.md>).

## 1. Objetivo

Este documento define o fluxo funcional e as telas da área Moderação do painel administrativo de um evento.

A área Moderação é o centro operacional de segurança do evento. Ela recebe denúncias e sinais derivados de bloqueios, permite investigação, registra decisões administrativas e mantém rastreabilidade.

Princípio central:

> Denúncia ≠ bloqueio ≠ punição administrativa.

Uma denúncia abre uma ocorrência.
Um bloqueio é uma decisão entre participantes.
Uma suspensão ou banimento é uma decisão administrativa.

## 2. Fluxo principal

Fluxo conceitual:

Moderação
→ Fila de ocorrências
→ Detalhes da ocorrência
→ Análise
→ Decisão administrativa
→ Confirmação
→ Ocorrência resolvida
→ Auditoria

Fluxo complementar:

Moderação
→ Sinais de bloqueios
→ Participante
→ Histórico relacionado

O menu inferior administrativo permanece:

Dashboard | Participantes | Moderação | Evento | Mais

O item Moderação poderá exibir um badge com a quantidade de ocorrências que exigem atenção.

Exemplo:

Moderação 3

## 3. Tela principal - Moderação

Cabeçalho:

Moderação
3 requerem atenção

Abas iniciais:

- Pendentes;
- Em análise;
- Resolvidas.

Exemplo:

Pendentes 2 | Em análise 1 | Resolvidas

Bloqueios isolados não precisam constituir uma aba própria, pois não são necessariamente casos administrativos. Eles entram como sinais quando atingirem critérios relevantes.

## 4. Cards de ocorrências

Cada ocorrência na fila deve apresentar informações suficientes para priorização sem exigir abertura imediata.

Exemplo de denúncia:

Denúncia - Pendente
Assédio ou comportamento inadequado
Denunciado: João Pedro, 31
Por: Ana Carolina
Hoje - 20:14
Ver ocorrência

Exemplo de sinal:

Sinal de bloqueios - Em análise
5 participantes bloquearam este usuário
Participante: Rafael Costa, 30
Hoje - 18:45
Ver ocorrência

Cores podem auxiliar na identificação do estado, mas nunca devem ser a única indicação.

## 5. Busca e filtros

Campo:

Buscar participante ou ocorrência

### 5.1 Tipo

- Todos;
- Denúncias;
- Sinais de bloqueio;
- Administrativas.

### 5.2 Status

- Pendente;
- Em análise;
- Resolvida.

### 5.3 Motivo

Catálogo conceitual inicial:

- assédio/comportamento inadequado;
- conteúdo impróprio;
- perfil falso;
- comportamento agressivo;
- spam;
- outro.

O catálogo definitivo deve ser configurável pelo sistema e não rigidamente definido na interface.

### 5.4 Ordenação

- Mais recentes;
- Mais antigas;
- Prioridade.

## 6. Detalhes da denúncia

A tela de detalhes é o principal ambiente de análise da ocorrência.

Cabeçalho conceitual:

Denúncia #EVT-00142
Pendente

Assédio ou comportamento inadequado
Hoje - 20:14

O identificador exibido poderá ser amigável. Internamente, as entidades continuam utilizando UUID conforme a arquitetura geral.

## 7. Envolvidos

Apresentar cards separados.

### Denunciante

Foto
Ana Carolina, 26
Ver participante

### Denunciado

Foto
João Pedro, 31
Ver participante

As ações Ver participante direcionam para as respectivas fichas administrativas sem perder o contexto da ocorrência.

## 8. Relato

Seção:

### Relato do participante

Exemplo:

“Durante o evento, o usuário fez comentários inapropriados e insistentes, mesmo depois que demonstrei que não tinha interesse.”

Apresentar também:

Motivo selecionado:
Assédio ou comportamento inadequado

Registrado:
03/10/2026 - 20:14

A descrição é conteúdo sensível e deve ser acessível somente a usuários com permissão de moderação.

## 9. Evidências

A arquitetura já prevê ReportEvidence, portanto a tela deve reservar uma seção:

### Evidências

Possíveis representações conceituais:
- imagem;
- anexo;
- outro elemento permitido.

Os tipos definitivos de evidência ainda não estão definidos.

Essa decisão deverá considerar:
- dados de terceiros;
- conteúdo privado;
- armazenamento;
- autorização de acesso;
- retenção;
- LegalHold;
- segurança.

A estrutura da tela deve estar preparada sem antecipar regras ainda não definidas.

## 10. Contexto relacionado

A ocorrência poderá apresentar informações auxiliares.

Exemplo:

### Contexto

3 bloqueios relacionados
1 denúncia anterior neste evento

Ver histórico

Essas informações ajudam o moderador a analisar contexto, mas não estabelecem automaticamente culpa.

Um volume alto de bloqueios é um sinal, não uma prova.

## 11. Assumir ocorrência

Ação:

Assumir ocorrência

Quando um moderador assume o caso:

Em análise

Responsável: Ana Carolina
Desde 20:18

Objetivos:
- indicar responsabilidade operacional;
- evitar investigação duplicada;
- permitir acompanhamento;
- atualizar métricas do Dashboard.

Exemplo:

2 pendentes
→
1 pendente + 1 em análise

## 12. Notas internas

Seção:

### Notas da moderação

Exemplo:

Ana Carolina - 20:22
Participante denunciado possui outra ocorrência no evento.

Ação:

Adicionar nota

As notas:
- são internas;
- não são exibidas ao denunciante;
- não são exibidas ao denunciado;
- devem ser vinculadas à ocorrência;
- devem ser auditáveis.

A arquitetura prevê ModerationNote para essa finalidade.

## 13. Histórico da ocorrência

A tela deve disponibilizar uma timeline imutável das principais ações.

Exemplo:

20:14
Denúncia criada por Ana Carolina.

20:14
Administrador do evento notificado.

20:14
Administração global notificada.

20:18
Moderadora Juliana Costa assumiu a ocorrência.

20:22
Nota administrativa adicionada.

O histórico é parte central da rastreabilidade.

## 14. Ações de moderação

Ação principal:

Tomar decisão

Ao selecionar, apresentar opções conforme a permissão do usuário.

### 14.1 Sem sanção

Arquivar sem ação administrativa

A denúncia permanece registrada, mas nenhuma punição é aplicada.

### 14.2 Restrição temporária

Suspender participante

Direciona ao fluxo administrativo de suspensão já definido em Participantes.

### 14.3 Restrição definitiva no evento

Banir do evento

Disponível somente para usuários com permissão adequada.

## 15. Limite de autoridade do evento

O administrador do evento não deve possuir uma ação genérica de “Excluir usuário”.

A administração do evento pode, conforme permissão:
- suspender naquele evento;
- banir daquele evento.

Excluir, suspender ou bloquear globalmente uma conta pertence à administração geral da plataforma.

Uma mesma conta pode participar de diferentes eventos.

## 16. Resolver sem sanção

Fluxo:

Tomar decisão
→ Arquivar sem ação administrativa
→ Conclusão
→ Observação interna
→ Resolver ocorrência

Tela conceitual:

Resolver ocorrência

Conclusão:
- Não foram encontrados elementos suficientes;
- Situação resolvida;
- Denúncia duplicada;
- Outro.

Observação interna:
[Descreva a decisão...]

Cancelar | Resolver ocorrência

A ocorrência passa para Resolvidas.

## 17. Decisão - suspensão

Fluxo:

Tomar decisão
→ Suspender participante
→ Motivo
→ Duração ou condição, quando aplicável
→ Observação
→ Confirmação

Resultado conceitual:

Participante suspenso

Ocorrência #EVT-00142
Ação: suspensão
Responsável: Ana Carolina
20:31

A regra definitiva deverá estabelecer se a ocorrência é automaticamente resolvida ou permanece em acompanhamento após a suspensão.

## 18. Decisão - banimento do evento

Disponível somente para papéis autorizados.

Tela conceitual:

Banir participante deste evento?

João Pedro perderá definitivamente o acesso a este evento.

Motivo:
[Selecionar]

Justificativa:
[Obrigatória]

[ ] Estou ciente de que esta ação restringirá o participante neste evento.

Cancelar | Confirmar banimento

O banimento exige confirmação mais forte do que a suspensão.

## 19. Ocorrência resolvida

Após conclusão:

Ocorrência resolvida

Decisão:
Participante suspenso

Responsável:
Ana Carolina - Moderadora

Resolvida em:
03/10/2026 - 20:31

Justificativa:
Comportamento incompatível com as regras do evento.

Ação:

Ver histórico completo

## 20. Reabertura

Uma ocorrência resolvida poderá ser reaberta por usuários autorizados.

Ação:

Mais opções
→ Reabrir ocorrência

A reabertura deve exigir motivo.

Exemplo:

Nova evidência recebida.

O histórico anterior não deve ser alterado ou apagado.

Exemplo:

20:31 - Resolvida
21:04 - Reaberta pelo administrador

A reabertura acrescenta um novo evento ao histórico.

## 21. Sinais de múltiplos bloqueios

Um bloqueio isolado entre participantes não deve abrir automaticamente uma denúncia.

O sistema poderá, entretanto, gerar um sinal de moderação quando forem atendidos critérios relevantes.

Exemplo:

Múltiplos bloqueios

Rafael Costa recebeu 5 bloqueios neste evento.

Ao abrir:

### Sinal de comportamento

Rafael Costa, 30

5 bloqueios recebidos

Linha temporal:

18:13 - bloqueio
18:47 - bloqueio
19:02 - bloqueio
19:51 - bloqueio
20:07 - bloqueio

Motivos agregados, quando disponíveis:

Comportamento inadequado - 3
Insistência - 1
Outro - 1

Essas informações representam sinais para análise, não prova de infração.

## 22. Limiares de alerta

Não definir neste momento um valor rígido como:

3 bloqueios = alerta.

Os limiares poderão futuramente ser:
- configuração global do SaaS;
- configuração específica por evento;
- regra derivada de outros critérios.

O fluxo deve estar preparado para receber sinais sem fixar prematuramente o algoritmo que os gera.

## 23. Nova denúncia em tempo real

Diferentemente de um novo cadastro, uma denúncia exige destaque operacional imediato.

Banner conceitual:

Nova denúncia

Assédio ou comportamento inadequado
Recebida agora

Ver ocorrência

O badge da navegação deve ser atualizado.

Exemplo:

Moderação 3
→
Moderação 4

Conforme o escopo geral, uma nova denúncia deve gerar notificação para:
- administração do evento;
- administração global da plataforma.

## 24. Permissões

Matriz conceitual inicial:

| Ação | Operador | Moderador | Administrador |
| --- | --- | --- | --- |
| Ver fila | Não | Sim | Sim |
| Ver denúncia | Não | Sim | Sim |
| Assumir caso | Não | Sim | Sim |
| Adicionar nota | Não | Sim | Sim |
| Resolver sem sanção | Não | Sim | Sim |
| Suspender | Não | Sim | Sim |
| Banir do evento | Não | Não | Sim |
| Reabrir caso | Não | Limitado | Sim |

Esta matriz permanece preliminar até a definição detalhada de Equipe e Permissões.

Todas as permissões devem ser validadas no backend.

## 25. Auditoria

Ações administrativas sensíveis devem produzir registro de auditoria.

Especialmente:
- criação da denúncia;
- mudança de status;
- moderador que assumiu;
- inclusão de notas;
- consulta de evidências sensíveis, quando aplicável;
- suspensão;
- reativação;
- banimento;
- resolução;
- reabertura.

O AuditLog permanece append-only conforme a arquitetura definida para o projeto.

Registros anteriores não devem ser sobrescritos para ocultar mudanças de decisão.

## 26. LGPD e retenção

Denúncias e evidências representam uma das categorias mais sensíveis do sistema.

Após o encerramento do evento, esses registros não devem simplesmente desaparecer junto com a experiência social.

Eles entram na política de retenção correspondente.

Quando existir fundamento válido para preservação, LegalHold impede a exclusão automática.

Após o prazo legal aplicável e sem fundamento para preservação, os dados sujeitos à eliminação seguem a política de retenção e exclusão definida pelo projeto.

Nenhum prazo numérico deve ser arbitrariamente fixado neste fluxo.

## 27. Telas previstas

O fluxo de Moderação deverá resultar inicialmente nas seguintes telas/estados:

1. Moderação - fila principal;
2. filtros de moderação;
3. detalhes da denúncia;
4. evidências e contexto;
5. ocorrência em análise - responsável e notas;
6. histórico da ocorrência;
7. tomar decisão;
8. resolver sem sanção;
9. suspensão;
10. banimento do evento;
11. ocorrência resolvida;
12. sinal de múltiplos bloqueios.

Estados adicionais:
- fila vazia;
- busca sem resultados;
- nova denúncia recebida;
- ocorrência reaberta;
- ausência de evidências;
- permissão insuficiente.

## 28. Diretrizes para desenvolvimento

- Mobile-first.
- Reutilizar a identidade visual da área administrativa.
- Tratar denúncia, bloqueio e punição como conceitos independentes.
- Não presumir culpa com base em denúncia ou quantidade de bloqueios.
- Permitir atribuição de responsável pela ocorrência.
- Manter notas internas separadas do conteúdo visível aos participantes.
- Preservar histórico de mudanças.
- Não permitir ao administrador do evento executar ações globais sobre contas.
- Exigir justificativa para decisões administrativas.
- Aplicar permissões no backend.
- Auditar ações sensíveis.
- Tratar evidências como conteúdo sensível.
- Respeitar retenção e LegalHold.
- Priorizar ocorrências que exigem atenção sem transformar sinais em condenações automáticas.

## 29. Princípio final do fluxo

O ciclo operacional de Moderação é:

Receber
→ Priorizar
→ Investigar
→ Contextualizar
→ Decidir
→ Registrar
→ Auditar

O sistema deve permitir segurança e resposta operacional sem confundir uma denúncia com uma condenação e sem conceder à administração de um evento autoridade global sobre a conta do participante.

Este documento deve permanecer como referência funcional para o desenvolvimento das telas administrativas de Moderação.

## Matriz de permissões

Administrador Global: usuário com Status de superusuário ativo no Django. Acesso ao Django Admin: flag Membro da equipe, sem equivalência automática com Administrador Global.

Administrador do Evento gerencia Moderadores e Operadores, permissões operacionais, métricas e relatórios. Pode delegar temporariamente a administração somente a Moderador e retomá-la depois; ambas as ações são auditadas e notificadas ao Administrador Global.

Permissões operacionais delegáveis: tratativas de denúncias, bloqueios/desbloqueios, passes, ativação/desativação de perfil, foto de ativação, remoção de foto e edição de bio vinculada a uma tratativa.

Moderador atua nas tratativas conforme permissões recebidas, sem gerenciar equipe/permissões e sem acesso a métricas/relatórios.

Operador atua principalmente na foto de outfit e ativação do perfil, disponibilização do QR Code e abertura de ocorrências administrativas do participante.

Intervenções em perfil devem ser vinculadas à denúncia que as originou ou à solicitação de suporte feita pelo participante dentro de Mensagens. Ações relevantes devem ser auditáveis.

## Denúncias e segurança

O participante pode denunciar pela Descoberta, perfil expandido ou Mensagens, com relato obrigatório e indicação do conteúdo relacionado. Conteúdos substituídos permanecem vinculados ao histórico para auditoria conforme retenção. Dez denúncias válidas alertam a moderação do evento; vinte desativam automaticamente o perfil para análise e notificam a Administração Global. Denúncias consideradas infundadas deixam de contar. O histórico permanece ligado ao perfil global, sem banimento automático em eventos futuros.

## LGPD, retenção e eliminação

As regras detalhadas de categorias de dados, temporalidade, anonimização, exclusão, direitos do titular e preservação judicial estão centralizadas no documento **LGPD - Retenção, Eliminação e Direitos do Titular**. Não existe prazo único para todos os dados: cada categoria deve seguir finalidade, base legal e matriz de retenção próprias. Os 15 dias para arquivamento do evento são regra operacional, não prazo jurídico. O projeto deve aplicar ConsentRecord, DataRetentionRecord, LegalHold, PrivacyRequest e AuditLog conforme essa política. Antes da produção, os prazos específicos ainda não fixados devem passar por validação jurídica.

Documento: https://docs.google.com/document/d/1iVfUgkg_0EBERID5z9ZA-WnRu9e6bIDECgBTFW0pmM0/edit
