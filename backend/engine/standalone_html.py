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
  <title>__TITLE__ — CatLog Gallery</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
  <style>
    :root, body.t-dark {
      --color-accent: __ACCENT__;
      --bg-main: #121316;
      --bg-card: #18191e;
      --bg-card-hover: #1f2127;
      --border-color: #272930;
      --text-main: #f4f4f7;
      --text-muted: #8b8f9e;
      --shadow-color: #0b0c0e;
      --font-family: 'Outfit', 'Inter', system-ui, -apple-system, sans-serif;
    }
    body.t-paper {
      --color-accent: __ACCENT__;
      --color-accent-text: #ffffff;
      --bg-main: #f4ede2;
      --bg-card: #fffdfa;
      --bg-card-hover: #ede7dc;
      --border-color: #2b2b2b;
      --text-main: #121316;
      --text-muted: #424652;
      --shadow-color: #2b2b2b;
      --font-family: 'Outfit', 'Inter', system-ui, sans-serif;
    }
    body.t-navy {
      --color-accent: __ACCENT__;
      --bg-main: #0c1322;
      --bg-card: #121c32;
      --bg-card-hover: #182542;
      --border-color: #1e2e50;
      --text-main: #f0f4fc;
      --text-muted: #8294b5;
      --shadow-color: #050810;
      --font-family: 'Outfit', 'Inter', system-ui, sans-serif;
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
      transition: background-color 0.2s ease, color 0.2s ease;
    }

    .btn-tactile {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      padding: 0.45rem 0.9rem;
      border-radius: 0.6rem;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      font-size: 0.8rem;
      border: 2px solid var(--border-color);
      background: var(--bg-card);
      color: var(--text-main);
      box-shadow: 2px 2px 0 var(--shadow-color);
      cursor: pointer;
      transition: all 0.15s ease;
      text-decoration: none;
    }
    .btn-tactile:hover {
      transform: translate(-1px, -1px);
      box-shadow: 3px 3px 0 var(--shadow-color);
    }
    .btn-tactile:active {
      transform: translate(1px, 1px);
      box-shadow: 1px 1px 0 var(--shadow-color);
    }
    .btn-accent {
      background: var(--color-accent);
      color: #ffffff;
      border-color: var(--border-color);
    }
    .btn-download-person {
      margin-top: 0.6rem;
      width: 100%;
      padding: 0.45rem 0.75rem;
      border-radius: 0.6rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      font-weight: 700;
      border: 2px solid var(--border-color);
      background: var(--color-accent);
      color: #fff;
      cursor: pointer;
      box-shadow: 2px 2px 0 var(--shadow-color);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.35rem;
      transition: all 0.15s ease;
    }
    .btn-download-person:hover {
      filter: brightness(1.08);
      transform: translate(-1px, -1px);
      box-shadow: 3px 3px 0 var(--shadow-color);
    }
    .btn-download-person:active {
      transform: translate(1px, 1px);
      box-shadow: 1px 1px 0 var(--shadow-color);
    }
    /* Header */
    header {
      position: sticky;
      top: 0;
      z-index: 40;
      background: var(--bg-card);
      border-bottom: 2px solid var(--border-color);
      box-shadow: 0 2px 0 var(--shadow-color);
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
      font-weight: 800;
      letter-spacing: -0.02em;
      color: var(--text-main);
    }

    .brand-title p {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 0.15rem;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
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
      background: var(--bg-card);
      border: 2px solid var(--border-color);
      color: var(--text-main);
      padding: 0.5rem 1rem 0.5rem 2.25rem;
      border-radius: 9999px;
      font-size: 0.875rem;
      font-family: 'JetBrains Mono', monospace;
      outline: none;
      width: 240px;
      box-shadow: 2px 2px 0 var(--shadow-color);
      transition: all 0.2s;
    }

    .search-box input::placeholder {
      color: var(--text-muted);
    }

    .search-box input:focus {
      border-color: var(--color-accent);
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
      background: var(--bg-card);
      padding: 0.25rem;
      border-radius: 9999px;
      border: 2px solid var(--border-color);
      box-shadow: 2px 2px 0 var(--shadow-color);
    }

    .nav-tab {
      padding: 0.4rem 0.9rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
      color: var(--text-muted);
      background: transparent;
      border: none;
      cursor: pointer;
      transition: all 0.2s;
    }

    .nav-tab.active {
      background: var(--color-accent);
      color: #ffffff;
      box-shadow: 1px 1px 0 var(--shadow-color);
    }

    /* Theme Switcher */
    .theme-switcher {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      padding: 0.25rem;
      border-radius: 9999px;
      border: 2px solid var(--border-color);
      background: var(--bg-card);
      box-shadow: 2px 2px 0 var(--shadow-color);
    }

    .theme-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.35rem 0.65rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
      color: var(--text-muted);
      background: transparent;
      border: none;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .theme-btn:hover {
      color: var(--text-main);
    }

    .theme-btn.active {
      background: var(--color-accent);
      color: #ffffff;
      box-shadow: 1px 1px 0 var(--shadow-color);
    }

    .theme-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      display: inline-block;
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
      border-bottom: 2px solid var(--border-color);
      font-size: 0.875rem;
      font-family: 'JetBrains Mono', monospace;
      color: var(--text-muted);
      font-weight: 600;
    }

    .stats-bar strong {
      color: var(--text-main);
      font-family: 'JetBrains Mono', monospace;
      font-weight: 800;
    }

    /* People Grid */
    .people-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 1.5rem;
    }

    .person-card {
      background: var(--bg-card);
      border: 2px solid var(--border-color);
      border-radius: 1rem;
      box-shadow: 3px 3px 0 var(--shadow-color);
      overflow: hidden;
      cursor: pointer;
      transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
      display: flex;
      flex-direction: column;
    }

    .person-card:hover {
      transform: translate(-2px, -2px);
      box-shadow: 5px 5px 0 var(--shadow-color);
      border-color: var(--color-accent);
      background: var(--bg-card-hover);
    }

    .avatar-wrapper {
      position: relative;
      width: 100%;
      aspect-ratio: 1;
      background: var(--bg-card);
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
      background: var(--bg-card);
      border: 1.5px solid var(--border-color);
      color: var(--text-main);
      font-size: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      padding: 0.25rem 0.6rem;
      border-radius: 6px;
      box-shadow: 1.5px 1.5px 0 var(--shadow-color);
    }

    .card-info {
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .person-label {
      font-weight: 700;
      font-size: 1rem;
      font-family: 'Outfit', sans-serif;
      color: var(--text-main);
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
      position: relative;
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .photo-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 8px 20px rgba(0,0,0,0.6);
      border-color: var(--color-accent);
    }

    .drive-badge {
      position: absolute;
      top: 8px;
      right: 8px;
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(6px);
      -webkit-backdrop-filter: blur(6px);
      color: #38bdf8;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 6px;
      border: 1px solid rgba(56, 189, 248, 0.4);
      display: inline-flex;
      align-items: center;
      gap: 4px;
      text-decoration: none;
      z-index: 5;
      transition: all 0.2s ease;
    }

    .drive-badge:hover {
      background: #0284c7;
      color: #ffffff;
      border-color: #38bdf8;
      transform: scale(1.05);
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
      background: var(--bg-main);
      border: 2px solid var(--border-color);
      color: var(--text-main);
      border-radius: 1.25rem;
      width: 100%;
      max-width: 1100px;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 6px 6px 0 var(--shadow-color);
    }

    .modal-header {
      padding: 1.25rem 1.5rem;
      border-bottom: 2px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: var(--bg-card);
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
      font-weight: 800;
      font-family: 'Outfit', sans-serif;
      color: var(--text-main);
    }

    .modal-title p {
      font-size: 0.8rem;
      font-family: 'JetBrains Mono', monospace;
      color: var(--text-muted);
      font-weight: 600;
    }

    .close-btn {
      background: var(--bg-card);
      border: 2px solid var(--border-color);
      color: var(--text-main);
      box-shadow: 1.5px 1.5px 0 var(--shadow-color);
      width: 2rem;
      height: 2rem;
      border-radius: 9999px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.25rem;
      transition: all 0.15s ease;
    }

    .close-btn:hover {
      transform: translate(-1px, -1px);
      box-shadow: 2.5px 2.5px 0 var(--shadow-color);
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
      background: var(--bg-card);
      cursor: pointer;
      position: relative;
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

    .unavailable-tile {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 1.5rem 1rem;
      text-align: center;
      background: var(--bg-card);
      border: 1.5px dashed var(--border-color);
      border-radius: 8px;
      min-height: 180px;
      width: 100%;
      box-sizing: border-box;
      gap: 0.5rem;
    }
    .unavailable-tile .tile-msg {
      font-size: 0.82rem;
      color: var(--text-muted);
      font-weight: 500;
    }
    .unavailable-tile .drive-btn {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: #0284c7;
      color: #ffffff;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.78rem;
      font-weight: 600;
      text-decoration: none;
      transition: background 0.15s;
    }
    .unavailable-tile .drive-btn:hover {
      background: #0369a1;
    }

    /* Footer */
    footer {
      border-top: 2px solid var(--border-color);
      padding: 1.75rem 1.5rem;
      text-align: center;
      color: var(--text-muted);
      background: var(--bg-card);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      font-weight: 600;
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
<body class="__THEME__">

  <!-- Top Header -->
  <header>
    <div class="header-container">
      <div style="display:flex; align-items:center; gap:0.75rem;">
        <div style="width:38px; height:38px; border-radius:10px; border:2px solid var(--border-color); box-shadow:2px 2px 0 var(--shadow-color); background:var(--bg-card); display:flex; align-items:center; justify-content:center; flex-shrink:0;">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>
            <circle cx="12" cy="13" r="3"/>
          </svg>
        </div>
        <div class="brand-title">
          <h1 id="event-title">__TITLE__</h1>
          <p id="event-subtitle">__SUBTITLE__</p>
        </div>
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

        <div class="theme-switcher" role="radiogroup" aria-label="Theme selector">
          <button type="button" class="theme-btn" data-theme="t-dark" title="Dark tactile theme">
            <span class="theme-dot" style="background:#fa7175;"></span>
            <span>Dark</span>
          </button>
          <button type="button" class="theme-btn" data-theme="t-paper" title="Paper risograph theme">
            <span class="theme-dot" style="background:#d94b4f;"></span>
            <span>Paper</span>
          </button>
          <button type="button" class="theme-btn" data-theme="t-navy" title="Navy midnight theme">
            <span class="theme-dot" style="background:#38bdf8;"></span>
            <span>Navy</span>
          </button>
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
        <div style="display: flex; align-items: center; gap: 0.75rem;">
          <button id="modal-download-btn" class="btn-download-person" style="padding: 0.45rem 0.85rem; font-size: 0.8rem;" title="Download all photos for this person as ZIP">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span>Download All (ZIP)</span>
          </button>
          <button class="close-btn" id="modal-close-btn">&times;</button>
        </div>
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
      <a class="lightbox-btn" id="lightbox-drive-btn" target="_blank" rel="noopener noreferrer" style="display:none; text-decoration:none; background: #0284c7;">Open in Drive ↗</a>
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

      window.handleImageError = function(imgEl, driveUrl) {
        imgEl.style.display = 'none';
        const parent = imgEl.parentElement;
        if (!parent || parent.querySelector('.unavailable-tile')) return;
        const tile = document.createElement('div');
        tile.className = 'unavailable-tile';
        tile.setAttribute('data-testid', 'unavailable-drive-tile');
        tile.innerHTML = `
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#a1a1aa" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          <span class="tile-msg">Photo unavailable locally</span>
          ${driveUrl ? `<a href="${driveUrl}" target="_blank" rel="noopener noreferrer" class="drive-btn" onclick="event.stopPropagation();">unavailable - open in Drive ↗</a>` : `<span class="tile-msg">Image unavailable</span>`}
        `;
        parent.appendChild(tile);
      };

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
          peopleGrid.innerHTML = '<p style="color: var(--text-muted); grid-column: 1/-1; text-align: center; padding: 3rem;">No people match your search.</p>';
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
              <button class="btn-download-person" data-person-id="${person.id}" title="Download all ${photoIds.length} photos for ${name}" onclick="event.stopPropagation(); window.downloadPerson('${person.id}')">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                <span>Download all (${photoIds.length})</span>
              </button>
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
          photosGrid.innerHTML = '<p style="color: var(--text-muted); grid-column: 1/-1; text-align: center; padding: 3rem;">No photos match your search.</p>';
          return;
        }

        filtered.forEach(([pid, photo], idx) => {
          const card = document.createElement('div');
          card.className = 'photo-card';
          const driveLink = photo.drive_url || photo.share_url || (photo.download && photo.download.startsWith('http') ? photo.download : (photo.drive_file_id ? 'https://drive.google.com/file/d/' + photo.drive_file_id + '/view' : null));
          card.innerHTML = `
            <div style="position: relative; width: 100%;">
              <img src="${photo.thumb}" alt="${photo.name}" loading="lazy" onerror="window.handleImageError(this, '${driveLink || ''}')" />
              ${driveLink ? `
                <a href="${driveLink}" target="_blank" rel="noopener noreferrer" class="drive-badge" title="Open photo in Google Drive" onclick="event.stopPropagation();">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right:2px;"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                  Drive ↗
                </a>` : ''}
            </div>
            <div class="photo-card-info">
              <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 130px;">${photo.name}</span>
              ${driveLink ? `
                <a href="${driveLink}" target="_blank" rel="noopener noreferrer" style="color: #38bdf8; font-size: 0.75rem; text-decoration: none; font-weight: 500;" onclick="event.stopPropagation();">
                  View full ↗
                </a>
              ` : `<span>${photo.width}x${photo.height}</span>`}
            </div>
          `;
          card.addEventListener('click', () => {
            if (driveLink) {
              window.open(driveLink, '_blank');
            } else {
              activeLightboxList = filtered.map(([_, p]) => ({ thumb: p.thumb, driveLink: p.drive_url || p.share_url || p.download }));
              activeLightboxIndex = idx;
              openLightbox();
            }
          });
          photosGrid.appendChild(card);
        });
      }

      // Render Unrecognized Faces
      function renderUnrecognized() {
        unrecGrid.innerHTML = '';
        const unrecFaces = (data.unrecognized && data.unrecognized.faces) || [];
        if (unrecFaces.length === 0) {
          unrecGrid.innerHTML = '<p style="color: var(--text-muted); grid-column: 1/-1; text-align: center; padding: 3rem;">No unrecognized faces.</p>';
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

        const modalDlBtn = document.getElementById('modal-download-btn');
        if (modalDlBtn) {
          modalDlBtn.setAttribute('data-person-id', person.id);
          modalDlBtn.onclick = (e) => {
            e.stopPropagation();
            window.downloadPerson(person.id);
          };
        }

        const personPhotoItems = [];
        photoIds.forEach((pid, idx) => {
          const pObj = data.photos[pid];
          if (pObj && pObj.thumb) {
            const driveLink = pObj.drive_url || pObj.share_url || (pObj.download && pObj.download.startsWith('http') ? pObj.download : (pObj.drive_file_id ? 'https://drive.google.com/file/d/' + pObj.drive_file_id + '/view' : null));
            personPhotoItems.push({ thumb: pObj.thumb, driveLink });
            const item = document.createElement('div');
            item.className = 'modal-photo-item';
            item.innerHTML = `
              <img src="${pObj.thumb}" alt="${pObj.name}" loading="lazy" onerror="window.handleImageError(this, '${driveLink || ''}')" />
              ${driveLink ? `
                <a href="${driveLink}" target="_blank" rel="noopener noreferrer" class="drive-badge" title="Open photo in Google Drive" onclick="event.stopPropagation();">
                  Drive ↗
                </a>` : ''}
            `;
            item.addEventListener('click', () => {
              if (driveLink) {
                window.open(driveLink, '_blank');
              } else {
                activeLightboxList = personPhotoItems;
                activeLightboxIndex = idx;
                openLightbox();
              }
            });
            modalGallery.appendChild(item);
          }
        });

        personModal.classList.add('open');
      }

      // Per-person photo download handler with ZIP packaging (Local & Google Drive)
      window.downloadPerson = async function(personId) {
        const person = (data.people || []).find(p => p.id === personId);
        if (!person) return;
        const photoIds = person.photo_ids || person.photos || [];
        if (!photoIds.length) return;
        const name = person.label || ('person_' + person.id.replace(/^p0*/, ''));
        const cleanBase = name.toLowerCase().replace(/[^a-z0-9_-]/g, '_').replace(/^_+|_+$/g, '') || 'person';

        const btn = document.querySelector(`button[data-person-id="${person.id}"]`);
        const origContent = btn ? btn.innerHTML : null;
        if (btn) btn.disabled = true;

        const setBtnText = (t) => {
          if (btn) {
            btn.innerHTML = `
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              <span>${t}</span>
            `;
          }
        };

        // Size Guard: warn if total estimated size exceeds 500 MB
        const estimatedBytes = photoIds.length * 2.5 * 1024 * 1024;
        if (estimatedBytes > 500 * 1024 * 1024) {
          const proceed = confirm(`Large Archive Size Warning:\nEstimated download size is ~${Math.round(estimatedBytes / (1024 * 1024))} MB (>500 MB).\nPackaging very large archives in browser memory can cause memory pressure.\n\nClick OK to proceed with download, or Cancel.`);
          if (!proceed) {
            if (btn && origContent) {
              btn.innerHTML = origContent;
              btn.disabled = false;
            }
            return;
          }
        }

        function getDriveFileId(photo) {
          if (!photo) return null;
          let driveId = photo.drive_file_id;
          if (!driveId) {
            const raw = (photo.download_url || photo.download || photo.drive_url || photo.share_url || '');
            const m = raw.match(/[/]d[/]([a-zA-Z0-9_-]{15,})/) || raw.match(/[?&]id=([a-zA-Z0-9_-]{15,})/);
            if (m) driveId = m[1];
          }
          return driveId || null;
        }

        function getFullResolutionPhotoUrl(photo) {
          if (!photo) return null;
          const driveId = getDriveFileId(photo);
          if (driveId) {
            return 'https://lh3.googleusercontent.com/d/' + driveId + '=s0';
          }
          return photo.download || photo.download_url || photo.thumb;
        }
        const getOriginalPhotoUrl = getFullResolutionPhotoUrl;

        // 1. If backend server is active, prefer direct server zip streaming
        const serverZipUrl = '/api/people/' + encodeURIComponent(person.id) + '/download-zip';
        let serverHandled = false;
        try {
          const testResp = await fetch(serverZipUrl, { method: 'HEAD' });
          if (testResp.ok) {
            setBtnText('Downloading...');
            const a = document.createElement('a');
            a.href = serverZipUrl;
            a.download = `${cleanBase}_photos.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            serverHandled = true;
          }
        } catch (_) {
          serverHandled = false;
        }

        if (serverHandled) {
          if (btn) {
            btn.innerHTML = `
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              <span>Downloaded!</span>
            `;
            setTimeout(() => {
              if (btn && origContent) {
                btn.innerHTML = origContent;
                btn.disabled = false;
              }
            }, 2500);
          }
          return;
        }

        // 2. Client-side ZIP generation with JSZip
        const getJSZip = async () => {
          if (typeof window.JSZip !== 'undefined') return window.JSZip;
          return new Promise((resolve) => {
            const s = document.createElement('script');
            s.src = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
            s.onload = () => resolve(window.JSZip || null);
            s.onerror = () => {
              const s2 = document.createElement('script');
              s2.src = 'https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js';
              s2.onload = () => resolve(window.JSZip || null);
              s2.onerror = () => resolve(null);
              document.head.appendChild(s2);
            };
            document.head.appendChild(s);
          });
        };

        try {
          const JSZipLib = await getJSZip();
          if (JSZipLib) {
            setBtnText(`Packing (0/${photoIds.length})...`);
            const zip = new JSZipLib();
            let packed = 0;
            let fullResCount = 0;
            const fallbackItems = [];
            const failedItems = [];

            for (let i = 0; i < photoIds.length; i++) {
              const pid = photoIds[i];
              const photo = data.photos[pid];
              if (!photo) continue;
              const pad = String(i + 1).padStart(3, '0');
              const ext = photo.name ? (photo.name.split('.').pop() || 'jpg') : 'jpg';
              const filename = `${cleanBase}_${pad}.${ext}`;

              const primaryUrl = getFullResolutionPhotoUrl(photo);
              let blob = null;

              if (primaryUrl) {
                try {
                  const resp = await fetch(primaryUrl);
                  if (resp.ok) {
                    blob = await resp.blob();
                    fullResCount++;
                  }
                } catch (e) {
                  console.warn('Full resolution fetch failed for', primaryUrl, e);
                }
              }

              // Fallback attempt: Documented Drive download link
              const driveId = getDriveFileId(photo);
              if (!blob && driveId) {
                const docDriveUrl = 'https://drive.google.com/uc?id=' + driveId + '&export=download';
                try {
                  const dResp = await fetch(docDriveUrl);
                  if (dResp.ok) {
                    blob = await dResp.blob();
                    fullResCount++;
                  }
                } catch (de) {
                  console.warn('Documented Drive link fetch failed:', de);
                }
              }

              // Fallback to thumbnail if full resolution failed
              if (!blob && photo.thumb && photo.thumb !== primaryUrl) {
                try {
                  const tResp = await fetch(photo.thumb);
                  if (tResp.ok) {
                    blob = await tResp.blob();
                    fallbackItems.push({
                      filename: filename,
                      originalName: photo.name || filename,
                      reason: 'Full resolution endpoint unavailable; packaged thumbnail resolution'
                    });
                  }
                } catch (te) {
                  console.warn('Thumbnail fallback failed for', photo.thumb, te);
                }
              }

              if (blob) {
                zip.file(filename, blob);
                packed++;
                setBtnText(`Packing (${packed}/${photoIds.length})...`);
              } else {
                failedItems.push({
                  filename: filename,
                  originalName: photo.name || filename,
                  error: 'Failed to fetch image from all sources'
                });
              }
            }

            // Include DOWNLOAD_NOTES.txt if any fallbacks or failures occurred
            if (fallbackItems.length > 0 || failedItems.length > 0) {
              const notesLines = [
                '================================================================================',
                'CATLOG DOWNLOAD NOTES & QUALITY REPORT',
                '================================================================================',
                'Person / Cluster : ' + (person.label || person.id),
                'Generated At     : ' + new Date().toISOString(),
                'Total In Cluster : ' + photoIds.length,
                'Full Resolution  : ' + fullResCount,
                'Thumbnail Fallback : ' + fallbackItems.length,
                'Failed Downloads   : ' + failedItems.length,
                '--------------------------------------------------------------------------------'
              ];
              if (fallbackItems.length > 0) {
                notesLines.push('THUMBNAIL FALLBACKS (Reduced resolution):');
                fallbackItems.forEach(item => {
                  notesLines.push(' - ' + item.filename + ' (' + item.originalName + '): ' + item.reason);
                });
                notesLines.push('--------------------------------------------------------------------------------');
              }
              if (failedItems.length > 0) {
                notesLines.push('FAILED DOWNLOADS:');
                failedItems.forEach(item => {
                  notesLines.push(' - ' + item.filename + ' (' + item.originalName + '): ' + item.error);
                });
                notesLines.push('--------------------------------------------------------------------------------');
              }
              zip.file('DOWNLOAD_NOTES.txt', notesLines.join('\n'));
            }

            if (packed > 0) {
              setBtnText('Generating zip...');
              const content = await zip.generateAsync({ type: 'blob' });
              const a = document.createElement('a');
              a.href = URL.createObjectURL(content);
              a.download = `${cleanBase}_photos.zip`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              setTimeout(() => URL.revokeObjectURL(a.href), 2000);

              if (btn) {
                const label = fallbackItems.length > 0
                  ? `Downloaded (${fallbackItems.length} thumbs)`
                  : 'Downloaded!';
                btn.innerHTML = `
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  <span>${label}</span>
                `;
                if (fallbackItems.length > 0) {
                  alert(`Download notice: ${fallbackItems.length} photo(s) fell back to thumbnail resolution (CDN was unavailable or throttled). A DOWNLOAD_NOTES.txt file was added to your ZIP archive.`);
                }
                setTimeout(() => {
                  if (btn && origContent) {
                    btn.innerHTML = origContent;
                    btn.disabled = false;
                  }
                }, 3000);
              }
              return;
            }
          }
        } catch (zipErr) {
          console.warn('JSZip packing failed, using sequential fallback:', zipErr);
        }

        // 3. Fallback: sequential download
        let count = 0;
        photoIds.forEach((pid, i) => {
          const photo = data.photos[pid];
          if (!photo) return;
          count++;
          const pad = String(count).padStart(3, '0');
          const ext = photo.name ? (photo.name.split('.').pop() || 'jpg') : 'jpg';
          const filename = `${cleanBase}_${pad}.${ext}`;
          const url = getOriginalPhotoUrl(photo) || photo.thumb;
          if (url) {
            setTimeout(() => {
              const a = document.createElement('a');
              a.href = url;
              a.download = filename;
              a.target = '_blank';
              a.rel = 'noopener noreferrer';
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
            }, i * 300);
          }
        });

        if (btn) {
          btn.innerHTML = `
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            <span>Downloaded!</span>
          `;
          setTimeout(() => {
            if (btn && origContent) {
              btn.innerHTML = origContent;
              btn.disabled = false;
            }
          }, 2500);
        }
      };

      // Lightbox Functions
      const lightboxDriveBtn = document.getElementById('lightbox-drive-btn');
      function openLightbox() {
        if (!activeLightboxList.length) return;
        updateLightbox();
        lightbox.classList.add('open');
      }

      function updateLightbox() {
        const item = activeLightboxList[activeLightboxIndex];
        const src = typeof item === 'string' ? item : item.thumb;
        const driveLink = typeof item === 'object' ? item.driveLink : null;
        lightboxImg.src = src;
        lightboxImg.onerror = function() {
          if (driveLink && lightboxDriveBtn) {
            lightboxDriveBtn.style.display = 'inline-block';
            lightboxDriveBtn.textContent = 'unavailable - open in Drive ↗';
          }
        };
        lightboxCounter.textContent = `${activeLightboxIndex + 1} / ${activeLightboxList.length}`;
        if (lightboxDriveBtn) {
          if (driveLink) {
            lightboxDriveBtn.href = driveLink;
            lightboxDriveBtn.style.display = 'inline-block';
          } else {
            lightboxDriveBtn.style.display = 'none';
          }
        }
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

      // Apply configured export theme & interactive switcher
      function applyTheme(themeName) {
        if (!themeName || !['t-dark', 't-paper', 't-navy'].includes(themeName)) {
          themeName = 't-dark';
        }
        document.body.classList.remove('t-dark', 't-paper', 't-navy');
        document.body.classList.add(themeName);
        document.querySelectorAll('.theme-btn').forEach(btn => {
          btn.classList.toggle('active', btn.dataset.theme === themeName);
        });
        try { localStorage.setItem('catlog-viewer-theme', themeName); } catch (e) {}
      }

      document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          applyTheme(btn.dataset.theme);
        });
      });

      // Apply initial theme from saved preference or config
      let initTheme = config.theme || 't-dark';
      try {
        const saved = localStorage.getItem('catlog-viewer-theme');
        if (saved && ['t-dark', 't-paper', 't-navy'].includes(saved)) {
          initTheme = saved;
        }
      } catch (e) {}
      applyTheme(initTheme);

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
    theme = config_data.get("theme", "t-dark")
    if theme not in ("t-dark", "t-paper", "t-navy"):
        theme = "t-dark"

    footer = config_data.get("footer", "Published with CatLog — Who was at the event?")
    default_accent = "#d94b4f" if theme == "t-paper" else "#fa7175"
    accent = config_data.get("accent") or default_accent

    return (
        HTML_TEMPLATE.replace("__TITLE__", title)
        .replace("__SUBTITLE__", subtitle)
        .replace("__ACCENT__", accent)
        .replace("__FOOTER__", footer)
        .replace("__THEME__", theme)
        .replace("__PEOPLE_JSON__", people_json_str)
        .replace("__CONFIG_JSON__", config_json_str)
    )
