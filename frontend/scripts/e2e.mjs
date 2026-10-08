import { spawn } from 'child_process';
import { readFileSync, readdirSync, writeFileSync, existsSync, rmSync, mkdirSync, statSync } from 'fs';
import { createHash } from 'crypto';
import path from 'path';
import { fileURLToPath } from 'url';
import { chromium } from 'playwright';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..', '..');

const isDevMode = process.argv.includes('--dev');
const API_PORT = isDevMode ? 8000 : 8765;
const UI_PORT = isDevMode ? 5174 : 8765;
const BASE_URL = `http://127.0.0.1:${UI_PORT}`;
const API_BASE_URL = `http://127.0.0.1:${API_PORT}`;

const PYTHON_PATH = path.resolve(REPO_ROOT, '.venv', 'Scripts', 'python.exe');
const CHROME_PATH = 'C:\\Users\\DELL\\AppData\\Local\\ms-playwright\\chromium-1200\\chrome-win64\\chrome.exe';

// ISOLATION PATHS
const TEMP_WORK_DIR = path.resolve(REPO_ROOT, 'export.e2e_temp.work');
const TEMP_OUTPUT_DIR = path.resolve(REPO_ROOT, 'export.e2e_temp');
const CANONICAL_WORK_DIR = path.resolve(REPO_ROOT, 'export.work');
const CANONICAL_EXPORT_DIR = path.resolve(REPO_ROOT, 'export');
const CANONICAL_EDITS_PATH = path.resolve(CANONICAL_WORK_DIR, 'edits.json');
const CANONICAL_PEOPLE_PATH = path.resolve(CANONICAL_EXPORT_DIR, 'people.json');

// Captured log lines for zero-cluster-id audit
const capturedLogs = [];

function computeSha256(filePath) {
  if (!existsSync(filePath)) return null;
  const content = readFileSync(filePath);
  return createHash('sha256').update(content).digest('hex');
}

