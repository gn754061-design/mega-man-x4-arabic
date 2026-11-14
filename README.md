# Mega Man X4 - Arabic Localization Tooling

Arabic localization tooling for *Mega Man X4* (PlayStation): glyph bitmap generation,
Arabic encoding tables, glyph catalogue construction, translation audit scripts and the
font investigation notes.

## Layout

| Path | Contents |
| --- | --- |
| `data/` | Arabic bitmap set, encoding tables, glyph map, per-batch build scripts |
| `scripts/` | Catalogue and build scripts (`build_ar_catalog.py`, ...) |
| `tools/` | Translation application and audit tooling |
| `docs/` | `FONT.md` and related investigation notes |
| `previews/` | Renders of the generated Arabic glyphs and the glyph catalogue |
| `DELIVERY.md`, `STATUS.md` | Delivery and status notes for the localization |

## Deliberately excluded

- **`MegaManX4_Arabic.bps` (565 MB)** - a patch that large is close to the size of the
  original disc and is not a legal delta patch. It is not distributed.
- **Disc images** (`.iso`, `.bin`), the extracted `DATA_CMN.BND`-style archives, and
  `ARC_FONT8X8.ARC` (the game's own font asset).
- Any Capcom-derived binary or header from the recompilation build.

This repository contains the localization scripts and generated Arabic assets only.

*Mega Man X4* is a trademark of Capcom. Non-commercial fan project.
