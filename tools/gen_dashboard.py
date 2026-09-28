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
    """Csúszka a pozícióhoz (0 = zárva, 100 = nyitva), valamint fel / félig (50%) / stop / le gomb."""
    e = f"cover.redony_{slug}"
    def gomb(ikon: str, svc: str, adat: dict | None = None) -> dict:
        act = {"action": "perform-action", "perform_action": f"cover.{svc}", "target": {"entity_id": e}}
        if adat:
            act["data"] = adat
        return {"icon": ikon, "show_background": True, "tap_action": act}
    return {"type": "custom:bubble-card", "card_type": "button", "button_type": "slider", "entity": e, "name": nev,
            "icon": "mdi:window-shutter", "grid_options": FULL, "state_content": "current_position",
            "sub_button": [gomb("mdi:arrow-up", "open_cover"),
                           gomb("mdi:circle-half-full", "set_cover_position", {"position": 50}),
                           gomb("mdi:stop", "stop_cover"),
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


def valasz_gomb(nev: str, ikon: str, valasz: str) -> dict:
    act = {"action": "perform-action", "perform_action": "script.iskola_valasz", "data": {"valasz": valasz}}
    return {"type": "custom:bubble-card", "card_type": "button", "button_type": "name", "card_layout": "large",
            "name": nev, "icon": ikon, "grid_options": HALF,
            "button_action": {"tap_action": act}, "tap_action": act}


def cim(nev: str) -> dict:
    return {"type": "custom:bubble-card", "card_type": "separator", "name": nev, "grid_options": FULL}


# a BMW i3 töltési állapota magyarul
TOLT = ("{% set t = states('sensor.i3_94_charging_ev_charging_state') %}"
        "{{ {'NOCHARGING':'nem tölt','CHARGINGACTIVE':'tölt','CHARGINGENDED':'töltés vége','CHARGINGPAUSED':'töltés szünetel',"
        "'FINISHED_FULLY_CHARGED':'feltöltve','FINISHED_NOT_FULL':'töltés befejezve','WAITING_FOR_CHARGING':'töltésre vár',"
        "'CHARGINGERROR':'töltési hiba'}.get(t, t | lower) }}")

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
    {**szoba_gomb("BMW i3", "mdi:car-electric", "#auto",
                  "{{ states('sensor.i3_94_battery_ev_state_of_charge') | float(0) | round(0) | int }}% · "
                  "{{ states('sensor.vaskut14_i3_94_range_ev_remaining_range') }} km · " + TOLT, None),
     "grid_options": FULL},
    cim("Gyors műveletek"),
    muvelet_gomb("Redőnyök le", "mdi:window-shutter", "script.redonyok_mind_le"),
    muvelet_gomb("Redőnyök fel", "mdi:window-shutter-open", "script.redonyok_mind_fel"),
    muvelet_gomb("Éjszakai mód", "mdi:shield-moon", "script.riaszto_ejszakai", "Éjszakai módba kapcsolod a riasztót?"),
    muvelet_gomb("Takarítás", "mdi:broom", "script.porszivo_minden", "Elindítod a takarítást az egész lakásban?"),
    {"type": "custom:bubble-card", "card_type": "button", "button_type": "switch", "card_layout": "large",
     "entity": "input_boolean.redony_hovedelem_ma", "name": "Hővédelem ma", "icon": "mdi:sun-thermometer",
     "state_content": "{{ 'Be – ma árnyékolok, ha süt a nap' if is_state('input_boolean.redony_hovedelem_ma','on') else 'Ki – koppints, ha ma meleg lesz' }}",
     "grid_options": FULL},
    {"type": "custom:bubble-card", "card_type": "button", "button_type": "switch", "card_layout": "large",
     "entity": "input_boolean.csepike_itthon", "name": "Csepike itthon maradt", "icon": "mdi:human-child",
     "state_content": "{{ 'Be – amíg itthon van, nem élesítek magamtól' if is_state('input_boolean.csepike_itthon','on') else 'Ki – koppints, ha itthon marad' }}",
     "grid_options": FULL},
    {**szoba_gomb("Automatizmusok", "mdi:robot-happy", "#automatizmusok", "Mi történik magától, és mikor"),
     "grid_options": FULL},
]

# Az automatizmusok összefoglalója (a push is erre nyílik); az élő részek Jinja-sablonok.
AUTOMATIZMUSOK = """## 🌙 Este
**Redőnyök lehúzása.** Napnyugta után fél órával minden redőny lemegy, kivéve a terasz 1-et, mert arra jártok ki.

**Iskolai kérdés (vasárnaptól csütörtökig, 21:00).** Pusht kaptok, hogy megy-e holnap Csepike iskolába. Ha rákoppintasz, megnyílik a válaszpanel. Ha igen, reggel 6:30-kor felmennek a redőnyök, a hálószobaiak kivételével.
Holnap: **{{ 'igen, 6:30-kor felmennek a redőnyök' if is_state('input_boolean.iskola_holnap','on') else 'nincs redőnyhúzás' }}**.

**Riasztó-emlékeztető (21:30).** Ha valaki itthon van, de a riasztó nincs éjszakai vagy távol módban, kritikus pusht kapsz, amely a Ne zavarjanak módon is átjön. \
Ha rákoppintasz, megnyílik egy ablak, ahol egy gombbal éjszakai módba kapcsolhatod.
Az emlékeztető: **{{ 'bekapcsolva' if is_state('automation.riaszto_22_00_emlekezteto_ha_nincs_ejszakai_modban', 'on') else 'kikapcsolva' }}**. A riasztó most: **{{ {'disarmed':'kikapcsolva','armed_night':'éjszakai mód','armed_home':'otthon mód','armed_away':'élesítve (távol)',
'arming':'élesítés folyamatban','triggered':'RIASZT'}.get(states('alarm_control_panel.vaskut14_otthon'), states('alarm_control_panel.vaskut14_otthon')) }}**.

## ☀️ Reggel
**Ébresztő.** Hanggal vagy a dashboardon állítható. Ébredéskor pusht kapsz (Leállítás vagy Még 10 perc), a hálószoba redőnyei előbb félig, 3 perc múlva teljesen felmennek, fűtési szezonban pedig a termosztát 21 °C-ra áll.
Az ébresztő most: **{% if is_state('input_boolean.ebreszto_aktiv','on') %}bekapcsolva, {{ states('input_datetime.ebreszto_ido')[:5] }} ({{ states('input_select.ebreszto_ismetles') | lower }}){% else %}kikapcsolva{% endif %}**.

**Iskolai reggel (6:30).** Kikapcsol a riasztó éjszakai módja (ha valamelyikőtök itthon van), \
és felmennek a redőnyök, a hálószobaiak kivételével. Csak akkor fut le, ha előző este igent nyomtatok, \
vagy hanggal kértétek (például: „Hey Mycroft, holnap ébreszd Csepikét fél hétkor”).

## 🏠 Távozás és hazaérkezés
**Elmentünk.** Ha mindketten 100 méternél messzebb vagytok, és a telefonotok a Wi-Firől is lecsatlakozott, \
5 perc múlva magától élesíti a riasztót, és ha ma még nem volt, elindítja a takarítást. Addig a pushra koppintva \
leállíthatjátok („Ne élesíts”), itthonról pedig a nappali Voice-nak szólva: „Hey Mycroft, itthon vagyok”. \
Ha valami arra utal, hogy valaki otthon van (Xbox, tévé, Apple TV, Csepike iPadjének forgalma, azóta nyílt bejárati ajtó, \
vagy be van kapcsolva a „Csepike itthon maradt” kapcsoló), nem élesít, csak rákérdez. A kapcsoló éjjel magától kikapcsol.

**Nappali takarítás.** A porszívó magától nem jut le, ezért a nappali parancsra előbb kimossa a felmosót, és a nappali Voice szól, \
hogy le lehet vinni. Lent porszívóz és felmos, a szőnyeget erős szívással és mélytisztítással takarítja. \
Ha közben elakad vagy lemerülőben van, a Voice szól, a végén pedig kéri, hogy vigyétek vissza a dokkolóra.

**Hazaérkezés.** Ha Ádám vagy Cerike telefonja az otthoni Wi-Fire csatlakozik, és 100 méteren belül van, a távol módban \
élesített riasztó magától kikapcsol (éjszakai módhoz nem nyúl). Ha üres lakásba, takarítás közben értek haza, a porszívó hazamegy, \
és ha a riasztó másfél perc múlva is élesítve van, szól.

## 🌡️ Nyári hővédelem
Májustól szeptemberig, ha kint legalább 28 °C van, azokat a redőnyöket, amelyekre éppen süt a nap, 70%-ban lehúzza. Ha a nap továbbvonult, vagy kint 26 °C alá hűlt, visszahúzza őket. A „Hővédelem ma” kapcsolóval bármelyik napon bekapcsolható, éjfélkor pedig magától kikapcsol.
Ma: **{{ 'bekapcsolva' if is_state('input_boolean.redony_hovedelem_ma','on') else 'automatikus' }}**.

## 🚗 Autó (BMW i3)
**Esti ellenőrzés (21:30, Ádámnak).** Ha az autó otthon áll, 40% alatt van, és nincs bedugva, szól, hogy dugd be. \
Ha holnap reggel fagyos idő lesz, emlékeztet, hogy állítsd be a MyBMW appban az előfűtést.

**Alacsony töltöttség (Ádámnak).** Ha 20% vagy 30 km alá esik, és nincs bedugva, szól.

**Heti összefoglaló (vasárnap 18:00, Ádámnak).** Hány kilométert mentél, mennyit töltöttél, és ez nagyjából mennyibe került \
(az áramár az autó ablakában állítható).

**Nincs bezárva.** Ha az autó nincs bezárva, vagy kívülről bezártátok, de nyitva maradt egy ablaka, annak szól, \naki mellette volt, és eltávolodott tőle. Ha valaki benne ül vagy vezeti, nem szól.

**Távozás.** Ha az autó elhagyja a házat, az is jel az „Elmentünk” rutinnak. Hanggal is megkérdezheted: „Hey Mycroft, mennyi a töltöttség?”

Az i3 ritkán küld adatot (zárás után, parkoláskor, töltés közben nem), ezért az értesítések késhetnek.

## 🎙️ Egyéb
**Rádió.** „Hey Mycroft, kapcsolj rádiót” → bekapcsol a nappali tévé (HDMI1, 8-as hangerő), és a House Nation UK szól; \
„Hey Mycroft, kapcsold be a Rádió 1-et” → a magyar Rádió 1; „Hey Mycroft, kapcsold ki a rádiót” → a tévé is kikapcsol.

**Mycroft.** A „Hey Mycroft” után magyarul irányíthatod a redőnyöket, a klímákat, a fűtést, a porszívót, az ébresztőt és a riasztó élesítését. Hatástalanítani csak az Ajax appban vagy a kezelőn lehet.

**Tanulás.** Vasárnap 18:00-kor összefoglalót kapsz a meg nem értett parancsokról. Újat csak a jóváhagyásod után tanul meg.

**Mentés.** Minden éjjel 3:30-kor titkosított mentés készül a NAS-ra, és az utolsó 14 megmarad.
"""

def auto_info(entity: str, nev: str, ikon: str, tartalom: str | None = None) -> dict:
    c = {"type": "custom:bubble-card", "card_type": "button", "button_type": "state", "entity": entity, "name": nev,
         "icon": ikon, "grid_options": HALF}
    if tartalom:
        c["state_content"] = tartalom
    return c


popupok = [
    popup("#nappali", "Nappali", "mdi:sofa", [
        klima("climate.nappali_klima"),
        cim("Redőnyök"),
        redony("nappali_terasz_1", "Terasz 1"), redony("nappali_terasz_2", "Terasz 2"),
        redony("nappali_ablak_1", "Ablak 1"), redony("nappali_ablak_2", "Ablak 2"),
        cim("Érzékelők"),
        info("sensor.nappali_homerseklet", "Hőmérséklet"), info("binary_sensor.vaskut14_terasz_ajto_ajto", "Teraszajtó"),
        takaritas("script.porszivo_nappali", "Takarítás itt (előbb vidd le)"),
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
    # az esti iskolai push koppintásra ide nyílik (packages/iskola.yaml)
    popup("#iskola", "Holnap iskola?", "mdi:school", [
        {"type": "custom:bubble-card", "card_type": "button", "button_type": "state", "card_layout": "large",
         "entity": "input_boolean.iskola_holnap", "name": "Holnap reggel", "icon": "mdi:school", "grid_options": FULL,
         "state_content": "{{ '6:30-kor felhúzom a redőnyöket.' if is_state('input_boolean.iskola_holnap','on') "
                          "else 'Nem húzom fel a redőnyöket.' }}"},
        valasz_gomb("Igen, megy", "mdi:check-bold", "igen"),
        valasz_gomb("Nem", "mdi:close-thick", "nem"),
    ]),
    # az esti riasztó-emlékeztető push koppintásra ide nyílik (packages/riaszto.yaml)
    popup("#riaszto", "Riasztó", "mdi:shield-moon", [
        {"type": "custom:bubble-card", "card_type": "button", "button_type": "state", "card_layout": "large",
         "entity": "alarm_control_panel.vaskut14_otthon", "name": "Most", "icon": "mdi:shield-home", "grid_options": FULL,
         "state_content": "{{ {'disarmed':'Kikapcsolva','armed_night':'Éjszakai mód','armed_home':'Otthon mód',"
                          "'armed_away':'Élesítve (távol)','arming':'Élesítés folyamatban','triggered':'RIASZT'}"
                          ".get(states('alarm_control_panel.vaskut14_otthon'), states('alarm_control_panel.vaskut14_otthon')) }}"},
        {**muvelet_gomb("Éjszakai mód bekapcsolása", "mdi:shield-moon", "script.riaszto_esti_bekapcsolas"),
         "grid_options": FULL},
    ]),
    # a távozás utáni push koppintásra ide nyílik (packages/elmentunk.yaml)
    popup("#elmentunk", "Elmentetek", "mdi:home-export-outline", [
        {"type": "custom:bubble-card", "card_type": "button", "button_type": "state", "card_layout": "large",
         "entity": "timer.elmentunk_elesites", "name": "Riasztó", "icon": "mdi:shield-sync", "grid_options": FULL,
         "state_content": "{% if is_state('timer.elmentunk_elesites', 'active') %}Élesítés "
                          "{{ (state_attr('timer.elmentunk_elesites', 'finishes_at') | as_datetime | as_local).strftime('%H:%M') }}-kor"
                          "{{ ', takarítás nélkül' if is_state('input_boolean.elmentunk_ne_takarits', 'on') else ', utána takarítás' }}"
                          "{% else %}Most nincs folyamatban élesítés.{% endif %}"},
        {"type": "custom:bubble-card", "card_type": "button", "button_type": "switch", "card_layout": "large",
         "entity": "input_boolean.csepike_itthon", "name": "Csepike itthon maradt", "icon": "mdi:human-child",
         "state_content": "{{ 'Be – amíg itthon van, nem élesítek magamtól' if is_state('input_boolean.csepike_itthon','on') else 'Ki – koppints, ha itthon marad' }}",
         "grid_options": FULL},
        {**muvelet_gomb("Ne élesíts – valaki itthon van", "mdi:shield-off-outline", "script.elmentunk_leallit"),
         "grid_options": FULL},
        muvelet_gomb("Ne takaríts", "mdi:robot-vacuum-off", "script.elmentunk_ne_takarits"),
        muvelet_gomb("Élesíts most", "mdi:shield-lock", "script.elmentunk_most"),
    ]),
    # BMW i3 (HACS kvanbiesen/bmw-cardata-ha): az i3 ritkán küld adatot, jellemzően csak leállításkor
    popup("#auto", "BMW i3", "mdi:car-electric", [
        {"type": "picture-entity", "entity": "image.i3_94_vehicle_image", "show_name": False, "show_state": False,
         "grid_options": FULL},
        auto_info("sensor.i3_94_battery_ev_state_of_charge", "Töltöttség", "mdi:battery-high",
                  "{{ states('sensor.i3_94_battery_ev_state_of_charge') | float(0) | round(0) | int }}%"),
        auto_info("sensor.vaskut14_i3_94_range_ev_remaining_range", "Hatótáv", "mdi:map-marker-distance"),
        auto_info("sensor.i3_94_charging_ev_charging_state", "Töltés", "mdi:ev-station", TOLT),
        auto_info("sensor.i3_94_battery_ev_target_state_of_charge", "Töltési cél", "mdi:battery-charging-high"),
        auto_info("sensor.i3_94_charging_ev_predicted_state_of_charge", "Becsült", "mdi:battery-sync",
                  "{{ states('sensor.i3_94_charging_ev_predicted_state_of_charge') | float(0) | round(0) | int }}%"),
        auto_info("sensor.i3_94_vehicle_mileage", "Kilométeróra", "mdi:counter",
                  "{{ '{:,}'.format(states('sensor.i3_94_vehicle_mileage') | float(0) | int).replace(',', ' ') }} km"),
        auto_info("sensor.vaskut14_i3_94ah_last_telematics_api_call", "Utolsó adat", "mdi:clock-outline",
                  "{{ as_timestamp(states('sensor.vaskut14_i3_94ah_last_telematics_api_call')) | timestamp_custom('%m.%d. %H:%M') }}"),
        auto_info("sensor.i3_94_battery_hv_energy_content", "Akku energia", "mdi:lightning-bolt"),
        auto_info("sensor.vaskut14_i3_94_doors_overall_state", "Zár", "mdi:car-door-lock",
                  "{{ {'SECURED':'bezárva','LOCKED':'bezárva','UNLOCKED':'nincs bezárva','SELECTIVE_LOCKED':'részben zárva'}"
                  ".get(states('sensor.vaskut14_i3_94_doors_overall_state'), states('sensor.vaskut14_i3_94_doors_overall_state') | lower) }}"),
        auto_info("sensor.vaskut14_i3_94_charging_port_plug_state", "Töltőkábel", "mdi:ev-plug-type2",
                  "{{ 'bedugva' if states('sensor.vaskut14_i3_94_charging_port_plug_state') == 'CONNECTED' else 'nincs bedugva' }}"),
        auto_info("sensor.i3_heti_km", "E heti km", "mdi:road-variant",
                  "{{ states('sensor.i3_heti_km') | float(0) | round(0) | int }} km"),
        auto_info("input_number.aram_ar", "Áramár", "mdi:cash",
                  "{{ states('input_number.aram_ar') | float(0) | round(1) | replace('.', ',') }} Ft/kWh"),
        {"type": "map", "entities": ["device_tracker.i3_94_location"], "default_zoom": 15, "grid_options": FULL},
    ]),
    popup("#automatizmusok", "Automatizmusok", "mdi:robot-happy", [
        {"type": "markdown", "content": AUTOMATIZMUSOK, "grid_options": FULL},
    ]),
    popup("#porszivo", "Porszívó", "mdi:robot-vacuum", [
        {"type": "tile", "entity": "vacuum.porszivo", "name": "Porszívó", "grid_options": FULL,
         "features": [{"type": "vacuum-commands", "commands": ["start_pause", "stop", "return_home", "locate"]}]},
        cim("Takarítás szobánként"),
        *[{**takaritas(f"script.porszivo_{s}", n), "grid_options": HALF} for s, n in
          [("gyerekszoba", "Gyerekszoba"), ("haloszoba", "Hálószoba"), ("konyha", "Konyha"),
           ("eloszoba", "Előszoba"), ("furdo", "Fürdő"), ("nappali", "Nappali (levinni)"),
           ("minden", "Mindenhol (fent)")]],
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
