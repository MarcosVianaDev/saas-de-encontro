import { frontendConfig } from "./config";
import { separatedSpa } from "./spa-routing";
import { request } from "./backend-client";

import {
  Administration,
  GlobalAdministration,
  LoginPage,
} from "./access-components";
import { Contexts } from "./Contexts";

import { ParticipantOnboarding } from "./ParticipantOnboarding";

import { LocationControl } from "./LocationControl";

import type { SessionData } from "./types";

import { useParticipantController } from "./hooks/useParticipantController";
import { Icon } from "./components/Icon";
import { stages } from "./participant-pages";
import { ProfilePage } from "./views/ProfilePage";
import { FiltersPage } from "./views/FiltersPage";
import { DiscoveryPage } from "./views/DiscoveryPage";
import { MessagesPage } from "./views/MessagesPage";
import { ParticipantsPage } from "./views/ParticipantsPage";
import { ParticipantAlerts } from "./components/ParticipantAlerts";
import { ParticipantMailbox } from "./components/ParticipantMailbox";
import { ParticipantNavigation } from "./components/ParticipantNavigation";
import { ParticipantDialogs } from "./components/ParticipantDialogs";
import { DemoSidebar } from "./components/DemoSidebar";
import { DemoContext } from "./components/DemoContext";

export function App() {
  const {
    activeChat,
    adminMode,
    applyData,
    applyFilters,
    authenticated,
    busy,
    canRegister,
    candidate,
    chatStates,
    chats,
    contexts,
    demoData,
    discoveryCount,
    details,
    eligible,
    eligibleFor,
    eventName,
    explainDiscoveryCount,
    filters,
    filterTopics,
    globalMode,
    interests,
    inviteName,
    leave,
    liked,
    loginSubmit,
    mailbox,
    match,
    mockEvent,
    navigate,
    navigateBottom,
    noticeUnread,
    notify,
    openChat,
    openNotification,
    page,
    people,
    photos,
    profile,
    purposes,
    ready,
    reviewParticipants,
    real,
    removePhoto,
    run,
    saveProfile,
    saved,
    seen,
    select,
    send,
    serverData,
    setActiveChat,
    setAdminMode,
    setAuthenticated,
    setDemoData,
    setDetails,
    setMailbox,
    setMatch,
    setNoticeUnread,
    setPage,
    setPeople,
    setPhotos,
    setProfile,
    setRemoteDiscovery,
    setSeen,
    setServerActive,
    setServerData,
    setToast,
    showDetails,
    stage,
    toast,
    toggleFavorite,
    unread,
    uploadPhotos,
  } = useParticipantController();
  if (separatedSpa && real && !ready)
    return (
      <main className="adm-loading">
        <p role="status">Carregando acesso…</p>
      </main>
    );
  if (authenticated && contexts)
    return (
      <Contexts
        contexts={contexts}
        onSelect={applyData}
        onLogout={() => void run(leave)}
      />
    );
  if (authenticated && globalMode)
    return <GlobalAdministration onSelect={applyData} onLogout={leave} />;
  if (
    frontendConfig.isDemonstration &&
    authenticated &&
    !adminMode &&
    demoData &&
    !demoData.onboardingComplete
  )
    return (
      <>
        <div className="backend-ribbon demo-onboarding-ribbon" role="status">
          <span>Demonstração · Complete seu perfil</span>
          <a href={location.pathname}>Voltar à Administração Global</a>
        </div>
        <ParticipantOnboarding
          mock
          data={demoData}
          onComplete={(data) => {
            setDemoData(data);
            applyData(data);
            navigate("filtros");
          }}
          onLogout={() => void run(leave)}
        />
      </>
    );
  if (
    real &&
    authenticated &&
    !adminMode &&
    serverData &&
    serverData.onboardingComplete === false &&
    !serverData.event.readOnly
  )
    return (
      <ParticipantOnboarding
        data={serverData}
        onComplete={(d) => {
          applyData(d);
          location.hash = "perfil";
          setPage("perfil");
        }}
        onLogout={() => void run(leave)}
      />
    );
  if (adminMode && authenticated)
    return (
      <Administration
        mock={!real}
        onContext={
          real
            ? () => {
                void request<SessionData>("contexts/", "POST", {
                  key: "global",
                }).then(applyData);
              }
            : undefined
        }
        onLogout={leave}
      />
    );
  return (
    <div
      className={`workspace ${real ? "django-workspace" : "mock-workspace"} ${frontendConfig.isDemonstration ? "runtime-demonstration" : ""} ${page === "login" ? "login-workspace" : "participant-workspace"} ${busy ? "is-busy" : ""}`}
      aria-busy={busy || !ready}
    >
      {!real && (
        <div className="backend-ribbon" role="status">
          <span>
            Demonstração ·{" "}
            {mockEvent ? `Ingresso em ${mockEvent.name}` : "Participante"}
          </span>
          {frontendConfig.isDemonstration && (
            <a href={location.pathname}>Voltar à Administração Global</a>
          )}
          {(!frontendConfig.isDemonstration || authenticated) && (
            <button
              onClick={() => {
                setAdminMode(true);
                setAuthenticated(true);
                location.hash = "admin-dashboard";
              }}
            >
              Explorar administração
            </button>
          )}
        </div>
      )}
      {real && (!ready || busy) && (
        <div className="backend-ribbon" role="status">
          {!ready ? "Conectando ao backend…" : busy ? "Salvando…" : "Conectado"}
        </div>
      )}
      {!real && <DemoSidebar navigate={navigate} page={page} />}
      <main className="main-area">
        {!real && (
          <div className="desktop-heading">
            <span>EXPERIÊNCIA DO PARTICIPANTE</span>
            <span className="event-tag">
              <i className="live-dot" /> Conecta São Paulo <span>/</span> Edição
              2026
            </span>
          </div>
        )}
        <div className="experience-layout">
          <section
            className={`app-screen ${page === "login" ? "login-screen" : ""}`}
            aria-label={stages[stage].title}
          >
            {page === "login" ? (
              <LoginPage
                canRegister={canRegister}
                inviteName={inviteName}
                loginSubmit={loginSubmit}
                navigate={navigate}
                real={real}
              />
            ) : (
              <>
                {(page === "perfil" || page === "filtros") && !real && (
                  <div className="onboarding-progress">
                    <button
                      className="icon-button"
                      aria-label="Voltar"
                      onClick={() =>
                        navigate(page === "perfil" ? "descobrir" : "perfil")
                      }
                    >
                      <Icon name="back" />
                    </button>
                    <div className="progress-track">
                      <span
                        style={{ width: page === "perfil" ? "50%" : "100%" }}
                      />
                    </div>
                    <span>{page === "perfil" ? "1" : "2"} de 2</span>
                  </div>
                )}
                {real && authenticated && serverData && (
                  <ParticipantAlerts
                    applyData={applyData}
                    busy={busy}
                    navigate={navigate}
                    notify={notify}
                    page={page}
                    run={run}
                    serverData={serverData}
                    setMailbox={setMailbox}
                  />
                )}
                <div
                  className={`screen-content ${page === "descobrir" ? "discovery-content" : ""} ${page === "mensagens" && activeChat !== null ? "chat-content" : ""}`}
                >
                  {real && authenticated && serverData && (
                    <>
                      <LocationControl
                        data={serverData}
                        onSupport={() => {
                          navigate("mensagens");
                          setMailbox("support");
                        }}
                        onChanged={(d) => {
                          setServerData(d);
                          setServerActive(d.active);
                          setPeople(d.people);
                          setRemoteDiscovery(d.discovery);
                        }}
                      />
                    </>
                  )}
                  {
                    <ParticipantMailbox
                      authenticated={authenticated}
                      mailbox={mailbox}
                      noticeUnread={noticeUnread}
                      openNotification={openNotification}
                      page={page}
                      real={real}
                      serverData={serverData}
                      setMailbox={setMailbox}
                      setNoticeUnread={setNoticeUnread}
                    />
                  }
                  {page === "perfil" && (
                    <ProfilePage
                      busy={busy}
                      interests={interests}
                      leave={leave}
                      notify={notify}
                      photos={photos}
                      profile={profile}
                      purposes={purposes}
                      real={real}
                      removePhoto={removePhoto}
                      run={run}
                      saveProfile={saveProfile}
                      serverData={serverData}
                      setPhotos={setPhotos}
                      setProfile={setProfile}
                      setServerData={setServerData}
                      uploadPhotos={uploadPhotos}
                    />
                  )}
                  {page === "filtros" && !serverData?.event.readOnly && (
                    <FiltersPage
                      filters={filters}
                      filterTopics={filterTopics}
                      applyFilters={applyFilters}
                      eligibleFor={eligibleFor}
                      interests={interests}
                      purposes={purposes}
                    />
                  )}
                  {page === "descobrir" && (
                    <DiscoveryPage
                      applyData={applyData}
                      candidate={candidate}
                      eligible={eligible}
                      eventName={eventName}
                      navigate={navigate}
                      page={page}
                      real={real}
                      seen={seen}
                      select={select}
                      serverData={serverData}
                      busy={busy}
                      reviewParticipants={reviewParticipants}
                      showDetails={showDetails}
                    />
                  )}

                  {page === "mensagens" && (
                    <MessagesPage
                      activeChat={activeChat}
                      applyData={applyData}
                      busy={busy}
                      chatStates={chatStates}
                      chats={chats}
                      mailbox={mailbox}
                      notify={notify}
                      openChat={openChat}
                      page={page}
                      people={people}
                      real={real}
                      run={run}
                      saved={saved}
                      send={send}
                      serverData={serverData}
                      setActiveChat={setActiveChat}
                      showDetails={showDetails}
                      toggleFavorite={toggleFavorite}
                      unread={unread}
                    />
                  )}
                  {page === "participantes" && (
                    <ParticipantsPage
                      chats={chats}
                      page={page}
                      people={people}
                      real={real}
                      serverData={serverData}
                      showDetails={showDetails}
                    />
                  )}
                </div>
                {(page === "perfil" || page === "filtros") &&
                  !serverData?.event.readOnly && (
                    <div className="onboarding-footer">
                      {page === "perfil" ? (
                        <button
                          type="submit"
                          form="profile-form"
                          className="primary"
                        >
                          Continuar <Icon name="arrow" size={19} />
                        </button>
                      ) : (
                        <button
                          type="submit"
                          form="filters-form"
                          className="primary"
                        >
                          Aplicar filtros <Icon name="arrow" size={19} />
                        </button>
                      )}
                    </div>
                  )}
                {[
                  "descobrir",
                  "mensagens",
                  "participantes",
                  "perfil",
                  "filtros",
                ].includes(page) && (
                  <ParticipantNavigation
                    discoveryCount={discoveryCount}
                    explainDiscoveryCount={explainDiscoveryCount}
                    navigateBottom={navigateBottom}
                    noticeUnread={noticeUnread}
                    page={page}
                    unread={unread}
                  />
                )}
              </>
            )}
          </section>
          {!real && <DemoContext page={page} people={people} stage={stage} />}
        </div>
        {!real && (
          <footer className="desktop-footer">
            <span>EventConnect © 2026</span>
            <span>Conexões que saem da tela.</span>
            <button onClick={() => void run(leave)}>
              Voltar ao início <Icon name="arrow" size={14} />
            </button>
          </footer>
        )}
      </main>
      {toast && (
        <div className="toast show" role="status">
          <Icon name="check" size={19} />
          {toast}
          <button aria-label="Fechar aviso" onClick={() => setToast("")}>
            <Icon name="close" size={15} />
          </button>
        </div>
      )}
      {
        <ParticipantDialogs
          applyData={applyData}
          chats={chats}
          details={details}
          liked={liked}
          match={match}
          openChat={openChat}
          photos={photos}
          real={real}
          select={select}
          setDetails={setDetails}
          setMatch={setMatch}
        />
      }
    </div>
  );
}
