"""
OCR Service — Local, CPU-only text extraction using EasyOCR.
No API key required. Runs entirely on the local machine.
"""

import base64
import io
import os

# Lazy import: easyocr is only imported once first use (heavy initialization ~3-5s)
_reader = None

# Max image size: 50MB
MAX_IMAGE_SIZE = int(os.getenv("OCR_MAX_IMAGE_SIZE", "50")) * 1024 * 1024


def _get_reader():
    """Lazy-initialize EasyOCR reader in CPU-only mode."""
    global _reader
    if _reader is None:
        import easyocr
        print("[OCRService] Initializing EasyOCR (CPU mode)... this may take a moment on first load.")
        _reader = easyocr.Reader(["en"], gpu=False)
        print("[OCRService] Ready.")
    return _reader


class OCRService:
    def extract_text(self, image_base64: str) -> str:
        """
        Extract all text from a base64-encoded image using EasyOCR.
        Includes validation for base64 format and image size.

        Returns:
            A single cleaned string of extracted text, or "" on failure.
        """
        if not image_base64:
            return ""

        try:
            # Validate input length to prevent DoS
            if len(image_base64) > MAX_IMAGE_SIZE:
                print(f"[OCRService] Image too large: {len(image_base64)} bytes (max: {MAX_IMAGE_SIZE})")
                return ""

            # Strip data URI prefix if present (e.g., "data:image/png;base64,...")
            if "," in image_base64:
                image_base64 = image_base64.split(",", 1)[1]
            
            # Add back missing padding (valid base64 must be multiple of 4)
            missing_padding = len(image_base64) % 4
            if missing_padding:
                image_base64 += "=" * (4 - missing_padding)

            # Validate base64 characters
            import string
            valid_chars = set(string.ascii_letters + string.digits + "+/=")
            if not all(c in valid_chars for c in image_base64):
                print("[OCRService] Invalid base64 characters detected")
                return ""

            # Decode and validate
            try:
                image_bytes = base64.b64decode(image_base64, validate=True)
            except Exception as e:
                print(f"[OCRService] Base64 decode error: {e}")
                return ""

            # Validate decoded size
            if len(image_bytes) > MAX_IMAGE_SIZE:
                print(f"[OCRService] Decoded image too large: {len(image_bytes)} bytes")
                return ""

            reader = _get_reader()
            results = reader.readtext(image_bytes, detail=0, paragraph=True)
            extracted = " ".join(results).strip()
            print(f"[OCRService] Extracted {len(extracted)} chars from image ({len(image_bytes)} byte image).")
            return extracted
        except Exception as e:
            print(f"[OCRService] Error during OCR: {e}")
            return ""
