/* ETNIKA contacts: georeferenced station label via Yandex Maps JS API 3.
   Public browser API key is HTTP Referer restricted by its owner.
   The native map widget is loaded only as a fallback. */
(function(){
  'use strict';
  var root=document.getElementById('etnika-contacts-map-live');
  if(!root || root.dataset.initialized) return;
  root.dataset.initialized='1';
  var shell=root.closest('.location-map');
  var section=document.getElementById('etnika-contacts-source');
  var fallbackFrame=shell && shell.querySelector('.etnika-map-widget-fallback');
  if(!shell || !section) return;
  var API_KEY='0c3d5b94-7c1d-4e23-b323-f4a620b3dcb1';
  // Moscow Metro: Avtozavodskaya, Zamoskvoretskaya line (not MCK).
  // Coordinate order in Yandex JS API v3 is [longitude, latitude].
  var STATION=[37.660467,55.706854];
  var VIEW_CENTER=[37.6566,55.7090];
  var started=false;

  function useFallback(){
    shell.dataset.mapState='fallback';
    if(fallbackFrame && !fallbackFrame.getAttribute('src')){
      fallbackFrame.setAttribute('src',fallbackFrame.getAttribute('data-map-src'));
    }
  }
  function makeStationLabel(){
    var marker=document.createElement('div');
    marker.className='etnika-map-station';
    marker.setAttribute('role','img');
    marker.setAttribute('aria-label','Метро Автозаводская');
    var icon=document.createElement('span');
    icon.className='etnika-map-station__icon';
    icon.textContent='М';
    icon.setAttribute('aria-hidden','true');
    var label=document.createElement('span');
    label.className='etnika-map-station__label';
    label.textContent='Автозаводская';
    marker.append(icon,label);
    return marker;
  }

  async function initialize(){
    if(!window.ymaps3) throw new Error('Yandex Maps API loader is unavailable');
    await window.ymaps3.ready;
    var api=window.ymaps3;
    var map=new api.YMap(root,{
      location:{center:VIEW_CENTER,zoom:15.8},
      mode:'vector',
      theme:'dark',
      showScaleInCopyrights:true
    });
    map.addChild(new api.YMapDefaultSchemeLayer({
      // Remove duplicate native station/stop labels; the target metro
      // gets a legible branded marker at its true geographic coordinate.
      customization:[{
        tags:{any:['transit_location']},
        elements:'label',
        stylers:[{visibility:'off'}]
      }]
    }));
    map.addChild(new api.YMapDefaultFeaturesLayer({zIndex:1800}));
    map.addChild(new api.YMapMarker({
      coordinates:STATION,
      draggable:false
    },makeStationLabel()));
    shell.dataset.mapState='ready';
    try{
      var ui=await api.import('@yandex/ymaps3-default-ui-theme');
      if(ui && ui.YMapZoomControl && api.YMapControls){
        map.addChild(new api.YMapControls({position:'right'})
          .addChild(new ui.YMapZoomControl({})));
      }
    }catch(ignore){
      // The map itself remains usable with mouse/touch zoom.
    }
  }

  function load(){
    if(started) return;
    started=true;
    shell.dataset.mapState='loading';
    var loader=document.createElement('script');
    loader.src='https://api-maps.yandex.ru/v3/?apikey='+encodeURIComponent(API_KEY)+'&lang=ru_RU';
    loader.async=true;
    loader.onload=function(){initialize().catch(useFallback);};
    loader.onerror=useFallback;
    document.head.appendChild(loader);
  }
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(entries){
      if(entries.some(function(entry){return entry.isIntersecting;})){
        io.disconnect();
        load();
      }
    },{rootMargin:'350px 0px'});
    io.observe(section);
  }else{
    load();
  }
})();
