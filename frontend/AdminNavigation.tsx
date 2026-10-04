import type { ReactNode } from "react";

export type AdminNavItem = {
  key: string;
  label: string;
  icon: "home" | "people" | "shield" | "calendar" | "more" | "global";
  badge?: number;
};

export function AdminNavIcon({ name }: { name: AdminNavItem["icon"] }) {
  const paths: Record<AdminNavItem["icon"], ReactNode> = {
    home: <path d="m3 10 9-7 9 7v10h-6v-6H9v6H3Z" />,
    people: (
      <>
        <circle cx="9" cy="7" r="3" />
        <path d="M2 21v-3a7 7 0 0 1 14 0v3M16 4a3 3 0 0 1 0 6M19 14a5 5 0 0 1 3 5v2" />
      </>
    ),
    shield: (
      <>
        <path d="m12 3 8 4v5c0 5-8 9-8 9s-8-4-8-9V7Z" />
        <path d="m8 12 3 3 5-6" />
      </>
    ),
    calendar: (
      <>
        <rect x="3" y="5" width="18" height="16" rx="2" />
        <path d="M7 3v4M17 3v4M3 11h18M8 15h2M14 15h2" />
      </>
    ),
    more: (
      <>
        <circle cx="4" cy="12" r="1" />
        <circle cx="12" cy="12" r="1" />
        <circle cx="20" cy="12" r="1" />
      </>
    ),
    global: (
      <>
        <circle cx="12" cy="12" r="9" />
        <ellipse cx="12" cy="12" rx="4" ry="9" />
        <path d="M3 12h18" />
      </>
    ),
  };
  return (
    <svg
      width="23"
      height="23"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}

export function AdminNavigation({
  items,
  current,
  onSelect,
  disabled = false,
  label = "Navegação administrativa",
}: {
  items: AdminNavItem[];
  current: string;
  onSelect: (key: string) => void;
  disabled?: boolean;
  label?: string;
}) {
  return (
    <nav className="adm-bottom" aria-label={label}>
      {items.map((item) => (
        <button
          key={item.key}
          type="button"
          aria-label={item.label}
          aria-current={current === item.key ? "page" : undefined}
          className={current === item.key ? "selected" : ""}
          disabled={disabled}
          onClick={() => onSelect(item.key)}
        >
          <span>
            <AdminNavIcon name={item.icon} />
            {Boolean(item.badge) && <b>{item.badge}</b>}
          </span>
          <small>{item.label}</small>
        </button>
      ))}
    </nav>
  );
}
