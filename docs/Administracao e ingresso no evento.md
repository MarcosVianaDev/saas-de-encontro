# Administração e ingresso no evento

Guia operacional de **12/10/2026**. A [versão anterior](<historico/Administracao e ingresso no evento - 04-10-2026.md>) foi preservada. Regras completas: [Estado atual](<Estado atual do sistema.md>); ambiente e comandos: [Operação e desenvolvimento](<Operacao e desenvolvimento.md>).

## Acesso, cliente e equipe

Use o modo real para persistir operações. Superuser acessa a administração global; a equipe acessa eventos conforme vínculo/papel. Participantes ingressam por convite válido. Staff sozinho não equivale a gestor global.

1. Use Novo cliente, com nome, e-mail e telefone.
2. Complete organização, cargo e observações na ficha do cliente.
3. Defina a senha pelo botão do Django Admin; não há envio de recuperação por e-mail nesse fluxo.
4. Cadastre integrantes com conta e função: Responsável pelo evento, Moderador ou Operador.
5. Clique no card para editar; Redefinir senha abre a operação técnica correspondente.

A seção Acesso ao sistema foi removida. Criar integrante rejeita colisão com conta existente; não vincula genericamente qualquer conta por e-mail. Alterar equipe de cliente não sincroniza a equipe de eventos anteriores.

## Cadastro de evento

Novo evento fica nas ações rápidas, lista de eventos e ficha do cliente. Cliente/Modalidade formam a primeira linha; depois Nome e Descrição; Início/Término ficam lado a lado abaixo da descrição. Presencial/Híbrido exigem Latitude/Longitude e Raio/Limite adicional. Selecione o responsável entre membros ativos do cliente.

O cadastro global cria Agendado. A solicitação feita pela gestão local cria Rascunho e aguarda aprovação global. A ativação automática ao completar o perfil é uma opção exclusiva de Online, validada no servidor.

### Tópicos

O catálogo é mantido em Mais → Participantes global: nome, opções separadas por vírgula e múltipla escolha. Interesses e Finalidade no evento são criados pela migração sem Outros; o mock mantém os catálogos antigos.

Expanda Tópicos do participante no cadastro global. Usar no evento fica à esquerda; Obrigatório à direita; labels acima dos toggles. Clicar no card mostra opções. Mínimo obrigatório aparece apenas em múltipla escolha obrigatória e com card aberto; fica à direita das opções que quebram em linhas. Aceita de 1 a 5, limitado pelo número de opções. Escolha única obrigatória exige uma resposta.

Desabilitar o tópico desmarca a obrigatoriedade. Recolher preserva o valor. A API aplica os requisitos ao salvar perfil e ativar participação.

### Presente inicial

Habilite Presente inicial e informe nome do passe, quantidade de revelações **ou** duração, além do atraso de entrega.

- 0: passe concedido e ativado ao ativar o perfil.
- Maior que 0: prazo desde o início previsto, com entrega aos perfis ativos quando o evento está Em andamento.
- Perfil ativado após o prazo: entrega na ativação, se ainda elegível.

Vale para todas as modalidades. A entrega deve ser anterior ao término; igualdade ou prazo além do término é rejeitado no formulário e servidor. A concessão gera notificação e ocorre uma vez por participação, mesmo com repetição da tarefa/reativação. Revogação não gera novo presente automático. Duração do passe temporal conta da concessão. Entrega agendada depende do worker/Beat e da próxima execução elegível, hoje a cada 30 segundos.

## Equipe do evento e Mais

Adicionar integrante fica à direita do cabeçalho. Editar oculta os demais cards e vira Cancelar; Cancelar descarta rascunho e restaura a lista; Salvar fica à direita. Permissões usam toggles. Não participa deste evento no seletor de Papel salva o vínculo inativo; outro papel o reativa. A gestão global controla ADMIN; a gestão local pode delegar temporariamente.

Mais do evento contém Avisos do Evento, Suporte e Passes em acordeon inicialmente fechado, com uma seção expandida por vez. Mais global tem abas Eventos, Participantes e Conta; Conta reúne sair e acesso ao Django Admin. Claro/Escuro/Automático compartilham preferência local e preservam a identidade de acesso.

## Ingresso e operação

O convite/QR Code permite ingresso conforme estado/validade. A ativação exige perfil válido, três fotos públicas e uma principal, requisitos do evento e, no fluxo convencional, outfit capturado pela equipe e localização aplicável. Online pode ativar automaticamente, sem outfit, mantendo fotos, bio e requisitos.

A operação inclui ativação, moderação, suporte, intervenções, avisos, passes e relatórios conforme permissão. Revelação de likes é cronológica e respeita quantidade/duração. Concessão manual cabe ao Operador autorizado; presente inicial é um fluxo automático específico. Concessão declarada não confirma recebimento financeiro externo.

## Arquivamento

Arquivamento automático ocorre quinze dias após encerramento e mantém consultas autorizadas. Existem lacunas de leitura exclusiva, consulta geral de auditoria e exportação; consulte [a etapa 10](<Etapa 10 - verificacao e pendencias.md>). O botão de exportação para testes está disponível no acesso global do evento; ver [Exportação de eventos](<Exportacao de eventos.md>).
