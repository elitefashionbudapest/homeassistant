"""Generálja a packages/redonyok.yaml-t: 11 RF-redőny időalapú pozícióval, esti lehúzás, nyári hővédelem.

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

# Nyári hővédelem: ablaksorok tájolása (azimut, fok) – Ádám mérése, 2026-09-27.
# A terasz 1 kimarad, mert arra járnak ki (ahogy az esti lehúzásból is).
HOVEDELEM_OLDALAK = [
    ("dk_terasz", "Terasz (DK, 150°)", 150, ["nappali_terasz_2"]),
    ("dk_halo", "Hálószoba 2 (DK, 141°)", 141, ["haloszoba_2"]),
    ("dny", "Nappali ablak 1, előszoba, konyha (DNy, 220°)", 220, ["nappali_ablak_1", "eloszoba", "konyha"]),
    ("eny", "Nappali ablak 2, fürdő, gyerekszoba 1 (ÉNy, 320°)", 320, ["nappali_ablak_2", "furdo", "gyerekszoba_1"]),
    ("ek", "Gyerekszoba 2, hálószoba 1 (ÉK, 49°)", 49, ["gyerekszoba_2", "haloszoba_1"]),
]
HOVEDELEM_KINT_MIN = 28      # °C – automatikusan csak ennél melegebb kinti hőmérsékletnél árnyékol
HOVEDELEM_KINT_VISSZA = 26   # °C – ez alá hűlve húzza vissza (hiszterézis, hogy ne menjen folyton fel-le)
HOVEDELEM_HONAPOK = (5, 9)   # automatikus mód csak májustól szeptemberig; télen a nap süssön be
HOVEDELEM_SZOG = 60          # ha a nap ennél kisebb szögben süt az ablak felé
HOVEDELEM_NAPMAGASSAG = 10   # ° – ennél alacsonyabb napnál nem árnyékol
HOVEDELEM_POZICIO = 30       # % nyitva árnyékoláskor = 70%-ban lent (Ádám kérése)


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

input_boolean = {"redony_hovedelem_aktiv": {"name": "Redőny hővédelem (automatikus, nyáron)", "icon": "mdi:weather-sunny-alert"},
                 "redony_hovedelem_ma": {"name": "Hővédelem ma", "icon": "mdi:sun-thermometer"}}
for kulcs, nev, _, _ in HOVEDELEM_OLDALAK:
    input_boolean[f"redony_hovedelem_{kulcs}"] = {"name": f"Hővédelem árnyékol – {nev}", "icon": "mdi:sun-angle"}

automation.append({
    "id": "redonyok_hovedelem",
    "alias": "Redőnyök – nyári hővédelem (napirány szerint)",
    "description": "Ha a nap egy ablaksorra süt, és vagy be van kapcsolva a „Hővédelem ma”, vagy nyár van "
                   "(máj–szept) és kint legalább 28 °C, akkor azokat a redőnyöket részben leengedi. Ha a nap napközben "
                   "elvonul, vagy a feltétel megszűnik, visszahúzza. Naplemente után nem húz fel semmit.",
    "mode": "single",
    "triggers": [{"trigger": "time_pattern", "minutes": "/5"}],
    "actions": [{"repeat": {
        "for_each": [{"flag": f"input_boolean.redony_hovedelem_{k}", "azimut": az,
                      "coverek": [f"cover.redony_{s}" for s in cs]} for k, _, az, cs in HOVEDELEM_OLDALAK],
        "sequence": [
            {"variables": {
                "nap_az": "{{ state_attr('sun.sun', 'azimuth') | float(0) }}",
                "nap_mag": "{{ state_attr('sun.sun', 'elevation') | float(-90) }}",
                "kint": "{{ state_attr('weather.forecast_otthon', 'temperature') | float(0) }}",
                "szog": "{{ (((nap_az - repeat.item.azimut + 540) % 360) - 180) | abs }}",
                "napos": "{{ nap_mag >= " + str(HOVEDELEM_NAPMAGASSAG) + " and szog <= " + str(HOVEDELEM_SZOG) + " }}",
                "ma": "{{ is_state('input_boolean.redony_hovedelem_ma', 'on') }}",
                "auto": "{{ is_state('input_boolean.redony_hovedelem_aktiv', 'on') and "
                        + str(HOVEDELEM_HONAPOK[0]) + " <= now().month <= " + str(HOVEDELEM_HONAPOK[1]) + " }}",
                "indit": "{{ ma or (auto and kint >= " + str(HOVEDELEM_KINT_MIN) + ") }}",
                "tart": "{{ ma or (auto and kint >= " + str(HOVEDELEM_KINT_VISSZA) + ") }}",
                "arnyekol": "{{ is_state(repeat.item.flag, 'on') }}"}},
            {"choose": [
                {"conditions": "{{ napos and indit and not arnyekol }}", "sequence": [
                    {"action": "cover.set_cover_position", "target": {"entity_id": "{{ repeat.item.coverek }}"},
                     "data": {"position": HOVEDELEM_POZICIO}},
                    {"action": "input_boolean.turn_on", "target": {"entity_id": "{{ repeat.item.flag }}"}}]},
                {"conditions": "{{ arnyekol and not (napos and tart) }}", "sequence": [
                    {"if": "{{ nap_mag > 5 }}", "then": [
                        {"action": "cover.open_cover", "target": {"entity_id": "{{ repeat.item.coverek }}"}}]},
                    {"action": "input_boolean.turn_off", "target": {"entity_id": "{{ repeat.item.flag }}"}}]},
            ]},
        ]}}],
})

automation.append({
    "id": "redonyok_hovedelem_ma_azonnal",
    "alias": "Redőnyök – „Hővédelem ma” azonnali futtatás",
    "mode": "restart",
    "triggers": [{"trigger": "state", "entity_id": "input_boolean.redony_hovedelem_ma", "to": ["on", "off"]}],
    "actions": [{"action": "automation.trigger", "target": {"entity_id": "automation.redonyok_nyari_hovedelem_napirany_szerint"},
                 "data": {"skip_condition": False}}],
})
automation.append({
    "id": "redonyok_hovedelem_ma_ejfel",
    "alias": "Redőnyök – „Hővédelem ma” kikapcsolása éjfélkor",
    "mode": "single",
    "triggers": [{"trigger": "time", "at": "00:00:00"}],
    "conditions": [{"condition": "state", "entity_id": "input_boolean.redony_hovedelem_ma", "state": "on"}],
    "actions": [{"action": "input_boolean.turn_off", "target": {"entity_id": "input_boolean.redony_hovedelem_ma"}}],
})

fej = ("# Redőnyök (Broadlink RF) időalapú pozícióval, esti lehúzással.\n"
       "# GENERÁLT FÁJL – a forrás a tools/gen_redonyok.py (futtatás: python tools/gen_redonyok.py .).\n"
       "# A kódok a Pi-n vannak: .storage/broadlink_remote_*_codes (remote.learn_command, eszköz = slug).\n")
tartalom = {"input_number": input_number, "input_boolean": input_boolean, "template": [{"cover": covers}], "script": scripts, "automation": automation}
(REPO / "packages" / "redonyok.yaml").write_text(fej + json.dumps(tartalom, ensure_ascii=False, indent=2) + "\n",
                                                encoding="utf-8", newline="\n")
print(f"kész: {len(covers)} redőny, {len(scripts)} szkript")
