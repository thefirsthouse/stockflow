import random
from typing import Optional


class SKUGenerator:
    def __init__(self):
        pass


    def generate_sku(self, brand: str, model: str, color: Optional[str] = None) -> str:
        """
        Generate a SKU based on brand, model, and optional color.
        The SKU format is: BRAND-MODEL-COLOR-RANDOMNUMBER
        """
        brand_part = brand.upper().replace(" ", "")
        model_part = model.upper().replace(" ", "")
        color_part = color.upper().replace(" ", "") if color else ""
        random_number = random.randint(1000, 9999)
        return f"{brand_part}-{model_part}-{color_part}-{random_number}"
