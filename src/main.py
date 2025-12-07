import argparse
import sys

from src.tui.app import DicomTreeApp


def main():
    parser = argparse.ArgumentParser(description="Terminal DICOM Navigator")
    parser.add_argument("file", help="Path to the DICOM file")
    args = parser.parse_args()

    app = DicomTreeApp(args.file)
    app.run()


if __name__ == "__main__":
    main()
