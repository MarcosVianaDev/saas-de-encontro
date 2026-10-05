import {
  memo,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type ImgHTMLAttributes,
} from "react";

type Entry = {
  promise: Promise<string>;
  controller: AbortController;
  url?: string;
  size: number;
  users: number;
  touched: number;
};
const entries = new Map<string, Entry>();
const listeners = new Set<() => void>();
const lifetime = 5 * 60 * 1000;
const byteLimit = 64 * 1024 * 1024;
let generation = 0;
const protectedImage = (src?: string) =>
  !!src && /^\/api\/(?:photos|outfits|event-admin\/photos)\//.test(src);
function dispose(src: string, entry: Entry) {
  entries.delete(src);
  entry.controller.abort();
  if (entry.url) URL.revokeObjectURL(entry.url);
}
function prune() {
  let bytes = [...entries.values()].reduce((sum, entry) => sum + entry.size, 0);
  for (const [src, entry] of [...entries].sort(
    (a, b) => a[1].touched - b[1].touched,
  )) {
    if (entry.users) continue;
    if (
      Date.now() - entry.touched > lifetime ||
      bytes > byteLimit ||
      entries.size > 64
    ) {
      bytes -= entry.size;
      dispose(src, entry);
    }
  }
}
function acquire(src: string) {
  prune();
  let entry = entries.get(src);
  if (!entry) {
    const controller = new AbortController();
    entry = {
      controller,
      promise: Promise.resolve(""),
      users: 0,
      size: 0,
      touched: Date.now(),
    };
    const created = entry;
    entry.promise = fetch(src, {
      credentials: "same-origin",
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error(`Image HTTP ${response.status}`);
        const blob = await response.blob();
        if (controller.signal.aborted) throw new Error("Image cache cleared");
        created.size = blob.size;
        created.url = URL.createObjectURL(blob);
        prune();
        return created.url;
      })
      .catch((error) => {
        if (entries.get(src) === created) entries.delete(src);
        throw error;
      });
    entries.set(src, entry);
  }
  entry.users += 1;
  entry.touched = Date.now();
  return entry;
}
export function clearImageCache() {
  for (const [src, entry] of entries) dispose(src, entry);
  generation += 1;
  listeners.forEach((listener) => listener());
}
const subscribe = (listener: () => void) => {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
};

export const CachedImage = memo(function CachedImage({
  src,
  loading,
  ...props
}: ImgHTMLAttributes<HTMLImageElement>) {
  const image = useRef<HTMLImageElement>(null);
  const version = useSyncExternalStore(subscribe, () => generation);
  const [resolved, setResolved] = useState<{
    src: string;
    url: string;
    version: number;
  }>();
  useEffect(() => {
    if (!src || !protectedImage(src)) return;
    let active = true;
    let entry: Entry | undefined;
    const load = () => {
      if (entry || !active) return;
      entry = acquire(src);
      entry.promise
        .then((url) => {
          if (active) setResolved({ src, url, version });
        })
        .catch(() => {
          if (active)
            setResolved({
              src,
              url: "/images/profile-placeholder.svg",
              version,
            });
        });
    };
    let observer: IntersectionObserver | undefined;
    if (
      loading === "lazy" &&
      image.current &&
      typeof IntersectionObserver !== "undefined"
    ) {
      observer = new IntersectionObserver(
        (changes) => {
          if (changes.some((change) => change.isIntersecting)) {
            load();
            observer?.disconnect();
          }
        },
        { rootMargin: "100px" },
      );
      observer.observe(image.current);
    } else load();
    return () => {
      active = false;
      observer?.disconnect();
      if (entry) {
        entry.users -= 1;
        prune();
      }
    };
  }, [src, loading, version]);
  const cached =
    resolved && resolved.src === src && resolved.version === version
      ? resolved.url
      : undefined;
  return (
    <img
      {...props}
      ref={image}
      loading={loading}
      src={protectedImage(src) ? cached : src}
    />
  );
});
