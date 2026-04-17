export function normalizeGiftCardCodeInput(value: string): string {
  return value.toUpperCase();
}

export function resolveGiftCardCodePayload(value: string): string | null {
  const normalized = normalizeGiftCardCodeInput(value).trim();
  return normalized ? normalized : null;
}
