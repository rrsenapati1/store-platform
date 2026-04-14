export function isStoreRuntimeDeveloperBootstrapEnabled(): boolean {
  return import.meta.env.DEV || import.meta.env.MODE === 'test';
}
