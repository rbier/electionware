from unittest import TestCase

from electionware.row_transformers import StatisticsTransformer, DefaultRowTransformer, \
    OfficeTitleCaseTransformer, CandidateTitleCaseTransformer, StripWriteInPrefixTransformer


class TestStatisticsTransformer(TestCase):
    def test__noop(self):
        row_to_test = {'office': 'unchanged'}
        row_expected = row_to_test.copy()
        row_actual = StatisticsTransformer().transform(row_to_test)
        self.assertEqual(row_expected, row_actual)
        self.assertEqual(row_expected, row_to_test)

    def test__bad_candidate(self):
        row_to_test = {'office': 'STATISTICS', 'candidate': 'Ballots Cast'}
        with self.assertRaises(ValueError):
            StatisticsTransformer().transform(row_to_test)

    def test__bad_party(self):
        row_to_test = {'office': 'STATISTICS',
                       'candidate': 'Ballots Cast - Anarchists'}
        with self.assertRaises(KeyError):
            StatisticsTransformer().transform(row_to_test)

    def test__republican_party(self):
        row_to_test = {'office': 'STATISTICS',
                       'candidate': 'Ballots Cast - Republican'}
        row_to_test_unmodified = row_to_test.copy()
        row_expected = {'office': 'Ballots Cast',
                        'party': 'REP', 'candidate': ''}
        row_actual = StatisticsTransformer().transform(row_to_test)
        self.assertEqual(row_expected, row_actual)
        self.assertEqual(row_to_test_unmodified, row_to_test)

    def test__democratic_party(self):
        row_to_test = {'office': 'STATISTICS',
                       'candidate': 'Registered Voters - Democratic'}
        row_to_test_unmodified = row_to_test.copy()
        row_expected = {'office': 'Registered Voters',
                        'party': 'DEM', 'candidate': ''}
        row_actual = StatisticsTransformer().transform(row_to_test)
        self.assertEqual(row_expected, row_actual)
        self.assertEqual(row_to_test_unmodified, row_to_test)


class TestDefaultTransformer(TestCase):
    RAW_OFFICE_TO_OFFICE_AND_DISTRICT = {
        'PRESIDENT OF THE UNITED STATES': ('President', ''),
        'REP IN CONGRESS 1ST DISTRICT': ('U.S. House', 1),
    }

    def setUp(self):
        self._row_transformer = DefaultRowTransformer(
            self.RAW_OFFICE_TO_OFFICE_AND_DISTRICT)

    def test__noop(self):
        row_to_test = {'office': 'unchanged', 'candidate': 'unchanged'}
        row_expected = row_to_test.copy()
        row_actual = self._row_transformer.transform(row_to_test)
        self.assertEqual(row_expected, row_actual)
        self.assertEqual(row_expected, row_to_test)

    def test__statistics(self):
        row_to_test = {'office': 'STATISTICS',
                       'candidate': 'Registered Voters - Democratic'}
        row_to_test_unmodified = row_to_test.copy()
        row_expected = {'office': 'Registered Voters',
                        'party': 'DEM', 'candidate': ''}
        row_actual = self._row_transformer.transform(row_to_test)
        self.assertEqual(row_expected, row_actual)
        self.assertEqual(row_to_test_unmodified, row_to_test)

    def test__office_no_district(self):
        row_to_test = {'office': 'PRESIDENT OF THE UNITED STATES',
                       'candidate': 'unchanged'}
        row_to_test_unmodified = row_to_test.copy()
        row_expected = {'office': 'President', 'district': '',
                        'candidate': 'unchanged'}
        row_actual = self._row_transformer.transform(row_to_test)
        self.assertEqual(row_expected, row_actual)
        self.assertEqual(row_to_test_unmodified, row_to_test)

    def test__office_with_district(self):
        row_to_test = {'office': 'REP IN CONGRESS 1ST DISTRICT',
                       'candidate': 'unchanged'}
        row_to_test_unmodified = row_to_test.copy()
        row_expected = {'office': 'U.S. House', 'district': 1,
                        'candidate': 'unchanged'}
        row_actual = self._row_transformer.transform(row_to_test)
        self.assertEqual(row_expected, row_actual)
        self.assertEqual(row_to_test_unmodified, row_to_test)

    def test__write_in(self):
        row_to_test = {'office': 'unchanged',
                       'candidate': 'Write-In Totals'}
        row_to_test_unmodified = row_to_test.copy()
        row_expected = {'office': 'unchanged', 'candidate': 'Write-in'}
        row_actual = self._row_transformer.transform(row_to_test)
        self.assertEqual(row_expected, row_actual)
        self.assertEqual(row_to_test_unmodified, row_to_test)

    def test__write_in_and_office_with_district(self):
        row_to_test = {'office': 'REP IN CONGRESS 1ST DISTRICT',
                       'candidate': 'Write-In Totals'}
        row_to_test_unmodified = row_to_test.copy()
        row_expected = {'office': 'U.S. House', 'district': 1,
                        'candidate': 'Write-in'}
        row_actual = self._row_transformer.transform(row_to_test)
        self.assertEqual(row_expected, row_actual)
        self.assertEqual(row_to_test_unmodified, row_to_test)


class TestTitleTransformers(TestCase):
    def test__office(self):
        row_to_test = {'office': 'TITLE CASE', 'candidate': 'TITLE CASE 2'}
        row_to_test_unmodified = row_to_test.copy()
        row_expected = {'office': 'Title Case', 'candidate': 'TITLE CASE 2'}
        row_actual = OfficeTitleCaseTransformer().transform(row_to_test)
        self.assertEqual(row_expected, row_actual)
        self.assertEqual(row_to_test_unmodified, row_to_test)

    def test__candidate(self):
        row_to_test = {'office': 'TITLE CASE', 'candidate': 'TITLE CASE 2'}
        row_to_test_unmodified = row_to_test.copy()
        row_expected = {'office': 'TITLE CASE', 'candidate': 'Title Case 2'}
        row_actual = CandidateTitleCaseTransformer().transform(row_to_test)
        self.assertEqual(row_expected, row_actual)
        self.assertEqual(row_to_test_unmodified, row_to_test)

    def test__candidate_and_office(self):
        row_to_test = {'office': 'TITLE CASE', 'candidate': 'TITLE CASE 2'}
        row_to_test_unmodified = row_to_test.copy()
        row_expected = {'office': 'Title Case', 'candidate': 'Title Case 2'}
        interim_row = OfficeTitleCaseTransformer().transform(row_to_test)
        row_actual = CandidateTitleCaseTransformer().transform(interim_row)
        self.assertEqual(row_expected, row_actual)
        self.assertEqual(row_to_test_unmodified, row_to_test)


class TestStripWriteInPrefixTransformer(TestCase):
    def test__noop(self):
        row_to_test = {'candidate': 'unchanged'}
        row_expected = row_to_test.copy()
        row_actual = StripWriteInPrefixTransformer().transform(row_to_test)
        self.assertEqual(row_expected, row_actual)
        self.assertEqual(row_expected, row_to_test)

    def test__strip_write_in(self):
        row_to_test = {'candidate': 'Write-In: Mickey Mouse'}
        row_to_test_unmodified = row_to_test.copy()
        row_expected = {'candidate': 'Mickey Mouse'}
        row_actual = StripWriteInPrefixTransformer().transform(row_to_test)
        self.assertEqual(row_expected, row_actual)
        self.assertEqual(row_to_test_unmodified, row_to_test)
