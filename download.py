#!/usr/bin/env python3
"""Download vanilla Minecraft resources for Horizon from Mojang's official CDN."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
import urllib.error
import urllib.request

MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
USER_AGENT = "horizon-resource-downloader/1.0"


class DownloadError(RuntimeError):
    pass


class Progress:
    def __init__(self, total_files: int, total_bytes: int) -> None:
        self.total_files = total_files
        self.total_bytes = total_bytes
        self.files = 0
        self.bytes = 0
        self.skipped = 0
        self.lock = threading.Lock()
        self.last_draw = 0.0
        self.is_tty = sys.stderr.isatty()

    def advance(self, amount: int) -> None:
        with self.lock:
            self.bytes += amount
            self._draw()

    def finish_file(self, skipped: bool = False) -> None:
        with self.lock:
            self.files += 1
            if skipped:
                self.skipped += 1
            self._draw(force=True)

    def _draw(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self.last_draw < 0.1:
            return
        self.last_draw = now
        mib = self.bytes / 1024 / 1024
        total_mib = self.total_bytes / 1024 / 1024
        percent = 100 * self.bytes / self.total_bytes if self.total_bytes else 100
        line = (
            f"\r{percent:6.2f}%  {mib:8.1f}/{total_mib:.1f} MiB  "
            f"files {self.files}/{self.total_files}  cached {self.skipped}"
        )
        end = "" if self.is_tty else "\n"
        print(line, end=end, file=sys.stderr, flush=True)

    def close(self) -> None:
        with self.lock:
            self._draw(force=True)
            if self.is_tty:
                print(file=sys.stderr)


def request(url: str, offset: int = 0) -> urllib.request.addinfourl:
    headers = {"User-Agent": USER_AGENT}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=headers), timeout=45
    )


def fetch_json(url: str, attempts: int = 4) -> dict:
    for attempt in range(1, attempts + 1):
        try:
            with request(url) as response:
                return json.load(response)
        except (OSError, ValueError, urllib.error.URLError) as exc:
            if attempt == attempts:
                raise DownloadError(f"Cannot fetch {url}: {exc}") from exc
            time.sleep(attempt)
    raise AssertionError("unreachable")


def valid_file(path: Path, sha1: str, size: int) -> bool:
    if not path.is_file() or path.stat().st_size != size:
        return False
    digest = hashlib.sha1()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest() == sha1


def download(
    url: str,
    destination: Path,
    sha1: str,
    size: int,
    progress: Progress | None = None,
    attempts: int = 4,
) -> bool:
    """Download and verify one file. Return True when an existing file was reused."""
    if valid_file(destination, sha1, size):
        if progress:
            progress.advance(size)
            progress.finish_file(skipped=True)
        return True

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")

    reported = 0
    for attempt in range(1, attempts + 1):
        offset = partial.stat().st_size if partial.exists() else 0
        if offset > size:
            partial.unlink()
            offset = 0
        try:
            with request(url, offset) as response:
                # A server may ignore Range; never append the full response then.
                append = offset > 0 and response.status == 206
                mode = "ab" if append else "wb"
                if not append:
                    offset = 0
                    if progress and reported:
                        progress.advance(-reported)
                        reported = 0
                digest = hashlib.sha1()
                if append:
                    with partial.open("rb") as old_file:
                        for block in iter(lambda: old_file.read(1024 * 1024), b""):
                            digest.update(block)
                with partial.open(mode) as file:
                    while True:
                        block = response.read(256 * 1024)
                        if not block:
                            break
                        file.write(block)
                        digest.update(block)
                        reported += len(block)
                        if progress:
                            progress.advance(len(block))

            if partial.stat().st_size != size:
                raise DownloadError(
                    f"Wrong size for {destination.name}: "
                    f"{partial.stat().st_size}, expected {size}"
                )
            if digest.hexdigest() != sha1:
                partial.unlink()
                raise DownloadError(f"SHA-1 mismatch for {destination.name}")
            os.replace(partial, destination)
            if progress:
                progress.finish_file()
            return False
        except (OSError, urllib.error.URLError, DownloadError) as exc:
            if attempt == attempts:
                if progress:
                    # Failed bytes must not remain in the overall progress total.
                    progress.advance(-reported)
                raise DownloadError(f"Failed to download {url}: {exc}") from exc
            time.sleep(attempt)
    raise AssertionError("unreachable")


def default_minecraft_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "minecraft"
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", Path.home())) / ".minecraft"
    return Path.home() / ".minecraft"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download official Minecraft Java resources for Horizon."
    )
    parser.add_argument("--version", default="26.3", help="Minecraft version (default: 26.3)")
    parser.add_argument("--dir", type=Path, default=default_minecraft_dir(), help="Minecraft folder")
    parser.add_argument("--jobs", type=int, default=8, help="Parallel downloads (default: 8)")
    parser.add_argument("--dry-run", action="store_true", help="Show the download size only")
    args = parser.parse_args()
    if args.jobs < 1 or args.jobs > 32:
        parser.error("--jobs must be between 1 and 32")
    return args


def main() -> int:
    args = parse_args()
    try:
        manifest = fetch_json(MANIFEST_URL)
        versions = {entry["id"]: entry for entry in manifest["versions"]}
        if args.version not in versions:
            latest = manifest["latest"]["release"]
            raise DownloadError(
                f"Version {args.version!r} was not found. Latest release: {latest}"
            )

        version_url = versions[args.version]["url"]
        version_meta = fetch_json(version_url)
        client = version_meta["downloads"]["client"]
        asset_index = version_meta["assetIndex"]
        version_id = version_meta["id"]
        root = args.dir.expanduser().resolve()

        tasks = [
            (
                client["url"],
                root / "versions" / version_id / f"{version_id}.jar",
                client["sha1"],
                client["size"],
            ),
            (
                asset_index["url"],
                root / "assets" / "indexes" / f"{asset_index['id']}.json",
                asset_index["sha1"],
                asset_index["size"],
            ),
        ]
        # Save metadata too, so other launchers can recognize the installation.
        metadata_path = root / "versions" / version_id / f"{version_id}.json"

        index_meta = fetch_json(asset_index["url"])
        for name, item in index_meta["objects"].items():
            object_hash = item["hash"]
            tasks.append(
                (
                    f"https://resources.download.minecraft.net/{object_hash[:2]}/{object_hash}",
                    root / "assets" / "objects" / object_hash[:2] / object_hash,
                    object_hash,
                    item["size"],
                )
            )

        total_bytes = sum(task[3] for task in tasks)
        print(f"Minecraft {version_id}: {len(tasks)} files, {total_bytes / 1024**3:.2f} GiB")
        print(f"Destination: {root}")
        if args.dry_run:
            print("Dry run: nothing was downloaded.")
            return 0

        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = metadata_path.with_suffix(".json.part")
        temporary.write_text(json.dumps(version_meta, indent=2), encoding="utf-8")
        os.replace(temporary, metadata_path)

        progress = Progress(len(tasks), total_bytes)
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
                futures = [pool.submit(download, *task, progress) for task in tasks]
                for future in concurrent.futures.as_completed(futures):
                    future.result()
        finally:
            progress.close()

        print("\nDone. All files passed SHA-1 verification.")
        print(f"Open Horizon → Play → Prepare and select: {root}")
        return 0
    except DownloadError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled. Complete files are kept; rerun to resume.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
