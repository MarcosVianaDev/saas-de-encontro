import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { request } from "./backend-client";
import { closeDialogOnBackdrop } from "./modal-backdrop";
import { ProfileGallery } from "./ProfileGallery";
import type { Participant } from "./Administration";
import type { Person } from "./types";

export function AdminParticipantProfile({
  participant,
  mock,
  onClose,
}: {
  participant: Participant;
  mock: boolean;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [profile, setProfile] = useState<Person | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    dialog.current?.showModal();
    let cancelled = false;
    if (mock) {
      setProfile({
        id: participant.id,
        name: participant.name,
        age: participant.age || 0,
        gender: "",
        job: participant.job,
        image: participant.image,
        interests: [],
        online: participant.online,
        mutual: false,
      });
    } else {
      void request<Person>(`event-admin/participants/${participant.id}/profile/`)
        .then((data) => {
          if (!cancelled) setProfile(data);
        })
        .catch((e: Error) => {
          if (!cancelled) setError(e.message);
        });
    }
    return () => {
      cancelled = true;
    };
  }, [participant.id, mock]);

  return createPortal(
    <dialog
      ref={dialog}
      className="person-modal admin-participant-profile"
      aria-label={`Perfil de ${participant.name}`}
      onCancel={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      onClick={(e) => closeDialogOnBackdrop(e, onClose)}
    >
      <button
        autoFocus
        className="modal-close"
        aria-label="Fechar perfil"
        onClick={onClose}
      >
        ×
      </button>
      <div className="person-modal-content">
        {profile ? (
          <>
            <ProfileGallery person={profile} />
            <div className="modal-body">
              <h2>
                {profile.name}{profile.age > 0 ? `, ${profile.age}` : ""}
              </h2>
              {profile.job && <p>{profile.job}</p>}
              {profile.city && <p>{profile.city}</p>}
              {profile.bio && <p>{profile.bio}</p>}
              <div className="chips">
                {profile.interests.map((interest) => (
                  <span className="chip" key={interest}>{interest}</span>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="modal-body">
            <p role="status">{error || "Carregando perfil…"}</p>
          </div>
        )}
      </div>
    </dialog>,
    document.body,
  );
}
