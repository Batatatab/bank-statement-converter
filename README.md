# Bank Statement to Excel Converter

A Python desktop application that converts bank statement PDFs into clean, organized Excel files.

I started building this project to make bank statement processing easier, especially when working with statements from different banks. The idea is simple: select a PDF, enter the required details, and get an Excel file with standardized transaction data and balance checks.

The application is designed with a classic Windows XP-inspired interface.

> **A note about the project:** I built this project by vibecoding with AI assistance. AI helped me write code, fix bugs, and figure out how different parts of the application work.

---

## Features

- **PDF to Excel:** Converts bank statement PDFs into a structured Excel workbook.
- **Standardized Format:** Organizes transactions into consistent columns, making statements easier to read and work with.
- **Balance Verification:** Compares transaction amounts with the balances printed in the original bank statement to help identify discrepancies.
- **Multiple Statement Formats:** The parser is being developed to handle different bank statement layouts and date formats.
- **Handles Opening and Closing Balances:** Uses the balances provided by the user and information available in the statement to help check whether the transactions add up correctly.
- **Cleaner Transaction Descriptions:** Attempts to keep unrelated text, footnotes, and other information at the end of a PDF out of the transaction data.
- **Excel Formatting:** Exports data into a formatted `.xlsx` file with readable columns and accounting-style number formats.
- **Windows Desktop App:** Uses Python and Tkinter, with an interface inspired by the classic Windows XP look.

---

## How It Works

The basic workflow is straightforward:

1. Select the bank statement PDF.
2. Enter the required details, such as the first transaction date and opening balance.
3. The application reads the PDF and extracts transaction information.
4. The extracted transactions are organized into a standardized format.
5. The application checks the balances and highlights discrepancies where its verification logic detects them.
6. Export the results to Excel for further review.

### Balance Verification

The main idea is to compare the transactions with the balances shown in the original statement.

For example, suppose the opening balance is ₹21,777.94.

| Transaction | Amount | Calculated Balance |
|---|---:|---:|
| Opening balance | — | ₹21,777.94 |
| Debit | ₹100.00 | ₹21,677.94 |
| Debit | ₹100.00 | ₹21,577.94 |

The application can compare the calculated balance with the balance printed in the PDF. Differences can then be flagged for review.

The aim is to make discrepancies easier to spot, not to replace manual verification or accounting review.

---

## Excel Output

The exported workbook is designed to contain columns such as:

| Column | Purpose |
|---|---|
| `Date` | Transaction date |
| `Ref No` | Transaction reference number |
| `Cheque No` | Cheque number, where available |
| `Particulars` | Transaction description |
| `Dr` | Debit amount |
| `Cr` | Credit amount |
| `Bal` | Running balance used by the application |
| `PDF Bal` | Balance extracted from the original PDF |
| `Status` | Verification result |
| `Warning` | Details of a detected discrepancy |

The exact data extracted depends on the layout and quality of the source PDF.

---

## Built With

- **Python** — Main programming language
- **Tkinter** — Desktop interface
- **pdfplumber** — Reading information from PDF files
- **pandas** — Organizing transaction data
- **openpyxl** — Creating and formatting Excel files
- **PyInstaller** — Packaging the application as a Windows executable
- **Inno Setup** — Creating a Windows installer

---

## Running the Project

### Requirements

- Python installed on your computer
- The project files
- The dependencies listed in `requirements.txt`

### Installation

Clone the repository:

```bash
git clone https://github.com/Batatatab/bank-statement-converter.git
cd bank-statement-converter
```

Create a virtual environment (optional but recommended):

```powershell
python -m venv venv
.\venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python app_gui.py
```

---

## Current Status

This project is a work in progress. Bank statements can differ significantly in their layout, and extracting every transaction correctly is one of the biggest challenges.

The application needs to be tested against different banks and statement formats. Extracted amounts, dates, and balances should always be checked against the original PDF, especially before using the output for accounting or reconciliation work.

Bug reports, suggestions, and contributions are welcome.

---

## AI-Assisted Development

This is a **vibecoded project**. I used AI tools extensively to help build the application, understand the code, troubleshoot errors, and improve the overall design.

I don't want to present it as perfect or claim that every feature works with every bank statement. There's still plenty to improve.

---
## Screenshots

### Main Application

![Bank Statement Converter - Main Window](screenshots/main-window.png)

### Conversion Process

![Conversion Process](screenshots/conversion-process.png)

### Excel Output

![Excel Output](screenshots/excel-output.png)


