# Telas administrativas do EventConnect

> As sínteses e matrizes abaixo descrevem a especificação inicial e a implementação registrada. Os fluxos completos receberam decisões posteriores dos DOCX; consulte o [índice e análise](README.md) e as seções finais desses fluxos para permissões, denúncias, geolocalização, ciclo de vida e exportação. Requisitos novos não significam funcionalidades já implementadas.

Atualizado em 04/10/2026. Estes fluxos definem requisitos para a área administrativa do evento. O painel React administrativo e seu backend foram implementados; a cobertura e as decisões adotadas estão em [Administração e ingresso](<Administracao e ingresso no evento.md>). O Django Admin permanece disponível em `/admin/`. As seis telas do participante continuam descritas em [Telas do frontend](<Telas do frontend.md>).

## Referências

As versões Markdown preservam o conteúdo textual dos DOCX. Nomes, contagens, horários e identificadores apresentados são exemplos.

| Fluxo | Especificação completa | Fonte original | Referência visual |
|---|---|---|---|
| Administração do evento | [Fluxo do evento](<Fluxo - Administração do Evento.md>) | [DOCX](<Fluxo - Administração do Evento.md.docx>) | [screen1.png](screen1.png) |
| Participantes | [Fluxo de participantes](<Fluxo - Administração - Participantes.md>) | [DOCX](<Fluxo - Administração - Participantes.md.docx>) | [screen2.png](screen2.png) |
| Moderação | [Fluxo de moderação](<Fluxo - Administração - Moderação.md>) | [DOCX](<Fluxo - Administração - Moderação.md.docx>) | [screen3.png](screen3.png) |

## Acesso e navegação

O login será compartilhado com os participantes. Após autenticar, o backend verificará conta, vínculo, papel e permissões no evento e direcionará o funcionário ao Dashboard correspondente. Uma conta poderá exercer papéis distintos em eventos diferentes. A administração global permanece separada.

A navegação mobile será **Dashboard | Participantes | Moderação | Evento | Mais**, com badge de ocorrências que exigem atenção. Mais poderá reunir Equipe, Relatórios, configurações permitidas e conta. A interface seguirá a identidade lilás/roxa, com cartões claros, informações acionáveis e confirmações de ações críticas. Status precisam de texto além da cor.

## Dashboard, Evento e QR Code

O Dashboard prioriza participantes e ativos recentes, com totais agregados de matches e conversas. Requer atenção reúne denúncias pendentes/em análise e sinais relevantes de bloqueios, com acesso à Moderação. Atividade recente, resumo de participantes e segurança complementam a operação; gráficos complexos não são requisito inicial.

Antes do evento, destacar início, preparação, cadastros e QR Code. Durante, destacar atividade, segurança e pendências. Depois, consolidar resultados e oferecer relatório final. Equipe no Dashboard é evolução prevista, não requisito obrigatório inicial.

Evento apresenta nome, UUID, início, término, responsável e status Agendado/Em andamento/Encerrado. Dados definidos pela administração global são somente leitura. O QR Code deve usar referência ou token seguro associado ao evento, com exibição em tela cheia e compartilhamento. O UUID exposto não substitui o mecanismo seguro de ingresso. Após encerramento, novos ingressos devem ser recusados e o atalho desabilitado ou removido.

## Participantes administrativos

A lista operacional pesquisa nome/e-mail somente no evento autorizado, com total, filtros rápidos Todos/Ativos/Novos e ordenação por nome, cadastro ou atividade recente. Os filtros avançados abrangem situação, cadastro e moderação, com Limpar e Aplicar.

A ficha usa `EventParticipant` como referência operacional e separa Informações de Ocorrências. Exibe somente dados necessários e permitidos. Cadastro incompleto, Ativo, Suspenso e Banido são estados administrativos conceituais; online/offline/inativo representam atividade.

Ocorrências levam à Moderação. Ações autorizadas incluem abrir ocorrência administrativa, suspender, reativar quando permitido e remover acesso ao evento. Sanções exigem motivo, contexto, confirmação e auditoria; banimento usa `EventBan` e confirmação mais forte. Suspensão neste fluxo restringe o evento correspondente, sem conferir autoridade global sobre a conta.

A ficha comum não expõe mensagens privadas, likes, passes, rejeições, matches individuais ou preferências privadas desnecessárias. Bloqueios podem aparecer agregados; relações detalhadas pertencem à investigação autorizada. Novos ingressos atualizam lista e contadores rapidamente, sem exigir aviso ostensivo por cadastro.

## Moderação

