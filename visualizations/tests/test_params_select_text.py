# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A select with numeric options accepts the option's value sent as text by a form (review UX-ui, leftovers L2)."""

from lfviz import registry


def _schema(viz_id):
    return registry.load(viz_id)["schema"]


def test_numeric_select_value_sent_as_text_is_taken_as_the_option():
    params, errors = _schema("v13_hydrogen_3d").resolve(None, {"ng": "64"})
    assert not errors and params["ng"] == 64 and isinstance(params["ng"], int)


def test_a_text_that_is_no_option_is_still_refused_in_russian():
    params, errors = _schema("v13_hydrogen_3d").resolve(None, {"ng": "65"})
    assert errors and "there is no option" in str(errors[0])
