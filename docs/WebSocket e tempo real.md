# WebSocket e tempo real

Implementado em **16/10/2026** para participante, administração de evento e administração global.

## Conexão e escopo

O Daphne atende HTTP e WebSocket em `config.asgi.application`. As conexões usam a sessão Django existente; não há senha ou token na URL. O evento vem da rota e não do evento selecionado no cookie, preservando o isolamento entre abas.

| Rota | Autorização |
|---|---|
| `/ws/events/<uuid>/participant/` | Conta autenticada, participação no evento, sem suspensão ou banimento vigente |
| `/ws/events/<uuid>/administration/` | Vínculo administrativo ativo naquele evento ou administrador global |
| `/ws/global/` | Administrador global |

O handshake valida o Host e exige Origin da própria aplicação ou de `DJANGO_CSRF_TRUSTED_ORIGINS`. Em produção, aceita somente origens HTTPS; o navegador usa `wss://`. Não aceita Origin ausente ou `*`. Sessão, conta e vínculo são revalidados durante a conexão, com intervalo de até 30 segundos. Logout em outra aba, troca de senha, suspensão e revogação de acesso passam a encerrar a conexão. A API revalida as permissões em cada consulta.

Há limite compartilhado em cache de **20 conexões/minuto/conta**. O cliente envia `{"type":"ping"}` a cada 30 segundos; o servidor responde `{"type":"pong"}`. Pings com intervalo menor que 10 segundos encerram a conexão. Frames de aplicação aceitos têm no máximo 256 caracteres; mensagens binárias, JSON inválido e comandos de escrita são rejeitados. O socket não recebe mensagens de chat para persistência: esses envios continuam nos endpoints HTTP com CSRF e throttling.

## Entrega

Após entrar nos grupos autorizados, o servidor envia `{"type":"ready"}`. Alterações disparam `{"type":"changed","topics":["messages","notifications","status"]}`, contendo somente os tópicos afetados. Não trafegam textos de chat, nomes, IDs de terceiros ou conteúdo de notificações pelo canal. A interface consulta `sync/`, `notifications/` ou seu painel autorizado para obter os dados.

- Mensagens e confirmações de leitura avisam as duas contas da conversa, naquele evento.
- Criação/encerramento de matches, criação de conversa e bloqueios avisam as contas envolvidas.
- Notificações individuais e em `bulk_create` avisam seu destinatário. Alertas administrativos alcançam o contexto global da conta e o contexto administrativo do evento correspondente.
- Alterações do evento avisam os sockets daquele evento. Alterações da participação e do vínculo administrativo avisam a conta correspondente.

Os avisos são agendados com `transaction.on_commit`: rollback não publica uma alteração inexistente. Uma falha do Redis é registrada e não transforma uma gravação confirmada em erro de envio para o usuário. Operações por `QuerySet.update()` não disparam sinais Django; a confirmação de leitura chama o publicador explicitamente. Novos pontos de atualização em lote devem fazer o mesmo. Alterações não sinalizadas continuam sendo recuperadas pela consulta periódica.

Redis Channel Layer distribui os avisos entre Daphne, processos HTTP e Celery. O prefixo padrão é `<DJANGO_CACHE_KEY_PREFIX>:channels`; `CHANNEL_REDIS_PREFIX` permite configurá-lo. Ambientes que compartilham Redis precisam de prefixos distintos. Nginx encaminha `/ws/` com HTTP/1.1, Upgrade e timeout de leitura de 90 segundos. O proxy do Vite também encaminha WebSocket.

## Recuperação e carga

Cada aba usa uma conexão compartilhada pelos componentes. A interface agrupa avisos próximos por 80 ms e evita sincronizações simultâneas. Com WebSocket disponível, mensagens/status têm consulta de recuperação a cada **60–63 segundos**, também usada para renovar presença; notificações têm recuperação a cada **60 segundos**. Na queda, mensagens/status usam **15–18 segundos** e notificações **5 segundos**. O painel administrativo conserva consulta de recuperação aproximadamente a cada minuto quando conectado. A administração global atualiza alertas ao receber avisos e ao reconectar.

A reconexão usa espera progressiva com variação, até aproximadamente 31 segundos. Cada reconexão solicita sincronização, cobrindo mensagens persistidas durante a indisponibilidade. Abas ocultas fecham o socket e suspendem as consultas desses componentes; ao voltar, reabrem e sincronizam. Mocks continuam locais.

WebSocket fornece aviso transitório, não uma fila durável por navegador. O banco é a fonte dos dados e o cursor HTTP preserva os limites descritos em [Sincronização de participantes](<Sincronizacao de participantes.md>). O catálogo de participantes continua separado, com atualização por minuto nas telas sociais. Não foi realizado ensaio de carga com centenas de conexões simultâneas.

## Código e testes

Backend: `backend/realtime/`, `config/asgi.py`, `config/settings`, manager de `Notification` e confirmação de leitura em `api/sync.py`. Frontend: `realtime.ts`, `hooks/useParticipantSync.ts`, `ParticipantExtras.tsx` e painéis administrativos.

`api.test_realtime` cobre autenticação, origem/host, HTTPS, escopo por evento/conta, vínculos, notificações em lote, rollback, falha de Redis, revogação de sessão e limites do protocolo. Usa PostgreSQL com transações reais e Channel Layer em memória isolado pelo runner. `check-realtime.cjs` usa Daphne e Redis reais, publica alterações de outro processo e verifica interface, recuperação HTTP e reconexão. Resultados em [Verificação da implementação](<Verificacao da implementacao.md>).

Referências oficiais: [autenticação no Channels](https://channels.readthedocs.io/en/stable/topics/authentication.html) e [validação de Origin](https://channels.readthedocs.io/en/stable/topics/security.html).
