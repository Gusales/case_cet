from decimal import Decimal
from typing import TypedDict

class CetRequestCalculateDto(TypedDict):
    valor_solicitado: Decimal
    taxa_juros_mensal: Decimal
    prazo: int
    iof: Decimal
    tarifa_cadastrada: Decimal