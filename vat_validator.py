"""
VAT Validator Module
Validates EU VAT numbers against the official VIES (VAT Information Exchange System) API.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from zeep import Client
from zeep.exceptions import Fault, TransportError

# VIES SOAP API endpoint
VIES_WSDL = "https://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl"

# VAT number format patterns by country
VAT_PATTERNS = {
    "AT": r"^U\d{8}$",           # Austria
    "BE": r"^[01]\d{9}$",        # Belgium
    "BG": r"^\d{9,10}$",         # Bulgaria
    "CY": r"^\d{8}[A-Z]$",       # Cyprus
    "CZ": r"^\d{8,10}$",         # Czech Republic
    "DE": r"^\d{9}$",            # Germany
    "DK": r"^\d{8}$",            # Denmark
    "EE": r"^\d{9}$",            # Estonia
    "EL": r"^\d{9}$",            # Greece
    "ES": r"^[A-Z0-9]\d{7}[A-Z0-9]$",  # Spain
    "FI": r"^\d{8}$",            # Finland
    "FR": r"^[A-Z0-9]{2}\d{9}$", # France
    "HR": r"^\d{11}$",           # Croatia
    "HU": r"^\d{8}$",            # Hungary
    "IE": r"^\d{7}[A-Z]{1,2}$|^\d[A-Z]\d{5}[A-Z]$",  # Ireland
    "IT": r"^\d{11}$",           # Italy
    "LT": r"^\d{9}$|^\d{12}$",   # Lithuania
    "LU": r"^\d{8}$",            # Luxembourg
    "LV": r"^\d{11}$",           # Latvia
    "MT": r"^\d{8}$",            # Malta
    "NL": r"^\d{9}B\d{2}$",      # Netherlands
    "PL": r"^\d{10}$",           # Poland
    "PT": r"^\d{9}$",            # Portugal
    "RO": r"^\d{2,10}$",         # Romania
    "SE": r"^\d{12}$",           # Sweden
    "SI": r"^\d{8}$",            # Slovenia
    "SK": r"^\d{10}$",           # Slovakia
}

EU_COUNTRIES = list(VAT_PATTERNS.keys())


@dataclass
class ValidationResult:
    """Result of a VAT validation check."""
    country_code: str
    vat_number: str
    is_valid: bool
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    request_date: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "country_code": self.country_code,
            "vat_number": self.vat_number,
            "is_valid": self.is_valid,
            "company_name": self.company_name or "",
            "company_address": self.company_address or "",
            "request_date": self.request_date or "",
            "error_message": self.error_message or "",
            "status": "Valid" if self.is_valid else "Invalid"
        }


class VATValidator:
    """Validates EU VAT numbers using the VIES SOAP API."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy initialization of SOAP client."""
        if self._client is None:
            self._client = Client(VIES_WSDL)
        return self._client

    def clean_vat_number(self, vat_number: str) -> str:
        """Remove spaces, dots, and dashes from VAT number."""
        return re.sub(r"[\s.\-]", "", vat_number.upper())

    def validate_format(self, country_code: str, vat_number: str) -> bool:
        """Check if VAT number matches the expected format for the country."""
        country_code = country_code.upper()
        if country_code not in VAT_PATTERNS:
            return False

        pattern = VAT_PATTERNS[country_code]
        return bool(re.match(pattern, vat_number))

    def validate(self, country_code: str, vat_number: str) -> ValidationResult:
        """
        Validate a VAT number against the VIES API.

        Args:
            country_code: Two-letter EU country code (e.g., 'NL', 'DE')
            vat_number: VAT number without country prefix

        Returns:
            ValidationResult with validation status and company details
        """
        country_code = country_code.upper().strip()
        vat_number = self.clean_vat_number(vat_number)
        request_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check if country is valid EU member
        if country_code not in EU_COUNTRIES:
            return ValidationResult(
                country_code=country_code,
                vat_number=vat_number,
                is_valid=False,
                request_date=request_date,
                error_message=f"Invalid country code: {country_code}. Must be EU member state."
            )

        # Validate format first (optional - VIES will also reject invalid formats)
        if not self.validate_format(country_code, vat_number):
            # Still try VIES API - format patterns might not be complete
            pass

        try:
            # Call VIES API
            response = self.client.service.checkVat(
                countryCode=country_code,
                vatNumber=vat_number
            )

            return ValidationResult(
                country_code=country_code,
                vat_number=vat_number,
                is_valid=response.valid,
                company_name=response.name if response.name != "---" else None,
                company_address=response.address if response.address != "---" else None,
                request_date=request_date
            )

        except Fault as e:
            # SOAP fault - usually means invalid VAT number
            return ValidationResult(
                country_code=country_code,
                vat_number=vat_number,
                is_valid=False,
                request_date=request_date,
                error_message=f"VIES error: {str(e)}"
            )

        except TransportError as e:
            # Network or service unavailable
            return ValidationResult(
                country_code=country_code,
                vat_number=vat_number,
                is_valid=False,
                request_date=request_date,
                error_message=f"Service unavailable: {str(e)}"
            )

        except Exception as e:
            # Unexpected error
            return ValidationResult(
                country_code=country_code,
                vat_number=vat_number,
                is_valid=False,
                request_date=request_date,
                error_message=f"Unexpected error: {str(e)}"
            )


def validate_batch(records: list[tuple[str, str]]) -> list[ValidationResult]:
    """
    Validate a batch of VAT numbers.

    Args:
        records: List of (country_code, vat_number) tuples

    Returns:
        List of ValidationResult objects
    """
    validator = VATValidator()
    results = []

    for country_code, vat_number in records:
        result = validator.validate(country_code, vat_number)
        results.append(result)

    return results
