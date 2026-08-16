from decimal import Decimal
from typing import Unpack

from src.dtos.cet_response_calculate_dto import CetResponseCalculateDto

class CetResponseCalculateDtoStub:
    def entity(self, **partial: Unpack[CetResponseCalculateDto]) -> CetResponseCalculateDto:
        entity_mock: CetResponseCalculateDto = {
            "principal_financiado": Decimal("10596.0700000"),
            "pmt": Decimal("402.4793410691311657794299916"),
            "valor_total_pago": Decimal("14489.25627848872196805947970"),
            "cet_mensal": Decimal("0.02159987048441704357694040418"),
            "cet_anual": Decimal("0.292319657271635223508178191")
        }

        return {**entity_mock, **partial}
