/** Renders the toast queue from {@link toastStore}. Click a toast to dismiss it. */

import { useSyncExternalStore } from "react";
import { toastStore } from "./notifications";

export function Toasts() {
  const toasts = useSyncExternalStore(toastStore.subscribe, toastStore.snapshot);
  if (toasts.length === 0) return null;
  return (
    <div className="toasts" role="status" aria-live="polite">
      {toasts.map((toast) => (
        <button
          key={toast.id}
          type="button"
          className={`toast toast--${toast.tone}`}
          onClick={() => toastStore.dismiss(toast.id)}
        >
          {toast.message}
        </button>
      ))}
    </div>
  );
}
