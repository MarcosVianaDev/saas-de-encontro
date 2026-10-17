# Exportação de eventos — etapas 10.3 e 10.4

Implementação em 12/10/2026. A geração é assíncrona no Celery e autorizada somente para conta ativa superuser. Para testes, qualquer estado de evento é aceito, inclusive antes do arquivamento; esse acesso não amplia permissões de ADMIN/MODERATOR/OPERATOR/staff.

Desde **16/10/2026**, a geração e seus retries usam a fila `exports`, atendida por `celery_exports`; as automações continuam em `celery_worker`, na fila `celery`. Os dois workers compartilham o volume de backups existente. Atualize também o novo serviço ao implantar: [filas e operação](<Operacao e desenvolvimento.md#processamento-assíncrono>).

## Uso na interface

No contexto global de um evento, abra Mais. Entre Relatório do evento e Sair da conta, **Exportar dados** solicita o pacote. O próprio botão mostra a etapa/progresso do job e consulta o status a cada dois segundos. Ao concluir, passa a um dropdown **Baixar dados** com as opções **Baixar o Termo** (PDF) e **Baixar ZIP**, sem label separada de conclusão. Em falha ou expiração, Exportar dados permite uma nova tentativa.

Geração não faz download automático ao concluir: escolha o arquivo no dropdown. Apenas uma geração pode estar pendente/processando para cada evento; repetição da requisição retorna o mesmo job. Recargas recuperam a exportação mais recente daquele evento.

## Arquivos e formato

Arquivos ficam em `backend/backups/<UUID do job>/event.zip` e `term.pdf`. Não são publicados como mídia/static nem expostos por caminho de filesystem. O ZIP contém:

- `event.sql`: snapshot com colunas nativas e relações, restaurável no schema isolado `event_export` de um PostgreSQL vazio; não é backup completo do ambiente de produção.
- `snapshot.json`: registros, estrutura, relações, mídias e omissões.
- `index.html`: interface administrativa offline, somente leitura, com consultas por área, busca, relações/detalhes e mídia. Abre diretamente no navegador, sem servidor.
- `media/`: arquivos disponíveis referenciados por registros exportados; arquivos removidos não são copiados. Mídias ausentes são listadas no manifesto.
- `manifest.json`: versão do formato/sistema, exportação/evento, responsável/referência, escopo, contagens, omissões, Legal Holds e hashes SHA-256 dos componentes.
- `verify.py`: verificação local dos hashes após extrair o ZIP (`python verify.py`).
- `README.txt`: instruções para consulta e restauração isolada.

Os scripts `full-clean.ps1` e `full-clean.sh` removem todas as exportações e termos em `backend/backups` ao limpar o banco/Redis, mantendo a pasta vazia e preservando `backend/media`. Essa limpeza é explícita e destrutiva, mediante confirmação `ZERAR` ou opção de execução forçada; não é uma rotina automática de retenção.

O PDF é externo ao ZIP e registra seu SHA-256 final, responsável, escopo, resumo e integridade. O termo gerado está **não assinado**. A API permite registrar um PDF assinado externamente e a referência de encaminhamento; o upload registra evidência/referência, sem verificar criptograficamente a assinatura GOV.BR e sem enviar documentos a terceiros.

A interface offline contém as áreas de consulta administrativa, não as operações mutáveis do aplicativo de produção: Dashboard, Evento/equipe, Participantes/perfis, Moderação, Mensagens/matches, Passes/financeiro, Avisos/suporte, Geolocalização, Consentimentos/preservação, Auditoria e Discovery/interações. Nenhuma chamada de API/produção é executada; CSP bloqueia conexões. Registros exportados alimentam as consultas e os links entre entidades. Os arquivos são dados estáticos, sem placeholders fictícios.

## Isolamento e consistência

O coletor parte do evento e suas participações, segue registros pertencentes a eles e inclui dependências necessárias. Usuários/organização compartilhados nunca são raízes de travessia reversa para buscar outros eventos. Senhas, sessões, grupos/permissões globais, preferências globais de conta e solicitações globais de privacidade não são exportadas. Contexto de evento explícito nos logs tem precedência; auditoria legada é associada por identidade do objeto pertencente ao evento.

Auditoria e dados de Legal Hold associados são obrigatórios. Na seleção personalizada, algumas identidades/dependências podem ser incluídas para manter relações; módulos omitidos são registrados. A exportação não recupera dados já eliminados, nem substitui motor de retenção ou validação jurídica da etapa 9. A versão atual dos modelos determina os metadados disponíveis sobre Legal Hold.

O worker lê o banco numa transação PostgreSQL repeatable-read, copia as mídias disponíveis durante a coleta e gera os arquivos fora da requisição HTTP. A mídia em storage externo não tem transação conjunta com PostgreSQL; desaparecimentos são registrados, e falhas de leitura distintas de ausência interrompem o job. A fotografia é consistente no banco, mas não é um mecanismo de congelamento de políticas/storage externo.

## Job, autorização e recuperação

`ExportJob` possui estados PENDING/PROCESSING/COMPLETED/FAILED, progresso, tentativas, etapas, timestamps, escopo, referência e hashes. Há constraint para um job ativo por evento e lock PostgreSQL durante o processamento. Pedido é auditado e enfileirado somente após commit. Falha de broker atualiza o job com mensagem pública controlada. O Celery tenta novamente até duas vezes, com backoff de 30/60 segundos; depois há retry manual. Processamento sem atualização por uma hora pode ser recuperado pela API, somente se o worker não mantiver o lock.

Conclusão só é gravada após produzir ZIP/PDF e auditoria. Arquivos temporários são removidos; tarefas repetidas não regeneram job concluído. Downloads revalidam superuser, evento da sessão, estado, prazo e SHA-256 e registram auditoria. Uma revogação de autorização do solicitante antes da geração impede executar o job.

O prazo técnico de download padrão é 168 horas (7 dias), configurável por `EXPORT_DOWNLOAD_TTL_HOURS`; zero desativa expiração de acesso. Expiração não apaga arquivos automaticamente e não define política de retenção jurídica. A API cria um novo job para uma exportação expirada, preservando os arquivos e metadados do job original. Não há publicação pública de links.

## API

| Rota relativa a `/api/` | Operação |
|---|---|
| GET `event-admin/exports/` | Último job do evento atual |
| POST `event-admin/exports/` | Criar job; `reference` e `modules` opcionais; sem campos, exportação completa para testes |
| GET `event-admin/exports/{id}/` | Estado/progresso/hash/links |
| POST `event-admin/exports/{id}/` | `action=retry`, `signature` (multipart `file` e `reference`) ou `delivery` (`reference`) |
| GET `event-admin/exports/{id}/download/` | ZIP; `?artifact=pdf` para termo; `?artifact=signed` para termo assinado registrado |

Módulos: participants, moderation, messages, location, passes, notifications, rooms, metrics, consent, audit. Audit é acrescentado obrigatoriamente pelo servidor.

## Instalação e limites de conclusão

Aplicar `events.0008_alter_event_mode_alter_event_radius_m_exportjob` e reiniciar backend/worker. A migração também reconcilia defaults de mode/radius já pendentes no check anterior. O Compose monta `./backend:/app`, portanto os arquivos do worker persistem na pasta solicitada do host. O novo código não executa alteração/eliminação do evento exportado.

A etapa 10.1 (leitura exclusiva integral/auditoria do painel) e o fluxo formal completo da 10.2 continuam separados. Assinatura criptográfica automatizada, encaminhamento externo e políticas aprovadas da etapa 9/12 não foram simulados como funcionalidades prontas. Testes em `api.test_exports` verificam job, autorização, isolamento com usuário/cliente compartilhado, restauração SQL, mídias ausentes, hashes, adulteração e recuperação de falhas.
