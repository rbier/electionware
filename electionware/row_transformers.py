from abc import abstractmethod
from typing import Dict, Tuple


class RowTransformer:
    """
    In this context, a row is a dictionary that is written to the
    output file via a csv.DictWriter. This row is created in the
    Electionware TableParser class.

    All registered RowTransformers are called in the TableParser,
    immediately after the row is populated, in the order that they
    were registered.

    The transform command will consume a row, make a copy,
    modify the copy as necessary, and return it.
    """
    def transform(self, row: Dict[str, str]) -> Dict[str, str]:
        return self._transform(row.copy())

    @abstractmethod
    def _transform(self, row: Dict[str, str]) -> Dict[str, str]:
        raise NotImplementedError


class StatisticsTransformer(RowTransformer):
    """
    Most counties have a summary statistics section prior to
    listing each individual contest. This section will generally
    have row titles in the format [statistic] - [party]. This
    transformer will split the title and assign the office and
    party to the associated values, clearing out the candidate
    value.
    """
    PARTY_ABBREVIATIONS: Dict[str, str] = {
        'Total': '',
        'Blank': 'Blank',
        'Democratic Party': 'DEM',
        'Republican Party': 'REP',
        'Democratic': 'DEM',
        'Republican': 'REP',
        'DEMOCRATIC': 'DEM',
        'REPUBLICAN': 'REP',
        'NONPARTISAN': 'NPA',
    }
    OFFICE_NAME: str = 'STATISTICS'

    def _transform(self, row: Dict[str, str]) -> Dict[str, str]:
        if row['office'] == self.OFFICE_NAME:
            row['office'], party = row['candidate'].split(' - ', 1)
            row['party'] = self.PARTY_ABBREVIATIONS[party]
            row['candidate'] = ''
        return row


class OfficeToOfficeAndDistrictTransformer(RowTransformer):
    """
    Most counties have a standard mapping of offices to their
    associated districts. This transformer is initialized with this
    mapping and performs these office and district updates.
    """
    def __init__(self, raw_office_to_office_and_district: Dict[str, Tuple[str, str]]):
        self._raw_office_to_office_and_district: Dict[str, Tuple[str, str]] = \
            raw_office_to_office_and_district

    def _transform(self, row: Dict[str, str]) -> Dict[str, str]:
        office: str = row['office']
        if office in self._raw_office_to_office_and_district:
            row['office'], row['district'] = \
                self._raw_office_to_office_and_district[office]
        return row


class OfficeTitleCaseTransformer(RowTransformer):
    """
    Some counties have offices in all-caps. This transformer
    converts them to Title Case.
    """
    def _transform(self, row: Dict[str, str]) -> Dict[str, str]:
        row['office'] = row['office'].title()
        return row


class CandidateTitleCaseTransformer(RowTransformer):
    """
    Some counties have candidates in all-caps. This transformer
    converts them to Title Case.
    """
    def _transform(self, row: Dict[str, str]) -> Dict[str, str]:
        row['candidate'] = row['candidate'].title()
        return row


class WriteInTotalsTransformer(RowTransformer):
    """
    Write-in Totals are standardized to be listed as "Write-in"
    in the candidate field.
    """
    def _transform(self, row: Dict[str, str]) -> Dict[str, str]:
        if row['candidate'] == 'Write-In Totals':
            row['candidate'] = 'Write-in'
        return row


class StripWriteInPrefixTransformer(RowTransformer):
    """
    In some cases, no Write-in Totals column is provided, and
    write-in candidates are provided with the prefix of "Write-In: ".
    This transformer strips the prefix and provides the candidate's
    name only.
    """
    def _transform(self, row: Dict[str, str]) -> Dict[str, str]:
        row['candidate'] = row['candidate'].replace('Write-In: ', '')
        return row


class DefaultRowTransformer(RowTransformer):
    """
    Most counties have a summary statistics section prior to
    listing each individual contest, a standard mapping of
    offices to their associated districts, and a Write-In Totals
    row. This transformer rolls together these three transformers
    for ease of re-use.
    """
    def __init__(self, raw_office_to_office_and_district: Dict[str, Tuple[str, str]]):
        self._row_transformers: list = [
            StatisticsTransformer(),
            OfficeToOfficeAndDistrictTransformer(raw_office_to_office_and_district),
            WriteInTotalsTransformer()]

    def _transform(self, row: Dict[str, str]) -> Dict[str, str]:
        for row_transformer in self._row_transformers:
            row = row_transformer.transform(row)
        return row
