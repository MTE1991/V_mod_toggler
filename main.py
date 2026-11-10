from __future__ import annotations

import json
import shutil
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

BACKUP_DIR_NAME = "_ONLINE_SAFE_BACKUP"
MANIFEST_NAME = "manifest.json"

# Common GTA V mod-related folders and trainer data/config folders.
# Matching is normalized, so names such as "Menyoo Stuff", "menyooStuff",
# "RampageFiles", and "Rampage Files" are treated consistently.
MOD_FOLDERS = {
    "mods", "scripts", "plugins", "asi", "lspdfr",
    "menyoo", "menyoostuff", "enhancednativetrainer", "ent", "entconfig",
    "rampage", "rampagefiles", "trainerv", "simpletrainer", "simpletrainerv",
    "nativeui", "stand", "lamance", "addonspawner",
}

KNOWN_MOD_DLLS = {
    "dinput8.dll", "dsound.dll", "scripthookv.dll", "scripthookvdotnet.asi",
    "scripthookvdotnet2.dll", "scripthookvdotnet3.dll", "openiv.asi",
    "ragepluginhook.dll", "ragepluginhook.ini", "rphsettings.ini",
    "menyoo.asi", "rampage.asi", "nativeui.dll", "version.dll", "xlive.dll", "xinput1_4.dll",
}

KNOWN_MOD_FILES = {
    "heapadjuster.asi", "heapadjuster.ini", "packfilelimitadjuster.asi",
    "packfilelimitadjuster.ini", "gameconfig.xml", "trainerv.asi",
    "enhancednativetrainer.asi", "ent.asi", "simpletrainer.asi",
    "addonspawner.asi", "addonspawner.ini", "lua.asi",
}

NEVER_TOUCH = {
    BACKUP_DIR_NAME.lower(), "gta5.exe", "playgtav.exe", "gtalauncher.exe",
    "bink2w64.dll", "commonredist", "redistributables", ".git", ".vscode",
}


def load_manifest(backup_dir: Path) -> dict:
    manifest_path = backup_dir / MANIFEST_NAME
    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {"moved": []}


def save_manifest(backup_dir: Path, manifest: dict) -> None:
    backup_dir.mkdir(exist_ok=True)
    with (backup_dir / MANIFEST_NAME).open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def normalize_name(name: str) -> str:
    return name.lower().replace(" ", "").replace("_", "").replace("-", "")


def is_mod_file(path: Path) -> bool:
    name = path.name.lower()
    if name in NEVER_TOUCH:
        return False
    if name in KNOWN_MOD_DLLS or name in KNOWN_MOD_FILES:
        return True
    if path.is_file() and path.suffix.lower() == ".asi":
        return True
    if path.is_file() and path.suffix.lower() == ".dll":
        return name in KNOWN_MOD_DLLS
    return False


def is_mod_folder(path: Path) -> bool:
    return path.is_dir() and normalize_name(path.name) in MOD_FOLDERS


def item_reason(path: Path) -> str:
    name = path.name.lower()
    normalized = normalize_name(path.name)
    if path.is_dir() and normalized in MOD_FOLDERS:
        return "Known mod/trainer folder"
    if name in KNOWN_MOD_DLLS:
        return "Known mod loader/plugin file"
    if name in KNOWN_MOD_FILES:
        return "Known mod support/trainer file"
    if path.is_file() and path.suffix.lower() == ".asi":
        return "ASI plugin file"
    return "Possible mod item"


