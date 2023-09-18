import pytest
from ckanext.who_romania import helpers as who_romania_helpers


class TestGetDates():

    @pytest.mark.parametrize("inputs, output", [
        (('2023-09',), ['01 Sep 2023', '08 Sep 2023', '15 Sep 2023', '22 Sep 2023', '29 Sep 2023']),
        (('2023-03', 1), ['07 Mar 2023', '14 Mar 2023', '21 Mar 2023', '28 Mar 2023']),
        (('2023-12', 0, '%Y-%m-%d'), ['2023-12-04', '2023-12-11', '2023-12-18', '2023-12-25']),
    ])
    def test_get_dates(self, inputs, output):
        dates = who_romania_helpers.get_dates_of_weekday_in_month(*inputs)
        assert dates == output
