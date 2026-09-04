import json
import unittest

from csv_profiler.__main__ import (
    infer_column_type,
    looks_like_date,
    profile_column,
    profile_csv,
    render_report,
)


def write_csv(tmpdir, content, name="data.csv"):
    path = f"{tmpdir}/{name}"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


class TypeInferenceTests(unittest.TestCase):
    def test_int_float_bool_date_string(self):
        self.assertEqual(infer_column_type(["1", "2", "-3"]), "integer")
        self.assertEqual(infer_column_type(["1.5", "2", "3.25"]), "float")
        self.assertEqual(infer_column_type(["true", "false"]), "boolean")
        self.assertEqual(infer_column_type(["2024-01-05", "1999-12-31"]), "date")
        self.assertEqual(infer_column_type(["abc", "123"]), "string")

    def test_empty_column(self):
        self.assertEqual(infer_column_type(["", "  "]), "empty")

    def test_date_bounds(self):
        self.assertTrue(looks_like_date("2024-02-29"))
        self.assertFalse(looks_like_date("2024-13-01"))
        self.assertFalse(looks_like_date("24-01-01"))


class ProfileColumnTests(unittest.TestCase):
    def test_numeric_stats(self):
        p = profile_column("age", ["10", "20", "30"])
        self.assertEqual(p.inferred_type, "integer")
        self.assertEqual(p.numeric["min"], 10)
        self.assertEqual(p.numeric["max"], 30)
        self.assertEqual(p.numeric["mean"], 20)
        self.assertEqual(p.numeric["sum"], 60)

    def test_nulls_and_uniques(self):
        p = profile_column("x", ["a", "a", "b", None, ""])
        self.assertEqual(p.total, 5)
        self.assertEqual(p.nulls, 1)
        self.assertEqual(p.empty_strings, 1)
        self.assertEqual(p.unique, 2)

    def test_top_values_ranked(self):
        p = profile_column("x", ["b", "a", "a", "b", "a", "c"])
        self.assertEqual(p.top_values[0], ["a", 3])
        self.assertEqual(p.top_values[1], ["b", 2])

    def test_string_lengths(self):
        p = profile_column("s", ["ab", "abcde"])
        self.assertEqual(p.min_length, 2)
        self.assertEqual(p.max_length, 5)


class ProfileCsvTests(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.tmp = tempfile.mkdtemp()

    def test_full_profile(self):
        path = write_csv(
            self.tmp,
            "name,age,joined\nada,36,2020-01-05\nbob,24,2021-06-30\ncyd,,2022-03-01\n",
        )
        result = profile_csv(path)
        self.assertEqual(result["rows"], 3)
        self.assertEqual(result["columns"], 3)
        by_name = {p["name"]: p for p in result["profiles"]}
        self.assertEqual(by_name["age"]["inferred_type"], "integer")
        self.assertEqual(by_name["age"]["empty_strings"], 1)
        self.assertEqual(by_name["joined"]["inferred_type"], "date")

    def test_missing_trailing_cell_is_null(self):
        path = write_csv(self.tmp, "a,b\n1,2\n3\n")
        result = profile_csv(path)
        by_name = {p["name"]: p for p in result["profiles"]}
        self.assertEqual(by_name["b"]["nulls"], 1)

    def test_tsv_delimiter(self):
        path = write_csv(self.tmp, "x\ty\n1\t2\n", name="data.tsv")
        result = profile_csv(path, delimiter="\t")
        self.assertEqual(result["columns"], 2)

    def test_empty_file_raises(self):
        path = write_csv(self.tmp, "")
        with self.assertRaises(ValueError):
            profile_csv(path)

    def test_json_serializable(self):
        path = write_csv(self.tmp, "a\n1\n2\n")
        result = profile_csv(path)
        json.dumps(result)


class RenderTests(unittest.TestCase):
    def test_report_contains_key_facts(self):
        path = "/tmp/x.csv"
        result = {
            "file": path,
            "rows": 2,
            "columns": 1,
            "profiles": [profile_column("a", ["1", "2"]).__dict__],
        }
        report = render_report(result)
        self.assertIn("rows: 2", report)
        self.assertIn("[a]", report)
        self.assertIn("type=integer", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
