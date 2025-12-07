import os
from pathlib import Path

import requests

BASE_URL = (
    "https://raw.githubusercontent.com/innolitics/dicom-standard/master/standard/"
)
FILES_TO_FETCH = [
    "attributes.json",
    "modules.json",
    "module_to_attributes.json",
    "ciods.json",
    "ciod_to_modules.json",
    "macros.json",
    "macro_to_attributes.json",
    "ciod_to_func_group_macros.json",
]


def fetch_standard_files(output_dir: str = "standard"):
    """
    Fetches the DICOM standard JSON files from the innolitics repository.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Fetching DICOM standard files to '{output_path.absolute()}'...")

    for filename in FILES_TO_FETCH:
        url = BASE_URL + filename
        dest_file = output_path / filename

        print(f"Downloading {filename}...")
        try:
            response = requests.get(url)
            response.raise_for_status()

            with open(dest_file, "wb") as f:
                f.write(response.content)
            print(f"  -> Saved {filename}")
        except requests.exceptions.RequestException as e:
            print(f"  -> Error downloading {filename}: {e}")


if __name__ == "__main__":
    fetch_standard_files()
