# 💰 Case CET

![Python Version](https://img.shields.io/badge/python-3.11%2B-blue?logo=python)
![pytest](https://img.shields.io/badge/pytest-8.4-0A9EDC?logo=pytest)
![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen)
![Tests](https://img.shields.io/badge/tests-92%20passing-brightgreen)
![Dependencies](https://img.shields.io/badge/runtime_deps-zero-lightgrey)

> **Calculadora de Custo Efetivo Total para empréstimos pessoais.**
>
> Recebe as condições de um empréstimo pela linha de comando e devolve a parcela mensal pela Tabela Price, o valor total pago e o CET mensal e anual — este último resolvido numericamente por Newton-Raphson com fallback de bissecção. Toda a aritmética monetária usa `Decimal`, sem ponto flutuante em nenhum ponto do caminho.

---

## 📋 Sumário

- [Sobre o Projeto](#-sobre-o-projeto)
- [Arquitetura](#-arquitetura)
- [O que é calculado](#-o-que-é-calculado)
- [Tech Stack](#-tech-stack)
- [Como Executar](#-como-executar)
- [Testes](#-testes)
- [Estrutura do Projeto](#-estrutura-do-projeto)

---

## 💡 Sobre o Projeto

O **Case CET** resolve o problema de traduzir as condições nominais de um empréstimo no custo que o cliente realmente paga. A taxa anunciada no contrato não é o custo real: IOF e tarifa de cadastro são embutidos no saldo devedor, então o cliente paga parcelas calculadas sobre um valor maior do que o que recebeu na conta. O CET é a taxa que expõe essa diferença.

O sistema recebe cinco entradas, valida cada uma, monta o principal financiado, calcula a parcela pela Tabela Price e então busca numericamente a taxa que iguala o valor presente das parcelas ao valor efetivamente recebido.

---

## 🏗 Arquitetura

```
Entrada do usuário (CLI)
    │
    ▼
main.py
    │
    ├── UserInputValidator
    │       └── Recusa valor ≤ 0, taxa < 0, prazo ≤ 0, IOF ou tarifa negativos
    │
    ├── CetService
    │       ├── calcula_principal()  → ValorSolicitado + IOF + Tarifa
    │       ├── calcula_pmt()        → Tabela Price (com ramo para taxa zero)
    │       └── calcula_cet()        → orquestra o fluxo e capitaliza o CET anual
    │                 │
    │                 └── CetRateSolver
    │                         ├── f(r) e f'(r)      → função objetivo e derivada
    │                         ├── Newton-Raphson    → método principal
    │                         ├── _candidato_valido() → valida cada passo
    │                         └── Bissecção         → fallback quando o passo é inválido
    │
    └── Logger
            └── Prefixa cada mensagem com [Classe.método] via inspeção de stack
```

O `CetRateSolver` não reinicia a busca ao cair para a bissecção: ele aproveita o intervalo `[baixo, alto]` já reduzido pelas iterações anteriores.

---

## 📐 O que é Calculado

| Etapa | Fórmula | Observação |
| :--- | :--- | :--- |
| **Principal financiado** | `P = V + (V × IOF) + Tarifa` | O IOF incide só sobre o valor solicitado, não sobre a tarifa |
| **PMT (Tabela Price)** | `PMT = P × [ i(1+i)ⁿ / ((1+i)ⁿ − 1) ]` | Com taxa zero, cai para `P / n` sem divisão por zero |
| **Valor total pago** | `Total = PMT × n` | |
| **CET mensal** | `r` tal que `Σ PMT/(1+r)ᵏ = V`, para `k = 1..n` | Sem solução fechada — resolvido numericamente |
| **CET anual** | `CET_anual = (1 + r)¹² − 1` | Capitalização composta |

### O método numérico

A função objetivo `f(r) = Σ PMT/(1+r)ᵏ − V` é estritamente decrescente, o que garante raiz única no intervalo de busca `[0, 10]` (0% a 1000% ao mês). O solver valida os extremos antes de iterar e falha explicitamente se a raiz não estiver contida neles.

Cada passo de Newton-Raphson produz um candidato que só é aceito se estiver dentro do intervalo conhecido e mantiver `1 + r > 0`. Quando o candidato é rejeitado — derivada nula, passo que escapa do intervalo, `InvalidOperation` do `Decimal` — o solver aplica um passo de bissecção no lugar. Isso dá a velocidade de convergência de Newton no caso comum e a garantia de convergência da bissecção no caso ruim.

O retorno inclui metadados da execução (`iteracoes`, `usos_fallback`, `erro_final`), usados nos testes para verificar que o caminho da bissecção é de fato exercitado.

---

## 🚀 Tech Stack

- **Linguagem:** Python 3.11+ (desenvolvido em 3.14.6)
- **Aritmética:** `decimal.Decimal` — precisão de 28 dígitos, sem ponto flutuante
- **Tipagem:** `TypedDict` para os DTOs, `Unpack` nos stubs de teste
- **Testes:** pytest 8.4 + pytest-cov 6.0
- **Dependências de runtime:** nenhuma — só biblioteca padrão

---

## ⚡ Como Executar

### Pré-requisitos

- Python 3.11 ou superior

### Passo a Passo

1. **Clone o repositório:**
    ```bash
    git clone https://github.com/Gusales/case_cet.git
    cd case_cet/app
    ```

2. **Crie e ative o ambiente virtual:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate   # Linux/Mac
    .venv\Scripts\activate      # Windows
    ```

3. **Execute a aplicação:**
    ```bash
    python main.py
    ```

    _A aplicação não tem dependências de runtime. O `requirements-dev.txt` só é necessário para rodar os testes._

### Exemplo de execução

O programa pede as cinco entradas em sequência. Usando o caso de referência do desafio:

```
Valor solicitado: 10000
Taxa de juros mensal (%): 2.5
Prazo (meses): 24
IOF (%): 0.38
Tarifa cadastrada (R$): 150
```

**Resultado:**

```
INFO - [CetService.calcula_cet] - Cálculo do CET finalizado, retornando o resultado final.
INFO - Cálculo concluído com sucesso.
INFO - {
    'principal_financiado': Decimal('10188.0000'),
    'pmt':                  Decimal('569.6398138287249351997965382'),
    'valor_total_pago':     Decimal('13671.35553188939844479511692'),
    'cet_mensal':           Decimal('0.02669314049967152600841711547'),
    'cet_anual':            Decimal('0.371790924403756286261650645')
}
```

Ou seja: parcela de **R$ 569,64**, total pago de **R$ 13.671,36**, e um CET de **2,67% ao mês** / **37,18% ao ano** — contra os 2,5% ao mês contratados.

> **Nota:** taxas são informadas em **percentual** (`2.5` para 2,5%) e convertidas internamente para fração. Os logs saem em `stderr`; apenas os prompts vão para `stdout`.

---

## 🧪 Testes

Instale as dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

A suíte tem **92 testes** e **98% de cobertura** sobre `src/`. Todos os comandos abaixo rodam a partir de `app/`.

### Testes unitários

Cobrem cada service, validator e utilitário isoladamente — as fórmulas financeiras, os ramos de guarda do solver, as fronteiras do validator e a formatação do logger.

```bash
pytest -m unit
```

<sub>70 testes</sub>

### Testes e2e

Percorrem cenários completos de ponta a ponta, a partir das personas documentadas em [`docs/PERSONAS.md`](docs/PERSONAS.md): entradas reais de crédito rotativo e consignado, com as saídas conferidas contra a tabela do documento.

```bash
pytest -m e2e
```

<sub>22 testes</sub>

### Outros comandos

```bash
# tudo
pytest

# com relatório de cobertura no terminal
pytest --cov=src --cov-report=term-missing

# relatório HTML em htmlcov/index.html
pytest --cov=src --cov-report=html

# um arquivo ou um teste específico
pytest tests/unit/services/test_cet_rate_solver.py
pytest -k "fallback"

# para no primeiro erro
pytest -x
```

No Windows, sem ativar a venv, use `.venv\Scripts\python.exe -m pytest` no lugar de `pytest`.

---

## 📁 Estrutura do Projeto

```
case_cet/
├── docs/
│   ├── DESAFIO.md                                   # Enunciado da entrevista técnica
│   ├── PERSONAS.md                                  # Casos de uso, derivações e passo a passo
│   └── USO_DE_IA_NO_DESENVOLVIMENTO.md              # Registro do uso de IA no projeto
└── app/
    ├── main.py                                      # Entrypoint da CLI
    ├── pytest.ini                                   # Config do pytest e markers
    ├── requirements-dev.txt                         # Dependências de teste
    ├── src/
    │   ├── dtos/
    │   │   ├── cet_request_calculate_dto.py         # Contrato de entrada (TypedDict)
    │   │   └── cet_response_calculate_dto.py        # Contrato de saída (TypedDict)
    │   ├── services/
    │   │   ├── cet_service.py                       # Principal, PMT e orquestração do CET
    │   │   └── cet_rate_solver.py                   # Newton-Raphson + fallback de bissecção
    │   ├── validators/
    │   │   └── user_input_validator.py              # Validação das entradas do usuário
    │   └── utils/
    │       └── logger.py                            # Logger colorido com prefixo [Classe.método]
    └── tests/
        ├── conftest.py                              # Fixtures das personas e comparadores
        ├── stubs/                                   # Stubs dos DTOs com override parcial
        ├── unit/                                    # Testes unitários (marker: unit)
        └── e2e/                                     # Cenários das personas (marker: e2e)
```

---

## 🎓 Contexto

Projeto desenvolvido como resposta à entrevista técnica descrita em [`docs/DESAFIO.md`](docs/DESAFIO.md), cujo objetivo é demonstrar o tratamento de cálculos financeiros, conversão de taxas, escolha de tipos adequados para moeda e tratamento de erros.

As decisões de modelagem — alíquotas de IOF por modalidade de crédito, tarifa proporcional ao valor solicitado e o que cada persona demonstra sobre o CET — estão documentadas e derivadas passo a passo em [`docs/PERSONAS.md`](docs/PERSONAS.md).
