"""
download_diag.py — Download GSI netCDF diagnostic files.

Downloads one or more GSI conventional diagnostic files from a remote
URL into a local output directory.  The remote base URL and output
directory can be supplied as arguments or read from the environment
variable ``DIAG_BASE_URL``.

File-naming convention expected on the server::

    <base_url>/diag_conv_<variable>_<ftype>.<YYYYMMDDHH>.nc4

where ``<variable>`` is one of ``t``, ``q``, ``uv``, ``ps`` and
``<ftype>`` is ``ges`` (first guess) or ``anl`` (analysis).

Usage (CLI)::

    python scripts/download_diag.py \\
        --date 2020092000 \\
        --variables t q uv \\
        --ftypes ges anl \\
        --base-url https://example.com/gsi_diags \\
        --outdir ./data

Usage (library)::

    from scripts.download_diag import download_diag_files
    paths = download_diag_files(
        date="2020092000",
        variables=["t", "q", "uv"],
        ftypes=["ges", "anl"],
        base_url="https://example.com/gsi_diags",
        outdir="./data",
    )
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence
from urllib.parse import urljoin
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

_VALID_VARIABLES: tuple[str, ...] = ("t", "q", "uv", "ps")
_VALID_FTYPES: tuple[str, ...] = ("ges", "anl")
_CHUNK_BYTES: int = 65536  # 64 KiB read chunk


def build_filename(variable: str, ftype: str, date: str) -> str:
    """Return the canonical GSI diagnostic file name.

    Parameters
    ----------
    variable:
        Observed quantity: ``'t'``, ``'q'``, ``'uv'``, or ``'ps'``.
    ftype:
        File type: ``'ges'`` (first-guess/background) or ``'anl'``
        (analysis).
    date:
        Cycle date-time string in ``YYYYMMDDHH`` format,
        e.g. ``'2020092000'``.

    Returns
    -------
    str
        File name, e.g. ``'diag_conv_t_ges.2020092000.nc4'``.

    Examples
    --------
    >>> build_filename('t', 'ges', '2020092000')
    'diag_conv_t_ges.2020092000.nc4'
    """
    if variable not in _VALID_VARIABLES:
        raise ValueError(
            f"variable '{variable}' is not valid. "
            f"Choose from: {', '.join(_VALID_VARIABLES)}"
        )
    if ftype not in _VALID_FTYPES:
        raise ValueError(
            f"ftype '{ftype}' is not valid. "
            f"Choose from: {', '.join(_VALID_FTYPES)}"
        )
    return f"diag_conv_{variable}_{ftype}.{date}.nc4"


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
    variables: Sequence[str] = ("t", "q", "uv"),
    ftypes: Sequence[str] = ("ges", "anl"),
    base_url: str | None = None,
    outdir: str | Path = ".",
    skip_existing: bool = True,
) -> dict[str, Path]:
    """Download a set of GSI conventional diagnostic files.

    Parameters
    ----------
    date:
        Cycle date-time in ``YYYYMMDDHH`` format, e.g. ``'2020092000'``.
    variables:
        Sequence of variable codes to download.  Valid values are
        ``'t'``, ``'q'``, ``'uv'``, and ``'ps'``.
        Defaults to ``('t', 'q', 'uv')``.
    ftypes:
        Sequence of file types to download: ``'ges'`` and/or ``'anl'``.
        Defaults to ``('ges', 'anl')``.
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
    dict[str, pathlib.Path]
        Mapping of ``'<variable>_<ftype>'`` keys to local file paths
        for every successfully downloaded file.

    Raises
    ------
    ValueError
        If *base_url* is not provided and ``DIAG_BASE_URL`` is unset
        or empty.

    Examples
    --------
    >>> paths = download_diag_files(
    ...     date="2020092000",
    ...     variables=["t", "q", "uv"],
    ...     ftypes=["ges", "anl"],
    ...     base_url="https://example.com/gsi_diags",
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

    downloaded: dict[str, Path] = {}

    for variable in variables:
        for ftype in ftypes:
            filename = build_filename(variable, ftype, date)
            dest = outdir / filename
            key = f"{variable}_{ftype}"

            if skip_existing and dest.exists() and dest.stat().st_size > 0:
                print(f"[skip]     {filename}  (already present)")
                downloaded[key] = dest
                continue

            url = urljoin(base_url, filename)
            print(f"[download] {url} -> {dest}")
            try:
                download_file(url, dest)
                downloaded[key] = dest
                print(f"[ok]       {filename}")
            except (HTTPError, URLError, OSError) as exc:
                print(f"[error]    {filename}: {exc}", file=sys.stderr)

    return downloaded


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download GSI conventional diagnostic netCDF4 files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--date",
        required=True,
        metavar="YYYYMMDDHH",
        help="Cycle date-time string (e.g. 2020092000).",
    )
    parser.add_argument(
        "--variables",
        nargs="+",
        default=["t", "q", "uv"],
        choices=list(_VALID_VARIABLES),
        metavar="VAR",
        help="Variable codes to download.",
    )
    parser.add_argument(
        "--ftypes",
        nargs="+",
        default=["ges", "anl"],
        choices=list(_VALID_FTYPES),
        metavar="FTYPE",
        help="File types: 'ges' (first guess) and/or 'anl' (analysis).",
    )
    parser.add_argument(
        "--base-url",
        default=None,
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
            variables=args.variables,
            ftypes=args.ftypes,
            base_url=args.base_url,
            outdir=args.outdir,
            skip_existing=args.skip_existing,
        )
    except ValueError as exc:
        print(f"FATAL ERROR: {exc}", file=sys.stderr)
        return 1

    expected = len(args.variables) * len(args.ftypes)
    if len(paths) < expected:
        print(
            f"WARNING: {expected - len(paths)} file(s) could not be downloaded.",
            file=sys.stderr,
        )
        return 1

    print(f"\nAll {len(paths)} file(s) ready in '{args.outdir}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
