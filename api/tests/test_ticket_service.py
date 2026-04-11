import pytest
from services.ticket_service import generate_ticket_code


def test_generate_ticket_code_uniqueness():
    """Test that generated ticket codes are unique."""
    # Generate a large number of codes to test for collisions
    num_codes = 10000
    secret = "test-secret"
    codes = {generate_ticket_code(secret) for _ in range(num_codes)}
    
    # The number of unique codes should be equal to the number of codes generated
    assert len(codes) == num_codes, f"Found {num_codes - len(codes)} collisions out of {num_codes} generated codes."

def test_generate_ticket_code_format():
    """Test that the generated ticket code has the correct format."""
    secret = "test-secret"
    code = generate_ticket_code(secret)
    
    # Check length
    assert len(code) == 8, f"Code length should be 8, but was {len(code)}"
    
    # Check if it's alphanumeric
    assert code.isalnum(), f"Code should be alphanumeric, but was '{code}'"
    
    # Check if it's uppercase
    assert code.isupper(), f"Code should be uppercase, but was '{code}'"

