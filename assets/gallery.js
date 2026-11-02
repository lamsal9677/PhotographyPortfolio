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
      contact.href = 'mailto:' + settings.email + '?subject=Photography%20inquiry';
      contact.textContent = a.kind === 'event' ? 'Inquire about your occasion ↗' : 'Get in touch ↗';
      const browse = document.createElement('a');
      browse.href = url(a.kind === 'event' ? 'work/?category=nature' : 'work/');
      browse.textContent = a.kind === 'event' ? 'Explore landscape & wildlife ↗' : 'Browse all photographs ↗';
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
      link.textContent = 'Read the story ↗';
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
    rows(natureGrid, a.featured, id => openLight(a.all, id, a.title), id => `<div class="image-caption"><b>${esc(activeNature === 'Selected' ? images[id].category : settings.name)}</b><span>View photograph ↗</span></div>`);
    document.querySelector('#natureNote').textContent = activeNature === 'Selected' ? 'A few selected frames' : `${a.all.length} photographs`;
    document.querySelector('#natureAlbum').textContent = activeNature === 'Selected' ? 'Explore the nature collection ↗' : `Explore ${activeNature.toLowerCase()} ↗`;
  }
  document.querySelectorAll('[data-category]').forEach(button => button.onclick = () => {
    activeNature = button.dataset.category;
    document.querySelectorAll('[data-category]').forEach(other => {
      other.classList.toggle('active', other === button);
      other.setAttribute('aria-pressed', String(other === button));
    });
    renderNature();
  });
  document.querySelector('#natureAlbum')?.addEventListener('click', () => openAlbum(activeNature));
  renderNature();

  /* Every published photograph, with filters and captions searchable in one view. */
  const allPhotos = document.querySelector('#allPhotos');
  if (allPhotos) {
    let filter = new URLSearchParams(location.search).get('category') || 'All';
    const supported = [...document.querySelectorAll('[data-work-filter]')].map(button => button.dataset.workFilter);
    if (!supported.includes(filter) && filter !== 'nature') filter = 'All';
    const search = document.querySelector('#photoSearch');
    function renderWork() {
      const term = search.value.trim().toLowerCase();
      const ids = albums.All.all.filter(id => {
        const category = images[id].category;
        const matchesCategory = filter === 'All' || (filter === 'nature' ? category !== 'People & events' : category === filter);
        return matchesCategory && (!term || `${alt(id)} ${images[id].caption} ${category}`.toLowerCase().includes(term));
      });
      document.querySelectorAll('[data-work-filter]').forEach(button => {
        const active = button.dataset.workFilter === filter;
        button.classList.toggle('active', active);
        button.setAttribute('aria-pressed', String(active));
      });
      document.querySelector('#workCount').textContent = `${ids.length} photograph${ids.length === 1 ? '' : 's'}${filter === 'All' ? '' : ' · ' + (filter === 'nature' ? 'Nature' : filter)}`;
      document.querySelector('#noResults').hidden = ids.length > 0;
      rows(allPhotos, ids, id => openLight(ids, id, filter === 'All' ? 'All photographs' : filter), id => `<div class="image-caption"><b>${esc(images[id].category || 'Photograph')}</b><span>${images[id].story ? 'Story available · ' : ''}View photograph ↗</span></div>`);
    }
    document.querySelectorAll('[data-work-filter]').forEach(button => button.onclick = () => {
      filter = button.dataset.workFilter;
      const current = new URL(location.href);
      if (filter === 'All') current.searchParams.delete('category');
      else current.searchParams.set('category', filter);
      history.replaceState(null, '', current.pathname + current.search);
      renderWork();
    });
    let searchTimer;
    search.addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(renderWork, 120); });
    document.querySelector('#resetFilters').onclick = () => {
      filter = 'All'; search.value = '';
      history.replaceState(null, '', location.pathname);
      renderWork();
    };
    renderWork();
  }

  /* A controlled slideshow: pauses on interaction, hidden tabs, and reduced motion. */
  const slideOpen = document.querySelector('#slideOpen');
  if (slideOpen && slides.length) {
    let index = 0;
    let playing = !reducedMotion.matches;
    let hovering = false;
    let onScreen = true;
    let request = 0;
    let timer;
    const play = document.querySelector('#slidePlay');
    const image = slideOpen.querySelector('img');
    function schedule() {
      clearTimeout(timer);
      play.textContent = playing ? 'Pause' : 'Play';
      play.setAttribute('aria-label', playing ? 'Pause slideshow' : 'Play slideshow');
      if (playing && !hovering && onScreen && !document.hidden && !album?.open && !lightbox?.open) timer = setTimeout(() => show(index + 1), 6500);
    }
    async function show(next) {
      const token = ++request;
      const nextIndex = (next + slides.length) % slides.length;
      const slide = slides[nextIndex];
      const preload = new Image();
      preload.src = photo(slide.image);
      try { await preload.decode(); } catch { schedule(); return; }
      if (token !== request) return;
      index = nextIndex;
      const [w, h] = sizes[slide.image];
      image.removeAttribute('srcset');
      image.src = preload.src;
      image.width = w; image.height = h; image.alt = alt(slide.image);
      if (!reducedMotion.matches && image.animate) image.animate([{ opacity: .2 }, { opacity: 1 }], { duration: 500, easing: 'ease-out' });
      slideOpen.setAttribute('aria-label', `Open ${slide.title} collection`);
      document.querySelector('#slideKind').textContent = slide.kind === 'event' ? 'People & events' : 'The natural world';
      document.querySelector('#slideCollection').textContent = slide.title + ' ↗';
      document.querySelector('#slideCount').textContent = `${String(index + 1).padStart(2, '0')} / ${String(slides.length).padStart(2, '0')}`;
      if (!playing) document.querySelector('#slideAnnouncement').textContent = `${slide.title}, photograph ${index + 1} of ${slides.length}`;
      schedule();
    }
    slideOpen.onclick = () => { playing = false; schedule(); openAlbum(slides[index].collection); };
    document.querySelector('#slideCollection').onclick = slideOpen.onclick;
    document.querySelector('#slidePrev').onclick = () => { playing = false; show(index - 1); };
    document.querySelector('#slideNext').onclick = () => { playing = false; show(index + 1); };
    play.onclick = () => { playing = !playing; schedule(); };
    const carousel = document.querySelector('.slideshow');
    carousel.addEventListener('pointerenter', () => { hovering = true; schedule(); });
    carousel.addEventListener('pointerleave', () => { hovering = false; schedule(); });
    carousel.addEventListener('focusin', () => { playing = false; schedule(); });
    carousel.addEventListener('keydown', event => {
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault(); playing = false;
        show(index + (event.key === 'ArrowLeft' ? -1 : 1));
      }
    });
    if ('IntersectionObserver' in window) {
      const visibility = new IntersectionObserver(entries => { onScreen = entries[0].isIntersecting; schedule(); });
      visibility.observe(carousel);
    }
    document.addEventListener('visibilitychange', schedule);
    reducedMotion.addEventListener('change', () => { if (reducedMotion.matches) playing = false; schedule(); });
    const initial = slides[0];
    document.querySelector('#slideKind').textContent = initial.kind === 'event' ? 'People & events' : 'The natural world';
    document.querySelector('#slideCollection').textContent = initial.title + ' ↗';
    document.querySelector('#slideCount').textContent = `01 / ${String(slides.length).padStart(2, '0')}`;
    schedule();
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
