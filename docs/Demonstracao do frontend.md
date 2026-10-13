# Demonstração do frontend

No dashboard da Administração Global, **Ações rápidas → Demonstração** aparece após **Novo evento**. Abre uma nova aba na tela de login, com e-mail e senha fictícios preenchidos. Não é necessário alterar `FRONTEND_DATA_MODE` no `.env` nem recriar o frontend para usar esse botão.

Clique em **Entrar na demonstração** e complete nome, sobrenome, nascimento, gênero e descrição do perfil. A etapa seguinte apresenta três fotos de exemplo; é possível trocá-las por arquivos locais. **Concluir e ativar perfil** termina o cadastro simulado e abre as preferências, de onde é possível acessar os participantes.

| Dados disponíveis | Conteúdo |
|---|---|
| Participantes | 50 perfis únicos, com idades entre 19 e 68 anos, profissões e interesses variados |
| Gênero | Mulheres, homens, não binário e preferência por não informar |
| Matches e mensagens | 14 conversas iniciais de matches; é possível criar outro match e enviar mensagens |
| Likes recebidos | 8 perfis disponíveis para consultar |
| Notificações | Likes, match, mensagem e avisos; abrir uma notificação a marca como lida |
| Avisos internos | Boas-vindas, roda de conversa e orientação de respeito, também em **Mais → Avisos do Evento** no painel administrativo simulado |
| Suporte | Atendimento fictício com histórico e envio de mensagens local |

Após o cadastro, **Explorar administração** abre o painel do evento simulado com a mesma base de 50 perfis. Os exemplos administrativos incluem situações de cadastro, suspensão, banimento e moderação. Eventos de demonstração agendados/encerrados mantêm os respectivos cenários de exemplo.

A URL `?demo=1` escolhe o mock somente na aba atual. Dados e operações ficam em memória, sem chamadas à API real; recarregar a aba reinicia a demonstração no login e restaura os exemplos. E-mail e senha exibidos são apenas exemplos. O botão **Voltar à Administração Global** e a aba original permitem retornar ao acesso real, cuja sessão é preservada, inclusive ao sair da conta no mock.

Essa demonstração é distinta da carga `seed_demo` do backend, que continua dependendo das configurações de desenvolvimento e do banco. Interesses e finalidades estáticos permanecem apenas no mock; os acessos reais continuam consultando seus catálogos na API.

Fontes: `frontend/config.ts`, `GlobalAdministration.tsx`, `participant-mock.ts`, `ParticipantOnboarding.tsx`, `ParticipantExtras.tsx` e `administration-mock.ts`. O teste `frontend/tests/browser/check-demonstration.cjs` verifica o botão, login preenchido, cadastro, fotos, diversidade dos perfis, interações, ausência de chamadas à API e preservação da sessão global.

Para verificar o fluxo com ambiente temporário:

```powershell
python scripts/run-browser-tests.py check-demonstration.cjs
```

## Validação em 12/10/2026

Build aprovado. Os 19 scripts de navegador foram aprovados: 18 na rodada completa e `check-mvp.cjs` na reexecução após ajustar a espera pela volta ao contexto global. Os 3 auxiliares concluíram sem erro de execução. Logs completos em `.tools/browser-tests/62176894c943/` e reexecução em `.tools/browser-tests/e10006927cae/`. O teste específico da demonstração também passou em `.tools/browser-tests/7f6a54a16c57/`, incluindo troca de foto, ausência de chamadas à API e preservação da sessão global. Os ambientes temporários foram encerrados pelo runner.
