"""Generálja a packages/redonyok.yaml-t: 11 RF-redőny időalapú pozícióval.

Futtatás a repó gyökerében:  python tools/gen_redonyok.py .
Utána: config check, majd template.reload + script.reload + input_number.reload + automation.reload.

Működés:
- A Broadlink RM4 Pro (remote.vaskut14) betanított kódjai: <slug> eszköz, fel / le / stop parancs.
- Minden RF-jel a sorba állító script.redony_rf_kuldes-en megy át (0,7 mp szünet a jelek között).
- A pozíciót egy input_number tárolja (0 = zárva, 100 = nyitva), a futásidőből számolva.
- Részleges állás (½ gomb, csúszka, „félig” hangparancs): a redőny előbb teljesen felmegy,
  aztán lefelé indul, és a kiszámolt idő után a HA leállítja. Így akkor is pontos, ha közben
  távirányítóval mozgatták. A teljes fel- és lehúzás közvetlenül megy.
- Visszajelzés nincs: ha a távirányítóval mozgatod, a HA nem tudja.
"""
import json
import sys
from pathlib import Path

REPO = Path(sys.argv[1])

# slug, név, lehúzási idő (mp). A felhúzási időt nem mértük, egyelőre ugyanennyinek vesszük.
REDONYOK = [
    ("nappali_terasz_1", "Nappali terasz 1", 36.0),
    ("nappali_terasz_2", "Nappali terasz 2", 36.0),
    ("nappali_ablak_1", "Nappali ablak 1", 22.5),
    ("nappali_ablak_2", "Nappali ablak 2", 22.5),
    ("konyha", "Konyha redőny", 22.5),
    ("eloszoba", "Előszoba redőny", 22.5),
    ("furdo", "Fürdő redőny", 15.5),
    ("gyerekszoba_1", "Gyerekszoba 1", 15.5),
    ("gyerekszoba_2", "Gyerekszoba 2", 22.5),
    ("haloszoba_1", "Hálószoba 1", 22.5),
    ("haloszoba_2", "Hálószoba 2", 22.5),
]
QUEUE_SZUNET = 0.7  # a redony_rf_kuldes ennyit vár a jel után; a részleges mozgásnál ezt levonjuk
FELHUZAS_RAHAGYAS = 1.0  # részleges állás előtt ennyivel tovább várunk a teljes felhúzásra
ESTI_KIVETEL = {"nappali_terasz_1"}


def kuld(slug: str, parancs: str) -> dict:
    """RF-jel a soron keresztül; a hívó megvárja, amíg a jel kiment."""
    return {"action": "script.redony_rf_kuldes", "data": {"eszkoz": slug, "parancs": parancs}}


def pozicio(slug: str) -> str:
    return f"input_number.redony_{slug}_pozicio"


input_number = {
    f"redony_{slug}_pozicio": {"name": f"{nev} pozíció", "min": 0, "max": 100, "step": 1, "mode": "slider",
                               "unit_of_measurement": "%", "icon": "mdi:window-shutter-settings"}
    for slug, nev, _ in REDONYOK
}

covers = []
for slug, nev, _ in REDONYOK:
    mozgat = f"script.redony_{slug}_mozgat"
    covers.append({
        "name": nev,
        "unique_id": f"redony_{slug}",
        "default_entity_id": f"cover.redony_{slug}",
        "device_class": "shutter",
        "position": "{{ states('" + pozicio(slug) + "') | int(0) }}",
        "open_cover": [{"action": "script.turn_on", "target": {"entity_id": mozgat}, "data": {"variables": {"cel": 100}}}],
        "close_cover": [{"action": "script.turn_on", "target": {"entity_id": mozgat}, "data": {"variables": {"cel": 0}}}],
        "set_cover_position": [{"action": "script.turn_on", "target": {"entity_id": mozgat},
                                "data": {"variables": {"cel": "{{ position }}"}}}],
        "stop_cover": [{"action": "script.turn_off", "target": {"entity_id": mozgat}}, kuld(slug, "stop")],
    })

