# (C) Copyright 2026 Anemoi contributors.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""repeated_dates mode=closest with request_by: valid_datetime (default) and base_datetime."""

import datetime

import pytest

from anemoi.datasets.create.input.repeated_dates import DateMapperClosest
from anemoi.datasets.create.recipe.dates import StartEndDates
from anemoi.datasets.dates.groups import GroupOfDates

D = datetime.datetime


class _Time:
    def __init__(self, base):
        self._base = base

    def base_datetime(self):
        return self._base


class _Field:
    def __init__(self, base, valid):
        self.time = _Time(base)
        self.valid_datetime = valid


def _daily_mean_source(first_day):
    """A stepless archive of daily means: requested by date D at 00 UTC, valid D+1 00 UTC."""

    def source(context, group):
        return [_Field(d, d + datetime.timedelta(days=1)) for d in group if d.hour == 0 and d >= first_day]

    return source


def _mapping(mapper, provider, stamps):
    group = GroupOfDates(stamps, provider)
    out = {}
    for requested, asked in mapper.transform(None, group):
        for a in asked:
            out[a] = list(requested)[0]
    return out


@pytest.fixture
def provider():
    return StartEndDates(start="2000-01-01T00:00:00", end="2000-01-05T18:00:00", frequency="6h")


STAMPS = [D(2000, 1, 3, h) for h in (0, 6, 12, 18)]


def test_closest_request_by_base_datetime(provider):
    mapper = DateMapperClosest(_daily_mean_source(D(2000, 1, 1)), frequency="6h", maximum="1d",
                               request_by="base_datetime")
    got = _mapping(mapper, provider, STAMPS)
    # the daily mean whose window ends closest: 00/06 -> day 2 (ends 3rd 00), 12/18 -> day 3 (tie to later)
    assert got == {STAMPS[0]: D(2000, 1, 2), STAMPS[1]: D(2000, 1, 2), STAMPS[2]: D(2000, 1, 3), STAMPS[3]: D(2000, 1, 3)}


def test_closest_default_requests_by_valid_datetime(provider):
    # unchanged behaviour: the valid time of the closest field is passed back to the source
    mapper = DateMapperClosest(_daily_mean_source(D(2000, 1, 1)), frequency="6h", maximum="1d")
    got = _mapping(mapper, provider, STAMPS)
    assert got == {STAMPS[0]: D(2000, 1, 3), STAMPS[1]: D(2000, 1, 3), STAMPS[2]: D(2000, 1, 4), STAMPS[3]: D(2000, 1, 4)}


def test_closest_invalid_request_by():
    with pytest.raises(ValueError):
        DateMapperClosest(None, request_by="step")
