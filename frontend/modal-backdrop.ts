import type { MouseEvent } from "react";

export function closeDialogOnBackdrop(
  event: MouseEvent<HTMLDialogElement>,
  close: () => void,
) {
  if (event.target !== event.currentTarget) return;
  const bounds = event.currentTarget.getBoundingClientRect();
  if (
    event.clientX < bounds.left ||
    event.clientX > bounds.right ||
    event.clientY < bounds.top ||
    event.clientY > bounds.bottom
  )
    close();
}