scripts = {
    "redony_rf_kuldes": {
        "alias": "Redőny RF-jel küldése (sorban)", "icon": "mdi:radio-tower", "mode": "queued", "max": 60,
        "fields": {"eszkoz": {"description": "A betanított eszköz neve a Broadlinkon (pl. nappali_terasz_1)"},
                   "parancs": {"description": "fel, le vagy stop"}},
        "sequence": [
            {"action": "remote.send_command", "target": {"entity_id": "remote.vaskut14"},
             "data": {"device": "{{ eszkoz }}", "command": "{{ parancs }}"}},
            {"delay": {"milliseconds": int(QUEUE_SZUNET * 1000)}},
        ],
    },
}
for slug, nev, ido in REDONYOK:
    scripts[f"redony_{slug}_mozgat"] = {
        "alias": f"{nev} – mozgatás", "icon": "mdi:window-shutter-cog", "mode": "restart",
        "fields": {"cel": {"description": "Célpozíció: 0 = zárva, 100 = nyitva"}},
        "sequence": [
            {"variables": {"ido": ido,
                           "c": "{{ [0, [100, cel | int(0)] | min] | max }}"}},
            {"choose": [
                {"conditions": "{{ c >= 100 }}", "sequence": [
                    {"action": "input_number.set_value", "target": {"entity_id": pozicio(slug)}, "data": {"value": 100}},
                    kuld(slug, "fel")]},
                {"conditions": "{{ c <= 0 }}", "sequence": [
                    {"action": "input_number.set_value", "target": {"entity_id": pozicio(slug)}, "data": {"value": 0}},
                    kuld(slug, "le")]},
            ], "default": [
                # Részleges állás: mindig felülről indul, így akkor is pontos, ha közben távirányítóval mozgatták.
                # 1. teljesen fel (teljes futásidő + ráhagyás), 2. le a célig, 3. stop.
                kuld(slug, "fel"),
                {"delay": {"seconds": "{{ (ido - " + str(QUEUE_SZUNET) + " + " + str(FELHUZAS_RAHAGYAS) + ") | round(2) }}"}},
                {"action": "input_number.set_value", "target": {"entity_id": pozicio(slug)}, "data": {"value": 100}},
                {"variables": {"mp": "{{ [(100 - c) / 100 * ido - " + str(QUEUE_SZUNET) + ", 0] | max | round(2) }}"}},
                kuld(slug, "le"),
                {"delay": {"seconds": "{{ mp }}"}},
                kuld(slug, "stop"),
                {"action": "input_number.set_value", "target": {"entity_id": pozicio(slug)}, "data": {"value": "{{ c }}"}},
            ]},
        ],
    }
for kulcs, alias, ikon, svc in (("redonyok_mind_fel", "Minden redőny fel", "mdi:arrow-up-bold-box-outline", "open_cover"),
                                ("redonyok_mind_le", "Minden redőny le", "mdi:arrow-down-bold-box-outline", "close_cover")):
    scripts[kulcs] = {"alias": alias, "icon": ikon, "mode": "single",
                      "sequence": [{"action": f"cover.{svc}", "target": {"entity_id": [f"cover.redony_{s}" for s, _, _ in REDONYOK]}}]}

automation = [{
    "id": "redonyok_esti_lehuzas",
    "alias": "Redőnyök – esti lehúzás (napnyugta + 30 perc)",
    "mode": "single",
    "triggers": [{"trigger": "sun", "event": "sunset", "offset": "00:30:00"}],
    "actions": [{"action": "cover.close_cover",
                 "target": {"entity_id": [f"cover.redony_{s}" for s, _, _ in REDONYOK if s not in ESTI_KIVETEL]}}],
}]

fej = ("# Redőnyök (Broadlink RF) időalapú pozícióval, esti lehúzással.\n"
       "# GENERÁLT FÁJL – a forrás a tools/gen_redonyok.py (futtatás: python tools/gen_redonyok.py .).\n"
       "# A kódok a Pi-n vannak: .storage/broadlink_remote_*_codes (remote.learn_command, eszköz = slug).\n")
tartalom = {"input_number": input_number, "template": [{"cover": covers}], "script": scripts, "automation": automation}
(REPO / "packages" / "redonyok.yaml").write_text(fej + json.dumps(tartalom, ensure_ascii=False, indent=2) + "\n",
                                                encoding="utf-8", newline="\n")
print(f"kész: {len(covers)} redőny, {len(scripts)} szkript")
