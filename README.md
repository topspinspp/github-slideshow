# Data Deduplication Script

## Overview

This script provides a command-line utility to read data from various file formats (CSV, TXT, Excel), identify and remove duplicate rows based on user-specified columns, and then write the unique rows to an output file. It is designed to be efficient for potentially large datasets.

## Features

*   **Versatile File Support:** Reads and writes CSV, TXT, and Excel (`.xls`, `.xlsx`) files.
*   **Flexible Deduplication:** Allows deduplication based on one or more columns, specified either by column name or by zero-based index.
*   **Command-Line Interface:** Easy-to-use CLI for specifying input/output files, target columns, and other options.
*   **Automatic File Type Inference:** Intelligently determines file types from extensions, but also allows manual override.
*   **Custom Delimiters:** Supports custom delimiters for both input and output TXT files.

## Dependencies

To use this script, you'll need:

*   **Python 3.x**
*   **`pandas` library:** Required for Excel file support and efficient data handling.
    *   Install using pip: `pip install pandas`
*   **`openpyxl` library:** Required by pandas for reading and writing modern Excel files (`.xlsx`).
    *   Install using pip: `pip install openpyxl`
*   **`xlrd` library:** Required by pandas for reading older Excel files (`.xls`).
    *   Install using pip: `pip install xlrd`

## Usage (Command-Line Interface)

The script is run from the command line using the following basic structure:

```bash
python deduplicator.py <input_file> <output_file> <group_by_columns> [options]
```

### Required Arguments:

*   **`input_file`**: Path to the source data file (e.g., `data.csv`, `report.xlsx`).
*   **`output_file`**: Path where the deduplicated data will be saved (e.g., `unique_data.csv`, `processed_report.txt`).
*   **`group_by_columns`**: A comma-separated string of column names or zero-based column indices to use for identifying duplicates.
    *   Example using column names: `"Name,Email Address"`
    *   Example using column indices: `"0,2"` (for the first and third columns)
    *   To deduplicate based on the content of **all columns**, provide an empty string: `""`

### Optional Arguments (Options):

*   `--file_type {csv,txt,excel}`: Manually specify the type of the input file if it cannot be inferred from the extension or if the extension is ambiguous.
*   `--output_file_type {csv,txt,excel}`: Manually specify the type of the output file. If the output file extension is ambiguous or missing, it defaults to CSV.
*   `--delimiter DELIMITER`: Specify the delimiter character used in TXT input files. (Default: `,`)
*   `--output_delimiter DELIMITER`: Specify the delimiter character to use for TXT output files. (Default: `,`)
*   `--help, -h`: Show the help message with all available options and exit.

### Examples:

1.  **Deduplicating a CSV file by an 'ID' column:**
    ```bash
    python deduplicator.py input.csv output.csv "ID"
    ```

2.  **Deduplicating an Excel file based on the first two columns (indices 0 and 1) and saving the output as a TXT file with tab delimiters:**
    ```bash
    python deduplicator.py data.xlsx results.txt "0,1" --output_file_type txt --output_delimiter "\t"
    ```
    *(Note: `\t` might need to be entered as `$'\\t'` in some shells or passed directly as a tab character if your shell supports it).*

3.  **Deduplicating a pipe-delimited TXT file (`|`) by 'TransactionID' and 'Date' columns, saving as CSV:**
    ```bash
    python deduplicator.py transactions.txt unique_transactions.csv "TransactionID,Date" --delimiter "|"
    ```
4.  **Deduplicating a CSV file based on all columns:**
    ```bash
    python deduplicator.py full_log.csv unique_log_entries.csv ""
    ```

## How it Works (Briefly)

The script operates by:

1.  Reading the header row from the input file to understand column names and structure.
2.  Iterating through the data rows. For each row, it constructs a key based on the values in the user-specified `group_by_columns`.
3.  It maintains a set of unique keys encountered so far.
4.  If a key for a row is new, the row is considered unique and is kept for the output. If the key has been seen before, the row is considered a duplicate and is discarded.
5.  The script writes out the header and only the first occurrence of each unique combination of values in the specified columns.
6.  While `pandas` is used for reading (especially Excel files, which might involve reading data in chunks depending on file size and pandas' internal mechanisms), the core deduplication logic processes rows one by one after they are loaded, which helps in managing memory usage for the core task.

## Running Tests

The script includes a suite of unit tests to ensure its functionality. To run the tests:

1.  Navigate to the root directory of the script.
2.  Execute the tests using one of the following commands:
    ```bash
    python -m unittest tests.test_deduplicator
    ```
    or
    ```bash
    python tests/test_deduplicator.py
    ```

This will run all defined test cases and report their status. Make sure you have the necessary dependencies installed, as some tests involve creating and reading test files in various formats.
