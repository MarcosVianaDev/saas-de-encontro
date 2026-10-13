# Testes de navegador

Os scripts de `.tools/ui-check` foram atualizados e incorporados em `browser/`. As dependências Playwright e jsQR estão no `package-lock.json` do frontend.

Com Docker Compose e os serviços `db`/`redis` disponíveis, execute na raiz do projeto:

```powershell
npm --prefix frontend ci
npm --prefix frontend run test:browser
```

O comando cria banco e container temporários, prepara os dados de teste, inicia dois frontends Vite nas portas 18081 (Django) e 18082 (mock) e executa os scripts. A API temporária usa a porta 18000. Essas portas devem estar livres. Ao terminar, remove banco/container e encerra os frontends; mídia e backups de uso não são usados. Credenciais geradas para a rodada são apagadas.

Os resultados JSON e logs ficam em `.tools/browser-tests/<identificador>/`. As capturas ficam em `.tools/ui-check/screenshots/`. O runner também executa os auxiliares de concorrência, diagnóstico de modelos e login HTTP do Django Admin.

Para reexecutar apenas um cenário:

```powershell
python scripts/run-browser-tests.py check-onboarding.cjs
```

No Windows, o Playwright usa o Edge instalado. Em outros sistemas, execute `npx playwright install chromium` na pasta `frontend`. `TEST_BROWSER_PATH` permite informar outro executável. Os scripts podem ser executados diretamente com `TEST_BASE_URL`, `TEST_MOCK_URL`, `TEST_CREDENTIALS_FILE` e `TEST_BACKEND_CONTAINER`, mas os cenários com backend real criam/alteram dados: prefira o runner isolado.

`check-lan.cjs` verifica a origem dos links e aceitação/rejeição de CSRF; no runner, usa loopback. Conectividade com outro dispositivo da LAN exige verificação separada.

O teste de exportação da interface usa respostas simuladas de job para validar botão, progresso, polling e links PDF/ZIP. A geração real do pacote é coberta por `api.test_exports` no backend.

`check-demonstration.cjs` abre o mock a partir do dashboard global em um frontend configurado como Django, verifica o login preenchido, completa o perfil/fotos e valida os 50 perfis, likes, matches, mensagens, notificações e avisos. Também verifica ausência de chamadas à API no mock e preservação da sessão global.

O auxiliar `verify_scope_gaps.py` é um diagnóstico: informa quais instâncias passam ou falham no `full_clean` e reverte seus dados. Sua conclusão sem exceção não comprova que todas as regras são impostas pelos modelos; permissões e validações dos serviços/API têm testes próprios.

Para validar os blocos de limpeza a partir dos scripts atuais, em diretórios temporários do container:

```powershell
docker compose run --rm --no-deps -T -v "${PWD}:/repo:ro" backend python /repo/scripts/verify_full_clean.py
```

Esse verificador extrai somente o bloco de limpeza de backups de `full-clean.ps1` e `full-clean.sh`; não executa reset do banco nem dos dados de uso.
