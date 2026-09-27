"""Generálja a magyar mondatmintákat (custom_sentences) és a végrehajtó intent_script-et."""
import json
import sys
from pathlib import Path

REPO = Path(sys.argv[1])


def lst(mapping: dict[str, list[str]]) -> dict:
    return {"values": [{"in": w, "out": out} for out, words in mapping.items() for w in words]}


# --- szavak -------------------------------------------------------------------
IRANY = {
    "fel": ["húzd fel", "húzza fel", "húzd föl", "emeld fel", "engedd fel", "nyisd ki", "nyissa ki", "nyisd fel",
            "húzd fel nekem"],
    "le": ["engedd le", "engedje le", "húzd le", "húzza le", "ereszd le", "eresszd le", "zárd be", "zárja be",
           "csukd be", "engedd le nekem"],
    "stop": ["állítsd meg", "állítsa meg", "állj meg", "állítsd le", "stop"],
}
SZOBA = {  # redőny/terület → area_id
    "nappali": ["nappali", "nappaliban", "nappalit", "nappalinak"],
    "haloszoba": ["hálószoba", "hálószobában", "hálószobát", "hálószobai", "háló", "hálóban", "hálót"],
    "gyerekszoba": ["gyerekszoba", "gyerekszobában", "gyerekszobát", "gyerekszobai", "gyerek szoba",
                    "gyerek szobában", "gyerekszobának"],
    "konyha": ["konyha", "konyhában", "konyhát", "konyhai"],
    "eloter": ["előszoba", "előszobában", "előszobát", "előszobai", "előtér", "előtérben", "folyosó", "folyosón"],
    "furdo": ["fürdő", "fürdőben", "fürdőt", "fürdőszoba", "fürdőszobában", "fürdőszobát", "fürdőszobai"],
}
EGYEDI = {
    "nappali_terasz_1": ["terasz 1", "terasz egy", "terasz egyes", "első terasz", "egyes terasz", "első teraszt", "terasz egyet", "egyes teraszt"],
    "nappali_terasz_2": ["terasz 2", "terasz kettő", "terasz kettes", "második terasz", "kettes terasz", "második teraszt", "terasz kettőt", "kettes teraszt"],
    "nappali_ablak_1": ["ablak 1", "ablak egy", "ablak egyes", "első ablak", "első ablakot", "ablak egyet", "egyes ablakot"],
    "nappali_ablak_2": ["ablak 2", "ablak kettő", "ablak kettes", "második ablak", "második ablakot", "ablak kettőt", "kettes ablakot"],
    "haloszoba_1": ["hálószoba 1", "hálószoba egy", "háló 1", "háló egy"],
    "haloszoba_2": ["hálószoba 2", "hálószoba kettő", "háló 2", "háló kettő"],
    "gyerekszoba_1": ["gyerekszoba 1", "gyerekszoba egy"],
    "gyerekszoba_2": ["gyerekszoba 2", "gyerekszoba kettő"],
}
PORSZIVO = {  # → script.porszivo_<out>
    "konyha": SZOBA["konyha"],
    "eloszoba": SZOBA["eloter"],
    "furdo": SZOBA["furdo"],
    "haloszoba": SZOBA["haloszoba"],
    "gyerekszoba": SZOBA["gyerekszoba"],
}
KLIMA = {
    "climate.nappali_klima": ["nappali", "nappaliban", "nappalit"],
    "climate.haloszoba_klima": ["hálószoba", "hálószobai", "hálószobában", "hálószobát", "háló", "hálóban", "hálót"],
    "climate.gyerekszoba_klima": ["gyerekszoba", "gyerekszobai", "gyerekszobában", "gyerekszobát",
                                  "gyerek szobában"],
}
KAPCS = {"be": ["kapcsold be", "kapcsolja be", "kapcsold fel", "indítsd el", "indítsd"],
         "ki": ["kapcsold ki", "kapcsolja ki", "kapcsold le", "állítsd le"]}
MOD = {"cool": ["hűtésre", "hűtés módba", "hűtő módba"], "heat": ["fűtésre", "fűtés módba", "fűtő módba"],
       "fan_only": ["ventilátorra", "ventilátor módba", "szellőztetésre"], "dry": ["szárításra", "párátlanításra"],
       "auto": ["automatára", "automatikusra", "auto módba", "automata módba"]}
