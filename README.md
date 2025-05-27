# HSN Code Validation Agent

A Google ADK based agent for validating HSN (Harmonized System of Nomenclature) codes with hierarchical validation and detailed feedback.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/bala-guhan/hsn-validation-agent.git
cd hsn-validation-agent
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

run the command

```bash
adk web
# or
adk run HSN_agent
```

## Features

- Validates single or multiple HSN codes
- Checks number format, length, and hierarchy
- Provides detailed validation feedback
- Supports CSV and Excel files
- Includes performance optimizations and caching

## Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

## License

MIT License
