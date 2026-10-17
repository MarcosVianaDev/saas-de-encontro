import { useState } from "react";
import { frontendConfig } from "../config";
import { mockCredentials } from "../participant-mock";

import { Icon } from "../components/Icon";

import type { ParticipantController } from "../hooks/useParticipantController";

type Props = Pick<
  ParticipantController,
  "canRegister" | "inviteName" | "loginSubmit" | "navigate" | "real"
>;

export function LoginPage({
  canRegister,
  inviteName,
  loginSubmit,
  navigate,
  real,
}: Props) {
  const [email, setEmail] = useState(
    frontendConfig.isDemonstration ? mockCredentials.email : "",
  );
  const [password, setPassword] = useState(
    frontendConfig.isDemonstration ? mockCredentials.password : "",
  );
  const [registering, setRegistering] = useState(false);
  const [loginForm, setLoginForm] = useState(
    real || frontendConfig.isDemonstration,
  );

  return (
    <>
      <div className="login-content">
        <div className="login-top">
          <span>SEU PRÓXIMO ENCONTRO</span>
          {!real && <span className="login-pill">Conecta SP</span>}
        </div>
        <div className="login-hero">
          <span className="hero-logo">
            <Icon name="people" size={66} />
          </span>
          <h2>
            Event<span>Connect</span>
          </h2>
          <p>
            Pessoas reais,
            <br />
            experiências incríveis.
          </p>
          <div className="hero-line" />
        </div>
        {loginForm || (real && !canRegister) ? (
          <form
            className="login-form"
            onSubmit={(event) => {
              event.preventDefault();
              void loginSubmit(email, password, registering);
            }}
          >
            <h3>
              {inviteName
                ? `Participar de ${inviteName}`
                : "Que bom ter você aqui."}
            </h3>
            <p>
              {real
                ? registering
                  ? inviteName
                    ? "Sua conta será vinculada a este evento. Complete o perfil após o cadastro."
                    : "Crie sua conta para começar."
                  : inviteName
                    ? "Entre para vincular sua participação a este evento."
                    : "Entre com sua conta. Seu vínculo determina a navegação."
                : "Acesso de demonstração, sem autenticação real."}
            </p>
            <label>
              E-mail
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="voce@exemplo.com"
                required
              />
            </label>
            <label>
              Senha
              <input
                type="password"
                autoComplete={registering ? "new-password" : "current-password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Sua senha"
                minLength={6}
                required
              />
            </label>
            <button className="primary" type="submit">
              {real
                ? registering
                  ? "Criar conta"
                  : inviteName
                    ? "Entrar no evento"
                    : "Entrar"
                : "Entrar na demonstração"}{" "}
              <Icon name="arrow" size={18} />
            </button>
            {canRegister && (
              <button
                className="text-button light"
                type="button"
                onClick={() => setLoginForm(false)}
              >
                Voltar
              </button>
            )}
            {real && canRegister && (
              <button
                className="text-button light"
                type="button"
                onClick={() => setRegistering(!registering)}
              >
                {registering ? "Já tenho uma conta" : "Criar uma conta"}
              </button>
            )}
          </form>
        ) : (
          <div className="login-actions">
            <button
              className="primary"
              onClick={() => {
                setRegistering(false);
                setLoginForm(true);
              }}
            >
              Entrar <Icon name="arrow" size={18} />
            </button>
            {canRegister && (
              <button
                className="secondary glass"
                onClick={() => {
                  if (real) {
                    setRegistering(true);
                    setLoginForm(true);
                  } else navigate("perfil");
                }}
              >
                Criar conta
              </button>
            )}
            {canRegister && (
              <button
                className="demo-link"
                onClick={() => {
                  if (real) {
                    setRegistering(true);
                    setLoginForm(true);
                  } else navigate("perfil");
                }}
              >
                {real ? "Criar uma nova conta" : "Explorar demonstração"}{" "}
                <Icon name="arrow" size={15} />
              </button>
            )}
          </div>
        )}
        {canRegister && (
          <div className="login-social-options">
            <div className="or">
              <span />
              ou continue com
              <span />
            </div>
            <button className="social" type="button" disabled>
              <span className="google-mark">G</span> Continuar com Google{" "}
              <small>Em breve</small>
            </button>
            <button className="social" type="button" disabled>
              <span className="apple-mark">●</span> Continuar com Apple{" "}
              <small>Em breve</small>
            </button>
          </div>
        )}
        <p className="login-terms">
          Sua próxima boa conversa está aqui.
          <br />
          {!real && (
            <span>Prévia com dados fictícios. Nenhuma conta é criada.</span>
          )}
        </p>
      </div>
    </>
  );
}
