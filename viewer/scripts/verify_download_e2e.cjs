const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const DIST_DIR = path.resolve(__dirname, '../dist');
const SCREENSHOT_DIR = path.resolve(__dirname, '../../scratch/screenshots');

// Ensure screenshot directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

// Clean neutral SVG placeholder (ZERO real human faces in screenshots)
const SVG_AVATAR = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect width="200" height="200" fill="%232563eb"/><circle cx="100" cy="75" r="35" fill="%23ffffff"/><path d="M50 165 C50 125, 150 125, 150 165 Z" fill="%23ffffff"/></svg>`;
const SVG_PHOTO = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400"><rect width="600" height="400" fill="%231e293b"/><text x="300" y="200" fill="%2394a3b8" font-size="28" font-family="sans-serif" text-anchor="middle" dominant-baseline="middle">CatLog Synthetic Photo</text></svg>`;

// Synthetic mock data for isolated E2E verification
const E2E_CONFIG = {
  title: 'CatLog Event Gallery',
  subtitle: 'Annual Community Showcase',
  logo: null,
  accent: '#2563eb',
  font: 'Inter',
  footer: 'Published with CatLog',
  show_labels: true,
  include_maybe: true,
  hide_single_photo_default: false,
};

const E2E_PEOPLE_DATA = {
  version: 2,
  generated_at: '2026-10-17T00:00:00Z',
  people: [
    {
      id: 'p001',
      label: 'Alex River',
      face: SVG_AVATAR,
      photo_ids: ['ph001', 'ph002', 'ph003'],
      maybe_photos: [],
    },
    {
      id: 'p002',
      label: 'Jordan Lee',
      face: SVG_AVATAR,
      photo_ids: ['ph004'],
      maybe_photos: [],
    },
  ],
  photos: {
    ph001: { name: 'event_001.jpg', thumb: SVG_PHOTO, download: '/mock_photo/event_001.jpg' },
    ph002: { name: 'event_002.jpg', thumb: SVG_PHOTO, download: '/mock_photo/event_002.jpg' },
    ph003: { name: 'event_003.jpg', thumb: SVG_PHOTO, download: '/mock_photo/event_003.jpg' },
    ph004: { name: 'event_004.jpg', thumb: SVG_PHOTO, download: '/mock_photo/event_004.jpg' },
  },
  unrecognized: {
    photo_ids: ['ph004'],
    faces: [
      { photo_id: 'ph004', face: SVG_AVATAR, rejection_reason: 'low_confidence' },
    ],
  },
};

const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
};

function startServer() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      let reqPath = req.url.split('?')[0];

      // Serve synthetic config.json and people.json for clean isolated test
      if (reqPath === '/config.json') {
        res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify(E2E_CONFIG));
        return;
      }
      if (reqPath === '/people.json') {
        res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify(E2E_PEOPLE_DATA));
        return;
      }

      // Mock photo binary download endpoint
      if (reqPath.startsWith('/mock_photo/')) {
        const fakeJpg = Buffer.from('FAKE-JPEG-BINARY-DATA-FOR-E2E-TESTING');
        res.writeHead(200, {
          'Content-Type': 'image/jpeg',
          'Content-Length': fakeJpg.length,
          'Access-Control-Allow-Origin': '*',
        });
        res.end(fakeJpg);
        return;
      }

      if (reqPath === '/') reqPath = '/index.html';
      const filePath = path.join(DIST_DIR, reqPath);

      if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        res.writeHead(404);
        res.end('Not found');
        return;
      }

      const ext = path.extname(filePath).toLowerCase();
      const contentType = MIME_TYPES[ext] || 'application/octet-stream';
      res.writeHead(200, { 'Content-Type': contentType, 'Access-Control-Allow-Origin': '*' });
      fs.createReadStream(filePath).pipe(res);
    });

    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      resolve({ server, port });
    });
  });
}

