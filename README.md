# HSN Code Validation Agent

A Python-based agent for validating HSN (Harmonized System of Nomenclature) codes with hierarchical validation and detailed feedback.

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

1. Prepare your HSN data file (CSV or Excel) with columns:

   - `HSNCode`: The HSN codes
   - `Description`: Descriptions for each code

2. Run the agent:

```python
from agent import Agent

# Initialize agent
agent = Agent()

# Load your data
agent.load_data("your_data.csv")  # or .xlsx

# Validate a single code
result = agent.validate_agent("010110")
is_valid, conversation, (code, description) = result

# Validate multiple codes
results = agent.validate_agent(["010110", "020110", "999999"])
```

## Features

- Validates single or multiple HSN codes
- Checks number format, length, and hierarchy
- Provides detailed validation feedback
- Supports CSV and Excel files
- Includes performance optimizations and caching

## Example Output

```python
# Single code validation
result = agent.validate_agent("010110")
is_valid, conversation, (code, description) = result

print(f"Code: {code}")
print(f"Description: {description}")
print(f"Is Valid: {is_valid}")
print("\nValidation Steps:")
for message in conversation:
    print(message)
```

## Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

## License

MIT License
