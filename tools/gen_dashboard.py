"""Az „Otthon” dashboard egyszerű, mobilos nézete (Bubble Card + visionOS téma).

Kimenet: egy websocket-üzenet JSON-ja, amely az új „Otthon” nézetet teszi az első helyre, a korábbi
részletes nézetet „Részletes” néven megtartja. Használat:
    python tools/gen_dashboard.py <jelenlegi_config.json> <kimenet.json>
"""
import json
import sys

JELEN, KI = sys.argv[1], sys.argv[2]

HALF, FULL = {"columns": 6}, {"columns": "full"}


def jinja_ikon_szin(sensor: str) -> str:
    """Az ikon színe a szoba hőmérsékletét mutatja: hűvös kék, kellemes semleges, meleg narancs."""
    return (".bubble-icon { color: {% set t = states('" + sensor + "') | float(0) %}"
            "{{ '#5AA9E6' if t < 21 else ('#F4A259' if t > 24.5 else 'var(--primary-text-color)') }} !important; }")


def szoba_gomb(nev: str, ikon: str, hash_: str, allapot: str, sensor: str | None = None) -> dict:
    c = {"type": "custom:bubble-card", "card_type": "button", "button_type": "name", "card_layout": "large",
         "name": nev, "icon": ikon, "state_content": allapot, "grid_options": HALF,
         "button_action": {"tap_action": {"action": "navigate", "navigation_path": hash_}},
         "tap_action": {"action": "navigate", "navigation_path": hash_}}
    if sensor:
        c["styles"] = jinja_ikon_szin(sensor)
    return c


def muvelet_gomb(nev: str, ikon: str, szkript: str, megerosites: str | None = None) -> dict:
    act = {"action": "perform-action", "perform_action": "script.turn_on", "target": {"entity_id": szkript}}
    if megerosites:
        act["confirmation"] = {"text": megerosites}
    return {"type": "custom:bubble-card", "card_type": "button", "button_type": "name", "card_layout": "large",
            "name": nev, "icon": ikon, "grid_options": HALF,
            "button_action": {"tap_action": act}, "tap_action": act}


def klima(entity: str, nev: str = "Klíma") -> dict:
    return {"type": "custom:bubble-card", "card_type": "climate", "entity": entity, "name": nev, "state_color": True,
            "grid_options": FULL,
            "sub_button": [{"entity": entity, "name": "Mód", "sub_button_type": "select", "select_attribute": "hvac_modes",
                            "show_arrow": True, "show_state": True, "state_background": False}]}


def redony(slug: str, nev: str) -> dict:
    """Csúszka a pozícióhoz (0 = zárva, 100 = nyitva) és fel / stop / le gomb."""
    e = f"cover.redony_{slug}"
    gomb = lambda ikon, svc: {"icon": ikon, "show_background": True,
                              "tap_action": {"action": "perform-action", "perform_action": f"cover.{svc}",
                                             "target": {"entity_id": e}}}
    return {"type": "custom:bubble-card", "card_type": "button", "button_type": "slider", "entity": e, "name": nev,
            "icon": "mdi:window-shutter", "grid_options": FULL, "state_content": "current_position",
            "sub_button": [gomb("mdi:arrow-up", "open_cover"), gomb("mdi:stop", "stop_cover"),
                           gomb("mdi:arrow-down", "close_cover")]}


def takaritas(szkript: str, nev: str = "Takarítás itt") -> dict:
    act = {"action": "perform-action", "perform_action": "script.turn_on", "target": {"entity_id": szkript}}
    return {"type": "custom:bubble-card", "card_type": "button", "button_type": "name", "name": nev,
            "icon": "mdi:robot-vacuum", "grid_options": FULL, "button_action": {"tap_action": act}, "tap_action": act}


def info(entity: str, nev: str, ikon: str | None = None) -> dict:
    c = {"type": "custom:bubble-card", "card_type": "button", "button_type": "state", "entity": entity, "name": nev,
         "grid_options": HALF}
    if ikon:
        c["icon"] = ikon
    return c


