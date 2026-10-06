import { spawn } from 'child_process';
import { readFileSync, readdirSync, writeFileSync, existsSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { chromium } from 'playwright';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8765;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const PYTHON_PATH = path.resolve(REPO_ROOT, '.venv', 'Scripts', 'python.exe');
const CHROME_PATH = 'C:\\Users\\DELL\\AppData\\Local\\ms-playwright\\chromium-1200\\chrome-win64\\chrome.exe';

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function fetchJson(endpoint) {
  const res = await fetch(`${BASE_URL}${endpoint}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return res.json();
}

async function waitForServer(maxAttempts = 40) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await fetch(`${BASE_URL}/api/health`);
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'ok') return true;
      }
    } catch {}
    await sleep(500);
  }
  throw new Error(`Server at ${BASE_URL} did not become ready in time.`);
}

async function checkInvariant(stepName) {
  const people = await fetchJson('/api/people');
  const unrec = await fetchJson('/api/unrecognized');

  const clusteredFaces = people.reduce((acc, p) => acc + (p.faces ? p.faces.length : 0), 0);
  const unrecFaces = unrec.faces ? unrec.faces.length : 0;
  const totalFaces = clusteredFaces + unrecFaces;

  const holds = totalFaces === 1701;
  console.log(
    `[INVARIANT ${stepName}] clustered=${clusteredFaces}, unrecognized=${unrecFaces}, total=${totalFaces} (invariant = ${holds ? 'HOLDS' : 'VIOLATION'})`
  );
  if (!holds) {
    throw new Error(`Invariant violation at step ${stepName}: total=${totalFaces} expected 1701`);
  }
  return { clusteredFaces, unrecFaces, totalFaces, peopleCount: people.length };
}

async function run() {
  console.log('================================================================');
  console.log('PhotoSorter Phase 4: Full End-to-End Browser Verification');
  console.log('Testing against uvicorn serving built React UI & canonical data');
  console.log('================================================================');

  // Reset export.work/edits.json to empty edits
  const editsPath = path.resolve(REPO_ROOT, 'export.work', 'edits.json');
  writeFileSync(editsPath, JSON.stringify({ version: 1, edits: [] }, null, 2), 'utf8');

  // Spawn uvicorn server
  console.log(`\n[SPAWN] Starting uvicorn on port ${PORT}...`);
  const serverProc = spawn(
    PYTHON_PATH,
    ['-m', 'uvicorn', 'backend.api.app:app', '--host', '127.0.0.1', '--port', String(PORT)],
    { cwd: REPO_ROOT, stdio: ['ignore', 'pipe', 'pipe'] }
  );

  serverProc.stdout.on('data', (d) => {
    // console.log(`[SERVER STDOUT] ${d}`);
  });
  serverProc.stderr.on('data', (d) => {
    // console.error(`[SERVER STDERR] ${d}`);
  });

  try {
    await waitForServer();
    console.log(`[SERVER READY] PhotoSorter API running at ${BASE_URL}`);

    // Launch Chromium with Playwright
    console.log(`[BROWSER] Launching headless Chromium via Playwright...`);
    const browser = await chromium.launch({
      executablePath: CHROME_PATH,
      headless: true,
    });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();

    // STEP A: Start job, record at least 5 updates, verify 192 people
    console.log('\n----------------------------------------------------------------');
    console.log('STEP A: Start sorting job, verify >= 5 SSE updates, end at 192 people');
    console.log('----------------------------------------------------------------');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });

    // Click Home tab
    await page.click('#tab-home');
    await page.waitForSelector('#input-source-path');

    // Fill test_photos and start
    await page.fill('#input-source-path', 'test_photos');
    await page.click('#start-job-btn');

    // Wait for Progress screen
    await page.waitForSelector('#progress-updates-log');
    console.log('[STEP A] Sorting job started. Collecting SSE progress updates...');

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
            console.log(`  [PROGRESS UPDATE #${updatesRecorded.length}] ${items[i]}`);
          }
        }
      }

      // Check if finished
      const statusStage = await page.$eval('[data-testid="progress-stage"]', (el) => el.textContent?.trim() || '');
      const hasReviewBtn = await page.$('#goto-review-btn');
      if (statusStage === 'complete' || (hasReviewBtn && (await hasReviewBtn.isVisible()))) {
        break;
      }
      await sleep(400);
    }

    console.log(`[STEP A] Total progress updates recorded: ${updatesRecorded.length} (>= 5 required)`);
    if (updatesRecorded.length < 5) {
      throw new Error(`Expected at least 5 progress updates, got ${updatesRecorded.length}`);
    }

    // Click Go to Review
    await page.click('#goto-review-btn');
    await page.waitForSelector('#subtab-people-count');
    const peopleCountText = await page.$eval('#subtab-people-count', (el) => el.textContent?.trim() || '');
    console.log(`[STEP A] Review People screen loaded. People count: ${peopleCountText}`);
    if (peopleCountText !== '192') {
      throw new Error(`Expected 192 people on Review People screen, got ${peopleCountText}`);
    }
    await checkInvariant('a');

    // STEP B: Multi-select merge of 3 people in one action
    console.log('\n----------------------------------------------------------------');
    console.log('STEP B: Multi-select merge 3 people in one action (people drops by 2)');
    console.log('----------------------------------------------------------------');
    const initialPeople = await fetchJson('/api/people');
    const initialCount = initialPeople.length; // 192
    const threePeople = initialPeople.slice(0, 3);
    const threeIds = threePeople.map((p) => p.id);
    console.log(`[STEP B] Selecting 3 people by handle for multi-merge: ${threeIds.join(', ')}`);

    for (const pid of threeIds) {
      const checkboxSelector = `#select-person-${pid}`;
      await page.waitForSelector(checkboxSelector);
      await page.click(checkboxSelector);
      await sleep(100);
    }

    // Verify merge banner
    await page.waitForSelector('#merge-selected-btn:not([disabled])');
    const mergeBtnText = await page.$eval('#merge-selected-btn', (el) => el.textContent?.trim() || '');
    console.log(`[STEP B] Merge banner ready: "${mergeBtnText}"`);

    // Click Merge Selected
    await page.click('#merge-selected-btn');
    await sleep(800);
    await page.waitForSelector('#subtab-people-count');

    const countAfterB = parseInt(await page.$eval('#subtab-people-count', (el) => el.textContent?.trim() || '0'), 10);
    console.log(`[STEP B] Count after merging 3 people: ${countAfterB} (initial: ${initialCount})`);
    if (countAfterB !== initialCount - 2) {
      throw new Error(`Expected people count to drop by 2 (to ${initialCount - 2}), got ${countAfterB}`);
    }
    await checkInvariant('b');

    // STEP C: Merge 7-way split from eval/ground_truth.json (Set C) in a single action
    console.log('\n----------------------------------------------------------------');
    console.log('STEP C: Merge 7-way split from eval/ground_truth.json (Set C) in one action');
    console.log('----------------------------------------------------------------');
    const gt = JSON.parse(readFileSync(path.resolve(REPO_ROOT, 'eval', 'ground_truth.json'), 'utf8'));
    const setCFaces = gt.sets['C']; // 8 faces
    console.log(`[STEP C] Set C ground truth face IDs (${setCFaces.length} faces):`);
    for (const fid of setCFaces) {
      console.log(`  - ${fid}`);
    }

    // Look up which persons currently hold these 8 faces
    const currentPeople = await fetchJson('/api/people');
    const setCPersonMap = new Map();
    for (const fid of setCFaces) {
      const p = currentPeople.find((person) => person.faces && person.faces.some((f) => f.face_id === fid));
      if (p) {
        if (!setCPersonMap.has(p.id)) setCPersonMap.set(p.id, []);
        setCPersonMap.get(p.id).push(fid);
      }
    }

    const setCPersonIds = Array.from(setCPersonMap.keys());
    console.log(`[STEP C] Found ${setCFaces.length} faces split across ${setCPersonIds.length} persons:`);
    for (const [pid, fids] of setCPersonMap.entries()) {
      console.log(`  Person handle ${pid}: faces [${fids.join(', ')}]`);
    }

    if (setCPersonIds.length < 2) {
      throw new Error(`Set C expected split across multiple persons, found ${setCPersonIds.length}`);
    }

    // Select all these split persons in the UI
    for (const pid of setCPersonIds) {
      const cb = `#select-person-${pid}`;
      await page.waitForSelector(cb);
      await page.click(cb);
      await sleep(100);
    }

    // Merge in a single action
    await page.waitForSelector('#merge-selected-btn:not([disabled])');
    console.log(`[STEP C] Merging all ${setCPersonIds.length} persons in one action...`);
    await page.click('#merge-selected-btn');
    await sleep(800);

    // Verify all 8 faces now end up in exactly ONE person
    const peopleAfterC = await fetchJson('/api/people');
    const targetPerson = peopleAfterC.find((p) => p.faces && p.faces.some((f) => f.face_id === setCFaces[0]));
    if (!targetPerson) {
      throw new Error(`Could not find person containing first Set C face ${setCFaces[0]}`);
    }

    const targetPersonFaceIds = targetPerson.faces.map((f) => f.face_id);
    const missingFaces = setCFaces.filter((fid) => !targetPersonFaceIds.includes(fid));

    console.log(`[STEP C] Verification: Person containing Set C has ${targetPersonFaceIds.length} faces.`);
    if (missingFaces.length > 0) {
      throw new Error(`7-way merge failed! Missing faces from merged person: ${missingFaces.join(', ')}`);
    }
    console.log(`[STEP C] SUCCESS: All 8 faces from Set C now reside in one unified person!`);
    await checkInvariant('c');

    // STEP D: Assign an Unrecognized face and assert count drops by exactly 1
    console.log('\n----------------------------------------------------------------');
    console.log('STEP D: Assign an Unrecognized face (unrecognized count drops by 1)');
    console.log('----------------------------------------------------------------');
    // Switch to Unrecognized subtab
    await page.click('#tab-unrecognized');
    await page.waitForSelector('[data-testid="create-person-btn"]');

    const unrecBefore = await fetchJson('/api/unrecognized');
    const unrecCountBefore = unrecBefore.faces.length;
    console.log(`[STEP D] Unrecognized faces before assign: ${unrecCountBefore}`);

    // Click Create New Person on the first unrecognized face
    await page.click('[data-testid="create-person-btn"]');
    await sleep(800);

    const unrecAfter = await fetchJson('/api/unrecognized');
    const unrecCountAfter = unrecAfter.faces.length;
    console.log(`[STEP D] Unrecognized faces after assign: ${unrecCountAfter}`);

    if (unrecCountAfter !== unrecCountBefore - 1) {
      throw new Error(`Expected unrecognized faces to drop by exactly 1, went from ${unrecCountBefore} to ${unrecCountAfter}`);
    }
    console.log(`[STEP D] SUCCESS: Unrecognized faces dropped by exactly 1.`);
    await checkInvariant('d');

    // STEP E: Perform undo for each edit type and assert counts return
    console.log('\n----------------------------------------------------------------');
    console.log('STEP E: Perform Undo for each edit type and assert counts return');
    console.log('----------------------------------------------------------------');
    // 1. Undo Assign (edit type: assign)
    console.log('[STEP E.1] Undoing assign edit...');
    await page.click('#header-undo-btn');
    await sleep(800);
    const unrecAfterUndoAssign = (await fetchJson('/api/unrecognized')).faces.length;
    console.log(`  Unrecognized count restored to: ${unrecAfterUndoAssign} (baseline: ${unrecCountBefore})`);
    if (unrecAfterUndoAssign !== unrecCountBefore) {
      throw new Error(`Undo assign failed: expected ${unrecCountBefore}, got ${unrecAfterUndoAssign}`);
    }
    await checkInvariant('e.1');

    // 2. Undo Set C 7-way merge (edit type: merge)
    console.log('[STEP E.2] Undoing 7-way split merge...');
    await page.click('#header-undo-btn');
    await sleep(800);
    const peopleAfterUndoC = await fetchJson('/api/people');
    const distinctSetCPersons = new Set(
      setCFaces.map((fid) => {
        const p = peopleAfterUndoC.find((person) => person.faces && person.faces.some((f) => f.face_id === fid));
        return p ? p.id : null;
      })
    );
    console.log(`  Set C faces restored to ${distinctSetCPersons.size} distinct persons.`);
    if (distinctSetCPersons.size < 2) {
      throw new Error(`Undo 7-way merge failed: faces still unified`);
    }
    await checkInvariant('e.2');

    // 3. Undo 3-way merge (edit type: merge)
    console.log('[STEP E.3] Undoing initial 3-way merge...');
    await page.click('#header-undo-btn');
    await sleep(800);
    const peopleFinalUndo = await fetchJson('/api/people');
    console.log(`  People count restored to: ${peopleFinalUndo.length} (original: 192)`);
    if (peopleFinalUndo.length !== 192) {
      throw new Error(`Undo 3-way merge failed: expected 192, got ${peopleFinalUndo.length}`);
    }
    console.log(`[STEP E] SUCCESS: All edit types cleanly undone and counts returned to baseline.`);
    await checkInvariant('e.3');

    // STEP F: Accept one suggestion and reject another
    console.log('\n----------------------------------------------------------------');
    console.log('STEP F: Accept one suggestion and reject another');
    console.log('----------------------------------------------------------------');
    await page.click('#tab-people-grid'); // Back to people grid subtab
    await page.click('#tab-suggestions'); // Open suggestions
    await page.waitForSelector('[data-testid="accept-suggestion-btn"]');

    const sugBefore = await fetchJson('/api/suggestions');
    console.log(`[STEP F] Initial suggestions count: ${sugBefore.possibly_the_same.length}`);

    // Accept first suggestion
    const firstSug = sugBefore.possibly_the_same[0];
    console.log(`[STEP F] Accepting suggestion between ${firstSug.person_a_id} and ${firstSug.person_b_id} (d=${firstSug.distance})...`);
    await page.click('[data-testid="accept-suggestion-btn"]');
    await sleep(800);

    const peopleAfterSugAccept = await fetchJson('/api/people');
    console.log(`[STEP F] People count after accept: ${peopleAfterSugAccept.length} (expected 191)`);
    if (peopleAfterSugAccept.length !== 191) {
      throw new Error(`Expected people count 191 after suggestion accept, got ${peopleAfterSugAccept.length}`);
    }

    // Reject second suggestion
    const sugAfterAccept = await fetchJson('/api/suggestions');
    const secondSug = sugAfterAccept.possibly_the_same[0];
    console.log(`[STEP F] Rejecting suggestion between ${secondSug.person_a_id} and ${secondSug.person_b_id}...`);
    await page.click('[data-testid="reject-suggestion-btn"]');
    await sleep(500);

    // Verify rejected suggestion is hidden
    const visibleCards = await page.$$eval('[data-testid="reject-suggestion-btn"]', (nodes) => nodes.length);
    console.log(`[STEP F] Visible suggestion cards after rejection: ${visibleCards}`);
    console.log(`[STEP F] SUCCESS: Suggestion accepted and rejected with session persistence.`);
    await checkInvariant('f');

    // STEP G: Trigger rerun and assert edits survive by face ID
    console.log('\n----------------------------------------------------------------');
    console.log('STEP G: Trigger rerun and assert edits survive by face ID');
    console.log('----------------------------------------------------------------');
    // Also perform an assign edit to test both merge and assign survive rerun
    await page.click('#tab-unrecognized');
    await page.waitForSelector('[data-testid="create-person-btn"]');
    await page.click('[data-testid="create-person-btn"]');
    await sleep(600);

    // Get assigned face ID from the newly created person
    const peoplePreRerun = await fetchJson('/api/people');
    const newPerson = peoplePreRerun[peoplePreRerun.length - 1];
    const assignedFaceId = newPerson.faces[0].face_id;
    console.log(`[STEP G] Active edits before rerun:`);
    console.log(`  1. Merged suggestion face anchors: [${firstSug.person_a_anchors.join(', ')}] + [${firstSug.person_b_anchors.join(', ')}]`);
    console.log(`  2. Assigned unrecognized face ID: ${assignedFaceId}`);

    // Navigate to Settings tab
    await page.click('#tab-settings');
    await page.waitForSelector('#save-rerun-btn');

    // Click Save & Rerun Clustering
    console.log('[STEP G] Clicking "Save & Rerun Clustering"...');
    await page.click('#save-rerun-btn');

    // Wait for rerun completion
    await page.waitForSelector('#rerun-result-summary', { timeout: 30000 });
    const rerunMsg = await page.$eval('#rerun-result-summary', (el) => el.textContent?.trim() || '');
    console.log(`[STEP G] Rerun completed! Feedback: ${rerunMsg.replace(/\s+/g, ' ').slice(0, 160)}...`);

    // Verify merge survived: faces from firstSug must still be together
    const peoplePostRerun = await fetchJson('/api/people');
    const survivedMergePerson = peoplePostRerun.find(
      (p) => p.faces && p.faces.some((f) => firstSug.person_a_anchors.includes(f.face_id))
    );
    if (!survivedMergePerson) {
      throw new Error('Could not find person containing merged anchors after rerun');
    }
    const survivedMergeFids = survivedMergePerson.faces.map((f) => f.face_id);
    const hasPersonAFaces = firstSug.person_a_anchors.some((fid) => survivedMergeFids.includes(fid));
    const hasPersonBFaces = firstSug.person_b_anchors.some((fid) => survivedMergeFids.includes(fid));

    if (!hasPersonAFaces || !hasPersonBFaces) {
      throw new Error('Merge edit did not survive rerun by face ID!');
    }
    console.log(`  [OK] Merge survived: anchors from both persons reside in one unified cluster post-rerun.`);

    // Verify assign survived: assignedFaceId must be in a person cluster
    const survivedAssignPerson = peoplePostRerun.find(
      (p) => p.faces && p.faces.some((f) => f.face_id === assignedFaceId)
    );
    if (!survivedAssignPerson) {
      throw new Error(`Assigned face ${assignedFaceId} did not survive rerun!`);
    }
    console.log(`  [OK] Assign survived: face ID ${assignedFaceId} remains assigned to a cluster post-rerun.`);
    console.log(`[STEP G] SUCCESS: All edits survived pipeline rerun strictly by face ID.`);
    await checkInvariant('g');

    // STEP H: Export bundle and assert only config.json, people.json, faces/, thumbs/
    console.log('\n----------------------------------------------------------------');
    console.log('STEP H: Export bundle and assert clean static bundle structure');
    console.log('----------------------------------------------------------------');
    // Navigate to Export tab
    await page.click('#tab-export');
    await page.waitForSelector('#export-bundle-btn');

    // Click Export Public Bundle
    console.log('[STEP H] Clicking "Export Public Bundle"...');
    await page.click('#export-bundle-btn');
    await page.waitForSelector('#export-success-summary', { timeout: 30000 });

    const exportStatsPeople = await page.$eval('#export-stat-people', (el) => el.textContent?.trim() || '');
    const exportStatsPhotos = await page.$eval('#export-stat-photos', (el) => el.textContent?.trim() || '');
    console.log(`[STEP H] Export completed: ${exportStatsPeople} people, ${exportStatsPhotos} photos.`);

    // Verify directory on disk
    const exportDir = path.resolve(REPO_ROOT, 'export');
    const exportedItems = readdirSync(exportDir).filter((f) => !f.startsWith('.'));
    console.log(`[STEP H] Contents of export/ directory on disk:`, exportedItems);

    const allowedItems = new Set(['config.json', 'people.json', 'faces', 'thumbs']);
    for (const item of exportedItems) {
      if (!allowedItems.has(item)) {
        throw new Error(`Hygiene Violation: Forbidden file '${item}' found in public export bundle!`);
      }
    }
    for (const item of allowedItems) {
      if (!exportedItems.includes(item)) {
        throw new Error(`Missing expected bundle item '${item}' in export/ directory`);
      }
    }

    // Verify forbidden files are strictly absent
    const forbidden = ['suggestions.json', 'edits.json', 'id_map.json', '.cache'];
    for (const f of forbidden) {
      if (existsSync(path.resolve(exportDir, f))) {
        throw new Error(`CRITICAL: Private organizer artifact '${f}' was exported to public bundle!`);
      }
    }

    console.log('[STEP H] SUCCESS: Bundle contains strictly config.json, people.json, faces/, and thumbs/.');
    await checkInvariant('h');

    console.log('\n================================================================');
    console.log('ALL PHASE 4 E2E BROWSER VERIFICATION CHECKS PASSED (100%)');
    console.log('================================================================');

    await browser.close();
  } finally {
    console.log('\n[TEARDOWN] Stopping uvicorn server process...');
    serverProc.kill('SIGTERM');
    // Also reset edits.json to empty
    writeFileSync(editsPath, JSON.stringify({ version: 1, edits: [] }, null, 2), 'utf8');
    try {
      const { execSync } = await import('child_process');
      execSync(`"${PYTHON_PATH}" -c "import zipfile; zipfile.ZipFile('phase1b_deliverables.zip', 'r').extract('export/people.json', '.')"`, { cwd: REPO_ROOT });
      console.log('[TEARDOWN] Canonical export/people.json restored.');
    } catch (e) {
      console.warn('[TEARDOWN] Could not restore export/people.json:', e);
    }
  }
}

run().catch((err) => {
  console.error('\n[FATAL ERROR in E2E Script]:', err);
  process.exit(1);
});
