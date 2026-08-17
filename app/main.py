import json

from http import HTTPStatus

from firebase_functions import https_fn
from flask import make_response

from src.services.cet_service import CetService
from src.utils.json_encoder import DecimalEncoder
from src.utils.logger import Logger
from src.validators.http_request_validator import HttpRequestValidator
from src.validators.user_input_validator import UserInputValidator

logger = Logger()

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS"
}


def _responde(corpo: dict, status: HTTPStatus):
    resposta = make_response(json.dumps(corpo, cls=DecimalEncoder), status)
    resposta.headers["Content-Type"] = "application/json"

    for header, valor in CORS_HEADERS.items():
        resposta.headers[header] = valor

    return resposta


@https_fn.on_request()
def lambda_handler(request: https_fn.Request) -> https_fn.Response:
    logger.info(f"[lambda_handler] - Request recebida: {request.method} {request.path}")

    if request.method == "OPTIONS":
        logger.info("[lambda_handler] - Preflight CORS respondido.")
        return _responde({}, HTTPStatus.NO_CONTENT)

    if request.method != "POST":
        logger.warning(f"[lambda_handler] - Método não permitido: {request.method}")
        return _responde(
            {"message": "Método não permitido. Use POST."},
            HTTPStatus.METHOD_NOT_ALLOWED
        )

    try:
        dados = HttpRequestValidator(
            body=request.get_json(silent=True)
        ).validate()

        UserInputValidator().validate(dados)

        resultado = CetService().calcula_cet(dados)

        logger.info("[lambda_handler] - Cálculo concluído com sucesso.")
        return _responde({"data": resultado}, HTTPStatus.OK)

    except ValueError as erro:
        # Cobre tanto o corpo malformado (HttpRequestValidator) quanto as regras
        # de negócio (UserInputValidator) — os dois são erro do cliente.
        logger.error(f"[lambda_handler] - Erro de validação: {erro}")
        return _responde({"message": str(erro)}, HTTPStatus.BAD_REQUEST)

    except Exception as erro:
        # O solver levanta ValueError quando não há raiz no intervalo, e isso já
        # é tratado acima. O que sobra aqui é falha inesperada — não vaza detalhe
        # interno na resposta, mas registra o traceback no log.
        logger.exception(f"[lambda_handler] - Falha inesperada ao calcular o CET: {erro}")
        return _responde(
            {"message": "Erro interno ao processar a requisição."},
            HTTPStatus.INTERNAL_SERVER_ERROR
        )
