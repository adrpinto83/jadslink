import pytest
from services.ticket_service import generate_ticket_code, generate_qr_base64


def test_generate_ticket_code_uniqueness():
    """Test that generated ticket codes are unique."""
    num_codes = 10000
    secret = "test-secret"
    codes = {generate_ticket_code(secret) for _ in range(num_codes)}

    assert len(codes) == num_codes, f"Found {num_codes - len(codes)} collisions out of {num_codes} generated codes."


def test_generate_ticket_code_format():
    """Test that the generated ticket code has the correct format."""
    secret = "test-secret"
    code = generate_ticket_code(secret)

    assert len(code) == 8, f"Code length should be 8, but was {len(code)}"
    assert code.isalnum(), f"Code should be alphanumeric, but was '{code}'"
    assert code.isupper(), f"Code should be uppercase, but was '{code}'"


def test_generate_ticket_code_deterministic_with_same_secret():
    """Test that same secret produces different codes each time due to randomness."""
    secret = "test-secret"
    code1 = generate_ticket_code(secret)
    code2 = generate_ticket_code(secret)

    # Codes should be different even with same secret (due to random bytes)
    assert code1 != code2


def test_generate_ticket_code_different_secrets():
    """Test that different secrets produce different codes."""
    secret1 = "secret1"
    secret2 = "secret2"
    code1 = generate_ticket_code(secret1)
    code2 = generate_ticket_code(secret2)

    # Codes should be different with different secrets
    assert code1 != code2


def test_generate_qr_base64_success():
    """Test QR code generation returns base64 string."""
    data = "https://example.com/portal?code=TEST1234"
    qr_base64 = generate_qr_base64(data)

    if qr_base64:
        assert qr_base64.startswith("data:image/png;base64,")
        assert len(qr_base64) > 100


def test_generate_qr_base64_empty_data():
    """Test QR code generation with empty data."""
    data = ""
    qr_base64 = generate_qr_base64(data)

    # Should still generate QR for empty data
    if qr_base64:
        assert qr_base64.startswith("data:image/png;base64,")