O fluxo será **fila → detalhes → análise → decisão → confirmação → resolução/acompanhamento → auditoria**. A fila terá Pendentes/Em análise/Resolvidas, busca, tipo, status, motivo configurável e ordenação por data ou prioridade. Cards identificam tipo, envolvidos, motivo, horário e status.

Detalhes incluem relato, envolvidos com acesso às fichas, evidências autorizadas, contexto e histórico. Assumir ocorrência registra responsável e mudança para Em análise. Notas são internas, vinculadas ao caso e auditáveis. A timeline preserva decisões anteriores.

As decisões previstas são resolver sem sanção, suspender temporariamente e banir do evento. Resolver sem sanção registra conclusão e observação interna. Banimento exige motivo, justificativa e confirmação explícita. Reabrir exige autorização e motivo, acrescentando histórico sem apagar decisões anteriores.

Denúncia, bloqueio e punição são independentes. Bloqueio isolado não abre denúncia automaticamente. Múltiplos bloqueios podem gerar sinais segundo critérios ainda a definir, sem presumir culpa nem aplicar sanção automática. Novas denúncias recebem destaque imediato e notificam a administração do evento e a global.

São previstos estados vazios, busca sem resultados, ausência de evidências, nova denúncia, reabertura e permissão insuficiente. Relatos e evidências têm acesso restrito. Retenção e `LegalHold` continuam após o encerramento; estes fluxos não estabelecem prazo numérico.

## Permissões preliminares

| Ação | Operador | Moderador | Administrador do evento |
|---|---|---|---|
| Consultar participantes | Sim | Sim | Sim |
| Consultar fila e ocorrências | Não | Sim | Sim |
| Assumir, anotar e resolver sem sanção | Não | Sim | Sim |
| Suspender no evento | Não | Sim | Sim |
| Banir do evento | Não | Não | Sim |
| Reabrir ocorrência | Não | Limitado, a definir | Sim |

A matriz depende da especificação de Equipe e Permissões. O backend deve validar papel, vínculo e escopo nas consultas e escritas. A administração do evento não exclui, suspende nem bloqueia globalmente contas. Ações sensíveis e consulta de evidências, quando aplicável, produzem `AuditLog` append-only.

## Diferenças dos mockups e decisões abertas

- `screen1.png` mostra lista de usuários bloqueados e relatório com gráfico. Bloqueios são sinais/contexto de investigação; aba independente e gráficos não são requisitos iniciais definidos pelos textos.
- `screen2.png` mostra “Bloquear usuário da plataforma”. Essa ação pertence exclusivamente à administração global e não deve compor o menu do funcionário do evento. O toast de novo participante é ilustrativo: o texto não exige aviso ostensivo. Cadastro “Personalizado” não é filtro inicial obrigatório.
- A observação da suspensão aparece opcional em `screen2.png` e obrigatória em `screen3.png`. Sua obrigatoriedade uniforme precisa de definição; motivo, contexto e rastreabilidade permanecem necessários.
- `screen3.png` mostra período de busca, alteração de responsável, adição de evidência e “Converter em denúncia”. Esses controles precisam de regras antes da implementação. Um sinal não equivale automaticamente a denúncia.
- O mockup mostra suspensão seguida de resolução. O texto deixa em aberto se suspender resolve automaticamente o caso ou mantém acompanhamento.
- As fontes deixaram abertos critérios de atividade recente e Novos, limiares de sinais, duração/condição de suspensão, evidências, permissões, métricas/relatórios e retenção. O [guia da implementação](<Administracao e ingresso no evento.md>) registra os critérios operacionais adotados e as pendências restantes. Os documentos completos preservam os estados conceituais originais; a implementação usa `is_active`, `EventSuspension` e `EventBan` para compor a situação administrativa.

## Relação com a implementação atual

O painel dedicado possui autorização por evento/papel, métricas calculadas a partir dos registros, QR Code assinado, participantes, fila e decisões de moderação, notas, sanções por evento, notificações internas e histórico baseado em auditoria. Equipe e relatório são consultivos; coleta/upload de evidências, catálogo formal de motivos, alertas automáticos e tempo real por WebSocket permanecem pendentes. Consulte [Administração e ingresso](<Administracao e ingresso no evento.md>) para a cobertura exata.

Consulte [Verificação da implementação](<Verificacao da implementacao.md>) para a cobertura atual e [Demonstração e API](<Demonstracao e API.md>) para os endpoints do participante. As especificações completas preservam as fontes originais; o guia operacional distingue os requisitos implementados dos que continuam abertos.
