"""
Script to generate sample Excel rate files for the Manufacturing Cost Engine.
"""

import pandas as pd
from pathlib import Path

DB_DIR = Path(__file__).parent

def generate_materials():
    data = {
        "Material": ["E46", "CR4", "SS304", "SS316", "MS", "AL6061"],
        "Rate_per_kg": [60.3, 58.0, 210.0, 250.0, 55.0, 180.0],
    }
    df = pd.DataFrame(data)
    filepath = DB_DIR / "materials.xlsx"
    df.to_excel(filepath, index=False, engine="openpyxl")
    print(f"Created: {filepath}")

def generate_process_rates():
    data = {
        "Process": ["shearing", "blanking", "piercing", "forming", "bending", "welding", "machining", "cutting"],
        "Cost": [1.86, 1.60, 1.60, 1.60, 1.60, 6.50, 5.00, 2.50],
    }
    df = pd.DataFrame(data)
    filepath = DB_DIR / "process_rates.xlsx"
    df.to_excel(filepath, index=False, engine="openpyxl")
    print(f"Created: {filepath}")

def generate_coating_rates():
    data = {
        "Coating": [
            "powder_coating", "primer", "zinc_plating",
            "chrome_plating", "painting", "anodizing",
            "galvanizing", "heat_treatment",
        ],
        "Rate_per_m2": [102.04, 28.00, 17.50, 85.00, 45.00, 60.00, 35.00, 25.00],
    }
    df = pd.DataFrame(data)
    filepath = DB_DIR / "coating_rates.xlsx"
    df.to_excel(filepath, index=False, engine="openpyxl")
    print(f"Created: {filepath}")

if __name__ == "__main__":
    generate_materials()
    generate_process_rates()
    generate_coating_rates()
    print("All rate files generated successfully.")
