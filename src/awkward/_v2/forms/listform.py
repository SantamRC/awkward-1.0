# BSD 3-Clause License; see https://github.com/scikit-hep/awkward-1.0/blob/main/LICENSE

import awkward as ak
from awkward._v2.forms.form import Form, _parameters_equal


class ListForm(Form):
    is_ListType = True

    def __init__(
        self,
        starts,
        stops,
        content,
        has_identifier=False,
        parameters=None,
        form_key=None,
    ):
        if not ak._util.isstr(starts):
            raise ak._v2._util.error(
                TypeError(
                    "{} 'starts' must be of type str, not {}".format(
                        type(self).__name__, repr(starts)
                    )
                )
            )
        if not ak._util.isstr(stops):
            raise ak._v2._util.error(
                TypeError(
                    "{} 'starts' must be of type str, not {}".format(
                        type(self).__name__, repr(starts)
                    )
                )
            )
        if not isinstance(content, Form):
            raise ak._v2._util.error(
                TypeError(
                    "{} all 'contents' must be Form subclasses, not {}".format(
                        type(self).__name__, repr(content)
                    )
                )
            )

        self._starts = starts
        self._stops = stops
        self._content = content
        self._init(has_identifier, parameters, form_key)

    @property
    def starts(self):
        return self._starts

    @property
    def stops(self):
        return self._stops

    @property
    def content(self):
        return self._content

    def __repr__(self):
        args = [
            repr(self._starts),
            repr(self._stops),
            repr(self._content),
        ] + self._repr_args()
        return "{}({})".format(type(self).__name__, ", ".join(args))

    def _tolist_part(self, verbose, toplevel):
        return self._tolist_extra(
            {
                "class": "ListArray",
                "starts": self._starts,
                "stops": self._stops,
                "content": self._content._tolist_part(verbose, toplevel=False),
            },
            verbose,
        )

    def _type(self, typestrs):
        return ak._v2.types.listtype.ListType(
            self._content._type(typestrs),
            self._parameters,
            ak._v2._util.gettypestr(self._parameters, typestrs),
        )

    def __eq__(self, other):
        if isinstance(other, ListForm):
            return (
                self._has_identifier == other._has_identifier
                and self._form_key == other._form_key
                and self._starts == other._starts
                and self._stops == other._stops
                and _parameters_equal(self._parameters, other._parameters)
                and self._content == other._content
            )
        else:
            return False

    def generated_compatibility(self, other):
        if other is None:
            return True

        elif isinstance(other, ListForm):
            return (
                self._starts == other._starts
                and self._stops == other._stops
                and _parameters_equal(self._parameters, other._parameters)
                and self._content.generated_compatibility(other._content)
            )

        else:
            return False

    def _getitem_range(self):
        return ListForm(
            self._starts,
            self._stops,
            self._content,
            has_identifier=self._has_identifier,
            parameters=self._parameters,
            form_key=None,
        )

    def _getitem_field(self, where, only_fields=()):
        return ListForm(
            self._starts,
            self._stops,
            self._content._getitem_field(where, only_fields),
            has_identifier=self._has_identifier,
            parameters=None,
            form_key=None,
        )

    def _getitem_fields(self, where, only_fields=()):
        return ListForm(
            self._starts,
            self._stops,
            self._content._getitem_fields(where, only_fields),
            has_identifier=self._has_identifier,
            parameters=None,
            form_key=None,
        )

    def _carry(self, allow_lazy):
        return ListForm(
            self._starts,
            self._stops,
            self._content,
            has_identifier=self._has_identifier,
            parameters=self._parameters,
            form_key=None,
        )

    def purelist_parameter(self, key):
        if self._parameters is None or key not in self._parameters:
            return self._content.purelist_parameter(key)
        else:
            return self._parameters[key]

    @property
    def purelist_isregular(self):
        return False

    @property
    def purelist_depth(self):
        if self.parameter("__array__") in ("string", "bytestring"):
            return 1
        else:
            return self._content.purelist_depth + 1

    @property
    def minmax_depth(self):
        if self.parameter("__array__") in ("string", "bytestring"):
            return (1, 1)
        else:
            mindepth, maxdepth = self._content.minmax_depth
            return (mindepth + 1, maxdepth + 1)

    @property
    def branch_depth(self):
        if self.parameter("__array__") in ("string", "bytestring"):
            return (False, 1)
        else:
            branch, depth = self._content.branch_depth
            return (branch, depth + 1)

    @property
    def fields(self):
        return self._content.fields

    @property
    def is_tuple(self):
        return self._content.is_tuple

    @property
    def dimension_optiontype(self):
        return False

    def _columns(self, path, output, list_indicator):
        if (
            self.parameter("__array__") not in ("string", "bytestring")
            and list_indicator is not None
        ):
            path = path + (list_indicator,)
        self._content._columns(path, output, list_indicator)

    def _select_columns(self, index, specifier, matches, output):
        return ListForm(
            self._starts,
            self._stops,
            self._content._select_columns(index, specifier, matches, output),
            self._has_identifier,
            self._parameters,
            self._form_key,
        )

    def _column_types(self):
        if self.parameter("__array__") in ("string", "bytestring"):
            return ("string",)
        else:
            return self._content._column_types()
