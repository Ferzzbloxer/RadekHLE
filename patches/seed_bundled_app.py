#!/usr/bin/env python3
"""
Injects a first-run "seed the bundled game into touchHLE_apps" step into
RadekHLE's MainActivity.java.

This was written against the DECOMPILED STRING TABLE of a RadekHLE APK,
not the real source, so it's deliberately conservative: it looks for the
onCreate(...) method signature and inserts a call right after its opening
brace. If it can't find that pattern, it exits with an error instead of
guessing further, so you don't end up with a silently-broken build.

Usage: python3 seed_bundled_app.py <path/to/MainActivity.java>
"""
import re
import sys

SEED_METHOD = """
    // --- injected by seed_bundled_app.py: bundle a fixed game into touchHLE_apps ---
    private void seedBundledAppIfNeeded() {
        java.io.File appsDir = new java.io.File(getExternalFilesDir(null), "touchHLE_apps");
        appsDir.mkdirs();
        java.io.File dest = new java.io.File(appsDir, "game.ipa");
        if (!dest.exists()) {
            try (java.io.InputStream in = getAssets().open("game.ipa");
                 java.io.OutputStream out = new java.io.FileOutputStream(dest)) {
                byte[] buf = new byte[8192];
                int n;
                while ((n = in.read(buf)) > 0) {
                    out.write(buf, 0, n);
                }
            } catch (java.io.IOException e) {
                android.util.Log.e("RadekHLE", "Couldn't seed bundled game: " + e);
            }
        }
    }
    // --- end injected block ---
"""

ONCREATE_RE = re.compile(
    r"(protected\s+void\s+onCreate\s*\([^)]*\)\s*\{)"
)


def main():
    if len(sys.argv) != 2:
        print("Usage: seed_bundled_app.py <path/to/MainActivity.java>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if "seedBundledAppIfNeeded" in content:
        print(f"[seed_bundled_app] {path} already patched, skipping.")
        return

    match = ONCREATE_RE.search(content)
    if not match:
        print(
            "[seed_bundled_app] ERROR: couldn't find a `protected void onCreate(...)` "
            "signature in this file. RadekHLE's real MainActivity.java may differ from "
            "what this script expects (e.g. a different visibility modifier, or logic "
            "split across a base class). Open the file, find onCreate manually, and "
            "add a call to a seeding method yourself -- see the README for the method "
            "body to use.",
            file=sys.stderr,
        )
        sys.exit(2)

    insert_at = match.end()
    # Insert the call to seedBundledAppIfNeeded() as the first statement in onCreate,
    # and append the method definition itself just before the class's final closing brace.
    patched = (
        content[:insert_at]
        + "\n        seedBundledAppIfNeeded();\n"
        + content[insert_at:]
    )

    last_brace = patched.rfind("}")
    if last_brace == -1:
        print("[seed_bundled_app] ERROR: couldn't find the class's closing brace.", file=sys.stderr)
        sys.exit(3)

    patched = patched[:last_brace] + SEED_METHOD + "\n" + patched[last_brace:]

    with open(path, "w", encoding="utf-8") as f:
        f.write(patched)

    print(f"[seed_bundled_app] Patched {path} successfully.")
    print("[seed_bundled_app] Please review the diff before trusting a release build --")
    print("[seed_bundled_app] this script has not been tested against RadekHLE's real source.")


if __name__ == "__main__":
    main()
