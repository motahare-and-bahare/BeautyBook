/**
 * Persian display labels for the authentication screens.
 *
 * The API keeps sending stable English enum values (`customer`, `active`, ...). Only the display
 * text is translated here, so changing the language never changes an API contract.
 */

const ROLE_LABELS: Readonly<Record<string, string>> = {
  customer: 'مشتری',
  salon_owner: 'سالن‌دار',
  admin: 'مدیر',
}

const STATUS_LABELS: Readonly<Record<string, string>> = {
  active: 'فعال',
  pending_approval: 'در انتظار تأیید',
  rejected: 'رد شده',
  suspended: 'تعلیق‌شده',
}

/**
 * Persian text for a backend field error. Backend messages are English, so a known field is
 * always rendered with its own Persian message instead of leaking the original string.
 */
const FIELD_ERROR_LABELS: Readonly<Record<string, string>> = {
  full_name: 'نام کامل را بررسی کنید.',
  email: 'ایمیل معتبر وارد کنید.',
  password: 'رمز عبور باید بین ۱۲ تا ۱۲۸ کاراکتر باشد.',
  confirm_password: 'رمزهای عبور یکسان نیستند.',
}

export function roleLabel(role: string): string {
  return ROLE_LABELS[role] ?? role
}

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status
}

export function roleLabels(roles: readonly string[]): string {
  return roles.map(roleLabel).join('، ')
}

export function fieldErrorLabel(field: string, fallback: string): string {
  return FIELD_ERROR_LABELS[field] ?? fallback
}