HOMERO = {
    "sensor.nappali_homerseklet": ["nappali", "nappaliban"],
    "sensor.haloszoba_homerseklet": ["hálószoba", "hálószobában", "háló", "hálóban"],
    "sensor.gyerekszoba_homerseklet": ["gyerekszoba", "gyerekszobában", "gyerek szobában"],
    "sensor.eloter_homerseklet": ["előszoba", "előszobában", "előtér", "előtérben", "folyosón"],
    "kint": ["kint", "kinn", "odakint", "kint az udvaron", "a szabadban"],
}

sentences = {
    "language": "hu",
    "expansion_rules": {
        "kerlek": "(kérlek|kérem|légyszi|légy szíves|légyszíves|jarvis|hé jarvis|hey jarvis|szia jarvis)",
        "redonyok": "(redőny|redőnyt|redőnyök|redőnyöket|redőnyeit|redőnyét|redőnyöt|árnyékolót|árnyékolókat|rolót|rolókat)",
        "osszes": "(az összes|minden|mindegyik|összes)",
        "takarit": "(takarítsd|porszívózd|szívd|mosd|takaríts|porszívózz|takarítson|porszívózzon|takarítsa) [ki|fel|meg]",
        "indit": "(indítsd|indítsa|kezdd|kezdje|indítsad) [el]",
        "klima": "(klímát|klíma|légkondit|légkondicionálót|klímáját)",
        "futes": "(fűtést|fűtés|termosztátot|termosztát|kazánt)",
        "riaszto": "(riasztót|riasztó|riasztórendszert|ajaxot)",
        "fokra": "(fokra|fok|fokosra|celsius fokra)",
    },
    "lists": {
        "irany": lst(IRANY), "szoba": lst(SZOBA), "egyedi": lst(EGYEDI), "psz": lst(PORSZIVO),
        "klima": lst(KLIMA), "kapcs": lst(KAPCS), "mod": lst(MOD), "homero": lst(HOMERO),
        "fok": {"range": {"from": 16, "to": 30}},
    },
    "intents": {
        "RedonySzoba": {"data": [{"sentences": [
            "[<kerlek>] ({irany}; [a |az ]<redonyok>; [a |az ]{szoba}) [<kerlek>]",
            "[<kerlek>] ({irany}; [a |az ]{szoba} <redonyok>) [<kerlek>]",
        ]}]},
        "RedonyEgyedi": {"data": [{"sentences": [
            "[<kerlek>] ({irany}; [a |az ][nappali ]{egyedi} [<redonyok>]) [<kerlek>]",
        ]}]},
        "RedonyMind": {"data": [{"sentences": [
            "[<kerlek>] ({irany}; <osszes> <redonyok>) [mindenhol|a lakásban|a házban] [<kerlek>]",
            "[<kerlek>] ({irany}; [a ]<redonyok> mindenhol) [<kerlek>]",
        ]}]},
        "KlimaKapcs": {"data": [{"sentences": [
            "[<kerlek>] ({kapcs}; [a |az ]<klima>; [a |az ]{klima}) [<kerlek>]",
            "[<kerlek>] ({kapcs}; [a |az ]{klima} <klima>) [<kerlek>]",
        ]}]},
        "KlimaMind": {"data": [{"sentences": [
            "[<kerlek>] ({kapcs}; <osszes> (klímát|klímákat|légkondit)) [<kerlek>]",
        ]}]},
        "KlimaHofok": {"data": [{"sentences": [
            "[<kerlek>] ((állítsd|állítsa|tedd|rakd|legyen); [a |az ]{klima} [<klima>]; {fok} <fokra>) [<kerlek>]",
            "[<kerlek>] ((állítsd|állítsa|tedd|rakd); [a |az ]<klima>; [a |az ]{klima}; {fok} <fokra>) [<kerlek>]",
            "[<kerlek>] legyen {fok} fok [a |az ]{klima} [<kerlek>]",
        ]}]},
        "KlimaMod": {"data": [
            {"sentences": ["[<kerlek>] ((kapcsold|állítsd|tedd|váltsd|kapcsolja|állítsa); [a |az ]{klima} [<klima>]; {mod}) [<kerlek>]",
                           "[<kerlek>] ((kapcsold|állítsd|tedd|váltsd); [a |az ]<klima>; [a |az ]{klima}; {mod}) [<kerlek>]"]},
            {"sentences": ["[<kerlek>] ((hűtsd le|hűtsd|hűtse le); [a |az ]{klima}) [<kerlek>]"], "slots": {"mod": "cool"}},
            {"sentences": ["[<kerlek>] ((fűtsd fel|fűtsd be|fűtse fel|melegítsd fel); [a |az ]{klima}) [<kerlek>]"], "slots": {"mod": "heat"}},
        ]},
        "FutesHofok": {"data": [{"sentences": [
            "[<kerlek>] ((állítsd|állítsa|tedd|rakd); [a ]<futes>; {fok} <fokra>) [<kerlek>]",
            "[<kerlek>] legyen {fok} fok [a ]<futes> [<kerlek>]",
        ]}]},
        "FutesKapcs": {"data": [
            {"sentences": ["[<kerlek>] ({kapcs}; [a ]<futes>) [<kerlek>]"]},
            {"sentences": ["[<kerlek>] ((kapcsold|állítsd|tedd); [a ]<futes>; (automatára|automatikusra|programra))"],
             "slots": {"kapcs": "auto"}},
        ]},
        "PorszivoSzoba": {"data": [{"sentences": [
            "[<kerlek>] (<takarit>; [a |az ]{psz}) [<kerlek>]",
            "[<kerlek>] (<indit>; [a ](takarítást|porszívózást|porszívót|felmosást); [a |az ]{psz}) [<kerlek>]",
            "[<kerlek>] [a ]porszívó (takarítson|menjen|porszívózzon) [a |az ]{psz} [<kerlek>]",
        ]}]},
        "PorszivoNappali": {"data": [{"sentences": [
            "[<kerlek>] (<takarit>; [a ](nappalit|nappaliban)) [<kerlek>]",
            "[<kerlek>] (<indit>; [a ](takarítást|porszívózást|porszívót); [a ](nappaliban|nappalit)) [<kerlek>]",
        ]}]},
        "PorszivoMind": {"data": [{"sentences": [
            "[<kerlek>] (<takarit>; (az egész lakást|mindenhol|az összes szobát|minden szobát|a lakást|a házat|mindent)) [<kerlek>]",
            "[<kerlek>] <indit> a (porszívót|takarítást|porszívózást) [mindenhol] [<kerlek>]",
        ]}]},
        "PorszivoHaza": {"data": [{"sentences": [
            "[<kerlek>] ((küldd|vidd|küldje) (haza|vissza); a porszívót) [a dokkolóba|a töltőre|tölteni] [<kerlek>]",
            "[<kerlek>] [a ]porszívó menjen (haza|vissza) [<kerlek>]",
        ]}]},
        "PorszivoStop": {"data": [{"sentences": [
            "[<kerlek>] ((állítsd le|állítsd meg|állítsa le|szüneteltesd); a (porszívót|takarítást|porszívózást)) [<kerlek>]",
        ]}]},
        "RiasztoEjszakai": {"data": [{"sentences": [
            "[<kerlek>] ((kapcsold|tedd|állítsd|kapcsolja|állítsa); [a ]<riaszto>; éjszakai (módba|üzemmódba)) [<kerlek>]",
            "[<kerlek>] ((élesítsd|élesítse|kapcsold be); [a ]<riaszto>; (éjszakára|éjszakai módban|éjszakai módba)) [<kerlek>]",
        ]}]},
        "RiasztoElesites": {"data": [{"sentences": [
            "[<kerlek>] (élesítsd|élesítse|kapcsold be|kapcsolja be) [a ]<riaszto> [teljesen] [<kerlek>]",
        ]}]},
        "RiasztoKi": {"data": [{"sentences": [
            "[<kerlek>] ((hatástalanítsd|hatástalanítsa|kapcsold ki|kapcsolja ki|kapcsold le|oldd fel); [a ]<riaszto>) [<kerlek>]",
        ]}]},
        "Homerseklet": {"data": [{"sentences": [
            "[<kerlek>] (hány fok van|hány fok|mennyi a hőmérséklet|milyen meleg van|milyen hideg van|mennyi fok van) [most] [a |az ]{homero} [<kerlek>]",
            "[<kerlek>] [a |az ]{homero} (hány fok van|mennyi a hőmérséklet|milyen meleg van) [most] [<kerlek>]",
        ]}]},
    },
}