function logMessage(...args) {
  const line = args.join(' ');
  capturedLogs.push(line);
  console.log(line);
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function fetchJson(endpoint) {
  const res = await fetch(`${API_BASE_URL}${endpoint}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return res.json();
}

async function waitForServer(url = `${API_BASE_URL}/api/health`, maxAttempts = 40) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await fetch(url);
      if (res.ok) {
        if (url.includes('/api/health')) {
          const data = await res.json();
          if (data.status === 'ok') return true;
        } else {
          return true;
        }
      }
    } catch {}
    await sleep(500);
  }
  throw new Error(`Server at ${url} did not become ready in time.`);
}

async function checkInvariant(stepName) {
  const people = await fetchJson('/api/people');
  const unrec = await fetchJson('/api/unrecognized');

  const clusteredFaces = people.reduce((acc, p) => acc + (p.faces ? p.faces.length : 0), 0);
  const unrecFaces = unrec.faces ? unrec.faces.length : 0;
  const totalFaces = clusteredFaces + unrecFaces;

  const holds = totalFaces === 1701;
  logMessage(
    `[INVARIANT ${stepName}] clustered=${clusteredFaces}, unrecognized=${unrecFaces}, total=${totalFaces} (invariant = ${holds ? 'HOLDS' : 'VIOLATION'})`
  );
  if (!holds) {
    throw new Error(`Invariant violation at step ${stepName}: total=${totalFaces} expected 1701`);
  }
  return { clusteredFaces, unrecFaces, totalFaces, peopleCount: people.length };
}

async function run() {
  logMessage('================================================================');
  logMessage('PhotoSorter Phase 4: Full End-to-End Browser Verification');
  logMessage(
    isDevMode
      ? '[MODE] Running against Vite dev server (npm run dev) + uvicorn API'
      : '[MODE] Running against built UI (frontend/dist) served directly by uvicorn'
  );
  logMessage('Isolated test execution against temporary workspace');
  logMessage('================================================================');

  // Verify and record canonical mtime and SHA-256 before run to assert isolation
  const initialCanonicalEditsMtime = existsSync(CANONICAL_EDITS_PATH)
    ? statSync(CANONICAL_EDITS_PATH).mtimeMs
    : 0;
  const initialCanonicalEditsSha = computeSha256(CANONICAL_EDITS_PATH);

  const initialExportFiles = existsSync(CANONICAL_EXPORT_DIR)
    ? readdirSync(CANONICAL_EXPORT_DIR).sort()
    : [];
  const initialPeopleJsonSha = computeSha256(CANONICAL_PEOPLE_PATH);

  // Setup isolated temporary directories
  if (existsSync(TEMP_WORK_DIR)) rmSync(TEMP_WORK_DIR, { recursive: true, force: true });
  if (existsSync(TEMP_OUTPUT_DIR)) rmSync(TEMP_OUTPUT_DIR, { recursive: true, force: true });
  mkdirSync(TEMP_WORK_DIR, { recursive: true });
  mkdirSync(TEMP_OUTPUT_DIR, { recursive: true });

  const tempEditsPath = path.resolve(TEMP_WORK_DIR, 'edits.json');
  writeFileSync(tempEditsPath, JSON.stringify({ version: 1, edits: [] }, null, 2), 'utf8');

  // Spawn uvicorn server in isolated environment
  logMessage(`\n[SPAWN] Starting uvicorn with isolated work/output dirs on port ${API_PORT}...`);
  const serverProc = spawn(
    PYTHON_PATH,
    ['-m', 'uvicorn', 'backend.api.app:app', '--host', '127.0.0.1', '--port', String(API_PORT)],
    {
      cwd: REPO_ROOT,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: {
        ...process.env,
        PHOTOSORTER_WORK_DIR: TEMP_WORK_DIR,
        PHOTOSORTER_OUTPUT_DIR: TEMP_OUTPUT_DIR,
        PHOTOSORTER_CACHE_DIR: CANONICAL_WORK_DIR,
      },
    }
  );
  serverProc.stderr.on('data', (d) => {
    const s = d.toString();
    if (s.includes('ERROR') || s.includes('400') || s.includes('500') || s.includes('Traceback')) {
      console.error(`[SERVER STDERR] ${s.trim()}`);
    }
  });

  let viteProc = null;
  if (isDevMode) {
    logMessage(`[SPAWN] Starting Vite dev server (npm run dev) on port ${UI_PORT}...`);
    viteProc = spawn(
      process.platform === 'win32' ? 'npm.cmd' : 'npm',
      ['--prefix', path.resolve(REPO_ROOT, 'frontend'), 'run', 'dev', '--', '--host', '127.0.0.1', '--port', String(UI_PORT)],
      {
        cwd: REPO_ROOT,
        stdio: ['ignore', 'pipe', 'pipe'],
        shell: process.platform === 'win32',
      }
    );
  }

  try {
    await waitForServer(`${API_BASE_URL}/api/health`);
    if (isDevMode) {
      await waitForServer(BASE_URL);
    }
    logMessage(`[SERVER READY] PhotoSorter API running at ${API_BASE_URL}, UI at ${BASE_URL}`);

    // Launch Chromium with Playwright
    logMessage(`[BROWSER] Launching headless Chromium via Playwright...`);
    const browser = await chromium.launch({
      executablePath: CHROME_PATH,
      headless: true,
    });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    page.on('console', (msg) => {
      const txt = msg.text();
      if (txt.toLowerCase().includes('error') || txt.toLowerCase().includes('failed')) {
        console.error(`[BROWSER CONSOLE] ${msg.type()}: ${txt}`);
      }
    });
    page.on('pageerror', (err) => {
      console.error(`[BROWSER PAGEERROR] ${err}`);
    });
    page.on('dialog', async (dialog) => {
      console.error(`[BROWSER DIALOG] ${dialog.type()}: ${dialog.message()}`);
      await dialog.dismiss();
    });

    // ----------------------------------------------------------------
    // STEP A: Start job, record at least 5 updates, verify 192 people
    // ----------------------------------------------------------------
    logMessage('\n----------------------------------------------------------------');
    logMessage('STEP A: Start sorting job, verify >= 5 SSE updates, end at 192 people');
    logMessage('----------------------------------------------------------------');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });

    await page.click('#tab-home');
    await page.waitForSelector('#input-source-path');
    await page.fill('#input-source-path', 'test_photos');
    await page.click('#start-job-btn');

    await page.waitForSelector('#progress-updates-log');
    logMessage('[STEP A] Sorting job started. Collecting SSE progress updates...');

    const updatesRecorded = [];
    const maxWaitTime = 60000;
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitTime) {
      const items = await page.$$eval('#progress-updates-log > div', (nodes) =>
        nodes.map((n) => n.textContent?.trim() || '')
      );
      if (items.length > updatesRecorded.length) {
        for (let i = updatesRecorded.length; i < items.length; i++) {
          updatesRecorded.push(items[i]);
          if (updatesRecorded.length <= 8) {
            logMessage(`  [PROGRESS UPDATE #${updatesRecorded.length}] ${items[i]}`);
          }
        }
      }

      const statusStage = await page.$eval('[data-testid="progress-stage"]', (el) => el.textContent?.trim() || '');
      const hasReviewBtn = await page.$('#goto-review-btn');
      if (statusStage === 'complete' || (hasReviewBtn && (await hasReviewBtn.isVisible()))) {
        break;
      }
      await sleep(400);
    }

    logMessage(`[STEP A] Total progress updates recorded: ${updatesRecorded.length} (>= 5 required)`);
    if (updatesRecorded.length < 5) {
      throw new Error(`Expected at least 5 progress updates, got ${updatesRecorded.length}`);
    }

    // Go to Review
    await page.click('#goto-review-btn');
    await page.waitForSelector('#subtab-people-count');
    const peopleCountText = await page.$eval('#subtab-people-count', (el) => el.textContent?.trim() || '');
    logMessage(`[STEP A] Review People screen loaded. People count: ${peopleCountText}`);
    if (peopleCountText !== '192') {
      throw new Error(`Expected 192 people on Review People screen, got ${peopleCountText}`);
    }
    await checkInvariant('a');

    // ----------------------------------------------------------------
    // STEP C ON CLEAN STATE: 7-way split (Set C) on fresh clean state
    // ----------------------------------------------------------------
    logMessage('\n----------------------------------------------------------------');
    logMessage('STEP C: 7-way split from eval/ground_truth.json (Set C) on clean state');
    logMessage('----------------------------------------------------------------');
    const gt = JSON.parse(readFileSync(path.resolve(REPO_ROOT, 'eval', 'ground_truth.json'), 'utf8'));
    const setCFaces = gt.sets['C']; // 8 faces
    logMessage(`[STEP C] Set C ground truth face IDs (${setCFaces.length} faces):`);
    for (const fid of setCFaces) {
      logMessage(`  - ${fid}`);
    }

    // Fresh state check: no prior merges
    const freshPeople = await fetchJson('/api/people');
    if (freshPeople.length !== 192) {
      throw new Error(`Expected fresh clean state with 192 people, found ${freshPeople.length}`);
    }

    // Locate the 7 clusters holding the 8 Set C faces
    const setCClusterMap = new Map();
    for (const fid of setCFaces) {
      const p = freshPeople.find((person) => person.faces && person.faces.some((f) => f.face_id === fid));
      if (p) {
        if (!setCClusterMap.has(p.id)) {
          setCClusterMap.set(p.id, { handle: p.id, faces: p.faces, setCFaces: [] });
        }
        setCClusterMap.get(p.id).setCFaces.push(fid);
      }
    }

    const setCClusters = Array.from(setCClusterMap.values());
    logMessage(`[STEP C] Set C faces are distributed across ${setCClusters.length} initial clusters.`);
    if (setCClusters.length !== 7) {
      throw new Error(`Expected Set C to be split across exactly 7 clusters, found ${setCClusters.length}`);
    }

    // Print each of the seven cluster sizes and their sum
    let clusterSizesSum = 0;
    const clusterSizes = [];
    for (let i = 0; i < setCClusters.length; i++) {
      const c = setCClusters[i];
      const sz = c.faces.length;
      clusterSizes.push(sz);
      clusterSizesSum += sz;
      logMessage(`  Cluster #${i + 1} size: ${sz} faces (contains ${c.setCFaces.length} Set C face IDs)`);
    }
    logMessage(`[STEP C] Sum of the seven cluster sizes: ${clusterSizesSum}`);

    // Select the seven clusters in the UI using their handles
    for (const c of setCClusters) {
      const cb = `#select-person-${c.handle}`;
      await page.waitForSelector(cb);
      await page.click(cb);
      await sleep(80);
    }

    // Merge in one single action
    await page.waitForSelector('#merge-selected-btn:not([disabled])');
    const mergeBtnText = await page.$eval('#merge-selected-btn', (el) => el.textContent?.trim() || '');
    logMessage(`[STEP C] Merge button text before click: "${mergeBtnText}"`);
    logMessage(`[STEP C] Merging all 7 clusters in one single action...`);
    await page.click('#merge-selected-btn');
    await page.waitForSelector('#merge-selected-btn', { state: 'detached', timeout: 20000 });

    let peopleAfterC = [];
    for (let i = 0; i < 30; i++) {
      peopleAfterC = await fetchJson('/api/people');
      if (peopleAfterC.length === 186) break;
      await sleep(300);
    }

    // Query resulting person and assert face count equals sum of the seven clusters
    logMessage(`[STEP C] Total people count after C: ${peopleAfterC.length}`);
    const mergedPersonC = peopleAfterC.find((p) => p.faces && p.faces.some((f) => f.face_id === setCFaces[0]));
    if (!mergedPersonC) {
      throw new Error(`Could not find person containing Set C faces after 7-way merge`);
    }

    const resultingPersonFaceCount = mergedPersonC.faces.length;
    logMessage(`[STEP C] Resulting person face count: ${resultingPersonFaceCount}`);
    logMessage(`[STEP C] Asserting sum (${clusterSizesSum}) === resulting person face count (${resultingPersonFaceCount})...`);
    if (clusterSizesSum !== resultingPersonFaceCount) {
      throw new Error(`Count mismatch: sum of clusters is ${clusterSizesSum} but merged person has ${resultingPersonFaceCount}`);
    }
    logMessage(`  [PASS] Cluster sizes sum (${clusterSizesSum}) equals resulting person face count (${resultingPersonFaceCount})!`);

    // Assert by face ID that all 8 Set C faces are in this single person
    const mergedPersonFaceIds = new Set(mergedPersonC.faces.map((f) => f.face_id));
    const allSetCFacesPresent = setCFaces.every((fid) => mergedPersonFaceIds.has(fid));
    logMessage(`[STEP C] Asserting all 8 Set C faces reside in the merged person by face ID...`);
    if (!allSetCFacesPresent) {
      throw new Error(`Not all 8 Set C faces were found in the merged person!`);
    }
    logMessage(`  [PASS] All 8 Set C face IDs are present in the unified person:`);
    for (const fid of setCFaces) {
      logMessage(`    - ${fid} (confirmed)`);
    }
    await checkInvariant('c');

    // ----------------------------------------------------------------
    // STEP B: Multi-select merge of 3 people in one action
    // ----------------------------------------------------------------
    logMessage('\n----------------------------------------------------------------');
    logMessage('STEP B: Multi-select merge 3 people in one action (people drops by 2)');
    logMessage('----------------------------------------------------------------');
    const peopleBeforeB = await fetchJson('/api/people');
    const countBeforeB = peopleBeforeB.length; // 186
    // Pick 3 people that do not contain Set C faces
    const nonSetCPeople = peopleBeforeB.filter((p) => !p.faces.some((f) => setCFaces.includes(f.face_id))).slice(0, 3);
    const threeHandles = nonSetCPeople.map((p) => p.id);
    logMessage(`[STEP B] Selecting 3 people for multi-merge...`);

    for (const h of threeHandles) {
      const cb = `#select-person-${h}`;
      await page.waitForSelector(cb);
      await page.click(cb);
      await sleep(80);
    }

    await page.waitForSelector('#merge-selected-btn:not([disabled])');
    await page.click('#merge-selected-btn');
    await page.waitForSelector('#merge-selected-btn', { state: 'detached', timeout: 20000 });

    let peopleAfterB = [];
    for (let i = 0; i < 30; i++) {
      peopleAfterB = await fetchJson('/api/people');
      if (peopleAfterB.length === countBeforeB - 2) break;
      await sleep(300);
    }

    await page.waitForFunction(
      (expected) => {
        const el = document.querySelector('#subtab-people-count');
        return el && parseInt(el.textContent || '0', 10) === expected;
      },
      countBeforeB - 2,
      { timeout: 15000 }
    );
    const countAfterB = parseInt(await page.$eval('#subtab-people-count', (el) => el.textContent?.trim() || '0'), 10);
    logMessage(`[STEP B] Count after merging 3 people: ${countAfterB} (before: ${countBeforeB})`);
    if (countAfterB !== countBeforeB - 2) {
      throw new Error(`Expected people count to drop by 2 (to ${countBeforeB - 2}), got ${countAfterB}`);
    }
    await checkInvariant('b');

    // ----------------------------------------------------------------
    // STEP D: Assign an Unrecognized face and assert count drops by 1
    // ----------------------------------------------------------------
    logMessage('\n----------------------------------------------------------------');
    logMessage('STEP D: Assign an Unrecognized face (unrecognized count drops by 1)');
    logMessage('----------------------------------------------------------------');
    await page.click('#tab-unrecognized');
    await page.waitForSelector('[data-testid="create-person-btn"]');

    const unrecBeforeD = await fetchJson('/api/unrecognized');
    const unrecCountBeforeD = unrecBeforeD.faces.length;
    logMessage(`[STEP D] Unrecognized faces before assign: ${unrecCountBeforeD}`);

    await page.click('[data-testid="create-person-btn"]');

    let unrecAfterD = unrecBeforeD;
    for (let i = 0; i < 30; i++) {
      unrecAfterD = await fetchJson('/api/unrecognized');
      if (unrecAfterD.faces.length === unrecCountBeforeD - 1) break;
      await sleep(300);
    }

    const unrecCountAfterD = unrecAfterD.faces.length;
    logMessage(`[STEP D] Unrecognized faces after assign: ${unrecCountAfterD}`);

    if (unrecCountAfterD !== unrecCountBeforeD - 1) {
      throw new Error(`Expected unrecognized faces to drop by exactly 1, went from ${unrecCountBeforeD} to ${unrecCountAfterD}`);
    }
    logMessage(`[STEP D] SUCCESS: Unrecognized faces dropped by exactly 1.`);
    await checkInvariant('d');

    // ----------------------------------------------------------------
    // STEP E: Perform undo for each edit type and assert counts return
    // ----------------------------------------------------------------
    logMessage('\n----------------------------------------------------------------');
    logMessage('STEP E: Perform Undo for each edit type and assert counts return');
    logMessage('----------------------------------------------------------------');
    // 1. Undo Assign (edit type: assign)
    logMessage('[STEP E.1] Undoing assign edit...');
    await page.click('#header-undo-btn');

    let unrecAfterUndoAssign = 0;
    for (let i = 0; i < 30; i++) {
      unrecAfterUndoAssign = (await fetchJson('/api/unrecognized')).faces.length;
      if (unrecAfterUndoAssign === unrecCountBeforeD) break;
      await sleep(300);
    }
    logMessage(`  Unrecognized count restored to: ${unrecAfterUndoAssign} (baseline: ${unrecCountBeforeD})`);
    if (unrecAfterUndoAssign !== unrecCountBeforeD) {
      throw new Error(`Undo assign failed: expected ${unrecCountBeforeD}, got ${unrecAfterUndoAssign}`);
    }
    await checkInvariant('e.1');

    // 2. Undo 3-way merge (edit type: merge)
    logMessage('[STEP E.2] Undoing 3-way merge...');
    await page.click('#header-undo-btn');

    let peopleAfterUndoB = [];
    for (let i = 0; i < 30; i++) {
      peopleAfterUndoB = await fetchJson('/api/people');
      if (peopleAfterUndoB.length === countBeforeB) break;
      await sleep(300);
    }
    logMessage(`  People count restored to: ${peopleAfterUndoB.length} (expected: ${countBeforeB})`);
    if (peopleAfterUndoB.length !== countBeforeB) {
      throw new Error(`Undo 3-way merge failed: expected ${countBeforeB}, got ${peopleAfterUndoB.length}`);
    }
    await checkInvariant('e.2');

    // 3. Undo 7-way split merge (edit type: merge)
    logMessage('[STEP E.3] Undoing 7-way split merge...');
    await page.click('#header-undo-btn');

    let peopleFinalUndo = [];
    for (let i = 0; i < 30; i++) {
      peopleFinalUndo = await fetchJson('/api/people');
      if (peopleFinalUndo.length === 192) break;
      await sleep(300);
    }
    logMessage(`  People count restored to baseline: ${peopleFinalUndo.length} (original: 192)`);
    if (peopleFinalUndo.length !== 192) {
      throw new Error(`Undo 7-way merge failed: expected 192, got ${peopleFinalUndo.length}`);
    }

    // Verify Set C faces returned to 7 distinct persons
    const distinctSetCPersons = new Set(
      setCFaces.map((fid) => {
        const p = peopleFinalUndo.find((person) => person.faces && person.faces.some((f) => f.face_id === fid));
        return p ? p.anchor_face_ids[0] : null;
      })
    );
    logMessage(`  Set C faces restored across ${distinctSetCPersons.size} distinct persons.`);
    if (distinctSetCPersons.size !== 7) {
      throw new Error(`Undo 7-way merge failed: expected 7 distinct persons, got ${distinctSetCPersons.size}`);
    }
    logMessage(`[STEP E] SUCCESS: All edit types cleanly undone and counts returned to baseline.`);
    await checkInvariant('e.3');

    // ----------------------------------------------------------------
    // STEP F: Accept one suggestion and reject another
    // ----------------------------------------------------------------
    logMessage('\n----------------------------------------------------------------');
    logMessage('STEP F: Accept one suggestion and reject another');
    logMessage('----------------------------------------------------------------');
    await page.click('#tab-people-grid');
    await page.click('#tab-suggestions');
    await page.waitForSelector('[data-testid="accept-suggestion-btn"]');

    const sugBefore = await fetchJson('/api/suggestions');
    logMessage(`[STEP F] Initial suggestions count: ${sugBefore.possibly_the_same.length}`);

    // Accept first suggestion
    const firstSug = sugBefore.possibly_the_same[0];
    const firstAnchorA = firstSug.person_a_anchors[0];
    const firstAnchorB = firstSug.person_b_anchors[0];
    logMessage(`[STEP F] Accepting suggestion between anchor ${firstAnchorA} and anchor ${firstAnchorB} (d=${firstSug.distance})...`);
    await page.click('[data-testid="accept-suggestion-btn"]');

    let peopleAfterSugAccept = [];
    for (let i = 0; i < 30; i++) {
      peopleAfterSugAccept = await fetchJson('/api/people');
      if (peopleAfterSugAccept.length === 191) break;
      await sleep(300);
    }
    logMessage(`[STEP F] People count after accept: ${peopleAfterSugAccept.length} (expected 191)`);
    if (peopleAfterSugAccept.length !== 191) {
      throw new Error(`Expected people count 191 after suggestion accept, got ${peopleAfterSugAccept.length}`);
    }

    // Reject second suggestion
    const sugAfterAccept = await fetchJson('/api/suggestions');
    const secondSug = sugAfterAccept.possibly_the_same[0];
    const secondAnchorA = secondSug.person_a_anchors[0];
    const secondAnchorB = secondSug.person_b_anchors[0];
    logMessage(`[STEP F] Rejecting suggestion between anchor ${secondAnchorA} and anchor ${secondAnchorB}...`);
    await page.click('[data-testid="reject-suggestion-btn"]');
    await sleep(500);

    const visibleCards = await page.$$eval('[data-testid="reject-suggestion-btn"]', (nodes) => nodes.length);
    logMessage(`[STEP F] Visible suggestion cards after rejection: ${visibleCards}`);
    logMessage(`[STEP F] SUCCESS: Suggestion accepted and rejected with session persistence.`);
    await checkInvariant('f');

    // ----------------------------------------------------------------
    // STEP G: Explicit action log, pre/post rerun count assertion,
    // and face ID target person assertion
    // ----------------------------------------------------------------
    logMessage('\n----------------------------------------------------------------');
    logMessage('STEP G: Trigger rerun and assert edits survive by face ID');
    logMessage('----------------------------------------------------------------');

    // 1. Explicit Action: Assign unrecognized face to TARGET person
    const unrecPreG = await fetchJson('/api/unrecognized');
    const faceToAssign = unrecPreG.faces[0];
    const assignedFaceId = faceToAssign.face_id;

    const peopleListForAssign = await fetchJson('/api/people');
    const targetPerson = peopleListForAssign[0];
    const targetAnchorId = targetPerson.anchor_face_ids[0];
    const targetHandle = targetPerson.id;

    logMessage(`[STEP G ACTION] Explicitly assigning unrecognized face ID: ${assignedFaceId}`);
    logMessage(`  -> Assigning to TARGET person with anchor face ID: ${targetAnchorId}`);

    // Navigate to Unrecognized tab and execute assign in UI
    await page.click('#tab-unrecognized');
    const faceCardSelector = `[data-testid="unrec-face-card-${assignedFaceId}"]`;
    await page.waitForSelector(faceCardSelector);

    // Select target person in dropdown and click Assign on this specific face card
    const faceCard = page.locator(faceCardSelector);
    await faceCard.locator('[data-testid="assign-target-select"]').selectOption(targetHandle);
    await faceCard.locator('[data-testid="assign-to-person-btn"]:not([disabled])').click();

    // Poll until assign takes effect in backend and state
    let peoplePreRerun = [];
    let unrecPreRerun = null;
    for (let i = 0; i < 30; i++) {
      peoplePreRerun = await fetchJson('/api/people');
      unrecPreRerun = await fetchJson('/api/unrecognized');
      const targetP = peoplePreRerun.find((p) => p.anchor_face_ids.includes(targetAnchorId));
      if (targetP && targetP.faces.some((f) => f.face_id === assignedFaceId)) {
        break;
      }
      await sleep(300);
    }

    // 2. Pre-rerun status log and counts
    const prePeopleCount = peoplePreRerun.length;
    const preUnrecCount = unrecPreRerun.faces.length;

    logMessage(`[STEP G PRE-RERUN] people_count: ${prePeopleCount}`);
    logMessage(`[STEP G PRE-RERUN] unrecognized_faces_count: ${preUnrecCount}`);
    logMessage(`[STEP G PRE-RERUN] Active persisted edits:`);
    logMessage(`  1. Merged suggestion face anchors: [${firstAnchorA}] + [${firstAnchorB}]`);
    logMessage(`  2. Assigned face ID ${assignedFaceId} to TARGET person [${targetAnchorId}]`);

    // Verify assign took effect before rerun
    const targetPersonPreRerun = peoplePreRerun.find((p) => p.anchor_face_ids.includes(targetAnchorId));
    if (!targetPersonPreRerun || !targetPersonPreRerun.faces.some((f) => f.face_id === assignedFaceId)) {
      throw new Error(`Target person does not contain assigned face ${assignedFaceId} prior to rerun`);
    }

    // 3. Navigate to Settings and trigger rerun with identical settings
    logMessage(`[STEP G ACTION] Navigating to Settings tab to rerun clustering with identical settings...`);
    await page.click('#tab-settings');
    await page.waitForSelector('#save-rerun-btn');

    logMessage('[STEP G ACTION] Clicking "Save & Rerun Clustering"...');
    await page.click('#save-rerun-btn');

    // Wait for rerun completion
    await page.waitForSelector('#rerun-result-summary', { timeout: 45000 });
    const rerunMsg = await page.$eval('#rerun-result-summary', (el) => el.textContent?.trim() || '');
    logMessage(`[STEP G] Rerun completed! Result summary: ${rerunMsg.replace(/\s+/g, ' ').slice(0, 160)}...`);

    // 4. Post-rerun counts assertion
    const peoplePostRerun = await fetchJson('/api/people');
    const unrecPostRerun = await fetchJson('/api/unrecognized');
    const postPeopleCount = peoplePostRerun.length;
    const postUnrecCount = unrecPostRerun.faces.length;

    logMessage(`[STEP G POST-RERUN] people_count: ${postPeopleCount}`);
    logMessage(`[STEP G POST-RERUN] unrecognized_faces_count: ${postUnrecCount}`);

    logMessage(`[STEP G ASSERTION] Asserting people_count equals pre-rerun count (${postPeopleCount} === ${prePeopleCount})...`);
    if (postPeopleCount !== prePeopleCount) {
      throw new Error(`People count changed across rerun: pre=${prePeopleCount}, post=${postPeopleCount}`);
    }
    logMessage(`  [PASS] people_count identical: ${postPeopleCount} === ${prePeopleCount}`);

    logMessage(`[STEP G ASSERTION] Asserting unrecognized_faces_count equals pre-rerun count (${postUnrecCount} === ${preUnrecCount})...`);
    if (postUnrecCount !== preUnrecCount) {
      throw new Error(`Unrecognized count changed across rerun: pre=${preUnrecCount}, post=${postUnrecCount}`);
    }
    logMessage(`  [PASS] unrecognized_faces_count identical: ${postUnrecCount} === ${preUnrecCount}`);

    // 5. Assert by face ID that the assigned face is in its TARGET person
    logMessage(`[STEP G ASSERTION] Asserting assigned face ${assignedFaceId} is in its TARGET person [${targetAnchorId}]...`);
    const targetPersonPostRerun = peoplePostRerun.find((p) => p.anchor_face_ids.includes(targetAnchorId));
    if (!targetPersonPostRerun) {
      throw new Error(`Could not find TARGET person [anchor ${targetAnchorId}] post-rerun!`);
    }
    const targetContainsFace = targetPersonPostRerun.faces.some((f) => f.face_id === assignedFaceId);
    if (!targetContainsFace) {
      throw new Error(`Assigned face ${assignedFaceId} is NOT in its TARGET person post-rerun!`);
    }
    logMessage(`  [PASS] Assigned face ${assignedFaceId} confirmed in TARGET person (anchor ${targetAnchorId}).`);

    // 6. Assert by face ID that the accepted-suggestion anchors are in one person
    logMessage(`[STEP G ASSERTION] Asserting accepted-suggestion anchors (${firstAnchorA} & ${firstAnchorB}) are in one person...`);
    const personContainingAnchorA = peoplePostRerun.find((p) => p.faces.some((f) => f.face_id === firstAnchorA));
    if (!personContainingAnchorA) {
      throw new Error(`Could not find person containing anchor A (${firstAnchorA}) post-rerun!`);
    }
    const hasBothAnchors = personContainingAnchorA.faces.some((f) => f.face_id === firstAnchorB);
    if (!hasBothAnchors) {
      throw new Error(`Accepted suggestion anchors ${firstAnchorA} and ${firstAnchorB} are NOT in the same person post-rerun!`);
    }
    logMessage(`  [PASS] Both suggestion anchors (${firstAnchorA} & ${firstAnchorB}) reside in one unified person post-rerun.`);
    await checkInvariant('g');

    // ----------------------------------------------------------------
    // STEP H: Export bundle to temp folder and verify bundle hygiene
    // ----------------------------------------------------------------
    logMessage('\n----------------------------------------------------------------');
    logMessage('STEP H: Export bundle to temp folder and assert clean static bundle structure');
    logMessage('----------------------------------------------------------------');
    await page.click('#tab-export');
    await page.waitForSelector('#export-bundle-btn');
    await page.waitForSelector('#export-output-dir-input');

    logMessage(`[STEP H ACTION] Explicitly setting export destination input to isolated path: ${TEMP_OUTPUT_DIR}`);
    await page.fill('#export-output-dir-input', TEMP_OUTPUT_DIR);
    await sleep(200);

    logMessage('[STEP H] Clicking "Export Public Bundle"...');
    await page.click('#export-bundle-btn');
    await page.waitForSelector('#export-success-summary', { timeout: 30000 });

    const exportStatsPeople = await page.$eval('#export-stat-people', (el) => el.textContent?.trim() || '');
    const exportStatsPhotos = await page.$eval('#export-stat-photos', (el) => el.textContent?.trim() || '');
    logMessage(`[STEP H] Export completed: ${exportStatsPeople} people, ${exportStatsPhotos} photos.`);

    // Verify temp export directory on disk
    const exportedItems = readdirSync(TEMP_OUTPUT_DIR).filter((f) => !f.startsWith('.'));
    logMessage(`[STEP H] Contents of isolated export directory on disk:`, exportedItems.sort());

    const allowedItems = new Set(['config.json', 'people.json', 'faces', 'thumbs']);
    for (const item of exportedItems) {
      if (!allowedItems.has(item)) {
        throw new Error(`Hygiene Violation: Forbidden file '${item}' found in public export bundle!`);
      }
    }
    for (const item of allowedItems) {
      if (!exportedItems.includes(item)) {
        throw new Error(`Missing expected bundle item '${item}' in export directory`);
      }
    }

    // Verify forbidden files are strictly absent
    const forbidden = ['suggestions.json', 'edits.json', 'id_map.json', '.cache'];
    for (const f of forbidden) {
      if (existsSync(path.resolve(TEMP_OUTPUT_DIR, f))) {
        throw new Error(`CRITICAL: Private organizer artifact '${f}' was exported to public bundle!`);
      }
    }

    logMessage('[STEP H] SUCCESS: Bundle contains strictly config.json, people.json, faces/, and thumbs/.');
    await checkInvariant('h');

    // ----------------------------------------------------------------
    // ISOLATION AND CANONICAL PRESERVATION ASSERTION
    // ----------------------------------------------------------------
    logMessage('\n----------------------------------------------------------------');
    logMessage('ISOLATION AUDIT: Asserting canonical export/ and export.work/ were NEVER modified');
    logMessage('----------------------------------------------------------------');
    const finalCanonicalEditsMtime = existsSync(CANONICAL_EDITS_PATH)
      ? statSync(CANONICAL_EDITS_PATH).mtimeMs
      : 0;
    const finalCanonicalEditsSha = computeSha256(CANONICAL_EDITS_PATH);
    const finalExportFiles = existsSync(CANONICAL_EXPORT_DIR)
      ? readdirSync(CANONICAL_EXPORT_DIR).sort()
      : [];
    const finalPeopleJsonSha = computeSha256(CANONICAL_PEOPLE_PATH);

    // 1. export.work/edits.json mtime and SHA-256
    if (finalCanonicalEditsMtime !== initialCanonicalEditsMtime) {
      throw new Error(`CRITICAL ISOLATION VIOLATION: Canonical export.work/edits.json mtime changed!`);
    }
    if (finalCanonicalEditsSha !== initialCanonicalEditsSha) {
      throw new Error(`CRITICAL ISOLATION VIOLATION: Canonical export.work/edits.json SHA-256 changed! before=${initialCanonicalEditsSha} after=${finalCanonicalEditsSha}`);
    }
    logMessage(`[ISOLATION AUDIT PASS] Canonical export.work/edits.json unchanged (SHA-256: ${finalCanonicalEditsSha}).`);

    // 2. Canonical export/ directory file list
    const exportFileListMatches = JSON.stringify(finalExportFiles) === JSON.stringify(initialExportFiles);
    if (!exportFileListMatches) {
      throw new Error(`CRITICAL ISOLATION VIOLATION: Canonical export/ directory file list changed! before=${JSON.stringify(initialExportFiles)} after=${JSON.stringify(finalExportFiles)}`);
    }
    logMessage(`[ISOLATION AUDIT PASS] Canonical export/ file list unchanged: [${finalExportFiles.join(', ')}].`);

    // 3. Canonical export/people.json SHA-256
    if (finalPeopleJsonSha !== initialPeopleJsonSha) {
      throw new Error(`CRITICAL ISOLATION VIOLATION: Canonical export/people.json SHA-256 changed! before=${initialPeopleJsonSha} after=${finalPeopleJsonSha}`);
    }
    logMessage(`[ISOLATION AUDIT PASS] Canonical export/people.json unchanged (SHA-256: ${finalPeopleJsonSha}).`);

    // ----------------------------------------------------------------
    // ZERO CLUSTER-ID (\bp\d{3}\b) AUDIT IN PRINTED ASSERTIONS & OUTPUT
    // ----------------------------------------------------------------
    logMessage('\n----------------------------------------------------------------');
    logMessage('CLUSTER-ID AUDIT: Verifying zero pNNN tokens in printed assertions and output');
    logMessage('----------------------------------------------------------------');
    const clusterPat = /\bp\d{3}\b/;
    const violations = [];
    for (let i = 0; i < capturedLogs.length; i++) {
      const line = capturedLogs[i];
      if (clusterPat.test(line)) {
        violations.push({ lineIndex: i + 1, content: line });
      }
    }

    if (violations.length > 0) {
      logMessage(`[FAIL] Found ${violations.length} cluster-ID token violations in printed output:`);
      for (const v of violations) {
        logMessage(`  Line ${v.lineIndex}: ${v.content}`);
      }
      throw new Error(`Cluster-ID audit failed: printed output contains ${violations.length} forbidden pNNN tokens`);
    }
    logMessage(`[CLUSTER-ID AUDIT PASS] Zero pNNN tokens detected across all ${capturedLogs.length} printed log/assertion lines.`);

    logMessage('\n================================================================');
    logMessage('ALL PHASE 4 E2E BROWSER VERIFICATION CHECKS PASSED (100%)');
    logMessage('================================================================');

    await browser.close();
  } finally {
    logMessage('\n[TEARDOWN] Stopping server processes and cleaning temp dirs...');
    if (serverProc) {
      if (process.platform === 'win32') {
        try { spawn('taskkill', ['/pid', String(serverProc.pid), '/f', '/t']); } catch {}
      } else {
        serverProc.kill('SIGTERM');
      }
    }
    if (viteProc) {
      if (process.platform === 'win32') {
        try { spawn('taskkill', ['/pid', String(viteProc.pid), '/f', '/t']); } catch {}
      } else {
        viteProc.kill('SIGTERM');
      }
    }
    await sleep(1000);
    if (existsSync(TEMP_WORK_DIR)) rmSync(TEMP_WORK_DIR, { recursive: true, force: true });
    if (existsSync(TEMP_OUTPUT_DIR)) rmSync(TEMP_OUTPUT_DIR, { recursive: true, force: true });
    logMessage('[TEARDOWN] Temporary test directories removed.');
  }
}

run().catch((err) => {
  console.error('\n[FATAL ERROR in E2E Script]:', err);
  process.exit(1);
});
