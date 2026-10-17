# Arquitetura do frontend

Refatoração do acesso participante em **16/10/2026**, mantendo os modos Django e mock, as URLs existentes e os três acessos.

## Organização

`frontend/main.tsx` importa os estilos e monta `App`. `App.tsx` compõe o layout, seleciona o contexto global/administrativo/participante e apresenta a página ativa. As regras de autorização permanecem no backend.

| Local | Responsabilidade |
|---|---|
| `views/LoginPage.tsx` | Login/cadastro e credenciais locais; demonstração com campos preenchidos |
| `views/ProfilePage.tsx` | Perfil, fotos e diálogo de miniatura |
| `views/FiltersPage.tsx` | Rascunho de preferências e envio explícito pelo formulário |
| `views/DiscoveryPage.tsx` | Descoberta, decisões e relatório do evento encerrado |
| `views/MessagesPage.tsx` | Lista de conversas, busca, composição e rolagem do chat |
| `views/ParticipantsPage.tsx` | Busca, categorias e tamanho dos cards de participantes |
| `components/Icon.tsx`, `Avatar.tsx` | Ícones SVG compartilhados e avatar; catálogo SVG criado uma vez |
| `components/Participant*.tsx` | Alertas, navegação, caixa de entrada e modais com Escape/controle de foco |
| `components/Demo*.tsx` | Elementos do layout exclusivo do mock |
| `hooks/useParticipantController.ts` | Estado compartilhado da sessão, carga inicial e escolha de contexto |
| `hooks/useParticipantRouter.ts` | Rotas por hash, histórico e restrições de navegação |
| `hooks/useParticipantProfile.ts` | Gravação do perfil/preferências e operações de fotos |
| `hooks/useParticipantSocial.ts` | Likes, favoritos, conversas e abertura de notificações |
| `hooks/useParticipantSync.ts` | Delta HTTP, atualização do catálogo e integração com WebSocket |
| `participant-pages.ts` | Tipos de página, etapas e catálogos exclusivos do mock |

As páginas recebem apenas as propriedades de que precisam, tipadas com `Pick<ParticipantController, ...>`. Essas referências são imports de tipo e não criam dependências de execução de volta para o controller. Os hooks de domínio têm contratos próprios. O TypeScript verifica também os subdiretórios de componentes, páginas e hooks.

## Navegação e estado

O roteador leve preserva `#login`, `#perfil`, `#filtros`, `#descobrir`, `#mensagens` e `#participantes`, incluindo Voltar/Avançar do navegador. Mantém os contextos e hashes administrativos separados e aplica as restrições de login e ativação tanto aos botões quanto às mudanças de hash.

Busca de participantes/conversas, credenciais, mensagem em composição, rascunho de filtros e referências dos diálogos pertencem às páginas/componentes. Digitar nesses controles não altera o estado do componente raiz. Os filtros somente são gravados por **Aplicar filtros**; sair sem aplicar descarta o rascunho. Os dados compartilhados de perfil, sessão e interações permanecem no controller, para uso da navegação e sincronização.

O centro de notificações continua montado durante a navegação do participante, preservando avisos e contadores. A extração conserva os deltas, confirmação de leitura, pausa da aba oculta e reconexão descritos em [Sincronização de participantes](<Sincronizacao de participantes.md>) e [WebSocket e tempo real](<WebSocket e tempo real.md>).

## Biografia e erros de validação

A biografia completa exige **50 a 200 caracteres**, após remover espaços nas extremidades na API. O backend centraliza os limites em `apps/profiles/constants.py`; serializers, validação do modelo, ativação e intervenção administrativa usam essas constantes. O frontend espelha os valores em `profile-validation.ts`, utilizados pelos formulários, validação local e mock. Alterações futuras nessa política devem atualizar os dois arquivos e os testes de limites.

A migração `profiles.0008_alter_participantprofile_bio` registra os validadores e o tamanho máximo do campo. Não trunca biografias existentes. Um perfil incompleto pode manter biografia vazia; ativação e edição exigem a faixa completa. Biografias antigas fora da faixa precisam ser corrigidas antes de uma nova ativação.

Erros de `django.core.exceptions.ValidationError` retornam HTTP 400 com listas de mensagens por campo, por exemplo `{"bio": ["Descrição inválida."]}`. Erros sem campo usam `non_field_errors`; parâmetros das mensagens são resolvidos pelo Django. O handler mantém o rollback e o contrato nativo do DRF. Erros inesperados continuam registrados no servidor com resposta pública genérica. O cliente apresenta a identificação do campo e as mensagens recebidas.

## Verificação

`api.test_profile_validation` cobre limites 49/50/200/201, espaços, modelo, ativação e intervenção administrativa sem efeitos em caso de rejeição. `api.test_exceptions` cobre múltiplos campos/mensagens, parâmetros, erros gerais, rollback, HTTP e preservação do tratamento de falhas inesperadas.

`check-participant-pages.cjs` cobre histórico por hash, estado local de busca, envio de mensagens, descarte/aplicação de filtros, limites do formulário, demonstração/login e mensagens de erro por campo. A suíte completa de navegador verifica os demais fluxos dos três acessos. Comandos e resultados em [Verificação da implementação](<Verificacao da implementacao.md>).
