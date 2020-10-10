from abc import abstractmethod
from typing import Dict, List


class RowFilter:
    """
    In this context, a row is a dictionary that is written to the
    output file via a csv.DictWriter. This row is created in the
    Electionware TableParser class.

    All registered RowFilters are called in the TableParser,
    right before the row is yielded to the consumer.

    The filter command will run a comparison against a given row
    and return whether or not this row should be yielded to the
    consumer.
    """
    @abstractmethod
    def filter(self, row: Dict[str, str]) -> bool:
        raise NotImplementedError


class InvalidOfficeFilterBase(RowFilter):
    """
    Abstract class for a generic filter on a given word that should
    not be contained in the row's office field.
    """
    _invalid_word = None

    def filter(self, row: Dict[str, str]) -> bool:
        return self._invalid_word in row['office']


class DelegateOfficeFilter(InvalidOfficeFilterBase):
    _invalid_word = 'Delegate'


class CommitteeOfficeFilter(InvalidOfficeFilterBase):
    _invalid_word = 'Committee'


class VoterTurnoutOfficeFilter(InvalidOfficeFilterBase):
    _invalid_word = 'Voter Turnout'


class BlankPartyFilter(RowFilter):
    """
    Although many statistics fields aer used, the statistics that
    are associated with the party marked as Blank are unused.
    """
    def filter(self, row: Dict[str, str]) -> bool:
        return row['party'] == 'Blank'


class InvalidCandidateFilter(RowFilter):
    """
    Although many statistics fields aer used, the statistics that
    are associated with the candidate fields of Total Votes Cast,
    Contest Totals, and Votes Not Assigned are unused.
    """
    def filter(self, row: Dict[str, str]) -> bool:
        return row['candidate'] in ('Total Votes Cast', 'Contest Totals', 'Not Assigned')


class SpecificWriteInCandidatesFilter(RowFilter):
    """
    Ignore all candidates with "Write-In: " as a prefix. This filter
    is used when there is both a "Write-In Totals" row and a detailed
    breakdown of each write-in candidate.
    """
    def filter(self, row: Dict[str, str]) -> bool:
        return row['candidate'].startswith('Write-In: ')


DEFAULT_ROW_FILTERS: List[RowFilter] = [InvalidCandidateFilter(),
                                        DelegateOfficeFilter(),
                                        VoterTurnoutOfficeFilter(),
                                        BlankPartyFilter()]
