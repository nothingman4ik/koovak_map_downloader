# Koovak's Map Downloader

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/) [![PyQt5](https://img.shields.io/badge/PyQt5-Required-green.svg)](https://pypi.org/project/PyQt5/) [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Description

Koovak's Map Downloader is a user-friendly GUI tool designed to simplify downloading Steam Workshop maps and scenarios for **KovaaK's FPS Aim Trainer** (Steam App ID: 824270). It supports downloading individual workshop items, full collections, or direct IDs/links. The tool uses a modified version of DepotDownloader to handle downloads securely and efficiently.

This project includes **DepotDownloaderMod.exe** (from the [SteamAutoCracks/DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod/) repository) in the repository for convenience, allowing seamless integration without external setup. DepotDownloaderMod is a Steam depot downloader utilizing the SteamKit2 library, with support for depot keys, manifests, and workshop items.

## Features

- **Intuitive GUI**: Built with PyQt5 for a modern, dark-themed interface with progress bars, console logs, and easy configuration.
- **Workshop Support**: Download single items by ID or URL, or entire collections automatically.
- **Account Selection**: Choose from pre-configured accounts (displayed as "Account 1" and "Account 2").
- **Game Folder Integration**: Select your KovaaK's root folder to automatically place downloaded `.sce` files in the correct Scenarios directory.
- **Progress Tracking**: Real-time progress bar and detailed logging for each download.
- **Cancel Functionality**: Stop ongoing downloads with a stylish "Cancel" button that changes color and text dynamically.
- **Error Handling**: Validates inputs, checks for DepotDownloaderMod.exe, and provides clear error messages.
- **Settings Persistence**: Remembers your game root folder across sessions using QSettings.

## Requirements

- **Python 3.8+**: Ensure you have Python installed.
- **PyQt5**: Install via `pip install PyQt5`.
- **DepotDownloaderMod.exe**: Included in this repository (from [SteamAutoCracks/DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod/)). No need to download separately.
- **KovaaK's FPS Aim Trainer**: Installed on your system, with the game root folder accessible.

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/koovaks-map-downloader.git
   cd koovaks-map-downloader
   ```

2. Install dependencies:
   ```
   pip install PyQt5
   ```

3. Ensure `DepotDownloaderMod.exe` is in the current directory or a subfolder (it's already included).

## Usage

1. Run the script:
   ```
   python map.py
   ```

2. **Select Account**: Choose from the dropdown (pre-configured).
3. **Select Game Root Folder**: Click "📁 Select Game Root Folder" and pick your KovaaK's installation directory (e.g., `C:\Program Files (x86)\Steam\steamapps\common\KovaaK's FPS Aim Trainer`). The tool will validate the `Scenarios` subfolder.
4. **Enter Workshop Items**: In the text area, paste Steam Workshop links, IDs, or collection URLs (one per line). Examples:
   - `https://steamcommunity.com/sharedfiles/filedetails/?id=123456789`
   - `987654321`
   - Collection links are fully supported!
5. **Start Download**: Click "🚀 Start Download". Monitor progress in the bar and console.
6. **Cancel if Needed**: The button turns red ("❌ Cancel Download") during operation—click to stop.
7. Downloaded `.sce` files will be moved to your game's Scenarios folder automatically.

**Example Console Output:**
```
✅ Target scenarios folder set to C:\...\Scenarios
🔄 Downloading 123456789...
✅ Moved .sce file: example_map.sce
✅ Download of 123456789 completed
```

## Troubleshooting

- **DepotDownloaderMod.exe Not Found**: Ensure it's in the repo directory or subfolders. Redownload from the included file if needed.
- **Invalid IDs**: Check your input—only numeric IDs or valid Steam URLs.
- **Download Errors**: May occur due to Steam rate limits. Try a different account or wait.
- **No .sce Files**: Some workshop items may not contain scenarios—verify on Steam.
- **2FA/Password Issues**: Accounts are pre-set; if prompted, check the script's decoded credentials.

## Credits

- **DepotDownloaderMod**: This tool relies on [SteamAutoCracks/DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod/), a modified Steam depot downloader. The executable is included here for ease of use. Original repository provides advanced features like manifest support—check it out for more details!
- **PyQt5**: For the GUI framework.
