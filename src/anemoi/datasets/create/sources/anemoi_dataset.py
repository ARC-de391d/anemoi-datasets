# (C) Copyright 2025-2026 Anemoi contributors.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import numpy as np
from anemoi.transform import Field
from anemoi.transform import FieldList

from . import source_registry
from .legacy import LegacySource


@source_registry.register("anemoi_dataset")
class AnemoiDatasetSource(LegacySource):

    @staticmethod
    def _execute(context, dates, params=None, **kwargs):

        from anemoi.datasets import open_dataset

        ds = open_dataset(**kwargs)
        # dates_to_index = {date: i for i, date in enumerate(ds.dates)}

        indices = []
        for date in dates:
            idx = np.where(ds.dates == date)[0]
            if len(idx) == 0:
                continue
            indices.append((int(idx[0]), date))

        vars = ds.variables
        if params is None:
            params = vars

        if not isinstance(params, (list, tuple, set)):
            params = [params]

        params = set(params)
        results = []

        ensemble = ds.shape[2] > 1
        geography = {"latitudes": ds.latitudes, "longitudes": ds.longitudes}

        # earthkit-data 1 builds fields from components; the legacy flat dicts
        # (valid_datetime=, param=, number=, ...) passed to FieldList.from_dicts are rejected
        # ("Field.from_components() got an unexpected keyword argument 'valid_datetime'").
        for idx, date in indices:
            for j, y in enumerate(ds[idx]):
                param = vars[j]
                if param not in params:
                    continue
                for k, e in enumerate(y):
                    components = dict(
                        values=e,
                        time={"valid_datetime": date},
                        parameter={"variable": param},
                        geography=geography,
                    )
                    if ensemble:
                        components["ensemble"] = {"member": k + 1}
                    results.append(Field.from_components(**components))

        return FieldList.from_fields(results)
