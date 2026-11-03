/** Public configuration contains a local origin only, never provider credentials. */
export function localBackendOrigin(value?: string): string {
  try {
    const url = new URL(value === undefined ? "http://127.0.0.1:8000" : value);
    if (!(url.protocol === "http:" || url.protocol === "https:") ||
      !["127.0.0.1", "localhost", "[::1]"].includes(url.hostname) ||
      url.username || url.password || url.pathname !== "/" || url.search || url.hash) {
      throw new Error();
    }
    return url.origin;
  } catch {
    // Do not retain a URL parser error: its message can contain the supplied value.
    throw new Error("Invalid backend origin. Configure an HTTP(S) loopback origin without credentials, path, query, or fragment.");
  }
}
