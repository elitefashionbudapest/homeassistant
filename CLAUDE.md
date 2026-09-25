# Home Assistant konfiguráció (Raspberry Pi 5, Home Assistant OS)

Ez a repó a Pi `/config` mappája. A Pi a **Git pull** add-onnal húzza le a változásokat.

## Szabályok
- Új YAML-konfig **csak a `packages/` mappába** kerül, témánként egy fájl (pl. `packages/lights.yaml`).
- Az `automations.yaml`, `scripts.yaml` és `scenes.yaml` fájlokat a HA UI kezeli. **Soha ne módosítsd őket a repóban**,
  különben a Pi-n a `git pull` ütközéssel elszáll.
- Titkok (tokenek, jelszavak) csak `!secret kulcs` formában. A kulcsot vedd fel a `secrets.example.yaml`-ba
  helykitöltő értékkel; a valódi értéket a felhasználó írja be a Pi-n lévő `secrets.yaml`-ba.
- A név, hely, időzóna és mértékegységek a UI-ban vannak beállítva, ezeket ne írd YAML-ba.
- Minden pushra lefut a `.github/workflows/check.yaml` config check. Csak zöld check után mondd, hogy kész.
- Push után a felhasználónak el kell indítania a Git pull add-ont (vagy az ismétlés kapcsolja be),
  majd újraindítani a HA-t (Fejlesztői eszközök → YAML → Konfiguráció ellenőrzése → Újraindítás).
