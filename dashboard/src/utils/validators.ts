/**
 * Validators for Venezuelan banking data
 */

export interface ValidationResult {
  isValid: boolean;
  error?: string;
  normalized?: string;
}

/**
 * Validate Venezuelan cédula (identity document)
 *
 * Valid formats:
 * - V-12345678 or E-12345678 (with prefix and dash)
 * - 12345678 (numbers only)
 * - V12345678 (prefix without dash)
 */
export function validateCedula(cedula: string): ValidationResult {
  if (!cedula) {
    return { isValid: false, error: 'Cédula es requerida' };
  }

  const cleaned = cedula.trim().toUpperCase();

  // Pattern: optional prefix (V/E/J/G) + optional dash + 6-9 digits
  const pattern = /^([VEJG])?-?(\d{6,9})$/;
  const match = cleaned.match(pattern);

  if (!match) {
    return { isValid: false, error: 'Formato inválido. Usa: V-12345678 o 12345678' };
  }

  const prefix = match[1] || 'V'; // Default to V
  const number = match[2];
  const normalized = `${prefix}-${number}`;

  return { isValid: true, normalized };
}

/**
 * Validate bank transfer reference
 *
 * Valid format: 8-12 digits
 */
export function validateReferencia(referencia: string): ValidationResult {
  if (!referencia) {
    return { isValid: false, error: 'Referencia es requerida' };
  }

  // Remove spaces, dashes, and other non-numeric
  const cleaned = referencia.replace(/\D/g, '');

  // Must be 8-12 digits
  if (cleaned.length < 8 || cleaned.length > 12) {
    return {
      isValid: false,
      error: `Referencia debe tener entre 8 y 12 dígitos (tienes ${cleaned.length})`,
    };
  }

  return { isValid: true, normalized: cleaned };
}

/**
 * Validate Venezuelan phone number
 */
export function validatePhoneVenezuela(phone: string): ValidationResult {
  if (!phone) {
    return { isValid: false, error: 'Teléfono es requerido' };
  }

  // Remove spaces, dashes, parentheses
  const cleaned = phone.replace(/[\s\-\(\)]/g, '');

  // Pattern: 0?(4|2)[0-9]{9}
  const pattern = /^0?(4|2)\d{9}$/;

  if (!pattern.test(cleaned)) {
    return { isValid: false, error: 'Formato inválido. Usa: 04121234567 o 02121234567' };
  }

  // Normalize: add leading 0 if missing
  const normalized = cleaned.startsWith('0') ? cleaned : '0' + cleaned;

  return { isValid: true, normalized };
}

/**
 * List of Venezuelan banks (for Pago Móvil)
 */
export const BANCOS_VENEZUELA = [
  'Bancamiga',
  'Banesco',
  'Mercantil',
  'Venezuela',
  'Provincial (BBVA)',
  'BNC',
  'Bicentenario',
  'Tesoro',
  'Banplus',
  'Sofitasa',
  'Activo',
  'Exterior',
  'Bancaribe',
];

/**
 * Validate bank is in the supported list
 */
export function validateBanco(banco: string): ValidationResult {
  if (!banco) {
    return { isValid: false, error: 'Banco es requerido' };
  }

  if (!BANCOS_VENEZUELA.includes(banco)) {
    return { isValid: false, error: `Banco '${banco}' no está soportado` };
  }

  return { isValid: true, normalized: banco };
}
