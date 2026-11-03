import { ApiClientError, type HealthClient, type HealthResponse, type PublicFailure } from "./api";

export type SystemStatusState =
  | { phase: "loading" }
  | { phase: "ready"; health: HealthResponse }
  | { phase: "error"; failure: PublicFailure };

export async function checkSystemStatus(client: HealthClient, signal?: AbortSignal): Promise<SystemStatusState> {
  try {
    return { phase: "ready", health: await client.getHealth(signal) };
  } catch (error: unknown) {
    return { phase: "error", failure: error instanceof ApiClientError ? error.failure : { kind: "connection" } };
  }
}
