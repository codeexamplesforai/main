#!/usr/bin/env python3
"""Build an inventory of S3 file arrival timestamps for the CM_CBK folder tree.

The bucket follows this layout (all top-level prefixes start with ``CM_CBK``):

    <bucket>/CM_CBK*/YYYYMMDD/CONTROL_FILE_YYYYMMDD.parquet
    <bucket>/CM_CBK<3-char country>/YYYYMMDD/IVISION_PAYMENTS_<3-char region>_YYYYMMDD.xml
    <bucket>/CM_CBK<2-char BU>/YYYYMMDD/PMT_CMR_DATAHUB_AML1_<2-char bu>_<YYYYMMDD>_<HHMISS>.xml

For every object whose date folder falls in the requested ``YYYYMMDD`` window
(default 20260501-20260531) we record:

  * the S3 object key
  * the top-level prefix (e.g. CM_CBK_USA)
  * the YYYYMMDD date folder parsed from the path
  * the file type (parquet / ivision_payments / pmt_cmr_datahub / other)
  * the code embedded in the filename -- the 3-char region in
    IVISION_PAYMENTS_<region>_... or the 2-char BU in PMT_CMR_DATAHUB_AML1_<bu>_...
  * the HHMISS timestamp embedded in the PMT_CMR_DATAHUB filename, if present
  * the S3 ``LastModified`` date and time -- i.e. when the file actually landed
  * the object size in bytes

Works against AWS S3 *and* on-prem S3-compatible stores (MinIO, Ceph/RGW,
Dell ECS, NetApp StorageGRID, ...) -- pass --endpoint-url plus credentials.

Usage (on-prem):
    python s3_inventory.py \
        --bucket my-bucket \
        --endpoint-url https://s3.internal.example.com:9000 \
        --access-key AKID --secret-key SECRET \
        --region us-east-1

Credentials may also be supplied via the standard environment variables
(AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY) instead of CLI flags, which keeps
secrets out of your shell history.

Usage (AWS):
    python s3_inventory.py --bucket my-bucket --start 20260501 --end 20260531
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

# Matches an 8-digit YYYYMMDD path segment between two slashes.
DATE_FOLDER_RE = re.compile(r"/(?P<date>\d{8})/")

# IVISION_PAYMENTS_<3-char region>_<YYYYMMDD>.xml
IVISION_CODE_RE = re.compile(
    r"^IVISION_PAYMENTS_(?P<code>[A-Za-z0-9]{3})_\d{8}\.xml$", re.IGNORECASE
)

# PMT_CMR_DATAHUB_AML1_<2-char bu>_<YYYYMMDD>_<HHMISS>.xml
PMT_RE = re.compile(
    r"^PMT_CMR_DATAHUB_AML1_(?P<code>[A-Za-z0-9]{2})_\d{8}_(?P<time>\d{6})\.xml$",
    re.IGNORECASE,
)

DATE_FMT = "%Y%m%d"


@dataclass(frozen=True)
class InventoryRow:
    """A single inventoried S3 object. Immutable by design."""

    key: str
    top_prefix: str
    date_folder: str
    file_type: str
    filename_code: str
    filename_time: str
    last_modified_date: str
    last_modified_time: str
    size_bytes: int


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", required=True, help="S3 bucket name")
    parser.add_argument(
        "--prefix",
        default="CM_CBK",
        help="Top-level key prefix to scan (default: CM_CBK)",
    )
    parser.add_argument(
        "--start",
        default="20260501",
        help="Inclusive start date folder, YYYYMMDD (default: 20260501)",
    )
    parser.add_argument(
        "--end",
        default="20260531",
        help="Inclusive end date folder, YYYYMMDD (default: 20260531)",
    )
    parser.add_argument(
        "--out",
        default="cm_cbk_inventory.csv",
        help="Output CSV path (default: cm_cbk_inventory.csv)",
    )
    parser.add_argument(
        "--endpoint-url",
        default=os.environ.get("S3_ENDPOINT_URL"),
        help="On-prem S3 endpoint, e.g. https://s3.internal.example.com:9000 "
        "(or set S3_ENDPOINT_URL). Omit for AWS.",
    )
    parser.add_argument(
        "--access-key",
        default=os.environ.get("AWS_ACCESS_KEY_ID"),
        help="Access key id (default: AWS_ACCESS_KEY_ID env var)",
    )
    parser.add_argument(
        "--secret-key",
        default=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        help="Secret access key (default: AWS_SECRET_ACCESS_KEY env var)",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Optional named AWS/credentials profile to use",
    )
    parser.add_argument(
        "--region",
        default=os.environ.get("AWS_DEFAULT_REGION"),
        help="Region name (default: AWS_DEFAULT_REGION env var)",
    )
    parser.add_argument(
        "--ca-bundle",
        default=os.environ.get("AWS_CA_BUNDLE"),
        help="Path to a CA bundle for the on-prem endpoint's TLS cert. "
        "PREFERRED way to trust a self-signed/internal cert "
        "(or set AWS_CA_BUNDLE).",
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="INSECURE last resort: disable TLS verification entirely. "
        "Exposes traffic (incl. credentials) to MITM. Prefer --ca-bundle.",
    )
    parser.add_argument(
        "--addressing-style",
        choices=("path", "virtual", "auto"),
        default="path",
        help="S3 addressing style; on-prem stores usually need 'path' (default)",
    )
    return parser.parse_args(argv)


def validate_date(value: str, label: str) -> date:
    """Parse a YYYYMMDD string, failing fast with a clear message."""
    try:
        return datetime.strptime(value, DATE_FMT).date()
    except ValueError as exc:
        raise SystemExit(f"Invalid {label} date {value!r}: expected YYYYMMDD") from exc


def parse_filename(key: str) -> tuple[str, str, str]:
    """Classify a key and pull the embedded code/time from its filename.

    Returns ``(file_type, code, time)`` where ``code`` is the 3-char region
    (IVISION) or 2-char BU (PMT), and ``time`` is the PMT HHMISS. Empty
    strings when not applicable.
    """
    name = key.rsplit("/", 1)[-1]
    upper = name.upper()

    if upper.startswith("CONTROL_FILE_") and upper.endswith(".PARQUET"):
        return "parquet", "", ""

    ivision = IVISION_CODE_RE.match(name)
    if ivision:
        return "ivision_payments", ivision.group("code").upper(), ""

    pmt = PMT_RE.match(name)
    if pmt:
        return "pmt_cmr_datahub", pmt.group("code").upper(), pmt.group("time")

    return "other", "", ""


def date_folder_in_range(date_folder: str, start: date, end: date) -> bool:
    try:
        parsed = datetime.strptime(date_folder, DATE_FMT).date()
    except ValueError:
        return False
    return start <= parsed <= end


def top_prefix_of(key: str) -> str:
    """First path segment (the CM_CBK_* business-unit/country prefix)."""
    return key.split("/", 1)[0]


def iter_objects(s3_client, bucket: str, prefix: str):
    """Yield every object dict under prefix, transparently paginating."""
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            yield obj


def build_inventory(
    s3_client, bucket: str, prefix: str, start: date, end: date
) -> list[InventoryRow]:
    rows: list[InventoryRow] = []
    for obj in iter_objects(s3_client, bucket, prefix):
        key = obj["Key"]

        # Skip "folder" placeholder keys.
        if key.endswith("/"):
            continue

        match = DATE_FOLDER_RE.search("/" + key)
        if not match:
            continue

        date_folder = match.group("date")
        if not date_folder_in_range(date_folder, start, end):
            continue

        file_type, filename_code, filename_time = parse_filename(key)
        last_modified: datetime = obj["LastModified"]
        rows.append(
            InventoryRow(
                key=key,
                top_prefix=top_prefix_of(key),
                date_folder=date_folder,
                file_type=file_type,
                filename_code=filename_code,
                filename_time=filename_time,
                last_modified_date=last_modified.strftime("%Y-%m-%d"),
                last_modified_time=last_modified.strftime("%H:%M:%S %Z").strip(),
                size_bytes=obj.get("Size", 0),
            )
        )
    return rows


def write_csv(rows: list[InventoryRow], out_path: str) -> None:
    fieldnames = list(InventoryRow.__annotations__.keys())
    with open(out_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    start = validate_date(args.start, "start")
    end = validate_date(args.end, "end")
    if start > end:
        raise SystemExit(f"--start {args.start} must not be after --end {args.end}")

    session = boto3.Session(
        aws_access_key_id=args.access_key,
        aws_secret_access_key=args.secret_key,
        profile_name=args.profile,
        region_name=args.region,
    )

    # path-style addressing + an explicit signature version is what most
    # on-prem S3 gateways expect; harmless against AWS too.
    client_config = Config(s3={"addressing_style": args.addressing_style})

    # Prefer trusting a custom CA bundle over disabling verification.
    # verify=False is a documented escape hatch but exposes traffic to MITM.
    verify: bool | str
    if args.ca_bundle:
        verify = args.ca_bundle
    elif args.no_verify_ssl:
        print(
            "WARNING: TLS verification disabled (--no-verify-ssl). Traffic, "
            "including your credentials, is exposed to interception. "
            "Add your internal CA via --ca-bundle instead.",
            file=sys.stderr,
        )
        verify = False
    else:
        verify = True

    s3_client = session.client(
        "s3",
        endpoint_url=args.endpoint_url,
        config=client_config,
        verify=verify,
    )

    try:
        rows = build_inventory(s3_client, args.bucket, args.prefix, start, end)
    except (BotoCoreError, ClientError) as exc:
        print(f"ERROR: S3 listing failed: {exc}", file=sys.stderr)
        return 1

    rows.sort(key=lambda r: (r.top_prefix, r.date_folder, r.key))
    write_csv(rows, args.out)

    print(
        f"Inventoried {len(rows)} object(s) under "
        f"s3://{args.bucket}/{args.prefix} for {args.start}-{args.end}"
    )
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
