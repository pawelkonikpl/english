import { useQuery } from "@tanstack/react-query";

import { api, queryKeys } from "./endpoints";

/** Modules enabled on the backend (ENABLED_MODULES). Fetched once per session. */
export function useEnabledModules() {
  return useQuery({ queryKey: queryKeys.modules, queryFn: api.modules, staleTime: Infinity });
}

/** True only once the module list has loaded and contains `key`. */
export function useModuleEnabled(key: string): boolean {
  const { data } = useEnabledModules();
  return data?.some((m) => m.key === key) ?? false;
}
