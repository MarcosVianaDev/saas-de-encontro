# Documentação do sistema

Consolidação em **12/10/2026**, confrontada com o código e as verificações desta data. A documentação está organizada por finalidade: referência atual, requisitos/backlog e fontes históricas. Os DOCX e os documentos de origem foram preservados.

## Referência atual

Atualização de implementação: [Exportação de eventos](<Exportacao de eventos.md>) documenta a entrega dos itens 10.3/10.4, o botão no acesso global, os arquivos em `backend/backups`, os testes e os limites da assinatura externa.

| Documento | Uso |
|---|---|
| [Estado atual do sistema](<Estado atual do sistema.md>) | Implementação dos três acessos e consolidação das alterações recentes |
| [Operação e desenvolvimento](<Operacao e desenvolvimento.md>) | Ambiente, comandos, automações, mapa de código e contratos recentes |
| [Administração e ingresso no evento](<Administracao e ingresso no evento.md>) | Roteiro atual de cliente, equipe, evento, tópicos, passes e ingresso |
| [Verificação da implementação](<Verificacao da implementacao.md>) | Testes/checks atuais, limitações e regressões |
| [Demonstração do frontend](<Demonstracao do frontend.md>) | Entrada pelo acesso global, login/cadastro simulado e 50 perfis, sem mudar o `.env` |
| [Etapa 10 — verificação e pendências](<Etapa 10 - verificacao e pendencias.md>) | Cobertura dos cards 10.1–10.4, lacunas, dependências e aceite |

## Requisitos e andamento

| Documento | Natureza |
|---|---|
| [Escopo Técnico](<Escopo Técnico.md>) | Requisitos de domínio/arquitetura e consolidações, incluindo exportação formal |
| [Escopo e Ideias](<Escopo e Ideias.md>) | Evolução das decisões de produto; contém propostas anteriores |
| [Trilha de implementação](<trilha de implementacao.md>) | Planejamento original e dependências |
| [Cards abertos](<trilha de implementacao(aberto).md>) | Backlog 9–12; etapa 10 revisada em 12/10/2026 |
| [Cards concluídos](<trilha de implementacao(fechado).md>) | Registro histórico de conclusão das etapas 1–8 |
| [Implementação das etapas 1 a 8](<Implementacao - etapas 1 a 8.md>) | Entrega de 04/10/2026; números de testes históricos |

Um requisito documentado não comprova entrega. A conclusão histórica de uma etapa não substitui a validação de hoje. Para exportação, a seção final **Exportação auditável do evento** do Escopo Técnico prevalece sobre textos antigos que ainda deixam todo o formato em aberto.

## Manuais, telas e fontes preservadas

| Documento | Como usar |
|---|---|
| [Manual do Participante](<Manual do Participante.md>) | Manual de requisitos/origem; conferir o Estado atual para comportamento entregue |
| [Manual do Contratante e Organizador](<Manual do Contratante e Organizador.md>) | Regras e intenções; não presume recursos implementados |
| [Telas do frontend](<Telas do frontend.md>) | Registro anterior da demonstração e integração |
| [Telas administrativas](<Telas administrativas.md>) | Referências de fluxos e mockups |
| [Fluxo de Administração do Evento](<Fluxo - Administração do Evento.md>) | Especificação de fluxo e decisões |
| [Fluxo — Participantes](<Fluxo - Administração - Participantes.md>) | Especificação da operação de participantes |
| [Fluxo — Moderação](<Fluxo - Administração - Moderação.md>) | Especificação da operação de ocorrências |
| [Demonstração e API](<Demonstracao e API.md>) | Registro anterior da carga/API; mapa atual em Operação e desenvolvimento |
| [README anterior](<README - versão anterior.md>) | Histórico anterior do projeto |

Os DOCX homônimos são fontes preservadas, sem sincronização automática com Markdown: Escopo Técnico, Escopo e Ideias, Manuais, os três Fluxos, Demonstração e API, Telas do usuário, Verificação da implementação e README. Os Markdown atuais são o ponto de manutenção. As imagens em [Imagens — Telas e Protótipos](<Imagens - Telas e Protótipos/>) são referências visuais, não evidência de funcionalidade persistida.

## Arquivo histórico desta reorganização

- [Índice e análise de 04/10/2026](<historico/Indice documental - 04-10-2026.md>): origens dos DOCX e divergências daquela revisão.
- [Verificação de 04/10/2026](<historico/Verificacao da implementacao - 04-10-2026.md>): resultado anterior às alterações atuais.
- [Administração e ingresso de 04/10/2026](<historico/Administracao e ingresso no evento - 04-10-2026.md>): fluxo anterior para comparação.

## Alterações consolidadas

Cadastro global de cliente com conta/equipe; responsável de evento vinculado ao cliente; equipe editável e controles de senha; criação/solicitação de eventos; Mais com abas/accordions; toggles; tema Claro/Escuro/Automático com cores por acesso; UF de residência; tópicos em banco com regras por evento e mínimo obrigatório; notificações por contexto e de mensagens/passes; revelação automática de likes; relatório pós-evento; Presente inicial gratuito imediato/agendado, com notificação, unicidade e validação de prazo.

Exportação ZIP, `ExportJob`, worker, consulta offline, manifesto/hashes e termo PDF externo foram implementados em 12/10/2026; consulte Exportação de eventos. Arquivamento existe, mas leitura exclusiva e auditoria geral do painel ainda têm lacunas próprias da etapa 10.1. Assinatura criptográfica automatizada e encaminhamento externo não fazem parte do botão de testes.

## Validação e manutenção

Última validação em 12/10/2026: **19 scripts de navegador aprovados** na entrega da [demonstração do frontend](<Demonstracao do frontend.md>), com build aprovado e 3 auxiliares concluídos. A última execução de backend, da etapa anterior, aprovou **181 testes**, `manage.py check` e check de migrações, sem migrações pendentes. Mudanças, execução isolada e limites no [relatório de correção dos testes](<Correcao dos testes - 12-10-2026.md>). O diagnóstico anterior foi preservado como histórico.

Atualize o Estado atual e o contrato operacional ao mudar comportamento. Registre comando/data/resultado em Verificação. Atualize o card correspondente sem fechar entregas parciais. Preserve requisitos e histórico; mantenha explícitas as decisões pendentes.
