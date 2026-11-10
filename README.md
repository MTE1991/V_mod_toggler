# GTA V Online Safe Mod Toggler

A small Python/Tkinter desktop app for temporarily moving common GTA V mod files, mod loaders, ASI plugins, trainer files, and trainer folders into a backup folder before launching GTA Online.

The app scans your GTA V installation folder, shows the detected mod-related files and folders, lets you choose exactly what should be moved, and saves a restore manifest so the selected items can be restored later.

> **Important:** This tool is designed to reduce the chance of accidentally launching GTA Online with obvious mod files present. It does **not** guarantee that Rockstar Games will consider your installation safe. Additionally, it does not fully cover special mods and plugins (e.g. LSPDFR, Rage Plugin Hook). Always use your own judgment and always close GTA V before moving or restoring files.

---

## Features

- Graphical interface built with Python's built-in `tkinter`
- Browse and select your GTA V installation folder
- Scan for common mod-related files and folders
- Detects common mod folders such as:
  - `mods`
  - `scripts`
  - `plugins`
  - `asi`
  - `lspdfr`
- Detects popular trainer folders and config folders such as:
  - Menyoo / `menyooStuff`
  - Enhanced Native Trainer / ENT
  - Rampage / `RampageFiles`
  - TrainerV
  - Simple Trainer
  - AddonSpawner
- Detects common mod loader/plugin files such as:
  - `dinput8.dll`
  - `xinput1_4.dll`
  - `ScriptHookV.dll`
  - `ScriptHookVDotNet*.dll`
  - `OpenIV.asi`
  - `Menyoo.asi`
  - `Rampage.asi`
  - `NativeUI.dll`
- Lets the user choose which detected items should be moved
- Moves selected items into `_ONLINE_SAFE_BACKUP`
- Stores moved item paths in `manifest.json`
- Restores previously moved items safely
- Avoids overwriting existing files during restore
- Includes a log panel for scan, backup, and restore actions

---

## Requirements

- OS: Windows/Linux
- Python 3.9 or newer recommended
- No external Python packages required

The script uses only Python standard library modules:

```python
json
shutil
threading
tkinter
pathlib
```

---

## Files

Main script:

```text
gta_v_mod_toggle_gui.py
```

Backup folder created by the app:

```text
_ONLINE_SAFE_BACKUP
```

Restore manifest created inside the backup folder:

```text
_ONLINE_SAFE_BACKUP/manifest.json
```

---

## How to Run

### 1. Recommended:
Download and run the latest binary directly from here: https://github.com/MTE1991/V_mod_toggler/releases/

### 2. Build it yourself:

1. Install Python if it is not already installed.
2. Place `gta_v_mod_toggle_gui.py` anywhere you want.
3. Run it with:

```bash
python gta_v_mod_toggle_gui.py
```

Or, on some systems:

```bash
py gta_v_mod_toggle_gui.py
```

The GUI window should open.

---

## How to Use

### 1. Select GTA V Folder

Click **Browse...** and select your GTA V installation folder.

Common Steam location:

```text
C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V
```

Common Epic Games location:

```text
C:\Program Files\Epic Games\GTAV
```

Common Rockstar Games Launcher location:

```text
C:\Program Files\Rockstar Games\Grand Theft Auto V
```

Your actual folder may be different.

---

### 2. Scan Mods

Click **Scan Mods**.

The app checks the selected GTA V root folder and lists detected mod-related files and folders.

Detected items appear in a table with:

- checkbox state
- item type
- file/folder name
- reason for detection

---

### 3. Choose What to Move

Review the detected list carefully.

Use the checkbox column to select or unselect items.

You can also use:

- **Select All** — selects all detected items
- **Clear Selection** — unselects all detected items

Only checked items will be moved to backup.

---

### 4. Move Selected Items to Backup

Click **Move Selected to Backup**.

The app asks for confirmation before moving anything.

Selected items are moved into:

```text
GTA V Folder\_ONLINE_SAFE_BACKUP
```

A manifest file is saved so the app knows what to restore later:

```text
GTA V Folder\_ONLINE_SAFE_BACKUP\manifest.json
```

---

### 5. Restore Mods

