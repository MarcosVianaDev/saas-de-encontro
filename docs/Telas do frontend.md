# Telas do EventConnect

> Este guia registra o comportamento atual da demonstração. As decisões posteriores de favoritos somente pós-match, fotos públicas imutáveis e outfit obrigatório estão nos [requisitos consolidados](<Escopo Técnico.md>); as diferenças estão no [índice e análise](README.md).

Referência visual: [screen0.png](<Imagens - Telas e Protótipos/screen0.png>).

Atualizado em 04/10/2026. Há dois modos de execução: prévia com mocks e fluxo conectado ao Django.

As seis etapas foram implementadas no frontend React/TypeScript existente, com layout mobile-first, tons violeta, cartões claros, fotos em destaque e navegação inferior. No desktop, uma navegação lateral permite acessar diretamente todas as etapas.

| Tela | Endereço local | Interações disponíveis |
|---|---|---|
| Login | http://localhost:8080/#login | Acesso à prévia em mock; autenticação real e cadastro de DEBUG no modo conectado |
| Perfil | http://localhost:8080/#perfil | Nome, sobrenome, nascimento, gênero, bio e seleção/remoção de fotos |
| Filtros | http://localhost:8080/#filtros | Faixa etária, gênero, interesses, finalidade e aplicação das preferências |
| Descoberta | http://localhost:8080/#descobrir | Cartão de pessoa, detalhes, passar, favoritar, curtir e modal de match |
| Mensagens | http://localhost:8080/#mensagens | Busca, lista de conversas e envio; no modo django, persistência e encerramento de match |
| Participantes | http://localhost:8080/#participantes | Busca, categorias Todos/Online/Matches, tamanho das miniaturas e detalhes do perfil |

## Telas administrativas

A área do evento possui navegação Dashboard, Participantes, Moderação, Evento e Mais. No modo conectado, usa login compartilhado e autorização por vínculo/papel no backend. No modo mock, **Explorar administração** ou `#admin-dashboard` abre a demonstração com dados locais e ações em memória, sem login ou consultas à API. Os três fluxos e mockups estão em [Telas administrativas](<Telas administrativas.md>). Endereços `#admin-*`, QR Code, simulação de papéis/eventos, sanções, equipe e relatório agregado estão descritos em [Administração e ingresso](<Administracao e ingresso no evento.md>). O QR Code mock abre uma prévia vinculada visualmente ao evento; o cadastro real por convite exige o modo conectado.

## Funcionamento da prévia

O modo é selecionado no `.env` raiz por `FRONTEND_DATA_MODE=mock|django`. `mock` habilita as telas abaixo com estado em memória; `django` conecta todas as etapas à API real, com sessão Django e persistência no PostgreSQL. Não usa mocks em caso de falha. Após alterar, recrie o frontend com `docker compose up -d --no-deps --force-recreate frontend`. `DJANGO_DEBUG` controla o Django separadamente. Consulte [Demonstração e API](<Demonstracao e API.md>) para a carga automática, credenciais e endpoints.

As observações seguintes descrevem exclusivamente o modo `mock`.

- Dados fictícios e estado em memória; recarregar a página restaura a demonstração.
- O formulário de login não autentica nem cria contas. Google e Apple aparecem desabilitados, identificados como futuros recursos.
- Perfil e filtros ficam disponíveis durante a sessão. A bio exige pelo menos 50 caracteres e é limitada a 200 na interface. Para avançar, são necessárias três fotos; são permitidas até dez, JPG/PNG/WebP de até 10 MB cada. Uploads permanecem somente no navegador.
- Faixa etária, gênero e interesses filtram a descoberta. Interesses usam correspondência com pelo menos uma opção selecionada; a finalidade é uma preferência informativa.
- Passar e curtir avançam o cartão. Alguns participantes têm reciprocidade fictícia predefinida para demonstrar o match e a abertura da conversa.
- A lista de participantes independe dos filtros de descoberta.
- Mensagens enviadas atualizam o chat e sua prévia localmente; não são enviadas a outra pessoa.
- Modais podem ser fechados com Escape, mantêm a navegação por Tab dentro do diálogo e restauram o foco quando possível.
- Fotografias de exemplo do Unsplash são servidas de `frontend/public/images`; as fontes Google Fonts têm alternativas locais do sistema.

## Validação

Compilação: `docker compose exec frontend npm run build`.

Verificação no navegador realizada com Playwright e Microsoft Edge, cobrindo as seis telas, login demonstrativo, validação/seleção de fotos, aplicação de filtros, match, envio de mensagem, busca, categorias e densidade de participantes, fechamento de modal e estado vazio. Layouts verificados nas larguras 320, 375, 768, 1024 e 1440 pixels, sem transbordamento horizontal.

## Integração com backend

O Django Admin continua em `/admin/`. No modo `django`, autenticação, perfil/fotos, filtros, descoberta, decisões/matches, favoritos, mensagens e participantes usam endpoints autenticados. Encerrar match preserva o histórico em modo somente leitura. Conversas são atualizadas por HTTP a cada cinco segundos. WebSocket, pagamentos e processos completos de governança permanecem para etapas posteriores.

No modo conectado, é necessário entrar antes de acessar as etapas. Uma conta nova precisa enviar três fotos e completar o perfil para ativar a participação. A conta demo já tem fotos e conversas iniciais. Atualizar a página recupera o estado do PostgreSQL; erros do backend são apresentados na interface sem usar mocks como alternativa. Login social continua desabilitado.

O teste conectado do participante verificou login, gravação de perfil/filtros, descoberta, participantes e envio real de mensagem, preservada após reload e restart do backend. A atualização administrativa possui 33 testes Django aprovados e validação no navegador, incluindo decodificação independente do QR Code. A cobertura das regras do escopo está registrada em [Verificação da implementação](<Verificacao da implementacao.md>).
