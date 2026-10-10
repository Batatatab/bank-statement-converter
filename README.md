# Bank Statement Converter

A Python-based desktop application that converts Indian bank statement PDFs into a standardized Excel format.

The tool is designed to extract transaction details from bank statements with different layouts and organize them into a consistent structure for accounting, bookkeeping, and further financial analysis.

## Features

- **PDF to Excel conversion:** Converts bank statement PDFs into structured Excel spreadsheets.
- **Standardized output:** Organizes transactions into columns such as Date, Reference Number, Cheque Number, Particulars, Debit, Credit, and Balance.
- **Multiple PDF layouts:** Uses table extraction and coordinate-based extraction techniques to handle different statement layouts.
- **Transaction date anchoring:** Allows the user to enter the first transaction date to help locate the starting point for extraction.
- **Balance verification:** Compares calculated running balances against balances extracted from the PDF where available.
- **Custom account information:** Optionally adds the account holder's name and account number to the output spreadsheet.
- **PDF password support:** Accepts a password for encrypted PDFs supported by the underlying PDF library.
- **Audit log:** Displays extraction progress, validation results, and warnings.
- **Desktop GUI:** Provides a graphical interface for selecting input PDFs and output Excel files.
- 
AI-Assisted Development

This project was developed with significant assistance from AI tools, including code generation, debugging, and implementation guidance. I am learning programming while building this tool, and AI has been an important part of the development process.

The project is still evolving, and the code and extraction logic require ongoing testing, review, and improvement. Contributions, bug reports, and suggestions are welcome.

## How It Works

1. Select a bank statement PDF.
2. Enter the first transaction date shown in the statement.
3. Optionally provide the opening balance and expected closing balance.
4. Choose where to save the Excel file.
5. Run the conversion.
6. Review the generated spreadsheet and any validation warnings.

The application extracts the available transaction data, standardizes it, and checks running balances where the required information is available.

## Balance Verification Logic

The converter uses user-provided inputs and running balance calculations to help verify extracted bank transactions.
"Annotated bank statement illustrating the extraction and balance verification logic" (docs/images/balance-verification-reference.png)

How it works:

- Inputs: First transaction date, opening balance, and expected closing balance.
- Extraction: Reads transaction dates, cheque numbers, particulars, debits, credits, and balances from the PDF.
- Calculation: Subtracts debits and adds credits to the previous balance.
- Verification: Compares calculated balances with the PDF balances and checks the final balance against the expected closing balance.

Missing values and discrepancies should be flagged for review rather than automatically marked as verified.

## Technology Stack

- Python
- Tkinter for the desktop interface
- pdfplumber for PDF text and table extraction
- pandas for structured transaction data
- openpyxl for Excel generation and formatting

## Intended Use

This tool is intended to reduce the manual effort involved in converting bank statements into a consistent format for accounting and financial workflows.

It may be useful for accountants, accounting students, bookkeepers, and anyone who regularly works with bank statement data.

## Limitations

Bank statement formats vary between banks and can change over time. Scanned PDFs, unusual table layouts, and OCR errors may affect extraction accuracy.

Always review the generated Excel file, particularly transaction amounts, debit/credit classification, running balances, and rows flagged with warnings, before using it for accounting or reconciliation purposes.

A successful export does not necessarily mean that every transaction has been extracted or verified correctly.

## Status

**Version:** v1.0.0 (Beta)

This project is under development. Testing across different banks and statement formats is ongoing, and extraction accuracy may vary.

## Disclaimer

This project is an independent utility and is not affiliated with or endorsed by any bank. Users are responsible for verifying the accuracy of the generated data before relying on it.
