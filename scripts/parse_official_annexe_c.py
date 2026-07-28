import pdfplumber
import json
import re
from pathlib import Path


def parse_pdf_annexe_c(pdf_path: Path):
    print(f"Parsing PDF: {pdf_path}")
    annexe_c = {}

    target_slots = ["A", "B", "D", "E", "G", "I", "K", "L"]
    slot_indices = None

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table in tables:
                if not table or not table[0]:
                    continue

                header = [
                    str(cell).replace("\n", "").strip() if cell else ""
                    for cell in table[0]
                ]

                current_slot_indices = {}
                for slot in target_slots:
                    expected_header = f"1{slot}"
                    for col_idx, col_name in enumerate(header):
                        if expected_header in col_name:
                            current_slot_indices[slot] = col_idx
                            break

                if len(current_slot_indices) == 8:
                    slot_indices = current_slot_indices
                    start_row = 1
                else:
                    if slot_indices is not None and len(table[0]) >= 8:
                        # Sometimes headers repeat, sometimes they don't.
                        # Let's check if the first row looks like data.
                        # We just join the row and see if it has a lot of 3X
                        row_str = "".join([str(c) for c in table[0] if c])
                        if re.search(r"3[A-L]", row_str):
                            start_row = 0
                        else:
                            start_row = 1
                    else:
                        continue

                if slot_indices is None:
                    continue

                # Parse the rows
                for row_idx, row in enumerate(table[start_row:]):
                    if not row or all(not cell for cell in row):
                        continue

                    mapping = {}
                    valid_row = True
                    for slot, col_idx in slot_indices.items():
                        if col_idx >= len(row):
                            valid_row = False
                            break
                        cell_val = (
                            str(row[col_idx]).replace("\n", "").replace(" ", "").strip()
                        )
                        m = re.search(r"3([A-L])", cell_val)
                        if m:
                            mapping[f"1{slot}"] = m.group(0)
                        else:
                            valid_row = False
                            break

                    if valid_row:
                        thirds = [v[-1] for v in mapping.values()]
                        if len(set(thirds)) == 8:
                            key = "-".join(sorted(thirds))
                            annexe_c[key] = mapping

    return annexe_c


if __name__ == "__main__":
    pdf_path = Path(__file__).resolve().parent.parent / "FWC26-regulations.pdf"

    annexe_c = parse_pdf_annexe_c(pdf_path)

    print(f"Found {len(annexe_c)} valid combinations in the PDF.")

    if len(annexe_c) == 495:
        print("Success: All 495 combinations extracted!")
        output_path = (
            Path(__file__).resolve().parent.parent
            / "src"
            / "simulator"
            / "annexe_c.json"
        )
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(annexe_c, f, indent=4)
        print(f"Saved to {output_path}")
    else:
        print("Error: Did not find exactly 495 combinations. Generating debug dump...")
        with open("annexe_c_debug.json", "w") as f:
            json.dump(annexe_c, f, indent=4)
