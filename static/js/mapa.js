(function () {
  const page = document.querySelector('.mapa-page');

  if (!page) {
    return;
  }

  const apiUrl = page.dataset.apiUrl;
  const repositionUrlTemplate = page.dataset.repositionUrlTemplate;
  const image = document.getElementById('mapaImage');
  const stage = document.getElementById('mapaStage');
  const scrollArea = document.getElementById('mapaScroll');
  const markersLayer = document.getElementById('mapaMarkers');
  const tooltip = document.getElementById('mapTooltip');
  const toastContainer = document.getElementById('mapToast');
  const repositionToggle = document.getElementById('repositionToggle');
  const detailsEmpty = document.getElementById('detailsEmpty');
  const detailsContent = document.getElementById('detailsContent');
  const detailFields = {
    nome: document.getElementById('detailNome'),
    nomeLink: document.getElementById('detailNomeLink'),
    status: document.getElementById('detailStatus'),
    usuario: document.getElementById('detailUsuario'),
    sala: document.getElementById('detailSala'),
    ram: document.getElementById('detailRam'),
    sistema: document.getElementById('detailSistema'),
    processador: document.getElementById('detailProcessador'),
    armazenamento: document.getElementById('detailArmazenamento'),
    placaVideo: document.getElementById('detailPlacaVideo'),
    x: document.getElementById('detailX'),
    y: document.getElementById('detailY'),
    qrCode: document.getElementById('detailQrCode'),
    edit: document.getElementById('detailEdit'),
  };
  let computadores = [];
  let mapScale = 1;
  let repositionMode = false;
  let selectedComputerId = null;
  let activeDrag = null;

  function valueOrDash(value) {
    const normalized = String(value || '').trim();

    return normalized || '-';
  }

  function statusClass(status) {
    const value = String(status || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase();

    if (value.includes('manuten')) {
      return 'status-manutencao';
    }

    if (value.includes('reserva')) {
      return 'status-reserva';
    }

    if (value.includes('desligado')) {
      return 'status-desligado';
    }

    return 'status-ativo';
  }

  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(';') : [];

    for (const cookie of cookies) {
      const trimmed = cookie.trim();

      if (trimmed.startsWith(`${name}=`)) {
        return decodeURIComponent(trimmed.slice(name.length + 1));
      }
    }

    return '';
  }

  function showToast(message, type) {
    if (!toastContainer) {
      return;
    }

    const toast = document.createElement('div');
    toast.className = `map-toast ${type === 'error' ? 'map-toast-error' : 'map-toast-success'}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);

    window.setTimeout(() => {
      toast.classList.add('is-leaving');
      window.setTimeout(() => toast.remove(), 220);
    }, 2600);
  }

  function syncStageSize() {
    if (!image || !stage || !markersLayer || !scrollArea) {
      return;
    }

    const naturalWidth = image.naturalWidth || image.offsetWidth;
    const naturalHeight = image.naturalHeight || image.offsetHeight;

    if (!naturalWidth || !naturalHeight) {
      return;
    }

    const availableWidth = Math.max(scrollArea.clientWidth - 28, 320);
    const availableHeight = Math.max(scrollArea.clientHeight - 28, 320);
    const fitScale = Math.min(availableWidth / naturalWidth, availableHeight / naturalHeight);
    const balancedWidthScale = (availableWidth * 0.72) / naturalWidth;
    const balancedHeightScale = (availableHeight * 1.18) / naturalHeight;
    mapScale = Math.min(Math.max(fitScale, balancedWidthScale, balancedHeightScale), 1.2);

    const width = Math.round(naturalWidth * mapScale);
    const height = Math.round(naturalHeight * mapScale);

    stage.style.width = `${width}px`;
    stage.style.height = `${height}px`;
    markersLayer.style.width = `${width}px`;
    markersLayer.style.height = `${height}px`;
    image.style.width = `${width}px`;
    image.style.height = `${height}px`;
    scrollArea.scrollLeft = Math.max((scrollArea.scrollWidth - scrollArea.clientWidth) / 2, 0);
    positionMarkers();
  }

  function positionMarker(marker) {
    marker.style.left = `${(Number(marker.dataset.x) || 0) * mapScale}px`;
    marker.style.top = `${(Number(marker.dataset.y) || 0) * mapScale}px`;
  }

  function positionMarkers() {
    if (!markersLayer) {
      return;
    }

    markersLayer.querySelectorAll('.map-marker').forEach(positionMarker);
  }

  function tooltipHtml(computador) {
    return `
      <strong>${valueOrDash(computador.id)}</strong>
      <span>Usuario: ${valueOrDash(computador.usuario)}</span>
      <span>Sala: ${valueOrDash(computador.sala)}</span>
      <span>Status: ${valueOrDash(computador.status)}</span>
    `;
  }

  function moveTooltip(event) {
    if (!tooltip) {
      return;
    }

    tooltip.style.left = `${event.clientX + 14}px`;
    tooltip.style.top = `${event.clientY + 14}px`;
  }

  function showTooltip(event, computador) {
    if (!tooltip || activeDrag) {
      return;
    }

    tooltip.innerHTML = tooltipHtml(computador);
    tooltip.hidden = false;
    moveTooltip(event);
  }

  function hideTooltip() {
    if (tooltip) {
      tooltip.hidden = true;
    }
  }

  function updatePositionDetails(computador) {
    if (selectedComputerId !== computador.id) {
      return;
    }

    detailFields.x.textContent = valueOrDash(computador.x);
    detailFields.y.textContent = valueOrDash(computador.y);
  }

  function openDetails(computador) {
    if (!detailsContent || !detailsEmpty) {
      return;
    }

    selectedComputerId = computador.id;
    detailsEmpty.hidden = true;
    detailsContent.hidden = false;
    detailFields.nome.textContent = valueOrDash(computador.nome || computador.id);
    detailFields.nomeLink.href = computador.detail_url;
    detailFields.status.textContent = valueOrDash(computador.status);
    detailFields.status.className = `status-pill ${statusClass(computador.status)}`;
    detailFields.usuario.textContent = valueOrDash(computador.usuario);
    detailFields.sala.textContent = valueOrDash(computador.sala);
    detailFields.ram.textContent = valueOrDash(computador.ram);
    detailFields.sistema.textContent = valueOrDash(computador.sistema);
    detailFields.processador.textContent = valueOrDash(computador.processador);
    detailFields.armazenamento.textContent = valueOrDash(computador.armazenamento);
    detailFields.placaVideo.textContent = valueOrDash(computador.placa_video);
    detailFields.x.textContent = valueOrDash(computador.x);
    detailFields.y.textContent = valueOrDash(computador.y);
    detailFields.qrCode.src = computador.qr_code_url || computador.qr_code || '';
    detailFields.edit.href = computador.edit_url;
  }

  function setMarkerCoordinates(marker, x, y) {
    marker.dataset.x = x;
    marker.dataset.y = y;
    positionMarker(marker);
  }

  function repositionUrl(id) {
    return repositionUrlTemplate.replace('__ID__', encodeURIComponent(id));
  }

  async function savePosition(marker, computador, previousX, previousY, nextX, nextY) {
    try {
      const response = await fetch(repositionUrl(computador.id), {
        method: 'POST',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ x: nextX, y: nextY }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.ok) {
        throw new Error(data.error || 'Nao foi possivel salvar a posicao.');
      }

      computador.x = data.computador.x;
      computador.y = data.computador.y;
      setMarkerCoordinates(marker, computador.x, computador.y);
      updatePositionDetails(computador);
      showToast('Posicao salva com sucesso.', 'success');
    } catch (error) {
      computador.x = previousX;
      computador.y = previousY;
      setMarkerCoordinates(marker, previousX, previousY);
      updatePositionDetails(computador);
      showToast(error.message || 'Erro ao salvar a posicao.', 'error');
    }
  }

  function pointerPositionToMap(event) {
    const rect = stage.getBoundingClientRect();
    const maxX = stage.clientWidth;
    const maxY = stage.clientHeight;
    const screenX = Math.min(Math.max(event.clientX - rect.left, 0), maxX);
    const screenY = Math.min(Math.max(event.clientY - rect.top, 0), maxY);

    return {
      screenX,
      screenY,
      x: Math.round(screenX / mapScale),
      y: Math.round(screenY / mapScale),
    };
  }

  function startDrag(event, marker, computador) {
    if (!repositionMode || event.button !== 0) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    hideTooltip();

    activeDrag = {
      marker,
      computador,
      pointerId: event.pointerId,
      startClientX: event.clientX,
      startClientY: event.clientY,
      previousX: Number(computador.x) || 0,
      previousY: Number(computador.y) || 0,
      nextX: Number(computador.x) || 0,
      nextY: Number(computador.y) || 0,
      moved: false,
    };

    marker.classList.add('is-dragging');
    marker.setPointerCapture(event.pointerId);
  }

  function moveDrag(event) {
    if (!activeDrag || event.pointerId !== activeDrag.pointerId) {
      return;
    }

    event.preventDefault();

    const distance = Math.hypot(
      event.clientX - activeDrag.startClientX,
      event.clientY - activeDrag.startClientY
    );
    const position = pointerPositionToMap(event);

    activeDrag.moved = activeDrag.moved || distance > 2;
    activeDrag.nextX = position.x;
    activeDrag.nextY = position.y;
    activeDrag.marker.style.left = `${position.screenX}px`;
    activeDrag.marker.style.top = `${position.screenY}px`;
    activeDrag.computador.x = position.x;
    activeDrag.computador.y = position.y;
    updatePositionDetails(activeDrag.computador);
  }

  function endDrag(event) {
    if (!activeDrag || event.pointerId !== activeDrag.pointerId) {
      return;
    }

    const drag = activeDrag;
    activeDrag = null;
    drag.marker.classList.remove('is-dragging');

    if (drag.marker.hasPointerCapture(event.pointerId)) {
      drag.marker.releasePointerCapture(event.pointerId);
    }

    if (!drag.moved) {
      drag.computador.x = drag.previousX;
      drag.computador.y = drag.previousY;
      setMarkerCoordinates(drag.marker, drag.previousX, drag.previousY);
      updatePositionDetails(drag.computador);
      return;
    }

    drag.marker.dataset.suppressClick = 'true';
    window.setTimeout(() => {
      delete drag.marker.dataset.suppressClick;
    }, 0);

    setMarkerCoordinates(drag.marker, drag.nextX, drag.nextY);
    savePosition(
      drag.marker,
      drag.computador,
      drag.previousX,
      drag.previousY,
      drag.nextX,
      drag.nextY
    );
  }

  function setRepositionMode(enabled) {
    repositionMode = enabled;
    page.classList.toggle('reposition-enabled', repositionMode);

    if (repositionToggle) {
      repositionToggle.classList.toggle('is-active', repositionMode);
      repositionToggle.setAttribute('aria-pressed', String(repositionMode));
      repositionToggle.textContent = repositionMode ? 'Reposicionamento ligado' : 'Modo reposicionar';
    }
  }

  function renderMarkers() {
    if (!markersLayer) {
      return;
    }

    markersLayer.innerHTML = '';
    syncStageSize();

    computadores.forEach((computador) => {
      const marker = document.createElement('button');
      marker.type = 'button';
      marker.className = `map-marker ${statusClass(computador.status)}`;
      marker.setAttribute('aria-label', `Computador ${computador.id}`);
      marker.dataset.id = computador.id;
      marker.dataset.x = Number(computador.x) || 0;
      marker.dataset.y = Number(computador.y) || 0;

      marker.addEventListener('mouseenter', (event) => showTooltip(event, computador));
      marker.addEventListener('mousemove', moveTooltip);
      marker.addEventListener('mouseleave', hideTooltip);
      marker.addEventListener('pointerdown', (event) => startDrag(event, marker, computador));
      marker.addEventListener('pointermove', moveDrag);
      marker.addEventListener('pointerup', endDrag);
      marker.addEventListener('pointercancel', endDrag);
      marker.addEventListener('click', () => {
        if (marker.dataset.suppressClick === 'true') {
          return;
        }

        openDetails(computador);
      });

      markersLayer.appendChild(marker);
    });

    positionMarkers();
  }

  async function loadComputadores() {
    const response = await fetch(apiUrl, {
      headers: {
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Nao foi possivel carregar os computadores.');
    }

    const data = await response.json();
    computadores = data.computadores || [];
    renderMarkers();
  }

  if (repositionToggle) {
    repositionToggle.addEventListener('click', () => setRepositionMode(!repositionMode));
  }

  if (image) {
    if (image.complete) {
      renderMarkers();
    } else {
      image.addEventListener('load', renderMarkers, { once: true });
    }
  }

  window.addEventListener('resize', syncStageSize);

  if (window.ResizeObserver && scrollArea) {
    const resizeObserver = new ResizeObserver(syncStageSize);
    resizeObserver.observe(scrollArea);
  }

  loadComputadores().catch(() => {
    if (markersLayer) {
      markersLayer.innerHTML = '<div class="mapa-load-error">Nao foi possivel carregar os computadores.</div>';
    }
  });
}());
