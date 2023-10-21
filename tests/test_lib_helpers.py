import unittest
from lib.Helpers import filefilter_to_extension, filepath_verify_extension


class HelpersTest(unittest.TestCase):

	def test_filepath_verify_extension(self):
		self.assertTrue(filepath_verify_extension("/home/buccanseersdan/test.json", "json"))
		self.assertFalse(filepath_verify_extension("/home/buccanseersdan/test.Json", "json", True))
		self.assertTrue(filepath_verify_extension("/home/buccanseersdan/test.JsOn", "jsoN"))

	def test_filefilter_to_extension(self):
		msg = "'{}' != 'csv' (maybe '{}' was not filtered)"

		ff = filefilter_to_extension("XY(*.csv)")
		self.assertEqual("csv", ff, msg.format(ff, "*."))

		ff = filefilter_to_extension("XY(.csv)")
		self.assertEqual("csv", ff, msg.format(ff, "."))

		ff = filefilter_to_extension("XY(csv)")
		self.assertEqual("csv", ff, msg.format(ff, ""))