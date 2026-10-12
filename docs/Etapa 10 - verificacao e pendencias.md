# Etapa 10 — verificação e pendências

Revisão em **12/10/2026**, por confronto do [backlog aberto](<trilha de implementacao(aberto).md>), da seção **Exportação auditável do evento** do [Escopo Técnico](<Escopo Técnico.md>) e do código atual. Esta revisão não implementa a exportação nem conclui cards.

## Resultado por card

| Card | Situação | Evidência existente | O que falta |
|---|---|---|---|
| 10.1 — Evento arquivado | Parcial | Estado `ARCHIVED`, `archived_at`, transição automática após 15 dias, consultas e vários bloqueios de escrita | Garantia integral de leitura exclusiva, apresentação dedicada do estado, consulta geral de auditoria e ação autorizada de exportação |
| 10.2 — Solicitar exportação | Não implementado | Autorização global e seleção de evento podem ser reutilizadas | Formulário/modal, referência formal, escopo completo/personalizado, API e auditoria da solicitação |
| 10.3 — Celery de exportação | Não implementado | Worker, Beat, serviços de domínio e tarefas de outros recursos existem | `ExportJob`, estados, enfileiramento, geração, tratamento de falha/retry, consulta de progresso e download autorizado |
| 10.4 — Estrutura do pacote | Requisitos principais definidos; geração não implementada | Escopo Técnico define SQL + SPA offline + manifesto + hashes + PDF externo | Esquemas e contratos executáveis, coleta isolada, geração dos artefatos e testes de integridade/offline/escopo |

**Não há `ExportJob`, rota de exportação/download de ZIP ou tarefa Celery de exportação no código revisado.** Os relatórios financeiros e os downloads individuais de evidências não são exportação auditável de evento.

## 10.1 — Cobertura e lacunas de arquivamento

### O que está implementado

- `backend/apps/events/models.py`: estado Arquivado e data de arquivamento.
- `backend/apps/events/services.py`: `CLOSED → ARCHIVED` somente por transição automática após quinze dias do encerramento; atualização com auditoria e notificações. Arquivamento não é eliminação de dados.
- `backend/apps/events/tasks.py` e Beat: sincronização periódica do ciclo de vida.
- `frontend/GlobalAdministration.tsx`: filtro Arquivados e acesso administrativo ao evento.
- `frontend/Administration.tsx`: `readOnly` para `CLOSED`/`ARCHIVED` e acesso às consultas existentes conforme papel.
- Serviços/endpoints de configuração, passes, avisos e diversas ações sociais/administrativas já verificam estado. Histórico de localização admite consulta em Pausado/Encerrado/Arquivado, com autorização e auditoria.
- Métricas administrativas são fornecidas para ADMIN; moderação depende de permissão; histórico de casos deriva da auditoria. Isso não é uma consulta geral de todos os logs do evento.

### O que precisa ser fechado

| Lacuna | Local concreto | Critério de aceite |
|---|---|---|
| Resposta de suporte ainda grava em evento arquivado | `AdminSupportView.post`, `backend/api/support.py`: cria mensagem e notificação sem barreira de estado | Rejeitar escrita operacional em `ARCHIVED` mesmo com requisição direta, ou documentar uma exceção de produto explícita e separada do pacote offline |
| Retomada de administração contorna a barreira | `TeamView.post`, `backend/api/team.py`: `action == reclaim` é tratado antes do bloqueio `CLOSED`/`ARCHIVED` | Não alterar delegação no evento arquivado; testar o caminho específico |
| Leitura exclusiva precisa de cobertura por endpoint/papel | Permissões e verificações estão distribuídas por views/serviços | Testar ADMIN, MODERATOR, OPERATOR, superuser, staff e participante, incluindo chamadas HTTP diretas |
| Avisos, suporte e outras telas não têm garantia uniforme só pelo prop `readOnly` | `Administration.tsx` monta componentes com contratos distintos | Nenhuma ação operacional de escrita disponível indevidamente na interface arquivada; a API continua sendo a barreira efetiva |
| Consulta de auditoria geral ausente | `backend/api/urls.py` não contém endpoint específico de auditoria de evento; frontend não apresenta área correspondente | Consulta paginada/filtrada com escopo e permissão, sem expor logs de outros eventos/contas |
| Experiência do arquivado incompleta | Estado aparece nos dados; não há fluxo completo do card 10.1 com exportação | Identificação clara de Evento arquivado e ações de consulta/exportação compatíveis com o papel |

