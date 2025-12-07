from typing import Any, Iterator, Tuple

import pydicom
from pydicom.dataelem import DataElement
from pydicom.dataset import Dataset


def load_dicom(path: str) -> Dataset:
    """
    Loads a DICOM file from the specified path.
    """
    try:
        return pydicom.dcmread(path, force=True)
    except Exception as e:
        raise IOError(f"Failed to load DICOM file: {e}")


def format_value(elem: DataElement) -> str:
    """
    Formats the value of a DataElement for display.
    """
    if elem.VR == "SQ":
        return f"{len(elem.value)} Item(s)"

    if elem.VM > 1:
        return str(elem.value)

    val = elem.value
    if isinstance(val, (bytes, bytearray)):
        return "<Binary Data>"

    # Handle long strings
    s_val = str(val)
    if len(s_val) > 50:
        return s_val[:47] + "..."
    return s_val


def get_tag_str(elem: DataElement) -> str:
    """
    Returns the tag string in (GGGG,EEEE) format.
    """
    return f"({elem.tag.group:04X},{elem.tag.element:04X})"


def iter_dataset(dataset: Dataset) -> Iterator[Tuple[str, str, str, str, Any]]:
    """
    Iterates over a dataset yielding (tag, name, vr, value_str, raw_value).
    """
    for elem in dataset:
        tag = get_tag_str(elem)
        name = elem.name
        vr = elem.VR
        value_str = format_value(elem)
        yield tag, name, vr, value_str, elem.value
