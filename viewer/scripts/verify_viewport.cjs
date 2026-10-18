const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const DIST_DIR = path.resolve(__dirname, '../dist');

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
      if (reqPath === '/') reqPath = '/index.html';
      const filePath = path.join(DIST_DIR, reqPath);

      if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        res.writeHead(404);
        res.end('Not found');
        return;
      }

      const ext = path.extname(filePath).toLowerCase();
      const contentType = MIME_TYPES[ext] || 'application/octet-stream';
      res.writeHead(200, { 'Content-Type': contentType });
      fs.createReadStream(filePath).pipe(res);
    });

    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      resolve({ server, port });
    });
  });
}

async function runViewportVerification() {
  console.log('=== Verifying Built Viewer Viewport Rendering (TASK 1a) ===');
  console.log(`Serving built viewer from: ${DIST_DIR}`);
  
  const { server, port } = await startServer();
  const url = `http://127.0.0.1:${port}/`;
  console.log(`Local test server running at: ${url}`);

  const chromePath = 'C:\\Users\\DELL\\AppData\\Local\\ms-playwright\\chromium-1200\\chrome-win64\\chrome.exe';
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(chromePath) ? chromePath : undefined,
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // 1. Render at 390px width (Mobile)
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForSelector('.grid');

    const mobileInfo = await page.evaluate(() => {
      const grid = document.querySelector('.grid');
      const style = window.getComputedStyle(grid);
      const templateCols = style.getPropertyValue('grid-template-columns');
      const cols = templateCols.split(' ').filter(Boolean).length;
      return {
        viewportWidth: window.innerWidth,
        gridTemplateColumns: templateCols,
        columnCount: cols,
      };
    });

    console.log('\n[Mobile Viewport: 390px]');
    console.log(`  window.innerWidth:        ${mobileInfo.viewportWidth}px`);
    console.log(`  grid-template-columns:    ${mobileInfo.gridTemplateColumns}`);
    console.log(`  Calculated Column Count:  ${mobileInfo.columnCount}`);

    // 2. Render at 1280px width (Desktop)
    await page.setViewportSize({ width: 1280, height: 800 });
    // Wait for resize reflow
    await page.waitForTimeout(300);

    const desktopInfo = await page.evaluate(() => {
      const grid = document.querySelector('.grid');
      const style = window.getComputedStyle(grid);
      const templateCols = style.getPropertyValue('grid-template-columns');
      const cols = templateCols.split(' ').filter(Boolean).length;
      return {
        viewportWidth: window.innerWidth,
        gridTemplateColumns: templateCols,
        columnCount: cols,
      };
    });

    console.log('\n[Desktop Viewport: 1280px]');
    console.log(`  window.innerWidth:        ${desktopInfo.viewportWidth}px`);
    console.log(`  grid-template-columns:    ${desktopInfo.gridTemplateColumns}`);
    console.log(`  Calculated Column Count:  ${desktopInfo.columnCount}`);

    // Assert that column counts differ between 390px and 1280px
    if (mobileInfo.columnCount === desktopInfo.columnCount) {
      throw new Error(
        `Assertion failed: Expected column counts to differ, but both are ${mobileInfo.columnCount}`
      );
    }

    console.log('\n=== ASSERTION SUCCESS ===');
    console.log(
      `Mobile column count (${mobileInfo.columnCount}) differs from Desktop column count (${desktopInfo.columnCount}).`
    );
    console.log('Requirement 1a PASS: Viewport evidence verified in headless Chromium.');
  } finally {
    await browser.close();
    server.close();
  }
}

runViewportVerification().catch((err) => {
  console.error('\nVerification FAILED:', err);
  process.exit(1);
});
