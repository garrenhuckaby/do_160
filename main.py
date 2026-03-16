import os
import fitz
import pytesseract
from pdf2image import convert_from_path
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import messagebox, Label

# --- Config ---
OUTPUT_FILE   = r"C:\Users\a02330649\Desktop\Life\do_160\extracted_text.txt"
TESSERACT     = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER       = r"C:\Users\a02330649\AppData\Local\poppler\poppler-25.12.0\Library\bin"
LOGO_PATH     = r"C:\Users\a02330649\Downloads\logoBat-removebg-preview.png"

pytesseract.pytesseract.tesseract_cmd = TESSERACT

def extract_text(pdf_path: str) -> str:
    """Your original extraction logic."""
    doc = fitz.open(pdf_path)
    text = "".join(page.get_text() for page in doc)
    doc.close()

    if len(text.strip()) >= 10:
        return text

    print("No text detected. Running OCR via Tesseract...")
    images = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER)
    return "".join(pytesseract.image_to_string(img) for img in images)

def handle_drop(event):
    # Clean the path (removes braces added by Windows/Tkinter for paths with spaces)
    pdf_path = event.data.strip('{}')
    
    if not pdf_path.lower().endswith('.pdf'):
        messagebox.showerror("Error", "Please drop a PDF file.")
        return

    label.config(text=f"Processing: {os.path.basename(pdf_path)}...")
    root.update()

    try:
        text = extract_text(pdf_path)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(text)
        messagebox.showinfo("Success", f"Done! Saved to:\n{OUTPUT_FILE}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")
    finally:
        label.config(text="Drop another PDF here")

# --- GUI Setup ---
root = TkinterDnD.Tk()
root.title("PDF OCR Dropzone")
root.geometry("400x250")

label = Label(root, text="Drop PDF file here", padx=10, pady=50, relief="groove", borderwidth=2)
label.pack(expand=True, fill="both", padx=20, pady=20)

# Register the label as a drop target
label.drop_target_register(DND_FILES)
label.dnd_bind('<<Drop>>', handle_drop)

root.mainloop()