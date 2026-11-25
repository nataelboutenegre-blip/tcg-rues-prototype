-- s3-71 (25/11/2026) : les 4 couleurs de clan ajoutées par patch253 / s2-52 (rose, ciel, tilleul, orange vif)
-- étaient acceptées par clan_modifier mais refusées par la contrainte de la table (« clans_couleur_check »).
alter table public.clans drop constraint clans_couleur_check;
alter table public.clans add constraint clans_couleur_check check (couleur = any (array['#E07A2E','#4C9BE8','#C45BD6','#2BB673','#E5484D','#E8C547',
  '#1ABC9C','#8E9AAF','#F06EA9','#7DD3FC','#A3E635','#F97316']));
