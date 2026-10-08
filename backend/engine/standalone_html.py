"""Generates a zero-dependency, single-file standalone HTML gallery (BUILD_PLAN / SPEC).

This HTML file embeds people.json and config.json inline, allowing it to be opened
directly via double-click (file:// protocol) in any browser without CORS errors,
while loading local images from faces/ and thumbs/ relative paths.
"""

import json
from pathlib import Path
from typing import Dict, Any

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__TITLE__ — PhotoSorter Gallery</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --color-accent: __ACCENT__;
      --bg-main: #09090b;
      --bg-card: rgba(24, 24, 27, 0.75);
      --bg-card-hover: rgba(39, 39, 42, 0.85);
      --border-color: rgba(63, 63, 70, 0.4);
      --text-main: #f4f4f5;
      --text-muted: #a1a1aa;
      --font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background-color: var(--bg-main);
      color: var(--text-main);
      font-family: var(--font-family);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      -webkit-font-smoothing: antialiased;
    }

    /* Header */
    header {
      position: sticky;
      top: 0;
      z-index: 40;
      background: rgba(9, 9, 11, 0.85);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border-color);
      padding: 1rem 1.5rem;
    }

    .header-container {
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }

    .brand-title h1 {
      font-family: 'Outfit', var(--font-family);
      font-size: 1.5rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: #fff;
    }

    .brand-title p {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 0.15rem;
    }

    .controls {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }

    .search-box {
      position: relative;
    }

    .search-box input {
      background: rgba(24, 24, 27, 0.8);
      border: 1px solid var(--border-color);
      color: #fff;
      padding: 0.5rem 1rem 0.5rem 2.25rem;
      border-radius: 9999px;
      font-size: 0.875rem;
      outline: none;
      width: 240px;
      transition: all 0.2s;
    }

    .search-box input:focus {
      border-color: var(--color-accent);
      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25);
      width: 280px;
    }

    .search-box svg {
      position: absolute;
      left: 0.75rem;
      top: 50%;
      transform: translateY(-50%);
      width: 1rem;
      height: 1rem;
      color: var(--text-muted);
      pointer-events: none;
    }

    /* Nav Tabs */
    .nav-tabs {
      display: flex;
      background: rgba(24, 24, 27, 0.6);
      padding: 0.25rem;
      border-radius: 9999px;
      border: 1px solid var(--border-color);
    }

    .nav-tab {
      padding: 0.4rem 0.9rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-muted);
      background: transparent;
      border: none;
      cursor: pointer;
      transition: all 0.2s;
    }

    .nav-tab.active {
      background: var(--color-accent);
      color: #fff;
      box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }

    /* Main Container */
    main {
      max-width: 1400px;
      margin: 0 auto;
      padding: 2rem 1.5rem;
      flex: 1;
      width: 100%;
    }

    .stats-bar {
      display: flex;
      gap: 1.5rem;
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid var(--border-color);
      font-size: 0.875rem;
      color: var(--text-muted);
    }

    .stats-bar strong {
      color: #fff;
      font-family: monospace;
    }

    /* People Grid */
    .people-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 1.5rem;
    }

    .person-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 1.25rem;
      overflow: hidden;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
      display: flex;
      flex-direction: column;
    }

    .person-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 24px -10px rgba(0, 0, 0, 0.7);
      border-color: rgba(99, 102, 241, 0.5);
      background: var(--bg-card-hover);
    }

    .avatar-wrapper {
      position: relative;
      width: 100%;
      aspect-ratio: 1;
      background: #18181b;
      overflow: hidden;
    }

    .avatar-wrapper img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.3s ease;
    }

    .person-card:hover .avatar-wrapper img {
      transform: scale(1.05);
    }

    .photo-count-badge {
      position: absolute;
      bottom: 0.75rem;
      right: 0.75rem;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #fff;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.25rem 0.6rem;
      border-radius: 9999px;
    }

    .card-info {
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .person-label {
      font-weight: 600;
      font-size: 1rem;
      color: #fff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .thumb-strip {
      display: flex;
      gap: 0.35rem;
      overflow: hidden;
      height: 48px;
    }

    .thumb-strip img {
      width: 48px;
      height: 48px;
      object-fit: cover;
      border-radius: 0.35rem;
      opacity: 0.85;
      transition: opacity 0.2s;
    }

    .person-card:hover .thumb-strip img {
      opacity: 1;
    }

    /* Photos Grid (All Photos View) */
    .photos-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 1.25rem;
    }

    .photo-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 1rem;
      overflow: hidden;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .photo-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 8px 20px rgba(0,0,0,0.6);
      border-color: var(--color-accent);
    }

    .photo-card img {
      width: 100%;
      aspect-ratio: 4/3;
      object-fit: cover;
      display: block;
    }

    .photo-card-info {
      padding: 0.6rem 0.75rem;
      font-size: 0.75rem;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    /* Unrecognized Grid */
    .unrec-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 1rem;
    }

    .unrec-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 0.75rem;
      overflow: hidden;
      text-align: center;
      padding-bottom: 0.5rem;
    }

    .unrec-card img {
      width: 100%;
      aspect-ratio: 1;
      object-fit: cover;
    }

    .unrec-card .reason {
      font-size: 0.65rem;
      color: #f59e0b;
      margin-top: 0.35rem;
      text-transform: capitalize;
    }

    /* Modal / Lightbox */
    .modal-overlay {
      display: none;
      position: fixed;
      inset: 0;
      z-index: 100;
      background: rgba(0, 0, 0, 0.85);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      justify-content: center;
      align-items: center;
      padding: 1.5rem;
    }

    .modal-overlay.open {
      display: flex;
    }

    .modal-content {
      background: #121214;
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 1.5rem;
      width: 100%;
      max-width: 1100px;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.85);
    }

    .modal-header {
      padding: 1.25rem 1.5rem;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(24, 24, 27, 0.5);
    }

    .modal-header-left {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .modal-header-left img {
      width: 48px;
      height: 48px;
      border-radius: 9999px;
      object-fit: cover;
      border: 2px solid var(--color-accent);
    }

    .modal-title h3 {
      font-size: 1.25rem;
      font-weight: 700;
      color: #fff;
    }

    .modal-title p {
      font-size: 0.8rem;
      color: var(--text-muted);
    }

    .close-btn {
      background: rgba(255, 255, 255, 0.1);
      border: none;
      color: #fff;
      width: 2rem;
      height: 2rem;
      border-radius: 9999px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.25rem;
      transition: background 0.2s;
    }

    .close-btn:hover {
      background: rgba(255, 255, 255, 0.2);
    }

    .modal-body {
      padding: 1.5rem;
      overflow-y: auto;
      flex: 1;
    }

    .modal-gallery {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 1rem;
    }

    .modal-photo-item {
      border-radius: 0.75rem;
      overflow: hidden;
      background: #18181b;
      cursor: pointer;
      border: 1px solid var(--border-color);
      transition: transform 0.2s;
    }

    .modal-photo-item:hover {
      transform: scale(1.03);
      border-color: var(--color-accent);
    }

    .modal-photo-item img {
      width: 100%;
      aspect-ratio: 4/3;
      object-fit: cover;
      display: block;
    }

    /* Lightbox Modal */
    .lightbox {
      display: none;
      position: fixed;
      inset: 0;
      z-index: 150;
      background: rgba(0, 0, 0, 0.95);
      flex-direction: column;
      justify-content: center;
      align-items: center;
      padding: 1rem;
    }

    .lightbox.open {
      display: flex;
    }

    .lightbox img {
      max-width: 90vw;
      max-height: 80vh;
      object-fit: contain;
      border-radius: 0.5rem;
      box-shadow: 0 0 30px rgba(0,0,0,0.8);
    }

    .lightbox-nav {
      margin-top: 1rem;
      display: flex;
      align-items: center;
      gap: 1.5rem;
    }

    .lightbox-btn {
      background: rgba(255, 255, 255, 0.15);
      border: none;
      color: #fff;
      padding: 0.5rem 1.25rem;
      border-radius: 9999px;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.85rem;
      transition: background 0.2s;
    }

    .lightbox-btn:hover {
      background: rgba(255, 255, 255, 0.3);
    }

    .lightbox-close {
      position: absolute;
      top: 1.5rem;
      right: 1.5rem;
      font-size: 2rem;
      color: #fff;
      background: transparent;
      border: none;
      cursor: pointer;
    }

    /* Footer */
    footer {
      border-top: 1px solid var(--border-color);
      padding: 1.5rem;
      text-align: center;
      color: var(--text-muted);
      font-size: 0.8rem;
    }

    @media (max-width: 640px) {
      .header-container {
        flex-direction: column;
        align-items: flex-start;
      }
      .search-box input {
        width: 100%;
      }
      .people-grid {
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      }
    }
  </style>
</head>
<body>

  <!-- Top Header -->
  <header>
    <div class="header-container">
      <div class="brand-title">
        <h1 id="event-title">__TITLE__</h1>
        <p id="event-subtitle">__SUBTITLE__</p>
      </div>

      <div class="controls">
        <div class="search-box">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input type="text" id="search-input" placeholder="Search people or photos..." />
        </div>

        <div class="nav-tabs">
          <button class="nav-tab active" data-tab="people">People</button>
          <button class="nav-tab" data-tab="photos">All Photos</button>
          <button class="nav-tab" data-tab="unrecognized">Unrecognized</button>
        </div>
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main>
    <div class="stats-bar">
      <span>People: <strong id="stat-people">0</strong></span>
      <span>Photos: <strong id="stat-photos">0</strong></span>
      <span>Recognized Faces: <strong id="stat-faces">0</strong></span>
    </div>

    <!-- People View -->
    <div id="view-people" class="tab-view">
      <div class="people-grid" id="people-grid"></div>
    </div>

    <!-- Photos View -->
    <div id="view-photos" class="tab-view" style="display: none;">
      <div class="photos-grid" id="photos-grid"></div>
    </div>

    <!-- Unrecognized View -->
    <div id="view-unrecognized" class="tab-view" style="display: none;">
      <div class="unrec-grid" id="unrec-grid"></div>
    </div>
  </main>

  <!-- Person Gallery Modal -->
  <div class="modal-overlay" id="person-modal">
    <div class="modal-content">
      <div class="modal-header">
        <div class="modal-header-left">
          <img id="modal-person-avatar" src="" alt="Avatar" />
          <div class="modal-title">
            <h3 id="modal-person-name">Person Name</h3>
            <p id="modal-person-count">0 photos</p>
          </div>
        </div>
        <button class="close-btn" id="modal-close-btn">&times;</button>
      </div>
      <div class="modal-body">
        <div class="modal-gallery" id="modal-gallery"></div>
      </div>
    </div>
  </div>

  <!-- Lightbox -->
  <div class="lightbox" id="lightbox">
    <button class="lightbox-close" id="lightbox-close-btn">&times;</button>
    <img id="lightbox-img" src="" alt="Enlarged Photo" />
    <div class="lightbox-nav">
      <button class="lightbox-btn" id="lightbox-prev">Previous</button>
      <span id="lightbox-counter" style="color: #aaa; font-size: 0.85rem;">1 / 1</span>
      <button class="lightbox-btn" id="lightbox-next">Next</button>
    </div>
  </div>

  <!-- Footer -->
  <footer>
    <p>__FOOTER__</p>
  </footer>

  <!-- Inline Gallery Dataset -->
  <script id="gallery-data" type="application/json">
__PEOPLE_JSON__
  </script>
  <script id="gallery-config" type="application/json">
__CONFIG_JSON__
  </script>

  <!-- Client App Logic -->
  <script>
    (function() {
      // Parse embedded data directly
      let data = JSON.parse(document.getElementById('gallery-data').textContent);
      let config = JSON.parse(document.getElementById('gallery-config').textContent);

      let currentTab = 'people';
      let searchQuery = '';
      let activeLightboxList = [];
      let activeLightboxIndex = 0;

      // DOM Elements
      const peopleGrid = document.getElementById('people-grid');
      const photosGrid = document.getElementById('photos-grid');
      const unrecGrid = document.getElementById('unrec-grid');
      const searchInput = document.getElementById('search-input');
      const personModal = document.getElementById('person-modal');
      const modalGallery = document.getElementById('modal-gallery');
      const modalAvatar = document.getElementById('modal-person-avatar');
      const modalName = document.getElementById('modal-person-name');
      const modalCount = document.getElementById('modal-person-count');
      const lightbox = document.getElementById('lightbox');
      const lightboxImg = document.getElementById('lightbox-img');
      const lightboxCounter = document.getElementById('lightbox-counter');

      // Update Stats
      document.getElementById('stat-people').textContent = data.people ? data.people.length : 0;
      document.getElementById('stat-photos').textContent = data.photos ? Object.keys(data.photos).length : 0;
      let totalFaces = 0;
      if (data.people) {
        data.people.forEach(p => totalFaces += (p.faces ? p.faces.length : 0));
      }
      document.getElementById('stat-faces').textContent = totalFaces;

      // Render People
      function renderPeople() {
        peopleGrid.innerHTML = '';
        const query = searchQuery.toLowerCase().trim();
        const filtered = (data.people || []).filter(p => {
          const name = p.label || ('Person ' + p.id.replace(/^p0*/, ''));
          return name.toLowerCase().includes(query) || p.id.toLowerCase().includes(query);
        });

        if (filtered.length === 0) {
          peopleGrid.innerHTML = '<p style="color: #71717a; grid-column: 1/-1; text-align: center; padding: 3rem;">No people match your search.</p>';
          return;
        }

        filtered.forEach(person => {
          const card = document.createElement('div');
          card.className = 'person-card';
          const name = person.label || ('Person ' + person.id.replace(/^p0*/, ''));
          const photoIds = person.photo_ids || person.photos || [];

          let thumbsHtml = '';
          photoIds.slice(0, 4).forEach(pid => {
            const pObj = data.photos[pid];
            if (pObj && pObj.thumb) {
              thumbsHtml += '<img src="' + pObj.thumb + '" alt="thumb" loading="lazy" />';
            }
          });

          card.innerHTML = `
            <div class="avatar-wrapper">
              <img src="${person.face}" alt="${name}" loading="lazy" />
              <div class="photo-count-badge">${photoIds.length} photo${photoIds.length === 1 ? '' : 's'}</div>
            </div>
            <div class="card-info">
              <div class="person-label">${name}</div>
              <div class="thumb-strip">${thumbsHtml}</div>
            </div>
          `;

          card.addEventListener('click', () => openPersonModal(person));
          peopleGrid.appendChild(card);
        });
      }

      // Render All Photos
      function renderPhotos() {
        photosGrid.innerHTML = '';
        const query = searchQuery.toLowerCase().trim();
        const photoEntries = Object.entries(data.photos || {});
        const filtered = photoEntries.filter(([pid, p]) => {
          return p.name.toLowerCase().includes(query) || pid.toLowerCase().includes(query);
        });

        if (filtered.length === 0) {
          photosGrid.innerHTML = '<p style="color: #71717a; grid-column: 1/-1; text-align: center; padding: 3rem;">No photos match your search.</p>';
          return;
        }

        filtered.forEach(([pid, photo], idx) => {
          const card = document.createElement('div');
          card.className = 'photo-card';
          card.innerHTML = `
            <img src="${photo.thumb}" alt="${photo.name}" loading="lazy" />
            <div class="photo-card-info">
              <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px;">${photo.name}</span>
              <span>${photo.width}x${photo.height}</span>
            </div>
          `;
          card.addEventListener('click', () => {
            activeLightboxList = filtered.map(([_, p]) => p.thumb);
            activeLightboxIndex = idx;
            openLightbox();
          });
          photosGrid.appendChild(card);
        });
      }

      // Render Unrecognized Faces
      function renderUnrecognized() {
        unrecGrid.innerHTML = '';
        const unrecFaces = (data.unrecognized && data.unrecognized.faces) || [];
        if (unrecFaces.length === 0) {
          unrecGrid.innerHTML = '<p style="color: #71717a; grid-column: 1/-1; text-align: center; padding: 3rem;">No unrecognized faces.</p>';
          return;
        }

        unrecFaces.forEach(f => {
          const card = document.createElement('div');
          card.className = 'unrec-card';
          card.innerHTML = `
            <img src="${f.face}" alt="${f.file_name}" loading="lazy" />
            <div class="reason">${f.rejection_reason || 'Unrecognized'}</div>
          `;
          unrecGrid.appendChild(card);
        });
      }

      // Person Modal Open
      function openPersonModal(person) {
        const name = person.label || ('Person ' + person.id.replace(/^p0*/, ''));
        const photoIds = person.photo_ids || person.photos || [];

        modalAvatar.src = person.face;
        modalName.textContent = name;
        modalCount.textContent = `${photoIds.length} photo${photoIds.length === 1 ? '' : 's'}`;
        modalGallery.innerHTML = '';

        const personPhotoThumbs = [];
        photoIds.forEach((pid, idx) => {
          const pObj = data.photos[pid];
          if (pObj && pObj.thumb) {
            personPhotoThumbs.push(pObj.thumb);
            const item = document.createElement('div');
            item.className = 'modal-photo-item';
            item.innerHTML = `<img src="${pObj.thumb}" alt="${pObj.name}" loading="lazy" />`;
            item.addEventListener('click', () => {
              activeLightboxList = personPhotoThumbs;
              activeLightboxIndex = idx;
              openLightbox();
            });
            modalGallery.appendChild(item);
          }
        });

        personModal.classList.add('open');
      }

      // Lightbox Functions
      function openLightbox() {
        if (!activeLightboxList.length) return;
        updateLightbox();
        lightbox.classList.add('open');
      }

      function updateLightbox() {
        lightboxImg.src = activeLightboxList[activeLightboxIndex];
        lightboxCounter.textContent = `${activeLightboxIndex + 1} / ${activeLightboxList.length}`;
      }

      document.getElementById('lightbox-prev').addEventListener('click', () => {
        activeLightboxIndex = (activeLightboxIndex - 1 + activeLightboxList.length) % activeLightboxList.length;
        updateLightbox();
      });

      document.getElementById('lightbox-next').addEventListener('click', () => {
        activeLightboxIndex = (activeLightboxIndex + 1) % activeLightboxList.length;
        updateLightbox();
      });

      document.getElementById('lightbox-close-btn').addEventListener('click', () => {
        lightbox.classList.remove('open');
      });

      document.getElementById('modal-close-btn').addEventListener('click', () => {
        personModal.classList.remove('open');
      });

      personModal.addEventListener('click', (e) => {
        if (e.target === personModal) personModal.classList.remove('open');
      });

      // Tab switching
      document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => {
          document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
          tab.classList.add('active');
          currentTab = tab.dataset.tab;

          document.getElementById('view-people').style.display = currentTab === 'people' ? 'block' : 'none';
          document.getElementById('view-photos').style.display = currentTab === 'photos' ? 'block' : 'none';
          document.getElementById('view-unrecognized').style.display = currentTab === 'unrecognized' ? 'block' : 'none';

          if (currentTab === 'people') renderPeople();
          if (currentTab === 'photos') renderPhotos();
          if (currentTab === 'unrecognized') renderUnrecognized();
        });
      });

      // Search Handler
      searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value;
        if (currentTab === 'people') renderPeople();
        if (currentTab === 'photos') renderPhotos();
      });

      // Initial Render
      renderPeople();
    })();
  </script>
</body>
</html>
"""


def generate_standalone_gallery_html(people_data: Dict[str, Any], config_data: Dict[str, Any]) -> str:
    """Produces the complete standalone HTML string with inline data and reactive UI."""
    people_json_str = json.dumps(people_data, ensure_ascii=False)
    config_json_str = json.dumps(config_data, ensure_ascii=False)

    title = config_data.get("title", "Event Gallery")
    subtitle = config_data.get("subtitle", "Photos grouped by person")
    accent = config_data.get("accent", "#3b82f6")
    footer = config_data.get("footer", "Published with PhotoSorter")

    return (
        HTML_TEMPLATE.replace("__TITLE__", title)
        .replace("__SUBTITLE__", subtitle)
        .replace("__ACCENT__", accent)
        .replace("__FOOTER__", footer)
        .replace("__PEOPLE_JSON__", people_json_str)
        .replace("__CONFIG_JSON__", config_json_str)
    )
