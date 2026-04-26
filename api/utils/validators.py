"""Custom validators for Venezuelan data (cédula, referencia bancaria, teléfono)."""

import re


def validate_cedula(cedula: str) -> tuple[bool, str]:
    """
    Validate Venezuelan cédula (identity document).

    Valid formats:
    - V-12345678 or E-12345678 (with prefix and dash)
    - 12345678 (numbers only)
    - V12345678 (prefix without dash)

    Args:
        cedula: String with the cédula

    Returns:
        (is_valid: bool, normalized_value_or_error: str)
    """
    if not cedula:
        return False, "Cédula es requerida"

    # Remove whitespace and convert to uppercase
    cleaned = cedula.strip().upper()

    # Pattern: optional prefix (V/E/J/G) + optional dash + 6-9 digits
    pattern = r"^([VEJG])?-?(\d{6,9})$"
    match = re.match(pattern, cleaned)

    if not match:
        return False, "Formato inválido. Usa: V-12345678 o 12345678"

    prefix = match.group(1) or "V"  # Default to V if no prefix
    number = match.group(2)

    # Normalized format
    normalized = f"{prefix}-{number}"

    return True, normalized


def validate_referencia(referencia: str) -> tuple[bool, str]:
    """
    Validate bank transfer reference.

    Valid format:
    - 8-12 digits (Venezuelan banks vary)
    - Most banks accept 10 digits

    Args:
        referencia: String with the reference

    Returns:
        (is_valid: bool, normalized_value_or_error: str)
    """
    if not referencia:
        return False, "Referencia es requerida"

    # Remove spaces, dashes, and other non-numeric characters
    cleaned = referencia.replace(" ", "").replace("-", "").strip()

    # Must be only digits
    if not cleaned.isdigit():
        return False, "Solo números (sin caracteres especiales)"

    # Validate length (8-12 digits is typical for Venezuelan banks)
    if len(cleaned) < 8 or len(cleaned) > 12:
        return (
            False,
            f"Referencia debe tener entre 8 y 12 dígitos (tienes {len(cleaned)})",
        )

    return True, cleaned


def validate_phone_venezuela(phone: str) -> tuple[bool, str]:
    """
    Validate Venezuelan phone number.

    Valid formats:
    - 04121234567 (11 digits, mobile with 0)
    - 4121234567 (10 digits, mobile without 0)
    - 02121234567 (11 digits, landline)
    - 0414-1234567 (with dash)

    Args:
        phone: String with phone number

    Returns:
        (is_valid: bool, normalized_value_or_error: str)
    """
    if not phone:
        return False, "Teléfono es requerido"

    # Remove spaces, dashes, parentheses
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)

    # Must start with 0 (add if missing), then 4 or 2, then 2-3 digits area code, then 7 digits
    # Pattern: 0?(4|2)[0-9]{2}[0-9]{7}
    pattern = r"^0?(4|2)\d{9}$"

    if not re.match(pattern, cleaned):
        return False, "Formato inválido. Usa: 04121234567 o 02121234567"

    # Normalize: add leading 0 if missing
    if not cleaned.startswith("0"):
        cleaned = "0" + cleaned

    return True, cleaned


# Venezuelan banks list (commonly used for Pago Móvil)
BANCOS_VENEZUELA = [
    "Bancamiga",
    "Banesco",
    "Mercantil",
    "Venezuela",
    "Provincial (BBVA)",
    "BNC",
    "Bicentenario",
    "Tesoro",
    "Banplus",
    "Sofitasa",
    "Activo",
    "Exterior",
    "Bancaribe",
]


def validate_banco(banco: str) -> tuple[bool, str]:
    """
    Validate that banco is in the list of supported Venezuelan banks.

    Args:
        banco: Bank name

    Returns:
        (is_valid: bool, error_or_bank: str)
    """
    if not banco:
        return False, "Banco es requerido"

    if banco not in BANCOS_VENEZUELA:
        return False, f"Banco '{banco}' no está en la lista de bancos soportados"

    return True, banco
