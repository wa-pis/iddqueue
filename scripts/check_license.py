"""Check built wheel/sdist license text and metadata (stdlib only)."""

import argparse
import hashlib
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

# LICENSE at upstream commit 80b1a490d0a494925a9f8be399a11b38cee5480a.
UPSTREAM_SHA256 = "80dd78e1fddd57202f52dd81a24ecd5bb2011df8970a8fddb6f604dc5fbfe0f8"


def check(artifact, expected):
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as archive:
            files = {name: archive.read(name) for name in archive.namelist()
                     if name.endswith(("/LICENSE", "/METADATA"))}
        metadata_suffix = "/METADATA"
    else:
        with tarfile.open(artifact) as archive:
            files = {member.name: archive.extractfile(member).read()
                     for member in archive.getmembers() if member.isfile()
                     and member.name.endswith(("/LICENSE", "/PKG-INFO"))}
        metadata_suffix = "/PKG-INFO"
    licenses = [data for name, data in files.items() if name.endswith("/LICENSE")]
    if not licenses or any(data != expected for data in licenses):
        raise ValueError(f"{artifact}: missing or altered LICENSE")
    metadata = [data for name, data in files.items() if name.endswith(metadata_suffix)]
    if not metadata or any((BytesParser().parsebytes(data).get("License-Expression")
                               or BytesParser().parsebytes(data).get("License")) != "PostgreSQL"
                           for data in metadata):
        raise ValueError(f"{artifact}: PostgreSQL license metadata missing")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", nargs="+", type=Path)
    args = parser.parse_args()
    expected = (Path(__file__).resolve().parents[1] / "LICENSE").read_bytes()
    if hashlib.sha256(expected).hexdigest() != UPSTREAM_SHA256:
        raise ValueError("Source LICENSE differs from preserved upstream text")
    for artifact in args.artifacts:
        check(artifact, expected)
        print(f"License verified: {artifact}")


if __name__ == "__main__":
    main()
