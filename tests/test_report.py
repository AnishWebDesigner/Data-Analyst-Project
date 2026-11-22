"""Tests for the two PDFs made by src/build_report.py."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import config
from helpers import ROOT, clean_data
from src import build_report as br
from src.captions import build_captions
from src.visualizations import save_all_charts


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        df = clean_data()
        charts = Path(cls.tmp) / "charts"
        save_all_charts(df, charts)
        cls.pdf = Path(cls.tmp) / "report.pdf"
        cls.info = br.build_report(df, build_captions(df), charts, cls.pdf)
        cls.footers = list(br.FOOTERS_DRAWN)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_a_real_pdf_is_made(self):
        """The report file starts with %PDF and is a decent size."""
        self.assertEqual(self.pdf.read_bytes()[:4], b"%PDF")
        self.assertGreater(self.pdf.stat().st_size, 100_000)

    def test_all_thirteen_charts_and_captions_are_in_it(self):
        """The report contains 13 charts and 13 captions."""
        self.assertEqual((self.info["figures"], self.info["captions"]), (13, 13))

    def test_page_count_is_sensible(self):
        """Between 8 and 20 pages: a compact report, not a book."""
        self.assertTrue(8 <= self.info["pages"] <= 20)

    def test_roll_number_is_on_every_page(self):
        """Each page footer contains the roll number and the student name."""
        self.assertEqual(len(self.footers), self.info["pages"])
        for label, page, text in self.footers:
            with self.subTest(page=page):
                self.assertIn(config.ROLL_NO, text)
                self.assertIn(config.STUDENT_NAME, text)

    @unittest.skipUnless(shutil.which("pdftotext"), "pdftotext is not installed")
    def test_cover_shows_name_roll_number_and_github_link(self):
        """The text on page 1 has the name, roll number and GitHub link."""
        text = subprocess.run(["pdftotext", "-f", "1", "-l", "1", str(self.pdf), "-"], capture_output=True, text=True).stdout
        for needed in (config.STUDENT_NAME, config.ROLL_NO, config.GITHUB_URL):
            self.assertIn(needed, text)


class DetailsAndSnapshotTests(unittest.TestCase):
    def test_details_in_config_are_filled_in(self):
        """Name, roll number and GitHub link are the real ones, not placeholders."""
        self.assertEqual(config.STUDENT_NAME, "Anish Kumar")
        self.assertEqual(config.ROLL_NO, "2026M01410002")
        self.assertEqual(config.GITHUB_URL, "https://github.com/AnishWebDesigner/Data-Analyst-Project")

    def test_file_names_start_with_the_roll_number(self):
        """Both PDFs are named with the roll number so they are easy to find."""
        for path in (config.REPORT_PDF, config.SNAPSHOT_PDF):
            self.assertTrue(path.name.startswith(config.ROLL_NO))

    def test_every_listed_source_file_exists(self):
        """All files listed for the code snapshot exist."""
        missing = [f for f in br.CODE_FILES if not (ROOT / f).exists()]
        self.assertEqual(missing, [])

    def test_snapshot_has_every_file_and_the_roll_number_on_every_page(self):
        """The code snapshot contains every source file, and each of its pages shows the roll number."""
        with tempfile.TemporaryDirectory() as folder:
            pdf = Path(folder) / "snapshot.pdf"
            info = br.build_code_snapshot(pdf)
            self.assertEqual(info["files"], br.CODE_FILES)
            self.assertEqual(pdf.read_bytes()[:4], b"%PDF")
            self.assertEqual(len(br.FOOTERS_DRAWN), info["pages"])
            self.assertTrue(all(config.ROLL_NO in text for _, _, text in br.FOOTERS_DRAWN))


if __name__ == "__main__":
    unittest.main()
