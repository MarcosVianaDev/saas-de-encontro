# Testes de navegador

O verificador `python scripts/verify_docker_environments.py` constrói as imagens e testa o Compose de produção completo em projeto descartável com HTTPS local: frontend compilado sem Node/npm, autenticação/cookies Secure, WebSocket, Admin CSS, cache/404, demonstração e HMR na imagem de desenvolvimento. O teste específico fica em `tests/docker/check-environments.cjs`, fora da suíte Vite, pois usa assets compilados e containers próprios. Guia: [Docker: desenvolvimento e produção](<../../docs/Docker - desenvolvimento e producao.md>).

Os estáticos coletados do Django também usam pasta exclusiva da rodada, montada no Nginx somente para leitura. A entrega com DEBUG desativado tem verificador próprio: `python scripts/verify_production_static.py`, com banco e containers descartáveis. Consulte [Verificação das prioridades](../../docs/Verificacao%20das%20prioridades.md).

`check-participant-pages.cjs` verifica as páginas separadas do participante: histórico por hash, buscas locais, envio de mensagens, filtros aplicados somente ao salvar, limites da biografia, proteção da demonstração antes do login e erros da API identificados por campo. A suíte de backend correspondente está em `api.test_profile_validation` e `api.test_exceptions`.

Os scripts de `.tools/ui-check` foram atualizados e incorporados em `browser/`. As dependências Playwright e jsQR estão no `package-lock.json` do frontend.

Com Docker Compose e os serviços `db`/`redis` disponíveis, execute na raiz do projeto:

```powershell
npm --prefix frontend ci
npm --prefix frontend run test:browser
```

O comando cria banco, backend e Nginx temporários, prepara os dados de teste, inicia dois frontends Vite nas portas 18081 (Django) e 18082 (mock) e executa os scripts. A API temporária usa a porta 18000; o Nginx usa a porta 18080 e recebe as chamadas de API/WebSocket do Vite. Essas portas devem estar livres. Usa a configuração real do Nginx e mídia exclusiva montada somente para leitura, com `MEDIA_USE_X_ACCEL_REDIRECT=1`. Ao terminar, remove banco/containers e encerra os frontends; mídia e backups de uso não são usados. Credenciais geradas para a rodada são apagadas.

O cache Redis usa prefixo exclusivo `test_browser_<identificador>`. Os contadores são reiniciados antes de cada cenário/auxiliar e removidos ao encerrar, apagando somente chaves desse prefixo. O runner mantém o throttling habilitado e usa `DRF_NUM_PROXIES=0` para o backend temporário. Ele não limpa o Redis do ambiente.

Os resultados JSON e logs ficam em `.tools/browser-tests/<identificador>/`. As capturas ficam em `.tools/ui-check/screenshots/`. O runner também executa os auxiliares de concorrência, diagnóstico de modelos e login HTTP do Django Admin.

Para reexecutar apenas um cenário:

```powershell
python scripts/run-browser-tests.py check-onboarding.cjs
```

No Windows, o Playwright usa o Edge instalado. Em outros sistemas, execute `npx playwright install chromium` na pasta `frontend`. `TEST_BROWSER_PATH` permite informar outro executável. Os scripts podem ser executados diretamente com `TEST_BASE_URL`, `TEST_MOCK_URL`, `TEST_CREDENTIALS_FILE` e `TEST_BACKEND_CONTAINER`, mas os cenários com backend real criam/alteram dados: prefira o runner isolado.

`check-lan.cjs` verifica a origem dos links e aceitação/rejeição de CSRF; no runner, usa loopback. Conectividade com outro dispositivo da LAN exige verificação separada.

O teste de exportação da interface usa respostas simuladas de job para validar botão, progresso, polling e links PDF/ZIP. A geração real do pacote é coberta por `api.test_exports` no backend.

`check-media-delivery.cjs` confirma que Django retorna o cabeçalho interno sem bytes e Nginx entrega as fotos, outfits e evidências autorizadas. Valida os bytes e uma imagem renderizada, MIME, cache, nomes com Unicode/caracteres reservados, HEAD, Range, negação do acesso direto à pasta, match encerrado, auditoria e logout. Exige o runner e seus serviços temporários.

O cenário de mídia restaura o match e o outfit anteriores e remove somente suas próprias fotos/denúncia/evidência em `finally`. A limpeza exige banco `test_browser_*`, preservando as três fotos públicas do ator compartilhado. Regressão de isolamento: `python scripts/run-browser-tests.py check-media-delivery.cjs check-real.cjs`.

`check-demonstration.cjs` abre o mock a partir do dashboard global em um frontend configurado como Django, verifica o login preenchido, completa o perfil/fotos e valida os 50 perfis, likes, matches, mensagens, notificações e avisos. Também verifica ausência de chamadas à API no mock e preservação da sessão global.

`check-event-tabs.cjs` usa duas abas no mesmo contexto de navegador, compartilhando a autenticação. Seleciona eventos diferentes, salva uma configuração pela interface da primeira aba após a segunda alterar a sessão e verifica o cabeçalho do evento, o isolamento dos dados e a persistência por aba após reload. Esse teste exige o runner, pois cria seus eventos no banco temporário. O helper `api()` reutiliza o cliente real do frontend para enviar os cabeçalhos de contexto da aba.

`check-participant-sync.cjs` recebe uma mensagem e um novo match pelo delta, confirma leitura apenas da mensagem entregue, verifica ausência de polling de bootstrap/histórico, pausa e retomada com visibilidade da aba e testa merge/deduplicação de mensagens e cards bloqueados. Exige o runner para as fixtures temporárias. As respostas simuladas dos demais testes incluem `sync/` e `catalog/` quando representam o participante real. Os dois servidores Vite usam diretórios de cache separados por modo.

O auxiliar `verify_scope_gaps.py` é um diagnóstico: informa quais instâncias passam ou falham no `full_clean` e reverte seus dados. Sua conclusão sem exceção não comprova que todas as regras são impostas pelos modelos; permissões e validações dos serviços/API têm testes próprios.

Para validar os blocos de limpeza a partir dos scripts atuais, em diretórios temporários do container:

```powershell
docker compose run --rm --no-deps -T -v "${PWD}:/repo:ro" backend python /repo/scripts/verify_full_clean.py
```

Esse verificador extrai somente o bloco de limpeza de backups de `full-clean.ps1` e `full-clean.sh`; não executa reset do banco nem dos dados de uso.

`check-realtime.cjs` verifica o WebSocket real com sessão, Daphne e Redis: alterações publicadas por outro processo chegam ao chat, às notificações e aos alertas globais; componentes compartilham uma conexão por aba. Testa ausência de consultas de mensagens no intervalo de 19 segundos com transporte saudável, queda forçada, recuperação HTTP e reconexão sem duplicatas. O servidor Vite de teste encaminha `/ws/`; o Channel Layer usa prefixo derivado do banco temporário, com expiração de mensagens/grupos.