def popup(hash_: str, nev: str, ikon: str, kartyak: list[dict]) -> dict:
    return {"type": "custom:bubble-card", "card_type": "pop-up", "hash": hash_, "name": nev, "icon": ikon,
            "cards": kartyak}


def cim(nev: str) -> dict:
    return {"type": "custom:bubble-card", "card_type": "separator", "name": nev, "grid_options": FULL}


fo = [
    {"type": "heading", "heading": "Otthon", "heading_style": "title", "icon": "mdi:home-heart",
     "badges": [
         {"type": "entity", "entity": "weather.forecast_otthon", "show_state": True, "show_icon": True,
          "state_content": "temperature"},
         {"type": "entity", "entity": "alarm_control_panel.vaskut14_otthon", "show_state": True, "show_icon": True},
         {"type": "entity", "entity": "sensor.porszivo_akkumulator", "show_state": True, "show_icon": True},
     ]},
    szoba_gomb("Nappali", "mdi:sofa", "#nappali",
               "{{ states('sensor.nappali_homerseklet') }} °C{{ ' · klíma' if not is_state('climate.nappali_klima','off') }}",
               "sensor.nappali_homerseklet"),
    szoba_gomb("Hálószoba", "mdi:bed-king", "#haloszoba",
               "{{ states('sensor.haloszoba_homerseklet') }} °C{{ ' · klíma' if not is_state('climate.haloszoba_klima','off') }}",
               "sensor.haloszoba_homerseklet"),
    szoba_gomb("Gyerekszoba", "mdi:teddy-bear", "#gyerekszoba",
               "{{ states('sensor.gyerekszoba_homerseklet') }} °C{{ ' · klíma' if not is_state('climate.gyerekszoba_klima','off') }}",
               "sensor.gyerekszoba_homerseklet"),
    szoba_gomb("Előszoba", "mdi:coat-rack", "#eloszoba",
               "{{ states('sensor.eloter_homerseklet') }} °C · {{ 'ajtó nyitva' if is_state('binary_sensor.vaskut14_bejarat_ajto','on') else 'ajtó zárva' }}",
               "sensor.eloter_homerseklet"),
    szoba_gomb("Konyha", "mdi:stove", "#konyha", "Redőny, takarítás"),
    szoba_gomb("Fürdő", "mdi:shower", "#furdo", "Redőny, takarítás"),
    szoba_gomb("Fűtés", "mdi:radiator", "#futes",
               "{{ state_attr('climate.termosztat','current_temperature') }} °C → {{ state_attr('climate.termosztat','temperature') }} °C",
               None),
    szoba_gomb("Porszívó", "mdi:robot-vacuum", "#porszivo",
               "{{ states('sensor.porszivo_akkumulator') }}% · {{ {'docked':'dokkolva','cleaning':'takarít','returning':'hazamegy',"
               "'paused':'szünetel','idle':'áll','error':'hiba'}.get(states('vacuum.porszivo'), states('vacuum.porszivo')) }}", None),
    cim("Gyors műveletek"),
    muvelet_gomb("Redőnyök le", "mdi:window-shutter", "script.redonyok_mind_le"),
    muvelet_gomb("Redőnyök fel", "mdi:window-shutter-open", "script.redonyok_mind_fel"),
    muvelet_gomb("Éjszakai mód", "mdi:shield-moon", "script.riaszto_ejszakai", "Éjszakai módba kapcsolod a riasztót?"),
    muvelet_gomb("Takarítás", "mdi:broom", "script.porszivo_minden", "Elindítod a takarítást az egész lakásban?"),
]