HELY = ("{% set hely = {'nappali':'a nappaliban','haloszoba':'a hálószobában','gyerekszoba':'a gyerekszobában',"
        "'konyha':'a konyhában','eloter':'az előszobában','furdo':'a fürdőben'} %}")
RNEV = ("{% set rnev = {'nappali_terasz_1':'a nappali terasz 1','nappali_terasz_2':'a nappali terasz 2',"
        "'nappali_ablak_1':'a nappali ablak 1','nappali_ablak_2':'a nappali ablak 2','haloszoba_1':'a hálószoba 1',"
        "'haloszoba_2':'a hálószoba 2','gyerekszoba_1':'a gyerekszoba 1','gyerekszoba_2':'a gyerekszoba 2'} %}")
KNEV = ("{% set knev = {'climate.nappali_klima':'a nappali','climate.haloszoba_klima':'a hálószoba',"
        "'climate.gyerekszoba_klima':'a gyerekszoba'} %}")
PNEV = ("{% set pnev = {'konyha':'a konyhában','eloszoba':'az előszobában','furdo':'a fürdőben',"
        "'haloszoba':'a hálószobában','gyerekszoba':'a gyerekszobában'} %}")
MNEV = "{% set mnev = {'cool':'hűtésre','heat':'fűtésre','fan_only':'ventilátorra','dry':'szárításra','auto':'automatára'} %}"
COVER_ACT = "cover.{{ {'fel':'open_cover','le':'close_cover'}.get(irany, 'stop_cover') }}"
IGE = "{{ {'fel':'Felhúzom','le':'Leengedem'}.get(irany, 'Megállítom') }}"

