# Verificação da implementação

Atualizado em 03/10/2026, após a carga automática de DEBUG e a integração das telas com a API.

Fontes: [Escopo Técnico](<Escopo Técnico.docx>), [Escopo e Ideias](<Escopo e Ideias.docx>), [README](../README.md) e código atual. Os documentos de escopo definem os requisitos; este documento registra a cobertura implementada.

## Estado atual

Infraestrutura Docker funcional com Django/DRF/Daphne, React/TypeScript/Vite, PostgreSQL, Redis, Celery, Nginx e Traefik. Os 19 apps têm modelos, migrações e registros no Admin. As seis telas funcionam com mocks locais ou endpoints reais, conforme `FRONTEND_DATA_MODE`.

`backend/start.py` aplica migrações e executa `seed_demo` antes do servidor quando DEBUG=True. A carga preenche as entidades dos 19 apps com UUIDs estáveis, transação, lock PostgreSQL e marcador de auditoria. Reinicializações preservam alterações. DEBUG=False impede a carga, mas não apaga dados já criados. Celery e comandos de teste não executam automaticamente essa inicialização.

Fixtures incluem 12 pessoas, oito conversas, perfis/fotos, preferências, interações, matches, organizações, eventos, salas, passes, pagamentos fictícios e exemplos de governança. Moderação fica em um evento histórico separado. Os registros financeiros não executam cobranças.

## Novos fluxos administrativos documentados

Foram incorporados os três documentos de administração do evento e os mockups `screen1.png`, `screen2.png` e `screen3.png`, reunidos em [Telas administrativas](<Telas administrativas.md>). Eles especificam Dashboard, Evento/QR Code, lista/ficha de participantes, filtros, sanções e fila/investigação/decisões de moderação. As versões Markdown preservam os textos originais.

O painel React administrativo, direcionamento por papel após login, ingresso por QR Code seguro, permissões completas por evento, métricas automáticas e ciclo operacional de moderação continuam pendentes. As matrizes de papéis são preliminares. Nenhuma tela, API ou regra foi implementada nesta atualização documental; a validação de código registrada abaixo se refere à implementação anterior.

## Cobertura por domínio

| Domínio | Implementado | Pendente |
|---|---|---|
| Identidade | Sessão Django, login/logout, CSRF, cadastro demo somente em DEBUG | Recuperação de senha, login social e autenticação de produção |
| Administração | Modelos, busca, autocomplete, permissões nativas | Papéis e escopo por organização/evento/sala |
| Perfil | Edição, idade calculada, validação de campos/bio, ativação pela API com três fotos e principal | Pré-preenchimento global, catálogo tipado e estados definitivos |
| Fotos | Upload local até dez fotos JPEG/PNG/WebP de 10 MB, três públicas, adicionais após match, acesso autenticado | S3/MinIO e upload de outfit separado |
| Descoberta | Filtros persistidos, exclusão de decisões anteriores e participantes indisponíveis; sem flexibilização automática | Catálogo e semântica completa das preferências |
| Interações e matches | LIKE/PASS com histórico, reciprocidade, par canônico único, locks e conversa automática | Invariantes equivalentes nas operações administrativas e revelações comerciais |
| Mensagens | Autorização das partes, envio com match ativo, encerramento somente leitura e restrição por bloqueio | WebSocket, anexos, recibos e notificações externas |
| Frontend | Seis telas, diretório, favoritos persistidos e modos mock/debug | Interfaces dos demais domínios |
| Bloqueios/moderação | Modelos/Admin e consulta de bloqueios, suspensão e banimento na API | Fluxo do participante, motivos/evidências, decisões, notificações e alertas entre eventos |
| Passes/pagamentos | Modelos/Admin e exemplos persistidos | Consumo atômico, saldo, expiração, revelação, estados financeiros e confirmação idempotente |
| Consentimento/retenção | Modelos/Admin e exemplos, incluindo legal hold | Concessão/revogação, política aprovada e eliminação/anonimização operacional |
| Auditoria | Triggers append-only e registros das operações principais da API | Cobertura administrativa e demais serviços |
| Notificações/métricas | Modelos/Admin e exemplos | Geração automática, escopo administrativo/sala e processamento assíncrono |
| Celery | Worker e tarefa de ping | Tarefas de domínio e agendamento; Celery Beat não está instalado |

## Limites das garantias

Ativação, reciprocidade e autorização de mensagens são verificadas na API. Cadastros pelo Admin ou código não reutilizam automaticamente todas essas regras. `save()` e operações em lote não executam `full_clean()`. A presença de modelos e constraints não comprova conformidade com todo o escopo.

`BaseModel.clean()` foi corrigido para aceitar campos globais com `event=None`. Relações indiretas, como consumo de passes e mensagens criadas fora da API, ainda precisam de invariantes explícitas. Querysets e autocomplete administrativos não implementam todo o isolamento por organização/evento/sala.

Fotos fictícias são assets públicos; uploads reais exigem autorização. A finalidade do filtro é informativa. O diretório independe dos filtros de descoberta. Conversas usam HTTP a cada cinco segundos, sem consumers WebSocket. Personagens não enviam respostas automáticas.

## Próximas implementações

1. Reutilizar serviços no Admin e tarefas, completar invariantes indiretas e impedir atalhos que contornem ativação, reciprocidade ou autorização.
2. Definir papéis e filtrar consultas, formulários, ações e autocomplete por contexto.
3. Completar perfil global, campos personalizados, outfit, estados e elegibilidade.
4. Implementar bloqueios/denúncias pelo participante, moderação, alertas entre eventos, consentimentos e notificações.
5. Implementar benefícios e pagamentos com regras comerciais definidas, idempotência e controle de concorrência.
6. Completar tempo real, métricas e tarefas operacionais; automatizar retenção apenas após definir a política e preservação legal.

Não substituir vínculos `PROTECT` por exclusão em cascata sem política explícita. Prazos jurídicos, regras fiscais de repasse, anexos, versionamento da API e infraestrutura de produção continuam em aberto.

## Validação concluída

```powershell
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend python manage.py test tests api --noinput
docker compose exec frontend npm run build
```

Última execução: 15 testes aprovados, sem migrações pendentes e compilação TypeScript/Vite aprovada. Cobertura: Admin, carga dos domínios, idempotência, DEBUG desativado, autenticação/CSRF, isolamento entre eventos, perfil/filtros, match, encerramento, mensagens e acesso a uploads.

Playwright/Edge verificou login, perfil, filtros, descoberta, participantes e mensagens reais persistidas após reload. Reiniciar o backend preservou a mensagem e manteve apenas um marcador de carga. O modo mock passou na verificação das seis telas, interações e cinco larguras responsivas. Não há cobertura completa de concorrência, governança ou produção.

Instruções: [Demonstração e API](<Demonstracao e API.md>) e [Telas do frontend](<Telas do frontend.md>).
