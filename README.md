# SaaS de Encontro

## Estado atual e execução local

O ambiente contém a infraestrutura, as seis telas React/TypeScript do participante, o painel administrativo do evento e o backend Django modular com migrações e Django Admin. As telas do participante seguem `docs/screen0.png` e podem usar mocks locais ou a API real com dados persistidos no PostgreSQL. O painel administrativo segue `docs/screen1.png`, `docs/screen2.png` e `docs/screen3.png` e usa a API autenticada.

- Python 3.14 no container, com virtualenv `/opt/venv`; `.venv` local usa o Python 3.12 disponível na máquina.
- Django 5.2.17 LTS, DRF, Channels/Daphne, Celery e psycopg; versões resolvidas em `requirements.lock`.
- Node 26.10.0 Current, React/TypeScript e Vite; dependências fixadas em `frontend/package-lock.json`.
- PostgreSQL 18, Redis 8, Nginx stable e Traefik 3 em containers.
- Fluxo HTTP: navegador → Traefik → Nginx → React ou Django. A porta 8080 é publicada em `0.0.0.0`, permitindo acesso por qualquer interface IPv4 do host. PostgreSQL e Redis permanecem na rede interna do Compose.
- PostgreSQL e Redis usam volumes persistentes. Fotos enviadas usam storage local em `backend/media/`, persistido pelo bind mount. MinIO/S3 e Celery Beat ficam para uma próxima etapa.

Na primeira execução, copie `.env.example` para `.env` e substitua os segredos de exemplo. O arquivo `.env` local já foi gerado com valores aleatórios e não deve ser versionado.

```powershell
docker compose up -d --build --wait
docker compose ps
```

Acesse http://localhost:8080 e http://localhost:8080/api/health/. O endpoint verifica as conexões reais com PostgreSQL e Redis.

Na rede local, use `http://<IP-do-computador>:8080`. Neste ambiente, o endereço é **http://192.168.1.32:8080**. O `.env` define `HTTP_BIND_ADDRESS=0.0.0.0`, `HTTP_PORT=8080` e `DJANGO_ALLOWED_HOSTS=*`; o backend e o Vite também escutam em `0.0.0.0` dentro dos containers. Login e escritas continuam protegidos por CSRF: acessos pela mesma origem funcionam sem cadastrar cada IP em `DJANGO_CSRF_TRUSTED_ORIGINS`. Origens diferentes devem ser autorizadas explicitamente.

O Firewall do Windows deste host possui a regra `EventConnect-HTTP-8080`, permitindo TCP 8080 da sub-rede local nos perfis Privado e Domínio. Em outro computador, a porta deve estar liberada no firewall correspondente. Para mudar o endereço de escuta ou a porta, ajuste o `.env` e recrie os containers com `docker compose up -d --force-recreate --wait`.

As telas de login, perfil, filtros, descoberta, mensagens e participantes estão descritas em [Telas do frontend](<docs/Telas do frontend.md>), com endereços de acesso e limites da demonstração.

O `.env` seleciona a fonte de dados do frontend:

```dotenv
FRONTEND_DATA_MODE=mock
```

- `mock`: usa a demonstração com dados fictícios mantidos pelo próprio frontend.
- `debug`: conecta as seis telas à API real: login, perfil/fotos, filtros, descobertas, matches, favoritos, participantes e mensagens persistidos. Não há fallback para mocks.

Depois de alterar o valor, execute `docker compose up -d --no-deps --force-recreate frontend` e recarregue o navegador. A chave é independente de `DJANGO_DEBUG`. O Compose expõe ao Vite somente `VITE_FRONTEND_DATA_MODE`, sem transmitir os segredos do backend ao frontend. As variáveis Vite são incorporadas durante a compilação; um build estático deve ser recompilado após mudar o modo.

O painel React administrativo implementa Dashboard, Evento/QR Code, Participantes, Moderação, Equipe consultiva e Relatório agregado, com base em `screen1.png`, `screen2.png` e `screen3.png`. O login reconhece vínculos e papéis por evento; o QR Code vincula login/cadastro ao evento por convite assinado. Consulte [Administração e ingresso](<docs/Administracao e ingresso no evento.md>) para acesso, permissões e limites atuais, e [Telas administrativas](<docs/Telas administrativas.md>) para os fluxos funcionais.

### Backend e Django Admin

Acesse **http://localhost:8080/admin/**. O administrador local usa o login `admin`; a senha aleatória está em `.tools/admin-credentials.json`, ignorado pelo Git. Para outro ambiente, crie seu próprio acesso:

```powershell
docker compose exec backend python manage.py createsuperuser
```

O código está em `backend/`, com `manage.py`, `config/settings`, URLs, ASGI/WSGI e Celery. Os 19 apps de `backend/apps/` seguem a proposta abaixo e possuem modelos registrados no Admin, com pesquisa e seleção de vínculos por autocomplete. O usuário customizado de `accounts` utiliza UUID e a autenticação nativa do Django; os dados operacionais se vinculam a `EventParticipant`.

O container backend aplica as migrações automaticamente ao iniciar e executa `seed_demo` somente com `DJANGO_DEBUG=1`. Configure `DEMO_USER_EMAIL` e `DEMO_USER_PASSWORD` no `.env`. A carga preenche os 19 apps uma única vez, preservando alterações e mensagens nas reinicializações. No ambiente local, as credenciais estão em `.tools/demo-credentials.json`; a senha não é enviada ao frontend. Consulte [Demonstração e API](<docs/Demonstracao e API.md>).

Para verificar alterações e executar os testes:

```powershell
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend python manage.py test tests api
```

O Admin é restrito a usuários da equipe, conforme permissões nativas do Django. `AuditLog` permite apenas inclusão pelo código e consulta no Admin, com triggers PostgreSQL bloqueando alterações, exclusões e truncamento. Bloqueios existentes não podem ser editados ou excluídos pelo Admin.

Perfil, filtros, descoberta, favoritos, match recíproco e mensagens têm endpoints autenticados. Encerrar um match preserva o histórico e impede novos envios. Políticas LGPD, revelações comerciais, expiração automática de passes e processamento de pagamentos seguem pendentes. `Notification` e `EventMetric` têm exemplos para inspeção no Admin, sem geração automática de métricas. Repasse/settlement segue pendente.

Os arquivos estáticos do Admin são servidos pelo Django apenas com `DJANGO_DEBUG=1`; o serviço definitivo de arquivos estáticos em produção continua pendente. Para mudar a porta local, ajuste também `DJANGO_CSRF_TRUSTED_ORIGINS` no `.env`.

```powershell
# Logs e encerramento (preserva dados)
docker compose logs -f
docker compose down

# Compilação React/TypeScript
docker compose exec frontend npm run build

# Ativar Python virtual e Node portátil local neste terminal
. .\infra\activate.ps1
```

O Node portátil está em `.tools/node-v26.10.0-win-x64`, ignorado pelo Git. Para instalar novamente o Python local: `python -m venv .venv` e `.\.venv\Scripts\python.exe -m pip install -r requirements.lock`.

As imagens de infraestrutura acompanham as séries indicadas; os locks fixam as dependências da aplicação. Este ambiente é de desenvolvimento. As decisões de produção listadas abaixo continuam pendentes.

---

Plataforma SaaS para experiências de encontro e relacionamento vinculadas a eventos e salas, com descoberta de participantes, likes, matches, chat, passes de revelação, moderação, auditoria e ciclo de vida de dados.

> **Status em 04/10/2026:** ambiente Docker funcional, 19 apps no Admin, carga automática em DEBUG, seis telas do participante, painel administrativo por evento/papel e ingresso por QR Code assinado. As seções seguintes descrevem a arquitetura aprovada e requisitos do produto; não significam que todos estejam implementados. Consulte [Verificação da implementação](<docs/Verificacao da implementacao.md>) para a cobertura atual e as pendências.

---

## 1. Arquitetura

A primeira versão será construída como um **monólito modular**, evitando microserviços nesta fase.

A solução é composta por:

- **Frontend:** React + TypeScript
- **Backend:** Python + Django
- **API:** Django REST Framework
- **Banco relacional:** PostgreSQL
- **Tempo real:** Django Channels + WebSockets
- **Tarefas assíncronas:** Celery
- **Broker/cache:** Redis
- **Storage local:** filesystem local ou MinIO
- **Storage de produção:** serviço compatível com S3
- **Ambiente local:** Docker + Docker Compose
- **Administração interna inicial:** Django Admin

O frontend se comunica com o backend por **HTTP/JSON**. Funcionalidades realmente em tempo real, principalmente chat e notificações, usam **WebSockets**.

---

## 2. Visão dos serviços