def scan_candidates(game_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    for item in game_dir.iterdir():
        if item.name.lower() in NEVER_TOUCH:
            continue
        if is_mod_folder(item) or is_mod_file(item):
            candidates.append(item)
    return sorted(candidates, key=lambda p: (p.is_file(), p.name.lower()))


class GTAVModToggleApp(tk.Tk):
    CHECKED = "☑"
    UNCHECKED = "☐"

    def __init__(self) -> None:
        super().__init__()
        self.title("GTA V (Legacy) Online Safe Mod Toggler")
        self.geometry("980x680")
        self.minsize(860, 580)
        self.iconbitmap("v_mod_toggler.ico")

        self.game_dir_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Select your GTA V installation folder.")
        self.detected_items: list[Path] = []
        self.checked_items: set[str] = set()
        self._build_ui()

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=14)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Grand Theft Auto V (Legacy) Online Safe Mod Toggler", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            main,
            text="Scan first, review detected mod files/folders, then choose exactly which items to move into backup.",
        ).pack(anchor="w", pady=(2, 14))

        path_frame = ttk.LabelFrame(main, text="GTA V Folder", padding=10)
        path_frame.pack(fill=tk.X)
        ttk.Entry(path_frame, textvariable=self.game_dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(path_frame, text="Browse...", command=self.browse_folder).pack(side=tk.LEFT)

        button_frame = ttk.Frame(main)
        button_frame.pack(fill=tk.X, pady=12)
        self.scan_btn = ttk.Button(button_frame, text="Scan Mods", command=self.scan_mods)
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.select_all_btn = ttk.Button(button_frame, text="Select All", command=self.select_all_items)
        self.select_all_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.clear_selection_btn = ttk.Button(button_frame, text="Clear Selection", command=self.clear_selection)
        self.clear_selection_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.disable_btn = ttk.Button(button_frame, text="Move Selected to Backup", command=self.disable_selected_mods)
        self.disable_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.restore_btn = ttk.Button(button_frame, text="Restore Mods", command=self.restore_mods)
        self.restore_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.clear_btn = ttk.Button(button_frame, text="Clear Log", command=self.clear_log)
        self.clear_btn.pack(side=tk.RIGHT)

        status_frame = ttk.LabelFrame(main, text="Status", padding=10)
        status_frame.pack(fill=tk.X)
        ttk.Label(status_frame, textvariable=self.status_var).pack(anchor="w")

        detected_frame = ttk.LabelFrame(main, text="Detected Items - click the checkbox column to choose", padding=10)
        detected_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.tree = ttk.Treeview(
            detected_frame,
            columns=("check", "type", "name", "reason"),
            show="headings",
            selectmode="browse",
            height=10,
        )
        for col, text, width, anchor in [
            ("check", "Use", 60, "center"),
            ("type", "Type", 90, "center"),
            ("name", "File / Folder", 360, "w"),
            ("reason", "Reason", 320, "w"),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor, stretch=(col in {"name", "reason"}))
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll = ttk.Scrollbar(detected_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)
        self.tree.bind("<space>", self.on_tree_space)

        log_frame = ttk.LabelFrame(main, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.log_box = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=9)
        self.log_box.pack(fill=tk.BOTH, expand=True)
        self.log_box.configure(state=tk.DISABLED)

        ttk.Label(
            main,
            text="Important: This does not guarantee Rockstar will consider the folder safe. Always close GTA V before disabling/restoring mods.",
            foreground="red",
        ).pack(anchor="w", pady=(8, 0))

    def browse_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select GTA V Installation Folder")
        if folder:
            self.game_dir_var.set(folder)
            self.detected_items.clear()
            self.checked_items.clear()
            self.refresh_detected_table()
            self.status_var.set("Folder selected. Click Scan Mods to review detected mod files.")
            self.log(f"Selected folder: {folder}")

    def get_game_dir(self) -> Path | None:
        raw_path = self.game_dir_var.get().strip()
        if not raw_path:
            messagebox.showerror("Missing Folder", "Please select your GTA V installation folder first.")
            return None
        game_dir = Path(raw_path).resolve()
        if not game_dir.exists() or not game_dir.is_dir():
            messagebox.showerror("Invalid Folder", "The selected path is not a valid folder.")
            return None
        return game_dir

    def get_game_dir_without_popup(self) -> Path | None:
        raw_path = self.game_dir_var.get().strip()
        if not raw_path:
            return None
        game_dir = Path(raw_path).resolve()
        return game_dir if game_dir.exists() and game_dir.is_dir() else None

    def log(self, message: str) -> None:
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state=tk.DISABLED)
        self.update_idletasks()

    def clear_log(self) -> None:
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.delete("1.0", tk.END)
        self.log_box.configure(state=tk.DISABLED)

    def set_buttons_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        for button in (self.scan_btn, self.select_all_btn, self.clear_selection_btn, self.disable_btn, self.restore_btn, self.clear_btn):
            button.configure(state=state)

    def run_threaded(self, task) -> None:
        self.set_buttons_enabled(False)
        def wrapper() -> None:
            try:
                task()
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Error", str(exc)))
                self.after(0, lambda: self.log(f"[ERROR] {exc}"))
            finally:
                self.after(0, lambda: self.set_buttons_enabled(True))
        threading.Thread(target=wrapper, daemon=True).start()

    def refresh_detected_table(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        game_dir = self.get_game_dir_without_popup()
        for item in self.detected_items:
            key = str(item)
            rel = item.name if game_dir is None else str(item.relative_to(game_dir))
            item_type = "Folder" if item.is_dir() else "File"
            check_text = self.CHECKED if key in self.checked_items else self.UNCHECKED
            self.tree.insert("", tk.END, iid=key, values=(check_text, item_type, rel, item_reason(item)))

    def select_all_items(self) -> None:
        self.checked_items = {str(item) for item in self.detected_items}
        self.refresh_detected_table()
        self.update_selection_status()

    def clear_selection(self) -> None:
        self.checked_items.clear()
        self.refresh_detected_table()
        self.update_selection_status()

    def on_tree_click(self, event) -> None:
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        if self.tree.identify_column(event.x) != "#1":
            return
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.toggle_item(row_id)

    def on_tree_space(self, _event) -> str:
        selected = self.tree.selection()
        if selected:
            self.toggle_item(selected[0])
        return "break"

    def toggle_item(self, row_id: str) -> None:
        if row_id in self.checked_items:
            self.checked_items.remove(row_id)
        else:
            self.checked_items.add(row_id)
        self.refresh_detected_table()
        self.tree.selection_set(row_id)
        self.update_selection_status()

    def update_selection_status(self) -> None:
        if not self.detected_items:
            self.status_var.set("No detected items to select.")
        else:
            self.status_var.set(f"Selected {len(self.checked_items)} of {len(self.detected_items)} detected item(s).")

    def scan_mods(self) -> None:
        game_dir = self.get_game_dir()
        if game_dir is None:
            return
        self.clear_log()
        self.detected_items.clear()
        self.checked_items.clear()
        self.refresh_detected_table()
        self.log(f"Scanning: {game_dir}")

        backup_dir = game_dir / BACKUP_DIR_NAME
        manifest = load_manifest(backup_dir)
        if manifest.get("moved"):
            self.status_var.set("Mods appear to be disabled already. Backup manifest found.")
            self.log("Backup manifest found. These items were previously moved:")
            for rel in manifest.get("moved", []):
                self.log(f"  - {rel}")
            return

        self.detected_items = scan_candidates(game_dir)
        self.checked_items = {str(item) for item in self.detected_items}  # default checked; user can uncheck
        self.refresh_detected_table()
        if not self.detected_items:
            self.status_var.set("No common mod files/folders found.")
            self.log("No common mod files/folders found.")
            return
        self.status_var.set(f"Found {len(self.detected_items)} possible mod item(s). Review and uncheck anything you do not want to move.")
        self.log("Detected possible mod files/folders:")
        for item in self.detected_items:
            self.log(f"  - {item.relative_to(game_dir)}  ({item_reason(item)})")

    def disable_selected_mods(self) -> None:
        game_dir = self.get_game_dir()
        if game_dir is None:
            return
        if not self.detected_items:
            messagebox.showinfo("Scan Required", "Click Scan Mods first, then select the items you want to move.")
            return
        selected_paths = [Path(path_str) for path_str in self.checked_items]
        selected_paths = [p for p in selected_paths if p.exists()]
        if not selected_paths:
            messagebox.showinfo("Nothing Selected", "Select at least one detected file or folder to move to backup.")
            return
        selected_preview = "\n".join(f"• {p.relative_to(game_dir)}" for p in selected_paths[:15])
        extra = "" if len(selected_paths) <= 15 else f"\n...and {len(selected_paths) - 15} more item(s)."
        if not messagebox.askyesno(
            "Move Selected Items?",
            f"Make sure GTA V is closed.\n\nThe following {len(selected_paths)} selected item(s) will be moved to {BACKUP_DIR_NAME}:\n\n{selected_preview}{extra}\n\nContinue?",
        ):
            return
        self.run_threaded(lambda: self._disable_mods_worker(game_dir, selected_paths))

    def _disable_mods_worker(self, game_dir: Path, selected_paths: list[Path]) -> None:
        backup_dir = game_dir / BACKUP_DIR_NAME
        manifest = load_manifest(backup_dir)
        self.after(0, lambda: self.log(f"Moving selected items to backup in: {game_dir}"))
        if manifest.get("moved"):
            self.after(0, lambda: self.status_var.set("Mods may already be disabled. Restore first if needed."))
            self.after(0, lambda: self.log("Mods may already be disabled. Restore first if needed."))
            return

        moved_count = 0
        for item in selected_paths:
            if not item.exists():
                self.after(0, lambda p=item: self.log(f"[SKIP] No longer exists: {p.name}"))
                continue
            if item.name.lower() in NEVER_TOUCH:
                self.after(0, lambda p=item: self.log(f"[SKIP] Protected item: {p.name}"))
                continue
            relative = item.relative_to(game_dir)
            target = backup_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                self.after(0, lambda rel=relative: self.log(f"[SKIP] Already exists in backup: {rel}"))
                continue
            shutil.move(str(item), str(target))
            manifest["moved"].append(str(relative))
            moved_count += 1
            self.after(0, lambda rel=relative: self.log(f"[BACKUP] {rel}"))

        if moved_count:
            save_manifest(backup_dir, manifest)

        def finish() -> None:
            self.detected_items = [item for item in self.detected_items if item.exists()]
            self.checked_items.clear()
            self.refresh_detected_table()
            self.status_var.set(f"Done. Moved {moved_count} selected item(s) to backup.")
            self.log(f"\nDone. Moved {moved_count} selected item(s). Your GTA V folder should now be safer for GTA Online.")
        self.after(0, finish)

    def restore_mods(self) -> None:
        game_dir = self.get_game_dir()
        if game_dir is None:
            return
        if not messagebox.askyesno(
            "Restore Mods?",
            "Make sure GTA V is closed.\n\nThis will restore files/folders from _ONLINE_SAFE_BACKUP. Continue?",
        ):
            return
        self.run_threaded(lambda: self._restore_mods_worker(game_dir))

    def _restore_mods_worker(self, game_dir: Path) -> None:
        backup_dir = game_dir / BACKUP_DIR_NAME
        if not backup_dir.exists():
            self.after(0, lambda: self.status_var.set("No backup folder found. Nothing to restore."))
            self.after(0, lambda: self.log("No backup folder found. Nothing to restore."))
            return
        manifest = load_manifest(backup_dir)
        moved = manifest.get("moved", [])
        if not moved:
            self.after(0, lambda: self.status_var.set("Nothing to restore."))
            self.after(0, lambda: self.log("Nothing to restore."))
            return

        restored_any = False
        remaining: list[str] = []
        for rel_str in moved:
            rel = Path(rel_str)
            source = backup_dir / rel
            target = game_dir / rel
            if not source.exists():
                self.after(0, lambda r=rel: self.log(f"[SKIP] Missing in backup: {r}"))
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                remaining.append(rel_str)
                self.after(0, lambda r=rel: self.log(f"[SKIP] Target already exists, not overwriting: {r}"))
                continue
            shutil.move(str(source), str(target))
            restored_any = True
            self.after(0, lambda r=rel: self.log(f"[RESTORE] {r}"))

        if remaining:
            save_manifest(backup_dir, {"moved": remaining})
        else:
            self._cleanup_backup_folder(backup_dir)

        def finish_restore() -> None:
            self.detected_items.clear()
            self.checked_items.clear()
            self.refresh_detected_table()
            self.status_var.set("Restore complete." if restored_any else "Nothing was restored.")
            self.log("Restore complete." if restored_any else "Nothing was restored.")
        self.after(0, finish_restore)

    def _cleanup_backup_folder(self, backup_dir: Path) -> None:
        try:
            manifest_path = backup_dir / MANIFEST_NAME
            if manifest_path.exists():
                manifest_path.unlink()
            for p in sorted(backup_dir.rglob("*"), reverse=True):
                if p.is_dir():
                    try:
                        p.rmdir()
                    except OSError:
                        pass
            try:
                backup_dir.rmdir()
            except OSError:
                pass
        except Exception as exc:
            self.after(0, lambda: self.log(f"[WARN] Cleanup issue: {exc}"))


if __name__ == "__main__":
    app = GTAVModToggleApp()
    app.mainloop()