intent_script = {
    "RedonySzoba": {"async_action": True,
                    "action": [{"action": COVER_ACT, "target": {"area_id": "{{ szoba }}"}}],
                    "speech": {"text": HELY + IGE + " a redőnyöket {{ hely[szoba] }}."}},
    "RedonyEgyedi": {"async_action": True,
                     "action": [{"action": COVER_ACT, "target": {"entity_id": "cover.redony_{{ egyedi }}"}}],
                     "speech": {"text": RNEV + IGE + " {{ rnev[egyedi] }} redőnyt."}},
    "RedonyMind": {"async_action": True,
                   "action": [{"choose": [
                       {"conditions": "{{ irany == 'fel' }}", "sequence": [{"action": "script.turn_on", "target": {"entity_id": "script.redonyok_mind_fel"}}]},
                       {"conditions": "{{ irany == 'le' }}", "sequence": [{"action": "script.turn_on", "target": {"entity_id": "script.redonyok_mind_le"}}]}],
                       "default": [{"action": "cover.stop_cover", "target": {"entity_id": "all"}}]}],
                   "speech": {"text": IGE + " az összes redőnyt."}},
    "KlimaKapcs": {"action": [{"action": "climate.turn_{{ 'on' if kapcs == 'be' else 'off' }}", "target": {"entity_id": "{{ klima }}"}}],
                   "speech": {"text": KNEV + "{{ 'Bekapcsoltam' if kapcs == 'be' else 'Kikapcsoltam' }} {{ knev[klima] }} klímát."}},
    "KlimaMind": {"action": [{"action": "climate.turn_{{ 'on' if kapcs == 'be' else 'off' }}",
                              "target": {"entity_id": ["climate.nappali_klima", "climate.haloszoba_klima", "climate.gyerekszoba_klima"]}}],
                  "speech": {"text": "{{ 'Bekapcsoltam' if kapcs == 'be' else 'Kikapcsoltam' }} az összes klímát."}},
    "KlimaHofok": {"action": [{"action": "climate.set_temperature", "target": {"entity_id": "{{ klima }}"}, "data": {"temperature": "{{ fok }}"}}],
                   "speech": {"text": KNEV + "Beállítottam {{ knev[klima] }} klímát {{ fok }} fokra."}},
    "KlimaMod": {"action": [{"action": "climate.set_hvac_mode", "target": {"entity_id": "{{ klima }}"}, "data": {"hvac_mode": "{{ mod }}"}}],
                 "speech": {"text": KNEV + MNEV + "Átállítottam {{ knev[klima] }} klímát {{ mnev[mod] }}."}},
    "FutesHofok": {"action": [{"action": "climate.set_temperature", "target": {"entity_id": "climate.termosztat"}, "data": {"temperature": "{{ fok }}"}}],
                   "speech": {"text": "A fűtést {{ fok }} fokra állítottam."}},
    "FutesKapcs": {"action": [{"action": "climate.set_hvac_mode", "target": {"entity_id": "climate.termosztat"},
                               "data": {"hvac_mode": "{{ {'be':'heat','ki':'off'}.get(kapcs, 'auto') }}"}}],
                   "speech": {"text": "{{ {'be':'Bekapcsoltam a fűtést.','ki':'Kikapcsoltam a fűtést.'}.get(kapcs, 'A fűtést automatára állítottam.') }}"}},
    "PorszivoSzoba": {"async_action": True,
                      "action": [{"action": "script.turn_on", "target": {"entity_id": "script.porszivo_{{ psz }}"}}],
                      "speech": {"text": PNEV + "Rendben, elindítottam a takarítást {{ pnev[psz] }}."}},
    "PorszivoNappali": {"speech": {"text": "A nappaliba sajnos nem tudok lemenni a lépcső miatt. Takarítsak másik szobában?"}},
    "PorszivoMind": {"async_action": True,
                     "action": [{"action": "script.turn_on", "target": {"entity_id": "script.porszivo_minden"}}],
                     "speech": {"text": "Rendben, elindítottam a takarítást az egész lakásban."}},
    "PorszivoHaza": {"async_action": True,
                     "action": [{"action": "vacuum.return_to_base", "target": {"entity_id": "vacuum.porszivo"}}],
                     "speech": {"text": "Hazaküldtem a porszívót a dokkolóba."}},
    "PorszivoStop": {"async_action": True,
                     "action": [{"action": "vacuum.stop", "target": {"entity_id": "vacuum.porszivo"}}],
                     "speech": {"text": "Leállítottam a porszívót."}},
    "RiasztoEjszakai": {"async_action": True,
                        "action": [{"action": "script.turn_on", "target": {"entity_id": "script.riaszto_ejszakai"}}],
                        "speech": {"text": "Éjszakai módba kapcsoltam a riasztót. Jó éjszakát!"}},
    "RiasztoElesites": {"async_action": True,
                        "action": [{"action": "script.turn_on", "target": {"entity_id": "script.riaszto_elesites"}}],
                        "speech": {"text": "Élesítettem a riasztót."}},
    "RiasztoKi": {"speech": {"text": "A riasztót biztonsági okból nem hatástalaníthatom. Kérlek, az Ajax appban vagy a kezelőn tedd meg."}},
    "Homerseklet": {"speech": {"text": (
        "{% if homero == 'kint' %}Kint most {{ state_attr('weather.forecast_otthon', 'temperature') | round(0) | int }} fok van."
        "{% else %}{% set h = {'sensor.nappali_homerseklet':'A nappaliban','sensor.haloszoba_homerseklet':'A hálószobában',"
        "'sensor.gyerekszoba_homerseklet':'A gyerekszobában','sensor.eloter_homerseklet':'Az előszobában'} %}"
        "{{ h[homero] }} most {{ states(homero) | round(0) | int }} fok van.{% endif %}")}},
}

