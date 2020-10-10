import os
from unittest import TestCase
from unittest.mock import patch

from electionware.csv import get_output_file_path, get_output_header, \
    write_electionware_pdf_to_csv


class TestOutputFilePath(TestCase):
    def test__output_file_path(self):
        expected = os.path.join(
            '..', '2000', '20001231__aa__test__county_name__precinct.csv')
        election_description = {'yyyymmdd': '20001231', 'state_abbrev': 'AA',
                                'type': 'test', 'county': 'County Name'}
        actual = get_output_file_path(election_description)
        self.assertEqual(expected, actual)


class TestOutputHeader(TestCase):
    def test__single_vote_type_header(self):
        expected = ['county', 'precinct', 'office', 'district', 'party',
                    'candidate', 'votes']
        table_processing = {'openelections_mapped_header': ['votes']}
        actual = get_output_header(table_processing)
        self.assertEqual(expected, actual)

    def test__multiple_vote_type_header(self):
        expected = ['county', 'precinct', 'office', 'district', 'party',
                    'candidate', 'election_day', 'absentee', 'votes']
        table_processing = {
            'openelections_mapped_header': ['votes', 'election_day', 'absentee']}
        actual = get_output_header(table_processing)
        self.assertEqual(expected, actual)


class TestCSV(TestCase):
    def test__pdf_to_csv(self):
        with patch('electionware.csv._write_electionware_pdf_to_csv') as mock:
            configuration = {
                'election_description': {
                    'yyyymmdd': '20001231', 'state_abbrev': 'AA',
                    'type': 'test', 'county': 'County Name'},
                'table_processing': {
                    'openelections_mapped_header': ['votes']}
            }
            write_electionware_pdf_to_csv(configuration.copy())
            expected_filepath = os.path.join(
                '..', '2000', '20001231__aa__test__county_name__precinct.csv')
            expected_header = ['county', 'precinct', 'office', 'district', 'party',
                               'candidate', 'votes']
            self.assertEqual(mock.call_args[0][0], expected_filepath)
            self.assertEqual(mock.call_args[0][1], expected_header)
            self.assertEqual(mock.call_args[0][2]._configuration, configuration)
