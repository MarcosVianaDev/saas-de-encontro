# Documentação do SaaS de Encontro

Consolidação e análise em 04/10/2026, abrangendo o README do projeto, os documentos Markdown, os 11 DOCX e os quatro mockups de `docs`. Os Markdown são a referência de leitura e manutenção. Os DOCX originais foram preservados, inclusive as alterações locais existentes.

## Como consultar

- [README do projeto](../README.md): apresentação, arquitetura e execução local.
- [Escopo Técnico](<Escopo Técnico.md>) e [Escopo e Ideias](<Escopo e Ideias.md>): requisitos e evolução das decisões.
- [Manual do Participante](<Manual do Participante.md>) e [Manual do Contratante e Organizador](<Manual do Contratante e Organizador.md>): regras previstas para cada público.
- [Telas do frontend](<Telas do frontend.md>): comportamento da demonstração e integração atual do participante.
- [Telas administrativas](<Telas administrativas.md>): síntese dos três fluxos completos de administração.
- [Administração e ingresso no evento](<Administracao e ingresso no evento.md>): operação atual, papéis, endpoints e QR Code.
- [Demonstração e API](<Demonstracao e API.md>): carga de dados fictícios e endpoints do participante.
- [Verificação da implementação](<Verificacao da implementacao.md>): cobertura e limitações registradas antes desta consolidação.
- [README anterior](<README - versão anterior.md>): histórico, sem substituir o README atual.
- [Trilha de implementação](<trilha de implementacao.md>): sequência proposta para reconciliar o domínio, completar o MVP e preparar o lançamento.

## Origem e destino dos DOCX

| Fonte preservada | Markdown consolidado | Tratamento |
|---|---|---|
| [Demonstração e API.docx](<Demonstração e API.docx>) | [Demonstracao e API.md](<Demonstracao e API.md>) | Markdown atual preservado: DOCX registra estado anterior de 03/10/2026. |
| [Escopo e Ideias.docx](<Escopo e Ideias.docx>) | [Escopo e Ideias.md](<Escopo e Ideias.md>) | Conteúdo textual integral consolidado, com notas de precedência. |
| [Escopo Técnico.docx](<Escopo Técnico.docx>) | [Escopo Técnico.md](<Escopo Técnico.md>) | Conteúdo textual integral consolidado, com notas de precedência. |
| [Fluxo - Administração - Moderação.md.docx](<Fluxo - Administração - Moderação.md.docx>) | [Fluxo - Administração - Moderação.md](<Fluxo - Administração - Moderação.md>) | Conteúdo textual integral consolidado, com notas de precedência. |
| [Fluxo - Administração - Participantes.md.docx](<Fluxo - Administração - Participantes.md.docx>) | [Fluxo - Administração - Participantes.md](<Fluxo - Administração - Participantes.md>) | Conteúdo textual integral consolidado, com notas de precedência. |
| [Fluxo - Administração do Evento.md.docx](<Fluxo - Administração do Evento.md.docx>) | [Fluxo - Administração do Evento.md](<Fluxo - Administração do Evento.md>) | Conteúdo textual integral consolidado, com notas de precedência. |
| [Manual do Contratante e Organizador.docx](<Manual do Contratante e Organizador.docx>) | [Manual do Contratante e Organizador.md](<Manual do Contratante e Organizador.md>) | Conteúdo textual integral consolidado, com notas de precedência. |
| [Manual do Participante.docx](<Manual do Participante.docx>) | [Manual do Participante.md](<Manual do Participante.md>) | Conteúdo textual integral consolidado, com notas de precedência. |
| [README.md.docx](<README.md.docx>) | [../README.md](<../README.md>) | Conteúdo novo incorporado; informações operacionais atuais preservadas. |
| [Telas do usuário.docx](<Telas do usuário.docx>) | [Telas do frontend.md](<Telas do frontend.md>) | Markdown atual preservado: DOCX registra estado anterior de 03/10/2026. |
| [Verificação da implementação.docx](<Verificação da implementação.docx>) | [Verificacao da implementacao.md](<Verificacao da implementacao.md>) | Markdown atual preservado: DOCX registra estado anterior de 03/10/2026. |

Os DOCX contêm texto, incluindo tabelas e blocos de código escritos em Markdown, sem imagens incorporadas, tabelas nativas, notas de rodapé ou cabeçalhos com conteúdo adicional. A consolidação mantém esse conteúdo e organiza títulos e parágrafos para leitura em Markdown.

## Precedência e divergências encontradas

Os documentos de escopo acumulam propostas e consolidações sucessivas. As seções finais específicas de cada assunto prevalecem sobre as hipóteses iniciais; o texto histórico foi preservado para não perder decisões ou contexto. Quando as fontes não resolvem uma divergência, ela permanece pendente. Requisito aprovado não comprova implementação.

