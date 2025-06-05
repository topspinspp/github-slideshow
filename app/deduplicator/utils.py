import os
import pandas as pd

def parse_txt_file(file_path: str) -> list[str]:
    """
    Parses a .txt file and returns its content as a list of lines.
    Tries UTF-8 and then GBK encoding.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            return [f"Error: Could not parse TXT file {os.path.basename(file_path)} with UTF-8 or GBK: {e}"]
    except FileNotFoundError:
        return [f"Error: File not found: {os.path.basename(file_path)}"]
    except Exception as e:
        return [f"Error: An unexpected error occurred while parsing {os.path.basename(file_path)}: {e}"]

def parse_csv_file(file_path: str, columns_to_use: list = None) -> list[str]:
    """
    Parses a CSV file, extracts text from specified or all columns,
    and returns a list of strings (one per row).
    Tries UTF-8 and then GBK encoding.
    """
    try:
        try:
            df = pd.read_csv(file_path, encoding='utf-8', keep_default_na=False)
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='gbk', keep_default_na=False)

        if df.empty:
            return [] # Return empty list for empty CSV file

        if columns_to_use:
            # Filter out columns not present in the DataFrame to prevent KeyErrors
            existing_columns = [col for col in columns_to_use if col in df.columns]
            if not existing_columns: # If no provided columns exist in the CSV
                 return [f"Error: None of the specified columns {columns_to_use} found in {os.path.basename(file_path)}."]
            df_subset = df[existing_columns]
        else:
            df_subset = df

        # Concatenate column values for each row, converting all to string
        return [' '.join(map(str, row)).strip() for row in df_subset.itertuples(index=False, name=None) if any(str(val).strip() for val in row)]

    except FileNotFoundError:
        return [f"Error: File not found: {os.path.basename(file_path)}"]
    except pd.errors.EmptyDataError:
        return [] # Return empty list for empty CSV file
    except Exception as e:
        return [f"Error: Could not parse CSV file {os.path.basename(file_path)}: {e}"]

def parse_excel_file(file_path: str, sheet_name=0, columns_to_use: list = None) -> list[str]:
    """
    Parses an Excel file, extracts text from specified or all columns from a given sheet,
    and returns a list of strings (one per row).
    """
    try:
        # For Excel, encoding is usually handled by the engine (openpyxl)
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', keep_default_na=False)

        if df.empty:
            return [] # Return empty list for empty Excel sheet

        if columns_to_use:
            existing_columns = [col for col in columns_to_use if col in df.columns]
            if not existing_columns:
                 return [f"Error: None of the specified columns {columns_to_use} found in sheet '{sheet_name}' of {os.path.basename(file_path)}."]
            df_subset = df[existing_columns]
        else:
            df_subset = df

        return [' '.join(map(str, row)).strip() for row in df_subset.itertuples(index=False, name=None) if any(str(val).strip() for val in row)]

    except FileNotFoundError:
        return [f"Error: File not found: {os.path.basename(file_path)}"]
    except pd.errors.EmptyDataError: # Though less common for Excel than CSV if sheet exists but is empty
        return []
    except Exception as e: # Catches errors like invalid sheet name from openpyxl/pandas
        return [f"Error: Could not parse Excel file {os.path.basename(file_path)} (sheet: {sheet_name}): {e}"]

def parse_file(file_path: str, sheet_name=None, columns_to_use: list = None) -> list[str]:
    """
    Parses a file based on its extension and returns its text content.
    Now returns a list of strings (lines/rows), or a list containing a single error string.
    """
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.txt':
        return parse_txt_file(file_path)
    elif file_extension == '.csv':
        return parse_csv_file(file_path, columns_to_use=columns_to_use)
    elif file_extension in ['.xls', '.xlsx']:
        # Pass sheet_name, default to 0 if None (which parse_excel_file already does)
        actual_sheet_name = sheet_name if sheet_name is not None else 0
        return parse_excel_file(file_path, sheet_name=actual_sheet_name, columns_to_use=columns_to_use)
    else:
        # This function used to handle .pdf and .docx; they are removed in this version.
        # If they need to be re-added, their parsing functions must also return list[str]
        # and handle errors by returning a list with a single error string.
        return [f"Error: Unsupported file type: {file_extension}"]
