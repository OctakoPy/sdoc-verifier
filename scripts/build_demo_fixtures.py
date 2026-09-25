from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1] / "demo" / "attachments"

FIELDS = [
    ("Shipper", "Northstar Paper Co."),
    ("Consignee", "Harbor Retail Ltd"),
    ("Notify Party", "Harbor Retail Ltd"),
    ("Port of Loading", "Port of Aster (AST)"),
    ("Port of Discharge", "Port of Birch (BIR)"),
    ("No. of Containers", "2 x 40'HC"),
    ("Gross Weight (KG)", "18,400 KG"),
]


def write_docx(path: Path, title: str, values: list[tuple[str, str]]) -> None:
    rows = "".join(
        f"<w:tr><w:tc><w:p><w:r><w:t>{escape(label)}</w:t></w:r></w:p></w:tc>"
        f"<w:tc><w:p><w:r><w:t>{escape(value)}</w:t></w:r></w:p></w:tc></w:tr>"
        for label, value in values
    )
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>{escape(title)}</w:t></w:r></w:p>
    <w:tbl>{rows}</w:tbl>
    <w:sectPr/>
  </w:body>
</w:document>""".encode()
    content_types = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    rels = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document)


def write_xlsx(path: Path, title: str, values: list[tuple[str, str]]) -> None:
    rows = [("A1", title), ("A2", "SHIPPING INSTRUCTION")]
    rows.extend(
        (f"A{index + 3}", f"{label}: {value}")
        for index, (label, value) in enumerate(values)
    )
    row_xml = [
        f'<row r="{int(cell[1:])}"><c r="{cell}" t="inlineStr"><is><t>{escape(value)}</t></is></c></row>'
        for cell, value in rows
    ]
    sheet = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>{"".join(row_xml)}</sheetData>
</worksheet>""".encode()
    workbook = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Demo" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    workbook_rels = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""
    content_types = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""
    rels = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)


def pdf_bytes(lines: list[str] | None) -> bytes:
    if lines is None:
        stream = b"q Q"
    else:
        commands = ["BT", "/F1 12 Tf", "72 740 Td", "14 TL"]
        for line in lines:
            escaped_line = (
                line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            )
            commands.append(f"({escaped_line}) Tj T*")
        commands.append("ET")
        stream = "\n".join(commands).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length "
        + str(len(stream)).encode()
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode())
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(output)


def main() -> None:
    mismatch_si = FIELDS.copy()
    mismatch_si[-1] = ("Gross Weight (KG)", "18,500 KG")
    mismatch_bl = FIELDS.copy()
    mismatch_bl[-2:] = [
        ("No. of Containers", "1 x 20'GP"),
        ("Gross Weight (KG)", "18,500 KG"),
    ]
    write_docx(ROOT / "si_mismatch.docx", "SHIPPING INSTRUCTION", mismatch_si)
    write_docx(ROOT / "bl_mismatch.docx", "BILL OF LADING (DRAFT)", mismatch_bl)
    write_xlsx(ROOT / "si_missing.xlsx", "NORTHSTAR PAPER CO.", FIELDS[:-1])
    native_si = ["SHIPPING INSTRUCTION"] + [
        f"{label}: {value}" for label, value in FIELDS
    ]
    native_bl = ["BILL OF LADING (DRAFT)"] + [
        f"{label}: {value}" for label, value in FIELDS
    ]
    (ROOT / "si_native.pdf").write_bytes(pdf_bytes(native_si))
    (ROOT / "bl_native.pdf").write_bytes(pdf_bytes(native_bl))
    (ROOT / "si_scan.pdf").write_bytes(pdf_bytes(None))
    (ROOT / "corrupt.pdf").write_bytes(b"not a valid pdf\n")


if __name__ == "__main__":
    main()
