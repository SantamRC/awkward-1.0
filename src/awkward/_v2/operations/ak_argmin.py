# BSD 3-Clause License; see https://github.com/scikit-hep/awkward-1.0/blob/main/LICENSE

import awkward as ak

np = ak.nplike.NumpyMetadata.instance()


# @ak._v2._connect.numpy.implements("argmin")
def argmin(array, axis=None, keepdims=False, mask_identity=True, flatten_records=False):
    """
    Args:
        array: Array-like data (anything #ak.to_layout recognizes).
        axis (None or int): If None, combine all values from the array into
            a single scalar result; if an int, group by that axis: `0` is the
            outermost, `1` is the first level of nested lists, etc., and
            negative `axis` counts from the innermost: `-1` is the innermost,
            `-2` is the next level up, etc.
        keepdims (bool): If False, this reducer decreases the number of
            dimensions by 1; if True, the reduced values are wrapped in a new
            length-1 dimension so that the result of this operation may be
            broadcasted with the original array.
        mask_identity (bool): If True, reducing over empty lists results in
            None (an option type); otherwise, reducing over empty lists
            results in the operation's identity.
        flatten_records (bool): If True, axis=None combines fields from different
            records; otherwise, records raise an error.

    Returns the index position of the minimum value in each group of elements
    from `array` (many types supported, including all Awkward Arrays and
    Records). The identity of minimization would be infinity, but argmin
    must return the position of the minimum element, which has no value for
    empty lists. Therefore, the identity should be masked: the argmin of
    an empty list is None. If `mask_identity=False`, the result would be `-1`,
    which is distinct from all valid index positions, but care should be taken
    that it is not misinterpreted as "the last element of the list."

    This operation is the same as NumPy's
    [argmin](https://docs.scipy.org/doc/numpy/reference/generated/numpy.argmin.html)
    if all lists at a given dimension have the same length and no None values,
    but it generalizes to cases where they do not.

    See #ak.sum for a more complete description of nested list and missing
    value (None) handling in reducers.

    See also #ak.nanargmin.
    """
    with ak._v2._util.OperationErrorContext(
        "ak._v2.argmin",
        dict(
            array=array,
            axis=axis,
            keepdims=keepdims,
            mask_identity=mask_identity,
            flatten_records=flatten_records,
        ),
    ):
        return _impl(array, axis, keepdims, mask_identity, flatten_records)


# @ak._v2._connect.numpy.implements("nanargmin")
def nanargmin(
    array, axis=None, keepdims=False, mask_identity=True, flatten_records=False
):
    """
    Args:
        array: Array-like data (anything #ak.to_layout recognizes).
        axis (None or int): If None, combine all values from the array into
            a single scalar result; if an int, group by that axis: `0` is the
            outermost, `1` is the first level of nested lists, etc., and
            negative `axis` counts from the innermost: `-1` is the innermost,
            `-2` is the next level up, etc.
        keepdims (bool): If False, this reducer decreases the number of
            dimensions by 1; if True, the reduced values are wrapped in a new
            length-1 dimension so that the result of this operation may be
            broadcasted with the original array.
        mask_identity (bool): If True, reducing over empty lists results in
            None (an option type); otherwise, reducing over empty lists
            results in the operation's identity.
        flatten_records (bool): If True, axis=None combines fields from different
            records; otherwise, records raise an error.

    Like #ak.argmin, but treating NaN ("not a number") values as missing.

    Equivalent to

        ak.argmin(ak.nan_to_none(array))

    with all other arguments unchanged.

    See also #ak.argmin.
    """
    with ak._v2._util.OperationErrorContext(
        "ak._v2.nanargmin",
        dict(
            array=array,
            axis=axis,
            keepdims=keepdims,
            mask_identity=mask_identity,
            flatten_records=flatten_records,
        ),
    ):
        array = ak._v2.operations.ak_nan_to_none._impl(array, False, None)

        return _impl(array, axis, keepdims, mask_identity, flatten_records)


def _impl(array, axis, keepdims, mask_identity, flatten_records):
    layout = ak._v2.operations.to_layout(array, allow_record=False, allow_other=False)

    if axis is None:
        if not layout.nplike.known_data or not layout.nplike.known_shape:
            reducer_cls = ak._v2._reducers.ArgMin
            return ak._v2._typetracer.MaybeNone(
                ak._v2._typetracer.UnknownScalar(
                    np.dtype(reducer_cls.return_dtype(None))
                )
            )

        layout = ak._v2.operations.fill_none(layout, np.inf, axis=-1, highlevel=False)

        best_index = None
        best_value = None
        for tmp in layout.completely_flatten(
            function_name="ak.argmin", flatten_records=flatten_records
        ):
            if len(tmp) > 0:
                out = layout.nplike.argmin(tmp, axis=None)
                if best_index is None or tmp[out] < best_value:
                    best_index = out
                    best_value = tmp[out]
        return best_index

    else:
        behavior = ak._v2._util.behavior_of(array)
        out = layout.argmin(axis=axis, mask=mask_identity, keepdims=keepdims)
        if isinstance(out, (ak._v2.contents.Content, ak._v2.record.Record)):
            return ak._v2._util.wrap(out, behavior)
        else:
            return out
