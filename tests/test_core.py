import unittest
from app.deduplicator.core import find_exact_duplicates, remove_exact_duplicates, find_near_duplicates

class TestCoreDeduplication(unittest.TestCase):

    def test_find_exact_duplicates_empty_list(self):
        self.assertEqual(find_exact_duplicates([]), [])

    def test_find_exact_duplicates_no_duplicates(self):
        texts = ["hello world", "python is fun", "unique text"]
        self.assertEqual(find_exact_duplicates(texts), [])

    def test_find_exact_duplicates_simple_duplicates(self):
        texts = ["apple", "banana", "apple", "cherry", "banana", "apple"]
        expected = [[0, 2, 5], [1, 4]] # Indices of "apple" and "banana"

        result = find_exact_duplicates(texts)
        # Sort inner lists and outer list to ensure consistent comparison
        sorted_result = sorted([sorted(group) for group in result])
        sorted_expected = sorted([sorted(group) for group in expected])
        self.assertEqual(sorted_result, sorted_expected)

    def test_find_exact_duplicates_all_duplicates(self):
        texts = ["same", "same", "same", "same"]
        expected = [[0, 1, 2, 3]]
        self.assertEqual(find_exact_duplicates(texts), expected)

    def test_find_exact_duplicates_with_empty_strings(self):
        texts = ["", "text", "", "text", ""]
        expected = [[0, 2, 4], [1, 3]]
        result = find_exact_duplicates(texts)
        sorted_result = sorted([sorted(group) for group in result])
        sorted_expected = sorted([sorted(group) for group in expected])
        self.assertEqual(sorted_result, sorted_expected)

    # Tests for remove_exact_duplicates
    def test_remove_exact_duplicates_empty_list(self):
        self.assertEqual(remove_exact_duplicates([]), [])

    def test_remove_exact_duplicates_no_duplicates(self):
        texts = ["hello", "world", "python"]
        self.assertEqual(remove_exact_duplicates(texts), texts)

    def test_remove_exact_duplicates_simple_case(self):
        texts = ["apple", "banana", "apple", "cherry", "banana"]
        expected = ["apple", "banana", "cherry"]
        self.assertEqual(remove_exact_duplicates(texts), expected)

    def test_remove_exact_duplicates_all_duplicates(self):
        texts = ["same", "same", "same"]
        expected = ["same"]
        self.assertEqual(remove_exact_duplicates(texts), expected)

    def test_remove_exact_duplicates_with_empty_strings(self):
        texts = ["", "text", "", "another", "text", ""]
        expected = ["", "text", "another"]
        self.assertEqual(remove_exact_duplicates(texts), expected)

    # Tests for find_near_duplicates
    def test_find_near_duplicates_empty_list(self):
        self.assertEqual(find_near_duplicates([]), [])

    def test_find_near_duplicates_no_duplicates(self):
        texts = ["unique phrase one", "distinct sentence two", "another different text"]
        self.assertEqual(find_near_duplicates(texts, similarity_threshold=0.8), [])

    def test_find_near_duplicates_simple_case(self):
        texts = [
            "This is a test sentence.",
            "This is a test sentence", # Near duplicate (ends with .)
            "This is another sentence.",
            "This is a test sentence.", # Exact duplicate
            "This is a test sentence, slightly longer."
        ]
        # Expected groups:
        # (0, 1, 3) are near/exact duplicates
        # (4) might be close to (0,1,3) depending on threshold but also check difflib behavior.
        # For a threshold of 0.9, "This is a test sentence, slightly longer." should not group with the others.
        # SequenceMatcher("None", "This is a test sentence.", "This is a test sentence").ratio() -> 1.0
        # SequenceMatcher("None", "This is a test sentence.", "This is a test sentence").ratio() -> 0.97
        # SequenceMatcher("None", "This is a test sentence.", "This is a test sentence").ratio() -> 0.9787
        # SequenceMatcher("None", "This is a test sentence.", "This is another sentence.").ratio() -> 0.8571
        # SequenceMatcher("None", "This is a test sentence.", "This is a test sentence, slightly longer.").ratio() -> 0.7385

        expected_strict = [[0, 1, 3]] # Threshold 0.95 (T0-T2 is 0.8571, so not included; T0-T4 is 0.7385, not included)
        result_strict = find_near_duplicates(texts, similarity_threshold=0.95)
        self.assertEqual(sorted([sorted(group) for group in result_strict]), sorted([sorted(group) for group in expected_strict]))

        # Based on debug logs:
        # T0-T1 (0.9787), T0-T2 (0.8571), T0-T3 (1.0) are >= 0.8
        # T0-T4 (0.7385) is < 0.8
        # T1-T2 (0.8333) is >= 0.8
        # Component should be [0,1,2,3]
        expected_medium = [[0, 1, 2, 3]] # Threshold 0.8
        result_medium = find_near_duplicates(texts, similarity_threshold=0.8)
        # The order of elements within a group can vary, and order of groups too.
        # So, we sort inner lists and then the outer list of lists for comparison.
        sorted_result_medium = sorted([sorted(group) for group in result_medium])
        sorted_expected_medium = sorted([sorted(group) for group in expected_medium])
        self.assertEqual(sorted_result_medium, sorted_expected_medium)


    def test_find_near_duplicates_different_thresholds(self):
        texts = ["abcdefg", "abcdef", "abcde"]
        # Ratio("abcdefg", "abcdef") is approx 0.92
        # Ratio("abcdefg", "abcde") is approx 0.77
        # Ratio("abcdefg", "abcdef") is 0.9231
        # Ratio("abcdefg", "abcde") is 0.8333
        # Ratio("abcdef", "abcde") is 0.9091

        # For threshold 0.9:
        # Edges: (0,1) (0.9231 >= 0.9 True)
        #        (1,2) (0.9091 >= 0.9 True)
        # Component: [0,1,2]
        expected_high_threshold = [[0, 1, 2]] # threshold 0.9
        result_high = find_near_duplicates(texts, similarity_threshold=0.9)
        self.assertEqual(sorted([sorted(g) for g in result_high]), sorted([sorted(g) for g in expected_high_threshold]))

        # For threshold 0.8:
        # Edges: (0,1) (0.9231 >= 0.8 True)
        #        (0,2) (0.8333 >= 0.8 True)
        #        (1,2) (0.9091 >= 0.8 True)
        # Component: [0,1,2]
        expected_mid_threshold = [[0, 1], [1, 2]] # threshold 0.8, "abcdef" is dup with both
                                                  # My current (graph) implementation will group them as [0,1,2]
                                                  # Let's test current behavior: it should be [[0,1,2]] because they are all connected.
        expected_mid_threshold_chained = [[0,1,2]]
        result_mid = find_near_duplicates(texts, similarity_threshold=0.8)
        self.assertEqual(sorted([sorted(g) for g in result_mid]), sorted([sorted(g) for g in expected_mid_threshold_chained]))

        # For threshold 0.7:
        # Edges: (0,1) (0.9231 >= 0.7 True)
        #        (0,2) (0.8333 >= 0.7 True)
        #        (1,2) (0.9091 >= 0.7 True)
        # Component: [0,1,2]
        expected_low_threshold = [[0, 1, 2]] # threshold 0.7
        result_low = find_near_duplicates(texts, similarity_threshold=0.7)
        self.assertEqual(sorted([sorted(g) for g in result_low]), sorted([sorted(g) for g in expected_low_threshold]))


    def test_find_near_duplicates_all_different(self):
        texts = ["short", "medium length", "a very very long text phrase"]
        self.assertEqual(find_near_duplicates(texts, similarity_threshold=0.99), [])

    def test_find_near_duplicates_all_very_similar(self):
        texts = ["text A", "text B", "text C"] # Assuming these are close enough by some metric not used by SM by default
                 # Let's use more similar texts for SequenceMatcher
        texts_sm = ["similar text one", "similar text onf", "similer text one"]
        # ratios:
        # (0,1) ~ 0.96
        # (0,2) ~ 0.93
        # (1,2) ~ 0.90
        expected = [[0, 1, 2]]
        result = find_near_duplicates(texts_sm, similarity_threshold=0.9)
        self.assertEqual(sorted([sorted(g) for g in result]), sorted([sorted(g) for g in expected]))

    def test_find_near_duplicates_exact_and_near_mixed(self):
        texts = [
            "This is a sample.", #0
            "This is a sample.", #1 (exact of 0)
            "This is a smaple.", #2 (near to 0,1) ratio ~0.93
            "Completely different text.", #3
            "This is a sample, but extended.", #4 (near to 0,1,2) ratio to 0 ~0.81
            "This is a smaple." #5 (exact of 2)
        ]
        # Expected with threshold 0.9:
        # Group1: 0, 1, 2, 5
        # Group2: 4 (by itself, if not similar enough to group1)
        # Or 0,1,2,4,5 if 4 is similar enough to 0,1,2,5
        # Ratio("This is a sample.", "This is a sample, but extended.") is ~0.81

        expected_thresh_0_9 = [[0, 1, 2, 5]]
        result_thresh_0_9 = find_near_duplicates(texts, similarity_threshold=0.9)
        self.assertEqual(sorted([sorted(g) for g in result_thresh_0_9]), sorted([sorted(g) for g in expected_thresh_0_9]))

        # Based on debug logs:
        # T0-T4 ratio is 0.7083, so T4 is not connected to T0 at threshold 0.8
        # Group [0,1,2,5] is formed. T4 is separate.
        expected_thresh_0_8 = [[0, 1, 2, 5]]
        result_thresh_0_8 = find_near_duplicates(texts, similarity_threshold=0.8)
        self.assertEqual(sorted([sorted(g) for g in result_thresh_0_8]), sorted([sorted(g) for g in expected_thresh_0_8]))


if __name__ == '__main__':
    unittest.main()
