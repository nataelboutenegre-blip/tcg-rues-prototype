# -*- coding: utf-8 -*-
u"""
patch84 — Message en français quand Supabase refuse un mot de passe déjà
paru dans une fuite (« Prevent use of leaked passwords », activé le
8 octobre). Avant : le message anglais de Supabase s'affichait tel quel.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
p = os.path.join(BASE, 'app.js')
s = io.open(p, encoding='utf-8').read()
avant = u"""    [/password should be at least (\\d+)/i, (x) => `Le mot de passe doit faire au moins ${x[1]} caractères.`],"""
apres = avant + u"""
    [/known to be weak|easy to guess|pwned|leaked/i, 'Ce mot de passe est apparu dans une fuite de données connue : choisis-en un autre.'],"""
assert s.count(avant) == 1, 'messageLisible introuvable'
s = s.replace(avant, apres)
io.open(p, 'w', encoding='utf-8').write(s)
print(u'patch84 : OK')
