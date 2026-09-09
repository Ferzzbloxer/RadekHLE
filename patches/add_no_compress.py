#!/usr/bin/env python3
"""
Adds `aaptOptions { noCompress "ipa" }` inside the `android { ... }` block of
a Gradle build file, so the packager doesn't try to re-compress the bundled
.ipa (which is itself a zip) and corrupt it.

Conservative by design: if it can't find `android {`, it exits with an
error rather than guessing where to insert the block.

Usage: python3 add_no_compress.py <path/to/build.gradle>
"""
import re
import sys

SNIPPET = '\n    aaptOptions {\n        noCompress "ipa"\n    }\n'

ANDROID_BLOCK_RE = re.compile(r"(android\s*\{)")


def main():
    if len(sys.argv) != 2:
        print("Usage: add_no_compress.py <path/to/build.gradle>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if 'noCompress "ipa"' in content or "noCompress 'ipa'" in content:
        print(f"[add_no_compress] {path} already has noCompress for ipa, skipping.")
        return

    match = ANDROID_BLOCK_RE.search(content)
    if not match:
        print(
            "[add_no_compress] ERROR: couldn't find an `android {` block in this file. "
            "Add `aaptOptions { noCompress \"ipa\" }` inside the android block manually.",
            file=sys.stderr,
        )
        sys.exit(2)

    insert_at = match.end()
    patched = content[:insert_at] + SNIPPET + content[insert_at:]

    with open(path, "w", encoding="utf-8") as f:
        f.write(patched)

    print(f"[add_no_compress] Patched {path} successfully.")


if __name__ == "__main__":
    main()