```text
Browser
  |
  +-- HTTP/JSON --------------------+
  |                                 |
  +-- WebSocket ----------------+   |
                               |   |
                         +-----v---v------+
                         | Django / DRF   |
                         | Channels       |
                         +--+----+-----+--+
                            |    |     |
                    +-------+    |     +----------+
                    |            |                |
              +-----v-----+ +----v----+     +-----v------+
              |PostgreSQL | |  Redis  |     | S3 / MinIO |
              +-----------+ +----+----+     +------------+
                                 |
                          +------v------+
                          |Celery Worker|
                          +-------------+
```

O React é executado como serviço próprio no ambiente de desenvolvimento. O backend Django concentra regras de negócio, API, autenticação/autorização, administração e comunicação com os demais componentes.

---

## 3. Containers previstos

O ambiente local deverá possuir, no mínimo, os seguintes serviços no `docker-compose.yml`:

| Serviço | Responsabilidade |
|---|---|
| `frontend` | Aplicação React/TypeScript |
| `backend` | Django + Django REST Framework + Channels |
| `db` | PostgreSQL |
| `redis` | Broker do Celery, cache e infraestrutura necessária ao tempo real quando aplicável |
| `celery_worker` | Execução de tarefas assíncronas |
| `minio` | Storage S3-compatible para desenvolvimento, quando esta opção for adotada |

### Serviço adicional recomendado para rotinas agendadas

`celery_beat` é uma consequência operacional natural das rotinas previstas no escopo — expiração, retenção, processamento pós-evento e tarefas periódicas. Porém, **Celery Beat ainda não foi explicitamente aprovado no escopo**. Deve ser confirmado antes de ser tratado como dependência definitiva.

### Não definidos ainda

Não foram fechados no escopo:

- Nginx, Traefik ou outro reverse proxy;
- servidor WSGI/ASGI definitivo de produção;
- provedor de cloud;
- provedor S3;
- CI/CD;
- registry de imagens;
- Kubernetes/orquestrador de produção;
- observabilidade/APM;
- versões exatas das imagens Docker.

Esses itens não devem ser considerados decisões tomadas até serem formalmente definidos.

---

## 4. Docker Compose

O Compose deverá coordenar dependências e healthchecks para que o ambiente possa ser inicializado de forma reproduzível.

Dependências conceituais:

```text
frontend
└── backend

backend
├── db
├── redis
└── minio (quando usado)

celery_worker
├── backend/codebase
├── db
├── redis
└── minio (quando necessário)
```

### Volumes persistentes

Devem existir volumes separados para:

- dados do PostgreSQL;
- objetos do MinIO, caso utilizado;
- arquivos locais de desenvolvimento, caso a alternativa filesystem seja usada.

Código-fonte poderá ser montado por bind mount em desenvolvimento para permitir hot reload.

### Networks

Uma rede interna do Compose é suficiente para a fase inicial. Exposição pública deve ser limitada aos serviços necessários ao desenvolvimento, normalmente frontend, backend e eventualmente console do MinIO.

---

## 5. Estrutura proposta do repositório

```text
saas-encontro/
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── docs/
│   ├── architecture/
│   ├── data-model/
│   ├── lgpd/
│   └── decisions/
│
├── backend/
│   ├── Dockerfile
│   ├── manage.py
│   ├── config/
│   │   ├── settings/
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── celery.py
│   └── apps/
│       ├── accounts/
│       ├── organizations/
│       ├── events/
│       ├── rooms/
│       ├── participants/
│       ├── profiles/
│       ├── discovery/
│       ├── interactions/
│       ├── matches/
│       ├── messaging/
│       ├── passes/
│       ├── payments/
│       ├── reports/
│       ├── moderation/
│       ├── consent/
│       ├── retention/
│       ├── audit/
│       ├── notifications/
│       └── analytics/
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       ├── app/
│       ├── pages/
│       ├── features/
│       ├── components/
│       ├── services/
│       ├── hooks/
│       ├── types/
│       └── utils/
│
└── storage/
    └── .gitkeep
```

Essa árvore é uma **proposta de organização coerente com os domínios já aprovados**, não uma obrigação de nomes físicos. O princípio obrigatório é manter a separação modular por domínio de negócio.

---

## 6. Domínios do backend

### Contas e identidade

Responsável por identidade persistente da plataforma, autenticação e dados globais do usuário.

Entidades centrais:

- `User`
- `UserProfile`
- `Organization`
- `OrganizationMember`

### Eventos

Responsável pelo ciclo de vida do evento e sua administração.

Entidades centrais:

- `Event`
- `EventAdministrator`

### Salas

Responsável pela configuração e operação de salas dentro de eventos.

Entidades centrais:

