/**
 * A tiny async-read hook. Everything the shell reads from the resource services
 * (`get`, `relations`, `list`) is a Promise, so this centralises the
 * loading/error/cancellation bookkeeping. Reads are keyed by `deps`; a stale
 * in-flight read is ignored when `deps` changes or the component unmounts.
 */

import { useEffect, useState } from "react";
import type { DependencyList } from "react";

export interface AsyncState<T> {
  value: T | undefined;
  loading: boolean;
  error: string | null;
}

export function useAsync<T>(compute: () => Promise<T>, deps: DependencyList): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({
    value: undefined,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let active = true;
    setState((prev) => ({ value: prev.value, loading: true, error: null }));
    compute().then(
      (value) => {
        if (active) setState({ value, loading: false, error: null });
      },
      (error: unknown) => {
        if (active) setState({ value: undefined, loading: false, error: String(error) });
      },
    );
    return () => {
      active = false;
    };
    // `compute` is intentionally excluded: reads are keyed by the caller's deps.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}