Não bloquear indiscriminadamente operações de conta ou direitos do titular: `profile/disposition/` foi desenhado para persistência/exclusão social após encerramento e precisa de análise própria. Marcar uma notificação como lida também não é edição do conteúdo operacional do evento. O acesso técnico ao Django Admin deve ser avaliado separadamente; o `readOnly` do React não o restringe.

O teste `api.test_mvp.FoundationTests.test_celery_calls_same_service_and_observes_automatic_delay` já contém o cenário de arquivamento, mas falhou nesta revisão por configuração presencial sem coordenadas antes de alcançar essa asserção. Portanto, há código e teste escritos, mas **não há aprovação atual desse teste**.

## 10.2 — Solicitação formal e autorização

O requisito consolidado restringe gerar, baixar e assinar a exportação ao **Administrador Global/superuser**. ADMIN do evento, MODERATOR, OPERATOR e `is_staff` sem `is_superuser` não possuem essa permissão. A restrição deve ser aplicada na API, no processamento e no download; ocultar um botão não basta.

Checklist pendente:

- [ ] Ação Exportar evento na experiência administrativa global do evento arquivado.
- [ ] Confirmação “Gerar pacote de exportação deste evento?”, indicando processamento assíncrono e auditoria.
- [ ] Referência da solicitação formal/ordem, responsável, contexto e escopo.
- [ ] Seleção completa ou personalizada por módulos; logs relacionados ao evento são obrigatórios.
- [ ] API transacional que valida autorização, evento, escopo e regras, cria o job e registra a solicitação.
- [ ] Enfileirar somente após commit; não produzir ZIP/dump pesado dentro da requisição HTTP.
- [ ] Impedir acesso cruzado a evento/artefato e cobrir permissões com testes.

A solicitação formal recebida por suporte/e-mail não deve disparar exportação automática. Não há autorização nesta revisão para envio de material a terceiros nem integração automática de e-mail.

## 10.3 — Job, geração assíncrona e entrega

Checklist pendente:

- [ ] Modelo e migração de `ExportJob`, com evento, solicitante, referência, escopo, estado, timestamps, erro público controlado e metadados dos artefatos.
- [ ] Estados Pendente → Processando → Concluído/Falhou e transições auditadas.
- [ ] Tarefa Celery que chama serviço de domínio; idempotência, locks, limpeza de arquivos temporários e registro de tentativas/falhas.
- [ ] Estratégia de retry e ação Tentar novamente, sem produzir artefatos contraditórios nem duplicar auditoria indevidamente.
- [ ] Definir como obter uma fotografia consistente dos registros e mídias, inclusive quando a retenção executar durante a geração.
- [ ] Endpoint de consulta/progresso; mensagens Preparando exportação, Exportação concluída e falha controlada.
- [ ] Download autenticado e auditado de ZIP e PDF; controle de disponibilidade, expiração e armazenamento privado.
- [ ] Registro de assinatura e encaminhamento formal; a assinatura eletrônica em GOV.BR é uma possibilidade do requisito, não integração implementada.
- [ ] Testes de falha de auditoria/storage/worker, repetição, download e ausência de acesso não autorizado.

O job não deve tratar um evento arquivado como banco eliminável: retenção, Legal Hold, acesso e arquivamento são mecanismos diferentes. Os modelos atuais de `LegalHold`, `DataRetentionRecord` e `PrivacyRequest` não entregam toda a governança operacional exigida pela exportação.

## 10.4 — Formato já definido e detalhes ainda pendentes