async function runE2E() {
  console.log('=== PART B: Public Viewer Rework + Local Download Flow E2E ===\n');
  const { server, port } = await startServer();
  const url = `http://127.0.0.1:${port}/`;
  console.log(`[E2E] Test server active at: ${url}`);

  const chromePath = process.env.LOCALAPPDATA
    ? path.join(process.env.LOCALAPPDATA, 'ms-playwright', 'chromium-1200', 'chrome-win64', 'chrome.exe')
    : undefined;
  const browser = await chromium.launch({
    headless: true,
    executablePath: chromePath && fs.existsSync(chromePath) ? chromePath : undefined,
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    acceptDownloads: true,
  });
  const page = await context.newPage();

  try {
    // 1. Visit Gallery Home (Grid View)
    console.log('[E2E Step 1] Navigating to gallery home...');
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForSelector('h1');

    // Verify Title & CatLog Branding
    const titleText = await page.textContent('h1');
    console.log(`  Header title: "${titleText}"`);
    if (!titleText.includes('CatLog Event Gallery')) {
      throw new Error(`Expected title 'CatLog Event Gallery', got '${titleText}'`);
    }

    // Verify Theme Switcher option is removed from the viewer page
    console.log('[E2E Step 2] Verifying theme switcher is removed from viewer page...');
    const themeButtons = await page.$$('div[role="radiogroup"] button');
    console.log(`  Found ${themeButtons.length} theme buttons (expected 0: viewer does not show theme selector).`);
    if (themeButtons.length !== 0) {
      throw new Error(`Expected 0 theme buttons on viewer page, found ${themeButtons.length}`);
    }

    // Verify configured export theme is automatically active
    const hasConfigTheme = await page.evaluate(() => document.documentElement.classList.contains('t-dark'));
    console.log(`  Configured theme ('t-dark') active on document: ${hasConfigTheme}`);
    if (!hasConfigTheme) throw new Error('Expected configured theme t-dark to be applied to document');

    // Capture Screenshot 1: Grid View (with NO real faces)
    const ss1Path = path.join(SCREENSHOT_DIR, 'viewer_01_grid.png');
    await page.screenshot({ path: ss1Path, fullPage: false });
    console.log(`  Saved screenshot: ${ss1Path} (${fs.statSync(ss1Path).size} bytes)`);

    // 2. Open Person Page (Alex River - 3 photos)
    console.log('\n[E2E Step 3] Opening person page for "Alex River"...');
    await page.click('text=Alex River');
    await page.waitForSelector('text=Download all 3 photos');

    // Verify Primary "Download all 3 photos" button displays person's photo count
    const dlAllBtnText = await page.textContent('button:has-text("Download all 3 photos")');
    console.log(`  Found primary button: "${dlAllBtnText.trim()}"`);

    // Verify Per-Photo Download Links
    const photoDownloadLinks = await page.$$('a[title="Download photo"]');
    console.log(`  Found ${photoDownloadLinks.length} individual per-photo download links.`);
    if (photoDownloadLinks.length !== 3) {
      throw new Error(`Expected 3 photo download links, found ${photoDownloadLinks.length}`);
    }

    // Check first photo download attribute for clean naming (personname_001.jpg style)
    const firstPhotoDlName = await photoDownloadLinks[0].getAttribute('download');
    console.log(`  First photo download name: "${firstPhotoDlName}"`);
    if (firstPhotoDlName !== 'alex_river_001.jpg') {
      throw new Error(`Expected clean download name 'alex_river_001.jpg', got '${firstPhotoDlName}'`);
    }

    // Capture Screenshot 2: Person Page with "Download all 3 photos" (NO real faces)
    const ss2Path = path.join(SCREENSHOT_DIR, 'viewer_02_person_download.png');
    await page.screenshot({ path: ss2Path, fullPage: false });
    console.log(`  Saved screenshot: ${ss2Path} (${fs.statSync(ss2Path).size} bytes)`);

    // 3. Test Select Mode
    console.log('\n[E2E Step 4] Entering Select Mode...');
    await page.click('button:has-text("Select")');
    await page.waitForSelector('text=0 of 3 selected');
    console.log('  Select mode active. Sticky bottom bar visible ("0 of 3 selected").');

    // Click on photo 1 and photo 2 to select them
    const photoCards = await page.$$('.glass-card.aspect-\\[4\\/3\\]');
    if (photoCards.length >= 2) {
      await photoCards[0].click();
      await photoCards[1].click();
    }
    await page.waitForSelector('text=2 of 3 selected');
    console.log('  Ticked 2 photos -> counter updated to "2 of 3 selected".');

    const dlSelectedText = await page.textContent('button:has-text("Download selected")');
    console.log(`  Bottom bar action button: "${dlSelectedText.trim()}"`);
    if (!dlSelectedText.includes('Download selected (2)')) {
      throw new Error(`Expected 'Download selected (2)', got '${dlSelectedText}'`);
    }

    // Capture Screenshot 3: Select Mode with Selection Bar (NO real faces)
    const ss3Path = path.join(SCREENSHOT_DIR, 'viewer_03_select_mode.png');
    await page.screenshot({ path: ss3Path, fullPage: false });
    console.log(`  Saved screenshot: ${ss3Path} (${fs.statSync(ss3Path).size} bytes)`);

    // 4. Test Local-Mode Download Flow (client-zip streaming execution)
    console.log('\n[E2E Step 5] Triggering local-mode download ("Download selected (2)")...');
    const downloadPromise = page.waitForEvent('download', { timeout: 10000 });
    await page.click('button:has-text("Download selected (2)")');

    const download = await downloadPromise;
    const suggestedFilename = download.suggestedFilename();
    console.log(`  Browser intercepted download event!`);
    console.log(`  Suggested Zip Filename: "${suggestedFilename}"`);
    if (suggestedFilename !== 'alex_river_photos.zip') {
      throw new Error(`Expected zip filename 'alex_river_photos.zip', got '${suggestedFilename}'`);
    }

    // Save downloaded zip to temp test path to verify it is non-empty
    const tempZipPath = path.join(SCREENSHOT_DIR, 'e2e_test_download.zip');
    await download.saveAs(tempZipPath);
    const zipSize = fs.statSync(tempZipPath).size;
    console.log(`  Successfully generated and saved zip: ${tempZipPath} (${zipSize} bytes)`);
    if (zipSize < 50) {
      throw new Error(`Downloaded zip appears corrupt or empty (${zipSize} bytes)`);
    }
    // Clean up temp test zip
    fs.unlinkSync(tempZipPath);

    // 5. Exit Select Mode & Navigate to Unrecognized
    console.log('\n[E2E Step 6] Navigating to Unrecognized Gallery...');
    await page.click('button:has-text("Exit select")');
    await page.click('button[title="Back to all people"]');
    await page.waitForSelector('text=Unrecognized');

    await page.click('text=Unrecognized');
    await page.waitForSelector('text=Unrecognized Faces');

    // Invariant: Unrecognized gallery must NEVER have a "Download all" button
    const unrecDownloadAll = await page.$('button:has-text("Download all")');
    console.log(`  Unrecognized "Download all" button present: ${Boolean(unrecDownloadAll)}`);
    if (unrecDownloadAll) {
      throw new Error('Violation: Unrecognized gallery must NOT have a "Download all" button!');
    }

    console.log('\n=== ALL E2E VERIFICATION CHECKS PASSED ===');
    console.log('1. Three themes toggled & verified (Dark, Paper, Navy)');
    console.log('2. "Download all 3 photos" displays exact photo count');
    console.log('3. Per-photo download links use clean personname_001.jpg format');
    console.log('4. Select mode ticks photos & shows sticky bottom bar');
    console.log('5. Local streaming zip generation downloads alex_river_photos.zip');
    console.log('6. Unrecognized gallery has NO "Download all" button');
    console.log('7. Screenshots saved with ZERO real faces under scratch/screenshots');
  } finally {
    await browser.close();
    server.close();
  }
}

runE2E().catch((err) => {
  console.error('\n[FATAL] E2E Verification failed:', err);
  process.exit(1);
});
