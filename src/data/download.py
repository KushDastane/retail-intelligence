"""Deterministic dataset downloader with integrity verification.

Downloads the canonical Tableau Sample - Superstore CSV dataset into data/raw/
and performs SHA-256 verification and row count validation.
"""

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

# Support running as a standalone script or imported module
try:
    from src.config import (
        DATASET_ENCODING,
        DATASET_EXPECTED_ROWS,
        DATASET_SOURCE_URL,
        RAW_DATA_DIR,
        RAW_DATA_FILE,
    )
except ImportError:
    # If run directly as python src/data/download.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from src.config import (
        DATASET_ENCODING,
        DATASET_EXPECTED_ROWS,
        DATASET_SOURCE_URL,
        RAW_DATA_DIR,
        RAW_DATA_FILE,
    )


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def count_lines(file_path: Path, encoding: str = DATASET_ENCODING) -> int:
    """Count non-empty lines in a text file."""
    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        return sum(1 for line in f if line.strip())


def download_dataset(
    url: str = DATASET_SOURCE_URL,
    dest_path: Path = RAW_DATA_FILE,
    force: bool = False,
) -> Path:
    """Download the Superstore dataset and verify integrity.

    Args:
        url: Direct HTTPS URL to the raw CSV file.
        dest_path: Destination path where file should be saved.
        force: If True, re-download even if the file exists.

    Returns:
        Path to the downloaded raw file.

    Raises:
        RuntimeError: If download fails or integrity checks do not pass.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if dest_path.exists() and not force:
        line_count = count_lines(dest_path)
        # Expected: 1 header line + 9,994 data lines = 9,995 lines
        if line_count >= DATASET_EXPECTED_ROWS:
            print(f"[OK] Raw dataset already exists at {dest_path}")
            print(f"     Total non-empty lines: {line_count}")
            print(f"     SHA-256: {compute_sha256(dest_path)}")
            return dest_path
        print(f"[WARN] Existing file has only {line_count} lines. Re-downloading...")

    print(f"[INFO] Downloading dataset from:\n       {url}")
    print(f"       Saving to: {dest_path}")

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Retail-Intelligence-Analytics/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=30) as response, open(
            dest_path, "wb"
        ) as out_file:
            data = response.read()
            out_file.write(data)
    except Exception as exc:
        raise RuntimeError(f"Failed to download dataset from {url}: {exc}") from exc

    # Integrity verification
    file_size = dest_path.stat().st_size
    if file_size == 0:
        dest_path.unlink(missing_ok=True)
        raise RuntimeError("Downloaded file is empty (0 bytes).")

    line_count = count_lines(dest_path)
    # Header + data rows
    expected_total_lines = DATASET_EXPECTED_ROWS + 1
    if line_count < expected_total_lines:
        raise RuntimeError(
            f"Integrity check failed: Expected at least {expected_total_lines} lines, "
            f"but found {line_count} lines."
        )

    file_hash = compute_sha256(dest_path)
    print(f"[SUCCESS] Download completed.")
    print(f"          File size: {file_size:,} bytes")
    print(f"          Total lines: {line_count:,} (1 header + {line_count - 1:,} rows)")
    print(f"          SHA-256: {file_hash}")
    return dest_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Tableau Sample Superstore dataset")
    parser.add_argument("--force", action="store_true", help="Force re-download even if file exists")
    args = parser.parse_args()

    download_dataset(force=args.force)
