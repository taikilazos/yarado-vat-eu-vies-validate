"""
EU VAT Validator - Streamlit Application
Demonstrates automated VAT validation for the Yarado Business Case.
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
from io import StringIO
from vat_validator import VATValidator, ValidationResult, EU_COUNTRIES

# Page configuration
st.set_page_config(
    page_title="EU VAT Validator",
    page_icon="🇪🇺",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748B;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #E2E8F0;
    }
    .valid-badge {
        background-color: #10B981;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: 500;
    }
    .invalid-badge {
        background-color: #EF4444;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "results" not in st.session_state:
        st.session_state.results = None
    if "processing_time" not in st.session_state:
        st.session_state.processing_time = None


def parse_csv(uploaded_file) -> pd.DataFrame:
    """Parse uploaded CSV file."""
    content = uploaded_file.getvalue().decode("utf-8")

    # Try different delimiters
    for delimiter in [";", ",", "\t"]:
        try:
            df = pd.read_csv(StringIO(content), delimiter=delimiter)
            if len(df.columns) >= 2:
                return df
        except:
            continue

    raise ValueError("Could not parse CSV file. Please check the format.")


def extract_records(df: pd.DataFrame, country_col: str, vat_col: str) -> tuple[list, list]:
    """
    Extract country codes and VAT numbers from dataframe using user-selected columns.
    Returns (records, errors) tuple.
    """
    records = []
    errors = []

    for idx, row in df.iterrows():
        country = str(row[country_col]).strip().upper()
        vat = str(row[vat_col]).strip()

        if country and vat and country != "NAN" and vat != "NAN":
            records.append((country, vat))
        else:
            errors.append(f"Row {idx + 1}: Invalid data")

    return records, errors


def guess_column(columns: list[str], keywords: list[str]) -> int:
    """Return the index of the first column whose name matches any keyword, else 0."""
    for i, col in enumerate(columns):
        col_lower = col.lower().replace("-", "").replace("_", "").replace(" ", "")
        if any(kw in col_lower for kw in keywords):
            return i
    return 0


def display_results(results: list[ValidationResult], processing_time: float):
    """Display validation results with metrics and table."""

    # Calculate metrics
    total = len(results)
    valid_count = sum(1 for r in results if r.is_valid)
    invalid_count = total - valid_count
    success_rate = (valid_count / total * 100) if total > 0 else 0

    # Metrics row
    st.markdown("### Results Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Records", total)
    with col2:
        st.metric("Valid", valid_count, delta=None)
    with col3:
        st.metric("Invalid", invalid_count, delta=None)
    with col4:
        st.metric("Processing Time", f"{processing_time:.2f}s")

    # Success rate progress bar
    st.markdown("#### Validation Success Rate")
    st.progress(success_rate / 100)
    st.caption(f"{success_rate:.1f}% of VAT numbers are valid")

    # Results table
    st.markdown("### Detailed Results")

    # Convert to DataFrame
    results_df = pd.DataFrame([r.to_dict() for r in results])

    # Rename columns for display
    display_df = results_df.rename(columns={
        "country_code": "Country",
        "vat_number": "VAT Number",
        "status": "Status",
        "company_name": "Company Name",
        "company_address": "Address",
        "request_date": "Validated At",
        "error_message": "Notes"
    })

    # Reorder columns
    column_order = ["Country", "VAT Number", "Status", "Company Name", "Address", "Validated At", "Notes"]
    display_df = display_df[[c for c in column_order if c in display_df.columns]]

    # Style the dataframe
    def highlight_status(val):
        if val == "Valid":
            return "background-color: #D1FAE5; color: #065F46"
        elif val == "Invalid":
            return "background-color: #FEE2E2; color: #991B1B"
        return ""

    styled_df = display_df.style.applymap(highlight_status, subset=["Status"])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # Download button
    st.markdown("### Export Results")

    csv_output = results_df.to_csv(index=False)
    st.download_button(
        label="Download Results as CSV",
        data=csv_output,
        file_name=f"vat_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

    # Show invalid records separately if any
    if invalid_count > 0:
        st.markdown("### Exception Report (Invalid Records)")
        invalid_df = display_df[display_df["Status"] == "Invalid"]
        st.dataframe(invalid_df, use_container_width=True, hide_index=True)


def main():
    """Main application."""
    init_session_state()

    # Header
    st.markdown('<p class="main-header">EU VAT Validator</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Automated VAT number validation against the official EU VIES system</p>', unsafe_allow_html=True)

    # Main content - tabs
    tab1, tab2 = st.tabs(["Batch Validation", "Single Validation"])

    with tab1:
        st.markdown("### Upload CSV File")
        st.caption("Upload a CSV file with country codes and VAT numbers")

        # Rate limiting settings
        with st.expander("⚙️ Advanced Settings (Rate Limiting)"):
            col1, col2 = st.columns(2)
            with col1:
                request_delay = st.slider(
                    "Delay between requests (seconds)",
                    min_value=0.1,
                    max_value=3.0,
                    value=0.5,
                    step=0.1,
                    help="Adds a delay between each VIES API request to avoid rate limiting"
                )
            with col2:
                max_retries = st.slider(
                    "Maximum retries",
                    min_value=1,
                    max_value=5,
                    value=3,
                    step=1,
                    help="Number of times to retry if a rate limit error occurs"
                )
            st.info("💡 If you encounter 'MS_MAX_CONCURRENT_REQ' errors, increase the delay or retries.")

        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=["csv", "txt"],
            help="File should contain columns for country code and VAT number"
        )

        if uploaded_file is not None:
            try:
                # Parse the file
                df = parse_csv(uploaded_file)

                st.markdown("#### Preview")
                st.dataframe(df.head(10), use_container_width=True, hide_index=True)
                st.caption(f"Showing first 10 of {len(df)} rows")

                # Let the user pick which columns to use
                st.markdown("#### Select Columns")
                col_left, col_right = st.columns(2)
                columns = list(df.columns)

                with col_left:
                    country_col = st.selectbox(
                        "Country code column",
                        options=columns,
                        index=guess_column(columns, ["country", "state", "land"]),
                    )
                with col_right:
                    vat_col = st.selectbox(
                        "VAT number column",
                        options=columns,
                        index=guess_column(columns, ["vat", "btw"]),
                    )

                # Extract records
                records, parse_errors = extract_records(df, country_col, vat_col)

                if parse_errors:
                    st.warning(f"Found {len(parse_errors)} rows with invalid data")

                st.markdown(f"**Ready to validate {len(records)} records**")

                # Validate button
                if st.button("Validate All", type="primary", use_container_width=True):
                    validator = VATValidator(request_delay=request_delay, max_retries=max_retries)
                    results = []

                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    start_time = time.time()

                    for i, (country, vat) in enumerate(records):
                        status_text.text(f"Validating {i + 1}/{len(records)}: {country} {vat}")
                        result = validator.validate(country, vat)
                        results.append(result)
                        progress_bar.progress((i + 1) / len(records))

                    processing_time = time.time() - start_time

                    status_text.empty()
                    progress_bar.empty()

                    # Store results in session state
                    st.session_state.results = results
                    st.session_state.processing_time = processing_time

                    st.success(f"Validation complete! Processed {len(results)} records in {processing_time:.2f} seconds")

                # Display results if available
                if st.session_state.results is not None:
                    display_results(st.session_state.results, st.session_state.processing_time)

            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

    with tab2:
        st.markdown("### Single VAT Validation")
        st.caption("Validate a single VAT number")

        col1, col2 = st.columns(2)

        with col1:
            country = st.selectbox(
                "Country",
                options=EU_COUNTRIES,
                index=EU_COUNTRIES.index("NL") if "NL" in EU_COUNTRIES else 0
            )

        with col2:
            vat_number = st.text_input(
                "VAT Number",
                placeholder="e.g., 860905494B01"
            )

        if st.button("Validate", type="primary"):
            if vat_number:
                with st.spinner("Validating..."):
                    validator = VATValidator()
                    start_time = time.time()
                    result = validator.validate(country, vat_number)
                    processing_time = time.time() - start_time

                # Display result
                if result.is_valid:
                    st.success(f"**Valid VAT Number**")

                    if result.company_name:
                        st.write(f"**Company:** {result.company_name}")
                    if result.company_address:
                        st.write(f"**Address:** {result.company_address}")
                else:
                    st.error(f"**Invalid VAT Number**")
                    if result.error_message:
                        st.write(f"**Reason:** {result.error_message}")

                st.caption(f"Validated at {result.request_date} ({processing_time:.2f}s)")
            else:
                st.warning("Please enter a VAT number")


if __name__ == "__main__":
    main()
