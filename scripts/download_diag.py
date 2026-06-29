"""
download_diag.py — Download and extract GSI tarred diagnostic files.

Downloads a GSI conventional diagnostic tar file from a remote
URL into a local output directory, and extracts it. The remote base URL and output
directory can be supplied as arguments or read from the environment
variable ``DIAG_BASE_URL``.

File-naming convention expected on the server::

    <base_url>/gdas.t<HH>z.cnvstat

where ``<HH>`` is the cycle hour (e.g. 00).

Usage (CLI)::

    python scripts/download_diag.py \
        --date 2026062900 \
        --base-url http://www.emc.ncep.noaa.gov/users/cmartin/cadre \
        --outdir ./data

Usage (library)::

    from scripts.download_diag import download_diag_files
    paths = download_diag_files(
        date="2026062900",
        base_url="http://www.emc.ncep.noaa.gov/users/cmartin/cadre",
        outdir="./data",
    )
"""

from __future__ import annotations

import argparse
import os
import sys
import tarfile
import gzip
import shutil
from pathlib import Path
from typing import Sequence
from urllib.parse import urljoin
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

_CHUNK_BYTES: int = 65536  # 64 KiB read chunk


def build_filename(date: str) -> str:
    """Return the canonical GSI diagnostic file name.

    Parameters
    ----------
    date:
        Cycle date-time string in ``YYYYMMDDHH`` format,
        e.g. ``'2026062900'``.

    Returns
    -------
    str
        File name, e.g. ``'gdas.t00z.cnvstat'``.

    Examples
    --------
    >>> build_filename('2026062900')
    'gdas.t00z.cnvstat'
    """
    hh = date[-2:]
    return f"gdas.t{hh}z.cnvstat"


def download_file(url: str, dest: Path) -> Path:
    """Stream a single file from *url* and save it to *dest*.

    Parameters
    ----------
    url:
        Fully-qualified URL of the remote file.
    dest:
        Local :class:`pathlib.Path` where the file will be written.
        Parent directories must already exist.

    Returns
    -------
    pathlib.Path
        Resolved path to the downloaded file.

    Raises
    ------
    HTTPError
        If the server returns a non-200 HTTP status code.
    URLError
        If a network-level error occurs (DNS failure, timeout, etc.).
    OSError
        If the local file cannot be written.
    """
    dest = dest.resolve()
    try:
        with urlopen(url) as response, open(dest, "wb") as fh:
            while True:
                chunk = response.read(_CHUNK_BYTES)
                if not chunk:
                    break
                fh.write(chunk)
    except HTTPError as exc:
        raise HTTPError(
            url, exc.code, f"HTTP {exc.code} downloading {url}", exc.headers, None
        ) from exc
    except URLError as exc:
        raise URLError(f"Network error downloading {url}: {exc.reason}") from exc
    return dest


def download_diag_files(
    date: str,
    base_url: str | None = None,
    outdir: str | Path = ".",
    skip_existing: bool = True,
) -> list[Path]:
    """Download a set of GSI conventional diagnostic files.

    Parameters
    ----------
    date:
        Cycle date-time in ``YYYYMMDDHH`` format, e.g. ``'2026062900'``.
    base_url:
        Base URL of the remote file server.  If *None*, the value of
        the ``DIAG_BASE_URL`` environment variable is used.  A
        trailing slash is added automatically when absent.
    outdir:
        Local directory where files are saved.  Created if it does not
        exist.
    skip_existing:
        If *True* (default), skip downloading a file that already
        exists locally with a non-zero size.

    Returns
    -------
    list[pathlib.Path]
        List of paths to the extracted files.

    Raises
    ------
    ValueError
        If *base_url* is not provided and ``DIAG_BASE_URL`` is unset
        or empty.

    Examples
    --------
    >>> paths = download_diag_files(
    ...     date="2026062900",
    ...     base_url="http://www.emc.ncep.noaa.gov/users/cmartin/cadre",
    ...     outdir="./data",
    ... )
    """
    if base_url is None:
        base_url = os.environ.get("DIAG_BASE_URL", "")
    if not base_url:
        raise ValueError(
            "A base URL must be supplied via the 'base_url' argument "
            "or the 'DIAG_BASE_URL' environment variable."
        )

    # Ensure trailing slash so urljoin behaves correctly.
    if not base_url.endswith("/"):
        base_url = base_url + "/"

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    filename = build_filename(date)
    dest = outdir / filename

    if skip_existing and dest.exists() and dest.stat().st_size > 0:
        print(f"[skip]     {filename}  (already present)")
    else:
        url = urljoin(base_url, filename)
        print(f"[download] {url} -> {dest}")
        try:
            download_file(url, dest)
            print(f"[ok]       {filename}")
        except (HTTPError, URLError, OSError) as exc:
            print(f"[error]    {filename}: {exc}", file=sys.stderr)
            return []

    # Extract the tar file
    print(f"[extract]  {dest} -> {outdir}")
    extracted_paths = []
    try:
        with tarfile.open(dest, "r") as tar:
            tar.extractall(path=outdir)
            for member in tar.getmembers():
                member_path = outdir / member.name
                if member_path.suffix == ".gz":
                    # Gunzip the file
                    uncompressed_path = member_path.with_suffix("")
                    print(f"[gunzip]   {member_path.name} -> {uncompressed_path.name}")
                    with gzip.open(member_path, "rb") as f_in:
                        with open(uncompressed_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    member_path.unlink()  # Remove the .gz file after extraction
                    extracted_paths.append(uncompressed_path)
                else:
                    extracted_paths.append(member_path)
        print(f"[ok]       Extracted {len(extracted_paths)} files")
    except (tarfile.TarError, OSError) as exc:
        print(f"[error]    Extracting {filename}: {exc}", file=sys.stderr)

    return extracted_paths


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download and extract GSI conventional diagnostic tar files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--date",
        required=True,
        metavar="YYYYMMDDHH",
        help="Cycle date-time string (e.g. 2026062900).",
    )
    parser.add_argument(
        "--base-url",
        default="http://www.emc.ncep.noaa.gov/users/cmartin/cadre",
        metavar="URL",
        help=(
            "Base URL of the remote server.  Falls back to the "
            "DIAG_BASE_URL environment variable."
        ),
    )
    parser.add_argument(
        "--outdir",
        default=".",
        metavar="DIR",
        help="Local directory where downloaded files are saved.",
    )
    parser.add_argument(
        "--no-skip-existing",
        dest="skip_existing",
        action="store_false",
        default=True,
        help="Re-download files that already exist locally.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point.

    Parameters
    ----------
    argv:
        Argument list; defaults to ``sys.argv[1:]`` when *None*.

    Returns
    -------
    int
        Exit code: 0 on success, 1 if any download failed.
    """
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    try:
        paths = download_diag_files(
            date=args.date,
            base_url=args.base_url,
            outdir=args.outdir,
            skip_existing=args.skip_existing,
        )
    except ValueError as exc:
        print(f"FATAL ERROR: {exc}", file=sys.stderr)
        return 1

    if not paths:
        print(
            "WARNING: The file could not be downloaded or extracted.",
            file=sys.stderr,
        )
        return 1

    print(f"\nExtracted {len(paths)} file(s) into '{args.outdir}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
