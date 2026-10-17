import { currentContext } from './backend-client';
import { frontendConfig } from './config';

type Update = { connected: boolean; topics: string[] };
const listeners = new Set<(update: Update) => void>();
let socket: WebSocket | null = null;
let connected = false;
let retry: number | undefined;
let heartbeat: number | undefined;
let debounce: number | undefined;
let attempts = 0;
let pongAt = 0;
let path = '';
const topics = new Set<string>();

export const realtimeConnected = () => connected;
function emit() {
  clearTimeout(debounce);
  debounce = window.setTimeout(() => {
    const update = { connected, topics: [...topics] };
    topics.clear();
    listeners.forEach(listener => listener(update));
  }, 80);
}
function stop() {
  clearTimeout(retry);
  clearInterval(heartbeat);
  const previous = socket;
  socket = null;
  path = '';
  connected = false;
  if (previous) { previous.onclose = null; previous.close(); }
}
function connect() {
  if (!listeners.size || document.hidden || frontendConfig.useMocks) return;
  const context = currentContext();
  const nextPath = context?.navigation === 'global' ? '/ws/global/'
    : context?.eventId && ['participant', 'administration'].includes(context.navigation)
      ? `/ws/events/${context.eventId}/${context.navigation}/` : '';
  if (socket && path === nextPath) return;
  stop();
  if (!nextPath) return;
  path = nextPath;
  const current = new WebSocket(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}${path}`);
  socket = current;
  current.onmessage = event => {
    if (socket !== current) return;
    let data: { type?: string; topics?: string[] };
    try { data = JSON.parse(event.data); } catch { return; }
    if (data.type === 'ready') {
      connected = true;
      attempts = 0;
      pongAt = Date.now();
      topics.add('reconnected');
      emit();
      heartbeat = window.setInterval(() => {
        if (Date.now() - pongAt > 65000) current.close();
        else if (current.readyState === WebSocket.OPEN) current.send(JSON.stringify({ type: 'ping' }));
      }, 30000);
    } else if (data.type === 'pong') pongAt = Date.now();
    else if (data.type === 'changed' && Array.isArray(data.topics)) {
      data.topics.filter(topic => ['messages', 'notifications', 'status'].includes(topic)).forEach(topic => topics.add(topic));
      emit();
    }
  };
  current.onclose = () => {
    if (socket !== current) return;
    stop();
    emit();
    retry = window.setTimeout(connect, Math.min(30000, 1000 * 2 ** Math.min(attempts++, 5)) + Math.random() * 1000);
  };
}
function changed() {
  stop();
  topics.clear();
  attempts = 0;
  emit();
  connect();
}
// One authenticated connection per tab, shared by messages and notifications.
export function subscribeRealtime(listener: (update: Update) => void) {
  if (frontendConfig.useMocks) return () => {};
  listeners.add(listener);
  if (listeners.size === 1) {
    window.addEventListener('eventconnect-context-changed', changed);
    document.addEventListener('visibilitychange', changed);
  }
  connect();
  return () => {
    listeners.delete(listener);
    if (!listeners.size) {
      stop();
      clearTimeout(debounce);
      topics.clear();
      window.removeEventListener('eventconnect-context-changed', changed);
      document.removeEventListener('visibilitychange', changed);
    }
  };
}
