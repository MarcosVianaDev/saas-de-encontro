# Análise de segurança — 17/10/2026

Atualização posterior: os achados S01 e S02 foram tratados nas [correções de autorização e login administrativo](<Correcoes de autorizacao e login administrativo.md>). Os resultados e evidências abaixo preservam o estado observado antes dessa correção.

Revisão do código no commit `ab475f2eec9450ed0e13340ee052a55e79f98977`, com testes adicionais e execução local do Docker de produção em projeto descartável. Nenhum serviço externo foi atacado e os bancos existentes não foram utilizados. As alterações desta análise acrescentam testes, diagnóstico e documentação; não corrigem as regras da aplicação.

Não foi demonstrada SQL Injection nos campos e consultas testados. Foram reproduzidos **um achado de autorização de gravidade alta, com duas variantes, e três achados de gravidade média**. Há ainda recomendações de configuração e um aviso de dependência sem caminho de exploração identificado neste projeto.

As classificações abaixo são avaliações de risco do projeto, não notas CVSS calculadas. Resultados estruturados e respostas observadas: [evidências](security/2026-10-17-evidencias.json).

## Resultados prioritários

| ID | Gravidade | Resultado | Situação |
|---|---|---|---|
| S01 | Alta | Suspensão global e revogação de delegado não bloqueiam todas as operações de gestão | Reproduzido com leitura e alteração persistida |
| S02 | Média | Login do Django Admin sem limitação de tentativas | Reproduzido inclusive no gateway de produção |
| S03 | Média | Fotos entregues a outros participantes preservam coordenadas GPS do EXIF | Reproduzido com download autorizado por outro participante |
| S04 | Média | Exclusões permitem acumular arquivos além do limite de fotos ativas | Reproduzido com 12 envios e exclusões |
| S05 | Baixa / reforço | Ausência de HSTS, CSP e proteção de iframe nos documentos dos SPAs | Cabeçalhos ausentes; exploração por iframe inconclusiva |
| D01 | Informativa no contexto | Twisted 26.4.0 com aviso de ReDoS em IMAP | Dependência afetada; IMAP não identificado na aplicação |

### S01 — autorização inconsistente após suspensão ou revogação

**Pré-condição:** conta que já tinha poderes de gestão, posteriormente suspensa globalmente, ou usuário que recebeu delegação e teve seu vínculo administrativo desativado.

