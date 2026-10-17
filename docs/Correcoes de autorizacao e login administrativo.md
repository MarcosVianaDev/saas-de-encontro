# Correções de autorização e login administrativo

Atualização de 17/10/2026, referente aos achados S01 e S02 da [análise de segurança](<Analise de seguranca - 17-10-2026.md>).

## Autorização

Contas com suspensão global vigente são bloqueadas nas APIs autenticadas, nos serviços de gestão, no Django Admin e na entrega dos SPAs. O encerramento de sessão continua disponível. Suspensões com prazo vencido não bloqueiam a conta.

O papel delegado exige vínculo ativo do destinatário como moderador e uma origem administrativa ativa, sem suspensão. Um vínculo revogado não concede acesso à configuração, transição ou solicitação de eventos, mesmo que exista uma referência antiga de delegação no banco. Ao salvar a desativação do vínculo ou a mudança de papel do destinatário, a referência é removida; reativar o vínculo não restaura automaticamente a delegação.

As verificações são aplicadas em cada requisição e nos serviços de domínio, incluindo escrita direta pela API, sem depender das opções mostradas pelo frontend.

## Django Admin em `/mcx/`

O painel está em `/mcx/` e o formulário em `/mcx/login/`. `/admin` e `/admin/...` retornam 404, sem redirecionamento para o endereço novo. Os links de administração, alteração de senha, proxy Vite e rotas Nginx foram atualizados.

Os assets do Django continuam em `/static/admin/...`: esse é o nome do pacote estático, independente do endereço de acesso ao painel.

## Proteção das tentativas de login

O login administrativo usa contadores atômicos no cache compartilhado. No Compose, esse cache é Redis e os limites valem entre processos e sessões diferentes.

| Variável | Padrão | Efeito |
|---|---|---|
| `DJANGO_ADMIN_LOGIN_IP_LIMIT` | `5` | Até cinco submissões por IP na janela |
| `DJANGO_ADMIN_LOGIN_ACCOUNT_LIMIT` | `10` | Até dez submissões para a mesma conta, entre IPs diferentes |
| `DJANGO_ADMIN_LOGIN_WINDOW_SECONDS` | `300` | Janela fixa de cinco minutos |

O limitador conta as submissões do formulário, inclusive as bem-sucedidas; não redefine o orçamento ao abrir outra sessão. As chaves de conta normalizam Unicode, espaços e caixa e são armazenadas como HMAC, sem nome ou IP em texto puro. A identificação do IP usa a mesma configuração de proxies confiáveis da API; o acesso direto ao backend deve usar `DRF_NUM_PROXIES=0`.

Quando excedido, o endpoint responde **HTTP 429**, `Retry-After` com o tempo restante e cache desativado. Se o cache de proteção estiver indisponível, responde 503 e não tenta autenticar. A proteção CSRF permanece obrigatória. Não há bloqueio permanente da conta.

Configure as variáveis no `.env` ou `.env.prod` e recrie os serviços para aplicar mudanças de configuração. A troca do endereço não substitui o limitador.

## Validação e implantação

Rodada concluída: **353 testes do backend passaram**, assim como as verificações em navegador no Docker de produção com HTTPS. Gestor suspenso e delegado revogado receberam 403 nas leituras/escritas de configuração, sem alterações no banco. O login válido em `/mcx/`, o 404 no caminho antigo e as respostas 429 após o limite foram confirmados. [Evidências da correção](security/2026-10-17-correcoes.json).

Os testes de regressão em `api.test_management_security` verificam suspensão, revogação, referências antigas, delegação válida, suspensão vencida, limites por IP/conta, tentativas simultâneas, normalização Unicode, prazo de recuperação, CSRF, falha de cache e login válido. Os testes de produção verificam o novo endereço e o bloqueio do antigo através do Nginx e HTTPS.

```sh
python scripts/verify_docker_environments.py --security
```

Para implantar os novos caminhos, código e bundles em produção:

```sh
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build --force-recreate --wait
```

Não há alteração de esquema de banco nesta correção. O relatório e as evidências da análise inicial preservam os resultados anteriores à correção.
