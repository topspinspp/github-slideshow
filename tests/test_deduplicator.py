import unittest
import os
import pandas as pd # For creating test .xlsx file
import sys

# Add the parent directory to sys.path to allow importing deduplicator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from deduplicator import (
    read_csv, read_txt, read_excel,
    deduplicate_data,
    get_column_indices,
    infer_file_type
)

class TestDeduplicator(unittest.TestCase):
    TEST_DATA_DIR = "tests" # Tests are expected to be run from the root directory
    SAMPLE_CSV_PATH = os.path.join(TEST_DATA_DIR, "sample.csv")
    SAMPLE_TXT_PATH = os.path.join(TEST_DATA_DIR, "sample.txt")
    SAMPLE_XLSX_PATH = os.path.join(TEST_DATA_DIR, "sample.xlsx")

    SAMPLE_DATA_LIST = [
        ["Name", "Email", "City", "Age"],
        ["Alice", "alice@example.com", "New York", "30"],
        ["Bob", "bob@example.com", "London", "25"],
        ["Alice", "alice@example.com", "Paris", "30"], # Duplicate Name and Email
        ["Charlie", "charlie@example.com", "New York", "35"],
        ["Bob", "bob_diff@example.com", "London", "25"], # Different Email for Bob
        ["David", "alice@example.com", "Berlin", "40"] # Same Email as Alice but different Name
    ]
    
    # For Excel, all data becomes string, so we need a string version for direct comparison
    SAMPLE_DATA_LIST_STR = [
        [str(item) for item in row] for row in SAMPLE_DATA_LIST
    ]


    def setUp(self):
        """Set up test files before each test."""
        # Create sample CSV
        with open(self.SAMPLE_CSV_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(self.SAMPLE_DATA_LIST)

        # Create sample TXT
        with open(self.SAMPLE_TXT_PATH, 'w') as f:
            for row in self.SAMPLE_DATA_LIST:
                f.write(",".join(map(str,row)) + "\n")

        # Create sample XLSX
        df = pd.DataFrame(self.SAMPLE_DATA_LIST[1:], columns=self.SAMPLE_DATA_LIST[0])
        df.to_excel(self.SAMPLE_XLSX_PATH, index=False)

    def tearDown(self):
        """Clean up test files after each test."""
        for path in [self.SAMPLE_CSV_PATH, self.SAMPLE_TXT_PATH, self.SAMPLE_XLSX_PATH]:
            if os.path.exists(path):
                os.remove(path)

    # --- Test File Reading ---
    def test_read_csv(self):
        data = read_csv(self.SAMPLE_CSV_PATH)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), len(self.SAMPLE_DATA_LIST))
        self.assertEqual(data, self.SAMPLE_DATA_LIST_STR) # CSV reader reads all as strings by default

    def test_read_txt(self):
        data = read_txt(self.SAMPLE_TXT_PATH, delimiter=',')
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), len(self.SAMPLE_DATA_LIST))
        self.assertEqual(data, self.SAMPLE_DATA_LIST_STR)

    def test_read_excel(self):
        # read_excel from deduplicator.py converts all read data to string by default now
        data = read_excel(self.SAMPLE_XLSX_PATH)
        self.assertIsInstance(data, list)
        # Pandas adds an index column if not specified, but our read_excel handles header and converts to list
        self.assertEqual(len(data), len(self.SAMPLE_DATA_LIST_STR))
        self.assertEqual(data, self.SAMPLE_DATA_LIST_STR)

    # --- Test infer_file_type ---
    def test_infer_file_type(self):
        self.assertEqual(infer_file_type("data.csv"), "csv")
        self.assertEqual(infer_file_type("data.txt"), "txt")
        self.assertEqual(infer_file_type("data.xlsx"), "excel")
        self.assertEqual(infer_file_type("data.xls"), "excel")
        self.assertEqual(infer_file_type("data.unknown", default_type='csv'), "csv")
        self.assertEqual(infer_file_type("data", default_type='txt'), "txt") # No extension
        self.assertEqual(infer_file_type("archive.tar.gz", default_type='csv'), "csv") # complex extension
        self.assertEqual(infer_file_type("UPPER.CSV"), "csv") # Test case insensitivity

    # --- Test get_column_indices ---
    HEADER = SAMPLE_DATA_LIST[0] # ["Name", "Email", "City", "Age"]

    def test_get_column_indices_by_name(self):
        self.assertEqual(get_column_indices(self.HEADER, "Name,Email"), [0, 1])
        self.assertEqual(get_column_indices(self.HEADER, "City"), [2])
        self.assertEqual(get_column_indices(self.HEADER, "age,name"), [3,0]) # test case-insensitivity

    def test_get_column_indices_by_index(self):
        self.assertEqual(get_column_indices(self.HEADER, "0,1"), [0, 1])
        self.assertEqual(get_column_indices(self.HEADER, "2"), [2])

    def test_get_column_indices_mixed(self):
        self.assertEqual(get_column_indices(self.HEADER, "Name,1,City,3"), [0, 1, 2, 3])

    def test_get_column_indices_invalid_name(self):
        with self.assertRaisesRegex(ValueError, "Column name 'NonExistent' not found"):
            get_column_indices(self.HEADER, "NonExistent")

    def test_get_column_indices_invalid_index(self):
        with self.assertRaisesRegex(ValueError, "Column index 7 is out of bounds"):
            get_column_indices(self.HEADER, "7")
        with self.assertRaisesRegex(ValueError, "Column index 4 is out of bounds"): # Exact boundary
            get_column_indices(self.HEADER, "4")


    def test_get_column_indices_empty_string(self):
        self.assertEqual(get_column_indices(self.HEADER, ""), [])
        self.assertEqual(get_column_indices(self.HEADER, "  "), []) # Test with whitespace

    # --- Test deduplicate_data ---
    # SAMPLE_DATA_LIST_STR is used as input because read functions return all strings
    
    def test_deduplicate_by_one_column_name(self):
        # Deduplicate by "Name" (index 0)
        # Expected: Alice (first), Bob (first), Charlie, David
        expected_data = [
            self.SAMPLE_DATA_LIST_STR[0], # Header
            self.SAMPLE_DATA_LIST_STR[1], # Alice
            self.SAMPLE_DATA_LIST_STR[2], # Bob
            self.SAMPLE_DATA_LIST_STR[4], # Charlie
            self.SAMPLE_DATA_LIST_STR[6]  # David
        ]
        result = deduplicate_data(self.SAMPLE_DATA_LIST_STR, [0])
        self.assertEqual(result, expected_data)

    def test_deduplicate_by_multiple_columns_name_email(self):
        # Deduplicate by "Name" (index 0) and "Email" (index 1)
        # Alice,alice@example.com is repeated (row 1 and 3). Second one should be removed.
        # Bob,bob@example.com (row 2)
        # Charlie,charlie@example.com (row 4)
        # Bob,bob_diff@example.com (row 5)
        # David,alice@example.com (row 6) - Different name, same email as Alice, should be kept
        expected_data = [
            self.SAMPLE_DATA_LIST_STR[0], # Header
            self.SAMPLE_DATA_LIST_STR[1], # Alice, alice@example.com
            self.SAMPLE_DATA_LIST_STR[2], # Bob, bob@example.com
            self.SAMPLE_DATA_LIST_STR[4], # Charlie, charlie@example.com
            self.SAMPLE_DATA_LIST_STR[5], # Bob, bob_diff@example.com
            self.SAMPLE_DATA_LIST_STR[6]  # David, alice@example.com
        ]
        result = deduplicate_data(self.SAMPLE_DATA_LIST_STR, [0, 1])
        self.assertEqual(result, expected_data)

    def test_deduplicate_no_duplicates_present(self):
        # Deduplicate by "Email" (index 1) and "City" (index 2)
        # No two rows have the same Email AND City in SAMPLE_DATA_LIST_STR
        # (Alice,NY), (Bob,Lon), (Alice,Paris), (Charlie,NY), (Bob_diff,Lon), (David,Berlin)
        # All rows should be kept.
        result = deduplicate_data(self.SAMPLE_DATA_LIST_STR, [1, 2])
        self.assertEqual(result, self.SAMPLE_DATA_LIST_STR)

    def test_deduplicate_all_rows_are_duplicates_criteria(self):
        # Create data where all rows are duplicates based on a specific column
        data = [
            ["Name", "Status"],
            ["TaskA", "Open"],
            ["TaskB", "Open"],
            ["TaskC", "Open"],
        ]
        expected_data = [
            ["Name", "Status"],
            ["TaskA", "Open"],
        ]
        result = deduplicate_data(data, [1]) # Deduplicate by "Status"
        self.assertEqual(result, expected_data)

    def test_deduplicate_empty_data(self):
        self.assertEqual(deduplicate_data([], []), [])
        self.assertEqual(deduplicate_data([self.HEADER], []), [self.HEADER])

    def test_deduplicate_empty_group_by_cols(self):
        # Deduplicate on all columns. Row 3 ("Alice", "alice@example.com", "Paris", "30")
        # is different from row 1 ("Alice", "alice@example.com", "New York", "30") by "City"
        # So, all rows in SAMPLE_DATA_LIST_STR are unique if all columns are considered.
        # However, our read_csv/txt/excel converts everything to string. Let's check.
        # The provided SAMPLE_DATA_LIST has row 1 and 3 which are:
        # ["Alice", "alice@example.com", "New York", "30"],
        # ["Alice", "alice@example.com", "Paris", "30"],
        # These differ by City, so they are unique when comparing all columns.
        # Let's create a specific case for this test.
        data_with_full_duplicates = [
            ["Name", "Email", "City", "Age"],
            ["Alice", "alice@example.com", "New York", "30"],
            ["Bob", "bob@example.com", "London", "25"],
            ["Alice", "alice@example.com", "New York", "30"], # Exact duplicate of row 1
            ["Charlie", "charlie@example.com", "New York", "35"],
        ]
        expected_data = [
            data_with_full_duplicates[0],
            data_with_full_duplicates[1],
            data_with_full_duplicates[2],
            data_with_full_duplicates[4],
        ]
        result = deduplicate_data(data_with_full_duplicates, []) # Empty list for group_by_column_indices
        self.assertEqual(result, expected_data)

if __name__ == '__main__':
    # Need to import csv for setUp, this is fine as it's part of test script
    import csv 
    unittest.main()
