#!/usr/bin/env python3
"""
Injects a first-run "seed the bundled game into touchHLE_apps" step, plus a
getArguments() override to auto-launch it, into RadekHLE's real
MainActivity.java (org.radekhle.android.MainActivity, which extends
SDLActivity and has no onCreate override of its own).

Usage: python3 seed_bundled_app.py <path/to/MainActivity.java>
"""
import sys

CLASS_DECL = "public class MainActivity extends SDLActivity {"

INJECTED_BLOCK = """
    @Override
    protected void onCreate(android.os.Bundle savedInstanceState) {
        seedBundledAppIfNeeded();
        super.onCreate(savedInstanceState);
    }

    // --- injected by seed_bundled_app.py: bundle a fixed game into touchHLE_apps ---
    private void seedBundledAppIfNeeded() {
        File target = new File(getExternalFilesDir(null), "touchHLE_apps");
        if (!target.exists() && !target.mkdirs()) {
            Log.e(TAG, "Couldn't create game folder: " + target);
            return;
        }
        File dest = new File(target, "game.ipa");
        if (dest.exists()) {
            return;
        }
        try (InputStream input = getAssets().open("game.ipa");
             OutputStream output = new FileOutputStream(dest)) {
            byte[] buffer = new byte[1024 * 1024];
            int count;
            while ((count = input.read(buffer)) != -1) {
                output.write(buffer, 0, count);
            }
            Log.i(TAG, "Seeded bundled game into " + dest);
        } catch (Exception ex) {
            Log.e(TAG, "Couldn't seed bundled game", ex);
        }
    }

    @Override
    protected String[] getArguments() {
        File game = new File(new File(getExternalFilesDir(null), "touchHLE_apps"), "game.ipa");
        if (game.exists()) {
            return new String[]{ game.getAbsolutePath() };
        }
        return super.getArguments();
    }
    // --- end injected block ---
"""


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

    if CLASS_DECL not in content:
        print(
            "[seed_bundled_app] ERROR: couldn't find the expected class declaration: "
            + CLASS_DECL
            + ". RadekHLE's MainActivity.java may have changed since this script was "
            + "written. Open the file, find the class body, and add an onCreate(Bundle) "
            + "override that calls a seeding method before super.onCreate(...) -- see "
            + "this script's INJECTED_BLOCK for the method bodies to reuse.",
            file=sys.stderr,
        )
        sys.exit(2)

    patched = content.replace(CLASS_DECL, CLASS_DECL + "\n" + INJECTED_BLOCK, 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(patched)

    print(f"[seed_bundled_app] Patched {path} successfully.")


if __name__ == "__main__":
    main()
