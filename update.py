import subprocess
import json
import re
from typing import Any
import urllib.request
from pathlib import Path
from dataclasses import dataclass


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

        out = re.sub(r"(_pkgver=)(.*)", rf"\g<1>{self.new_version}", self.text)

        for arch, sha in shas.items():
            out = re.sub(rf"(sha256sums_{arch}=)\('(.*)'\)", rf"\g<1>('{sha}')", out)

        self.path.write_text(out)

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


if __name__ == "__main__":
    pkgbuild = Pkgbuild.from_path(Path("PKGBUILD"))
    if not pkgbuild.check_update():
        print(f"{pkgbuild.path.absolute()} is already up to date")
        exit(0)

    pkgbuild.update_pkgbuild()

    print(
        f"Updated {pkgbuild.path.absolute()} from {pkgbuild.current_version} "
        f"to {pkgbuild.new_version}"
    )

    srcinfo = subprocess.check_output(["makepkg", "--printsrcinfo"])

    Path(".SRCINFO").write_text(srcinfo.decode("utf-8"))

    print("Updated .SRCINFO")
