/* The style showcase's script (docs/site/styles/, see showcase.css for the idea). One clock for every sample: t is the
   wall clock modulo 5 s, so a card, the strip and a style's player all start where the others are, on this page and the
   next. Samples load only when they are about to play (preload="none"); with prefers-reduced-motion or Save-Data nothing
   plays on its own. The page-to-page cuts are View Transitions, set up by the small script in each page's <head>. */
(() => {
  'use strict';
  const d = document, html = d.documentElement;
  const $ = (s, r = d) => r.querySelector(s), $$ = (s, r = d) => Array.from(r.querySelectorAll(s));
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = matchMedia('(hover: hover) and (pointer: fine)').matches;
  const saveData = !!(navigator.connection && navigator.connection.saveData);
  const live = !reduced && !saveData;                       // pictures that start moving on their own
  const LOOP = 5;
  const epoch = () => (performance.timeOrigin + performance.now()) / 1000;
  const clock = () => epoch() % LOOP;
  const isStyle = d.body.classList.contains('style');
  const ROOT = isStyle ? '../../../../' : '../../../';      // the repo, where the samples are
  const swatch = slug => `${ROOT}styles/${slug}/media/swatch.mp4`;
  const media = (slug, i) => `${isStyle ? '../' : ''}media/${slug}/${i}.jpg`;
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  let lang = html.getAttribute('data-lang') || 'en';

  /* ---------- language ---------- */
  function setLang(l) {
    lang = l; html.setAttribute('data-lang', l); html.lang = l === 'zh' ? 'zh-CN' : 'en';
    d.title = html.getAttribute('data-title-' + l) || d.title;
    const k = l === 'zh' ? 'Zh' : 'En';
    $$('[data-aria-en]').forEach(e => e.setAttribute('aria-label', e.dataset['aria' + k]));
    $$('[data-ph-en]').forEach(e => { e.placeholder = e.dataset['ph' + k]; });
    try { localStorage.setItem('ovh-lang', l); } catch (e) { /* private mode */ }
    if (found) found();
  }
  let found = null;
  $('#langbtn').addEventListener('click', () => setLang(lang === 'zh' ? 'en' : 'zh'));

  /* ---------- the room's colour follows the style in front of you ---------- */
  const tint = (a1, a2) => { d.body.style.setProperty('--a1', a1); d.body.style.setProperty('--a2', a2); };

  /* ---------- a sample that starts where the clock is ---------- */
  function video() {
    const v = d.createElement('video');
    v.muted = true; v.loop = true; v.playsInline = true; v.preload = 'none';
    v.setAttribute('muted', ''); v.setAttribute('playsinline', '');
    return v;
  }
  function startAt(v, src, shown) {   // shown() runs once a frame from the clock's time is on screen
    if (src && v.getAttribute('src') !== src) v.src = src;
    const go = () => {
      const dur = isFinite(v.duration) && v.duration > 0 ? v.duration : LOOP;
      try { v.currentTime = Math.min(dur - 0.04, clock() + 0.05); } catch (e) { /* not seekable yet */ }
      const p = v.play();
      const done = () => shown && shown();
      (p && p.then ? p : Promise.resolve()).then(() => {
        if ('requestVideoFrameCallback' in v) v.requestVideoFrameCallback(done); else setTimeout(done, 80);
      }).catch(() => {});
    };
    if (v.readyState >= 1) go(); else v.addEventListener('loadedmetadata', go, { once: true });
  }

  /* ---------- cards: hover plays from the clock's time; a thin line under the picture is that time ---------- */
  const cards = $$('.card');
  let active = null;
  function enter(c) {
    if (active && active !== c) leave(active);
    active = c;
    tint(c.style.getPropertyValue('--a1'), c.style.getPropertyValue('--a2'));
    if (!live || !fine) return;
    clearTimeout(c._t);
    c._t = setTimeout(() => {   // a short wait: skimming across the grid does not load every sample
      let v = $('video', c);
      if (!v) { v = video(); $('.pic', c).insertBefore(v, $('.tick', c)); }
      startAt(v, swatch(c.dataset.slug), () => { if (active === c) c.classList.add('on'); });
    }, 110);
  }
  function leave(c) {
    clearTimeout(c._t); c.classList.remove('on');
    const v = $('video', c); if (v) v.pause();
    if (active === c) active = null;
  }
  cards.forEach(c => {
    c.addEventListener('pointerenter', e => { if (e.pointerType === 'mouse') enter(c); });
    c.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse') leave(c); });
    c.addEventListener('focus', () => enter(c));
    c.addEventListener('blur', () => leave(c));
  });

  /* ---------- things arrive once: blocks fade up, cards open like a shutter, row by row ---------- */
  if (html.classList.contains('motion') && 'IntersectionObserver' in window) {
    cards.forEach(c => c.classList.add('pending'));
    const io = new IntersectionObserver(entries => {
      const hits = entries.filter(e => e.isIntersecting).map(e => e.target)
        .sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top || a.getBoundingClientRect().left - b.getBoundingClientRect().left);
      hits.forEach((el, i) => {
        io.unobserve(el);
        const delay = Math.min(i, 8) * 70;
        if (el.classList.contains('card')) {
          $('.pic', el).style.transitionDelay = `0s, 0s, ${delay}ms`;
          ['.cap', '.for', '.chips'].forEach(s => { const x = $(s, el); if (x) x.style.transitionDelay = `${delay + 160}ms`; });
          el.classList.remove('pending');
          setTimeout(() => { $('.pic', el).style.transitionDelay = ''; }, delay + 1000);
        } else el.classList.add('in');
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    cards.forEach(c => io.observe(c));
    $$('[data-r]').forEach(e => io.observe(e));
  } else $$('[data-r]').forEach(e => e.classList.add('in'));

  /* ---------- one loop for every moving readout ---------- */
  const ticks = [];
  (function frame() {
    ticks.forEach(f => f());
    if (active && active.classList.contains('on')) {
      const v = $('video', active);
      if (v && v.duration) $('.tick', active).style.setProperty('--p', (v.currentTime / v.duration).toFixed(4));
    }
    requestAnimationFrame(frame);
  })();
  addEventListener('pagehide', () => { if (active) leave(active); $$('video').forEach(v => v.pause()); });

  /* ================================================================ the overview ================================= */
  const rack = $('#rack');
  if (rack) {
    const data = JSON.parse($('#styles-data').textContent);
    const S = data.styles, G = data.groups;
    const sls = $$('.sl', rack), strip = $('.slices', rack), frame = $('.frame', rack);
    const fImg = $('img', frame), fVid = $('video', frame);
    const narrow = matchMedia('(max-width: 900px)');
    const nIdx = $('#nIdx'), nName = $('#nName'), nGroup = $('#nGroup'), tc = $('#tc'), tph = $('#tph');
    let cur = -1, dwell = 0, hovering = false, autoSteps = 0, inView = true, lastBeat = Math.floor(epoch() / LOOP);
    const fit = () => rack.style.setProperty('--rh', rack.clientHeight + 'px');   // the open slice is 16:9 at the strip's height
    fit(); addEventListener('resize', fit);

    function show(i, how) {
      i = (i + S.length) % S.length;
      if (i === cur) return;
      const old = sls[cur];
      if (old) { old.classList.remove('open', 'on'); const v = $('video', old); if (v) v.pause(); }
      cur = i;
      const s = S[i], el = sls[i], img = $('img', el);
      el.classList.add('open');
      if (!img.dataset.big) {   // the strip's small thumbnail, swapped for the sharper still once it is open
        img.dataset.big = '1';
        const big = new Image(); big.src = media(s.s, 3);
        (big.decode ? big.decode() : Promise.resolve()).then(() => { img.src = big.src; }).catch(() => {});
      }
      nIdx.textContent = String(i + 1).padStart(2, '0');
      nName.href = s.s + '/';
      $('b', nName).innerHTML = `<span lang="en">${esc(s.en)}</span><span lang="zh">${esc(s.zh)}</span>`;
      $('small', nName).innerHTML = `<span class="gl-en" lang="zh">${esc(s.zh)}</span><span class="gl-zh" lang="en">${esc(s.en)}</span>`;
      nGroup.innerHTML = `<span lang="en">${esc(G[s.g].en)}</span><span lang="zh">${esc(G[s.g].zh)}</span>`;
      tint(s.p[0], s.p[2]);
      if (narrow.matches) { frame.classList.remove('on'); fVid.pause(); fImg.src = media(s.s, 3); }
      clearTimeout(dwell);
      if (!live || (how === 'auto' && (!fine || autoSteps > 12))) return;   // phones flip stills on their own; samples play when touched
      dwell = setTimeout(() => {
        if (cur !== i) return;
        if (narrow.matches) { startAt(fVid, swatch(s.s), () => { if (cur === i) frame.classList.add('on'); }); return; }
        let v = $('video', el);
        if (!v) { v = video(); el.appendChild(v); }
        startAt(v, swatch(s.s), () => { if (cur === i) el.classList.add('on'); });
      }, how === 'pointer' ? 200 : 30);
    }
    const at = x => { const r = strip.getBoundingClientRect(); return Math.max(0, Math.min(S.length - 1, Math.floor((x - r.left) / r.width * S.length))); };

    // a mouse over the strip: its position along the strip is the style; the open one is always under it
    rack.addEventListener('pointermove', e => {
      if (e.pointerType !== 'mouse' || narrow.matches) return;
      hovering = true; autoSteps = 0; show(at(e.clientX), 'pointer');
    });
    rack.addEventListener('pointerleave', () => { hovering = false; });
    // a finger on the spines: drag along them to flip; lifting it plays the one it stopped on
    let drag = null;
    strip.addEventListener('pointerdown', e => {
      if (e.pointerType === 'mouse' || !narrow.matches) return;
      drag = { x: e.clientX, moved: false }; strip.setPointerCapture(e.pointerId); hovering = true; show(at(e.clientX), 'pointer');
    });
    strip.addEventListener('pointermove', e => { if (drag) { if (Math.abs(e.clientX - drag.x) > 4) drag.moved = true; show(at(e.clientX), 'pointer'); } });
    const end = () => { drag = null; hovering = false; autoSteps = 0; };
    strip.addEventListener('pointerup', end); strip.addEventListener('pointercancel', end);
    sls.forEach((a, i) => a.addEventListener('click', e => {
      if (narrow.matches) { e.preventDefault(); show(i, 'pointer'); }   // on a phone a spine picks; the frame opens
    }));
    frame.addEventListener('click', () => { if (cur >= 0) location.href = S[cur].s + '/'; });
    rack.addEventListener('keydown', e => {
      const k = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: 1, ArrowUp: -1 }[e.key];
      if (k) { e.preventDefault(); autoSteps = 0; show(cur + k, 'key'); }
      else if (e.key === 'Home' || e.key === 'End') { e.preventDefault(); show(e.key === 'Home' ? 0 : S.length - 1, 'key'); }
      else if (e.key === 'Enter') location.href = S[cur].s + '/';
    });
    rack.addEventListener('focus', () => { hovering = true; });
    rack.addEventListener('blur', () => { hovering = false; });
    if ('IntersectionObserver' in window) new IntersectionObserver(es => { inView = es[0].isIntersecting; }).observe(rack);

    // what is on now: the same wall clock picks the first style, so every visit opens on a different one
    show(Math.floor(epoch() / LOOP) % S.length, 'auto');
    ticks.push(() => {
      const t = clock();
      tc.textContent = `t = ${t.toFixed(2)} s`;
      tph.style.left = `calc(${(t / LOOP * 100).toFixed(2)}% - 1px)`;
      const beat = Math.floor(epoch() / LOOP);
      if (beat !== lastBeat) {   // at the end of each loop, when nobody is choosing, the next style comes on
        lastBeat = beat;
        if (!hovering && inView && !d.hidden && !reduced && autoSteps < 40) { autoSteps++; show(cur + 1, 'auto'); }
      }
    });

    /* ---------- the group bar: where you are, and search ---------- */
    const groups = $$('.group'), links = $$('.gl a'), q = $('#q'), empty = $('#empty'), foundEl = $('#found'), gnav = $('#gnav');
    if ('IntersectionObserver' in window) {
      const seen = new Map();
      const spy = new IntersectionObserver(es => {
        es.forEach(e => seen.set(e.target.id, e.isIntersecting));
        const on = groups.find(g => seen.get(g.id) && !g.hidden);
        links.forEach(a => a.classList.toggle('on', !!on && a.dataset.g === on.id));
      }, { rootMargin: '-35% 0px -55% 0px' });
      groups.forEach(g => spy.observe(g));
    }
    const norm = s => s.toLowerCase().normalize('NFKC').trim();
    let last = '', count = cards.length;
    found = () => {
      const terms = norm(q.value);
      foundEl.textContent = terms ? (lang === 'zh' ? `找到 ${count} 种` : `${count} found`) : '';
    };
    function filter(animate) {
      const v = norm(q.value);
      if (v === last) return;
      last = v;
      const terms = v.split(/\s+/).filter(Boolean);
      const before = new Map();
      if (animate && !reduced) cards.forEach(c => { if (!c.hidden) before.set(c, c.getBoundingClientRect()); });
      count = 0;
      cards.forEach(c => { const hit = terms.every(t => c.dataset.q.includes(t)); c.hidden = !hit; if (hit) count++; });
      groups.forEach(g => {
        const k = $$('.card:not([hidden])', g).length;
        g.hidden = k === 0; $('.gc', g).textContent = k;
        const a = links.find(l => l.dataset.g === g.id); $('small', a).textContent = k; a.classList.toggle('none', k === 0);
      });
      empty.hidden = count > 0;
      found();
      const top = gnav.getBoundingClientRect().top + scrollY - parseFloat(getComputedStyle(gnav).top);
      if (terms.length && scrollY < top - 2) { scrollTo({ top, behavior: 'instant' }); before.clear(); }   // bring the results up under the bar
      if (animate && !reduced) cards.forEach(c => {
        if (c.hidden) return;
        const a = before.get(c), b = c.getBoundingClientRect();
        if (a && (a.left !== b.left || a.top !== b.top)) c.animate([{ transform: `translate(${a.left - b.left}px, ${a.top - b.top}px)` }, { transform: 'none' }], { duration: 520, easing: 'cubic-bezier(.2,.7,.1,1)' });
        else if (!a) c.animate([{ opacity: 0, transform: 'translateY(10px)' }, { opacity: 1, transform: 'none' }], { duration: 420, easing: 'cubic-bezier(.2,.7,.1,1)' });
      });
      const u = new URL(location.href);
      if (v) u.searchParams.set('q', q.value); else u.searchParams.delete('q');
      history.replaceState(null, '', u);
    }
    q.addEventListener('input', () => filter(true));
    addEventListener('keydown', e => {
      const typing = /^(input|textarea|select)$/i.test(d.activeElement.tagName);
      if (e.key === '/' && !typing) { e.preventDefault(); q.focus(); }
      else if (e.key === 'Escape' && d.activeElement === q) { q.value = ''; filter(true); q.blur(); }
    });
    const q0 = new URLSearchParams(location.search).get('q');
    if (q0) { q.value = q0; filter(false); }
  }

  /* ================================================================ a style's page ============================== */
  const v = $('#v');
  if (v) {
    const player = $('.player'), ruler = $('#ruler'), rph = $('#rph'), tc = $('#tc'), snd = $('#snd');
    const stills = $$('.still');
    const paused = p => player.classList.toggle('paused', p);
    paused(true);
    if (live) startAt(v, null, () => paused(v.paused));
    v.addEventListener('play', () => paused(false));
    v.addEventListener('pause', () => paused(true));
    const toggle = () => { if (v.paused) v.play().catch(() => {}); else v.pause(); };
    $('#pp').addEventListener('click', toggle);
    $('#big').addEventListener('click', toggle);
    v.addEventListener('click', toggle);
    snd.addEventListener('click', () => {   // sound starts the sample from the top, so its music is heard whole
      const on = v.muted;
      v.muted = !on; snd.setAttribute('aria-pressed', String(on));
      if (on) { v.currentTime = 0; v.play().catch(() => {}); }
    });
    const dur = () => (isFinite(v.duration) && v.duration > 0 ? v.duration : LOOP);
    const seek = x => { const r = ruler.getBoundingClientRect(); v.currentTime = Math.max(0, Math.min(0.999, (x - r.left) / r.width)) * dur(); };
    ruler.addEventListener('pointerdown', e => {
      ruler.setPointerCapture(e.pointerId); seek(e.clientX);
      const mv = ev => seek(ev.clientX);
      ruler.addEventListener('pointermove', mv);
      ruler.addEventListener('pointerup', () => ruler.removeEventListener('pointermove', mv), { once: true });
    });
    ruler.addEventListener('keydown', e => {
      const k = { ArrowRight: 0.2, ArrowLeft: -0.2 }[e.key];
      if (k) { e.preventDefault(); v.currentTime = Math.max(0, Math.min(dur() - 0.04, v.currentTime + k)); }
    });
    stills.forEach(b => b.addEventListener('click', () => {   // jump to that moment and hold it in the big player
      v.pause(); v.currentTime = +b.dataset.t;
      const r = player.getBoundingClientRect();
      if (r.top < 0 || r.bottom > innerHeight) player.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'center' });
    }));
    ticks.push(() => {
      const t = v.currentTime || 0, p = t / dur();
      tc.textContent = `t = ${t.toFixed(2)} s`;
      rph.style.left = `calc(${(p * 100).toFixed(2)}% - 1px)`;
      ruler.setAttribute('aria-valuenow', t.toFixed(1));
      stills.forEach(b => b.classList.toggle('here', v.paused && Math.abs(+b.dataset.t - t) < 0.06));
    });

    /* the sentence for the agent: fill in the blank, copy it whole */
    $$('.blank').forEach(inp => {
      if (CSS.supports && CSS.supports('field-sizing', 'content')) return;
      const size = () => { inp.size = Math.max(4, (inp.value || inp.placeholder).length + (/[㐀-鿿]/.test(inp.value || inp.placeholder) ? (inp.value || inp.placeholder).length : 0)); };
      size(); inp.addEventListener('input', size);
    });
    const copyBtn = $('#copy');
    copyBtn.addEventListener('click', () => {
      const p = $(`.sentence[lang="${lang}"]`);
      let text = '';
      p.childNodes.forEach(n => {
        if (n.nodeType === 3) text += n.textContent;
        else if (n.classList && n.classList.contains('blank')) text += n.value.trim() || `${n.dataset.o}${n.placeholder}${n.dataset.c}`;
        else text += n.textContent;
      });
      copy(text.trim(), () => {
        copyBtn.classList.add('done');
        const s = $(`[lang="${lang}"]`, copyBtn), was = s.textContent;
        s.textContent = lang === 'zh' ? '已复制' : 'Copied';
        setTimeout(() => { s.textContent = was; copyBtn.classList.remove('done'); }, 1600);
      });
    });
    $$('.sw').forEach(b => b.addEventListener('click', () => copy(b.dataset.hex, () => {
      b.classList.add('copied'); const c = $('code', b), was = c.textContent;
      c.textContent = lang === 'zh' ? '已复制' : 'Copied';
      setTimeout(() => { c.textContent = was; b.classList.remove('copied'); }, 1200);
    })));

    /* ← and → step through the styles; the cut is a playhead sweeping the next one in */
    addEventListener('keydown', e => {
      if (/^(input|textarea|select)$/i.test(d.activeElement.tagName) || d.activeElement === ruler || e.metaKey || e.ctrlKey || e.altKey) return;
      const a = e.key === 'ArrowRight' ? $('a[rel="next"]') : e.key === 'ArrowLeft' ? $('a[rel="prev"]') : null;
      if (a) { e.preventDefault(); mark('wipe-' + a.rel); location.href = a.href; }
    });
  }

  function copy(text, ok) {
    const fallback = () => {
      const t = d.createElement('textarea'); t.value = text; t.style.position = 'fixed'; t.style.opacity = '0';
      d.body.appendChild(t); t.select();
      try { if (d.execCommand('copy')) ok(); } catch (e) { /* the reader can select it by hand */ }
      t.remove();
    };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(ok, fallback); else fallback();
  }

  /* ---------- the cuts between pages (cross-document View Transitions; the <head> script reads these) ---------- */
  function mark(kind, pic) {
    try { sessionStorage.setItem('ovh-cut', kind); } catch (e) { /* no transition then */ }
    const hero = $('.screen');
    $$('.pic, .sl').forEach(p => { p.style.viewTransitionName = ''; });
    if (hero) hero.style.viewTransitionName = 'none';
    if (kind === 'morph' && pic) pic.style.viewTransitionName = 'hero';
  }
  d.addEventListener('click', e => {
    const a = e.target.closest && e.target.closest('a');
    if (!a || a.target === '_blank' || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.defaultPrevented) return;
    const rel = a.getAttribute('rel');
    if (rel === 'prev' || rel === 'next') mark('wipe-' + rel);
    else if (a.classList.contains('card')) mark('morph', $('.pic', a));
    else if (a.classList.contains('sl')) mark('morph', a);
    else if (a.id === 'nName' && rack) mark('morph', $('.sl.open', rack));
  });
  addEventListener('pageshow', e => {   // back from another page out of the cache: the names set for the cut are spent
    if (!e.persisted) return;
    setTimeout(() => { $$('.pic, .sl').forEach(p => { p.style.viewTransitionName = ''; }); const h = $('.screen'); if (h) h.style.viewTransitionName = ''; }, 900);
  });

  setLang(lang);
})();
