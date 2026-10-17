# Entrega de mídia protegida

Implementado em **16/10/2026**: Django autoriza o acesso; Nginx lê e transmite os arquivos locais por `X-Accel-Redirect`.

## Fluxo e permissões

Os endereços públicos continuam nas rotas da API, inclusive os aliases com `/api/events/<uuid>/...`:

| Rota | Autorização preservada |
|---|---|
| `photos/<uuid>/content/` | Foto própria ou participante visível no mesmo evento; foto pós-match exige match ativo |
| `outfits/<uuid>/content/` | Outfit próprio ou match ativo, sem bloqueio, no mesmo evento |
| `event-admin/photos/<uuid>/content/` | Vínculo administrativo ativo ou superuser; foto pública não removida daquele evento |
| `event-admin/evidence/<uuid>/content/` | Papel/permissão de moderação, escopo do evento e registro obrigatório de auditoria |

Após autorizar, `api/protected_media.py` valida a chave e os metadados do arquivo. Com a entrega acelerada ativa, retorna corpo vazio, tipo de conteúdo, disposição inline/attachment, `Cache-Control: private, no-store`, `nosniff` e `X-Accel-Redirect`. Não abre nem lê os bytes da mídia. Nginx consome esse cabeçalho e entrega o arquivo, incluindo HEAD e Range. O cabeçalho interno não chega ao navegador.

Evidências mantêm download como anexo e auditoria antes de liberar a resposta. Falha na auditoria não retorna o redirecionamento interno. Conta, contexto, match, bloqueio e permissões continuam sendo avaliados no Django em cada requisição; não há URL pública permanente para contornar essas regras.

## Configuração

No Compose, `MEDIA_USE_X_ACCEL_REDIRECT` é **1 por padrão**, mesmo quando a variável ainda não existe no `.env`. O Nginx monta `backend/media` em `/srv/private-media` como **somente leitura**. Os uploads continuam sendo gravados pelo Django no volume existente.

`infra/nginx.conf` contém a rota `/_protected_media/` com `internal`, `alias`, `disable_symlinks on` e `sendfile on`. Acesso direto à rota retorna 404. `/media/` também retorna 404; a mídia protegida não é publicada como diretório estático. O Nginx mantém `nosniff` na resposta entregue.

Para carregar o código, a configuração e o volume novos:

```powershell
docker compose up -d --build backend frontend nginx
```

Recriar o serviço Nginx é necessário para adicionar o bind mount, além de recarregar a configuração. Em uma implantação personalizada, o diretório montado no Nginx deve conter exatamente os arquivos do `MEDIA_ROOT` do Django. A opção acelerada exige `FileSystemStorage` nesse diretório; outro storage não é silenciosamente convertido em uma URL local.

Ao executar Django diretamente sem Nginx, use `MEDIA_USE_X_ACCEL_REDIRECT=0`. Sem a variável e fora do Compose, o padrão da configuração Django é desativado. Esse modo mantém `FileResponse` para desenvolvimento direto e storages sem caminho local. Uma requisição HTTP não pode escolher entre os modos: a opção é definida no ambiente do servidor. A interface padrão pelo Compose passa pelo Nginx; o acesso direto ao Vite, se usado sem esse proxy, também exige a configuração correspondente.

## Validação de caminhos

Somente chaves relativas são aceitas. Caminhos absolutos, drives Windows, barras invertidas, segmentos vazios/`.`/`..`, controles, NUL, diretórios e arquivos ausentes retornam 404. O caminho real precisa permanecer dentro do storage. Links simbólicos dentro da árvore são recusados pelo Django e pelo Nginx na abertura do arquivo.

Nomes com espaços, Unicode, `%`, `#` ou `?` são escapados ao montar o URI interno. Esses caracteres permanecem dados do nome do arquivo, sem criar query string ou outro destino. Acesso a placeholders em `/images/` continua pelo frontend.

## Testes e limites

`api.test_protected_media` cobre cabeçalhos/corpo vazio sem abrir mídia em Python, disposição de anexo, validação de caminho, links simbólicos, fallback explícito, storage incompatível, autenticação, evento, fotos removidas, match/bloqueio, permissões administrativas e falha de auditoria. O runner de testes Django usa o modo direto por padrão para os testes existentes; a classe de entrega acelerada habilita a opção explicitamente.

O runner de navegador agora inicia um Nginx temporário com a configuração real e um volume de mídia exclusivo. Vite encaminha a API/WebSocket para esse Nginx na porta 18080, que usa o backend temporário da porta 18000. `check-media-delivery.cjs` verifica os bytes efetivos, imagem renderizada, MIME, cache, nomes escapados, HEAD/Range, bloqueio do caminho interno, autenticação, match, anexos/auditoria e logout. A chamada direta ao upstream confirma corpo vazio com o cabeçalho interno.

Resultados em [Verificação da implementação](<Verificacao da implementacao.md>). A mudança remove a transmissão da mídia do processo Python no fluxo pelo Nginx; autorização e acesso ao banco continuam no Django. Não foi realizado ensaio com centenas de downloads simultâneos.

Referências oficiais: [tratamento de X-Accel-Redirect](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_ignore_headers), [internal](https://nginx.org/en/docs/http/ngx_http_core_module.html#internal), [alias](https://nginx.org/en/docs/http/ngx_http_core_module.html#alias) e [disable_symlinks](https://nginx.org/en/docs/http/ngx_http_core_module.html#disable_symlinks).
