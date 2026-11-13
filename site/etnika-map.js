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
  // Actual Avtozavodskaya station on the Zamoskvoretskaya line.
  // The previous coordinate [37.660467,55.706854] was positioned toward the MCC
  // and placed our badge to the RIGHT of the native station label.
  // Station coordinate: https://en.wikipedia.org/wiki/List_of_Moscow_Metro_stations
  const METRO = [37.6576, 55.7074];
  // Moscow open-data entrance №3 via russianmetro.ru -> Yandex Maps:
  // https://yandex.ru/maps/?l=map&pt=37.657319%2C55.70865&z=18
  // Closer to Omega-2 than exit №2 [37.658257, 55.708399].
  const METRO_EXIT_3 = [37.657319, 55.708650];
  // Visual orientation only if routing service is unavailable. The route
  // service's real walking geometry replaces this dotted guide on success.
  const APPROXIMATE_WALK_GUIDE = [
    METRO_EXIT_3,
    [37.65706, 55.70896],
    [37.65668, 55.70919],
    [37.65552, 55.70972],
    [37.654610, 55.710130]
  ];
  // Business center Omega-2, Leninskaya Sloboda 26/26A:
  // Yandex building location yandex.com/maps/213/moscow/house/ulitsa_leninskaya_sloboda_26/.
  // The marker denotes the building, not an individual office entrance.
  const STUDIO = [37.654610, 55.710130];
  const MAP_CENTER = [37.65615, 55.70913];
  const MAPS_URL = 'https://yandex.ru/maps/?text=' +
    encodeURIComponent('Москва, улица Ленинская Слобода, 26А, БЦ Омега-2');
  // Official Yandex Maps walking route if the browser router API is unavailable.
  const WALK_ROUTE_URL = 'https://yandex.ru/maps/?rtext=' +
    '55.708650%2C37.657319~55.710130%2C37.654610&rtt=pd';
  const walkingLink = shell.querySelector('.etnika-map-directions');
  if (walkingLink) walkingLink.href = WALK_ROUTE_URL;
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

    // Real Moscow Metro sign from Simple Icons, stored locally as SVG.
    const logo = document.createElement('img');
    logo.className = 'etnika-map-station__logo';
    logo.src = 'assets/moscow-metro-mark.svg';
    logo.width = 34;
    logo.height = 28;
    logo.alt = '';
    logo.decoding = 'async';

    const label=document.createElement('span');
    label.className='etnika-map-station__label';
    label.textContent='Автозаводская';
    mark.append(logo,label);
    return mark;
  }

  function createExitMark() {
    const mark = document.createElement('div');
    mark.className = 'etnika-map-exit';
    mark.setAttribute('role', 'img');
    mark.setAttribute('aria-label', 'Ближайший выход №3 из метро Автозаводская');
    const number = document.createElement('span');
    number.className = 'etnika-map-exit__number';
    number.textContent = '3';
    const label = document.createElement('span');
    label.className = 'etnika-map-exit__label';
    label.textContent = 'Выход №3';
    mark.append(number, label);
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

  async function drawPedestrianRoute(map, api) {
    if (typeof api.YMapFeature !== 'function') return;

    // Show a minimal dotted orientation guide immediately. It is explicitly
    // marked schematic until Yandex returns real pedestrian street geometry.
    const routeStyle = {
      simplificationRate: 0,
      stroke: [{width: 4, color: '#f04456', opacity: 0.96, dash: [5, 7]}]
    };
    const guide = new api.YMapFeature({
      geometry: {type: 'LineString', coordinates: APPROXIMATE_WALK_GUIDE},
      style: routeStyle
    });
    map.addChild(guide);
    shell.dataset.routeState = 'schematic';

    if (typeof api.route !== 'function') return;
    try {
      if (typeof api.getDefaultConfig === 'function') {
        const config = api.getDefaultConfig();
        if (config && typeof config.setApikeys === 'function') {
          config.setApikeys({router: API_KEY});
        }
      }
      const results = await api.route({
        points: [METRO_EXIT_3, STUDIO],
        type: 'walking'
      });
      const walking = results && results[0] && results[0].toRoute();
      const coordinates = walking && walking.geometry && walking.geometry.coordinates;
      if (!Array.isArray(coordinates) || coordinates.length < 2) return;
      // Replaces the guide, never draws two competing routes.
      guide.update({
        geometry: {type: 'LineString', coordinates: coordinates},
        style: routeStyle
      });
      shell.dataset.routeState = 'verified';
    } catch (error) {
      // Keep the explicitly labeled schematic guide, but never invent a
      // precise route. The Yandex Maps link gives walking directions.
      shell.dataset.routeState = 'schematic';
      if (window.console && console.warn) {
        console.warn('ETNIKA: walking directions available via Yandex link; embedded guide is schematic', error);
      }
    }
  }

  async function init() {
    if (!window.ymaps3) throw new Error('Yandex Maps v3 did not load');
    await window.ymaps3.ready;
    const api = window.ymaps3;
    const map = new api.YMap(root, {
      location: {center: MAP_CENTER, zoom: 16.2},
      mode: 'vector',
      showScaleInCopyrights: true
    });
    // Desaturate the native base map, including default POI and transit icons.
    // Branded markers are DOM elements above the map, so they remain red/white.
    const monochrome = [
      {elements: 'geometry', stylers: [{saturation: -1}]},
      {elements: 'label.icon', stylers: [{saturation: -1}]},
      {elements: 'label.text', stylers: [{saturation: -1}]},
      // Hide original transit-station captions so the real Moscow Metro
      // sign and our station name are the sole clean readable label.
      {tags: {all: ['transit_location']}, elements: 'label.text',
        stylers: [{visibility: 'off'}]}
    ];
    map.addChild(new api.YMapDefaultSchemeLayer({
      theme: 'dark',
      customization: monochrome
    }));
    map.addChild(new api.YMapDefaultFeaturesLayer({zIndex: 1800}));
    // Ask Yandex's pedestrian router for the real street-following geometry.
    // Keep the two accurate geo-markers even when routing is unavailable.
    drawPedestrianRoute(map, api);
    // Station center, actual nearest entrance, and studio are geo-anchored.
    map.addChild(new api.YMapMarker(
      {coordinates: METRO_EXIT_3, draggable: false}, createExitMark()
    ));
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
