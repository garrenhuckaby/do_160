import os
from docling.document_converter import DocumentConverter
from pathlib import Path

# --- Config ---
INPUT_PDF = '/content/do_160/Document_Cloud/703931356-Rtca-Do-160g-part-2.pdf'
OUTPUT_MD = '/content/do_160/output.md'

# Initialize Docling Converter (this loads the local AI models)
converter = DocumentConverter()

def main():
    if not os.path.exists(INPUT_PDF):
        print(f"Error: Input PDF not found at {INPUT_PDF}")
        return

    print(f"Processing PDF: {INPUT_PDF}")
    try:
        # Docling does the heavy lifting here:
        # It identifies text, tables, and figures automatically.
        result = converter.convert(INPUT_PDF)
        
        # We export to Markdown because it's the best format for Vector Search
        markdown_output = result.document.export_to_markdown()

        # Ensure the output directory exists
        output_dir = os.path.dirname(OUTPUT_MD)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(OUTPUT_MD, "w", encoding="utf-8") as f:
            f.write(markdown_output)
            
        print(f"AI-Ready Markdown saved to: {OUTPUT_MD}")
    except Exception as e:
        print(f"AI Parsing failed: {e}")

if __name__ == "__main__":
    main()