When you want your mods back, select the same GTA V folder and click **Restore Mods**.

The app reads the manifest and moves the backed-up items back to their original locations.

If a file or folder already exists at the original location, the app skips it instead of overwriting it.

---

## What the App Detects

The app mainly scans the GTA V root folder. It does not deeply scan every subfolder.

### Folder Detection

The app detects known mod and trainer folders using normalized names. This means spaces, underscores, and hyphens are ignored.

For example, these can be treated similarly:

```text
menyooStuff
Menyoo Stuff
menyoo_stuff
menyoo-stuff
```

Known folder categories include:

```text
mods
scripts
plugins
asi
lspdfr
menyoo
menyooStuff
Enhanced Native Trainer / ENT
Rampage
RampageFiles
TrainerV
Simple Trainer
NativeUI
AddonSpawner
```

### File Detection

The app detects known mod loader, trainer, ASI, DLL, INI, and support files.

Examples:

```text
dinput8.dll
ScriptHookV.dll
ScriptHookVDotNet.asi
ScriptHookVDotNet2.dll
ScriptHookVDotNet3.dll
OpenIV.asi
Menyoo.asi
Rampage.asi
NativeUI.dll
heapadjuster.asi
packfilelimitadjuster.asi
gameconfig.xml
TrainerV.asi
EnhancedNativeTrainer.asi
ENT.asi
AddonSpawner.asi
```

The app also detects any `.asi` file in the GTA V root folder.

---

## Protected Items

The app intentionally avoids moving important game files and internal folders such as:

```text
gta5.exe
PlayGTAV.exe
GTALauncher.exe
bink2w64.dll
commonredist
redistributables
_ONLINE_SAFE_BACKUP
.git
.vscode
```

This helps reduce the risk of damaging the GTA V installation.

---

## Safety Notes

- Close GTA V before using **Move Selected to Backup** or **Restore Mods**.
- Do not run the app while GTA V, OpenIV, or a mod manager is actively using the same files.
- Review the detected list before moving files.
- Keep a separate backup of important custom mod files if needed.
- This tool only moves files and folders. It does not edit game archives, registry entries, Rockstar files, or cloud saves.
- This tool does not bypass anti-cheat systems and should not be used for cheating.

---

## Limitations

- The app only detects common mod files and folders.
- Unknown or custom-named mod files may not be detected.
- Mods installed directly inside `.rpf` archives are not automatically reverted.
- It does not verify game integrity.
- It does not guarantee GTA Online safety.
- If another file appears in the original location before restore, the app skips restoring that item to avoid overwriting.

---

## FAQ & Troubleshooting

### The app says no mod files were found

Possible reasons:

- You selected the wrong folder.
- Your mods are installed under custom names.
- Your mods are installed inside archives rather than as root files/folders.
- The mods were already moved to `_ONLINE_SAFE_BACKUP`.

### Restore does nothing

Possible reasons:

- `_ONLINE_SAFE_BACKUP` does not exist.
- `manifest.json` is missing or empty.
- The files were manually moved or deleted from the backup folder.
- Files with the same names already exist in the GTA V folder.

### A file was skipped during restore

The app skips restore if the original target path already exists.

This is intentional to avoid overwriting files.

You can manually compare the file in `_ONLINE_SAFE_BACKUP` with the file in the GTA V folder before deciding what to do.

---

## Recommended Workflow

Before playing GTA Online:

1. Close GTA V.
2. Open the GUI app.
3. Select your GTA V folder.
4. Click **Scan Mods**.
5. Review the detected list.
6. Keep only the mod files/folders you want to disable checked.
7. Click **Move Selected to Backup**.
8. Launch GTA Online.

Before playing modded Story Mode again:

1. Close GTA V.
2. Open the GUI app.
3. Select the same GTA V folder.
4. Click **Restore Mods**.
5. Launch GTA V Story Mode.

---

## Disclaimer

This project is a convenience tool for temporarily moving local mod files. It is not affiliated with Rockstar Games, Take-Two Interactive, OpenIV, Script Hook V, Menyoo, Rampage, Enhanced Native Trainer, or any other mod/trainer project.

Use it at your own risk.
