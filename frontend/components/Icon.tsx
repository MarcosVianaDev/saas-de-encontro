import { memo, type ReactNode } from "react";
export type IconName =
  | "people"
  | "search"
  | "heart"
  | "chat"
  | "user"
  | "filter"
  | "arrow"
  | "back"
  | "close"
  | "star"
  | "camera"
  | "plus"
  | "pin"
  | "work"
  | "check"
  | "send"
  | "grid";
const paths: Record<IconName, ReactNode> = {
  people: (
    <>
      <circle cx="12" cy="7" r="3" />
      <path d="M6 21v-3a6 6 0 0 1 12 0v3M3 10a2 2 0 1 0 0-4m18 4a2 2 0 1 1 0-4M2 20v-3a4 4 0 0 1 3-4m17 7v-3a4 4 0 0 0-3-4" />
    </>
  ),
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="m16 16 5 5" />
    </>
  ),
  heart: (
    <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z" />
  ),
  chat: <path d="M4 4h16v13H9l-5 4V4Zm4 5h8m-8 4h5" />,
  user: (
    <>
      <circle cx="12" cy="7" r="4" />
      <path d="M4 22v-2a8 8 0 0 1 16 0v2" />
    </>
  ),
  filter: (
    <>
      <path d="M3 6h18M3 12h18M3 18h18" />
      <circle cx="8" cy="6" r="2" />
      <circle cx="16" cy="12" r="2" />
      <circle cx="9" cy="18" r="2" />
    </>
  ),
  arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
  back: <path d="m15 5-7 7 7 7" />,
  close: <path d="m5 5 14 14M19 5 5 19" />,
  star: (
    <path d="m12 2 3 6.2 6.8 1-4.9 4.8 1.2 6.8-6.1-3.2-6.1 3.2 1.2-6.8L2.2 9.2l6.8-1L12 2Z" />
  ),
  camera: (
    <>
      <path d="M3 7h4l2-3h6l2 3h4v14H3V7Z" />
      <circle cx="12" cy="13" r="4" />
    </>
  ),
  plus: <path d="M12 4v16M4 12h16" />,
  pin: (
    <>
      <path d="M19 9c0 5-7 12-7 12S5 14 5 9a7 7 0 1 1 14 0Z" />
      <circle cx="12" cy="9" r="2" />
    </>
  ),
  work: (
    <>
      <rect x="3" y="7" width="18" height="14" rx="2" />
      <path d="M8 7V3h8v4M3 12h18m-9 0v3" />
    </>
  ),
  check: <path d="m5 12 4 4L19 6" />,
  send: <path d="m3 3 19 9-19 9 4-9-4-9Zm4 9h15" />,
  grid: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </>
  ),
};

function IconComponent({ name, size = 22 }: { name: IconName; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}
export const Icon = memo(IconComponent);
