/* ETNIKA Prices v3 — prices and inclusions preserved from the current site */
(function () {
  'use strict';
  const root=document.getElementById('etnika-prices-clear');
  if(!root || !root.classList.contains('ev3') || root.dataset.ev3Initialized==='true') return;
  root.dataset.ev3Initialized='true';
  const packages={
    express:{
      name:'Экспресс',mins:'30 минут',people:'до 2 человек · больше — по согласованию',
      kicker:'Быстрый формат',description:'Для короткой индивидуальной съёмки, новых портретов или быстрого обновления контента.',
      prices:{weekday:'2 900',weekend:'3 900'},photo:'assets/etnika-bw-portrait.jpg',
      features:[
        'Базовый белый фон',
        'Неограниченное число ч/б или цветных фотографий с цветокоррекцией',
        'Портретная съёмка или фотографии в полный рост',
        'Готовые фотографии в течение 24 часов',
        'Гримёрная зона',
        'Кулер с водой'
      ]
    },
    standard:{
      name:'Стандарт',mins:'60 минут',people:'до 4 человек · больше — по согласованию',
      kicker:'Оптимальный выбор',description:'Оптимально, если хочется спокойно поснимать несколько образов без спешки.',
      prices:{weekday:'4 500',weekend:'5 900'},photo:'assets/etnika-portrait-dark.jpg',
      features:[
        'Базовый белый фон',
        'Неограниченное число ч/б или цветных фотографий с цветокоррекцией',
        'Портретная съёмка или фотографии в полный рост',
        'Готовые фотографии в течение 24 часов',
        'Чай, кофе, вода и сладости',
        'Гримёрная зона и отпариватель для одежды',
        'Музыкальная колонка и Wi-Fi',
        'Реквизит бесплатно'
      ]
    },
    premium:{
      name:'Премиум',mins:'100 минут',people:'до 6 человек · больше — по согласованию',
      kicker:'Максимум свободы',description:'Для нескольких образов, большой компании и съёмки, где хочется времени на эксперименты.',
      prices:{weekday:'7 500',weekend:'9 000'},photo:'assets/etnika-portrait-beige.jpg',
      features:[
        'Базовый белый фон',
        'Неограниченное число ч/б или цветных фотографий с цветокоррекцией',
        'Портретная съёмка или фотографии в полный рост',
        'Готовые фотографии в течение 24 часов',
        'Чай, кофе, вода и сладости',
        'Гримёрная зона и отпариватель для одежды',
        'Музыкальная колонка и Wi-Fi',
        'Реквизит бесплатно',
        'Онлайн-альбом готовых фотографий',
        'Подарки детям и именинникам'
      ]
    }
  };
  const planButtons=[...root.querySelectorAll('.ev3-plan')];
  const modeButtons=[...root.querySelectorAll('.ev3-modes button')];
  const photo=root.querySelector('.ev3-photo');
  const visual=root.querySelector('.ev3-visual');
  const photoLabel=root.querySelector('.ev3-photo-label strong');
  const photoKicker=root.querySelector('.ev3-photo-label span');
  const sheet=root.querySelector('.ev3-sheet');
  const sheetPanel=root.querySelector('.ev3-sheet-panel');
  const sheetTitle=root.querySelector('.ev3-sheet-title');
  const sheetSub=root.querySelector('.ev3-sheet-sub');
  const sheetDescription=root.querySelector('.ev3-sheet-description');
  const featureList=root.querySelector('.ev3-feature-list');
  const priceSheet=root.querySelector('.ev3-sheet-price');
  const buttonOpen=root.querySelector('.ev3-details-open');
  const buttonClose=root.querySelector('.ev3-close');
  const backdrop=root.querySelector('.ev3-scrim');
  let plan='standard';
  let mode='weekday';
  let lastFocus=null;
  let previousBodyOverflow='';
  let sheetOpen=false;
  function render(){
    const data=packages[plan];
    planButtons.forEach(button=>{
      const selected=button.dataset.plan===plan;
      button.setAttribute('aria-pressed',String(selected));
      button.querySelector('.ev3-plan-price').textContent=packages[button.dataset.plan].prices[mode]+' ₽';
    });
    modeButtons.forEach(button=>{
      button.setAttribute('aria-pressed',String(button.dataset.mode===mode));
    });
    photo.src=data.photo;
    photo.alt=data.name+' — съёмка в студии ЭТНИКА';
    photoLabel.textContent=data.name+' · '+data.mins;
    photoKicker.textContent=data.kicker;
    sheetTitle.textContent=data.name;
    sheetSub.textContent=data.mins+' · '+data.people;
    sheetDescription.textContent=data.description;
    featureList.replaceChildren(...data.features.map(feature=>{
      const li=document.createElement('li');
      li.textContent=feature;
      return li;
    }));
    priceSheet.textContent=data.prices[mode]+' ₽';
    root.dataset.planTheme=plan;
  }
  /* The drawer has 100dvh height, but its LEFT edge must never cover prices.
     The photo's horizontal start is the natural boundary of the right rail.
     Actual price-label geometry is a hard safety bound on narrower desktops. */
  function updatePanelRail(){
    const desktop=window.innerWidth>=1101;
    sheet.setAttribute('aria-modal',String(!desktop));
    if(!desktop){
      sheet.style.removeProperty('--ev3-panel-left');
      return;
    }
    const photoLeft=visual.getBoundingClientRect().left;
    const priceRight=Math.max(...planButtons.map(button=>
      button.querySelector('.ev3-plan-price').getBoundingClientRect().right
    ));
    const panelLeft=Math.ceil(Math.max(photoLeft,priceRight+24));
    sheet.style.setProperty('--ev3-panel-left',panelLeft+'px');
  }
  window.addEventListener('resize',()=>{
    if(sheetOpen){
      updatePanelRail();
      document.body.style.overflow=window.innerWidth>=1101?previousBodyOverflow:'hidden';
    }
  },{passive:true});
  function open(){
    if(sheetOpen) return;
    updatePanelRail();
    sheetOpen=true;
    lastFocus=document.activeElement;
    previousBodyOverflow=document.body.style.overflow;
    /* Desktop is a non-modal side rail: the tariff list must remain scrollable. */
    if(window.innerWidth<1101)document.body.style.overflow='hidden';
    sheet.inert=false;
    sheet.setAttribute('aria-hidden','false');
    sheet.dataset.open='true';
    buttonOpen.setAttribute('aria-expanded','true');
    buttonClose.focus();
  }
  function close(){
    if(!sheetOpen) return;
    sheetOpen=false;
    sheet.dataset.open='false';
    sheet.setAttribute('aria-hidden','true');
    sheet.inert=true;
    buttonOpen.setAttribute('aria-expanded','false');
    document.body.style.overflow=previousBodyOverflow;
    if(lastFocus && document.contains(lastFocus)) lastFocus.focus();
  }
  planButtons.forEach(button=>{
    button.addEventListener('click',()=>{
      plan=button.dataset.plan;
      render();
      if(sheetOpen)close();
    });
  });
  modeButtons.forEach(button=>{
    button.addEventListener('click',()=>{
      mode=button.dataset.mode;
      render();
    });
  });
  buttonOpen.addEventListener('click',open);
  buttonClose.addEventListener('click',close);
  backdrop.addEventListener('click',close);
  document.addEventListener('pointerdown',event=>{
    if(sheetOpen && window.innerWidth>=1101 &&
       !sheetPanel.contains(event.target) &&
       !buttonOpen.contains(event.target)){
      close();
    }
  });
  document.addEventListener('keydown',event=>{
    if(!sheetOpen)return;
    if(event.key==='Escape'){
      event.preventDefault();close();return;
    }
    if(event.key==='Tab' && window.innerWidth<1101){
      const focusable=[...sheetPanel.querySelectorAll('button:not([disabled]),a[href],input:not([disabled])')].filter(x=>x.getClientRects().length);
      if(!focusable.length)return;
      const first=focusable[0],last=focusable[focusable.length-1];
      if(event.shiftKey && document.activeElement===first){event.preventDefault();last.focus();}
      else if(!event.shiftKey && document.activeElement===last){event.preventDefault();first.focus();}
    }
  });
  render();
})();
