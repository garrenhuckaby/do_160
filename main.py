import os
import fitz
import pytesseract
from pdf2image import convert_from_path

# --- Config ---
PDF_PATH      = r"C:\Users\a02330649\Desktop\Life\DO-160G\Document_Cloud\waterproof.pdf"
OUTPUT_FILE   = r"C:\Users\a02330649\Desktop\Life\DO-160G\extracted_text.txt"
TESSERACT     = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER       = r"C:\Users\a02330649\AppData\Local\poppler\poppler-25.12.0\Library\bin"

pytesseract.pytesseract.tesseract_cmd = TESSERACT

def extract_text(pdf_path: str) -> str:
    """Extract text from PDF, falling back to OCR if needed."""
    doc = fitz.open(pdf_path)
    text = "".join(page.get_text() for page in doc)
    doc.close()

    if len(text.strip()) >= 10:
        return text

    print("No text detected. Running OCR via Tesseract...")
    images = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER)
    ocr_text = ""
    for i, image in enumerate(images):
        print(f"  OCR on page {i+1}/{len(images)}...")
        ocr_text += pytesseract.image_to_string(image)
    return ocr_text

def main():
    if not os.path.exists(PDF_PATH):
        print(f"Error: Could not find PDF: {PDF_PATH}")
        return

    try:
        text = extract_text(PDF_PATH)
    except Exception as e:
        print(f"Failed: {e}")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Done! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()