from decimal import Decimal
from typing import TypedDict

class CetResponseCalculateDto(TypedDict):
    principal_financiado: Decimal
    pmt: Decimal
    valor_total_pago: Decimal
    cet_mensal: Decimal
    cet_anual: Decimal