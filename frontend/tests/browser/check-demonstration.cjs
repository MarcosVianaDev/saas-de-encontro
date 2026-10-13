const {
  BASE_URL,
  launch,
  testCredentials,
  login,
  api,
} = require("./helpers.cjs");
const assert = require("node:assert/strict");
const path = require("node:path");
(async () => {
  const browser = await launch();
  try {
    const context = await browser.newContext({
      viewport: { width: 390, height: 900 },
    });
    const global = await context.newPage();
    const errors = [];
    let demoApiCalls = 0;
    global.on("pageerror", (e) => errors.push(e.message));
    await login(global, testCredentials().adminEmail);
    const quick = global
      .locator("section")
      .filter({
        has: global.getByRole("heading", {
          name: "Ações rápidas",
          exact: true,
        }),
      });
    assert.deepEqual(await quick.getByRole("button").allTextContents(), [
      "+ Novo cliente",
      "+ Novo evento",
      "Demonstração",
    ]);
    context.on("page", (page) => {
      if (page !== global) {
        page.on("pageerror", (e) => errors.push(e.message));
        page.on("request", (r) => {
          if (new URL(r.url()).pathname.startsWith("/api/")) demoApiCalls++;
        });
      }
    });
    const [demo] = await Promise.all([
      context.waitForEvent("page"),
      quick.getByRole("button", { name: "Demonstração", exact: true }).click(),
    ]);
    await demo.waitForLoadState("networkidle");
    assert.equal(new URL(demo.url()).searchParams.get("demo"), "1");
    assert.equal(new URL(demo.url()).hash, "#login");
    assert.equal(
      await demo.getByLabel("E-mail", { exact: true }).inputValue(),
      "demonstracao@example.test",
    );
    assert.equal(
      await demo.getByLabel("Senha", { exact: true }).inputValue(),
      "Demonstracao123!",
    );
    assert.equal(
      await demo.locator(".participant-tile,.participant-onboarding").count(),
      0,
    );
    await demo
      .locator("form")
      .getByRole("button", { name: "Entrar na demonstração", exact: true })
      .click();
    await demo
      .getByRole("heading", { name: "Seu perfil", exact: true })
      .waitFor();
    assert.equal(
      await demo.getByLabel("Nome", { exact: true }).inputValue(),
      "",
    );
    await demo.getByLabel("Nome", { exact: true }).fill("Pessoa");
    await demo.getByLabel("Sobrenome", { exact: true }).fill("Demonstração");
    await demo.getByLabel("Mês de nascimento").selectOption("5");
    await demo.getByLabel("Ano de nascimento").selectOption("1994");
    await demo
      .getByLabel("Sobre você")
      .fill(
        "Perfil fictício para conhecer pessoas, trocar ideias sobre música e viagens e explorar a demonstração.",
      );
    await demo.getByRole("button", { name: "Continuar", exact: true }).click();
    await demo
      .getByRole("heading", { name: "Suas fotos", exact: true })
      .waitFor();
    assert.equal(await demo.locator(".onboarding-photos img").count(), 3);
    await demo
      .getByRole("button", { name: "Trocar foto", exact: true })
      .first()
      .click();
    await demo.waitForFunction(
      () => document.querySelectorAll(".onboarding-photos img").length === 2,
    );
    await demo
      .getByLabel("Adicionar fotos")
      .setInputFiles(
        path.resolve(
          "frontend/public/images/photo-1535713875002-d1d0cf377fde.jpg",
        ),
      );
    await demo.waitForFunction(
      () => document.querySelectorAll(".onboarding-photos img").length === 3,
    );
    await demo
      .getByRole("button", { name: "Concluir e ativar perfil", exact: true })
      .click();
    await demo
      .getByRole("button", { name: "Aplicar filtros", exact: false })
      .click();
    const nav = demo.locator(".bottom-nav");
    await nav
      .getByRole("button", { name: "Participantes", exact: true })
      .click();
    await demo.waitForFunction(
      () => document.querySelectorAll(".participant-tile").length === 50,
    );
    const fixture = await demo.evaluate(async () => {
      const { mockPeople, initialChats } = await import("/participant-mock.ts");
      return {
        count: mockPeople.length,
        ids: mockPeople.map((p) => p.id),
        ages: mockPeople.map((p) => p.age),
        genders: [...new Set(mockPeople.map((p) => p.gender))],
        interests: [...new Set(mockPeople.flatMap((p) => p.interests))],
        chats: Object.values(initialChats),
      };
    });
    assert.equal(fixture.count, 50);
    assert.equal(new Set(fixture.ids).size, 50);
    assert(Math.min(...fixture.ages) < 25 && Math.max(...fixture.ages) > 60);
    assert(
      fixture.genders.includes("Mulheres") &&
        fixture.genders.includes("Homens") &&
        fixture.genders.includes("Não binário"),
    );
    assert(fixture.interests.length >= 7);
    assert(
      fixture.chats.length >= 10 &&
        fixture.chats.every((chat) => chat.length > 0),
    );
    await demo
      .getByRole("button", { name: "Likes recebidos (8)", exact: true })
      .click();
    const likes = demo.getByRole("dialog", {
      name: "Likes recebidos",
      exact: true,
    });
    await likes.waitFor();
    assert.equal(await likes.locator(".conversation-row").count(), 8);
    await likes
      .getByRole("button", { name: "Fechar likes recebidos", exact: true })
      .click();
    await nav.getByRole("button", { name: "Descobrir", exact: true }).click();
    await demo
      .getByRole("button", { name: "Curtir Camila", exact: true })
      .click();
    await demo.getByRole("dialog", { name: "Novo match" }).waitFor();
    await demo
      .getByRole("button", { name: "Começar conversa", exact: true })
      .click();
    await demo
      .getByLabel("Mensagem", { exact: true })
      .fill("Mensagem fictícia depois do match.");
    await demo
      .getByRole("button", { name: "Enviar mensagem", exact: true })
      .click();
    await demo
      .getByText("Mensagem fictícia depois do match.", { exact: true })
      .waitFor();
    await demo
      .getByRole("button", { name: "Voltar às conversas", exact: true })
      .click();
    await demo
      .locator(".mailbox-tabs")
      .getByRole("button", { name: /Notificações/ })
      .click();
    const welcome = demo
      .locator(".notification-card")
      .filter({
        has: demo.getByRole("heading", {
          name: "Bem-vindos ao evento",
          exact: true,
        }),
      });
    await welcome.waitFor();
    await welcome.click();
    await welcome.getByText("Lida", { exact: true }).waitFor();
    assert(
      await demo.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    );
    await demo
      .getByRole("button", { name: "Explorar administração", exact: true })
      .click();
    await demo.locator(".adm-hero").waitFor();
    assert.equal(
      await demo.locator(".adm-stat strong").first().innerText(),
      "50",
    );
    await demo
      .locator(".adm-bottom")
      .getByRole("button", { name: "Mais", exact: true })
      .click();
    await demo
      .getByRole("button", { name: "Avisos do Evento", exact: true })
      .click();
    await demo
      .getByRole("heading", { name: "Roda de conversa às 16h", exact: true })
      .waitFor();
    await demo
      .getByRole("button", { name: "Sair da conta", exact: true })
      .filter({ visible: true })
      .click();
    await demo.getByLabel("E-mail", { exact: true }).waitFor();
    assert.equal(
      demoApiCalls,
      0,
      "Demo must not call the real API, including logout",
    );
    assert.equal(
      (await api(global, "session/")).authenticated,
      true,
      "Global session must remain authenticated",
    );
    assert.deepEqual(errors, []);
    console.log(
      "PASS: global quick action, prefilled login, profile/photos onboarding, 50 diverse participants, received likes, matches/messages, notifications/announcements, no API calls and preserved global session.",
    );
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
