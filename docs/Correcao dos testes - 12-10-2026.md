# Correção e validação dos testes — 12/10/2026

Após atualizar os cenários e corrigir os defeitos reproduzidos, a suíte passou. O [relatório anterior](<Reexecucao de testes - 12-10-2026.md>) foi preservado como diagnóstico histórico.

| Verificação | Resultado final |
|---|---|
| `docker compose exec -T backend python manage.py test tests api --noinput --verbosity 1` | **181 testes aprovados, sem falhas nem erros** |
| `python scripts/run-browser-tests.py` | **18 scripts de navegador aprovados** e 3 verificadores auxiliares concluídos sem erro de execução |
| `npm --prefix frontend run build` | Aprovado; permanecem avisos de diretivas `use client` do React Bootstrap |
| `manage.py check` | Aprovado |
| `manage.py makemigrations --check --dry-run` | Aprovado, nenhuma migração pendente |
| `verify_full_clean.py` em container, com fontes montadas somente para leitura | Aprovado para os blocos de limpeza de ambos os scripts |

## Alterações nos testes

As fixtures de eventos presenciais passaram a definir coordenadas válidas e registrar leitura de localização antes dos cenários sociais/ativação. O responsável pertence à equipe do cliente. O cenário antigo de cadastro guiado foi substituído por criação de cliente, atualização idempotente e criação separada do evento. A leitura para presença `OUTSIDE` agora fica entre o raio e a tolerância, conforme a regra atual. O seed verifica explicitamente que não cria jobs de exportação sob demanda.

Os 17 scripts de navegador anteriores foram atualizados e incorporados em `frontend/tests/browser`. Usam navegação inferior, dropdowns, abas, seletores de membros, toggles e cadastro de participante em duas etapas (ou três quando há requisitos obrigatórios). Login aguarda a seleção do evento e o contexto carregado. O teste de passes valida revelação automática e consumo único do crédito. O payload legado de perfil preserva os headers da resposta interceptada.

Foi acrescentado `check-export-button.cjs`: solicitação, progresso no botão desabilitado, polling, dropdown “Baixar dados”, links “Baixar o Termo”/“Baixar ZIP” e ausência da label de conclusão. A geração do pacote continua coberta pelos 9 testes de `api.test_exports`.

## Correções de aplicação

- O aviso de erro usa a classe `show`, evitando que o Bootstrap o esconda; logout malsucedido mantém a sessão e exibe o erro.
- A imagem de miniatura só é renderizada quando há uma foto selecionada, eliminando o elemento sem `src`.
- O UUID de evento informado na URL volta a ser enviado na validação do convite, login e cadastro; o teste verifica também divergência entre UUID e convite.
- O select de responsável tem nome acessível explícito.
- `ExportJob` está registrado no Django Admin para consulta, com criação/alteração/exclusão bloqueadas. Um teste novo verifica acesso de leitura e rejeição das escritas, sem alterar o job.

Nenhuma regra de autorização, localização ou vínculo do responsável foi afrouxada para aprovar os testes.

## Execução reproduzível e limites

`npm --prefix frontend run test:browser` executa o runner isolado. Ele cria banco/container, mídia/backups temporários e credenciais próprias; encerra os frontends, remove banco/container e apaga credenciais ao terminar. Os logs da rodada final ficam em `.tools/browser-tests/8f8491d32d28/`; a suíte completa de backend foi registrada em `.tools/test-backend-final.log`. Esses artefatos locais não são versionados. Instruções e pré-requisitos em [Testes de navegador](<../frontend/tests/README.md>).

Os auxiliares verificaram concorrência com duas conexões PostgreSQL, login HTTP/CSRF do Admin e diagnóstico de modelos. O diagnóstico de escopo agora ordena o par de participantes antes de persistir o match, permitindo concluir os probes. Ele continua informando casos aceitos/rejeitados pelo `full_clean`; terminar sem exceção não é uma certificação de todas as validações de domínio.

O cenário de origem/CSRF foi executado em loopback; conectividade física LAN permanece uma verificação separada. O teste de interface de exportação simula respostas de job; esta rodada não fez nova geração ponta a ponta por worker Celery externo. O verificador de `full-clean` extrai o código atual e trabalha em diretórios temporários, incluindo links, conteúdo oculto, subdiretórios, repetição e pasta ausente; nenhum reset dos dados de uso foi executado.
