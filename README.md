# Fintech
This is python driven project for integrating Tech in Finance domain.

## Fetch NIFTY 50 order book data

The repository now contains a helper script that downloads the latest market
depth (order book) snapshot for all NIFTY 50 constituents from NSE India and
saves it as a JSON file.

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Usage

```bash
python fetch_order_books.py --output data/nifty50_order_books.json
```

Use `--limit` to test a smaller subset of symbols while developing:

```bash
python fetch_order_books.py --limit 5
```
