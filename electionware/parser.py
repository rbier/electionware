from typing import Dict, Iterable, Iterator, List, Union, Tuple

from electionware.data_source import DataSource
from electionware.pdf import PDFPageIterator, PDFStrings, PDFStringsIterator
from electionware.row_filters import RowFilter, DEFAULT_ROW_FILTERS
from electionware.row_transformers import RowTransformer, DefaultRowTransformer

INSTRUCTION_ROW_PREFIX: str = 'Vote For'


class ElectionwareStringIterator(PDFStringsIterator):
    """
    Given a list of Electionware strings, this class provides basic
    PDFStringsIterator support for iteration and peek() functionaliy,
    while adding Electionware specific logic to determine when specific
    blocks of the PDF are complete, through the page_is_done() and
    table_is_done functions.
    There is also a bad behavior that the PDFs exhibit, where the row
    header and the first field for the Ballots Cast statistic are stored
    in reverse order than expected. The swap_any_bad_ballots_cast_fields
    function manages this behavior to simplify parsing.
    """
    ELECTIONWARE_FOOTER: str = 'Report generated with Electionware'
    BALLOTS_CAST_PREFIX: str = 'Ballots Cast'

    def __init__(self, page_structure: Dict[str, str], strings: List[str]):
        super().__init__(strings)
        self._expected_footer: str = page_structure['expected_footer']

    def page_is_done(self) -> bool:
        s: str = self.peek()
        return s.startswith(self._expected_footer) or \
            s.startswith(self.ELECTIONWARE_FOOTER)

    def table_is_done(self) -> bool:
        return self.peek().startswith(INSTRUCTION_ROW_PREFIX)

    def swap_any_bad_ballots_cast_fields(self) -> None:
        s: str = self._strings[self._strings_offset + 1]
        if s.startswith(self.BALLOTS_CAST_PREFIX):
            self._strings[self._strings_offset + 1] = \
                self._strings[self._strings_offset]
            self._strings[self._strings_offset] = s


class DataSourceParser(Iterable[Dict[str, str]]):
    """
    Wrapper for a collection of ElectionwarePDFs that iterates over
    each page of each PDF and returns rows to be written to the
    OpenElections CSV file.
    The ElectionwarePDFs are extracted from a configuration dictionary.
    In most cases the data source is in the form of a single PDF file.
    """
    def __init__(self, configuration: Dict[str, Union[Dict, List]]):
        self._configuration: Dict[str, Union[str, List]] = configuration

    def __iter__(self) -> Iterator[Dict[str, str]]:
        for data_source in self._configuration['data_source']:
            yield from self._parse(data_source)

    def _parse(self, data_source: DataSource) -> Iterator[Dict[str, str]]:
        with data_source.get_file_like_object() as f_obj:
            for page in PDFPageIterator(f_obj=f_obj):
                print(f'processing page {page.get_page_number()} of {f_obj.name}')
                yield from PageParser(self._configuration, page)


class PageParser(Iterable[Dict[str, str]]):
    """
    Given the strings extracted from a PDF, verifies that the header
    matches the expected page header, extracts the precinct from the
    sub-header, and then iterates over each table found on the PDF
    page.
    """
    def __init__(self, configuration: Dict[str, Union[Dict, List]],
                 page: PDFStrings):
        self._configuration: Dict[str, Union[Dict, List]] = configuration
        page_structure: Dict[str, Union[List, str, bool]] = \
            configuration['page_structure']
        self._string_iterator: ElectionwareStringIterator = \
            ElectionwareStringIterator(page_structure, page.get_strings())
        self._verify_header(page_structure['expected_header'])
        self._precinct: str = self._read_precinct()

    def __iter__(self) -> Iterator[Dict[str, str]]:
        while not self._string_iterator.page_is_done():
            yield from TableParser(self._configuration, self._precinct,
                                   self._string_iterator)

    def _verify_header(self, expected_header: List[str]) -> None:
        header: List[str] = [next(self._string_iterator)
                             for _ in range(len(expected_header))]
        assert header == expected_header

    def _read_precinct(self) -> str:
        return next(self._string_iterator)


