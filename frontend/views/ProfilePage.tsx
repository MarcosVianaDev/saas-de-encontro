import { BIO_MIN_LENGTH, BIO_MAX_LENGTH } from "../profile-validation";
import { useEffect, useRef, useState } from "react";

import { api } from "../backend-client";

import { ProfileTopics } from "../ProfileTopics";

import { CachedImage } from "../CachedImage";
import { closeDialogOnBackdrop } from "../modal-backdrop";
import { birthMonths, birthYears, latestBirthYear } from "../birth-options";
import { brazilStates } from "../brazil-states";

import { ThemeSelector } from "../ThemeSelector";
import { HeightField } from "../components/HeightField";
import { Icon } from "../components/Icon";

import type { ParticipantController } from "../hooks/useParticipantController";

type Props = Pick<
  ParticipantController,
  | "busy"
  | "interests"
  | "leave"
  | "notify"
  | "photos"
  | "profile"
  | "purposes"
  | "real"
  | "removePhoto"
  | "run"
  | "saveProfile"
  | "serverData"
  | "setPhotos"
  | "setProfile"
  | "setServerData"
  | "uploadPhotos"
>;

export function ProfilePage({
  busy,
  interests,
  leave,
  notify,
  photos,
  profile,
  purposes,
  real,
  removePhoto,
  run,
  saveProfile,
  serverData,
  setPhotos,
  setProfile,
  setServerData,
  uploadPhotos,
}: Props) {
  const [thumbnailPhoto, setThumbnailPhoto] = useState<string | null>(null);
  const thumbnailDialog = useRef<HTMLDialogElement>(null);
  const uploadRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (thumbnailPhoto) thumbnailDialog.current?.showModal();
    else thumbnailDialog.current?.close();
  }, [thumbnailPhoto]);

  return (
    <>
      <form className="profile-form" id="profile-form" onSubmit={saveProfile}>
        <div className="profile-theme-toolbar">
          <ThemeSelector />
        </div>
        <fieldset
          disabled={Boolean(serverData?.event.readOnly)}
          className="profile-readonly-fields"
        >
          <h2>
            {real && serverData?.onboardingComplete
              ? "Meu perfil"
              : "Vamos criar seu perfil"}{" "}
            <span className="tiny-spark">✦</span>
          </h2>
          <p className="subtitle">
            Conte um pouco sobre você para
            <br />
            conectar com pessoas incríveis.
          </p>
          <div className="profile-avatar">
            <CachedImage
              src={photos[0] || "/images/profile-placeholder.svg"}
              alt="Foto principal do seu perfil"
            />
          </div>
          <div className="form-row">
            <label className="field">
              <span>Nome</span>
              <input
                value={profile.first}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    first: e.target.value,
                  })
                }
                required
                maxLength={150}
              />
            </label>
            <label className="field">
              <span>Sobrenome</span>
              <input
                value={profile.last}
                onChange={(e) =>
                  setProfile({ ...profile, last: e.target.value })
                }
                required
                maxLength={150}
              />
            </label>
          </div>
          <fieldset className="birth-field">
            <legend>Nascimento</legend>
            <div className="form-row">
              <label>
                Mês
                <select
                  value={profile.month}
                  onChange={(e) =>
                    setProfile({
                      ...profile,
                      month: e.target.value,
                    })
                  }
                >
                  {birthMonths.map((month, i) => (
                    <option key={month} value={i + 1}>
                      {month}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Ano
                <select
                  value={profile.year || String(latestBirthYear)}
                  required
                  onChange={(e) =>
                    setProfile({
                      ...profile,
                      year: e.target.value,
                    })
                  }
                >
                  {birthYears.map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </fieldset>
          <div className="form-row">
            <label className="field">
              <span>Gênero</span>
              <select
                value={profile.gender}
                onChange={(e) =>
                  setProfile({ ...profile, gender: e.target.value })
                }
              >
                <option value="Homens">Masculino</option>
                <option value="Mulheres">Feminino</option>
                <option>Não binário</option>
                <option>Prefiro não informar</option>
              </select>
            </label>
            <label className="field">
              <span>Estado em que reside (opcional)</span>
              <select
                value={profile.residenceState || ""}
                onChange={(e) =>
                  setProfile({ ...profile, residenceState: e.target.value })
                }
              >
                <option value="">Não informado</option>
                {brazilStates.map(([code, name]) => (
                  <option key={code} value={code}>
                    {name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <HeightField value={profile.height} onChange={(height) => setProfile({ ...profile, height })} />
          <label className="field bio-field">
            <span>Sobre você</span>
            <textarea
              value={profile.bio}
              onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
              rows={3}
              maxLength={BIO_MAX_LENGTH}
              minLength={BIO_MIN_LENGTH}
              required
            />
          </label>
          <div className="field-help">
            <span>Mínimo de {BIO_MIN_LENGTH} caracteres</span>
            <span>
              {profile.bio.length}/{BIO_MAX_LENGTH}
            </span>
          </div>
          {real ? (
            <ProfileTopics
              topics={serverData?.profileTopics || []}
              profile={profile}
              onChange={setProfile}
            />
          ) : (
            <>
              <fieldset className="filter-card">
                <legend>Interesses</legend>
                <p className="microcopy">
                  Selecione os interesses que combinam com você.
                </p>
                <div className="chips">
                  {interests.map((item) => (
                    <button
                      key={item}
                      type="button"
                      aria-pressed={profile.interests.includes(item)}
                      className={`chip ${profile.interests.includes(item) ? "active" : ""}`}
                      onClick={() =>
                        setProfile({
                          ...profile,
                          interests: profile.interests.includes(item)
                            ? profile.interests.filter(
                                (interest) => interest !== item,
                              )
                            : [...profile.interests, item],
                        })
                      }
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </fieldset>
              <fieldset className="filter-card">
                <legend>Finalidade no evento</legend>
                <p className="microcopy">
                  Selecione o que você procura neste evento.
                </p>
                <div className="chips">
                  {purposes.map((item) => (
                    <button
                      key={item}
                      type="button"
                      aria-pressed={profile.purpose === item}
                      className={`chip ${profile.purpose === item ? "active" : ""}`}
                      onClick={() =>
                        setProfile({
                          ...profile,
                          purpose: profile.purpose === item ? "" : item,
                        })
                      }
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </fieldset>
            </>
          )}
          <div className="section-label">
            <h3>Fotos do seu perfil</h3>
            <span>{photos.length}/10</span>
          </div>
          <p className="microcopy">
            As 3 primeiras são públicas. As demais, só após o match. Clique em
            uma foto pública para escolher a miniatura do perfil.
          </p>
          <div className="photo-grid">
            {photos.map((url, index) => (
              <div className="photo-tile" key={url + index}>
                {(
                  !real ? index < 3 : serverData?.publicPhotos?.includes(url)
                ) ? (
                  <button
                    type="button"
                    className="profile-thumbnail-choice"
                    aria-label={`Escolher foto pública ${index + 1} como miniatura`}
                    onClick={() => setThumbnailPhoto(url)}
                  >
                    <CachedImage
                      src={url}
                      alt={`Foto ${index + 1} do perfil`}
                    />
                  </button>
                ) : (
                  <CachedImage src={url} alt={`Foto ${index + 1} do perfil`} />
                )}
                <button
                  className="remove-photo"
                  disabled={Boolean(
                    real &&
                      serverData?.activated &&
                      serverData.publicPhotos?.includes(url),
                  )}
                  title={
                    real &&
                    serverData?.activated &&
                    serverData.publicPhotos?.includes(url)
                      ? "Esta foto faz parte do perfil aprovado para este evento e não pode ser alterada diretamente."
                      : undefined
                  }
                  type="button"
                  aria-label={`Remover foto ${index + 1}`}
                  onClick={() => removePhoto(url, index)}
                >
                  <Icon name="close" size={12} />
                </button>
                {index === 0 && <span>Principal</span>}
              </div>
            ))}
            {photos.length < 10 && (
              <button
                type="button"
                className="add-photo"
                aria-label="Adicionar foto"
                onClick={() => uploadRef.current?.click()}
              >
                <Icon name="plus" />
              </button>
            )}
          </div>
          <input
            ref={uploadRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            multiple
            hidden
            onChange={(e) => {
              const files = Array.from(e.target.files || []);
              e.target.value = "";
              void uploadPhotos(files);
            }}
          />
          <dialog
            ref={thumbnailDialog}
            className="thumbnail-dialog"
            aria-label="Escolher miniatura do perfil"
            onCancel={() => setThumbnailPhoto(null)}
            onClick={(e) =>
              closeDialogOnBackdrop(e, () => setThumbnailPhoto(null))
            }
          >
            <h2>Miniatura do perfil</h2>
            {thumbnailPhoto && (
              <CachedImage
                src={thumbnailPhoto}
                alt="Foto pública selecionada"
              />
            )}
            <div className="onboarding-actions">
              <button type="button" onClick={() => setThumbnailPhoto(null)}>
                Cancelar
              </button>
              <button
                type="button"
                className="primary"
                disabled={busy}
                onClick={() =>
                  void run(async () => {
                    if (!thumbnailPhoto) return;
                    if (real) {
                      const updated = await api.setThumbnail(thumbnailPhoto);
                      setPhotos(updated.photos);
                      setServerData(updated);
                    } else
                      setPhotos([
                        thumbnailPhoto,
                        ...photos.filter((url) => url !== thumbnailPhoto),
                      ]);
                    setThumbnailPhoto(null);
                    notify("Miniatura do perfil atualizada.");
                  })
                }
              >
                Definir como miniatura do perfil
              </button>
            </div>
          </dialog>
        </fieldset>
        <section className="profile-account" aria-label="Conta do participante">
          <h3>Conta</h3>
          <button
            type="button"
            className="account-logout"
            disabled={busy}
            onClick={() => void run(leave)}
          >
            Sair da conta
          </button>
        </section>
      </form>
    </>
  );
}