| Assunto | Proposta ou registro anterior | Definição consolidada / consequência |
|---|---|---|
| Favoritos | `screen0.png` e o guia atual mostram favorito na Descoberta. | Requisito novo: apenas PASS/LIKE na Descoberta; favorito pertence ao pós-match, em Mensagens. A interface atual precisa ser alinhada. |
| Ativação e fotos | Ativação com três fotos e outfit tratado como recurso posterior. | Três fotos públicas imutáveis para o participante após ativação e outfit obrigatório capturado pela equipe. Remoção administrativa de foto pública exige desativação, reposição e validação. |
| Permissões | Matrizes preliminares dos fluxos e permissões fixas da API atual. | Superuser representa Administração Global; staff permite acesso técnico ao Django Admin. Administrador do Evento gerencia equipe e pode delegar temporariamente a Moderador; Moderador não acessa métricas/relatórios. Permissões operacionais precisam de alinhamento. |
| Bloqueio e sanções | Bloqueio pessoal irreversível no evento; textos novos mencionam desbloqueio operacional e banimento reversível por geolocalização. | Bloqueio pessoal, suspensão e banimento são conceitos distintos. A abrangência do desbloqueio operacional e a compatibilidade com o banimento definitivo dos fluxos iniciais ainda precisam de definição explícita. |
| Sinais de segurança | Mockups e fluxos iniciais destacam múltiplos bloqueios. | Múltiplos bloqueios não geram alerta automático. Dez denúncias válidas alertam a moderação; vinte desativam o perfil para análise e notificam a Administração Global. Infundadas não contam; recorrência não bane automaticamente em novos eventos. |
| Geolocalização | Tolerância e limiares inicialmente indefinidos; saída do raio sem restrição. | Raio e limite adicional padrão de 1.000 m cada; cinco retries de um minuto; velocidade acima de 60 km/h ou duas leituras além do limite máximo geram sinais. Falha técnica, recusa de localização e anomalia têm tratamentos distintos. Consulta de histórico somente por gestores, em Pausado ou após encerramento, com auditoria. |
| Ciclo de vida | Três estados nos mockups; abertura e início descritos genericamente. | Sete estados. Abertura manual desde duas horas antes; automática cinco minutos antes. Início no horário previsto se abertura manual; dez minutos depois se automática. Tarja final de quinze minutos; pausa não prorroga; arquivamento quinze dias após encerramento. |
| Exportação | ZIP/HTML com estrutura e integridade a definir. | Exportação formal exclusiva do superuser: ZIP com SQL restrito ao evento, SPA estática somente leitura, manifesto e hashes; SHA-256 final e termo PDF externo assinável. Logs do evento obrigatórios, minimização e auditoria do procedimento. |
| Passes e pagamentos | Três modalidades comerciais, gateway e estados financeiros planejados. | Versão atual do escopo: concessão manual por Operador autorizado, com valor configurado ou cortesia; sem confirmação externa de recebimento. Revogação preserva a venda declarada original. Gateway, conciliação e estorno são evolução futura. |
| Retenção | Textos iniciais podem sugerir exclusão no encerramento. | Encerramento, arquivamento e eliminação são processos distintos; quinze dias é regra operacional. Retenção depende da categoria e de LegalHold. Não foi definido prazo final de geolocalização. |
| MVP e produção | S3/MinIO e infraestrutura definitiva aparecem como arquitetura futura. | Validação em VPS/homelab com storage local e dados fictícios. Preparação de produção e seus controles ficam para antes do lançamento. |

As definições detalhadas de geolocalização, ciclo de vida, exportação, passes e segurança do MVP estão nas seções finais de Escopo Técnico, Escopo e Ideias e Fluxo de Administração do Evento. Os manuais foram preservados integralmente e remetem a essas atualizações posteriores.

## Referências visuais

| Arquivo | Conteúdo analisado | Uso |
|---|---|---|
| [screen0.png](screen0.png) | Login, perfil, filtros, descoberta, mensagens e participantes. | Referência visual; favorito na Descoberta diverge da decisão posterior. |
| [screen1.png](screen1.png) | Dashboard, evento, QR Code, participantes, moderação, equipe e relatório. | Referência visual; os três estados ilustrados não cobrem o ciclo final completo. |
| [screen2.png](screen2.png) | Filtros/ficha de participantes, suspensão e remoção. | Ações globais exigem permissão global; não decorrem do papel de evento. |
| [screen3.png](screen3.png) | Fila, evidências, notas, histórico e decisões de moderação. | Contagens de bloqueios são ilustrativas; aplicar os requisitos finais de denúncias. |

## Limites desta análise

Esta alteração consolida documentação; não modifica o código da aplicação nem executa novamente a suíte de testes. Os números de testes e validações existentes nos guias continuam sendo registros das verificações anteriores. Os DOCX de demonstração, telas e verificação registravam 15 testes em 03/10/2026; os Markdown atuais registram a atualização administrativa com 33 testes em 04/10/2026 e foram preservados.

A política LGPD é citada nas fontes por um link externo. Seu conteúdo não está na pasta analisada e não foi importado ou considerado validado por esta consolidação. Permanecem as pendências jurídicas registradas nas próprias fontes.
