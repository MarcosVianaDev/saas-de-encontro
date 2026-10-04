# Verificação da implementação

> Os DOCX foram consolidados em Markdown em 04/10/2026. As decisões finais de escopo ampliam os requisitos considerados por esta verificação. Favoritos pós-match, outfit obrigatório, imutabilidade das fotos públicas, permissões delegáveis, geolocalização, automações do ciclo completo, alertas de 10/20 denúncias, concessão manual de passes e exportação auditável precisam de nova verificação específica. A cobertura e os testes registrados abaixo não foram reexecutados nesta alteração documental. Consulte o [índice e análise](README.md).

Atualizado em 04/10/2026, após a implementação do painel administrativo e do ingresso por QR Code.

Fontes: [Escopo Técnico](<Escopo Técnico.md>), [Escopo e Ideias](<Escopo e Ideias.md>), [README](../README.md) e código atual. Os documentos de escopo definem os requisitos; este documento registra a cobertura implementada.

## Estado atual

Infraestrutura Docker funcional com Django/DRF/Daphne, React/TypeScript/Vite, PostgreSQL, Redis, Celery, Nginx e Traefik. Os 19 apps têm modelos, migrações e registros no Admin. As seis telas funcionam com mocks locais ou endpoints reais, conforme `FRONTEND_DATA_MODE`.

`backend/start.py` aplica migrações e executa `seed_demo` antes do servidor quando DEBUG=True. A carga preenche as entidades dos 19 apps com UUIDs estáveis, transação, lock PostgreSQL e marcador de auditoria. Reinicializações preservam alterações. DEBUG=False impede a carga, mas não apaga dados já criados. Celery e comandos de teste não executam automaticamente essa inicialização.

Fixtures incluem 12 pessoas, oito conversas, perfis/fotos, preferências, interações, matches, organizações, eventos, salas, passes, pagamentos fictícios e exemplos de governança. Moderação fica em um evento histórico separado. Os registros financeiros não executam cobranças.

## Novos fluxos administrativos documentados

O frontend também oferece demonstração administrativa em `FRONTEND_DATA_MODE=mock`: três estados de evento, participantes com situações distintas, ocorrências, evidências fictícias, notas/histórico, bloqueios, equipe e relatório. As ações operam em memória e não consultam a API. A verificação no navegador cobre suspensão/reativação, assumir/adicionar nota/resolver/reabrir, simulação de papéis, troca de evento, QR Code demonstrativo e todas as áreas em 320, 375, 768 e 1440 pixels, confirmando ausência de chamadas ao backend.

Foram incorporados os três documentos de administração do evento e os mockups `screen1.png`, `screen2.png` e `screen3.png`, reunidos em [Telas administrativas](<Telas administrativas.md>). Eles especificam Dashboard, Evento/QR Code, lista/ficha de participantes, filtros, sanções e fila/investigação/decisões de moderação. As versões Markdown preservam os textos originais.

O painel React administrativo, direcionamento por papel/vínculo após login, ingresso por convite assinado, permissões por evento e ciclo de moderação foram implementados. Há suspensão por participação, banimento, notas, resolução/reabertura, histórico de auditoria, indicadores de bloqueios e evidências autorizadas. Métricas são calculadas na consulta; atividade recente utiliza `last_seen_at`. Equipe e relatório são consultivos. Detalhes e limites: [Administração e ingresso](<Administracao e ingresso no evento.md>).

## Cobertura por domínio

| Domínio | Implementado | Pendente |
|---|---|---|
| Identidade | Sessão Django, login/logout, CSRF, cadastro demo somente em DEBUG | Recuperação de senha, login social e autenticação de produção |
| Administração | Django Admin e painel React; papéis ADMIN/MODERATOR/OPERATOR e escopo por evento na API administrativa | Isolamento completo no Django Admin, escopo por organização/sala e edição de equipe no React |
| Perfil | Edição, idade calculada, validação de campos/bio, ativação pela API com três fotos e principal | Pré-preenchimento global, catálogo tipado e estados definitivos |
| Fotos | Upload local até dez fotos JPEG/PNG/WebP de 10 MB, três públicas, adicionais após match, acesso autenticado | S3/MinIO e upload de outfit separado |
| Descoberta | Filtros persistidos, exclusão de decisões anteriores e participantes indisponíveis; sem flexibilização automática | Catálogo e semântica completa das preferências |
| Interações e matches | LIKE/PASS com histórico, reciprocidade, par canônico único, locks e conversa automática | Invariantes equivalentes nas operações administrativas e revelações comerciais |
| Mensagens | Autorização das partes, envio com match ativo, encerramento somente leitura e restrição por bloqueio | WebSocket, anexos, recibos e notificações externas |
| Frontend | Seis telas do participante e painel administrativo, QR Code, equipe consultiva e relatório agregado | Interfaces comerciais, equipe editável, gráficos e exportação de relatórios |
| Bloqueios/moderação | API administrativa por evento/papel, casos, notas, decisões, suspensão/reativação, banimento, indicadores de bloqueios e download auditado de evidências | Fluxo de denúncia/bloqueio do participante, coleta de evidências, catálogo formal de motivos e alertas automáticos/entre eventos |
| Passes/pagamentos | Modelos/Admin e exemplos persistidos | Consumo atômico, saldo, expiração, revelação, estados financeiros e confirmação idempotente |
| Consentimento/retenção | Modelos/Admin e exemplos, incluindo legal hold | Concessão/revogação, política aprovada e eliminação/anonimização operacional |
| Auditoria | Triggers append-only, ações administrativas da API e histórico de casos baseado em AuditLog | Cobertura das alterações pelo Django Admin e demais serviços |
| Notificações/métricas | Notificações internas de ocorrência administrativa e totais/atividade calculados por evento | E-mail/push, métricas históricas por intervalo/sala e processamento assíncrono |
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

Última execução em 04/10/2026: 33 testes aprovados, sem migrações pendentes e compilação TypeScript/Vite aprovada. Além da cobertura anterior, foram verificados login administrativo sem participação, papéis e isolamento, suspensão/reativação por evento, banimento, atribuição/notas/resolução/reabertura, notificações internas, atividade recente real, evidências autorizadas e ingresso/cadastro por convite assinado, incluindo DEBUG desativado e CSRF.

A verificação anterior com Playwright/Edge cobriu as seis telas do participante, persistência após reload/restart e modo mock. A verificação administrativa cobre login por vínculo, navegação, filtros, ficha, modal de suspensão sem executar sanção na base local, restauração de sessão, QR Code decodificado por leitor independente e ingresso de conta existente. As áreas administrativas foram verificadas em 320, 375, 768 e 1440 pixels. Não há cobertura completa de concorrência, governança ou produção.

Instruções: [Demonstração e API](<Demonstracao e API.md>) e [Telas do frontend](<Telas do frontend.md>).
