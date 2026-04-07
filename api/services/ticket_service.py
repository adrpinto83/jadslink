import hmac
import hashlib
import secrets
import base64
from config import get_settings

settings = get_settings()


def generate_ticket_code(secret: str) -> str:
    """Generate 8-character alphanumeric code using HMAC"""
    random_bytes = secrets.token_bytes(16)
    mac = hmac.new(secret.encode(), random_bytes, hashlib.sha256).digest()
    code = base64.b32encode(mac[:5]).decode().upper()
    return code[:8]


def generate_qr_base64(data: str) -> str | None:
    """Generate QR code as PNG base64 string"""
    try:
        import qrcode
        from io import BytesIO

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{qr_base64}"
    except Exception as e:
        print(f"QR generation error: {e}")
        return None
