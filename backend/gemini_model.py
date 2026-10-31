from pydantic import BaseModel
from typing import List, Optional

class GeminiInfo(BaseModel):
    treatment_name: str
    treatment_description: str
    tumor_factor: float