import type { Dispatch, SetStateAction } from "react";
import { BIO_MIN_LENGTH, BIO_MAX_LENGTH } from "../profile-validation";

import { type FormEvent } from "react";

import { api } from "../backend-client";
import { saveGenderFilters } from "../gender-filters";
import { normalizeTopicFilters } from "../topic-filters";

import type { Profile, Filters, SessionData, ProfileTopic } from "../types";
import { type Page } from "../participant-pages";

type Options = {
  applyData: (data: SessionData) => void;
  navigate: (next: Page) => void;
  notify: (text: string) => void;
  photos: string[];
  profile: Profile;
  real: boolean;
  eventId?: string;
  filterTopics: ProfileTopic[] | null;
  run: (action: () => Promise<void>) => Promise<void>;
  setFilters: Dispatch<SetStateAction<Filters>>;
  setPhotos: Dispatch<SetStateAction<string[]>>;
  setServerActive: Dispatch<SetStateAction<boolean>>;
};

export function useParticipantProfile({
  applyData,
  navigate,
  notify,
  photos,
  profile,
  real,
  eventId,
  filterTopics,
  run,
  setFilters,
  setPhotos,
  setServerActive,
}: Options) {
  const saveProfile = async (event: FormEvent) => {
    event.preventDefault();
    if (
      profile.bio.trim().length < BIO_MIN_LENGTH ||
      profile.bio.trim().length > BIO_MAX_LENGTH
    ) {
      notify(
        `A bio deve conter entre ${BIO_MIN_LENGTH} e ${BIO_MAX_LENGTH} caracteres.`,
      );
      return;
    }
    if (photos.length < 3) {
      notify("Adicione pelo menos 3 fotos para continuar.");
      return;
    }
    if (!real) {
      navigate("filtros");
      return;
    }
    await run(async () => {
      applyData(await api.saveProfile(profile));
      navigate("descobrir");
      notify("Perfil salvo.");
    });
  };
  const applyFilters = async (draft: Filters) => {
    if (!real) {
      if (eventId) saveGenderFilters(eventId, draft);
      setFilters({ ...draft, interests: [...draft.interests] });
      navigate("descobrir");
      notify("Preferências aplicadas. Boas conexões!");
      return;
    }
    await run(async () => {
      const { genders: _genders, ...backendFilters } = normalizeTopicFilters(draft, filterTopics || []);
      const data = await api.saveFilters({ ...backendFilters, gender: "Todos" });
      saveGenderFilters(data.event.id, draft);
      applyData(data);
      navigate("descobrir");
      notify("Preferências aplicadas. Boas conexões!");
    });
  };
  const removePhoto = async (url: string, index: number) => {
    if (real) {
      await run(async () => {
        const result = await api.removePhoto(url);
        setPhotos(result.photos);
        setServerActive(result.active);
      });
      return;
    }
    if (url.startsWith("blob:")) URL.revokeObjectURL(url);
    setPhotos((old) => old.filter((_, i) => i !== index));
  };
  const uploadPhotos = async (files: File[]) => {
    const valid = files.filter(
      (f) =>
        ["image/jpeg", "image/png", "image/webp"].includes(f.type) &&
        f.size <= 10 * 1024 * 1024,
    );
    if (valid.length !== files.length)
      notify("Use fotos JPG, PNG ou WebP de até 10 MB.");
    if (valid.length + photos.length > 10)
      notify("Você pode adicionar até 10 fotos.");
    const selected = valid.slice(0, 10 - photos.length);
    if (!real) {
      setPhotos((old) => [
        ...old,
        ...selected.map((f) => URL.createObjectURL(f)),
      ]);
      return;
    }
    await run(async () => {
      for (const file of selected) {
        const result = await api.upload(file);
        setPhotos(result.photos);
        setServerActive(result.active);
      }
    });
  };
  return { saveProfile, applyFilters, removePhoto, uploadPhotos };
}
