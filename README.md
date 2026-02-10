# EU VAT Validator

A Streamlit application that demonstrates automated VAT number validation against the official EU VIES system.

## Features

- **Batch Validation**: Upload a CSV file with multiple VAT numbers
- **Single Validation**: Validate individual VAT numbers
- **Real API**: Uses the official EU VIES SOAP API
- **Export Results**: Download validation results as CSV
- **Exception Report**: Highlights invalid records for review
- **Audit Trail**: Timestamps for all validations

## Installation

```bash
# Navigate to the app directory
cd vat_validator

# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Running the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Input Format

The CSV file should have two columns:
- Country code (2-letter EU code)
- VAT number (without country prefix)

Example:
```csv
%client-state%;%client-vat%
NL;860905494B01
FR;61420495178
FI;08974643
```

Supported delimiters: `;`, `,`, `\t`

## Supported Countries

AT, BE, BG, CY, CZ, DE, DK, EE, EL, ES, FI, FR, HR, HU, IE, IT, LT, LU, LV, MT, NL, PL, PT, RO, SE, SI, SK

## Sample Data

Use `sample_data.csv` for testing. It contains a mix of valid and invalid VAT numbers.

## Project Structure

```
vat_validator/
├── app.py              # Main Streamlit application
├── vat_validator.py    # VAT validation logic
├── requirements.txt    # Python dependencies
├── sample_data.csv     # Test data
└── README.md          # This file
```

## Technical Details

- **API**: EU VIES SOAP API (https://ec.europa.eu/taxation_customs/vies/)
- **Framework**: Streamlit
- **SOAP Client**: Zeep

## Business Case Context

This tool demonstrates the "Future State" automation proposed in the Yarado business case for EU VAT validation. It replaces the manual copy-paste workflow with:

1. Batch processing (all records at once)
2. Automated API calls to official EU system
3. Audit trail with timestamps
4. Exception reporting for human review
5. Exportable results

---

*Created for Yarado Business Case - EU VAT Validation Automation*
