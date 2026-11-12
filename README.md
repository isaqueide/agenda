# Monitoramento do Diário Oficial do Estado do Acre

Sistema automatizado desenvolvido em Python para consultar
o Diário Oficial do Estado do Acre, pesquisar nomes e enviar
notificações de ocorrências encontradas pelo Telegram.

A execução é realizada pelo GitHub Actions, sem necessidade
de servidor próprio ou VPS.

## 1. Funcionalidades

- Download automático do PDF.
- Validação da integridade do documento.
- Cálculo de hash SHA-256.
- Extração de texto com PyMuPDF.
- OCR com Tesseract.
- Pesquisa de nomes completos.
- Normalização de acentos.
- Pesquisa sem distinção entre maiúsculas e minúsculas.
- Identificação das páginas.
- Preservação do contexto.
- Notificações pelo Telegram.
- Controle de notificações duplicadas.
- Histórico persistente.
- Logs de execução.
- Testes automatizados.

## 2. Requisitos

- Python 3.12 ou superior.
- Git.
- Conta no GitHub.
- Bot criado no Telegram.
- Repositório GitHub.
- Tesseract OCR para documentos digitalizados.

## 3. Estrutura do projeto

```text
monitor-diario-oficial/
├── .github/
│   └── workflows/
│       └── monitoramento.yml
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── downloader.py
│   ├── history.py
│   ├── main.py
│   ├── name_search.py
│   ├── pdf_processor.py
│   └── telegram_bot.py
├── tests/
│   ├── conftest.py
│   ├── test_name_search.py
│   ├── test_pdf_processor.py
│   └── test_telegram_bot.py
├── state/
│   └── history.json
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt