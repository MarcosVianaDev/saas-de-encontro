import { CachedImage } from "./CachedImage";
import { useRef, useState } from "react";
import type { Person } from "./types";
import { closeDialogOnBackdrop } from "./modal-backdrop";

export function ProfileGallery({ person }: { person: Person }) {
  const leading = person.outfit || person.image;
  const photos = [...new Set(person.photos || [])].filter(
    (url) => url !== leading,
  );
  const carousel = useRef<HTMLDivElement>(null);
  const viewer = useRef<HTMLDialogElement>(null);
  const [page, setPage] = useState(0);
  const allPhotos = [leading, ...photos];
  const [expandedIndex, setExpandedIndex] = useState(0);
  const swipe = useRef<{ x: number; y: number } | null>(null);
  const moveExpanded = (direction: number) => {
    setExpandedIndex((index) =>
      Math.max(0, Math.min(allPhotos.length - 1, index + direction)),
    );
  };
  const expand = (index: number) => {
    setExpandedIndex(index);
    viewer.current?.showModal();
  };
  const move = (direction: number) => {
    const element = carousel.current;
    if (element)
      element.scrollBy({
        left: direction * element.clientWidth,
        behavior: "smooth",
      });
  };
  return (
    <>
      <button
        className="profile-photo-button"
        aria-label={
          person.outfit ? "Ampliar foto do outfit" : "Ampliar foto principal"
        }
        onClick={() => expand(0)}
      >
        <CachedImage
          className="modal-photo"
          src={leading}
          alt={person.outfit ? `Outfit de ${person.name}` : person.name}
        />
      </button>
      {photos.length > 0 && (
        <section
          className="profile-photo-gallery"
          aria-label="Fotos do participante"
        >
          <div
            className="profile-photo-carousel"
            ref={carousel}
            onScroll={(e) =>
              setPage(
                Math.round(
                  e.currentTarget.scrollLeft / e.currentTarget.clientWidth,
                ),
              )
            }
          >
            {photos.map((url, index) => (
              <button
                key={url}
                className="profile-photo-button"
                aria-label={`Ampliar foto ${index + 1}`}
                onClick={() => expand(index + 1)}
              >
                <CachedImage
                  className="modal-photo"
                  src={url}
                  alt={`Foto ${index + 1} de ${person.name}`}
                />
              </button>
            ))}
          </div>
          {photos.length > 1 && (
            <div className="profile-carousel-controls">
              <button
                aria-label="Foto anterior"
                disabled={page === 0}
                onClick={() => move(-1)}
              >
                ‹
              </button>
              <span aria-live="polite">
                {page + 1} / {photos.length}
              </span>
              <button
                aria-label="Próxima foto"
                disabled={page === photos.length - 1}
                onClick={() => move(1)}
              >
                ›
              </button>
            </div>
          )}
        </section>
      )}
      <dialog
        ref={viewer}
        className="profile-photo-viewer"
        aria-label="Foto ampliada"
        onKeyDown={(e) => {
          if (e.key === "Escape") e.stopPropagation();
          if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
            e.preventDefault();
            e.stopPropagation();
            moveExpanded(e.key === "ArrowLeft" ? -1 : 1);
          }
        }}
        onClick={(e) => closeDialogOnBackdrop(e, () => viewer.current?.close())}
      >
        <button
          className="modal-close"
          aria-label="Fechar foto ampliada"
          onClick={() => viewer.current?.close()}
        >
          ×
        </button>
        <div
          className="expanded-photo-stage"
          onPointerDown={(e) => {
            if (!e.isPrimary || e.button !== 0) return;
            swipe.current = { x: e.clientX, y: e.clientY };
            e.currentTarget.setPointerCapture(e.pointerId);
          }}
          onPointerCancel={() => {
            swipe.current = null;
          }}
          onPointerUp={(e) => {
            const start = swipe.current;
            swipe.current = null;
            if (!start) return;
            const x = e.clientX - start.x;
            const y = e.clientY - start.y;
            if (Math.abs(x) >= 50 && Math.abs(x) > Math.abs(y))
              moveExpanded(x < 0 ? 1 : -1);
          }}
        >
          <CachedImage
            draggable={false}
            src={allPhotos[expandedIndex]}
            alt={
              expandedIndex === 0
                ? person.outfit
                  ? `Outfit de ${person.name}`
                  : person.name
                : `Foto ${expandedIndex} de ${person.name}`
            }
          />
        </div>
        {allPhotos.length > 1 && (
          <div className="profile-carousel-controls expanded-carousel-controls">
            <button
              aria-label="Foto anterior"
              disabled={expandedIndex === 0}
              onClick={() => moveExpanded(-1)}
            >
              ‹
            </button>
            <span aria-live="polite">
              {expandedIndex + 1} / {allPhotos.length}
            </span>
            <button
              aria-label="Próxima foto"
              disabled={expandedIndex === allPhotos.length - 1}
              onClick={() => moveExpanded(1)}
            >
              ›
            </button>
          </div>
        )}
      </dialog>
    </>
  );
}
