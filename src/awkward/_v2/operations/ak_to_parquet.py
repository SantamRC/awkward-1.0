# BSD 3-Clause License; see https://github.com/scikit-hep/awkward-1.0/blob/main/LICENSE

from collections.abc import Iterable, Sized, Mapping, Sequence

import numpy as np

import awkward as ak


def to_parquet(
    data,
    destination,
    list_to32=False,
    string_to32=True,
    bytestring_to32=True,
    emptyarray_to=None,
    categorical_as_dictionary=False,
    extensionarray=True,
    count_nulls=True,
    compression="zstd",
    compression_level=None,
    row_group_size=64 * 1024 * 1024,
    data_page_size=None,
    parquet_flavor=None,
    parquet_version="1.0",
    parquet_page_version="1.0",
    parquet_metadata_statistics=True,
    parquet_dictionary_encoding=False,
    parquet_byte_stream_split=False,
    parquet_coerce_timestamps=None,
    parquet_old_int96_timestamps=None,
    parquet_compliant_nested=False,  # https://issues.apache.org/jira/browse/ARROW-16348
    parquet_extra_options=None,
    hook_after_write=None,
):
    import awkward._v2._connect.pyarrow

    pyarrow_parquet = awkward._v2._connect.pyarrow.import_pyarrow_parquet(
        "ak.to_parquet"
    )
    fsspec = awkward._v2._connect.pyarrow.import_fsspec("ak.to_parquet")

    if isinstance(data, (ak._v2.highlevel.Record, ak._v2.record.Record)):
        iterator = iter([data])
    elif isinstance(data, Iterable) and not isinstance(data, Sized):
        iterator = iter(data)
    elif isinstance(data, Iterable):
        iterator = iter([data])
    else:
        raise ak._v2._util.error(
            TypeError(
                "'data' must be an array (one row group) or iterable of arrays (row group per array)"
            )
        )

    row_group = 0
    array = next(iterator)
    layout = ak._v2.operations.ak_to_layout.to_layout(
        array, allow_record=True, allow_other=False
    )
    table = ak._v2.operations.ak_to_arrow_table._impl(
        layout,
        list_to32,
        string_to32,
        bytestring_to32,
        emptyarray_to,
        categorical_as_dictionary,
        extensionarray,
        count_nulls,
    )

    if parquet_compliant_nested:
        list_indicator = "list.element"
    else:
        list_indicator = "list.item"

    if table.column_names == [""]:
        column_prefix = ("",)
    else:
        column_prefix = ()

    if isinstance(layout, ak._v2.record.Record):
        form = layout.array.form
    else:
        form = layout.form

    def parquet_columns(specifier, only=None):
        if specifier is None:
            selected_form = form
        else:
            selected_form = form.select_columns(specifier)

        parquet_column_names = selected_form.columns(
            list_indicator=list_indicator, column_prefix=column_prefix
        )
        if only is not None:
            column_types = selected_form.column_types()
            assert len(parquet_column_names) == len(column_types)
            if only == "string":
                return [
                    x
                    for x, y in zip(parquet_column_names, column_types)
                    if y == "string"
                ]
            elif only == "floating":
                return [
                    x
                    for x, y in zip(parquet_column_names, column_types)
                    if isinstance(y, np.dtype) and issubclass(y.type, np.floating)
                ]
        else:
            return parquet_column_names

    if compression is True:
        compression = "zstd"
    elif compression is False or compression is None:
        compression = "none"
    elif isinstance(compression, Mapping):
        replacement = {}
        for specifier, value in compression.items():
            replacement.update({x: value for x in parquet_columns(specifier)})
        compression = replacement

    if isinstance(compression_level, Mapping):
        replacement = {}
        for specifier, value in compression_level.items():
            replacement.update({x: value for x in parquet_columns(specifier)})
        compression_level = replacement

    if parquet_metadata_statistics is True:
        parquet_metadata_statistics = True
    elif parquet_metadata_statistics is False or parquet_metadata_statistics is None:
        parquet_metadata_statistics = False
    elif isinstance(parquet_metadata_statistics, Mapping):
        replacement = {}
        for specifier, value in parquet_metadata_statistics.items():
            replacement.update({x: value for x in parquet_columns(specifier)})
        parquet_metadata_statistics = [x for x, value in replacement.items() if value]
    elif isinstance(parquet_metadata_statistics, Sequence):
        replacement = []
        for specifier in parquet_metadata_statistics:
            replacement.extend([x for x in parquet_columns(specifier)])
        parquet_metadata_statistics = replacement

    if parquet_dictionary_encoding is True:
        parquet_dictionary_encoding = parquet_columns(None, only="string")
    elif parquet_dictionary_encoding is False or parquet_dictionary_encoding is None:
        parquet_dictionary_encoding = False
    elif isinstance(parquet_dictionary_encoding, Mapping):
        replacement = {}
        for specifier, value in parquet_dictionary_encoding.items():
            replacement.update(
                {x: value for x in parquet_columns(specifier, only="string")}
            )
        parquet_dictionary_encoding = [x for x, value in replacement.items() if value]

    if parquet_byte_stream_split is True:
        parquet_byte_stream_split = parquet_columns(None, only="floating")
    elif parquet_byte_stream_split is False or parquet_byte_stream_split is None:
        parquet_byte_stream_split = False
    elif isinstance(parquet_byte_stream_split, Mapping):
        replacement = {}
        for specifier, value in parquet_byte_stream_split.items():
            replacement.update(
                {x: value for x in parquet_columns(specifier, only="floating")}
            )
        parquet_byte_stream_split = [x for x, value in replacement.items() if value]

    if parquet_extra_options is None:
        parquet_extra_options = {}

    with fsspec.open(destination, "wb") as file:
        with pyarrow_parquet.ParquetWriter(
            destination,
            table.schema,
            filesystem=file.fs,
            flavor=parquet_flavor,
            version=parquet_version,
            use_dictionary=parquet_dictionary_encoding,
            compression=compression,
            write_statistics=parquet_metadata_statistics,
            use_deprecated_int96_timestamps=parquet_old_int96_timestamps,
            compression_level=compression_level,
            use_byte_stream_split=parquet_byte_stream_split,
            data_page_version=parquet_page_version,
            use_compliant_nested_type=parquet_compliant_nested,
            data_page_size=data_page_size,
            coerce_timestamps=parquet_coerce_timestamps,
            **parquet_extra_options,
        ) as writer:
            while True:
                writer.write_table(table, row_group_size=row_group_size)
                if hook_after_write is not None:
                    hook_after_write(
                        row_group=row_group,
                        array=array,
                        layout=layout,
                        table=table,
                        writer=writer,
                    )

                row_group += 1
                try:
                    array = next(iterator)
                except StopIteration:
                    break
                layout = ak._v2.operations.ak_to_layout.to_layout(
                    array, allow_record=True, allow_other=False
                )
                table = ak._v2.operations.ak_to_arrow_table._impl(
                    layout,
                    list_to32,
                    string_to32,
                    bytestring_to32,
                    emptyarray_to,
                    categorical_as_dictionary,
                    extensionarray,
                    count_nulls,
                )
