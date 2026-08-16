from decimal import Decimal, InvalidOperation

from src.utils.logger import Logger

class CetRateSolver:
    """
    Encapsula a busca da taxa r tal que:

        f(r) = Σ PMT/(1+r)^k - ValorSolicitado = 0   (k = 1..n)

    Estratégia: Newton-Raphson como método principal, validando cada
    candidato produzido; quando o candidato não é válido, um passo de
    Bissecção é usado no lugar, aproveitando o intervalo [baixo, alto]
    já reduzido até aquele ponto (não reinicia a busca do zero).
    """

    def __init__(
            self,
            pmt: Decimal,
            valor_solicitado: Decimal,
            prazo: int,
            tolerancia: Decimal = Decimal("0.0000001"),
            max_iteracoes: int = 100,
    ):
        self._logger = Logger(self.__class__)
        self.pmt = pmt
        self.valor_solicitado = valor_solicitado
        self.prazo = prazo
        self.tolerancia = tolerancia
        self.max_iteracoes = max_iteracoes

        self._logger.info(
            f"Solver instanciado com pmt={pmt}, valor_solicitado={valor_solicitado}, "
            f"prazo={prazo}, tolerancia={tolerancia} e max_iteracoes={max_iteracoes}"
        )

    def f(self, r: Decimal) -> Decimal:
        """f(r) = Σ PMT/(1+r)^k - ValorSolicitado, para k=1..n"""
        total = Decimal(0)
        for k in range(1, self.prazo + 1):
            total += self.pmt / ((1 + r) ** k)

        resultado = total - self.valor_solicitado
        self._logger.debug(f"f({r}) = {resultado}")
        return resultado

    def f_linha(self, r: Decimal) -> Decimal:
        """f'(r) = Σ -k * PMT / (1+r)^(k+1), para k=1..n"""
        total = Decimal(0)
        for k in range(1, self.prazo + 1):
            total += Decimal(-k) * self.pmt / ((1 + r) ** (k + 1))

        self._logger.debug(f"f'({r}) = {total}")
        return total

    def _candidato_valido(self, r_candidato, baixo: Decimal, alto: Decimal) -> bool:
        """
        Verifica se o candidato do Newton-Raphson pode ser aceito:
        - deve estar numa região onde 1+r > 0 (denominador válido)
        - deve permanecer dentro do intervalo conhecido da raiz
        """
        if r_candidato is None:
            self._logger.debug("Candidato rejeitado: não foi possível calcular o passo de Newton-Raphson.")
            return False
        if r_candidato <= Decimal("-1"):
            self._logger.debug(f"Candidato rejeitado: {r_candidato} deixaria (1 + r) menor ou igual a zero.")
            return False
        if r_candidato <= baixo or r_candidato >= alto:
            self._logger.debug(f"Candidato rejeitado: {r_candidato} saiu do intervalo garantido [{baixo}, {alto}].")
            return False

        self._logger.debug(f"Candidato aceito: {r_candidato} está dentro do intervalo [{baixo}, {alto}].")
        return True

    def resolver(self, chute_inicial: Decimal) -> dict:
        """
        Executa a busca e retorna um dicionário com o r encontrado e
        metadados da execução (iterações, quantas vezes o fallback
        foi usado, erro final).
        """
        self._logger.info(f"Iniciando a busca da taxa 'r' com chute_inicial={chute_inicial}")

        baixo = Decimal("0")
        alto = Decimal("10")  # 1000% a.m. -> limite bem folgado
        self._logger.info(f"Intervalo inicial de busca definido como [{baixo}, {alto}]")

        self._logger.info("Validando se a raiz está contida no intervalo inicial.")
        if self.f(baixo) <= 0:
            self._logger.error(f"Não há raiz no intervalo esperado: f({baixo}) <= 0.")
            raise ValueError("Não há raiz no intervalo esperado (f(0) <= 0).")
        if self.f(alto) >= 0:
            self._logger.error(f"Intervalo de busca insuficiente: f({alto}) >= 0.")
            raise ValueError("Intervalo de busca insuficiente (f(alto) >= 0).")
        self._logger.info("Intervalo inicial validado, a raiz está garantidamente dentro dele.")

        r_atual = chute_inicial
        iteracoes_realizadas = 0
        usos_fallback = 0
        convergiu = False

        for iteracao in range(1, self.max_iteracoes + 1):
            iteracoes_realizadas = iteracao
            valor_f = self.f(r_atual)
            self._logger.debug(f"Iteração {iteracao}: r_atual={r_atual}, f(r_atual)={valor_f}")

            if abs(valor_f) < self.tolerancia:
                convergiu = True
                self._logger.info(
                    f"Convergência atingida na iteração {iteracao}: "
                    f"|f(r)|={abs(valor_f)} é menor que a tolerância {self.tolerancia}"
                )
                break

            if valor_f > 0:
                baixo = r_atual
            else:
                alto = r_atual
            self._logger.debug(f"Iteração {iteracao}: intervalo reduzido para [{baixo}, {alto}]")

            candidato = None
            try:
                derivada = self.f_linha(r_atual)
                if derivada != 0:
                    candidato = r_atual - (valor_f / derivada)
                else:
                    self._logger.warning(f"Iteração {iteracao}: derivada igual a zero, o passo de Newton-Raphson não pôde ser calculado.")
            except (InvalidOperation, ZeroDivisionError) as erro:
                self._logger.warning(f"Iteração {iteracao}: falha ao calcular o passo de Newton-Raphson ({erro.__class__.__name__}).")
                candidato = None

            if self._candidato_valido(candidato, baixo, alto):
                r_atual = candidato
                self._logger.debug(f"Iteração {iteracao}: passo de Newton-Raphson aplicado, novo r={r_atual}")
            else:
                usos_fallback += 1
                r_atual = (baixo + alto) / 2
                self._logger.debug(f"Iteração {iteracao}: fallback de Bissecção aplicado, novo r={r_atual}")

        if not convergiu:
            self._logger.warning(
                f"A busca terminou sem convergir dentro do limite de {self.max_iteracoes} iterações, "
                f"o melhor r encontrado foi {r_atual}."
            )

        erro_final = abs(self.f(r_atual))
        self._logger.info(
            f"Busca finalizada: r={r_atual}, iteracoes={iteracoes_realizadas}, "
            f"usos_fallback={usos_fallback}, erro_final={erro_final}"
        )

        return {
            "r": r_atual,
            "iteracoes": iteracoes_realizadas,
            "usos_fallback": usos_fallback,
            "erro_final": erro_final,
        }