- `Room`
- `RoomConfiguration`
- `RoomAdministrator`
- `RoomParticipant`

### Participantes e perfis

`EventParticipant` é o pivô operacional do usuário dentro de um evento. Dados do evento não devem apontar diretamente para a identidade global quando o vínculo correto for a participação.

Entidades centrais:

- `EventParticipant`
- `ParticipantProfile`
- `ParticipantPhoto`
- `EventOutfitPhoto`
- `ProfileField`
- `ProfileFieldOption`
- `ParticipantFieldValue`
- `ParticipantPreference`

### Descoberta e interações

Responsável por elegibilidade, filtros, apresentação de perfis e histórico de decisões.

Entidades:

- `ProfileDiscovery`
- `Interaction`
- `InteractionHistory`

Estados iniciais de interação:

- `LIKE`
- `PASS`

O sistema não flexibiliza filtros automaticamente. Ao esgotar perfis elegíveis, a descoberta é interrompida e o participante deve revisar os filtros.

### Matches e comunicação

Entidades:

- `Match`
- `Conversation`
- `Message`

O interesse mútuo gera match. Match ativo libera fotos pós-match, outfit e conversa.

Ao desfazer o match:

- não são permitidas novas mensagens;
- o histórico permanece em modo somente leitura;
- fotos pós-match e outfit deixam de ser acessíveis.

### Passes e comercialização

Entidades previstas:

- `PassType`
- `EventPassOffer`
- `ParticipantPass`
- `PassUsage`
- `PassPurchase`
- `Payment`
- `PassActivation`
- `Payout` / `Settlement`, quando aplicável

Passes podem funcionar por:

- tempo;
- quantidade de revelações;
- combinação dos dois.

Os modelos comerciais previstos são:

1. pagamento externo ao evento/estabelecimento com ativação administrativa;
2. pagamento processado pela plataforma com eventual repasse ao evento;
3. pagamento destinado diretamente à plataforma.

As regras comerciais e fiscais de repasse ainda estão **a definir**.

### Segurança e moderação

Entidades:

- `Block`
- `Report`
- `ReportEvidence`
- `ModerationCase`
- `ModerationAction`
- `ModerationNote`
- `UserSuspension`
- `EventBan`
- `RoomBan`

Denúncia, bloqueio e punição são conceitos independentes.

O bloqueio é irreversível dentro do evento. Após bloqueio, os perfis deixam de ser mutuamente acessíveis e a conversa permanece somente como histórico anonimizado.

### LGPD, retenção e auditoria

Entidades:

- `ConsentRecord`
- `DataRetentionRecord`
- `LegalHold`
- `PrivacyRequest`
- `AuditLog`

`AuditLog` deve seguir modelo **append-only**.

A retenção deve ser configurada por categoria de dado. O prazo jurídico definitivo ainda precisa de validação e não deve ser hardcoded arbitrariamente.

`LegalHold` impede eliminação automática quando existir fundamento válido de preservação.

---

## 7. Regras essenciais de perfil

Para ativação do participante, o escopo prevê:

- nome obrigatório;
- sobrenome obrigatório;
- mês e ano de nascimento obrigatórios;
- idade calculada;
- gênero obrigatório;
- bio com no mínimo 50 caracteres;
- pelo menos 3 fotos;
- uma foto definida como principal;
- cumprimento dos demais campos obrigatórios definidos pelo evento.

O participante pode ter até **10 fotos de perfil**:

- 3 fotos obrigatórias visíveis antes do match;
- até 7 fotos adicionais visíveis somente após match.

A foto de outfit é separada da galeria e também é visível somente após match.

Campos e tags podem ser globais, cadastrados pela administração da plataforma, ou específicos do evento.

---

## 8. Persistência global versus dados do evento

A arquitetura deve separar claramente:

### Persistente na plataforma

Dados que o usuário optar por manter em seu perfil global para reutilização em outros eventos.

### Vinculado ao evento

Dados operacionais e contextuais associados a `EventParticipant`, incluindo participação, interações, matches, outfit, moderação e demais registros do ciclo daquele evento.

Ao entrar em novo evento, informações persistentes podem pré-preencher o novo perfil, que continua sendo contextualizado para aquele evento.

---

## 9. Likes e revelação

Sem passe de revelação, o usuário pode ser informado de que recebeu um like, porém sem dados suficientes para identificar diretamente quem o enviou.

A revelação da identidade é controlada por benefícios/passes.

Cada revelação consumida deve ser registrada para controle e auditoria.