popupok = [
    popup("#nappali", "Nappali", "mdi:sofa", [
        klima("climate.nappali_klima"),
        cim("Redőnyök"),
        redony("nappali_terasz_1", "Terasz 1"), redony("nappali_terasz_2", "Terasz 2"),
        redony("nappali_ablak_1", "Ablak 1"), redony("nappali_ablak_2", "Ablak 2"),
        cim("Érzékelők"),
        info("sensor.nappali_homerseklet", "Hőmérséklet"), info("binary_sensor.vaskut14_terasz_ajto_ajto", "Teraszajtó"),
    ]),
    popup("#haloszoba", "Hálószoba", "mdi:bed-king", [
        klima("climate.haloszoba_klima"),
        cim("Redőnyök"), redony("haloszoba_1", "Redőny 1"), redony("haloszoba_2", "Redőny 2"),
        takaritas("script.porszivo_haloszoba"),
    ]),
    popup("#gyerekszoba", "Gyerekszoba", "mdi:teddy-bear", [
        klima("climate.gyerekszoba_klima"),
        cim("Redőnyök"), redony("gyerekszoba_1", "Redőny 1"), redony("gyerekszoba_2", "Redőny 2"),
        takaritas("script.porszivo_gyerekszoba"),
    ]),
    popup("#eloszoba", "Előszoba", "mdi:coat-rack", [
        redony("eloszoba", "Redőny"), takaritas("script.porszivo_eloszoba"),
        info("binary_sensor.vaskut14_bejarat_ajto", "Bejárati ajtó"), info("sensor.eloter_homerseklet", "Hőmérséklet"),
    ]),
    popup("#konyha", "Konyha", "mdi:stove", [redony("konyha", "Redőny"), takaritas("script.porszivo_konyha")]),
    popup("#furdo", "Fürdő", "mdi:shower", [redony("furdo", "Redőny"), takaritas("script.porszivo_furdo")]),
    popup("#futes", "Fűtés", "mdi:radiator", [klima("climate.termosztat", "Termosztát")]),
    popup("#porszivo", "Porszívó", "mdi:robot-vacuum", [
        {"type": "tile", "entity": "vacuum.porszivo", "name": "Porszívó", "grid_options": FULL,
         "features": [{"type": "vacuum-commands", "commands": ["start_pause", "stop", "return_home", "locate"]}]},
        cim("Takarítás szobánként"),
        *[{**takaritas(f"script.porszivo_{s}", n), "grid_options": HALF} for s, n in
          [("gyerekszoba", "Gyerekszoba"), ("haloszoba", "Hálószoba"), ("konyha", "Konyha"),
           ("eloszoba", "Előszoba"), ("furdo", "Fürdő"), ("minden", "Mindenhol")]],
        {"type": "picture-entity", "entity": "camera.porszivo_terkep", "camera_view": "auto",
         "show_name": False, "show_state": False, "grid_options": FULL},
    ]),
]

# A Bubble-kártyák a téma (Liquid Glass / visionOS) üveges kártyahátterét és elmosását kapják
UVEG = (":host { --bubble-main-background-color: var(--ha-card-background); "
        "--bubble-pop-up-background-color: var(--ha-card-background); } "
        ".bubble-container { backdrop-filter: var(--ha-card-backdrop-filter); "
        "-webkit-backdrop-filter: var(--ha-card-backdrop-filter); }")


def uvegesit(kartyak: list[dict]) -> None:
    for c in kartyak:
        if c.get("type") == "custom:bubble-card" and c.get("card_type") not in ("separator", "pop-up"):
            c["styles"] = (c.get("styles", "") + " " + UVEG).strip()
        uvegesit(c.get("cards", []))


uvegesit(fo)
uvegesit(popupok)

uj_nezet = {"title": "Otthon", "path": "otthon", "icon": "mdi:home", "type": "sections", "max_columns": 2,
            "sections": [{"type": "grid", "cards": fo}, {"type": "grid", "cards": popupok}]}

cfg = json.load(open(JELEN, encoding="utf-8-sig"))
nezetek = [v for v in cfg["views"] if v.get("path") != "otthon" or v.get("title") != "Otthon" or "sections" not in v
           or not any(c.get("card_type") == "pop-up" for s in v["sections"] for c in s.get("cards", []))]
for v in nezetek:
    if v.get("path") == "otthon":
        v.update(title="Részletes", path="reszletes", icon="mdi:view-dashboard-variant")
cfg["views"] = [uj_nezet] + nezetek
json.dump([{"type": "lovelace/config/save", "url_path": "otthon-homerseklet", "config": cfg}],
          open(KI, "w", encoding="utf-8"), ensure_ascii=False)
print("nézetek:", [v["title"] for v in cfg["views"]])
