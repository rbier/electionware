import csv
import os
from typing import Dict, List, Union

from electionware.parser import DataSourceParser

OUTPUT_FILE_FORMAT: str = '{}__{}__{}__{}__precinct.csv'
BASE_OUTPUT_HEADER: list = ['county', 'precinct', 'office',
                            'district', 'party', 'candidate']


def get_output_file_path(election_description: Dict[str, str]) -> str:
    """
    Given an election_description dictionary, provide the file path that the csv
    will be written to. This path will be in the structure (all lowercase):
    ../{yyyy}/{yyyymmdd}__{state_abbrev}__{election_type}__{county}__precinct.csv
    """
    yyyymmdd: str = election_description['yyyymmdd']
    state_abbrev: str = election_description['state_abbrev'].lower()
    election_type: str = election_description['type']
    county: str = election_description['county'].lower().replace(' ', '_')
    output_file: str = OUTPUT_FILE_FORMAT.format(
        yyyymmdd, state_abbrev, election_type, county)
    return os.path.join('..', yyyymmdd[:4], output_file)


def get_output_header(table_processing: Dict[str, List[str]]) -> List[str]:
    """
    Given a table_processing dictionary, provide the header for the csv file that
    will be written. This includes standard details on the office, candidate, and
    location of the vote, custom vote-type columns, and the total votes for the
    given office and candidate.
    """
    mapped_header: List[str] = table_processing['openelections_mapped_header']
    header_suffix: List[str] = [x for x in mapped_header if x != 'votes'] + ['votes']
    return BASE_OUTPUT_HEADER + header_suffix


def write_electionware_pdf_to_csv(configuration: Dict[str, Union[Dict, List]]) -> None:
    """
    Given a configuration dictionary, convert a PDF or collection of PDFs into
    a single csv file written in a standard OpenElections format.
    """
    output_file_path: str = get_output_file_path(configuration['election_description'])
    output_header: List[str] = get_output_header(configuration['table_processing'])
    parser: DataSourceParser = DataSourceParser(configuration)
    _write_electionware_pdf_to_csv(output_file_path, output_header, parser)


def _write_electionware_pdf_to_csv(output_file_path: str, output_header: List[str],
                                   parser: DataSourceParser) -> None:
    with open(output_file_path, 'w', newline='') as f_out:
        csv_writer: csv.DictWriter = csv.DictWriter(f_out, output_header)
        csv_writer.writeheader()
        for row in parser:
            csv_writer.writerow(row)
