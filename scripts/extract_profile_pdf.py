from __future__ import annotations

import hashlib
from pathlib import Path

from pypdf import PdfReader

root = Path(__file__).resolve().parents[1]
out = root / "scripts" / "profile_pdf_text.txt"

pdfs = sorted(
    path for path in root.rglob("*.pdf")
    if ".git" not in path.parts
)
if not pdfs:
    raise SystemExit("No PDF files found in repository")

parts: list[str] = []
parts.append("UPLOADED PDF INVENTORY")
for pdf in pdfs:
    data = pdf.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    rel = pdf.relative_to(root).as_posix()
    reader = PdfReader(str(pdf))
    parts.append(f"\n===== FILE: {rel} =====")
    parts.append(f"SHA256: {digest}")
    parts.append(f"PAGES: {len(reader.pages)}")
    for index, page in enumerate(reader.pages, start=1):
        parts.append(f"\n----- {rel} · PDF PAGE {index} -----\n")
        parts.append(page.extract_text() or "")

out.write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")
print(f"Extracted {len(pdfs)} PDF file(s) to {out}")
for pdf in pdfs:
    print(pdf.relative_to(root).as_posix())
