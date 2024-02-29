#!/bin/env python3
import argparse
import json
import re
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Pkgbuild:
    path: Path
    text: str
    data: dict[str, Any]
    current_version: str
    new_version: str

    def check_update(self):
        return self.current_version != self.new_version

    def update_pkgbuild(self):
        assets = {
            asset["name"]: asset
            for asset in self.data["assets"]
            if "linux-gnu" in asset["name"]
        }

        shas = {}
        for arch in ("aarch64", "i686", "x86_64"):
            for name, asset in assets.items():
                if arch in name and name.endswith(".tar.gz.sha256"):
                    response = urllib.request.urlopen(asset["browser_download_url"])
                    shas[arch] = response.readlines()[0].split()[0].decode("utf-8")
                    break

        out = self.text
        out = re.sub(r"(_pkgver=)(.*)", rf"\g<1>{self.new_version}", out)
        out = re.sub(r"(pkgrel=)(\d*)", r"\g<1>1", out)

        for arch, sha in shas.items():
            out = re.sub(rf"(sha256sums_{arch}=)\('(.*)'\)", rf"\g<1>('{sha}')", out)

        self.path.write_text(out)

        print(f"Updated {self.path} from {self.current_version} to {self.new_version}")

        self.update_srcinfo()

    def update_srcinfo(self):
        srcinfo = self.path.parent / ".SRCINFO"
        res = subprocess.check_output(
            ["makepkg", "--printsrcinfo"], cwd=self.path.parent
        )
        srcinfo.write_text(res.decode("utf-8"))

        print("Updated .SRCINFO")

    @classmethod
    def from_path(cls, path: Path):
        text = path.read_text()

        url = re.search(r"_release_url='(.*)'", text)

        if not url:
            raise ValueError("No release URL found")

        url = url.group(1)

        response = urllib.request.urlopen(url)

        data = json.load(response)

        current_version = re.search(r"pkgver=(.*)", text)

        if not current_version:
            raise ValueError("No current version found")

        current_version = current_version.group(1)

        new_version = data["tag_name"]

        return Pkgbuild(path, text, data, current_version, new_version)


def main(path, check):
    pkgbuild = Pkgbuild.from_path(path)

    if not pkgbuild.check_update():
        return False

    if check:
        return True

    pkgbuild.update_pkgbuild()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update PKGBUILD")
    parser.add_argument("path", type=Path, help="Path to package directory")
    parser.add_argument("--check", action="store_true", help="Check for updates")
    parser.add_argument(
        "--repo",
        action="store_true",
        help="Directory is repository of packages, not a single package",
    )
    parser.add_argument(
        "--skip", nargs="+", help="Names of packages to skip", default=["dura-git"]
    )

    args = parser.parse_args()

    paths = (
        Path(args.path).glob("*/PKGBUILD")
        if args.repo
        else [Path(args.path) / "PKGBUILD"]
    )

    out = []
    for path in paths:
        if path.parent.name in args.skip:
            continue
        res = main(path, check=args.check)
        if res:
            out.append(str(path.parent))

    if args.check:
        print(json.dumps({"include": [{"package": p} for p in out]}))
