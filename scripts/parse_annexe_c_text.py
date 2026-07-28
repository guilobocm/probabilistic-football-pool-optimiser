import pdfplumber
import json
import re
from pathlib import Path


def parse_pdf_text(pdf_path: Path):
    target_slots = ["A", "B", "D", "E", "G", "I", "K", "L"]
    annexe_c = {}

    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    # The table rows usually look like: 3A 3B 3C 3D 3E 3F 3G 3H
    # Let's find any line that has exactly 8 occurrences of 3X
    for line in text.split("\n"):
        matches = re.findall(r"3[A-L]", line)
        if len(matches) == 8:
            mapping = {f"1{target_slots[i]}": matches[i] for i in range(8)}
            thirds = [v[-1] for v in matches]
            if len(set(thirds)) == 8:
                key = "-".join(sorted(thirds))
                annexe_c[key] = mapping

    return annexe_c


if __name__ == "__main__":
    pdf_path = Path(__file__).resolve().parent.parent / "FWC26-regulations.pdf"

    annexe_c = parse_pdf_text(pdf_path)

    print(f"Found {len(annexe_c)} valid combinations via text extraction.")

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
        with open("annexe_c_debug_text.json", "w") as f:
            json.dump(annexe_c, f, indent=4)
