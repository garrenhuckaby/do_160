import os
from docling.document_converter import DocumentConverter
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import messagebox, Label
from pathlib import Path

# --- Config ---
OUTPUT_MD = Path.home() / "Downloads" / "do160" / "processed_doc.md"

# Initialize Docling Converter (this loads the local AI models)
converter = DocumentConverter()

def handle_drop(event):
    pdf_path = event.data.strip('{}')
    
    if not pdf_path.lower().endswith('.pdf'):
        messagebox.showerror("Error", "Please drop a PDF file.")
        return

    label.config(text="AI is analyzing layout (Tables/Charts)...")
    root.update()

    try:
        # Docling does the heavy lifting here:
        # It identifies text, tables, and figures automatically.
        result = converter.convert(pdf_path)
        
        # We export to Markdown because it's the best format for Vector Search
        markdown_output = result.document.export_to_markdown()

        with open(OUTPUT_MD, "w", encoding="utf-8") as f:
            f.write(markdown_output)
            
        messagebox.showinfo("Success", f"AI-Ready Markdown saved to:\n{OUTPUT_MD}")
    except Exception as e:
        messagebox.showerror("Error", f"AI Parsing failed: {e}")
    finally:
        label.config(text="Drop another PDF for AI Vectorization")

def process_with_vision_tracking(pdf_path):
    result = converter.convert(pdf_path)
    
    # 1. Iterate through the "Layout Objects" Docling found
    for element, level in result.document.iterate_items():
        # Get the page number for THIS specific piece of text or image
        page_num = element.prov[0].page_no if element.prov else "Unknown"
        
        if element.label == "picture":
            print(f"--- Found Image on Page {page_num} ---")
            # Here you would:
            # 1. Export the 'element' as an image
            # 2. Run your Vision AI on it
            # 3. Insert the description into your text record
            
        elif element.label == "table":
            print(f"--- Found Table on Page {page_num} ---")
            # Tables are best kept as Markdown or JSON

# --- GUI Setup ---
root = TkinterDnD.Tk()
root.title("Docling AI Processor")
root.geometry("400x300")

label = Label(root, text="Drag & Drop PDF\n(Detects Charts, Tables, & Text)", 
              padx=10, pady=50, relief="groove", borderwidth=2, font=("Arial", 10, "bold"))
label.pack(expand=True, fill="both", padx=20, pady=20)

label.drop_target_register(DND_FILES)
label.dnd_bind('<<Drop>>', handle_drop)

root.mainloop()