import pdfplumber
from pathlib import Path
import json
import re

def dump_tables():
    pdf_path = Path(__file__).resolve().parent.parent / "FWC26-regulations.pdf"
    
    with pdfplumber.open(pdf_path) as pdf:
        # Pages 41 to 49 (indices 40 to 48)
        all_rows = []
        for i in range(40, 49):
            page = pdf.pages[i]
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Clean row
                    clean_row = [str(c).replace('\n', '').replace(' ', '').strip() if c else "" for c in row]
                    # Check if it has 8 elements matching 3X
                    valid_elements = [c for c in clean_row if re.fullmatch(r'3[A-L]', c)]
                    if len(valid_elements) == 8:
                        all_rows.append(valid_elements)
                    elif len(valid_elements) > 0:
                        # Print partially matched rows to see why they failed
                        print(f"Page {i+1} partial row: {clean_row}")

        print(f"Found {len(all_rows)} completely valid rows.")
        
        target_slots = ['A', 'B', 'D', 'E', 'G', 'I', 'K', 'L']
        annexe_c = {}
        for r in all_rows:
            mapping = {f"1{target_slots[i]}": r[i] for i in range(8)}
            thirds = [v[-1] for v in r]
            if len(set(thirds)) == 8:
                key = "-".join(sorted(thirds))
                annexe_c[key] = mapping
                
        print(f"Unique valid combinations: {len(annexe_c)}")
        
        if len(annexe_c) == 495:
            output_path = Path(__file__).resolve().parent.parent / "src" / "simulator" / "annexe_c.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(annexe_c, f, indent=4)
            print("Successfully updated annexe_c.json!")

if __name__ == "__main__":
    dump_tables()
