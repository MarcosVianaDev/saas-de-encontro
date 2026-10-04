# Demonstração persistida e API

Estado verificado em 03/10/2026. Este guia descreve o ambiente local atual.

Configure no `.env`:

```dotenv
DJANGO_DEBUG=1
FRONTEND_DATA_MODE=debug
DEMO_USER_EMAIL=demo@eventconnect.local
DEMO_USER_PASSWORD=substitua-por-uma-senha-local
```

Execute `docker compose up -d --build --wait`. Acesse http://localhost:8080. O frontend mostra o formulário de login e usa a senha configurada no backend. Neste workspace as credenciais locais estão no arquivo ignorado `.tools/demo-credentials.json`. O usuário `admin-demo@eventconnect.local` usa a mesma senha e acessa http://localhost:8080/admin/.

O `.env` deste workspace já está em modo `debug`. `.env.example` mantém `mock` como padrão. Para trocar somente o modo do frontend, altere `FRONTEND_DATA_MODE` e execute `docker compose up -d --no-deps --force-recreate frontend`. Para alterar variáveis do Django, recrie também o backend com `docker compose up -d backend celery_worker`. Um build estático precisa ser recompilado para incorporar a variável Vite.

`backend/start.py` aplica migrações, executa `seed_demo` se DEBUG estiver ativo, coleta estáticos e inicia Daphne. A carga é uma transação protegida por lock PostgreSQL; UUIDs estáveis e um registro de auditoria impedem duplicação e sobrescrita. Celery e comandos de teste não iniciam essa carga automaticamente. Também é possível executar `docker compose exec backend python manage.py seed_demo`. Com DEBUG=False o comando não grava dados. Alterar DEBUG não remove dados anteriormente criados.

`DEMO_USER_PASSWORD` é obrigatório para a carga em DEBUG. Após a primeira carga, mudar as variáveis de credenciais não altera as contas já criadas. Para trocar a senha, use `docker compose exec backend python manage.py changepassword demo@eventconnect.local`, substituindo o login caso tenha configurado outro e-mail. Atualize também seu arquivo local de credenciais. A carga não é um mecanismo de reset; remover o marcador de auditoria não faz parte do fluxo suportado.

As fixtures reproduzem os 12 perfis e oito conversas do frontend. Incluem fotos, interesses, preferências, interações, matches, salas, passes, compras/pagamentos fictícios, consentimento e métricas. Moderação, bloqueios, retenção e solicitações de privacidade recebem exemplos em um evento histórico separado, preservando o fluxo principal. Nenhuma cobrança é executada.

O login demo começa com perfil ativo e três fotos. É possível editar o perfil, salvar filtros, descobrir candidatos restantes, curtir Camila para gerar um novo match recíproco e conversar. A opção criar conta em DEBUG permite testar um cadastro vazio: enviar três fotos, preencher os campos e ativar o perfil. Uma conta nova só tem match após curtidas recíprocas reais; não há respostas automáticas dos personagens.

## Endpoints

Todos têm prefixo `/api/`; exceto sessão/login e cadastro de DEBUG, exigem sessão autenticada. Escritas usam token CSRF obtido em `session/`. Login renova o token. Participação, evento, bloqueios, banimentos e suspensão são verificados no backend.

| Caminho | Método | Comportamento |
|---|---|---|
| `health/` | GET | Conexões com PostgreSQL e Redis, sem login |
| `session/` | GET | Sessão e token CSRF |
| `auth/login/`, `auth/register/`, `auth/logout/` | POST | Autenticação, cadastro de DEBUG, logout |
| `bootstrap/` | GET | Estado inicial das telas |
| `profile/` | GET, PUT | Perfil próprio e ativação |
| `profile/photos/` | POST, DELETE | Upload multipart `file`, remoção por `url` |
| `photos/<uuid>/content/` | GET | Foto enviada com autorização |
| `filters/` | PUT | Preferências de descoberta |
| `participants/` | GET | Diretório, busca por `search` |
| `participants/<uuid>/` | GET | Perfil e fotos autorizadas |
| `discovery/` | GET | Candidatos filtrados sem decisões anteriores |
| `interactions/<uuid>/` | POST | `decision`: `LIKE` ou `PASS`; match recíproco |
| `favorites/<uuid>/` | POST | Alternar favorito |
| `conversations/` | GET | Conversas e estados |
| `conversations/<uuid>/messages/` | GET, POST | Histórico e envio de `text` |
| `matches/<uuid>/end/` | POST | Encerrar match mantendo histórico |

UUIDs nas rotas de pessoas identificam `EventParticipant`. Perfil aceita `first`, `last`, `month`, `year`, `gender`, `bio`; filtros aceitam `min`, `max`, `gender`, `interests`, `purpose`. As respostas de escrita devolvem o estado atualizado quando necessário. O frontend guarda apenas o estado de renderização; o PostgreSQL é a fonte dos dados no modo debug.

Imagens enviadas ficam em `backend/media/` (ignorado no Git e persistido pelo bind mount), com acesso autenticado. Limites: dez fotos JPEG/PNG/WebP de até 10 MB, três públicas, restantes após match; mensagens de até 2.000 caracteres. Fotos iniciais são assets públicos fictícios. Mensagens usam HTTP com atualização a cada cinco segundos na tela de conversas; WebSocket e envio de notificações externas ficam para uma etapa posterior.

Validação: `docker compose exec backend python manage.py test tests api` e `docker compose exec frontend npm run build`. A carga possui testes de idempotência, cobertura das entidades, DEBUG desativado, autenticação/CSRF, isolamento entre eventos, filtros, match, mensagens e acesso a fotos.

Os containers estavam saudáveis na última verificação, com 15 testes e compilação aprovados. Mensagens foram preservadas após reload e reinicialização do Django. `docker compose down` preserva os volumes; uploads ficam no diretório local `backend/media/`. O estado de cobertura e as funcionalidades pendentes estão em [Verificação da implementação](<Verificacao da implementacao.md>).
