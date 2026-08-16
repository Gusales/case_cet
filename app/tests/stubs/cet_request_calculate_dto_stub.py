from decimal import Decimal
from typing import Unpack

from src.dtos.cet_request_calculate_dto import CetRequestCalculateDto

class CetRequestCalculateDtoStub:
    def entity(self, **partial: Unpack[CetRequestCalculateDto]) -> CetRequestCalculateDto:
        entity_mock: CetRequestCalculateDto = {
            "prazo": 36,
            "tarifa_cadastrada": Decimal("150"),
            "iof": Decimal("0.0446070"),
            "taxa_juros_mensal": Decimal("0.018"),
            "valor_solicitado": Decimal("10000")
        }

        return {**entity_mock, **partial}
