# Sincronização de participantes

Implementação em **16/10/2026**. Substitui o polling de `bootstrap/` a cada 5 segundos no acesso de participante.

## Presença e gravações

`current()` continua validando conta, evento, banimento, suspensão e ativação. `last_seen_at` só é atualizado quando ausente ou com pelo menos **60 segundos**. O mesmo limite vale para Online, Presencial e Híbrido; o modo Online não força mais um UPDATE em cada requisição.

A condição também fica no WHERE do UPDATE. Se duas requisições carregarem o mesmo timestamp antigo, somente uma consegue renová-lo; a outra recupera o valor atual. O heartbeat não altera `updated_at`, evitando transformar atividade em alteração de cadastro. Ao renovar a presença Online, grava também `presence=PRESENT`. A definição de ausência pelo intervalo do evento e as regras de GPS permanecem próprias de cada modalidade.

## Contratos

Todos os endpoints usam autenticação, throttling e o contexto de evento da aba, conforme [Operação e desenvolvimento](<Operacao e desenvolvimento.md>).

| Endpoint | Comportamento |
|---|---|
| `GET /api/bootstrap/` | Snapshot inicial e resposta de operações explícitas existentes. Inclui `syncCursor`, criado antes de carregar o snapshot. Continua contendo o histórico inicial. |
| `GET /api/sync/?cursor=...&state=RUNNING` | Até **100 mensagens** novas/alteradas, cursor seguinte, `hasMore`, status do participante/evento, estado das próprias conversas, IDs com não lidas, IDs bloqueados e cards de parceiros de match alterados. Não serializa o catálogo de participantes, tópicos, fotos próprias ou histórico inteiro. |
| `POST /api/conversations/<peer>/read/` | Corpo `{messages: [uuid, ...]}`, máximo 100. Marca somente mensagens recebidas daquela conversa, dentre os IDs informados. Retorna IDs confirmados e timestamp. Sem novas leituras, não executa UPDATE. |
| `GET /api/catalog/` | Lista de perfis visíveis e descoberta com os filtros salvos. Usa o mesmo conjunto serializado para os dois resultados e aproveita prefetch de fotos. Não retorna chats, tópicos ou perfil próprio. |

`sync/` não confirma leitura por si só. Conversas encerradas/bloqueadas conservam o histórico autorizado; estados impedem novas mensagens e cards bloqueados são anonimizados. Permissões, sanções e escopo são revalidados em cada chamada. O GET legado de mensagens confirma leituras e serializa somente a conversa solicitada, sem chamar `bootstrap()`.

O parâmetro `state` informa o último estado conhecido do evento. Ao observar Encerrado/Arquivado pela primeira vez, o status também traz o relatório agregado próprio. Nas chamadas seguintes com esse estado, os agregados não são recalculados.

## Cursor e consistência

O cursor é assinado e vinculado à participação e ao evento. Token alterado ou de outro participante/evento retorna HTTP 400. Sem cursor, o endpoint permite recuperar o histórico em páginas limitadas.

As mensagens são ordenadas por `(updated_at, id)`, com limite superior fixado para cada janela de paginação. Empates de timestamp usam o UUID como desempate. `hasMore=true` preserva a janela e a posição, evitando pular mensagens durante a paginação. Mensagens que surgem depois do limite superior são consultadas na janela seguinte.

Cada janela incremental recua **2 minutos**, para reencontrar alterações que só se tornaram visíveis após a consulta anterior, dentro desse intervalo. Esse recuo pode retransmitir mensagens; o frontend faz merge por ID e versão `updated`, preserva a ordem `created/id` e não duplica bolhas nem reverte uma confirmação de leitura mais recente. Transações que permaneçam invisíveis por mais do que a janela de recuo não têm garantia de recuperação por esse mecanismo; o snapshot inicial/reload continua recuperando o histórico persistido. Não é um log de alterações com ordenação por commit.

## Frequências e interface

- Sincronização imediata ao entrar/trocar de tela, conversa ou receber aviso pelo [WebSocket](<WebSocket e tempo real.md>). Com a conexão disponível, recuperação a cada **60 a 63 segundos**; sem conexão, **15 a 18 segundos**, com variação para distribuir chamadas.
- Uma chamada de sincronização por vez. O próximo timeout é criado após a resposta. Com páginas pendentes ou lote de leituras cheio, continua após 1 segundo.
- Aba oculta e operação explícita em andamento suspendem a consulta periódica. Ao voltar a ficar visível, sincroniza imediatamente. HTTP 429 aplica espera de 60 segundos.
- O catálogo é consultado ao entrar em Descoberta/Participantes e, nessas telas, a cada **60 segundos**, somente com funções sociais disponíveis e aba visível. Não é recarregado ao permanecer no chat ou no perfil.
- O mock conserva suas simulações locais. A central de notificações usa o mesmo WebSocket, com recuperação HTTP a cada 60 segundos quando conectada e 5 segundos sem conexão; os intervalos acima descrevem mensagens/status e catálogo.

Novos matches entram no estado local mesmo sem mensagens. As confirmações de leitura só enviam IDs efetivamente disponíveis no chat aberto. Atualizações do catálogo não restauram um card que a sincronização já tenha identificado como bloqueado.

## Índices e validação

A migração **`messaging.0003_message_sync_index`** acrescenta índice `(conversation, updated_at, id)` e índice parcial por conversa para `read_at IS NULL`. `backend/start.py` aplica as migrações na inicialização; ambientes atualizados manualmente devem executar `python manage.py migrate` antes de atender tráfego com os índices novos.

Cobertura: `api.test_participant_sync`, `api.test_online_presence` e `check-participant-sync.cjs`. O teste de população adiciona 500 participantes e verifica que a quantidade de queries de uma sincronização ociosa permanece constante; isso não substitui ensaio de carga com 500 clientes concorrentes. Resultados da suíte estão em [Verificação da implementação](<Verificacao da implementacao.md>).

Fontes: `backend/api/sync.py`, `services.py`, `views.py`, `backend/apps/messaging/models.py`, `frontend/participant-sync.ts`, `backend-client.ts` e `hooks/useParticipantSync.ts`, integrado por `useParticipantController.ts`.
