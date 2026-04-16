export function normalizePromotionCodeInput(value: string): string {
  return value.toUpperCase();
}

export function resolvePromotionCodePayload(value: string): string | null {
  const normalized = normalizePromotionCodeInput(value).trim();
  return normalized ? normalized : null;
}
