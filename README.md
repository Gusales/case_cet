# 💰 Case CET

![Python Version](https://img.shields.io/badge/python-3.11%2B-blue?logo=python)
![Firebase Functions](https://img.shields.io/badge/Firebase_Functions-0.6%2B-FFCA28?logo=firebase)
![Architecture](https://img.shields.io/badge/Architecture-Serverless-orange)
![pytest](https://img.shields.io/badge/pytest-8.4-0A9EDC?logo=pytest)
![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen)
![Tests](https://img.shields.io/badge/tests-120%20passing-brightgreen)

> **Calculadora de Custo Efetivo Total para empréstimos pessoais.**
>
> Exposta como uma Firebase Cloud Function, a API recebe as condições de um empréstimo e devolve a parcela mensal pela Tabela Price, o valor total pago e o CET mensal e anual — este último resolvido numericamente por Newton-Raphson com fallback de bissecção. Toda a aritmética monetária usa `Decimal`, sem ponto flutuante em nenhum ponto do caminho.

---

## 📋 Sumário

- [Sobre o Projeto](#-sobre-o-projeto)
- [Arquitetura](#-arquitetura)
- [O que é calculado](#-o-que-é-calculado)
- [Tech Stack](#-tech-stack)
- [Como Executar](#-como-executar)
- [API](#-api)
- [Testes](#-testes)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Documentação](#-documentação)

---

## 💡 Sobre o Projeto

O **Case CET** resolve o problema de traduzir as condições nominais de um empréstimo no custo que o cliente realmente paga. A taxa anunciada no contrato não é o custo real: IOF e tarifa de cadastro são embutidos no saldo devedor, então o cliente paga parcelas calculadas sobre um valor maior do que o que recebeu na conta. O CET é a taxa que expõe essa diferença.

O sistema recebe cinco entradas, valida cada uma, monta o principal financiado, calcula a parcela pela Tabela Price e então busca numericamente a taxa que iguala o valor presente das parcelas ao valor efetivamente recebido.

O núcleo de cálculo é independente do meio de entrada: a mesma `src/` atende tanto a **Cloud Function** (`main.py`) quanto a **CLI** (`local-debug/main.py`), que continua disponível para uso local.

---

## 🏗 Arquitetura

```
Cliente HTTP                              Terminal
    │                                         │
    ▼                                         ▼
main.py                                local-debug/main.py
(Firebase Cloud Function)                    (CLI)
    │                                         │
    ├── HttpRequestValidator                  │
    │       └── Valida o JSON, converte       │
    │          percentuais e monta o DTO      │
    │                                         │
    └───────────────┬─────────────────────────┘
                    ▼
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
    ├── DecimalEncoder
    │       └── Serializa Decimal como string, preservando a precisão no JSON
    │
    └── Logger
            └── Prefixa cada mensagem com [Classe.método] via inspeção de stack
```

A validação é dividida em duas camadas de propósito: o `HttpRequestValidator` cuida do
transporte (JSON bem formado, campos presentes, tipos convertíveis) e o `UserInputValidator`
cuida da regra de negócio. É o que permite distinguir "JSON malformado" de "empréstimo
inválido" — e é também o que mantém o `UserInputValidator` reutilizado sem alteração entre a
CLI e a function.

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

- **Linguagem:** Python 3.11+
- **Serverless:** Firebase Cloud Functions (`firebase_functions`) — 2ª geração
- **Framework HTTP:** Flask (via `firebase-functions`)
- **Deploy:** Firebase CLI
- **Aritmética:** `decimal.Decimal` — precisão de 28 dígitos, sem ponto flutuante
- **Tipagem:** `TypedDict` para os DTOs, `Unpack` nos stubs de teste
- **Testes:** pytest 8.4 + pytest-cov 6.0

O núcleo em `src/` não depende de nada além da biblioteca padrão. O `firebase-functions` só é
exigido pelo `main.py`, então a CLI e a suíte de testes rodam sem ele.

---

## ⚡ Como Executar

### Pré-requisitos

- Python 3.11 ou superior
- [Firebase CLI](https://firebase.google.com/docs/cli) instalado (para o emulador e o deploy)
- Projeto Firebase criado

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

3. **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Execute localmente com o emulador:**
    ```bash
    firebase emulators:start --only functions
    ```

    A function fica disponível em
    `http://localhost:5001/<seu-projeto>/us-central1/lambda_handler`.

### Modo CLI

O mesmo núcleo de cálculo continua acessível pelo terminal, sem precisar de Firebase nem de
nenhuma dependência externa. A partir de `app/`:

```bash
python -m local-debug.main
```

> O `-m` é necessário: executar `python local-debug/main.py` coloca `local-debug/` no
> `sys.path` em vez de `app/`, e os imports de `src` falham.

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

## 🔌 API

`POST /` · `Content-Type: application/json`

### Requisição

| Campo | Tipo | Unidade |
| :--- | :--- | :--- |
| `valor_solicitado` | número ou string numérica | Reais (R$) |
| `taxa_juros_mensal` | número ou string numérica | Percentual (`2.5` = 2,5% a.m.) |
| `prazo` | inteiro | Meses |
| `iof` | número ou string numérica | Percentual (`0.38` = 0,38%) |
| `tarifa_cadastrada` | número ou string numérica | Reais (R$) |

```bash
curl -X POST https://us-central1-lambda-bedrock-analytics.cloudfunctions.net/calcula_cet \
  -H "Content-Type: application/json" \
  -d '{
        "valor_solicitado": 10000,
        "taxa_juros_mensal": 2.5,
        "prazo": 24,
        "iof": 0.38,
        "tarifa_cadastrada": 150
      }'
```

### Resposta — `200 OK`

```json
{
  "data": {
    "principal_financiado": "10188.0000",
    "pmt": "569.6398138287249351997965382",
    "valor_total_pago": "13671.35553188939844479511692",
    "cet_mensal": "0.02669314049967152600841711547",
    "cet_anual": "0.371790924403756286261650645"
  }
}
```

> **Por que os valores saem como string:** converter `Decimal` para `float` no JSON
> desfaria o motivo de o projeto inteiro usar `Decimal`. String é lossless — o consumidor
> decide como interpretar e arredondar.

### Erros

| Status | Quando | Exemplo de resposta |
| :---: | :--- | :--- |
| `400` | Corpo ausente ou JSON malformado | `{"message": "O corpo da requisição deve ser um JSON válido."}` |
| `400` | Campo obrigatório faltando | `{"message": "Campos obrigatórios ausentes: iof, tarifa_cadastrada."}` |
| `400` | Valor não numérico | `{"message": "Campo 'valor_solicitado' deve ser um número. Recebido: 'abc'."}` |
| `400` | Regra de negócio violada | `{"message": "Valor solicitado deve ser positivo."}` |
| `405` | Método diferente de `POST` | `{"message": "Método não permitido. Use POST."}` |
| `500` | Falha inesperada | `{"message": "Erro interno ao processar a requisição."}` |

O `204 No Content` é devolvido para o preflight `OPTIONS`. CORS está liberado para qualquer
origem (`Access-Control-Allow-Origin: *`).

---

## 🧪 Testes

Instale as dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

A suíte tem **120 testes** e **98% de cobertura** sobre `src/`. Todos os comandos abaixo rodam a partir de `app/`.

Os testes não dependem do `firebase-functions`: a lógica de parsing da requisição e de
serialização vive em `src/`, e o `main.py` é só o invólucro HTTP.

### Testes unitários

Cobrem cada service, validator e utilitário isoladamente — as fórmulas financeiras, os ramos de guarda do solver, as fronteiras do validator, o parsing do corpo HTTP, a serialização dos `Decimal` e a formatação do logger.

```bash
pytest -m unit
```

<sub>98 testes</sub>

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
    ├── main.py                                      # Cloud Function (entrypoint do Firebase)
    ├── local-debug/
    │   └── main.py                                  # CLI, para execução local
    ├── pytest.ini                                   # Config do pytest e markers
    ├── requirements.txt                             # Dependências da function
    ├── requirements-dev.txt                         # Dependências de teste
    ├── src/
    │   ├── dtos/
    │   │   ├── cet_request_calculate_dto.py         # Contrato de entrada (TypedDict)
    │   │   └── cet_response_calculate_dto.py        # Contrato de saída (TypedDict)
    │   ├── services/
    │   │   ├── cet_service.py                       # Principal, PMT e orquestração do CET
    │   │   └── cet_rate_solver.py                   # Newton-Raphson + fallback de bissecção
    │   ├── validators/
    │   │   ├── http_request_validator.py            # Parsing e conversão do corpo JSON
    │   │   └── user_input_validator.py              # Regras de negócio das entradas
    │   └── utils/
    │       ├── json_encoder.py                      # Serializa Decimal sem perder precisão
    │       └── logger.py                            # Logger colorido com prefixo [Classe.método]
    └── tests/
        ├── conftest.py                              # Fixtures das personas e comparadores
        ├── stubs/                                   # Stubs dos DTOs com override parcial
        ├── unit/                                    # Testes unitários (marker: unit)
        └── e2e/                                     # Cenários das personas (marker: e2e)
```

---

## 📚 Documentação

| Documento | O que contém |
| :--- | :--- |
| [**Desafio**](docs/DESAFIO.md) | O enunciado original da entrevista técnica: parâmetros, fórmula da Tabela Price, definição do CET anualizado e o caso de referência |
| [**Personas**](docs/PERSONAS.md) | Os dois casos de uso que guiam os testes — contexto, entradas, saídas esperadas e a derivação passo a passo de cada número, incluindo as alíquotas de IOF e a tarifa proporcional |
| [**Uso de IA no desenvolvimento**](docs/USO_DE_IA_NO_DESENVOLVIMENTO.md) | Registro de como ferramentas de IA foram usadas ao longo do projeto |

---

## 🎓 Contexto

Projeto desenvolvido como resposta à entrevista técnica descrita em [`docs/DESAFIO.md`](docs/DESAFIO.md), cujo objetivo é demonstrar o tratamento de cálculos financeiros, conversão de taxas, escolha de tipos adequados para moeda e tratamento de erros.

As decisões de modelagem — alíquotas de IOF por modalidade de crédito, tarifa proporcional ao valor solicitado e o que cada persona demonstra sobre o CET — estão documentadas e derivadas passo a passo em [`docs/PERSONAS.md`](docs/PERSONAS.md).
