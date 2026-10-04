# Cards abertos

Atualização em 04/10/2026: os 45 cards das etapas 1 a 8 foram implementados e transferidos integralmente para [cards concluídos](<trilha de implementacao(fechado).md>). Consulte [cobertura e validação](<Implementacao - etapas 1 a 8.md>). Permanecem abertos os cards das etapas 9 a 12 e as diretrizes gerais abaixo.

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
