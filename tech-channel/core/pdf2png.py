"""Rasterize a PDF to one PNG per page at a given DPI (default 150 -> 2000x1125).

Usage: python core/pdf2png.py <input.pdf> <output_dir> [dpi]
"""
import os
import sys

import fitz  # PyMuPDF


def main() -> None:
    pdf, outdir = sys.argv[1], sys.argv[2]
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 150
    os.makedirs(outdir, exist_ok=True)
    doc = fitz.open(pdf)
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=dpi)
        pix.save(os.path.join(outdir, f"slide-{i:02d}.png"))
    print(f"{doc.page_count} PNG(s) @ {dpi}dpi ({pix.width}x{pix.height}) -> {outdir}")


if __name__ == "__main__":
    main()
