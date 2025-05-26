import csv
import pandas as pd
import argparse
import os

# --- File Reading Functions ---
def read_csv(file_path):
    """Reads a CSV file and returns its content as a list of lists."""
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            return list(reader)
    except FileNotFoundError:
        print(f"Error: Input file not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading CSV file {file_path}: {e}")
        return []

def read_txt(file_path, delimiter=','):
    """Reads a TXT file and returns its content as a list of lists."""
    try:
        with open(file_path, 'r', encoding='utf-8') as txtfile:
            data = []
            for line in txtfile:
                line = line.strip()
                if line:
                    data.append(line.split(delimiter))
            return data
    except FileNotFoundError:
        print(f"Error: Input file not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading TXT file {file_path}: {e}")
        return []

def read_excel(file_path):
    """Reads an Excel file and returns its content as a list of lists (header first)."""
    try:
        df = pd.read_excel(file_path)
        header = [str(col) for col in df.columns.tolist()] # Ensure header items are strings
        data = df.astype(str).values.tolist()
        return [header] + data
    except FileNotFoundError:
        print(f"Error: Input file not found at {file_path}")
        return []
    except Exception as e:
        print(f"An error occurred while reading the Excel file: {e}")
        print("Please ensure pandas is installed and you have the necessary Excel engines (e.g., openpyxl for .xlsx, xlrd for .xls).")
        return []

# --- Data Processing Function ---
def deduplicate_data(data_with_header, group_by_column_indices):
    """Deduplicates rows based on specified column indices."""
    if not data_with_header:
        print("Warning: No data provided to deduplicate_data.")
        return []
    
    header = data_with_header[0]
    data_rows = data_with_header[1:]

    if not data_rows:
        print("Warning: No data rows found after header in deduplicate_data.")
        return [header]

    num_columns = len(header)
    if group_by_column_indices:
        for index in group_by_column_indices:
            if not (0 <= index < num_columns):
                # This error should ideally be caught by get_column_indices earlier
                raise ValueError(
                    f"Column index {index} is out of bounds. "
                    f"Data has {num_columns} columns (indices 0 to {num_columns - 1})."
                )
    
    unique_rows_set = set()
    deduplicated_data_rows = []

    for row in data_rows:
        if len(row) != num_columns:
            print(f"Warning: Skipping row with inconsistent column count: {row} (expected {num_columns}, got {len(row)})")
            continue

        if not group_by_column_indices:
            key_tuple = tuple(str(item) for item in row)
        else:
            try:
                key_tuple = tuple(str(row[index]) for index in group_by_column_indices)
            except IndexError:
                print(f"Warning: Skipping row due to IndexError (likely inconsistent columns or bad index after validation): {row}")
                continue
        
        if key_tuple not in unique_rows_set:
            unique_rows_set.add(key_tuple)
            deduplicated_data_rows.append(row)

    return [header] + deduplicated_data_rows

# --- File Writing Functions ---
def write_csv(file_path, data_with_header):
    """Writes data to a CSV file."""
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(data_with_header)
        print(f"Data successfully written to {file_path}")
    except IOError:
        print(f"Error: Could not write to CSV file at {file_path}. Check path and permissions.")
    except Exception as e:
        print(f"An unexpected error occurred while writing to CSV: {e}")

def write_txt(file_path, data_with_header, delimiter=','):
    """Writes data to a TXT file with a specified delimiter."""
    try:
        with open(file_path, 'w', encoding='utf-8') as txtfile:
            for row in data_with_header:
                txtfile.write(delimiter.join(map(str, row)) + '\n')
        print(f"Data successfully written to {file_path}")
    except IOError:
        print(f"Error: Could not write to TXT file at {file_path}. Check path and permissions.")
    except Exception as e:
        print(f"An unexpected error occurred while writing to TXT: {e}")

def write_excel(file_path, data_with_header):
    """Writes data to an Excel file (.xlsx)."""
    if not data_with_header:
        print("Warning: No data provided to write_excel. Creating an empty file.")
        df = pd.DataFrame()
    elif len(data_with_header) == 1:
        print("Warning: Only header provided to write_excel. Creating a file with only headers.")
        df = pd.DataFrame(columns=data_with_header[0])
    else:
        header = data_with_header[0]
        data_rows = data_with_header[1:]
        df = pd.DataFrame(data_rows, columns=header)
    
    try:
        df.to_excel(file_path, index=False)
        print(f"Data successfully written to {file_path}")
    except IOError:
        print(f"Error: Could not write to Excel file at {file_path}. Check path and permissions.")
    except Exception as e:
        print(f"An error occurred while writing the Excel file: {e}")
        print("Please ensure pandas and openpyxl (for .xlsx) are installed.")

