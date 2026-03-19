import os
import torch
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions, 
    EasyOcrOptions, 
    AcceleratorOptions, 
    AcceleratorDevice
)

# --- Config ---
INPUT_PDF = '/content/do_160/703931356-Rtca-Do-160g-part-7.pdf'
OUTPUT_MD = '/content/do_160/output.md'

def main():
    if not os.path.exists(INPUT_PDF):
        print(f"Error: File not found.")
        return

    # 1. Hardware Detection (Crucial for local deployment)
    # This automatically uses the T4 in Colab or your GPU/CPU at home.
    if torch.cuda.is_available():
        device = AcceleratorDevice.CUDA
    elif torch.backends.mps.is_available(): # Support for Mac M1/M2/M3
        device = AcceleratorDevice.MPS
    else:
        device = AcceleratorDevice.CPU
    
    print(f"ALFRD Engine using: {device}")

    # 2. Configure for Local Portability
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    
    # Use EasyOCR - better for local apps because it's bundled in Python
    pipeline_options.ocr_options = EasyOcrOptions()

    # 3. Memory Management
    pipeline_options.accelerator_options = AcceleratorOptions(
        device=device,
        num_threads=4 # Limits CPU usage so your computer doesn't freeze
    )

    # 4. Conversion
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    print("Parsing document structure...")
    try:
        result = converter.convert(INPUT_PDF)
        markdown_output = result.document.export_to_markdown()

        output_path = Path(OUTPUT_MD)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_output)
            
        print(f"Success! File ready for local RAG at: {OUTPUT_MD}")
        
    except Exception as e:
        print(f"Parsing failed: {e}")

if __name__ == "__main__":
    main()