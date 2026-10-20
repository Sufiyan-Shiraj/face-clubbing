"""Generates a zero-dependency, single-file standalone HTML gallery (BUILD_PLAN / SPEC).

This HTML file embeds people.json and config.json inline, allowing it to be opened
directly via double-click (file:// protocol) in any browser without CORS errors,
while loading local images from faces/ and thumbs/ relative paths.
"""

import base64
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
      scrollbar-width: thin;
      scrollbar-color: var(--border-color) transparent;
    }

    /* WebKit Custom Scrollbar */
    ::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }

    ::-webkit-scrollbar-track {
      background: transparent;
    }

    ::-webkit-scrollbar-thumb {
      background: var(--border-color);
      border-radius: 9999px;
      border: 2px solid transparent;
      background-clip: content-box;
      transition: background-color 0.15s ease;
    }

    ::-webkit-scrollbar-thumb:hover {
      background: var(--color-accent);
      background-clip: content-box;
    }

    ::-webkit-scrollbar-thumb:active {
      background: var(--color-accent);
    }

    ::-webkit-scrollbar-corner {
      background: transparent;
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

    /* Brand Badge & Header Elements */
    .brand-container {
      display: flex;
      align-items: center;
      gap: 0.85rem;
      flex-wrap: wrap;
    }

    .catlog-brand-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      cursor: default;
      user-select: none;
      text-decoration: none;
    }

    .catlog-icon-box {
      width: 38px;
      height: 38px;
      border-radius: 10px;
      border: 2px solid var(--border-color);
      box-shadow: 2px 2px 0 var(--shadow-color);
      background: var(--bg-card);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      overflow: hidden;
    }

    .catlog-icon-box img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }

    .catlog-brand-text {
      display: flex;
      flex-direction: column;
      justify-content: center;
      line-height: 1;
    }

    .catlog-brand-name {
      font-family: 'Outfit', 'Archivo Black', 'Inter', sans-serif;
      font-size: 1.15rem;
      font-weight: 900;
      color: var(--text-main);
      letter-spacing: -0.02em;
      text-shadow: 1.5px 1.5px 0 var(--color-accent);
      line-height: 1;
    }

    .catlog-brand-sub {
      font-size: 8px;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-top: 3px;
    }

    .brand-divider {
      width: 2px;
      height: 28px;
      background: var(--border-color);
      margin: 0 0.15rem;
    }

    @media (max-width: 640px) {
      .brand-divider {
        display: none;
      }
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
      <div class="brand-container">
        <div class="catlog-brand-badge" title="CatLog — Who was at the event?">
          <div class="catlog-icon-box">
            <img src="__CATLOG_ICON_DATA__" alt="CatLog" />
          </div>
          <div class="catlog-brand-text">
            <span class="catlog-brand-name">CatLog</span>
            <span class="catlog-brand-sub">WHO WAS AT THE EVENT?</span>
          </div>
        </div>

        <div class="brand-divider"></div>

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
    <div style="max-width: 1400px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap;">
      <div style="display: flex; align-items: center; gap: 0.75rem;">
        <img src="__MASCOT_POSE6_DATA__" class="mascot-footer" alt="CatLog Mascot" onerror="this.style.display='none'" style="width: 32px; height: 32px; object-fit: contain;" />
        <p style="margin: 0;">__FOOTER__</p>
      </div>
      <div style="display: flex; align-items: center; gap: 0.75rem;">
        <span class="badge-chip" style="font-size: 0.75rem; padding: 0.3rem 0.65rem; border-radius: 9999px; border: 1.5px solid var(--border-color); background: var(--bg-main); color: var(--text-muted); font-family: 'JetBrains Mono', monospace; font-weight: 700;">CatLog v0.1.0</span>
      </div>
    </div>
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
          peopleGrid.innerHTML = `
            <div style="grid-column: 1/-1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem 1rem; text-align: center;">
              <img src="__MASCOT_POSE2_DATA__" alt="Searching" onerror="this.style.display='none'" style="width: 96px; height: 96px; object-fit: contain; margin-bottom: 0.75rem;" />
              <p style="color: var(--text-muted); font-size: 0.95rem; font-family: 'JetBrains Mono', monospace; font-weight: 600;">No people match your search.</p>
            </div>
          `;
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
          photosGrid.innerHTML = `
            <div style="grid-column: 1/-1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem 1rem; text-align: center;">
              <img src="__MASCOT_POSE2_DATA__" alt="Searching" onerror="this.style.display='none'" style="width: 96px; height: 96px; object-fit: contain; margin-bottom: 0.75rem;" />
              <p style="color: var(--text-muted); font-size: 0.95rem; font-family: 'JetBrains Mono', monospace; font-weight: 600;">No photos match your search.</p>
            </div>
          `;
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
          unrecGrid.innerHTML = `
            <div style="grid-column: 1/-1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem 1rem; text-align: center;">
              <img src="__MASCOT_POSE6_DATA__" alt="All Clear" onerror="this.style.display='none'" style="width: 96px; height: 96px; object-fit: contain; margin-bottom: 0.75rem;" />
              <p style="color: var(--text-muted); font-size: 0.95rem; font-family: 'JetBrains Mono', monospace; font-weight: 600;">No unrecognized faces — all faces organized!</p>
            </div>
          `;
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

        // Size Guard: detect mobile vs desktop
        const isMobile = (function() {
          if (navigator.deviceMemory && navigator.deviceMemory <= 4) return true;
          if (/android|iphone|ipad|ipod|mobile/i.test(navigator.userAgent || '')) return true;
          return false;
        })();
        const thresholdBytes = isMobile ? 150 * 1024 * 1024 : 500 * 1024 * 1024;
        const estimatedBytes = photoIds.length * 2.5 * 1024 * 1024;
        if (estimatedBytes > thresholdBytes) {
          const proceed = confirm(`Large Archive Size Warning:\nEstimated download size is ~${Math.round(estimatedBytes / (1024 * 1024))} MB (>${Math.round(thresholdBytes / (1024 * 1024))} MB threshold${isMobile ? ' on mobile' : ''}).\nPackaging very large archives in browser memory can cause memory pressure.\n\nClick OK to proceed with download, or Cancel.`);
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
                '',
                'FORMAT NOTE:',
                'Drive HEIC photos download as JPEG (full pixel dimensions preserved); JPEGs are byte-identical.',
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
              zip.file('DOWNLOAD_NOTES.txt', notesLines.join(String.fromCharCode(10)));
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

      // Enforce organizer configured export theme (no viewer toggle or localStorage override)
      const exportTheme = config.theme || '__THEME__' || 't-dark';
      document.body.classList.remove('t-dark', 't-paper', 't-navy');
      document.body.classList.add(exportTheme);

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


CATLOG_ICON_DATA_URI = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAYAAADimHc4AAA3F0lEQVR42u19d7RfVZX/Z59zy7fX1/PSQwIkgYTelBesIAICCQgiNkBRBIdRVEaS6KCMZVBELHRRkBeQJgihJKGXAAnpvef19u333nPO/v1xv8kw/nBGFNRZK3utrKz1XvJ99+6zzy6f/dn7Aftkn+yTfbJP9sk+2Sf7ZJ/sk32yT/bJPtkn+2Sf7JN9sk/2ybsu9E5/IDPTggULBACsWrWK58+fb/7ZlcBz5wp0dAh09PGCBUBjYyN1dHRoIuL/MyfJzMTcKd/i64I7//+v/zPI3LlzxVs985u//39G+Xsf+tJTM88++NOjn37k1vf98dbvjXvzQfyzvFBoLLxX8Z03zp1U2fbUFdz78v1rnr/nD4sf/OVVP5x7YcOfvtu7IdY78TJExDf9x2eSx773xH/zlTlvbHtra9lj0ISxpbUv3b+oNNBzPREtBIDOzk45Z84c/Q9TfmenJCINQH/10s9M+dqFH/t6PJmZvXlnb3zL9tXIZlI4bMb0j1TK1fMf/e0PP0Ik1vLcuYL+GV1peIWZHrjxG8396x9bWt79En/1y5/msz724eDsM07yz51zsula+yTzyAreueyh3z5w49xJe93Su2xZ/5OLvPbS8zOvPn7rD7a+9kBxzYsP8MWfOdOMam2subb0EjHHP+7IGZXSrpf4pYV3PLdo7lyLmf85XVFn3bdveXnBwt0bn+P9J4+vOLYMWppyKh6LqFw2FRx/zKHeL677TsDlVdyz5vGh733ryxf+6f//ez0nACx99KbTvN3Prh/c/DRfefkFesLYNi/iWEEyHlGZVEynk1ENQH/j8gu9SvfrfO3VXz2tbmzWP5nfD1/quYd/8en1r9zPJ7z3yJoUUGef/mHV2pxXjbmUymeTqiGXVpl0Qn/+M2d5b7z4kPF6X+f1z9997wM3fqP57/FiixaFn3/j3M/mVj1z561mYBk/cNd1fMDkcbVUIhZkUjHVkEuqXDqhUomoyqbjKh6L6Gn7T/Qeu+8m80jnz+4JD3H2/2Qsov7n76R8gJiZrp87O7Hl1d9v77ztRyafTQUtTVk9elSzamrIqAljW1VzY1Y15FK6KZ9W40a36pkHTw3uv/O6GvNW7l37xNbOn80//k1Konde+YssAHjw9u8eve6l+zauX3o/X3Lhx/1MOhEkYq7KpGIqn02qVDKmkvGIaswlVS6TDDKpuI66tvrBd77G3Le054avn5P9HwIyCQKkAObOhXg33uPPWtXjv7/h/F0rHuYT3nOY39SQ1W3NeTV2dItqacio9tZGNWZUk8pnkqqpIRM05FIqHnVVKhFV3/7GxV6paynvWvOkd913L//S3rjwDj78nizn2Qeu/5TX+2plycO/5mkHTq5l0gmdSydUPptSqWRMpZJRlU3HVCoRU040pvKZRNCYS6mI66izzzjRD3pf5lcfu/GjewL4nyq//sAHATjsr3nOv+raLF4MA4CmTR7/6S27B3n5yvWoVqvsuDZsS7IRNtu2RK1ag+s6rJSCUgrJZBxEhKu+d4P1uS99S9m2JWfNOu6nD9/5n98nIoMwPaR3QvlEpFc9e9eVo0aPv/X6G3/nXPK1f/f7enstKYgDpWBJAceyIJjhBYAQwGGjCIFmMsZACOCFl14zpWIZrY25DwIAGhvf/GySGWDg0POOjLxyzWmxlw9ssh6MRDC6bkj0rmU+AHD/Td+esvWNP/pfuuAc3ZRPq1EtDWr82FGqIZfW08bntBOJqXg8oVob0yqXSahcJqEasimVTSdUUz6t41FHH3vkDLXs+fu9ws5X+LmHb7oJADF3yr/lJuy5nVte7vw2l5bzVV+/xG/MZ4JRLXmVSsZUNh1XiZirUomYamlIaWFHVHvOVU9enFa17+fUhEZXxeLxIJOKqWw65d97x0945bMLljHP/W+Z2+zZkERAe9ZasPuqFPMN8dLzF0XYssRV9DZS/Ld9A+Z1dAgAOGrmASclXMt+ZOGSwPMDCAL6BgvIRxnPXOTi9rNtakkBfUUNWwowM1zXRTTiIggUJxJxrF67kT538TetVWs21GbOmPrZTS/fdyvRHL140SL5ZgvaE3N47lzBc+eKMP3d8/d/KWXRornWrFnz1ROd117ZNnbCty69/Pv+zbf9jowxVPN8OLYNIgHLsuBYhO4hn48aAzzzRZdOGC/IdYCTprmo1jQijo1ytSqefu5lzmTTU675xvZxRMR1AxSdnTDMOODsGc4pra5R6FfO/Wt1VSnzcN0vmXcrnxYA4O189tFnH7uDU4mo19yQUe0teeVEE+qCWY2abxqv+fo21XN1kz7vyLSGHdVNDRnVkEvqbDqhsumESidjujGX1pl0Qjfm0vrRe39V27zsMV73zJ3XAMDKlZ3OokV/WQ5ORFjZ2ekAwA3/ccVn+tY9zt/9t4trY9pbg4ZsUiXjUZVNxVVjPq0y6YRqbkgpWFF14rSYHrkmq/knGdXz742af5LT93w2q6QdUQ2ZhLItqU77yPu8oOdFXvPkLee86YZJApBL2r9c+bUM8/fj5UWfT7Lryv8gALMB+a5UwvWq13T+6Cu5qhccds/9j4EZggEYY2CMoeMnRmFqBkNFjYgJ+NefTtJB7VVc9XCZIhGbBTGUZliWBWlJLlerFE0l8akvfMO64FNn+t/+9mVXPP+HX22YNm3OzeFPnY9DAfvazqsz49r3S3d37Y6s3jEkTug4yDz3wvrS9lceGrjilueL0+bM8X/8nYuPO+esj/7yrvueCO5Y8JjlezUYwyACIhEXliXBpoKe4QCnTbfo7vNsCCFQKgUUkwF7FYOD22yko4AXKGQzSQwMDqO/v4BA2McAuLNvMQQzAiKMO/0g+9z98jqoVRCZ94S/wfP0t3kuBM3/y63/bebgCwQAPev9s2ZakvIrV6xRlhSktCY2xDFXYEazgigHiGoNbdsoFRX/6wmGJmZtfPI3HmBZcCRBa81BEMB1HASBzyOFCp5/8VW5Yf1OM2Hi+Ov61i5s2NlfbhvTnJka+N7oYs3k3YQbr/QVrBmHtFNXT4GPOnK6d9KHjx26/Gq7t1Qsr/B8r2PZ8lXWD39yY1AuV6lYKrOUEsyMmudB+MBwlXHCBMZdH7eYA4KvFAk40DAoaQtjk8DYDLBuwIbRGi+/upzWbO3B5NGNhwLAzxYvNmcJcDLuXnThTMQdR1V/8JSyl2wMLpOEMs2HfDvu5+0dwOIwCxiuejMRl9i0o1trY6xE1OWRkocJLTZPaJKktA3LqpE0PoaGDYQn8LFDLNzjgM64xeeaJkQcCZICgoh9XyGdSuDJp5fSv1/9U/znd/81sviZl6/ZuqsfheEBFEtVrN+8E0GgDAC2LYF8LiOaG3Px3v7B+Mzpk9v3nzTukKn7T8SlV/5Id/f0SykFXNchY5iJCGCDoi8wtUHRvZ+OgPyANUdga0KQsGCUhZitYQuFSWnGyj6GJQWEELR163a0Z6OTPnjUUbnHlywZZMSbT9yfLzh0jFDrt6joj1/me4jwyOlnQi5YAP3ugXEdHQwAsXhi2qNPPYee3n5EIy4AhqeBcSlG1Bbss4AkIlXUnI87EMRU6vbwoUmCf/3xCJ31Gw+WZBYC0KzJGMPZTBoN+SzWbtiMsz77Na7VPL+3u4e37NhNiXhc1DwfsYgDZsDzA2pqzHPN8/XQ8DDf2fkQDGCmTBonEomYyGYzXK1WIQRBmwAwDGWA5qhHd54T4TgzlIyCiMGJBCwmFsqDSMQAVcbkvAWzsR5JDdOip180J806NHfp5z40YeGLLw4KK7jgCzOsvJAIrlyih3YPqcuYQUT40/6BmD07TCb+3MG8XRjAAEAsYk2pFAoAGwIzPM+H8hVPzDsEKOiKBiwbQsRAroApldmWQN+wotMPFnyzitIFC2qUcAUrbdi2bZTKJZTKVQ4CjeGRAhzbtgZGihyPxWCYEYtGYIwBkUA8EcPg0BAAQjKZIK00EomoHBwcpmKpjGqtBiKgVvMhBUEIQqWq6IL3ZnlqcwBjCEG5hCJiiJLkSK1IpHwOalU4CYkJOSIdBFypMmLRCFm2rRsbG+3jjzmkBUDs9IPsizoOQHDPC8q+Z4X+liTsIoIE9ipZzJ4N+v290AsWvENpKANERPyjH30lunFrV2uhUoNhEDODAAZArSkAgQazIbIIgWUjqNagtSYSRI0xiXVdLl7rBqfjNitt6laqYTTDtiz09vWjf2AQu7t7YVsWhJSwpMSeYk5KATYMz1ektUGpVEEQBCiVqjCGuVgsszEGNc9HxLVhmMOAmnT4theqOPomCzevjEBEXDSLKhy/CqMNYAIIMCBttCQECOHzKBVg5ao1XC2XEM/lMwBGvXc0tY8UjH3VM/o5NuaG08/cq3wxG5BSwCxYAK0NZo5vsG5vz8ofA7DfqkCz3kYKBBBhWlQkJ44fnfzhL+6C0YZICAjBEJaFjAOgViXJFoZKHiutkGONiGuhJzD43uOab3mtSsUaOB0FXNcNs6fAh9IKfhDAtiSCQCGTSaNSrQEMRKIutLaRiMcQcR0IIah9VAsHgYbn1VCuVGns6FHYtmMXV4slZDNJuI6NWs1HOp1EqVSB0gaWFFi+o4IvbAVuGWPTD05u5OMmAqqvAqUlCQ4YJkEx14Jt+SAhEAQedu7uRU9BoXvVxkkA7vzZK+ra217TB6zpCb4sAOYFoNmA/L2AXmAAGEwfnbO+euZB1lmXHkfOMxsZ53fya5LNr8GwAKi3fwDz5hEAnnLIkfFkVERtwUxCkBAEMJMgRswCQUo2ZR9JyaCqj0jOwX0biL/6sMKmPo1kFJyJAtFYHNWaB0FANBpDreaBgPBrQpLnBWhvbUYqEYdj28hl0yhXqqh5NURcl6UUUErB8xWiEZe1YbLHjYHXFmB3dzeGRgrwfQXXdWHbFgBGtebBlYSYLfDqthqf+/sMzpwu8PWZDhqdMoqeQ65X44Tlk20J+IGCZVtwHQc93T1IJSKtAMy6Lv9fwAZEAIexWtUVv19rxr787Ol0/kVHy8iUBhFAqGLbVJm8ukl+cm23+fXs2eA3u6W3cQAA5gP3LlyS6DjuGEdpw1bdWm1JMMZQNCoYmlElB2lhSGejuOQRn2940UPMsdCQlNAMCCJWgSIpCMwM3/PJsGYhBEa3taAhn0M+l4UgwPc9gJm6evq4XPOhNaNUGQAzA2CkEjHE3BqIwOlkAtlMGtGoC9dxsbunF7t2d0NphUQ8DikUmA18ZZBwBQZ7duG2cg4Ll2v+5UdsHNNiyFeABWatFKQlEXEsBEpDBwEaW/IuAHRe9S0Hq+frs+6BBqC0wYR0wr703Bn06S8eYSUPzCofNteGB3Vkaa+073gtGOwt6zsYIFrwN7YkRzcknVw2K4WwjajX3H6gwIa5UgmAqkaOBPqqAuf9IcBjKz00ZSwIacEPFJTWiLoOKaUBIui6GxvV0ozmxjyy6TSYDZfKZerqHUJfoYpS1ePAqyLlaKRjkhIusdEaBoL6egSGKoYVbERdF20NSWrOpyAEMHZUK48Z1Yot23YgmYzR6rWb2bYtCDC0YVi2A/KL2FBknHKXxPUfMjj7IFBZAVISO44NpRRXhgtozkbhQEUAoLEDZtZ8aAAttm1fft6h4sJLjqDUjDGkoFlv3MHOw1sMHtqIN55c598GmLsAdFPo//XfdAD5XJuyJJjZIBaLhilotQoQwdMCiDLW9wicucDwyu6AsgkikuGLxKJRlCtVVGoeLBmipZlMiqceMAWZVBzlUgU7d+/Gzt4RdPcX0JBkOmqcw8ePNTRzVIRHpwj5lOCoYJCUKAYKlaJGf8Wilf0GT28N8PTmPjy9tQsNmSRPHtuCRCKG/caPoVKlikQiTuVymYmIpJTMxiBgIGoDShv69MMWHBNgco7hKSKLAlbGYPLEMVi7rQ+NqYgIs/F5Jp3+ceaQxspTPzrROWDmGK1QNVi0VlqdK3Xp8U384Ka+4BYAi4mgBQDNEG9VoL09FwQgkaRq38CwX6nW7EKhCNuxIQWBQQgCxs4hog//VvP2QYXmlA1PMbQ28AIFRg2RiIugGMDzAxx1+Ew05jIoFEsYHBzCpu1d2N41hANHSfrXM+I4bbLGxAwDbAAOCKwBaTEMAbqKqEWMBkHjyMdhbQqfmibQVXH4qd1J+tmSIp57dQ2Nasnz5HFtHIvHcMzhM2nlmnW0dfsuTqUS0ACxUtBEsCUhAsOf/SPTGVPArgQ0MwQJ7O7uR2M2iYMmNFUAwLWl8ZWJjZ3iTp7UCNzwtLEe3mBWPLJe3QFj7gWwWdZTQ8OwdGj15m+qA+r6R+/2rvJJZxzrtbU0uYHSKhp1iY2BLQwWbgZufY15Z4GRigBVX8OyJIgNJBFqXgDfD2AYOGzGdLQ0NXBf/wBVymW8snorslHgJ2fG6NMzDScjAeD7BCVpbT/wRrfG2n5g24ihoaqBlAJZ26AtqXlSi4VDW2yakgy4NVrFuRNrOG1iFA9uifGVDxbp+WUbcdDkNm5ubOT9J09CPp+nFavWsOu6bFkWaWPgK12HVYnvWA1EBEPIMEtPp5Jobm5C73CxAAA//dnP7Ysuumj3HcvUnMc38Ym7BvSDgH6UgEAI4PQzIOuB1rw54/mbmHF76Cdf/cwpyQsvOn/NHx5/btTX5v1EZdIJ4QdBCClocMR1oP0aSctGEPhgBsViEfi+4iAIIKRF7zn6UPh+AK9W476BQazZ0EWnHmzjP0+OYEKjYngeBjwH965QuH8NsHSnwYhvUaCIhRTkOhaMMfB8BRCxLRgpR9HhrYbPPtzGRyaA8lECSHKvb9Olf/DxuxcrPH3/MZTLZXjCuNFY+vpK2rB5K8eiEdJKgwSx1gaRiAtiRtUPwvRGaeRyOfXIgl+4+RjmtRx0ynxetMiiWbP2KvbN1l5X+juPBRERExF+cMuDpQ+fcmJf++jRo4wxzAwOCyWNmCOFCjyORKPwfB/SsgBmLpdrSCZiVK3WcPIHT4CE4R2DQ+gfGMb6bd2Yf3IcVx0HAFVUKwK/WQZc+0wNa/otOLaFVMxGS8JmrRSiERckBHzfhxAREBE8L0AtUPx8r40/3lnCtMaA537IxUmTFOWNh7tOc/jAnI2rHtnCU6eMgyUlGvNZLhTLGBgcYse2wPXCi0BgIWBboQ4NA+1tTdSYT6NcGNoBAIvfVMhKguF6b3L2meAFC/YWt+Ydx4KMMRIgg5Gjtzy68LkZti1ZqdAQhCB4gWYwQytNtmUxAFSrHqQkjBSK2H/yBBRHRrhYLKOnbwCbdvTRz89K4vNHaKCisGpQ4OIHA3p6i+RE1EFTmsi2bB7V1kJSCG5qyBMD9XaiZBKSunr7MFIowfN9jIyMIJ6PokcnMfu2QZx7iMBPP+pwtOjhWx0WxZ0oLr9/OxMbtLW2Yr/xY1CpVlCt1mDbEgyCZUv4vgqrb62htQ4RA+NjuLdvc537uhfz0WzPAYIyGM8tWIBhAiDqN+I9DGtJ/XKEYMLf2BF79dVfCSLw+nUbX00k42hraUY0EoHWGsxMlpQwzAiUYiIgCBQLQah5AU2aOB6TJ03ASKGIoeEhbNrWg2vPTOLzhzNQ8fiPW8Dv/YXHz++w0Zx1qL0lSxPGjOF0KokJY9rR1JAP3Zzncc3zQEKgWq1yIhajcaPb0JjLkOcrsh0XiYjEAZNa8btVDp9ws0d9sMivaPzLkYQr3ufQyvW7MDwyAmlJTBw3lkAEoznEjCpVAMx+oAAQEvEYzjr9RBopePr+R57vJSJ+5plbLADIxq2v3Ha2ffdvz0n+4VOH2aumt1r3MsRFmrG/YWAJoKSAlgSePRvyrfRtvT3+5wIDQErwYbZtcSQaocGhYdiOA0HE8VgUhWIRzEC16kNpRY5jw7IsvOfow7Bh4xYuFApYs3EXLu5I0GWHakbFx/1bbJx5ew2pVAITswlubGykUU0NPFwoYqRQQLlS5UApsDFIxOOo1mrs+Qq+CivdgcFhWrN+MyaNHwshBHoHBlGqBdh/bB4rt/XxB35Voyc/46BBCv73D1lYukPj6TXb6NhDIpxIxLilqQHdPX2wAFiWhSBQe4Ov53l46dWVfMJxh4ovfOGsWzLCfHg4M64g6DFYtmybnCUcPV7pc6aJ1sESTn++yz79mc3w3+hWy5buVov6i/wEgFcXLMDQW+lV/uVIdIc1fvzJeudr9/5i7IQJ5170le+olWs2yGQiiiAIIQGtFaRlMVEY3B3HQbFYxqEzphGBMTg4hLVbujB9lMRdZxBso+m53QKn3FpDMhmH71VJGWBMWzMq1RoEEfoGhpHJpABmCCEhJIGEQKVaRTIWQ//QMDZu2U7jxrSzDHvPlE2nEShF/YMjGNWUwbquKi3dGeCcmYKCso8T9ndx26s+FasBNeWziEVc6urth6mDg0RERAi7ZeUqbNsWXV1d5sQPv3/M6LEth9713S/+bmUv89XX/PCl21+tyaU7uT3QIjspBcwYzf4HpjBmj8eYj05zjjt4nPPJbFx+Ugc4ctiX64wxvfWbwH/xAXBnpxx/8sn6uYd+fun4KVOuvPhfrvbvf/hJmYzHUKv5sG2bbdsipRR8PyAQwbIsaK05EY/RqLZmFEtl7OruxVChhLs+GcOkrEJ3gfCRX9dQMS5JwfTFz5+P8z9+Kv3+D0+S0RqpZALbd3WhtbkJliVDV2cMjGHE4zGMFEtYv3kbjR/TjmgkAqU0lFYgAqKRCADQUKGM1oYEXt9aQaAYHznAoqxrqOYZPLTK53w6AjcShQoUSuVymDYTgYiglELEtdHXN0DrN22jlas3+Z+9YM7k93Z8KJdsO+DhWq3mXflvVz2+tlffct8qs/KxLYhvGaQJSSKnPW2hpZkqh40S+mOjTfpjk3nawm2Y3FM0v+6cDbFg9V94AJ2dnXL6WXP0c/f++PAjjjnq7h9df4e+/sa7RDqVIK01HNeBlJKCIIBt2RB16JjBqFRqNHH8GDQ35NDT00drN3XjE0dEcMkhBuwpXP6YxlNbHURkQN+dfwW+8a0vYvoh0/GHB59AxLHRPzSCoeER5HMZSsfj0Mzwaj4S8bCiXrdxK40b0w4BsGXbkFKCjQEzw/MDyqRS8DwflaqPZMLFk+sr+PABDloijP2bJd3xuoeKsTCqqYECpWhgcBgkBAjMQhA5tg1jGNKyIITAxs07RLFQUUccddjRF338o8vzY6auveSSD7tLX9lYIeIV3UXz2+e26fs712DklS5urVaoOR+FlY4Yv69C8rqX9R/KHj/auxpyWz1L+l+D8KpVq5gZ1oRJ43/27EvLrdvuvJ9TiRhprREEqt7TDaC1gR8EYGYIIaCVQTwaoXQygUKxhOFimV0X9OUjiQT7eKVH4rblIJtqdOpHT8QXLzoLeqSENUtXYMOmbahUqxgeKYABqlaqrLQGmNGQyyBQGqvWbsSY9lbEoxEmKeH7AbRWcCyLpZQAA57noSGfBQhwHQuGHHznKQ9KCLSmDX/iEJu6+ooYHh7iRDzOiUQcbExYjYWHCC8IoJRCtVqDVj7+48c3iZdfX2Na21t+/MsrZqevyx0ZfOuqucIw5Ny5EFJgRbGqv/HA6uDgz9wXnHHi7cFDVz5p8M3Fptw9In9BBCx5U4oq/jeS0/z5883Lj/zyzJbR4w6/7Tf3BcawDJSC1hqRiENDwyPwfB/RiAuud2eEFPCDALlcDqlUAoViEdt7RqhjPGFmTgEK+OmLAQVGIp9N41++8AkYpSEjLr7/k1uwddsOLFu1HsbsgTHq2LxSKFerWL5qHfbfbzzSyTg7loVUIo5oxIFt2WCAgkCRlAJExGBGYy6LStVHS0MST23U2NATEISFjx1gsQmqqHo+4rEokok4/CCAMWG88TwfEdehoG5YUkpEXFf88ua7gkjUHfu+k0/7Ms2fbzpCrpSePz8MI8cDliCUJenfr+4KTvnu4mDG3cuDmQR/jWEQ/tID6OiYpwGI/SdP+pcnF7/If3ziGQwNj1A0EkU8FkUQKLYsC1II1DwPzIBWeo8Voakxx7Wah1KxSEYpPnOaBRGxsGmY6I/rGZI9TJo0EYfMOAAiGcM99y7Ebb+5F5865zR88/LPEwlBjuOgWKqQlIJcx8HzS5ejf2CQVq3dSEuXr8LKdRuwYfM2lCtVlCsV8oMAiXgU8XiMpRSIRFzE47GQBkOMim/h92sAKIODsowpTQJ9wxX4vo9MKgEhJACw1hqOY8HzAq5ngTBsIKXglWs2yCcWv2KyDU0XXzv3/MwJJ8xSbyKImSWAMgzS/3Ur1grCxnpHjP+iNLSzPkmy+pk7jmQhDrn5N7/XWnOI4LMBSMAYhusIMBPKVQ8EkBAEISWiEReubaNarcLTQMLRdOToCOD7/OxOgcGSooZMDF3dPfz6G2tpcHgYF375Ssw+/UTcetP3gaiDl15djqeWvIBkPIpqzcNrb6ymQrHEEdfhweERAMDA4DAAYNuOXdSYzwEASUns+5ocx0Ik4sJxHE6n4qhUquREHX5ic42/caShVJz5qNFEd6wsYmJ7wIl4HIl4FMYwKRXeBMuSMGxCThETHMcCEcQDjz2rZh07s+WE4447lfn22xcvXiz/BPfh+q14s6H/5WhoY+MqAoBiJThrzaYu+cLSNzxtjEUU8rFHCkW4jo1AaSil2ZJE8XgcWmvUPA+xaLROhNLo7h/hKY2SJsUMAIElm3yQtNhxHHT39OGk2V9gpTWKpTIu+OQZhGga21avxqo1G+DYNhtjsGL1OnT19CERi0CbsBkkKEw7DTOCQHE04lJrSzP3DwwilRSo1jyMFIoAiIIggDEGFhmsHwDt9IjHZmyanvdh6i5mT5zxPA+u68LzPSitEYtEEagARIAUEuVKlZetWEWbtu7kUW1tswHc3tHRYf43MsPbqoQ7Oubp2bMhJ44fd8LqdZsxPFwQQhAS8QS0ZlhSMjODGYhFXQIIWitobcCGIYQgIQSVKxV4AdOEHCGaEghqTKv6ATfiwLYtTJ4wFlopMlqR6zhY9OxrWPbaclx02Tz0Dwwhk0mhf3AI3b19iEVd6HqWQ0QAQiYzc2ip23d1oVKpUEiVAbuuw7lMFulUEvlclm3HQSYZRX+FefcIIHTAE9IMQtjEl1KEN5sZSoVwhCXD9NcYDusdz4Pn+RgplMTTzy8lCPvIG7739SwRmb+G2S3+3NwsEfG3P3PtaClp0lPPvMhKaZJSolgKcRfLsohNeNP8QIEZ8P0wBw/p3xYHQQApBTEztyfDf1sIgO6igWsLKM2IR6OYMXUK2luaEHFt+vHPbuEPfPAsfvGlVzmVTLDvB2Q0w5IWiAQIxEIIgEEhTyDM2es9Yu7u6+dkMhG2LBnQRrPv+8zMcB0nbEkpRlfZEMhCzjVgaPb8AFIIWFboWplNmM1phZrnoc6wIwaDAZRLZby2aquKJlMNx84YMy0kDi4Q78gBLJg6lQCgt+ZO2dk9FFu1eqMiAvm+ghAC6VQCRIA2eq81WpaENgZBoEAgUkqR0pqlEMzaICMZ2tOo1gyqfjhVYgyHhZMQ3NLciAMmjcfYUS1kjIFt23WMKQTNmZmN0cxgMIMNGzbMe92t1gaWZaGntx+9fQOIx2IQQsCSErYVfpYlBRujCSSoZgggjUjcZkFAEARkjCEpJAAGg6B16DnCZ1GwLMlEAoIInuejWqnoYqmI5lGjDniL+YG//gD2+H/DZj+SEuVy2QAUklxdG+VyGUoZuK4T8nq0RhAE5Hk+tGGQCC0SIFSqHmA0WYIgLQlICZIEQQRjdIi9qADVmsfRWBRjR7dhv/FjKJWIke/7CAI/9HMEEqG1U4j+hngH1w9BCIEgUBg/th01z0MQBBAhU42FoL2K3JOFiJDlSNrXAARIEBvDbAxD1LEUpTSICI5thS7WmLpxWPADHzt2daNvoAjXjY1/R+eEO9ABYD5mHDi5baDkoW9wGI5jh5CzF6Dm+SElJAj7y4KAbDaDxoYY9fYPQGsT3gop628ruKBBUAqOLRC1iYscHlLN8/+rsR9qkyxLYsyoFm7IZbF9Vxd5vg/btsAk6pgQURh/Qq5SSA8xcBwL2Uwaw8MFjBRLyGcz5JfKsCwLDJBSipUK+yUNjQnABg+Wy2QYcMJKmg0bGEaIRQmBUkURUGEAsAQQjUZgjECY7QkaGi4iSiof9gkWvzMHsOeDnn11VaS1pRlTp0zEqrUbwQzWWhMDNH36gTho2n48Y9oUmjn9AEzZbywaWxv4zI9fhnsffBxBoKhcqcKSkqRtYXdBMQBko6DmBFFPX4CI7bLWGkREgohL5SqIwI7jUKA0RSIu9t9vPHYn4tjZ1c1BEIRDFqCQpigIzKEr830fY8e0UzwWZRUobN/VhWjEhW3b8AMfQRCwUhoGoKgr0BYLGKUA3RUC6hT2kGbPqNV8fOfKS+i8T56J119+FSvXbqKV67Zi7YYtWL9uI2lt4Dg2r12/mQUHaG8ZbdcTFwbmv3M3YPKYFiSaWpHJpKC1RjwWpf7BESz49Y/51I9/jABJUEWMdA1i+co1uO2uB2nZirUcjdgUqACWJSkWcZgI2DZiUPJtuEpheiPhlZ0+29kYKtUapVMJ9rzQh4f+XDMRUalcYSkEMpkU0ukkdnX10PBwgQFAGwMdaAghEHFdcmwbjbkMAt+HYYN8Nouh4QKydSSViMjzPHiKuT1rod0JY8vrfQZk2RxxXVSqVRitIaTApm27MDDQh/fPOhqnfuKM0FubAAvvX4jTzr2UPd+HbVmUSqUwOFJQ4ezcYnpHVxU0NOQKzyxdgUcWPo1MOgHP9wEClr72BhkQL3xiCS1buR4bN23D8EgBShmWBESiLgdKhe3CQCEZtbFhwKOhksboDPHRzUw3K0VaKy5VKnvTVjDzHr+rwwAe8koNMYgwelQrAMLg0DDi8RhlUkkk6lVuqVTmWCRChVI5DL6WgOd7CJQmx3bY88sgMJcqPo6cIpHJSNRGAizdDTiOpEgkgqGRIleqNUQjDm79ze/x6zvvQ2tLE8aNa8ch0yfze487nLZt62LHlvB8g0kTx6KhsQFb128c3uM73hkXtDj8oKVvrNrSnG/ApPGjaWdXD1zHRiIWxTX/eRMrEwY/15EcklgNpZNxJFMJjIwUoJRGteZREAScT8dp4/YSXtllMDoKOmGKRH6JRrHik2MJDBdLSCbiKBZD5REhBPmUIm0MKtVaHSq2kcukMW7MKEQjEfi+zyDC9h270NSQJ83MgdbQvg/fD5BNpzEwNMwtTQ3kBwqGGTAap091CJ6H9cMSy7sCtLUkUanWuFSuQGkNwUT5XAaDg8PYubsHu7t6+NnnX8V1v7yLASCViIKZSSvFUYtRVsGWvzYIv2UW1Dd1KgPA1PGtG6ZPbMXY9hahVJhyMjPS6QQacilkUjH2fA0SEp/8+Gl4YXEnLXv2PkokEhQECqVKFa0tTYg4NoMJD60zgCSMzwMfm2phpFBlx7a4t38QSmlOJuPgelXbXWdJDw2PwLYsjGsfhbHtrZzLpgEAg0PDXCiW0Ns/CGOYXMdGoVSGMQa1mgfDYX0ihcDg0DCMVihVFfZvJnrfOAFo8INrAniBRCoR2ROzyPMVzjv7NGxauwQ/uvqrmDJpLAAgHnWQTSeQjEdJSknMjMaGnBwp1dC9Y+s6AOjrW83vyAHMnj3bAMCDv39ozWDZ6zv5pPdZETfC2vCe/i9K5Qq8QOGz58/BK4vuxu13Xs9N+QzP+971GCkUYVsWhodH4HsBSdtBOhXBgxsZWwsAqgpfmikQtQ0qVY+01ugbGMTA4DANDA5RsViieDSKpoY8jxszCq3NjaSZoZTG0HCBqtXaXvBvZKSATDrJXqA4hKQ1SAiwMdBGw7YsFEtlEBilUhVXnJBEyva4uwDc+oZBPBmB7bgMMCqVCkdcGy+/tgKvv/I6vvLNL2DVSw/ipz+4ktpaW6lUrpAQxARAa2OOOeJgC0F1RMYzK0O9dZp35ACIiJlZXHzNnUMjIyPLxrW3cKVWNQAgZUjIjcfjeH7hXbjptp/TqLZmXHXF1Zg88yRc/6s7WRJg26Ff7h8cBBGhOZ/hwTLjxmUAbIGDGzW+cpRFQyMVWGTQ09sPz/N4THsrt7U1I5NOQkqJcqXGQyMFJgLXPJ+IgHKlSrYdWrwUAslEHOVyBZaUeypWaB0G6GrNQ9S1sbOngPcd6NLZ+3kMX+F3q5k2DzLaG9OwbQcjxTJ7fgDHtrBi5VrM+sin+NSPfA7LVm7giy//HNYv+wOOPmImypUaAq1NNBoxRx46nZOZ3CvnXHBlDzOLv2bD1p8tnRfPmycA4JXXV9w/tr2NPvDeo9iSEswm9KUMdPUO0XU/+AEOOOIU+s73f45KpUypRHRvjq6MQbFUQSadRjKRQCoV5Rte0dg4IADN+LfjBY6daPPu3hLymQRqvo/BoREEvo+a51O5UoXWGtoYFIplUkqxMcxCEKtAoVyuIJ9No1qtAQCqnodS3Q0RUUg3sQTKlQCNKYlfnuIgonzsHJa45nmFfC6NXC7HSisMDA5DCgEShGQizomYiwcfeYqPft/ZOGf2xXjg0WdRroR9aikEHXPkIXzMETNpxfLlD9XjpnhHVxV0zJunAaAlmVyQjDkDZ576QdvzA9YmJDB5Xg0nnfE5vvRr1/BA/wA35NIQJKDDl2cGkIhF0T84hMGhYViWxOiWBgxXNF/6uAakBdcAv53j0Ji8oF19RUgw9fQP0nChtNeajWGoQO2ptuEHAYgINc+D41hk2zYqNa9eaGnscZOlShVgjaoXUC3wcdd5CUx0fYYhuuwJg54y8ZjWBmjD6OsfRB23CvvK9QyuIZeGlIS77vkjnzbnC7xm7QbEYy5s2+ZPnDbLrhZGCvc/vnRB/QDMO760b8/Ohc3PL/hhLJu//L0fOd/rHxyywkCpISSxFBJERNoYEEJMRUgJQcTGGCitkU4mMX7saJQrVSoURrB1Zx++90EXX+8g+D6wpWzhpNtrvLkXGNWcIGVCN5hNp+C6LupQMgVac+AHcF0HhWIJDbksACAIsXtSWrPvBwiUgiMJA4UqGRXg7k8kcOo4H1Cav/8C6IrHA4wf3cjpVBpMwOatO2B0CCg6jgNjdL1KD+BYFiBC6EQbA4Bw4JRJ+tHO652gOPTTxoNP+TJzpyT667aAif9lKoaZmTavf/1aAVP43PlnWbl8HoZBMqR/URAoBPXRolgsBiEkvxmqllJiaKRApXKF4rEoYrE4MskIX/mk4ttfYzgEjHEDfuaCCE6cKmlXTwFVT8GxJAaHh9HV24uRQhGeH3CIVkrUajW4jk1CCtR8H5Wqh2KpzOVyFZKYYAzt7C6iJa6x8IIkTm2rArWAb1/BuOJxxY3ZOGfSaUgp0N3TG1p/ODgOpVXYSdEMKQjSsuDUwThjDFzH5ovOP112dfeMPP70M9cwM82bt+qv3q74P7Ii5i9ZwlOnTpUfPffLI0fO3N//wPuO+/Dy5SvV+s3bRdgpYti2RVprDpQmrRQJKchoQ0prqnNsIKWk/sEhpJJJTiZiiMWiVK6U6N6VCqOzFg4fA9iewrkzBTWlbby0rYZdfTWCEBR1LAIzajUPQeCDKBxj0lrD8zzyPQ9gA2YDL9DoK/pU82r4TEeafjM7jmluCWCDG5cTXfiwRj4bx+j2VmijMVwoYWBwaG/gBgOOY4HrNQ5CakoIewOoVD28771HmUs/f669Y8uWqz766W89Nm/qVDnrS18y7+beUOLOTkFz5nDXGw8sdFP5933oYxf4q9dtsSwp2LIsGDZstKE6ckzGGNY6hJSJAFNHES3L4nGjR0FaFrxaDbt7+mhwpIorjrfx7RMEHALgA7s8wq9XE+54zcfaXsPMErZrQ8Ig6jpg1gAIhkF+YFDzFWA0MjHGh/a3cel7oji6wQOUYj8A/u0pph88HyCbjvKY9ja4bgTFYpE2bd3Bjm1DSAFjDLTWiEWj8AMflrT28GFJG8MEojHtreqhO69zIo71TOuawqwFAGbPmWPoz/A+/+YbsNcTHXggzVu8mBc+eNdTrS0tZ8+YdkBm4aLnValUIQo5XpRKxqGUhtYGUkrEYmEbrz7Kyq7rQimNkUKR4rEoItEIkokEgRUeW13Fkh2C928QGJ0GUqToPWMJ5x0ewfETLBqTIYpZBoIV+b5HbDRZFFBSBpjYAHxwioVL3uPiuydEcOE0g9GRGgDCC9sNfeJ+pt+t1BjdmkdTYwPAhCDwsWX7rnpXDSBBJIgQcV14ngcpZH0sNxwAY8MoVWrmsovPs4+eMbn/t7+555RjL7tyoPPAA4mWLOG/y+bczs7Zcs6cBfrnV1927Ps/MOvRLTt2xy+87NtB/+CQdGwbQRD8VwOUGVIICCHDXmr9OgsSpLVmAJgyaTzZtsWVmgcV+LRm026WgukTB1n44hESh7cLBpigDWARo8YoKWDIM1QzAhYYcQKycQnbJYA0QzPga3qlT+Lnywi/fT1gnwX2a29ANpeFUhrDwyPY3d0HIfb2B8K2JsLhwfDmWnun5JmZ06m4+dQnzqTjDz/QtDUkT5p6wqef5M5OSe/A+k16u8uQZs2ar95YfOcHxo0f9cCTzyyLfvdHN3orVq21UqnwBkQiUYwUChBEEELAsCGjDQshwgo1pK+DBKG9rRUN+Syq1Rpq1SoNDhe4u69Its3omCBx6hSJo9sYo1NAY9xmsAbIABaH/ANBBB9c8IEtI4wXdht6cAPhiY2Kg0BQU0McjbksR6IRMAN9/YPoGxgMB7B1OPTt2g78QBHCCToObzDBsiyqVGvI53Lqok/Plt+49JNy09q1Z+9//Pl379ED/hG7o/f88EV3/PtRkw89orNQ9EZ/8zvXek8ueckCGzi2hWotpI+LOlFeax1aVRjnwmpaKfL9AMlkgluaGimViHOpXEbge1Qs17hrsEzaC9hxDI3NAOOzksdkCJm4hEthGlwICDtHDG0cMLxlGPA8gGyHmjMRbsxn4LgumIFKtYqevn6Uy1VEXBfaaLiOU8/3w+upjYGpj94KIVCp1rD/5EnBDf/xtci49ubq6hWrzv7geVc8uGjRImvWm6Zj/iHLu/fkvfdcf/nYmYcffXs+nz/+lrv/qP/zZ7frYqkk6wQ57G3ZgkEiDBa2lPD8YO8hsGG2LEGJRJIz6STisSgsacPzqqhWKihVPRop+1yq+mSMCf1bGBMZlgTAlIpHOB13kYpHYFkWhLAAAmo1D4NDwyiVK2F2UO+6aGMQi0Uo8APey7Aggus4KJZK0Brm/LNP5nnf/JJjfH/z9vXrPnHcnK+88E5a/t+8Pf1NPlCuffaOebnGtq89ueQl5+77HvMfeeJZMsYI13VgScl7uJa2bcH3w1ghpYCu+9iQhcCwpKBIJMKJeAzJRMhsiOzpO6uAtDbwfJ+lEOQ6DmtjiNmwkBZUvULXWqNULqNYKqNQLIPCn8WWbZOqzxiQEDDakGUJgIiNDiHvWCTCU/Ybb847+xTn3DM/hOHens6bb7nzy9+7+aGed0P5f/P6+rlz54p58+YxEfHvfvLNo2adcMz3bWm9Z8HCl3DvA48Fz764FBHHEb7SkAKQ0qpvsAqLNBWO/0AKAQC0B/cJewLhwIdj22TbNsdj0b3B3bbtkDBb88JJe99HtVaD7ysoHepIawPHlgAJaKWYSJC0JEyd4xONOKj5AXzPh2E2+08az+d//DTnM2efhGjEWr/sjVVzj/7oxb97t/dd0zu1RXdPKb7w7us+Pv2A8V9raW2b8bv7HsP1t9xr1q3foIrFEuVyWapUqiGtoR4jgkDBtiW0NqSUAQniN0/gh67M7N3QGRZ+ho3hcC2JNv9td5yUYfaljYYggOoUSoAhpaBSucquYyMScU0sFjPJREx+87LPWe9/z+Fg7W/v7+v9+Veuufanjz/+Rrm+r47fzd8j8A4uSp0rgHl7Htba/lLnR/sK1S/EY7GOWCxuX3fz3Vjywuvc09MbdPf2MxsmrTVFI45QSsNxbNi2BaU0EYGJCEJIGGP2xpEQF1L1vm34PSEIJnRjJOtEKqVCuovSeg+1hD1fmVjUxbFHzkRf/5A89cRZ8rgjD0ZrSx4TRjW+unbjtpu/96uf3rlgwasjf88t7/RuLMp+84MXVz0w1U7kTh4uVU7evKP7kPGj22I/u/l3iDo2dvcO4bHFL+h8Lm2Ghku8afM2mDojzbIsCnyfDQO2JShcCgjYlmAA5Ku9ls8iJDYAALKZFEciLkqlCjKpuGhubBDjxrbLXDqBkz9wLMa2N2HH7j599GEzVhaLQ4+MjFT+ePD7z3tuD38z3Ik9x7zF9qv/GwfwZvgCs2ebN1/f6vpHJnYPlA63HfeoUc25Q3oHhyYMlkxTJhmxN27vxqbN21CplBGLxqCVh1dWbIJtW9i6dRssy8FwsYR8Ng3HtsBGI5NKQmkN3/MgbQeHzpiKZMxFc2MW+cZWQNWQSydMKpUaiLtyAxu9bEd39ysxKV4bffQ5K/conYhgzN0S+O/P+3/5AP67a1rcIfAWv5PlknM/nPrG5Z9vdx1rTM/ASHsqGR81qr2lySvX0tWal8hk0+lCqRpbvmK1td/ECbJQDUTEYlMoV824tgZIKX2tdFAuF4JYPFOKRCLlaqm/nw16INze4ZHSrmJ5eOfzTz+x66L5d/W/1XLvvr4+njNnzp+d4/0/fwB/mjV1dEAAHfh7/5IcZqaQw78YHR0wRPP5H6X0f9gBvPXs8TwCptLixatoDyUMHR2MBQuA2bP5f8pC9tDB582bR1OnTqXZs2dj8eLF1FFn6HT09TFmr+I3JQf7ZJ/sk32yT/bJPtkn+2Sf7JN9sk/2yT75h8r/AwTSRUIpGXfWAAAAAElFTkSuQmCC"


def generate_standalone_gallery_html(people_data: Dict[str, Any], config_data: Dict[str, Any]) -> str:
    """Produces the complete standalone HTML string with inline data and reactive UI."""
    people_json_str = json.dumps(people_data, ensure_ascii=False)
    config_json_str = json.dumps(config_data, ensure_ascii=False)

    title = config_data.get("title", "Event Gallery")
    subtitle = config_data.get("subtitle", "Photos grouped by person")
    theme = config_data.get("theme", "t-dark")
    if theme not in ("t-dark", "t-paper", "t-navy"):
        theme = "t-dark"

    theme_folder = "navy" if theme == "t-navy" else ("paper" if theme == "t-paper" else "dark")
    mascot_dir = Path(__file__).resolve().parent.parent.parent / "viewer" / "public" / "mascot" / theme_folder
    pose2_uri = ""
    pose6_uri = ""
    if mascot_dir.exists():
        p2_path = mascot_dir / "pose2.png"
        p6_path = mascot_dir / "pose6.png"
        if p2_path.exists():
            pose2_uri = "data:image/png;base64," + base64.b64encode(p2_path.read_bytes()).decode("ascii")
        if p6_path.exists():
            pose6_uri = "data:image/png;base64," + base64.b64encode(p6_path.read_bytes()).decode("ascii")

    footer = config_data.get("footer", "Published with CatLog — Who was at the event?")
    default_accent = "#d94b4f" if theme == "t-paper" else "#fa7175"
    accent = config_data.get("accent") or default_accent

    return (
        HTML_TEMPLATE.replace("__TITLE__", title)
        .replace("__SUBTITLE__", subtitle)
        .replace("__ACCENT__", accent)
        .replace("__FOOTER__", footer)
        .replace("__THEME__", theme)
        .replace("__THEME_FOLDER__", theme_folder)
        .replace("__CATLOG_ICON_DATA__", CATLOG_ICON_DATA_URI)
        .replace("__MASCOT_POSE2_DATA__", pose2_uri)
        .replace("__MASCOT_POSE6_DATA__", pose6_uri)
        .replace("__PEOPLE_JSON__", people_json_str)
        .replace("__CONFIG_JSON__", config_json_str)
    )
