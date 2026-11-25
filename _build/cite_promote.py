#!/usr/bin/env python3
"""Copia las copias finales citadas sobre los resúmenes fuente, con respaldo.

Uso:
    python3 _build/cite_promote.py --dry-run
    python3 _build/cite_promote.py
"""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT.parent / "Anatopato" / "Capitulos" / "resumenes"
FINAL = ROOT / "_build" / "cites" / "final"
BACKUP = Path("/tmp/opencode/anatopato_citas/original")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    missing = [c for c in range(1, 11) if not (FINAL / f"Cap{c:02d}.md").exists()]
    if missing:
        raise SystemExit(f"Faltan copias finales: {missing}")

    BACKUP.mkdir(parents=True, exist_ok=True)
    for chapter in range(1, 11):
        src = RES / f"Cap{chapter:02d}.md"
        dst = FINAL / f"Cap{chapter:02d}.md"
        backup = BACKUP / f"Cap{chapter:02d}.md"
        if not backup.exists():
            shutil.copy2(src, backup)
        print(f"Cap{chapter:02d}: {src} <- {dst.name} (respaldo {backup})")
        if not args.dry_run:
            shutil.copy2(dst, src)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
