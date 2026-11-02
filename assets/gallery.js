/* Static portfolio interactions. Content comes from the generated data asset. */
(() => {
  'use strict';
  const { albums, sizes, descriptions, images, settings, slides = [] } = window.PORTFOLIO;
  const script = document.currentScript || document.querySelector('script[src*="assets/gallery.js"]');
  const root = new URL('../', script.src);
  const url = path => new URL(path, root).href;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const photo = (id, small = false) => url(small ? images[id].small : images[id].src);
  const alt = id => descriptions[id] || 'Photograph by ' + settings.name;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const album = document.querySelector('#album');
  const lightbox = document.querySelector('#lightbox');
  let activeAlbum = null;
  let expanded = false;
  let lightPhotos = [];
  let lightIndex = 0;
  let lastTouch = null;

  function imageMarkup(id) {
    const [w, h] = sizes[id];
    return `<img src="${photo(id)}" srcset="${photo(id, true)} ${images[id].smallWidth}w, ${photo(id)} ${w}w" sizes="(max-width:600px) calc(100vw - 40px), 55vw" width="${w}" height="${h}" alt="${esc(alt(id))}" loading="lazy" decoding="async">`;
  }
  function item(id, handler, options = {}) {
    const button = document.createElement('button');
    const [w, h] = sizes[id];
    button.className = 'photo-item' + (options.album ? ' albumphoto' : '');
    button.style.flexGrow = w / h;
    button.style.setProperty('--ratio', `${w}/${h}`);
    button.setAttribute('aria-label', `View photograph: ${alt(id)}`);
    button.innerHTML = imageMarkup(id) + (options.caption || '');
    button.onclick = handler;
    return button;
  }
  function rows(container, ids, handler, caption, options = {}) {
    if (!container) return;
    const fragment = document.createDocumentFragment();
    for (let i = 0; i < ids.length; i += 2) {
      const pair = ids.slice(i, i + 2);
      const row = document.createElement('div');
      row.className = 'photo-row' + (pair.length === 1 ? ' solo' : '');
      pair.forEach(id => row.append(item(id, () => handler(id), { ...options, caption: caption ? caption(id) : '' })));
      fragment.append(row);
    }
    container.replaceChildren(fragment);
  }
  function syncLock() {
    document.body.classList.toggle('modal-open', !!(album?.open || lightbox?.open));
  }
  function renderAlbum() {
    const a = albums[activeAlbum];
    const ids = expanded ? a.all : a.featured;
    const toggle = document.querySelector('#albumToggle');
    document.querySelector('#albumCount').textContent = expanded ? `${a.all.length} photographs` : `${a.featured.length} highlights / ${a.all.length} photographs`;
    toggle.textContent = expanded ? 'Show highlights ↑' : 'View full collection ↓';
    toggle.setAttribute('aria-expanded', String(expanded));
    toggle.hidden = a.all.length <= a.featured.length;
    rows(document.querySelector('#albumgrid'), ids, id => openLight(a.all, id, a.title), null, { album: true });
  }
  function showAlbum(key) {
    const a = albums[key];
    if (!a || !album) return;
    if (activeAlbum !== key || !album.open) {
      activeAlbum = key;
      expanded = false;
      document.querySelector('#albumTitle').textContent = a.title;
      document.querySelector('#albumLabel').textContent = a.type;
      document.querySelector('#albumDescription').textContent = a.description;
      const foot = document.querySelector('#albumfoot');
      const contact = document.createElement('a');
      contact.href = url('#contact');
      contact.textContent = a.kind === 'event' ? 'Inquire about your occasion' : 'Get in touch';
      const browse = document.createElement('a');
      browse.href = url(a.kind === 'event' ? 'work/?category=nature' : 'work/');
      browse.textContent = a.kind === 'event' ? 'Explore landscape & wildlife' : 'Browse all photographs';
      foot.replaceChildren(contact, browse);
      renderAlbum();
      album.scrollTop = 0;
    }
    if (!album.open) album.showModal();
  }
  function renderLight() {
    const id = lightPhotos[lightIndex];
    if (!id || !images[id]) return;
    const image = document.querySelector('#lightImage');
    image.src = photo(id);
    image.alt = alt(id);
    document.querySelector('#lightCount').textContent = `${String(lightIndex + 1).padStart(2, '0')} / ${String(lightPhotos.length).padStart(2, '0')}`;
    const caption = document.querySelector('#lightCaption');
    caption.replaceChildren();
    if (images[id].caption) caption.append(document.createTextNode(images[id].caption));
    if (images[id].story) {
      const link = document.createElement('a');
      link.href = url(images[id].story);
      link.textContent = 'Read the story';
      caption.append(link);
    }
    if (lightPhotos.length > 1) {
      const next = new Image();
      next.src = photo(lightPhotos[(lightIndex + 1) % lightPhotos.length]);
    }
  }
  function applyRoute() {
    if (!album || !lightbox) return;
    const params = new URLSearchParams(location.hash.slice(1));
    const collection = params.get('collection');
    const id = params.get('photo');
    if (collection && albums[collection]) showAlbum(collection);
    else if (album.open) album.close();
    if (id && images[id]) {
      const state = history.state || {};
      lightPhotos = (state.photoIds || (albums[collection] || albums.All).all).filter(key => images[key]);
      if (!lightPhotos.includes(id)) lightPhotos = [id, ...lightPhotos];
      lightIndex = lightPhotos.indexOf(id);
      document.querySelector('#lightTitle').textContent = state.photoTitle || albums[collection]?.title || 'All photographs';
      renderLight();
      if (!lightbox.open) lightbox.showModal();
    } else if (lightbox.open) lightbox.close();
    syncLock();
  }
  function navigate(params, extra = {}) {
    history.pushState({ portfolio: true, ...extra }, '', '#' + params.toString());
    applyRoute();
  }
  function openAlbum(key) {
    if (albums[key]) navigate(new URLSearchParams({ collection: key }));
  }
  function openLight(ids, id, title) {
    const params = new URLSearchParams();
    if (album?.open && activeAlbum) params.set('collection', activeAlbum);
    params.set('photo', id);
    navigate(params, { photoIds: ids, photoTitle: title });
  }
  function closeLayer() {
    if (history.state?.portfolio) history.back();
    else {
      const params = new URLSearchParams(location.hash.slice(1));
      if (lightbox?.open) params.delete('photo');
      else params.delete('collection');
      history.replaceState(null, '', location.pathname + location.search + (params.size ? '#' + params.toString() : ''));
      applyRoute();
    }
  }
  function step(amount) {
    if (!lightPhotos.length) return;
    lightIndex = (lightIndex + amount + lightPhotos.length) % lightPhotos.length;
    const params = new URLSearchParams(location.hash.slice(1));
    params.set('photo', lightPhotos[lightIndex]);
    history.replaceState(history.state, '', '#' + params.toString());
    renderLight();
  }
  document.querySelectorAll('[data-open-album]').forEach(button => button.onclick = () => openAlbum(button.dataset.openAlbum));
  document.querySelector('#albumToggle')?.addEventListener('click', () => { expanded = !expanded; renderAlbum(); });
  document.querySelector('#previous')?.addEventListener('click', () => step(-1));
  document.querySelector('#next')?.addEventListener('click', () => step(1));
  lightbox?.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      step(event.key === 'ArrowLeft' ? -1 : 1);
    }
  });
  const stage = document.querySelector('.lightstage');
  stage?.addEventListener('touchstart', event => { lastTouch = { x: event.changedTouches[0].clientX, y: event.changedTouches[0].clientY }; }, { passive: true });
  stage?.addEventListener('touchend', event => {
    if (!lastTouch) return;
    const dx = event.changedTouches[0].clientX - lastTouch.x;
    const dy = event.changedTouches[0].clientY - lastTouch.y;
    if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy) * 1.5) step(dx < 0 ? 1 : -1);
    lastTouch = null;
  }, { passive: true });
  document.querySelectorAll('dialog').forEach(dialog => {
    dialog.querySelector('.close').onclick = closeLayer;
    dialog.addEventListener('cancel', event => { event.preventDefault(); closeLayer(); });
    dialog.addEventListener('close', syncLock);
    dialog.addEventListener('click', event => {
      if (event.target !== dialog) return;
      const bounds = dialog.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) closeLayer();
    });
  });
  window.addEventListener('popstate', applyRoute);
  window.addEventListener('hashchange', applyRoute);
  applyRoute();

  /* Homepage collection filters. */
  const natureGrid = document.querySelector('#naturegrid');
  let activeNature = 'Selected';
  function renderNature() {
    const a = albums[activeNature];
    if (!natureGrid || !a) return;
    rows(natureGrid, a.featured, id => openLight(a.all, id, a.title), id => activeNature === 'Selected' ? `<div class="image-caption"><b>${esc(images[id].category)}</b></div>` : (images[id].caption ? `<div class="image-caption">${esc(images[id].caption)}</div>` : ''));
  }
  document.querySelectorAll('[data-category]').forEach(button => button.onclick = () => {
    activeNature = button.dataset.category;
    document.querySelectorAll('[data-category]').forEach(other => {
      other.classList.toggle('active', other === button);
      other.setAttribute('aria-pressed', String(other === button));
    });
    renderNature();
  });
  renderNature();

  /* Every published photograph, with people/events first and category filters. */
  const allPhotos = document.querySelector('#allPhotos');
  if (allPhotos) {
    let filter = new URLSearchParams(location.search).get('category') || 'All';
    const supported = [...document.querySelectorAll('[data-work-filter]')].map(button => button.dataset.workFilter);
    if (!supported.includes(filter) && filter !== 'nature') filter = 'All';
    function renderWork() {
      const ids = albums.All.all.filter(id => {
        const category = images[id].category;
        const matchesCategory = filter === 'All' || (filter === 'nature' ? category !== 'People & events' : category === filter);
        return matchesCategory;
      });
      document.querySelectorAll('[data-work-filter]').forEach(button => {
        const active = button.dataset.workFilter === filter;
        button.classList.toggle('active', active);
        button.setAttribute('aria-pressed', String(active));
      });
      document.querySelector('#workCount').textContent = `${ids.length} photograph${ids.length === 1 ? '' : 's'}${filter === 'All' ? '' : ' · ' + (filter === 'nature' ? 'Nature' : filter)}`;
      document.querySelector('#noResults').hidden = ids.length > 0;
      rows(allPhotos, ids, id => openLight(ids, id, filter === 'All' ? 'All photographs' : filter));
    }
    document.querySelectorAll('[data-work-filter]').forEach(button => button.onclick = () => {
      filter = button.dataset.workFilter;
      const current = new URL(location.href);
      if (filter === 'All') current.searchParams.delete('category');
      else current.searchParams.set('category', filter);
      history.replaceState(null, '', current.pathname + current.search);
      renderWork();
    });
    document.querySelector('#resetFilters').onclick = () => {
      filter = 'All';
      history.replaceState(null, '', location.pathname);
      renderWork();
    };
    renderWork();
  }

  /* A quiet, automatically advancing photographic strip. Interaction stops motion. */
  const rail = document.querySelector('#showcaseRail');
  if (rail && slides.length) {
    const frames = [...rail.querySelectorAll('.showcase-frame')];
    let index = 0;
    let playing = !reducedMotion.matches;
    let hovering = false;
    let onScreen = true;
    let timer;
    let resetTimer;
    let scrolling = false;
    const progress = document.querySelector('#showcaseProgress');
    progress.innerHTML = slides.map((_,i) => `<span class="${i===0?'active':''}"></span>`).join('');
    function describe(next) {
      index = ((next % slides.length) + slides.length) % slides.length;
      const slide = slides[index];
      document.querySelector('#showcaseKind').textContent = slide.kind === 'event' ? 'People & events' : 'The natural world';
      document.querySelector('#showcaseCollection').textContent = slide.title;
      document.querySelector('#showcaseCount').textContent = String(index + 1).padStart(2,'0') + ' / ' + String(slides.length).padStart(2,'0');
      [...progress.children].forEach((span,i) => span.classList.toggle('active',i===index));
    }
    function target(frame) {
      return Math.max(0, frame.offsetLeft - (rail.clientWidth - frame.clientWidth) / 2);
    }
    function schedule() {
      clearTimeout(timer);
      if (playing && !hovering && onScreen && !document.hidden && !album?.open && !lightbox?.open) timer = setTimeout(advance,5200);
    }
    function show(next, automatic=false) {
      clearTimeout(resetTimer);
      const rendered = automatic && next === slides.length ? slides.length : ((next % slides.length) + slides.length) % slides.length;
      const frame = frames[rendered];
      if (!frame) return;
      scrolling = true;
      const left = rendered >= slides.length ? Math.max(0,frame.offsetLeft-parseFloat(getComputedStyle(rail).paddingLeft)) : target(frame);
      rail.scrollTo({left,behavior:reducedMotion.matches?'instant':'smooth'});
      describe(rendered);
      resetTimer = setTimeout(() => {
        if (rendered >= slides.length) rail.scrollTo({left:target(frames[0]),behavior:'instant'});
        scrolling = false;
        schedule();
      },reducedMotion.matches?0:850);
    }
    function advance() { show(index + 1,true); }
    function stop() { playing = false; clearTimeout(timer); }
    frames.forEach(frame => frame.onclick = () => { stop(); openAlbum(frame.dataset.collection); });
    document.querySelector('#showcaseCollection').onclick = () => { stop(); openAlbum(slides[index].collection); };
    rail.addEventListener('pointerdown',stop,{passive:true});
    rail.addEventListener('touchstart',stop,{passive:true});
    rail.addEventListener('wheel',stop,{passive:true});
    rail.addEventListener('focusin',stop);
    rail.addEventListener('pointerenter',() => { hovering=true;clearTimeout(timer); });
    rail.addEventListener('pointerleave',() => { hovering=false;schedule(); });
    rail.addEventListener('keydown',event => {
      if (event.key==='ArrowLeft'||event.key==='ArrowRight') {
        event.preventDefault();stop();show(index+(event.key==='ArrowLeft'?-1:1));
      }
      if (event.key==='Escape') stop();
    });
    let scrollTimer;
    rail.addEventListener('scroll',() => {
      clearTimeout(scrollTimer);
      if (scrolling) return;
      scrollTimer=setTimeout(() => {
        const middle=rail.scrollLeft+rail.clientWidth/2;
        let closest=0,distance=Infinity;
        frames.forEach((frame,i) => {
          const delta=Math.abs(frame.offsetLeft+frame.clientWidth/2-middle);
          if(delta<distance){closest=i;distance=delta;}
        });
        describe(closest);
      },100);
    },{passive:true});
    if('IntersectionObserver' in window) {
      const observer=new IntersectionObserver(entries=>{onScreen=entries[0].isIntersecting;schedule();});
      observer.observe(rail);
    }
    document.addEventListener('visibilitychange',schedule);
    reducedMotion.addEventListener('change',()=>{if(reducedMotion.matches)stop();});
    describe(0);schedule();
  }
  if (!reducedMotion.matches && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target); }
    }), { threshold: .08 });
    document.querySelectorAll('.reveal-section').forEach(section => observer.observe(section));
  }
  const year = document.querySelector('#year');
  if (year) year.textContent = new Date().getFullYear();
})();
