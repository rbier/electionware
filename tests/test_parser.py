from unittest import TestCase
from unittest.mock import patch

from electionware.parser import ElectionwareStringIterator, DataSourceParser, PageParser, TableParser
from electionware.pdf import PDFStrings


class TestElectionwareStringIterator(TestCase):
    def test__page_is_done(self):
        page_structure = {'expected_footer': 'DONE'}
        string_iterator = ElectionwareStringIterator(
            page_structure, ['ok', 'DONE'])
        self.assertFalse(string_iterator.page_is_done())
        self.assertEqual('ok', next(string_iterator))
        self.assertTrue(string_iterator.page_is_done())
        string_iterator = ElectionwareStringIterator(
            page_structure, ['data', 'Report generated with Electionware'])
        self.assertFalse(string_iterator.page_is_done())
        self.assertEqual('data', next(string_iterator))
        self.assertTrue(string_iterator.page_is_done())

    def test__table_is_done(self):
        page_structure = {'expected_footer': 'DONE'}
        string_iterator = ElectionwareStringIterator(
            page_structure, ['ok', 'Vote For', 'DONE'])
        self.assertFalse(string_iterator.page_is_done())
        self.assertFalse(string_iterator.table_is_done())
        self.assertEqual('ok', next(string_iterator))
        self.assertTrue(string_iterator.table_is_done())
        self.assertFalse(string_iterator.page_is_done())
        self.assertEqual('Vote For', next(string_iterator))
        self.assertFalse(string_iterator.table_is_done())
        self.assertTrue(string_iterator.page_is_done())

    def test__ballots_cast_swap(self):
        page_structure = {'expected_footer': 'DONE'}
        string_iterator = ElectionwareStringIterator(
            page_structure, ['ok', '100', 'Ballots Cast', 'DONE'])
        string_iterator.swap_any_bad_ballots_cast_fields()
        self.assertFalse(string_iterator.page_is_done())
        self.assertFalse(string_iterator.table_is_done())
        self.assertEqual('ok', next(string_iterator))
        string_iterator.swap_any_bad_ballots_cast_fields()
        self.assertFalse(string_iterator.table_is_done())
        self.assertFalse(string_iterator.page_is_done())
        self.assertEqual('Ballots Cast', next(string_iterator))
        string_iterator.swap_any_bad_ballots_cast_fields()
        self.assertFalse(string_iterator.table_is_done())
        self.assertFalse(string_iterator.page_is_done())
        self.assertEqual('100', next(string_iterator))
        self.assertFalse(string_iterator.table_is_done())
        self.assertTrue(string_iterator.page_is_done())


class TestDataSourceParser(TestCase):
    def test__data_source_parser(self):
        configuration = {'data_source': [None]}
        data_source_parser = DataSourceParser(configuration)
        data_source_parser._parse = lambda x: [1, 2, 3]
        self.assertEqual(3, len(list(data_source_parser)))


class TestPageParser(TestCase):
    def test__page_parser(self):
        configuration = {
            'page_structure': {
                'expected_header': ['1', 'a'],
                'expected_footer': 'DONE'
            }
        }
        with patch('pdfreader.SimplePDFViewer') as mock:
            mock.current_page_number = 3
            mock.canvas.strings = ['1', 'a', 'b', 'DONE']
            pdf_strings = PDFStrings(mock)
            page_parser = PageParser(configuration, pdf_strings)
            self.assertEqual(page_parser._precinct, 'b')
            self.assertEqual(0, len(list(page_parser)))


class TestTableParser(TestCase):
    def test__table_parser(self):
        configuration = {
            'election_description': {'county': 'test-county'},
            'page_structure': {
                'expected_header': ['a', 'ok'],
                'expected_footer': 'DONE',
                'table_headers': [['votes']],
                'has_vote_percent_column': True
            },
            'table_processing': {
                'extra_row_transformers': [],
                'extra_row_filters': [],
                'raw_office_to_office_and_district': {
                    'office-12': ('test-office', 12),
                },
                'openelections_mapped_header': ['votes'],
            },
        }
        strings = ['Vote For', 'REP office-12', 'VOTE %', 'votes',
                   'test-candidate', '2', '100%',
                   'Registered Voters', '2', 'DONE']
        string_iterator = ElectionwareStringIterator(
            configuration['page_structure'], strings)
        parser = TableParser(configuration, 'test-precinct', string_iterator)
        iterator = iter(parser)
        actual_row = next(iterator)
        expected_row = {'county': 'test-county', 'precinct': 'test-precinct',
                        'party': 'REP', 'office': 'test-office', 'district': 12,
                        'candidate': 'test-candidate', 'votes': 2}
        self.assertEqual(actual_row, expected_row)
        actual_row = next(iterator)
        expected_row = {'county': 'test-county', 'precinct': 'test-precinct',
                        'party': 'REP', 'office': 'test-office', 'district': 12,
                        'candidate': 'Registered Voters', 'votes': 2}
        self.assertEqual(actual_row, expected_row)
        with self.assertRaises(StopIteration):
            next(iterator)
