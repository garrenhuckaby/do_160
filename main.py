import os
import re
import torch
import pandas as pd
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    EasyOcrOptions,
    AcceleratorOptions,
    AcceleratorDevice
)
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem, TextItem, DocItemLabel

# --- Config ---
INPUT_PDF  = '/content/do_160/Document_Cloud/703931356-Rtca-Do-160g-part-7.pdf'
OUTPUT_DIR = '/content/do_160/'
OUTPUT_MD  = os.path.join(OUTPUT_DIR, 'output.md')
IMAGES_DIR = os.path.join(OUTPUT_DIR, 'images')
TABLES_DIR = os.path.join(OUTPUT_DIR, 'tables')

# Items whose bounding box top-edge falls within this fraction of page height
# are treated as headers; bottom fraction treated as footers — both excluded.
HEADER_THRESHOLD = 0.08   # top 8% of page
FOOTER_THRESHOLD = 0.92   # bottom 8% of page


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def setup_directories():
    for path in [OUTPUT_DIR, IMAGES_DIR, TABLES_DIR]:
        Path(path).mkdir(parents=True, exist_ok=True)


def detect_device():
    if torch.cuda.is_available():
        return AcceleratorDevice.CUDA
    elif torch.backends.mps.is_available():
        return AcceleratorDevice.MPS
    return AcceleratorDevice.CPU


def build_converter(device):
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.images_scale = 2.0
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True
    pipeline_options.ocr_options = EasyOcrOptions()
    pipeline_options.accelerator_options = AcceleratorOptions(
        device=device,
        num_threads=4
    )
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )


def is_header_or_footer(item, doc) -> bool:
    """
    Return True if the item's bounding box sits in the top or bottom margin
    of its page. Docling normalises bbox coordinates 0-1 with y=0 at top.
    """
    if not item.prov:
        return False
    prov = item.prov[0]
    bbox = prov.bbox
    if bbox is None:
        return False
    return bbox.t < HEADER_THRESHOLD or bbox.b > FOOTER_THRESHOLD


def sanitize_filename(text: str, max_len: int = 80) -> str:
    """Convert caption text into a safe filesystem name."""
    text = text.strip()
    text = re.sub(r'\s+', '_', text)
    text = re.sub(r'[^\w\-.]', '', text)
    text = re.sub(r'_+', '_', text)
    text = text.strip('_')
    return text[:max_len] if text else "unnamed"


def get_caption_text(item, doc) -> str:
    """
    Find the best human-readable label for a figure or table.

    Strategy:
      1. Use Docling's structured item.captions references (most reliable).
      2. Fall back to scanning ±3 neighbouring items for a line beginning
         with "Figure", "Fig.", or "Table".
    """
    # 1. Structured captions
    if hasattr(item, 'captions') and item.captions:
        texts = []
        for cap_ref in item.captions:
            try:
                cap_item = doc.resolve_ref(cap_ref)
                if cap_item and hasattr(cap_item, 'text') and cap_item.text:
                    texts.append(cap_item.text.strip())
            except Exception:
                pass
        if texts:
            return ' '.join(texts)

    # 2. Neighbour scan fallback
    all_items = list(doc.iterate_items())
    target_idx = next(
        (idx for idx, (it, _) in enumerate(all_items) if it is item), None
    )
    if target_idx is None:
        return ""

    window = range(max(0, target_idx - 3), min(len(all_items), target_idx + 4))
    for idx in window:
        candidate, _ = all_items[idx]
        if candidate is item:
            continue
        if isinstance(candidate, TextItem) and candidate.text:
            t = candidate.text.strip()
            if re.match(r'^(Figure|Fig\.|Table)\s', t, re.IGNORECASE):
                return t

    return ""


def build_filename(item, doc, prefix: str, fallback_index: int) -> str:
    """
    Return a filename stem derived from the item's caption,
    falling back to prefix_page<N>_<index> if no caption found.
    """
    caption = get_caption_text(item, doc)
    if caption:
        return sanitize_filename(caption)
    page_num = item.prov[0].page_no if item.prov else "unknown"
    return f"{prefix}_page{page_num}_{fallback_index:03d}"