---

## 10. Bloqueios entre eventos

O bloqueio é definitivo apenas no evento onde foi realizado.

O histórico global do bloqueio é preservado. Em evento futuro, os usuários podem voltar a se encontrar.

O alerta de bloqueio anterior:

- não aparece ao visualizar o perfil;
- não aparece ao escolher `PASS`;
- aparece quando quem bloqueou anteriormente tenta enviar `LIKE`;
- exige confirmação para prosseguir.

Se o usuário confirmar o novo LIKE, o histórico antigo continua registrado, mas o alerta daquele par é encerrado para eventos futuros até que ocorra um novo bloqueio manual.

---

## 11. API

A API será implementada com **Django REST Framework**.

A API atual usa `/api/`, sessão Django e CSRF nas escritas. Os endpoints estão em [Demonstração e API](<docs/Demonstracao e API.md>). Versionamento, autenticação de produção e formato definitivo de erros ainda devem ser formalmente definidos.

Os recursos da API deverão respeitar os limites de contexto:

```text
User
└── EventParticipant
    ├── ParticipantProfile
    ├── Preferences
    ├── Discovery
    ├── Interactions
    ├── Matches
    ├── Conversations
    ├── Passes
    ├── Reports
    └── Blocks
```

Permissões nunca devem depender apenas da interface. Regras de acesso precisam ser aplicadas no backend.

---

## 12. WebSockets

Django Channels será usado somente onde tempo real trouxer benefício real.

Casos previstos:

- chat;
- notificações durante o evento;
- atualizações operacionais que precisem chegar imediatamente ao cliente.

O protocolo detalhado dos eventos WebSocket ainda está **a definir**.

---

## 13. Celery

Celery deverá processar operações que não devem bloquear requisições HTTP, incluindo:

- notificações;
- rotinas pós-evento;
- expiração de benefícios;
- processamento de métricas;
- arquivamento;
- rotinas de retenção;
- eliminação de dados quando autorizada;
- processamento assíncrono adicional necessário ao produto.

Operações destrutivas relacionadas à retenção devem respeitar `LegalHold` e as políticas aplicáveis antes da execução.

---

## 14. Redis

Redis será utilizado como:

- broker para Celery;
- camada de cache quando necessário;
- infraestrutura de apoio ao tempo real quando exigido pela configuração adotada para Channels.

Estratégias de cache, TTLs e invalidação ainda estão **a definir** e não devem antecipar otimizações sem necessidade.

---

## 15. PostgreSQL

PostgreSQL será a fonte relacional principal.

Princípios definidos:

- UUID nas entidades principais;
- integridade referencial por FKs;
- estados explícitos;
- separação entre identidade global e participação em evento;
- auditoria append-only;
- evitar soft delete genérico;
- índices definidos conforme fluxos reais de consulta;
- constraints de integridade também no banco quando aplicável.

Índices e constraints definitivos serão fechados com o DER lógico completo e os fluxos de consulta.

---

## 16. Storage de arquivos

Arquivos binários não devem ser armazenados no PostgreSQL.

O banco mantém:

- referências;
- metadados;
- ownership;
- contexto do evento;
- categoria da foto;
- regras de visibilidade;
- timestamps;
- informações necessárias ao ciclo de retenção.

### Desenvolvimento

Pode utilizar:

- filesystem local; ou
- MinIO.

### Produção

Deve utilizar storage compatível com S3.

O provedor definitivo ainda está **a definir**.

---

## 17. Variáveis de ambiente

O repositório deve conter `.env.example`, nunca credenciais reais.

Categorias previstas:

```dotenv
# Django
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=

# PostgreSQL
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=

# Redis
REDIS_URL=

# Celery
CELERY_BROKER_URL=

# Storage
STORAGE_BACKEND=
S3_ENDPOINT_URL=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
S3_BUCKET_NAME=
S3_REGION=

# Frontend
FRONTEND_API_URL=
FRONTEND_WS_URL=
```

Os nomes finais poderão ser ajustados na implementação. O princípio obrigatório é manter configuração e segredos fora do código-fonte.

---

## 18. Segurança

Requisitos estruturais desde a primeira versão:

- autenticação e autorização no backend;
- permissões por nível global, organização, evento e sala;
- validação de ownership/contexto;
- bloqueio e denúncia desde o início;
- auditoria de ações administrativas e sensíveis;
- separação entre denúncia e punição;
- anonimização da interface após bloqueio;
- proteção de dados pessoais;
- consentimentos rastreáveis;
- política explícita de retenção;
- preservação por `LegalHold`;
- eliminação definitiva quando aplicável.

