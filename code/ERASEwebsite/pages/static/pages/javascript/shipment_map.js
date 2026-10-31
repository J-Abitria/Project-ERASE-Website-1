(function () {
  'use strict';

  const configElement = document.getElementById('map-config');
  const page = document.querySelector('.map-page');
  if (!configElement || !page) return;

  const config = JSON.parse(configElement.textContent);
  const locations = Array.isArray(config.locations) ? config.locations : [];
  const language = page.lang.toLowerCase().startsWith('es') ? 'es' : 'en';
  const copy = {
    en: {
      showing: (count, total) => `Showing ${count} of ${total} workshop${total === 1 ? '' : 's'}`,
      mapUnavailable: 'The map could not load. You can still browse workshop locations below.',
      tilesUnavailable: 'The map background is unavailable right now. The location list is still available.',
      invalidCoordinates: 'Some locations have invalid coordinates and cannot appear as map markers.',
      choosePoint: 'Click the map to choose a workshop location.',
      addTitle: 'Add workshop location', editTitle: 'Edit workshop location',
      deleteConfirm: 'Delete this workshop location? This cannot be undone.',
      addJourney: 'Add supply journey', editJourney: 'Edit supply journey',
      deleteJourney: 'Delete this supply journey? This cannot be undone.'
    },
    es: {
      showing: (count, total) => `Mostrando ${count} de ${total} taller${total === 1 ? '' : 'es'}`,
      mapUnavailable: 'No se pudo cargar el mapa. Aún puede consultar la lista de talleres.',
      tilesUnavailable: 'El fondo del mapa no está disponible ahora. Puede consultar la lista de lugares.',
      invalidCoordinates: 'Algunos lugares tienen coordenadas incorrectas y no aparecen en el mapa.',
      choosePoint: 'Haga clic en el mapa para elegir el lugar del taller.',
      addTitle: 'Agregar lugar del taller', editTitle: 'Editar lugar del taller',
      deleteConfirm: '¿Eliminar este lugar del taller? Esta acción no se puede deshacer.',
      addJourney: 'Agregar trayecto de suministros', editJourney: 'Editar trayecto de suministros',
      deleteJourney: '¿Eliminar este trayecto de suministros? Esta acción no se puede deshacer.'
    }
  }[language];

  function normalized(value) {
    return String(value || '').toLocaleLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  function validCoordinates(location) {
    const lat = location.latitude;
    const lng = location.longitude;
    return Number.isFinite(lat) && Number.isFinite(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
  }

  function validJourney(journey) {
    return validCoordinates({ latitude: journey.origin_latitude, longitude: journey.origin_longitude }) &&
      validCoordinates({ latitude: journey.destination_latitude, longitude: journey.destination_longitude });
  }

  function workshopDate(value) {
    const date = new Date(`${value}T12:00:00`);
    return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat(language, { dateStyle: 'medium' }).format(date);
  }

  const byId = new Map(locations.map(location => [Number(location.id), location]));
  const journeys = Array.isArray(config.journeys) ? config.journeys : [];
  const journeysById = new Map(journeys.map(journey => [Number(journey.id), journey]));
  const cards = [...document.querySelectorAll('.workshop-card')];
  const search = document.getElementById('workshop-search');
  const city = document.getElementById('city-filter');
  const when = document.getElementById('date-filter');
  const summary = document.getElementById('filter-summary');
  const notice = document.getElementById('map-notice');
  const noResults = document.getElementById('no-filter-results');
  const mapElement = document.getElementById('map');
  const today = new Date();
  const todayIso = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

  let map = null;
  const markers = new Map();
  const journeyMarkers = new Map();
  let pickingPoint = false;
  let tileWarningShown = false;
  let persistentNotice = '';

  function showNotice(message, persistent = true) {
    if (persistent) persistentNotice = message;
    notice.textContent = message;
    notice.hidden = false;
  }

  function restoreNotice() {
    notice.textContent = persistentNotice;
    notice.hidden = !persistentNotice;
  }

  function makePopup(location) {
    const content = document.createElement('div');
    const title = document.createElement('strong');
    title.textContent = location.title;
    content.appendChild(title);
    const details = document.createElement('p');
    details.textContent = [location.city, workshopDate(location.date)].filter(Boolean).join(' · ');
    content.appendChild(details);
    if (location.description) {
      const description = document.createElement('p');
      description.textContent = location.description;
      content.appendChild(description);
    }
    if (location.photo_url) {
      const photo = document.createElement('img');
      photo.src = location.photo_url;
      photo.alt = '';
      photo.loading = 'lazy';
      photo.style.cssText = 'display:block;max-width:220px;max-height:150px;object-fit:cover;margin-top:8px;border-radius:6px';
      content.appendChild(photo);
    }
    return content;
  }

  function fitLocations(visible) {
    if (!map) return;
    const points = visible.filter(validCoordinates).map(location => [Number(location.longitude), Number(location.latitude)]);
    if (points.length > 1) {
      const bounds = points.reduce((acc, point) => acc.extend(point), new maplibregl.LngLatBounds(points[0], points[0]));
      map.fitBounds(bounds, { padding: 35, maxZoom: 11 });
    } else if (points.length === 1) {
      map.flyTo({ center: points[0], zoom: 10 });
    } else {
      map.flyTo({ center: [-90.6, 15.2], zoom: 6 });
    }
  }

  function fitAll() {
    if (!map) return;
    const points = locations.filter(validCoordinates).map(location => [Number(location.longitude), Number(location.latitude)]);
    journeys.filter(validJourney).forEach(journey => {
      points.push([Number(journey.origin_longitude), Number(journey.origin_latitude)]);
      points.push([Number(journey.destination_longitude), Number(journey.destination_latitude)]);
    });
    if (points.length > 1) {
      const bounds = points.reduce((acc, point) => acc.extend(point), new maplibregl.LngLatBounds(points[0], points[0]));
      map.fitBounds(bounds, { padding: 45, maxZoom: 9 });
    } else if (points.length === 1) {
      map.flyTo({ center: points[0], zoom: 10 });
    }
  }

  // This curve illustrates the reported endpoints; it is never a measured travel path.
  function routeArc(journey) {
    const start = [Number(journey.origin_longitude), Number(journey.origin_latitude)];
    const end = [Number(journey.destination_longitude), Number(journey.destination_latitude)];
    const dx = end[0] - start[0];
    const dy = end[1] - start[1];
    const bend = 0.13;
    const control = [(start[0] + end[0]) / 2 - dy * bend, (start[1] + end[1]) / 2 + dx * bend];
    return Array.from({ length: 33 }, (_, index) => {
      const t = index / 32;
      const u = 1 - t;
      return [u * u * start[0] + 2 * u * t * control[0] + t * t * end[0],
        Math.max(-89, Math.min(89, u * u * start[1] + 2 * u * t * control[1] + t * t * end[1]))];
    });
  }

  function makeJourneyPopup(journey) {
    const content = document.createElement('div');
    const title = document.createElement('strong');
    title.textContent = journey.title;
    content.appendChild(title);
    [
      `${journey.origin_name} → ${journey.destination_name}`,
      `${journey.status_label} · ${workshopDate(journey.status_date)}`,
      journey.contents_summary,
      journey.impact_summary,
      journey.partner_name
    ].filter(Boolean).forEach(value => {
      const paragraph = document.createElement('p');
      paragraph.textContent = value;
      content.appendChild(paragraph);
    });
    return content;
  }

  function filteredLocations() {
    const query = normalized(search.value.trim());
    const selectedCity = city.value;
    const selectedWhen = when.value;
    return locations.filter(location => {
      const text = normalized([location.title, location.city, location.description].join(' '));
      if (query && !text.includes(query)) return false;
      if (selectedCity && location.city !== selectedCity) return false;
      if (selectedWhen === 'upcoming' && location.date < todayIso) return false;
      if (selectedWhen === 'past' && location.date >= todayIso) return false;
      return true;
    });
  }

  function updateFilters() {
    const visible = filteredLocations();
    const ids = new Set(visible.map(location => Number(location.id)));
    cards.forEach(card => { card.hidden = !ids.has(Number(card.dataset.workshopId)); });
    noResults.hidden = !locations.length || visible.length !== 0;
    summary.textContent = copy.showing(visible.length, locations.length);
    markers.forEach((marker, id) => {
      if (ids.has(id)) marker.addTo(map);
      else marker.remove();
    });
    fitLocations(visible);
  }

  if (typeof maplibregl !== 'undefined') {
    try {
      map = new maplibregl.Map({
        container: mapElement,
        style: config.style_url,
        center: [-90.6, 15.2],
        zoom: 6,
        maxZoom: 19,
        attributionControl: true
      });
    } catch (error) {
      showNotice(copy.mapUnavailable);
    }
  }
  if (map) {
    map.scrollZoom.disable();
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left');
    map.on('error', () => {
      if (!tileWarningShown) {
        showNotice(copy.tilesUnavailable);
        tileWarningShown = true;
      }
    });
    map.on('load', () => {
      map.addSource('supply-journeys', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: journeys.filter(validJourney).map(journey => ({
            type: 'Feature',
            geometry: { type: 'LineString', coordinates: routeArc(journey) },
            properties: { id: journey.id }
          }))
        }
      });
      map.addLayer({
        id: 'supply-journeys', type: 'line', source: 'supply-journeys',
        paint: { 'line-color': '#d17621', 'line-width': 3, 'line-opacity': 0.85, 'line-dasharray': [2, 2] }
      });
    });
    locations.filter(validCoordinates).forEach(location => {
      const popup = new maplibregl.Popup({ maxWidth: '260px' }).setDOMContent(makePopup(location));
      const marker = new maplibregl.Marker()
        .setLngLat([Number(location.longitude), Number(location.latitude)])
        .setPopup(popup);
      marker.getElement().setAttribute('aria-label', [location.title, location.city].filter(Boolean).join(', '));
      markers.set(Number(location.id), marker);
    });
    journeys.filter(validJourney).forEach(journey => {
      const element = document.createElement('button');
      element.type = 'button';
      element.className = 'journey-marker';
      element.textContent = '●';
      element.setAttribute('aria-label', [journey.title, journey.destination_name].join(', '));
      const marker = new maplibregl.Marker({ element, anchor: 'bottom' })
        .setLngLat([Number(journey.destination_longitude), Number(journey.destination_latitude)])
        .setPopup(new maplibregl.Popup({ maxWidth: '260px' }).setDOMContent(makeJourneyPopup(journey)));
      marker.addTo(map);
      journeyMarkers.set(Number(journey.id), marker);
    });
    document.querySelectorAll('.focus-shipment').forEach(button => {
      if (journeyMarkers.has(Number(button.dataset.id))) button.hidden = false;
    });
    if (locations.some(location => !validCoordinates(location))) showNotice(copy.invalidCoordinates);
    document.getElementById('fit-workshops').hidden = false;
    document.querySelectorAll('.focus-workshop').forEach(button => {
      if (markers.has(Number(button.dataset.id))) button.hidden = false;
    });
  } else if (notice.hidden) {
    showNotice(copy.mapUnavailable);
  }

  search.addEventListener('input', updateFilters);
  city.addEventListener('change', updateFilters);
  when.addEventListener('change', updateFilters);
  document.getElementById('clear-filters').addEventListener('click', () => {
    search.value = '';
    city.value = '';
    when.value = '';
    updateFilters();
  });
  document.getElementById('fit-workshops').addEventListener('click', fitAll);
  document.querySelectorAll('.focus-workshop').forEach(button => {
    button.addEventListener('click', () => {
      const marker = markers.get(Number(button.dataset.id));
      if (!marker || !map) return;
      const position = marker.getLngLat();
      map.flyTo({ center: [position.lng, position.lat], zoom: Math.max(map.getZoom(), 10) });
      if (!marker.getPopup().isOpen()) marker.togglePopup();
      mapElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  });
  updateFilters();
  if (journeys.length) fitAll();

  document.querySelectorAll('.focus-shipment').forEach(button => {
    button.addEventListener('click', () => {
      const journey = journeysById.get(Number(button.dataset.id));
      const marker = journeyMarkers.get(Number(button.dataset.id));
      if (!journey || !marker || !map) return;
      const bounds = new maplibregl.LngLatBounds()
        .extend([Number(journey.origin_longitude), Number(journey.origin_latitude)])
        .extend([Number(journey.destination_longitude), Number(journey.destination_latitude)]);
      map.fitBounds(bounds, { padding: 55, maxZoom: 10 });
      if (!marker.getPopup().isOpen()) marker.togglePopup();
      mapElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  });

  const dialog = document.getElementById('workshop-dialog');
  if (!dialog) return;
  const form = document.getElementById('workshop-form');
  const action = document.getElementById('workshop-action');
  const workshopId = document.getElementById('workshop-id');
  const dialogTitle = document.getElementById('workshop-dialog-title');
  const pickButton = document.getElementById('pick-workshop-point');
  if (map) pickButton.hidden = false;

  function openEditor(location) {
    pickingPoint = false;
    form.reset();
    action.value = location ? 'update_workshop' : 'create_workshop';
    workshopId.value = location ? location.id : '';
    dialogTitle.textContent = location ? copy.editTitle : copy.addTitle;
    if (location) {
      ['title', 'city', 'date', 'description', 'latitude', 'longitude'].forEach(name => {
        form.elements[name].value = location[name] ?? '';
      });
    }
    dialog.showModal();
  }

  document.getElementById('add-workshop').addEventListener('click', () => openEditor(null));
  document.querySelectorAll('.edit-workshop').forEach(button => {
    button.addEventListener('click', () => openEditor(byId.get(Number(button.dataset.id))));
  });
  document.querySelectorAll('.delete-workshop-form').forEach(deleteForm => {
    deleteForm.addEventListener('submit', event => {
      if (!window.confirm(copy.deleteConfirm)) event.preventDefault();
    });
  });
  document.getElementById('close-workshop').addEventListener('click', () => dialog.close());
  document.getElementById('cancel-workshop').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => {
    if (!pickingPoint) restoreNotice();
  });
  if (map) {
    pickButton.addEventListener('click', () => {
      pickingPoint = true;
      dialog.close();
      showNotice(copy.choosePoint, false);
      mapElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      mapElement.focus();
    });
    map.on('click', event => {
      if (!pickingPoint) return;
      form.elements.latitude.value = event.lngLat.lat.toFixed(6);
      form.elements.longitude.value = event.lngLat.lng.toFixed(6);
      pickingPoint = false;
      restoreNotice();
      dialog.showModal();
    });
  }
  if (dialog.hasAttribute('data-open-on-load')) dialog.showModal();

  const shipmentDialog = document.getElementById('shipment-dialog');
  const shipmentForm = document.getElementById('shipment-form');
  const shipmentAction = document.getElementById('shipment-action');
  const shipmentId = document.getElementById('shipment-id');
  const shipmentTitle = document.getElementById('shipment-dialog-title');
  function openShipmentEditor(journey) {
    shipmentForm.reset();
    shipmentAction.value = journey ? 'update_shipment' : 'create_shipment';
    shipmentId.value = journey ? journey.id : '';
    shipmentTitle.textContent = journey ? copy.editJourney : copy.addJourney;
    if (journey) {
      [
        'title', 'origin_name', 'origin_latitude', 'origin_longitude',
        'destination_name', 'destination_latitude', 'destination_longitude',
        'contents_summary', 'impact_summary', 'partner_name', 'status', 'status_date'
      ].forEach(name => { shipmentForm.elements[name].value = journey[name] ?? ''; });
      shipmentForm.elements.is_published.checked = Boolean(journey.is_published);
    }
    shipmentDialog.showModal();
  }
  document.getElementById('add-shipment').addEventListener('click', () => openShipmentEditor(null));
  document.querySelectorAll('.edit-shipment').forEach(button => {
    button.addEventListener('click', () => openShipmentEditor(journeysById.get(Number(button.dataset.id))));
  });
  document.querySelectorAll('.delete-shipment-form').forEach(deleteForm => {
    deleteForm.addEventListener('submit', event => {
      if (!window.confirm(copy.deleteJourney)) event.preventDefault();
    });
  });
  document.getElementById('close-shipment').addEventListener('click', () => shipmentDialog.close());
  document.getElementById('cancel-shipment').addEventListener('click', () => shipmentDialog.close());
  if (shipmentDialog.hasAttribute('data-open-on-load')) shipmentDialog.showModal();
})();
