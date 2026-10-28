# patch249 : la bulle d'un département ne restait jamais cachée sur ordinateur
# (.map-infobulle.dept{display:flex} écrasait .map-infobulle[hidden]{display:none} : même poids, déclarée après)
import pathlib
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
s += "\n/* ---------- patch249 : la bulle du département se cache vraiment ---------- */\n.map-infobulle.dept[hidden]{ display:none; }\n"
f.write_text(s, encoding='utf-8'); print('patch249 ok')