def unique_path(directory: str, stem: str, ext: str) -> str:
    """Return a path that doesn't exist yet, appending _1, _2 … if needed."""
    path = os.path.join(directory, f"{stem}{ext}")
    counter = 1
    while os.path.exists(path):
        path = os.path.join(directory, f"{stem}_{counter}{ext}")
        counter += 1
    return path


# ---------------------------------------------------------------------------
# Export functions
# ---------------------------------------------------------------------------

def save_markdown(doc, output_path: str):
    """
    Export markdown with figures referenced by filename.
    Post-process to strip running header/footer lines (e.g. "2010 RTCA, Inc.").
    """
    md = doc.export_to_markdown(image_mode=ImageRefMode.REFERENCED)

    clean_lines = []
    for line in md.splitlines():
        stripped = line.strip()
        if re.match(
            r'^(©|\d{4}\s+RTCA|Page\s+\d+|RTCA,\s*Inc\.?)[\s\d\-\.]*$',
            stripped, re.IGNORECASE
        ):
            continue
        clean_lines.append(line)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write('\n'.join(clean_lines))
    print(f"  Markdown saved → {output_path}")


def save_figures(doc, images_dir: str):
    """
    Save each PictureItem as a PNG named from its document caption.
    Header/footer regions are skipped.
    """
    saved = 0
    skipped_hf = 0
    fig_index = 0

    for item, _ in doc.iterate_items():
        if not isinstance(item, PictureItem):
            continue
        fig_index += 1

        if is_header_or_footer(item, doc):
            skipped_hf += 1
            continue

        try:
            image = item.get_image(doc)
            if image is None:
                print(f"  [warn] Figure {fig_index}: no image data, skipping.")
                continue

            stem = build_filename(item, doc, prefix="figure", fallback_index=fig_index)
            out_path = unique_path(images_dir, stem, ".png")
            image.save(out_path)
            saved += 1
            print(f"    Saved: {os.path.basename(out_path)}")

        except Exception as e:
            print(f"  [warn] Could not save figure {fig_index}: {e}")

    print(f"  Figures done → {images_dir}  "
          f"({saved} saved, {skipped_hf} header/footer skipped)")
    return saved


def save_tables(doc, tables_dir: str):
    """
    Save each TableItem as CSV + JSON named from its document caption.
    Header/footer regions are skipped.
    """
    saved = 0
    skipped_hf = 0
    tbl_index = 0

    for item, _ in doc.iterate_items():
        if not isinstance(item, TableItem):
            continue
        tbl_index += 1

        if is_header_or_footer(item, doc):
            skipped_hf += 1
            continue

        try:
            df = item.export_to_dataframe()
            stem = build_filename(item, doc, prefix="table", fallback_index=tbl_index)

            csv_path  = unique_path(tables_dir, stem, ".csv")
            # Use the same stem (already unique from csv check) for JSON
            json_stem = os.path.splitext(os.path.basename(csv_path))[0]
            json_path = os.path.join(tables_dir, f"{json_stem}.json")

            df.to_csv(csv_path, index=False)
            df.to_json(json_path, orient="records", indent=2)
            saved += 1
            print(f"    Saved: {os.path.basename(csv_path)}")

        except Exception as e:
            print(f"  [warn] Could not save table {tbl_index}: {e}")

    print(f"  Tables done → {tables_dir}  "
          f"({saved} saved, {skipped_hf} header/footer skipped)")
    return saved


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not os.path.exists(INPUT_PDF):
        print(f"Error: File not found at {INPUT_PDF}")
        return

    setup_directories()

    device = detect_device()
    print(f"Compute device: {device}")

    converter = build_converter(device)

    print("Parsing document structure (OCR + layout + tables)...")
    try:
        result = converter.convert(INPUT_PDF)
        doc = result.document

        print("\nExporting outputs:")
        save_markdown(doc, OUTPUT_MD)
        save_figures(doc, IMAGES_DIR)
        save_tables(doc, TABLES_DIR)

        print("\nAll done! Output structure:")
        print(f"  {OUTPUT_DIR}")
        print(f"  ├── output.md          ← markdown (headers/footers stripped)")
        print(f"  ├── images/            ← figures named from document captions")
        print(f"  └── tables/            ← tables named from document captions (CSV + JSON)")

    except Exception as e:
        print(f"Parsing failed: {e}")
        raise


if __name__ == "__main__":
    main()