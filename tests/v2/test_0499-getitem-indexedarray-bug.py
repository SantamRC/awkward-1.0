# BSD 3-Clause License; see https://github.com/scikit-hep/awkward-1.0/blob/main/LICENSE

import pytest  # noqa: F401
import numpy as np  # noqa: F401
import awkward as ak  # noqa: F401

to_list = ak._v2.operations.to_list


def test():
    one_content = ak._v2.highlevel.Array(
        [[1.1, 2.2, 3.3], [], [4.4, 5.5], [6.6], [7.7, 8.8, 9.9, 10.0]]
    ).layout
    one_starts = ak._v2.index.Index64(np.array([0, 2, 3, 3], dtype=np.int64))
    one_stops = ak._v2.index.Index64(np.array([2, 3, 3, 5], dtype=np.int64))
    one = ak._v2.contents.ListArray(one_starts, one_stops, one_content)
    assert to_list(one) == [
        [[1.1, 2.2, 3.3], []],
        [[4.4, 5.5]],
        [],
        [[6.6], [7.7, 8.8, 9.9, 10.0]],
    ]

    two_content = ak._v2.highlevel.Array(
        [
            [123],
            [1.1, 2.2, 3.3],
            [],
            [234],
            [4.4, 5.5],
            [345],
            [6.6],
            [7.7, 8.8, 9.9, 10.0],
            [456],
        ]
    ).layout
    two_starts = ak._v2.index.Index64(np.array([1, 4, 5, 6], dtype=np.int64))
    two_stops = ak._v2.index.Index64(np.array([3, 5, 5, 8], dtype=np.int64))
    two = ak._v2.contents.ListArray(two_starts, two_stops, two_content)

    assert to_list(two) == [
        [[1.1, 2.2, 3.3], []],
        [[4.4, 5.5]],
        [],
        [[6.6], [7.7, 8.8, 9.9, 10.0]],
    ]

    assert to_list(one[[[[0, 1, 2], []], [[0, 1]], [], [[0], [0, 1, 2, 3]]]]) == [
        [[1.1, 2.2, 3.3], []],
        [[4.4, 5.5]],
        [],
        [[6.6], [7.7, 8.8, 9.9, 10.0]],
    ]
    assert (
        one.typetracer[[[[0, 1, 2], []], [[0, 1]], [], [[0], [0, 1, 2, 3]]]].form
        == one[[[[0, 1, 2], []], [[0, 1]], [], [[0], [0, 1, 2, 3]]]].form
    )
    assert to_list(two[[[[0, 1, 2], []], [[0, 1]], [], [[0], [0, 1, 2, 3]]]]) == [
        [[1.1, 2.2, 3.3], []],
        [[4.4, 5.5]],
        [],
        [[6.6], [7.7, 8.8, 9.9, 10.0]],
    ]
    assert (
        two.typetracer[[[[0, 1, 2], []], [[0, 1]], [], [[0], [0, 1, 2, 3]]]].form
        == two[[[[0, 1, 2], []], [[0, 1]], [], [[0], [0, 1, 2, 3]]]].form
    )
