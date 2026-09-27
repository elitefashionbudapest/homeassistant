# Home Assistant konfiguráció (Raspberry Pi 5, Home Assistant OS)

Ez a repó a Pi `/config` (= `/homeassistant`) mappája, a `main` ágon. A telepítés SSH-n megy:
`ssh ha` (Terminal & SSH add-on, 192.168.1.37:22, root, kulcs `~/.ssh/ha_pi`). A HA webes felülete: http://192.168.1.37/ (80-as port).

## Telepítés
1. Commit + push a `main` ágra, várd meg a zöld CI-t.
2. `ssh ha 'cd /homeassistant && git pull --ff-only && ha core check'`
3. Ha a check sikeres: `ssh ha 'ha core restart'` (vagy ha elég, a megfelelő `reload` szolgáltatás).

## Szabályok
- Új YAML-konfig **csak a `packages/` mappába** kerül, témánként egy fájl (pl. `packages/lights.yaml`).
  Kivétel: a magyar hangparancsok mondatmintái a `custom_sentences/hu/` mappába kerülnek, mert a HA onnan olvassa.
  Ezt és a `packages/hangvezerles.yaml`-t a `tools/gen_hang.py` generálja; kézzel ne szerkeszd őket, hanem a generátort
  módosítsd, és futtasd: `python tools/gen_hang.py .` Utána: `conversation.reload` és `intent_script.reload`.
- Közös Jinja-makrók a `custom_templates/` mappában vannak (a HA onnan olvassa), pl. `ido.jinja` = magyar
  időkifejezés → „HH:MM”. Módosítás után: `homeassistant.reload_custom_templates`.
- A `packages/redonyok.yaml`-t a `tools/gen_redonyok.py` generálja (redőnyök, futásidők, pozíció, esti lehúzás).
  Módosítás után: `python tools/gen_redonyok.py .`, majd `template.reload`, `script.reload`, `input_number.reload`,
  `automation.reload`.
- Az `automations.yaml`, `scripts.yaml` és `scenes.yaml` fájlokat a HA UI kezeli. **Soha ne módosítsd őket a repóban**,
  különben a Pi-n a `git pull` ütközéssel elszáll.
- Titkok (tokenek, jelszavak) csak `!secret kulcs` formában. A kulcsot vedd fel a `secrets.example.yaml`-ba
  helykitöltő értékkel; a valódi értéket a felhasználó írja be a Pi-n lévő `secrets.yaml`-ba.
- A név, hely, időzóna és mértékegységek a UI-ban vannak beállítva, ezeket ne írd YAML-ba.
- Minden pushra lefut a `.github/workflows/check.yaml` config check. Csak zöld check után mondd, hogy kész.
- A Pi-n soha ne szerkessz kézzel követett fájlt, mert akkor a `git pull` elakad. Minden változás a repón át megy.
