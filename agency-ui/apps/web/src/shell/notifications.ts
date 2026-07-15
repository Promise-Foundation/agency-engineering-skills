/**
 * A toast-backed {@link NotificationService}. The host is constructed with this
 * as its `notifications`, so *any* `host.notifications.info/warn/error(...)` --
 * from the shell, a command handler, or a plugin -- surfaces as a visible toast.
 * React subscribes to the store through `useSyncExternalStore`.
 */

import type { NotificationService } from "@agency/skill-sdk";

export type ToastTone = "info" | "warn" | "error";

export interface Toast {
  id: number;
  tone: ToastTone;
  message: string;
}

type Listener = () => void;

const AUTO_DISMISS_MS = 6000;

class ToastStore {
  private toasts: Toast[] = [];
  private readonly listeners = new Set<Listener>();
  private nextId = 1;

  push(tone: ToastTone, message: string): void {
    const id = this.nextId++;
    this.toasts = [...this.toasts, { id, tone, message }];
    this.emit();
    setTimeout(() => this.dismiss(id), AUTO_DISMISS_MS);
  }

  dismiss(id: number): void {
    const next = this.toasts.filter((toast) => toast.id !== id);
    if (next.length === this.toasts.length) return;
    this.toasts = next;
    this.emit();
  }

  // Arrow properties keep a stable identity for useSyncExternalStore.
  readonly subscribe = (listener: Listener): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  readonly snapshot = (): Toast[] => this.toasts;

  private emit(): void {
    for (const listener of this.listeners) listener();
  }
}

export const toastStore = new ToastStore();

export const toastNotifications: NotificationService = {
  info: (message) => toastStore.push("info", message),
  warn: (message) => toastStore.push("warn", message),
  error: (message) => toastStore.push("error", message),
};
