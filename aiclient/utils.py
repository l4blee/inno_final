from dataclasses import dataclass

@dataclass
class GPTResponse:
    content: str
    tokens_total: int
    tokens_completion: int

@dataclass
class DallEResponse:
    img_url: str
