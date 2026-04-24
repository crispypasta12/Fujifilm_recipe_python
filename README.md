# FujiRecipe — Fujifilm Film Simulation Recipe Editor

A desktop application for reading, editing, and writing film simulation presets directly to Fujifilm cameras over USB. Browse a built-in library of 70+ community recipes, tweak every parameter, and push changes straight to your camera's custom slots (C1–C7).

---

## Features

- **USB camera connection** — connects to Fujifilm cameras via PTP/USB (tested on X100VI)
- **Read & write presets** — read all 7 custom preset slots from the camera and write edited presets back
- **Recipe browser** — 70+ built-in recipes for X-Trans V sensors, sourced from [fujixweekly.com](https://fujixweekly.com)
- **Full parameter control** — edit every film simulation setting:
  - Film Simulation (Provia, Velvia, Astia, Classic Chrome, Classic Neg, Eterna, Acros, Nostalgic Neg, Reala Ace, and more)
  - Dynamic Range (DR100 / DR200 / DR400) and D-Range Priority
  - Grain Effect (Off / Weak / Strong × Small / Large)
  - Color Chrome Effect and Color Chrome FX Blue
  - White Balance (Auto, Daylight, Shade, Kelvin, and custom R/B shifts)
  - Highlight Tone, Shadow Tone, Color, Sharpness, Noise Reduction, Clarity
  - Smooth Skin Effect
  - Monochrome Warm/Cool and Magenta/Green toning
- **My Recipes** — save any slot's settings as a named custom recipe
- **Import / Export** — load and save presets as JSON files; export individual slots or all 7 at once
- **Recipe cards** — export a 900×540 PNG recipe card summarising a slot's settings
- **Recipe scraper** — included `scrape_recipes.py` script to pull new recipes from fujixweekly.com

---

## Requirements

- Python 3.11+
- [PyQt6](https://pypi.org/project/PyQt6/) >= 6.6
- [pyusb](https://pypi.org/project/pyusb/) >= 1.2.1
- A libusb backend (see [pyusb installation guide](https://github.com/pyusb/pyusb))

For the scraper only:
- `requests`
- `beautifulsoup4`

---

## Installation

```bash
git clone https://github.com/crispypasta12/Fujifilm_recipe_python.git
cd Fujifilm_recipe_python
pip install -r requirements.txt
```

**Windows users:** install [libusb](https://libusb.info/) and place the DLL on your PATH, or use [Zadig](https://zadig.akeo.ie/) to install the WinUSB driver for your camera.

---

## Usage

### Launch the app

```bash
python main.py
```

### Connect your camera

1. Connect the camera to your PC via USB and set **USB Mode -> PC Auto Save** (or similar) so the camera exposes a PTP interface.
2. Click **Connect** in the app. The status indicator turns green when the connection is established and all 7 preset slots are read automatically.

### Edit a slot

Select a slot tab (C1–C7) and adjust the parameters using the dropdowns and sliders. A dot appears on the tab label when a slot has unsaved changes.

### Browse built-in recipes

Click **Browse Recipes** to open the recipe browser. Select a sensor generation, pick a recipe, preview its settings and sample image, then load it into a slot or write it directly to the camera.

### Write to camera

Click **Write** on a slot panel to push that slot's settings to the camera. You will be asked to confirm before any write is performed.

### Import / Export

Use the **File** menu to:
- **Import Recipe...** — load a JSON file into the current slot
- **Import All...** — load a folder of JSON files into C1–C7
- **Export Slot...** — save the current slot as a JSON file
- **Export All...** — save all 7 slots to a folder
- **Export Card...** — save a PNG recipe card for the current slot

---

## Recipe JSON format

```json
{
  "name": "My Recipe",
  "camera": "X100VI",
  "slot": 1,
  "filmSimulation": "Classic Negative",
  "dynamicRange": "DR400",
  "grainEffect": "Weak, Large",
  "colorChrome": "Strong",
  "colorChromeFxBlue": "Weak",
  "whiteBalance": "Auto",
  "wbShiftR": 1,
  "wbShiftB": -2,
  "highlightTone": -1,
  "shadowTone": 1,
  "color": 2,
  "sharpness": -1,
  "noiseReduction": -4,
  "clarity": 0
}
```

---

## Scraping new recipes

```bash
pip install requests beautifulsoup4
python scrape_recipes.py              # scrape all X-Trans V recipes
python scrape_recipes.py --dry-run    # preview discovered URLs only
python scrape_recipes.py --limit 5    # scrape only the first 5 recipes
```

Scraped JSON and sample images are saved to `recipes/builtin/x-trans-v/`.

---

## Project structure

```
fuji-recipe/
├── main.py                  # entry point
├── requirements.txt
├── scrape_recipes.py        # recipe scraper
├── profile/                 # camera profile: enums, preset translation
├── ptp/                     # PTP/USB transport and session layer
├── recipes/
│   ├── loader.py            # loads built-in recipe JSONs
│   ├── user_store.py        # persists user-created recipes
│   └── builtin/
│       └── x-trans-v/       # 70+ X-Trans V recipes + sample images
└── ui/                      # PyQt6 interface components
```

---

## Compatibility

Currently targeted at **X-Trans V** cameras (e.g. X100VI, X-T5, X-S20). Support for earlier sensor generations (X-Trans IV etc.) can be added by scraping recipes into a new `recipes/builtin/x-trans-iv/` folder and uncommenting the entry in `recipes/loader.py`.

---

## License

MIT
