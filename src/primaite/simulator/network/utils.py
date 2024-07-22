from typing import Union


def convert_bytes_to_megabits(B: Union[int, float]) -> float:  # noqa - Keep it as B as this is how Bytes are expressed
    """
    Convert Bytes (file size) to Megabits (data transfer).

    Technically Mebibits - but for simplicity sake, we'll call it megabit

    :param B: The file size in Bytes.
    :return: File bits to transfer in Megabits.
    """
    if isinstance(B, int):
        B = float(B)
    bits = B * 8.0
    return bits / 1024.0**2.0


def convert_megabits_to_bytes(Mbits: Union[int, float]) -> float:  # noqa - The same for Mbits
    """
    Convert Megabits (data transfer) to Bytes (file size).

    :param Mbits bits to transfer in Megabits.
    :return: The file size in Bytes.
    """
    if isinstance(Mbits, int):
        Mbits = float(Mbits)
    bits = Mbits * 1024.0**2.0
    return bits / 8