# --- tanult parancsok (a Jarvis tanuló modulja írja: tools/tanult.json) ------------------
# Minden tanult mondat saját intentet kap, amely a Claude által egyszer már végrehajtott
# szolgáltatáshívásokat játssza vissza, token nélkül.
tanult_path = REPO / "tools" / "tanult.json"
tanult = json.loads(tanult_path.read_text(encoding="utf-8")) if tanult_path.exists() else []
for i, t in enumerate(tanult, 1):
    name = f"Tanult{i:03d}"
    sentences["intents"][name] = {"data": [{"sentences": [f"[<kerlek>] {t['mondat']} [<kerlek>]"]}]}
    intent_script[name] = {"async_action": True, "action": t["muveletek"], "speech": {"text": t["valasz"]}}

(REPO / "custom_sentences" / "hu").mkdir(parents=True, exist_ok=True)
hdr_s = ("# Magyar hangparancsok (tokenmentes, helyben a Pi-n). GENERÁLT FÁJL – a forrás a tools/gen_hang.py (futtatás: python tools/gen_hang.py .).\n"
         "# A HA a custom_sentences/<nyelv>/ mappából olvassa, ezért nem a packages/ alatt van.\n")
hdr_p = ("# A custom_sentences/hu/hangvezerles.yaml mondatainak végrehajtása és magyar válaszai.\n"
         "# GENERÁLT FÁJL – a forrás a tools/gen_hang.py (futtatás: python tools/gen_hang.py .). Amit ez nem ért, az a Claude-hoz megy tovább.\n")
(REPO / "custom_sentences" / "hu" / "hangvezerles.yaml").write_text(
    hdr_s + json.dumps(sentences, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
(REPO / "packages" / "hangvezerles.yaml").write_text(
    hdr_p + json.dumps({"intent_script": intent_script}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print("kész")
