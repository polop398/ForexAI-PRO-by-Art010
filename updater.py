# -*- coding: utf-8 -*-
"""ForexAI PRO updater. Supports local startup bundle and standalone --apply mode."""
from pathlib import Path
import argparse, os, shutil, sys, time, zipfile, subprocess
ROOT = Path(__file__).resolve().parent

def safe_extract_apply(bundle: Path, root: Path):
    root = root.resolve()
    with zipfile.ZipFile(bundle, "r") as z:
        names = z.namelist()
        for name in names:
            p = Path(name)
            if p.is_absolute() or ".." in p.parts or name.startswith(("/", "\\")):
                raise ValueError(f"Unsafe path in update: {name}")
        backup_root = root / "update_backup"
        backup_root.mkdir(exist_ok=True)
        with __import__('tempfile').TemporaryDirectory(prefix="forexai_update_") as td:
            temp = Path(td); z.extractall(temp)
            for item in temp.rglob("*"):
                if not item.is_file(): continue
                rel = item.relative_to(temp)
                if rel.parts and rel.parts[0] in ("updates", "update_backup"): continue
                dest = (root / rel).resolve()
                if root not in dest.parents and dest != root: raise ValueError("Unsafe destination")
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    backup = backup_root / rel
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dest, backup)
                shutil.copy2(item, dest)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--pid', type=int, default=0)
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--bundle', default=str(ROOT/'updates'/'update.zip'))
    parser.add_argument('--restart', default='ForexAI_PRO.exe')
    args=parser.parse_args()
    if args.apply:
        # Wait for the main GUI process to exit before replacing files on Windows.
        if args.pid:
            try:
                import ctypes
                handle=ctypes.windll.kernel32.OpenProcess(0x100000, False, args.pid)
                if handle:
                    ctypes.windll.kernel32.WaitForSingleObject(handle, 30000)
                    ctypes.windll.kernel32.CloseHandle(handle)
            except Exception: time.sleep(3)
        bundle=Path(args.bundle); root=Path(args.root)
        safe_extract_apply(bundle, root)
        try: bundle.unlink()
        except OSError: pass
        exe=root/args.restart
        if exe.exists(): subprocess.Popen([str(exe)], cwd=str(root))
        return
    bundle=ROOT/'updates'/'update.zip'
    if bundle.exists():
        try:
            safe_extract_apply(bundle, ROOT); bundle.unlink()
            print('ติดตั้งไฟล์อัปเดตเรียบร้อยแล้ว')
        except Exception as exc:
            print(f'ติดตั้งอัปเดตไม่สำเร็จ: {exc}')

if __name__=='__main__': main()
