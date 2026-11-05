// TerraFront · les compteurs du haut qui défilent comme un vieux compteur mécanique (scène portrait).
// direct.js écrit toujours ses chiffres dans #cConquetes, #cLibres et #cEnLigne (cachés) ;
// ici on recopie chaque nouvelle valeur dans des rouleaux de 0 à 9 qui tournent jusqu'au bon chiffre.
'use strict';
(function(){
  const IDS = ['cConquetes', 'cLibres', 'cEnLigne'];
  const CHIFFRES = '0123456789';
  for(const id of IDS){
    const src = document.getElementById(id);
    if(!src) continue;
    const odo = document.createElement('b');
    odo.className = 'odo'; odo.setAttribute('aria-hidden', 'true');
    src.after(odo); src.classList.add('odo-source');
    let avant = '';
    const maj = () => {
      const txt = (src.textContent || '').trim();
      if(txt === avant) return;
      const chiffresSeuls = /^[\d\s  ]+$/.test(txt);
      if(!chiffresSeuls){ odo.textContent = txt; avant = txt; return; }   // « — » au chargement
      const neuf = !/^[\d\s  ]+$/.test(avant) || avant.replace(/\D/g, '').length !== txt.replace(/\D/g, '').length;
      if(neuf){
        // nombre de chiffres différent (ou premier affichage) : on reconstruit, tout part de 0
        odo.innerHTML = [...txt].map((c) => /\d/.test(c)
          ? '<span class="rou"><span class="ban">' + CHIFFRES.split('').map((d) => '<i>' + d + '</i>').join('') + '</span></span>'
          : '<span class="sep">' + (c === ' ' ? ' ' : c) + '</span>').join('');
        void odo.offsetWidth;   // pour que la transition parte bien de 0
      }
      const rouleaux = odo.querySelectorAll('.ban'), digits = txt.replace(/\D/g, '');
      rouleaux.forEach((ban, i) => {
        const d = Number(digits[i]);
        // les rouleaux de droite tournent un peu après ceux de gauche, comme une mécanique
        ban.style.transitionDelay = ((rouleaux.length - 1 - i) * 70) + 'ms';
        ban.style.transform = 'translateY(' + (-d * 10) + '%)';
      });
      avant = txt;
    };
    new MutationObserver(maj).observe(src, { childList: true, characterData: true, subtree: true });
    maj();
  }
})();