class TableParser(Iterable[Dict[str, str]]):
    """
    Given the strings extracted from a PDF for a given table, iteratesextracts
    the candidates verifies that the header
    matches the expected page header, extracts the precinct from the
    sub-header, and then iterates over each table found on the PDF
    page.
    """
    PARTIES: List[str] = ['DEM', 'REP']
    STATISTICS_OFFICE_HEADER: str = 'STATISTICS'
    SINGLE_COLUMN_OFFICES: List[str] = ['Registered Voters', 'Voter Turnout']
    VOTE_PERCENT_COLUMN_HEADER: str = 'VOTE %'

    def __init__(self, configuration: Dict[str, object], precinct: str,
                 string_iterator: ElectionwareStringIterator):
        self._string_iterator: ElectionwareStringIterator = string_iterator
        self._precinct: str = precinct
        # configuration installation
        election_description: Dict[str, str] = \
            configuration['election_description']
        self._county: str = election_description['county']
        page_structure: Dict[str, str] = configuration['page_structure']
        table_headers: List[str] = page_structure['table_headers']
        self._has_vote_percent_column: bool = \
            page_structure['has_vote_percent_column']
        self._expected_table_headers: List[str] = \
            [' '.join(header) for header in table_headers]
        table_processing: Dict[str, Union[Dict, List, str]] = \
            configuration['table_processing']
        default_row_transformer: RowTransformer = DefaultRowTransformer(
            table_processing['raw_office_to_office_and_district'])
        self._openelections_mapped_header: List[str] = \
            table_processing['openelections_mapped_header']
        self._row_transformers: List[RowTransformer] = \
            [default_row_transformer] + table_processing['extra_row_transformers']
        self._row_filters: List[RowFilter] = \
            DEFAULT_ROW_FILTERS +  table_processing['extra_row_filters']
        # header processing
        self._skip_instruction_row()
        self._office: str = self._read_office()
        self._party: str = ''
        self._office, self._party = self._extract_party_from_office(self._office)
        self._verify_and_skip_table_header()

    def __iter__(self) -> Iterator[Dict[str, str]]:
        while True:
            row: Dict[str, str] = self._get_next_row()
            if not any(row_filter.filter(row) for row_filter in self._row_filters):
                yield row

    def _read_office(self) -> str:
        return next(self._string_iterator)

    def _get_next_row(self) -> Dict[str, str]:
        if self._string_iterator.page_is_done() or self._string_iterator.table_is_done():
            raise StopIteration
        self._string_iterator.swap_any_bad_ballots_cast_fields()
        row: Dict[str, str] = self._create_next_row()
        self._skip_vote_percent_field()
        return row

    def _create_next_row(self) -> Dict[str, str]:
        candidate: str = next(self._string_iterator)
        row: Dict[str, str] = self._create_row_shell_for_candidate(candidate)
        for row_transformer in self._row_transformers:
            row = row_transformer.transform(row)
        self._populate_row_votes(row)
        return row

    def _create_row_shell_for_candidate(self, candidate: str) -> Dict[str, str]:
        return {'county': self._county, 'precinct': self._precinct,
                'office': self._office, 'party': self._party, 'district': '',
                'candidate': candidate.strip()}

    def _populate_row_votes(self, row: Dict[str, str]) -> None:
        for header in self._openelections_mapped_header:
            votes: str = next(self._string_iterator)
            if '%' not in votes:
                row[header] = int(votes.replace(',', ''))
            if row['office'] in self.SINGLE_COLUMN_OFFICES:
                break

    def _verify_and_skip_table_header(self) -> None:
        self._skip_vote_percent_column_header()
        actual_header: str = ''
        while len(actual_header) < len(self._expected_table_headers[0]):
            actual_header += next(self._string_iterator) + ' '
        assert actual_header.strip() in self._expected_table_headers

    def _skip_instruction_row(self) -> None:
        if self._string_iterator.peek().startswith(INSTRUCTION_ROW_PREFIX):
            next(self._string_iterator)

    def _skip_vote_percent_column_header(self) -> None:
        if self._has_vote_percent_column:
            if self._office != self.STATISTICS_OFFICE_HEADER:
                vote_percent_header = next(self._string_iterator)
                assert vote_percent_header == self.VOTE_PERCENT_COLUMN_HEADER

    def _skip_vote_percent_field(self) -> None:
        if self._has_vote_percent_column:
            if '%' in self._string_iterator.peek():
                next(self._string_iterator)

    def _extract_party_from_office(self, office: str) -> Tuple[str, str]:
        for test_party in self.PARTIES:
            if office.upper().startswith(test_party + ' '):
                party, office = office.split(' ', 1)
                return office, party.upper()
        return office, ''
