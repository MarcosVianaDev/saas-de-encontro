# Entrega dos SPAs em produção

O login é uma aplicação independente, pública em `/`. Depois da autenticação, o Django define o destino conforme a conta e o contexto selecionado. A navegação carrega outro documento, sem importar o pacote de gestão para o login.

| Aplicação | URL | Conteúdo |
|---|---|---|
| Login | `/` | Login, cadastro por convite e seleção de contexto |
| Participante | `/spa/participant/` | Cadastro de perfil, descoberta, conversas e demais recursos do participante |
| Gestor do evento | `/spa/event-manager/` | Administração dos eventos vinculados ao gestor |
| Gestor global | `/spa/global/` | Aplicação completa, incluindo gestão de eventos e demonstração |

`npm run build:production` verifica os tipos e executa quatro builds Vite independentes. Cada SPA tem seus próprios arquivos, sem chunks compartilhados entre as aplicações. O build falha se módulos de gestão forem importados pelo participante ou se a interface global for importada pelo gestor de evento. Os builds não publicam sourcemaps nem manifests. `npm run build` e o servidor Vite continuam disponíveis para desenvolvimento.

## Autorização dos arquivos

O Nginx do frontend verifica a sessão no Django através de `auth_request` antes de entregar **HTML, JavaScript, CSS ou qualquer arquivo** de `/spa/.../`. Saber o nome ou hash de um arquivo não permite baixá-lo sem autorização. As verificações usam a conta autenticada e os vínculos atuais do banco, ignorando papéis declarados pelo cliente:

- Participante: precisa ter participação em algum evento.
- Gestor de evento: precisa ter vínculo administrativo ativo.
- Gestor global: precisa ser superusuário; pode receber todas as aplicações.

Uma conta pode ser participante e gestora e, nesse caso, acessar seus dois pacotes. A autorização dos dados de cada evento continua sendo responsabilidade da API, com as verificações existentes de evento, papel e permissões.

Visitantes sem sessão voltam ao login; usuários autenticados sem permissão recebem HTTP 403. Os arquivos autenticados usam `Cache-Control: private, no-store`. Apenas os assets públicos do login usam cache imutável. Vínculos revogados deixam de autorizar novos downloads imediatamente. Código já recebido pelo navegador não pode ser recolhido; segredos e decisões de autorização permanecem no servidor.

O modo de demonstração em produção fica disponível dentro do pacote global, após autenticação. `?demo=1` não transforma o login ou o SPA do participante numa aplicação administrativa.

## Docker e implantação

O estágio `production` do Dockerfile compila os quatro pacotes e copia apenas os resultados para Nginx, sem Node, npm, dependências ou fontes TypeScript na imagem final. O frontend depende do backend saudável para resolver e consultar o serviço de autorização. O gateway preserva cookies e o protocolo HTTPS original nessa consulta.

Não publique `dist` inteiro com um servidor estático comum, CDN pública ou `vite preview`: isso removeria a autorização dos pacotes. Use a imagem e as configurações Nginx de produção do projeto. O ambiente de desenvolvimento com Vite expõe os fontes para HMR e não oferece essa separação de entrega.

```sh
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build --force-recreate --wait
```

## Verificação

`python scripts/verify_docker_environments.py` cria um ambiente descartável, com HTTPS local e contas separadas de participante, gestor de evento e gestor global. Verifica login, destinos, pacotes baixados, bloqueio de acesso direto aos arquivos, cabeçalhos de cache, ausência de sourcemaps, recarga, logout e funcionamento do desenvolvimento. Também executa os testes de autorização e de isolamento de eventos do backend. Não usa o banco de produção ou de desenvolvimento.

Referências: [autorização por subrequest do Nginx](https://nginx.org/en/docs/http/ngx_http_auth_request_module.html) e [builds e caminhos públicos no Vite](https://vite.dev/guide/build).