Políticas específicas de rate limiting, CORS, CSP, autenticação/token, proteção antiabuso e gestão de segredos devem ser detalhadas antes da entrada em produção.

---

## 19. Métricas e analytics

O sistema deverá produzir métricas consolidadas por evento e sala, incluindo indicadores operacionais e de moderação.

Não devem ser materializados indiscriminadamente números que possam ser calculados. Agregações persistentes devem ser introduzidas quando houver necessidade de desempenho, histórico consolidado ou regra de negócio.

Dados identificáveis do evento devem obedecer ao ciclo de retenção. Métricas consolidadas previstas pelo produto podem permanecer conforme a política definida, sem depender da manutenção indevida de dados pessoais do evento.

---

## 20. Administração

Na fase inicial, **Django Admin** será usado para acelerar:

- gestão interna;
- operação;
- moderação;
- inspeção de registros;
- cadastros globais;
- suporte administrativo.

Interfaces personalizadas em React serão introduzidas conforme os fluxos do organizador, administrador e participante forem amadurecendo.

---

## 21. Estratégia inicial de desenvolvimento

Ordem sugerida, respeitando as dependências do domínio:

1. infraestrutura Docker/Compose;
2. configuração Django, React, PostgreSQL e Redis;
3. contas, identidade e autenticação;
4. organizações, eventos e salas;
5. `EventParticipant` e perfis;
6. campos configuráveis e fotos/storage;
7. descoberta, filtros e histórico;
8. LIKE/PASS e match;
9. Channels, conversa e mensagens;
10. bloqueios, denúncias e moderação;
11. passes, ativação e pagamentos;
12. consentimentos, retenção, `LegalHold` e auditoria;
13. notificações;
14. métricas e dashboards;
15. hardening de segurança e preparação de produção.

Essa sequência é de implementação técnica e pode ser refinada em épicos/sprints sem alterar o escopo funcional.

---

## 22. Arquivos iniciais esperados no repositório

```text
README.md
.env.example
.gitignore
docker-compose.yml
backend/Dockerfile
frontend/Dockerfile
```

Posteriormente, conforme decisões forem fechadas:

```text
docker-compose.prod.yml       # se adotado
.github/workflows/*           # CI/CD, quando definido
infra/*                       # infraestrutura, se necessária
docs/*                        # ADRs, DER e documentação
```

---

## 23. Decisões pendentes antes de produção

- versões oficiais de Python, Django, Node, React, PostgreSQL e Redis;
- ferramenta de gerenciamento de dependências Python;
- gerenciador de pacotes JavaScript;
- estratégia de autenticação da API;
- servidor ASGI de produção;
- reverse proxy;
- provedor de infraestrutura;
- provedor S3;
- estratégia de e-mail/notificações externas;
- observabilidade e logging centralizado;
- CI/CD;
- backups e disaster recovery;
- regras comerciais/fiscais de pagamentos e repasses;
- prazo jurídico definitivo de retenção;
- políticas finais de anexos;
- estados e transições formais das entidades;
- catálogo definitivo dos campos de perfil;
- estratégia de testes e metas de cobertura.

---

## 24. Princípios do projeto

1. **Monólito modular primeiro.**
2. **`EventParticipant` é o pivô operacional do evento.**
3. **Identidade global e dados do evento permanecem separados.**
4. **Segurança, LGPD, bloqueios, denúncias e auditoria fazem parte da arquitetura inicial.**
5. **Denúncia não equivale a punição.**
6. **Auditoria é append-only.**
7. **Não usar soft delete genérico como solução universal.**
8. **Arquivos ficam fora do banco relacional.**
9. **Tempo real somente onde necessário.**
10. **Filtros não são flexibilizados automaticamente.**
11. **Bloqueios são irreversíveis dentro do evento.**
12. **Retenção e eliminação dependem de política explícita e preservação legal aplicável.**
13. **Não introduzir complexidade operacional antes de existir necessidade real.**

---

## 25. Estado deste README

Este README descreve a **arquitetura técnica aprovada até o momento** e complementa o escopo técnico do projeto para servir como documento inicial do repositório.

Ele não substitui:

- DER lógico detalhado;
- contratos de API;
- ADRs;
- documentação de infraestrutura de produção;
- política jurídica definitiva de retenção;
- documentação operacional dos ambientes.

Esses documentos deverão evoluir junto com o projeto.
