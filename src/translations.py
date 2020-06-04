import gettext
import logging
from pathlib import Path

import config

conf = config.get_section("data")
DEFAULT_LANGUAGE = conf.get("Language")
DOMAIN = "textflight"
LOCALEDIR = conf.get("LocaleDir")
if LOCALEDIR == "":
	LOCALEDIR = None

languages = {}

languages["en"] = gettext.NullTranslations()
gettext.bindtextdomain(DOMAIN, localedir=LOCALEDIR)
for path in gettext.find(DOMAIN, localedir=LOCALEDIR, all=True):
	lang = Path(path).parent.parent.name
	languages[lang] = gettext.translation(DOMAIN, languages=[lang], localedir=LOCALEDIR)
	logging.info("Loaded translation '%s'", lang)

def get_default():
	return languages[DEFAULT_LANGUAGE]