A frase antiga “Não implementar formato definitivo até fecharmos conteúdo...” deve ser interpretada à luz da consolidação posterior do Escopo Técnico. Os seguintes requisitos **já estão documentados**, e não precisam ser reinventados:

1. ZIP limitado ao evento e ao escopo autorizado.
2. Dump SQL dos dados selecionados com a estrutura necessária à consulta/restauração, incluindo todos os logs relacionados ao evento.
3. SPA administrativa estática fiel às consultas aplicáveis, navegável offline e somente leitura; sem chamadas a produção, edição, criação de registros ou novos logs.
4. Manifesto com identificação, data/hora, versão, evento, modalidade completa/personalizada, módulos incluídos/excluídos e hashes dos componentes.
5. Mídias/evidências somente quando autorizadas e legalmente disponíveis no escopo.
6. Congelamento do ZIP e cálculo de SHA-256 do arquivo final.
7. Termo de Exportação e Integridade em PDF **externo ao ZIP**, evitando circularidade do hash; inclui identificação, responsável, escopo, resumo, hashes e ressalvas sobre eliminação/anonimização e Legal Hold.
8. Auditoria de solicitação, geração, escopo efetivo, hash, termo, assinatura, download e registro de encaminhamento.

Ainda devem ser especificados para implementação e aceite:

- [ ] Matriz exata de dados por módulo e tratamento de entidades compartilhadas, contas, organização, relações entre participantes e logs globais que referenciem o evento.
- [ ] Estrutura de diretórios, versões de manifesto e schema do snapshot consumido pela SPA.
- [ ] Método de SQL restrito, ordenação de dependências e estratégia comprovável de consulta/restauração em ambiente isolado. Dump integral do banco não atende ao isolamento.
- [ ] Tratamento de módulos omitidos, registros eliminados/anonimizados e evidências ausentes, sem criar dados fictícios para preencher lacunas.
- [ ] Política de armazenamento, validade dos links, expiração dos artefatos, custódia, auditoria e associação com Legal Hold; decisões jurídicas devem ser aprovadas pelos responsáveis.
- [ ] Procedimento de assinatura/entrega e limites da integração escolhida. Hash de integridade não substitui autenticação ou assinatura.
- [ ] Reutilização segura da interface administrativa: o mock atual serve como referência visual, mas possui ações mutáveis e não é a SPA offline exigida.
- [ ] Testes que abram o pacote sem rede e comprovem ausência de chamadas externas/API, leitura exclusiva e isolamento entre dois eventos.
- [ ] Verificação de hashes internos, SHA-256 final e detecção de adulteração; PDF separado com o hash do ZIP correspondente.

## Dependências e ordem sugerida

1. Corrigir e testar leitura exclusiva do arquivado; revisar matriz de papéis e acesso à auditoria.
2. Fechar matriz de módulos, associação com Legal Hold e contratos de snapshot/manifesto/entrega.
3. Implementar `ExportJob`, API e auditoria com testes de autorização e transação.
4. Implementar serviço e tarefa de geração com fotografia consistente e recuperação de falha.
5. Gerar SQL, SPA offline, mídias, manifesto, ZIP e PDF externo; verificar integridade.
6. Conectar progresso, retry e downloads à interface global.
7. Homologar ponta a ponta com dois eventos, todos os papéis, dados omitidos/eliminados e falhas simuladas.

Os requisitos de minimização, retenção e Legal Hold dependem de partes da etapa 9; os controles definitivos de storage/entrega se relacionam à etapa 12. Não marcar etapa 10 como concluída com base no arquivamento automático ou na geração de um ZIP genérico.

## Validação desta revisão

Busca em modelos, rotas, serviços, tarefas e componentes não encontrou exportação de evento implementada. O build do frontend passou. A suíte completa descobriu **171 testes**, com **9 falhas e 5 erros**; detalhes e comandos estão em [Verificação da implementação](<Verificacao da implementacao.md>). Esses resultados impedem apresentar a homologação atual como integralmente aprovada.
