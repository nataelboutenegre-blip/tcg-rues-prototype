
// ---------- patch549 : sur ordinateur, la molette fait défiler les rangées horizontales ----------
// Sans pavé tactile, une souris ne peut pas faire défiler une rangée qui glisse sur le côté (catégories du motif,
// filtres, onglets…). Ici, la molette verticale au-dessus d'une telle rangée la fait défiler ; arrivée au bout, la page reprend.
(function(){
  if(!window.matchMedia || !matchMedia('(hover: hover) and (pointer: fine)').matches) return;
  const peut = (v) => v === 'auto' || v === 'scroll';
  document.addEventListener('wheel', (e) => {
    if(e.ctrlKey || !e.deltaY || Math.abs(e.deltaX) >= Math.abs(e.deltaY)) return;
    for(let el = e.target; el && el.nodeType === 1 && el !== document.body; el = el.parentElement){
      if(el.id === 'mapWrap' || el.tagName === 'CANVAS') return;
      if(el.scrollWidth <= el.clientWidth + 2) continue;
      const s = getComputedStyle(el);
      if(!peut(s.overflowX)) continue;
      if(peut(s.overflowY) && el.scrollHeight > el.clientHeight + 2) return;
      const d = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaMode === 2 ? e.deltaY * el.clientWidth : e.deltaY;
      const max = el.scrollWidth - el.clientWidth;
      if((d > 0 && el.scrollLeft >= max - 1) || (d < 0 && el.scrollLeft <= 0)) return;
      el.scrollLeft = Math.max(0, Math.min(max, el.scrollLeft + d));
      e.preventDefault();
      return;
    }
  }, { passive: false });
})();
