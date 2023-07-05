from __future__ import annotations

from pathlib import Path

import polars as pl


def compare_transaction_file(output_a_file_path: str | Path, output_b_file_path: str | Path):
    """Function used to check if contents of transaction files are the same."""
    # load output a file
    data_a = pl.read_csv(output_a_file_path)

    # load output b file
    data_b = pl.read_csv(output_b_file_path)

    # remove the time stamp column
    data_a = data_a.drop("Timestamp")
    data_b = data_b.drop("Timestamp")

    # if the comparison is empty, both files are the same i.e. True
    return data_a.frame_equal(data_b)
