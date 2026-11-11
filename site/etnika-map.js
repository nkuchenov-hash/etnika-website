/* ETNIKA · contacts map · 2026-11-06
   Yandex Maps API 3: georeferenced marks for the studio and metro.
   The built-in Yandex map widget remains the error fallback.
   All station and studio marks must move with the map on pan/zoom. */
(function () {
  'use strict';
  const root = document.getElementById('etnika-contacts-map-live');
  if (!root || root.dataset.initialized === '1') return;
  root.dataset.initialized = '1';

  const shell = root.closest('.location-map');
  const section = document.getElementById('etnika-contacts-source');
  const fallbackFrame = shell && shell.querySelector('.etnika-map-widget-fallback');
  if (!shell || !section) return;

  // This is a public, HTTP-Referer-restricted browser API key.
  const API_KEY = '0c3d5b94-7c1d-4e23-b323-f4a620b3dcb1';
  // Coordinates are [longitude, latitude]. Avtozavodskaya Zamoskvoretskaya
  // line: vmetro.moscow/station/avtozavodskaya/.
  const METRO = [37.660467, 55.706854];
  // Business center Omega-2, Leninskaya Sloboda 26/26A:
  // Yandex building location yandex.com/maps/213/moscow/house/ulitsa_leninskaya_sloboda_26/.
  // The marker denotes the building, not an individual office entrance.
  const STUDIO = [37.654610, 55.710130];
  const MAP_CENTER = [37.6573, 55.70865];
  const MAPS_URL = 'https://yandex.ru/maps/?text=' +
    encodeURIComponent('Москва, улица Ленинская Слобода, 26А, БЦ Омега-2');
  let started = false;

  // The embedded map is always usable as a backup when the v3 API, its key,
  // WebGL or any optional module fails to initialize.
  function useFallback(error) {
    if (shell.dataset.mapState === 'ready') return;
    shell.dataset.mapState = 'fallback';
    root.setAttribute('aria-hidden', 'true');
    if (fallbackFrame && fallbackFrame.dataset.mapSrc &&
        !fallbackFrame.getAttribute('src')) {
      fallbackFrame.src = fallbackFrame.dataset.mapSrc;
    }
    if (error && window.console && console.warn) {
      console.warn('ETNIKA map: switched to embedded Yandex map', error);
    }
  }

  // Load the reliable embedded map before attempting the enhanced v3 layer.
  // This also keeps the map functional if the v3 CDN never answers.
  root.setAttribute('aria-hidden', 'true');
  if (fallbackFrame && fallbackFrame.dataset.mapSrc &&
      !fallbackFrame.getAttribute('src')) {
    fallbackFrame.src = fallbackFrame.dataset.mapSrc;
  }

  function createMetroMark() {
    const mark = document.createElement('div');
    mark.className = 'etnika-map-station';
    mark.setAttribute('role', 'img');
    mark.setAttribute('aria-label', 'Метро Автозаводская, Замоскворецкая линия');

    /* One local vector: no remote Wikimedia dependency or broken black square.
       High-contrast red Moscow metro M and compact clear station label. */
    const logo=document.createElementNS('http://www.w3.org/2000/svg','svg');
    logo.setAttribute('class','etnika-map-station__logo');
    logo.setAttribute('viewBox','0 0 72 55');
    logo.setAttribute('aria-hidden','true');
    const path=document.createElementNS('http://www.w3.org/2000/svg','path');
    path.setAttribute('fill','#da182a');
    path.setAttribute('d','M4 49 18 5 36 33 54 5 68 49H55L49 27 36 51 23 27 17 49Z');
    logo.appendChild(path);

    const label=document.createElement('span');
    label.className='etnika-map-station__label';
    label.textContent='Автозаводская';
    mark.append(logo,label);
    return mark;
  }

  function createStudioMark() {
    const mark = document.createElement('div');
    mark.className = 'etnika-map-studio';

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'etnika-map-studio__button';
    button.setAttribute('aria-expanded', 'false');
    button.setAttribute('aria-label', 'ЭТНИКА — студия автопортрета, показать адрес');

    const pin = document.createElement('span');
    pin.className = 'etnika-map-studio__pin';
    pin.setAttribute('aria-hidden', 'true');
    pin.innerHTML = '<svg viewBox="0 0 32 42" width="32" height="42" aria-hidden="true">' +
      '<path d="M16 1C7.7 1 1 7.7 1 16c0 10 15 25 15 25s15-15 15-25C31 7.7 24.3 1 16 1Z" fill="#B31727" stroke="#fff" stroke-width="1.5"/>' +
      '<circle cx="16" cy="16" r="6" fill="#fff"/></svg>';
    const studioName = document.createElement('span');
    studioName.className = 'etnika-map-studio__name';
    studioName.textContent = 'ЭТНИКА';
    button.append(pin, studioName);

    const popup = document.createElement('div');
    popup.className = 'etnika-map-studio__popup';
    popup.hidden = true;
    const title = document.createElement('strong');
    title.textContent = 'ЭТНИКА · студия автопортрета';
    const address = document.createElement('span');
    address.textContent = 'Ленинская Слобода, 26А · БЦ «Омега-2», офис 416';
    const link = document.createElement('a');
    link.href = MAPS_URL;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = 'Открыть в Яндекс Картах ↗';
    popup.append(title, address, link);

    button.addEventListener('click', function () {
      const isOpen = popup.hidden;
      popup.hidden = !isOpen;
      button.setAttribute('aria-expanded', String(isOpen));
    });

    mark.append(popup, button);
    return mark;
  }

  async function init() {
    if (!window.ymaps3) throw new Error('Yandex Maps v3 did not load');
    await window.ymaps3.ready;
    const api = window.ymaps3;
    const map = new api.YMap(root, {
      location: {center: MAP_CENTER, zoom: 15.6},
      mode: 'vector',
      showScaleInCopyrights: true
    });
    // Desaturate the native base map, including default POI and transit icons.
    // Branded markers are DOM elements above the map, so they remain red/white.
    const monochrome = [
      {elements: 'geometry', stylers: [{saturation: -1}]},
      {elements: 'label.icon', stylers: [{saturation: -1}]},
      {elements: 'label.text', stylers: [{saturation: -1}]}
    ];
    map.addChild(new api.YMapDefaultSchemeLayer({
      theme: 'dark',
      customization: monochrome
    }));
    map.addChild(new api.YMapDefaultFeaturesLayer({zIndex: 1800}));
    // Both marks are anchored to geographic points and move with the map.
    map.addChild(new api.YMapMarker(
      {coordinates: STUDIO, draggable: false}, createStudioMark()
    ));
    map.addChild(new api.YMapMarker(
      {coordinates: METRO, draggable: false}, createMetroMark()
    ));
    shell.dataset.mapState = 'ready';
    root.setAttribute('aria-hidden', 'false');

    try {
      const ui = await api.import('@yandex/ymaps3-default-ui-theme');
      if (ui && ui.YMapZoomControl && api.YMapControls) {
        map.addChild(new api.YMapControls({position: 'right'})
          .addChild(new ui.YMapZoomControl({})));
      }
    } catch (e) {
      // Native scroll and touch zoom still work.
    }
  }

  function load() {
    if (started) return;
    started = true;
    shell.dataset.mapState = 'loading';
    const loader = document.createElement('script');
    loader.src = 'https://api-maps.yandex.ru/v3/?apikey=' +
      encodeURIComponent(API_KEY) + '&lang=ru_RU';
    loader.async = true;
    loader.onload = function () {init().catch(useFallback);};
    loader.onerror = function () {
      useFallback(new Error('Yandex Maps script failed to load'));
    };
    document.head.appendChild(loader);
    // Some privacy/ad blockers silently stall the script without onerror.
    window.setTimeout(function () {
      if (shell.dataset.mapState !== 'ready') {
        useFallback(new Error('Yandex Maps v3 timed out'));
      }
    }, 10000);
  }

  /* Warm the browser API before the visitor reaches this last section.
     A longer intersection threshold still handles fast-scrolling visitors. */
  if ('IntersectionObserver' in window) {
    const observer=new IntersectionObserver(function(entries){
      if(entries.some(function(entry){return entry.isIntersecting;})){
        observer.disconnect();load();
      }
    },{rootMargin:'2500px 0px'});
    observer.observe(section);
  }
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(load,{timeout:1800});
  } else {
    window.addEventListener('load',load,{once:true});
  }
})();
