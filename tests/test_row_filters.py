from unittest import TestCase

from electionware.row_filters import DelegateOfficeFilter, CommitteeOfficeFilter, VoterTurnoutOfficeFilter, \
    InvalidCandidateFilter, SpecificWriteInCandidatesFilter, BlankPartyFilter


class TestInvalidOfficeFilters(TestCase):
    def test__filters(self):
        office_filters = [DelegateOfficeFilter(),
                          CommitteeOfficeFilter(),
                          VoterTurnoutOfficeFilter()]
        row = {'office': 'nofilter'}
        self.assertFalse(any(office_filter.filter(row)
                             for office_filter in office_filters))
        row = {'office': 'Delegate, 12th District'}
        self.assertTrue(any(office_filter.filter(row)
                            for office_filter in office_filters))
        row = {'office': '12th District Committee on Committees'}
        self.assertTrue(any(office_filter.filter(row)
                            for office_filter in office_filters))
        row = {'office': 'Voter Turnout'}
        self.assertTrue(any(office_filter.filter(row)
                            for office_filter in office_filters))
        row = {'office': 'nofilter', 'candidate': 'Delegate',
               'party': 'Committee', 'district': 'Voter Turnout'}
        self.assertFalse(any(office_filter.filter(row)
                             for office_filter in office_filters))


class TestInvalidCandidateFilters(TestCase):
    def test__filters(self):
        office_filters = [InvalidCandidateFilter(),
                          SpecificWriteInCandidatesFilter()]
        row = {'candidate': 'nofilter'}
        self.assertFalse(any(office_filter.filter(row)
                             for office_filter in office_filters))
        row = {'candidate': 'Write-In: filtered'}
        self.assertTrue(any(office_filter.filter(row)
                            for office_filter in office_filters))
        row = {'candidate': 'Total Votes Cast'}
        self.assertTrue(any(office_filter.filter(row)
                            for office_filter in office_filters))
        row = {'office': 'Total Votes Cast', 'candidate': 'nofilter',
               'party': 'Write-In: any'}
        self.assertFalse(any(office_filter.filter(row)
                             for office_filter in office_filters))


class TestInvalidPartyFilters(TestCase):
    def test__filters(self):
        party_filter = BlankPartyFilter()
        row = {'party': 'nofilter'}
        self.assertFalse(party_filter.filter(row))
        row = {'party': 'Blank'}
        self.assertTrue(party_filter.filter(row))
        row = {'office': 'Blank', 'candidate': 'Blank',
               'party': 'nofilter'}
        self.assertFalse(party_filter.filter(row))