# --- CLI Helper Functions ---
def infer_file_type(file_path, default_type='csv'):
    """Infers file type from extension. Defaults to 'csv'."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext == '.csv':
        return 'csv'
    elif ext == '.txt':
        return 'txt'
    elif ext in ['.xlsx', '.xls']:
        return 'excel'
    elif not ext: # No extension, use default for output
        return default_type 
    else: # Unknown extension
        print(f"Warning: Unknown file extension '{ext}'. Using default type '{default_type}'.")
        return default_type

def get_column_indices(header_row, group_by_columns_str):
    """Converts a comma-separated string of column names or indices to a list of integer indices."""
    indices = []
    column_identifiers = [col.strip() for col in group_by_columns_str.split(',')]
    
    if not column_identifiers or not group_by_columns_str:
        # This case means deduplicate on all columns, handled by passing empty list to deduplicate_data
        return []

    header_map = {name.lower(): i for i, name in enumerate(header_row)} # Case-insensitive mapping

    for identifier in column_identifiers:
        if identifier.isdigit():
            index = int(identifier)
            if not (0 <= index < len(header_row)):
                raise ValueError(f"Column index {index} is out of bounds. Header has {len(header_row)} columns.")
            indices.append(index)
        else:
            # Try case-insensitive match first
            idx = header_map.get(identifier.lower())
            if idx is not None:
                indices.append(idx)
            else: # If not found, try case-sensitive (though header_map is already lower)
                try:
                    indices.append(header_row.index(identifier))
                except ValueError:
                    raise ValueError(f"Column name '{identifier}' not found in header: {header_row}")
    return indices

# --- Main Execution Block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deduplicate rows in CSV, TXT, or Excel files.")
    parser.add_argument("input_file", help="Path to the input file.")
    parser.add_argument("output_file", help="Path to the output file.")
    parser.add_argument("group_by_columns", 
                        help="Comma-separated string of column names or zero-based column indices to group by. "
                             "If an empty string or only whitespace is provided, deduplication will be based on all columns.")
    parser.add_argument("--file_type", choices=['csv', 'txt', 'excel'], 
                        help="Type of the input file. Inferred from extension if not provided.")
    parser.add_argument("--output_file_type", choices=['csv', 'txt', 'excel'],
                        help="Type of the output file. Inferred from extension if not provided (defaults to CSV if ambiguous).")
    parser.add_argument("--delimiter", default=',', 
                        help="Delimiter for TXT input files (default: ',').")
    parser.add_argument("--output_delimiter", default=',',
                        help="Delimiter for TXT output files (default: ',').")

    args = parser.parse_args()

    # Determine input file type
    input_type = args.file_type if args.file_type else infer_file_type(args.input_file)

    # Read data
    data_with_header = []
    print(f"Reading input file: {args.input_file} (type: {input_type})")
    if input_type == 'csv':
        data_with_header = read_csv(args.input_file)
    elif input_type == 'txt':
        data_with_header = read_txt(args.input_file, delimiter=args.delimiter)
    elif input_type == 'excel':
        data_with_header = read_excel(args.input_file)
    else: # Should not happen if infer_file_type has a default
        print(f"Error: Unsupported input file type '{input_type}'.")
        exit(1)

    if not data_with_header:
        print("No data read from input file. Exiting.")
        exit(1)
    
    if len(data_with_header) < 1: # Check if there's at least a header
        print("Error: Data read from file is empty or does not contain a header row.")
        exit(1)

    header = data_with_header[0]
    
    # Get column indices for deduplication
    try:
        # Handle case where group_by_columns might be an empty string explicitly
        # to mean deduplicate on all columns.
        group_by_cols_str = args.group_by_columns.strip()
        if not group_by_cols_str:
            print("No specific columns provided for grouping; deduplication will be based on all columns.")
            column_indices_to_group_by = []
        else:
            column_indices_to_group_by = get_column_indices(header, group_by_cols_str)
            print(f"Deduplicating based on columns: {', '.join([header[i] for i in column_indices_to_group_by])}")

    except ValueError as e:
        print(f"Error processing group_by_columns: {e}")
        exit(1)

    # Deduplicate data
    print("Deduplicating data...")
    try:
        deduplicated_data = deduplicate_data(data_with_header, column_indices_to_group_by)
    except ValueError as e: # Should be caught by get_column_indices, but as a safeguard
        print(f"Error during deduplication: {e}")
        exit(1)

    if not deduplicated_data or len(deduplicated_data) <=1 and len(deduplicated_data[0]) == 0 : # Check if only header with no data or completely empty
        # Check if the header itself is empty, which means no data was actually processed
        if not deduplicated_data or not deduplicated_data[0]:
             print("No data left after deduplication (or initial data was empty/header-only). Output file will not be created.")
             exit(0)


    # Determine output file type
    output_type = args.output_file_type if args.output_file_type else infer_file_type(args.output_file, default_type='csv')
    
    # Write data
    print(f"Writing output file: {args.output_file} (type: {output_type})")
    if output_type == 'csv':
        write_csv(args.output_file, deduplicated_data)
    elif output_type == 'txt':
        write_txt(args.output_file, deduplicated_data, delimiter=args.output_delimiter)
    elif output_type == 'excel':
        write_excel(args.output_file, deduplicated_data)
    else: # Should not happen
        print(f"Error: Unsupported output file type '{output_type}'.")
        exit(1)
    
    print("Deduplication process completed.")
