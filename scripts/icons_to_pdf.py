# /// script
# requires-python = ">=3.14"
# dependencies = ["cairosvg"]
# ///
"""Convert the bundled SVG icons to PDF for LaTeX output.

pdflatex can't include SVG. Run with ``make icons`` when the icons change.
"""

from pathlib import Path

import cairocffi
import cairosvg.surface

ROOT = Path(__file__).parent.parent / "src" / "sphinx_eu_ai_label"
SVG_DIR = ROOT / "_static" / "eu_ai_label" / "icons"
PDF_DIR = ROOT / "latex" / "icons"


class PDF15Surface(cairocffi.PDFSurface):
    """pdflatex warns about including anything newer than PDF 1.5, and cairo defaults to 1.7.

    Also pins the creation date, so regenerating unchanged icons gives identical files.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.restrict_to_version(cairocffi.PDF_VERSION_1_5)
        self.set_metadata(cairocffi.PDF_METADATA_CREATE_DATE, "2026-01-01T00:00:00Z")


cairosvg.surface.PDFSurface.surface_class = PDF15Surface

PDF_DIR.mkdir(parents=True, exist_ok=True)
for svg in sorted(SVG_DIR.glob("*.svg")):
    cairosvg.svg2pdf(url=str(svg), write_to=str(PDF_DIR / f"{svg.stem}.pdf"))
