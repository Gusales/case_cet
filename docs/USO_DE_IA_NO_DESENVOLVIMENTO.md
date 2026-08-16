# Utilização da IA no Desenvolvimento do Desafio

Utilizei IA's (Claude, Claude Code, Claude Design e Google Gemini) como apoio em diferentes etapas do desenvolvimento do desafio técnico de cálculo de CET. Abaixo, resumo como cada etapa foi conduzida com esse suporte.

## Entendimento do Desafio

- Interpretei o markdown do desafio junto com as IA, revisando as entradas e saídas esperadas, a fórmula da Tabela Price e o conceito de CET
- Utilizei para pesquisar os conceitos matemáticos por trás da solução (juros compostos, valor presente, anuidades) e entender por que a taxa `r` do CET não tem solução algébrica fechada

## Implementação em Python

- Utilizei o Claude Code para criar a primeira versão da função de cálculo (PMT + CET), utilizando `Decimal` para evitar erros de ponto flutuante em valores monetários
- A IA escreveu, validou e realizou teste com os valores oficiais do desafio (R$ 10.000,00, 2,5% a.m., 24 meses) e validou o resultado
- Defini, com apoio da IA, as validações de input necessárias (valores negativos, taxa zero, prazo inválido, entre outras)

## Métodos Numéricos

- Utilizei o Claude.ai para definir as alternativas para encontrar a taxa `r` (Bissecção, Newton-Raphson, Secante, Método de Brent), comparando os trade-offs de cada uma
- Refatorei o código utilizando o Claude Code CLI ao longo do processo: extraí `calcular_principal` como função separada e, posteriormente, consolidei `f`, `f_linha` e a busca da raiz em uma classe (`CETSolver`)

## Personas e Casos de Uso

- Avaliei e ajustei três personas propostas, discutindo com a IA se fazia sentido aplicar o CET em cada uma
- Analisei como as características de cada persona (prazo, precisão exigida, robustez) se conectam à escolha do método numérico
- Gerei os markdowns de teste (entradas/saídas) das personas, posteriormente recalculados com base no projeto real

## Revisão do Projeto Desenvolvido

- Utilizei a IA para revisar o projeto completo (DTOs, Validators, Services, Logger, testes)
- Rodei a suíte de testes (90 casos, todos passando) para confirmar que tudo funcionava corretamente
- Usei essas informações reais para reescrever as seções de "Demonstração" e "Benefício" da apresentação

## Apresentação

- Escrevi, com apoio da IA, o texto dos slides (Dor / Demonstração / Benefício), ajustando o foco conforme necessário — saindo de um caso de teste específico para a capacidade geral da solução
- Recriei o markdown do desafio original e o markdown das personas como arquivos de referência
- Montei prompts estruturados para o Claude Design: um para criar a apresentação do zero (abertura, entrega, cronograma, personas) e outro para editá-la (renomeação de personas, inclusão de novos slides)

## Considerações Finais

Ao longo do processo, apliquei diversos ajustes e correções sobre o que a IA sugeriu — como preferir nomes de função mais precisos, evitar números de teste específicos na seção de "Benefício" e refinar a motivação real por trás das personas (relacionada à performance do solver, não apenas à didática). Esses ajustes moldaram a versão final da solução e do material de apresentação.