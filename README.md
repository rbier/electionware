This package is used to convert Electionware PDFs to OpenElections-style CSVs. Validated with Pennsylvania
2020 Primaries; additional states and elections TBD. Support for Python 3.6+.

An example parser that uses this converter is as follows (uses data from openelections-sources-pa and is
equivalent to the Washington county parser in openelections-data-pa):

    from electionware.csv import write_electionware_pdf_to_csv
    from electionware.data_source import FileSource
    from electionware.row_filters import SpecificWriteInCandidatesFilter
    from electionware.row_transformers import CandidateTitleCaseTransformer, OfficeTitleCaseTransformer
       
    # low-code config object used for the PDF to CSV converter
    CONFIGURATION = {
        # Where to read data from. This can be multiple PDF files on local disk
        # or can be other DataSource types (see data_source.DataSource).
        'data_source': [
            FileSource('Washington PA 2020 Primary Precinct Summary.pdf')
        ],
     
        # Location, date, and type of election. Used for determining output file
        # location and the county column of each CSV
        'election_description': {
            'county': 'Washington',
            'state_abbrev': 'PA',
            'yyyymmdd': '20200602',
            'type': 'primary',
        },
     
        # The headers and footers for the given PDFs, which are used as hints to
        # determine the boundaries of each table on the PDF page. Also includes
        # whether there is a "Vote %" column, since those columns are ignoreable.
        'page_structure': {
            'expected_header': [
                '',
                'Summary Results Report',
                '2020 Presidential Primary',
                'June 2, 2020',
                'OFFICIAL RESULTS',
                'Washington',
            ],
            'expected_footer': 'Precinct Summary - 06/23/2020',
            'table_headers': [
                ['TOTAL', 'Election Day', 'Absentee', 'Provisional', 'Military',],
                ['TOTAL', 'Election Day', 'Military', 'Provisional', 'Absentee',],
            ],
            'has_vote_percent_column': True
        },
     
        # Data transformation objects. Row transformers modify fields before writing
        # them to CSV (e.g. by converting candidate name "JOHN DOE" to "John Doe").
        # Row filters determine which rows to not write to CSV (e.g. skipping all
        # instances of "Write-In: JOHN DOE"). Also maps provided offices names to
        # standardized OpenElections office and district, and maps the provided vote
        # types (see page_structure->table_headers) to the OpenElections equivalents.
        'table_processing': {
            'extra_row_transformers': [
                CandidateTitleCaseTransformer(),
                OfficeTitleCaseTransformer()
            ],
            'extra_row_filters': [
                SpecificWriteInCandidatesFilter()
            ],
            'raw_office_to_office_and_district': {
                'PRESIDENT OF THE UNITED STATES': ('President', ''),
                'REPRESENTATIVE IN CONGRESS': ('U.S. House', 14),
                'REPRESENTATIVE IN THE GENERAL ASSEMBLY 15TH DISTRICT': ('General Assembly', 15),
                'REPRESENTATIVE IN THE GENERAL ASSEMBLY 39TH DISTRICT': ('General Assembly', 39),
                'REPRESENTATIVE IN THE GENERAL ASSEMBLY 40TH DISTRICT': ('General Assembly', 40),
                'REPRESENTATIVE IN THE GENERAL ASSEMBLY 46TH DISTRICT': ('General Assembly', 46),
                'REPRESENTATIVE IN THE GENERAL ASSEMBLY 48TH DISTRICT': ('General Assembly', 48),
                'REPRESENTATIVE IN THE GENERAL ASSEMBLY 49TH DISTRICT': ('General Assembly', 49),
                'REPRESENTATIVE IN THE GENERAL ASSEMBLY 50TH DISTRICT': ('General Assembly', 50),
                'SENATOR IN THE GENERAL ASSEMBLY 37TH DISTRICT': ('State Senate', 37),
            },
            'openelections_mapped_header': [
                'votes', 'election_day', 'absentee', 'provisional', 'military',
            ],
        },
    }
     
    # Performs the PDF to CSV conversion
    if __name__ == "__main__":
        write_electionware_pdf_to_csv(CONFIGURATION)
