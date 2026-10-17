# Docker: desenvolvimento e produção

Configuração separada em **16/10/2026**. O ambiente padrão continua sendo desenvolvimento, preservando os comandos, o projeto e os dados locais existentes.

Requisito: Docker Compose **2.20 ou mais recente**, por causa do `include` da entrada explícita de desenvolvimento.

| Aspecto | Desenvolvimento | Produção |
|---|---|---|
| Compose | `docker-compose.dev.yml`, que inclui `docker-compose.yml` | `docker-compose.prod.yml` independente |
| Projeto/recursos | `saas-de-encontro` | `saas-de-encontro-prod` |
| Ambiente | `.env`, baseado em `.env.example` | `.env.prod`, baseado em `.env.prod.example` |
| Frontend | Target `development`: Vite, HMR, código montado e dependências em volume | Target `production`: somente Nginx e `dist`, sem Node/npm/watchers |
| Build | Dependências pelo lockfile | `npm ci`, validação do compilador e `npm run build` em estágio descartado |
| Backend | Código local montado em `/app` | Código copiado para a imagem, sem montagem do código-fonte |
| Django | DEBUG/carga de exemplo configuráveis | DEBUG e carga automática de demonstração desativados |
| Fonte de dados | `FRONTEND_DATA_MODE=mock|django` | `django` fixado no build; demonstração disponível por `?demo=1` |
| Entrada | HTTP, porta 8080 por padrão | HTTP 80 redirecionado para HTTPS 443; Traefik/Let's Encrypt |
| Persistência | Volumes locais existentes, `backend/media`, `backend/backups`, `backend/staticfiles` | Volumes PostgreSQL/Redis/ACME próprios e `data/production/{media,backups,staticfiles}` |

## Desenvolvimento

Copie `.env.example` para `.env` caso ainda não exista, preencha os segredos locais e execute:

```powershell
docker compose -f docker-compose.dev.yml up -d --build --wait
docker compose -f docker-compose.dev.yml logs -f
```

Acesse `http://localhost:8080`. `docker compose up -d --build --wait` continua equivalente e mantém o mesmo projeto/volumes. O container frontend usa o estágio `development` de `frontend/Dockerfile`, com Node e Vite na porta interna 5173. As alterações na pasta frontend são montadas no container; HMR passa pelo Nginx.

O Node dos estágios de dependências, desenvolvimento e compilação está fixado em **24.22.0**. As versões de React, TypeScript, Vite e demais pacotes continuam vindo do lockfile. O estágio de produção não contém esse Node nem `node_modules`.

Os scripts `full-clean.ps1` e `full-clean.sh` continuam voltados ao Compose padrão de desenvolvimento. A troca de ambiente não executa limpeza nem transfere dados.

## Produção

Copie `.env.prod.example` para `.env.prod` e configure:

- `APP_DOMAIN`: domínio público, sem protocolo, porta ou caminho.
- `ACME_EMAIL`: e-mail usado no cadastro ACME.
- `DJANGO_SECRET_KEY` e `POSTGRES_PASSWORD`: segredos próprios de produção.
- `APP_VERSION`: tag das imagens da aplicação.
- `PROD_DATA_DIR`: diretório persistente do host, `./data/production` por padrão.

O domínio deve apontar para o servidor, com as portas 80 e 443 disponíveis. O Compose configura a terminação TLS no Traefik, HTTP-01 do Let's Encrypt, redirecionamento HTTPS, hosts e origem CSRF do Django. Não há necessidade de Docker socket no Traefik.

```powershell
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build --wait
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
docker compose --env-file .env.prod -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

Acesse `https://SEU_DOMINIO`. `backend/start.py` aplica migrações e coleta os estáticos antes de iniciar Daphne. A carga demonstrativa não é criada automaticamente. A aplicação usa um banco/Redis próprios e inicia sem os cadastros do desenvolvimento; qualquer transferência dos dados existentes exige exportação/restauração planejada.

O frontend é compilado com `VITE_FRONTEND_DATA_MODE=django`. Somente essa opção pública vai ao build; segredos Django/PostgreSQL não são enviados para o frontend. Alterações de código ou configuração de build exigem reconstruir a imagem:

```powershell
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build --force-recreate --wait
```

`PROD_ENV_FILE` permite indicar outro arquivo para o `env_file` dos serviços; o padrão é `.env.prod`. Ao usar um caminho alternativo, informe também esse arquivo no `--env-file` da CLI para a interpolação dos domínios, tags e diretórios. `.env.prod`, os dados persistentes e arquivos locais de mídia/backups não entram nas imagens nem no Git.

Na atualização, `--force-recreate` também recarrega os gateways e suas rotas após mudanças de configuração/IPs internos. Os volumes e diretórios persistentes são preservados; esse comando não oferece implantação sem interrupção.

## Rotas e arquivos

O fluxo de produção é navegador → Traefik HTTPS → Nginx gateway → frontend estático ou Daphne. O gateway de desenvolvimento usa `infra/nginx.conf`; o de produção usa `infra/nginx.prod.conf`. Ambos incluem `infra/app-routes.conf`, preservando exatamente as mesmas rotas de API, Admin, WebSocket e mídia autorizada.

O Nginx da imagem frontend serve `dist` na porta interna 80. `index.html` exige revalidação; chunks com hash em `/assets/` usam cache imutável. Assets ausentes retornam 404. Rotas da SPA têm fallback para `index.html`; a navegação por hash continua funcionando.

Os estáticos coletados do Django são servidos pelo gateway em `/static/`, com montagem somente para leitura. Mídia privada continua exigindo autorização no Django e `X-Accel-Redirect`, com acesso direto bloqueado. WebSocket usa `wss://` por HTTPS e mantém o encaminhamento de Upgrade. Veja [Mídia protegida](<Midia protegida.md>) e [WebSocket e tempo real](<WebSocket e tempo real.md>).

Dentro do backend, exportações permanecem em **`/app/backups`**; no host de produção, ficam em **`data/production/backups`** por padrão. Essa separação preserva os arquivos locais de desenvolvimento. Os workers operacionais e de exportação continuam nas filas distintas `celery` e `exports`.

## Verificação reproduzível

```powershell
python scripts/verify_docker_environments.py
```

O verificador constrói as imagens, compara o Compose explícito de desenvolvimento com o padrão e inicia os nove serviços da configuração de produção em um projeto descartável. Usa bancos, Redis, dados e portas próprios, domínio localhost e certificado local do Traefik; desativa ACME no teste, sem contatar o Let's Encrypt. Confere ausência de Node/npm na imagem final, ausência de carga automática, login HTTPS/cookies Secure, assets compilados/cache/404, Admin CSS, WebSocket com aviso entre processos, demonstração e HMR no desenvolvimento. Depois remove o projeto, seus volumes e credenciais. Não altera os serviços em uso.

`--skip-build` reutiliza as imagens de uma execução anterior. O verificador exige as dependências de testes do frontend instaladas e o navegador usado pelos demais testes. A emissão pública do certificado depende do domínio/DNS do ambiente de implantação.

Referências: [Compose include](https://docs.docker.com/reference/compose-file/include/), [Traefik file provider](https://doc.traefik.io/traefik/reference/install-configuration/providers/others/file/) e [releases oficiais do Node](https://nodejs.org/en/blog/release).