As verificações de [access()](../backend/api/event_admin.py#L77) e de [managed_event()](../backend/api/event_operations.py#L18) são diferentes. `access()` verifica suspensão e exige vínculo administrativo ativo. `managed_event()` depende de [is_manager()](../backend/apps/events/services.py#L30), que não verifica a suspensão global e aceita delegação sem exigir que o vínculo do destinatário continue ativo.

As duas reproduções usaram `GET` e `PUT /api/event-admin/configuration/`, com o identificador explícito do próprio evento:

| Conta | Bootstrap do painel | Leitura da configuração | Alteração da configuração | Alteração confirmada no banco |
|---|---|---|---|---|
| Gestor com `UserSuspension` ativa | 403 | 200 | 200 | Sim |
| Delegado com `EventAdministrator.is_active=False` | 404 | 200 | 200 | Sim |

A alteração foi realizada em um evento em rascunho. Não depende de carregar o painel nem de manipular o pacote JavaScript. Não foi demonstrado acesso a eventos arbitrários de outra organização: o problema reproduzido é a continuidade de poderes que deveriam ter sido suspensos ou revogados.

**Impacto:** um ex-gestor delegado ou gestor suspenso mantém operações administrativas por API. Os endpoints de transição e solicitação de novos eventos também dependem de `managed_event()` e precisam integrar a revisão, embora esta reprodução tenha confirmado diretamente a configuração.

**Correção recomendada:** centralizar a política de autorização; verificar usuário ativo, suspensão global, vínculo ativo do solicitante, evento, papel efetivo e validade das duas pontas da delegação em toda operação. Desativar o vínculo deve invalidar a delegação correspondente. Revisar também os autorizadores globais e de entrega dos SPAs para aplicar uma política consistente. Acrescentar regressões que exijam 403/404 e ausência de escrita nos dois cenários.

### S02 — tentativas ilimitadas no Django Admin

Foram enviadas **12 tentativas consecutivas com senha incorreta e CSRF válido** a `/admin/login/`. Todas retornaram 200, mostrando novamente o formulário, sem 429 ou bloqueio. O resultado foi igual nos testes internos e através do stack com HTTPS. A inspeção das rotas Nginx/Traefik não encontrou limitador externo para esse caminho.

O login da API tem limite por IP: com orçamento reduzido para três tentativas no teste, a quarta tentativa retornou 429. O mesmo identificador de conta com IPs distintos continuou recebendo respostas normais de falha. Isso demonstra a ausência de orçamento por conta nesse fluxo; não representa falsificação de IP através do gateway, nem um ataque distribuído real executado.

**Impacto:** exposição a tentativa de adivinhar senhas e credential stuffing, especialmente relevante para contas administrativas. Não foi obtida uma senha nem demonstrada tomada de conta.

**Correção recomendada:** limitar o Django Admin no aplicativo e/ou gateway, acrescentar proteção por conta e por IP, espera progressiva, monitoramento e MFA para gestores globais. Evitar bloqueio permanente acionável por terceiros. O Django documenta que limitação de tentativas de login não faz parte da autenticação padrão: [documentação oficial](https://docs.djangoproject.com/en/5.2/topics/auth/).

### S03 — vazamento de GPS nos arquivos de imagem

[PhotosView.post()](../backend/api/views.py#L393) verifica formato e dimensões, mas salva o arquivo original. A mesma estratégia aparece no upload de outfit em [profile_operations.py](../backend/api/profile_operations.py#L71).

O teste enviou um JPEG pequeno com EXIF GPS, completou as fotos públicas e simulou o perfil aprovado. **Outro participante** baixou a imagem pelo endpoint protegido. O JPEG recebido ainda continha as tags de latitude, longitude e suas referências — `[1, 2, 3, 4]` do IFD GPS.

**Impacto:** uma imagem que contenha metadados GPS pode divulgar localização precisa a outros participantes, inclusive em evento online. A falha depende de o arquivo enviado conter esses dados; não significa que todas as fotos contenham GPS. A reprodução confirmou fotos de perfil. O risco equivalente em outfit foi identificado pela leitura do código, sem uma segunda reprodução específica.

**Correção recomendada:** gerar uma nova imagem para distribuição, respeitando a orientação e removendo EXIF/GPS e metadados desnecessários. Se o original precisar ser mantido para evidência, armazená-lo separadamente e restringir sua consulta à finalidade autorizada.

### S04 — armazenamento acumulado sem quota por participante

O limite de dez fotos em [PhotosView.post()](../backend/api/views.py#L412) conta apenas registros com `removed_at` vazio. [PhotosView.delete()](../backend/api/views.py#L425) marca o registro como removido e mantém o arquivo.

Com 12 ciclos de envio e exclusão, foram aceitos 12 uploads, restaram zero fotos ativas e **12 arquivos continuaram no armazenamento**. As imagens eram minúsculas, totalizando apenas 816 bytes; não foi executado um ataque de esgotamento de disco. Cada arquivo individual pode ter até 10 MB na configuração atual.

**Impacto:** uma conta autorizada pode consumir armazenamento continuamente, apesar do limite de fotos exibido na interface. O limitador geral da API reduz a frequência, mas não limita o total acumulado ou o orçamento de bytes de upload.

**Correção recomendada:** quota de bytes e quantidade por participante/organização, limite de uploads por janela, alertas de consumo e política de retenção. A limpeza precisa preservar evidências e obrigações legais; não basta apagar indiscriminadamente arquivos removidos. Referência: [OWASP API4 — consumo irrestrito de recursos](https://api-security.owasp.org/editions/2023/en/0xa4-unrestricted-resource-consumption/).

### S05 — cabeçalhos de proteção dos documentos frontend

Nos documentos públicos e globais servidos pelo Nginx:

- `X-Content-Type-Options: nosniff` presente.
- `Cache-Control: private, no-store` presente no SPA global.
- `Content-Security-Policy`, `X-Frame-Options` e `Strict-Transport-Security` ausentes.
- `manage.py check --deploy` apontou `security.W004`, referente a HSTS.

O `X_FRAME_OPTIONS='DENY'` do Django protege respostas do Django; ele não adiciona esse cabeçalho ao HTML servido diretamente pelo Nginx do frontend.

**Limite da prova:** o teste de iframe entre origens distintas do mesmo site terminou numa página interna de erro do navegador, `chrome-error://chromewebdata/`. Portanto, esta rodada **não confirmou exploração de clickjacking**. A ausência dos cabeçalhos foi confirmada e merece reforço independentemente dessa limitação.

**Correção recomendada:** configurar `frame-ancestors 'none'` e, para compatibilidade, `X-Frame-Options: DENY` nos documentos frontend. Implantar CSP compatível com imagens blob, fontes e WebSocket utilizados. Configurar HSTS na borda HTTPS após avaliar os domínios e subdomínios afetados. Referências: [OWASP Clickjacking Defense](https://cheatsheetseries.owasp.org/cheatsheets/Clickjacking_Defense_Cheat_Sheet.html) e [CSP](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html).

## SQL Injection e demais testes

Os dez testes novos de entradas estão em [test_security_inputs.py](../backend/api/test_security_inputs.py). A revisão manual incluiu os pontos de SQL direto encontrados no backend.

| Superfície / técnica | Verificação | Resultado observado |
|---|---|---|
| E-mail e senha de login | Payloads com aspas, `OR`, comentário SQL e comando adicional | 400, sem sessão autenticada ou exclusão de registros |
| Busca de participantes | Aspas, `%`, `_`, barra e texto contendo `pg_sleep` | Busca literal, sem expansão de resultados; nenhuma chamada real a `pg_sleep` foi executada |
| Campos numéricos de filtro | Texto SQL, objeto JSON, lista, `NaN`, `Infinity` | 400 |
| Identificador do evento | Texto SQL, traversal e UUID inexistente | 400/404; sem traceback na resposta |
| Texto de mensagem | SQL, HTML/script e expressões de template | Armazenamento como texto literal |
| SQL da exportação | Aspas, barras e JSON com payloads importados em PostgreSQL no banco de teste | Valores preservados literalmente e tabela original intacta |
| XSS persistente em nome de evento | Texto com fechamento de script e `onerror` exibido no SPA global real | Texto literal visível, nenhum elemento injetado e nenhum script executado |
| CSRF | Login sem token e envio de mensagem com origem externa/sem token | 403; nenhuma mensagem criada |
| Elevação por cadastro | `is_superuser`, `is_staff`, `role` e `navigation` no corpo do registro | Conta criada sem privilégios; API global retorna 403 |
| Convite adulterado | UUID sem assinatura enviado como convite | 400 |
| Upload executável / XXE | SVG, HTML disfarçado de PNG e JPEG inválido | 400; nenhum arquivo salvo |
| Traversal no nome de upload | PNG válido com nome `../../payload.php` | Nome gerado no servidor, extensão `.png`, dentro da pasta do participante |
| URL executável em aviso | Esquemas `javascript:`, `data:` e `file:` | 400 |
| IDOR/BOLA e escopo por evento | Suíte existente de vínculos, papéis, duas abas, mídia, exportação e cabeçalhos forjados | Testes passaram; permanece a exceção S01 identificada por provas adicionais |
| WebSocket | Suíte existente de origem, autenticação, escopo, sessão revogada e mensagens inválidas | Testes passaram |
| Injeção de comandos e SSRF | Busca por execução dinâmica, shell e clientes HTTP controlados por entrada | Nenhum caminho desse tipo identificado no código analisado; não foi um teste exaustivo de rede |

O Bandit apontou SQL por concatenação em [sql_snapshot()](../backend/apps/events/export_snapshot.py#L156). Esse código gera um arquivo SQL offline, com nomes derivados dos modelos, identificadores cotados, aspas duplicadas e `standard_conforming_strings=on`. O teste adicional importou payloads no PostgreSQL e confirmou valores literais. O alerta **não foi confirmado como SQL Injection explorável**. Os demais usos de `cursor.execute()` encontrados usam instruções constantes ou parâmetros separados.

## Dependências e análise estática

- **npm audit:** zero vulnerabilidades conhecidas retornadas para o lockfile, incluindo dependências de desenvolvimento.
- **pip-audit:** 46 dependências examinadas, um aviso em Twisted 26.4.0: **CVE-2026-106454 / GHSA-8pqf-f4m5-798g**, classificado como moderado pelo fornecedor. Afeta tratamento de padrões de IMAP. Não foram encontrados serviço IMAP nem chamadas a esse componente no projeto; não foi demonstrada exploração via Django/Daphne. Na consulta, o aviso não informava versão corrigida. Acompanhar a correção upstream, sem tratar esse resultado como falha remota comprovada da aplicação HTTP. [Aviso oficial do Twisted](https://github.com/twisted/twisted/security/advisories/GHSA-8pqf-f4m5-798g).
- **Bandit:** 223 arquivos Python de produção, 7.025 linhas, seis alertas: dois médios e quatro baixos. Além do gerador SQL, foram classificados manualmente: bind em `0.0.0.0` necessário ao container, `execvp` com comando/argumentos constantes e sem shell, `assert` de consistência da carga demo e exceção ignorada apenas na limpeza de grupo WebSocket. Não foram promovidos a exploração confirmada.
- **Segredos:** busca por alguns padrões de chaves privadas e tokens não retornou arquivos. Apenas os exemplos `.env.example` e `.env.prod.example` são rastreados. Isso não equivale a uma varredura completa de todo o histórico Git nem certifica os segredos da VPS.

## Docker e produção

Foram validados os builds separados dos SPAs, bloqueio de download de pacotes sem permissão, cache privado, ausência de Node/npm na imagem final do frontend, HTTPS, cookies Secure/HttpOnly, WebSocket e ausência de carga automática de demonstração.

Como reforço adicional, o backend não define usuário não privilegiado no Dockerfile, o Compose não define quotas de CPU/memória/PIDs e as imagens de infraestrutura usam tags mutáveis. Recomenda-se usuário não-root, privilégios mínimos, limites de recursos e política de atualização/digests. Avaliar também uma conta de banco de execução com menos privilégios que a conta de migração. Esses pontos foram identificados na configuração; não foi demonstrada fuga de container ou comprometimento do host.

## Execução e reprodução

Na rodada final, **334 testes da suíte completa passaram**, além de **duas provas adicionais de autorização**, também concluídas. Os testes de navegador executaram os assets de produção com HTTPS local, sem mock das APIs. Os projetos descartáveis e seus volumes foram removidos ao final.

Os métodos de [security_review.py](../backend/security_review.py) produzem linhas `SECURITY_OBSERVATION`: são diagnósticos que registram comportamentos vulneráveis sem exigir que a vulnerabilidade permaneça para a suíte comum ficar verde. Assim, a conclusão sem erro dessas provas **não significa que os controles de segurança passaram**. Os controles seguros esperados estão cobertos separadamente pelos testes de regressão.

Para repetir com a versão atual dos arquivos, reconstruindo as imagens:

```sh
python scripts/verify_docker_environments.py --security
```

Esse modo executa as suítes `api`, `tests` e `security_review`, as verificações de navegador e `check --deploy`. Os relatórios detalhados ficam na pasta `.tools/docker-environments/<rodada>/`. `--skip-build` só deve ser usado quando as imagens já refletirem o código a ser auditado. As duas provas adicionais desta análise foram executadas no mesmo stack descartável após a suíte principal, usando o módulo de diagnóstico atualizado.

Para as dependências, em ambiente de ferramentas separado:

```sh
npm --prefix frontend audit --json
pip-audit -r requirements.lock --no-deps --disable-pip
```

## Ordem recomendada de correção e limites

1. Corrigir S01 e transformar as duas reproduções em testes que exijam bloqueio e ausência de alteração.
2. Proteger o login administrativo e adotar MFA.
3. Remover metadados das imagens distribuídas e estabelecer quotas de armazenamento/retenção.
4. Aplicar os cabeçalhos no frontend e HSTS na borda; repetir iframe com certificado e origem de teste válidos.
5. Acompanhar o aviso do Twisted e reforçar os containers.

A análise combina revisão de código, scanners e testes dirigidos. Não incluiu pentest da VPS real, engenharia social, teste de carga destrutivo, varredura de CVEs dos pacotes do sistema operacional das imagens ou fuzzing exaustivo de todos os campos e combinações. Os resultados negativos se limitam às superfícies e aos cenários descritos; não constituem garantia de ausência de outras vulnerabilidades.
