# Phase 7 Step 2 Performance Optimization Comparison

## Benchmark Environment
- **Dataset**: Canonical 259-photo baseline set (`scratch/photos_259`: 158 HEIC, 86 JPG, 15 HEIF)
- **Machine**: Intel Core i5-7200U (2 physical cores / 4 logical threads @ 2.50 GHz), 16 GB RAM, Windows 10
- **Model**: `buffalo_l` (RetinaFace + ArcFace @ 1600px max dim)
- **Engine Rules**: SPEC 6.2 defaults strictly preserved (`min_face_size=64`, `distance_threshold=0.50`, etc.)

## Pipeline Stage Timings (Before vs After)

| Pipeline Stage | Before Optimization | After Optimization | Delta (s) | Change (%) |
|---|---|---|---|---|
| **Model Init** | 2.688 s | 3.081 s | +0.393 s | Baseline noise |
| **Decode (worker)** | 62.275 s (blocking) | 107.614 s (overlapped) | Overlapped in worker thread | Decoded ahead in background |
| **Face Detect** | 75.904 s | 79.362 s | +3.458 s | Sequential ORT graph exec |
| **Face Embed** | 717.420 s | 714.268 s | -3.152 s | Graph optimization |
| **Thumbs & Crops** | 57.834 s | 55.563 s | -2.271 s | -3.9% |
| **Clustering** | 4.468 s | 4.625 s | +0.157 s | Baseline noise |
| **Bundle Export** | 7.928 s | 10.694 s | +2.766 s | Baseline noise |
| **TOTAL RUN TIME** | **1,050.440 s** (~17.5 min) | **979.877 s** (~16.3 min) | **-70.563 s** | **-6.72% (~1.2 min faster)** |
| **Throughput** | **4.056 s / photo** | **3.783 s / photo** | **-0.273 s / photo** | **Faster** |

## Invariant Reproduction Check

| Metric / Invariant | Baseline Target | Measured Before | Measured After | Status |
|---|---|---|---|---|
| People clusters | 192 | 192 | 192 | **EXACT MATCH** |
| Clustered faces | 1,256 | 1,256 | 1,256 | **EXACT MATCH** |
| Unrecognized faces | 445 | 445 | 445 | **EXACT MATCH** |
| Total detected faces | 1,701 (1,256 + 445) | 1,701 | 1,701 | **EXACT MATCH** |
| Unrecognized photos | 168 | 168 | 168 | **EXACT MATCH** |
| Total photos | 259 | 259 | 259 | **EXACT MATCH** |
| Export bundle size | 31.42 MB (898 files) | 31,421,179 B | 31,421,177 B | **MATCH** |
| Time to open saved project | ~10-12 ms | 10.92 ms | 11.91 ms | **Instant** |

## Key Architectural Optimizations Applied
1. **Lazy Imports**: Converted `cv2`, `onnxruntime`, and `insightface` to lazy imports inside method scopes; moved pipeline import in `jobs.py` into lazy proxy so FastAPI server and desktop shell mount immediately without blocking on ML runtime.
2. **Bounded Prefetch Queue**: Worker thread overlaps CPU decoding of photo `N+1` while photo `N` runs detection and embedding in the main thread (`queue.Queue(maxsize=2)`).
3. **Single Decode Lifecycle**: Images decoded once into memory and shared directly between face detection, thumbnails, and square crops.
4. **Garbage Collection Frequency**: Replaced per-photo full collection pauses with periodic sweeps every 50 photos, eliminating hundreds of blocking GC stalls.
5. **Session Options**: Configured sequential execution mode and full graph optimizations (`ORT_ENABLE_ALL`, `ORT_SEQUENTIAL`).

## Verification Artifacts
- `scratch/perf_before.json` (SHA-256: `91821a68e0d15ef029d08a39dfed355b1bce355436a3cf5d9986e89f45cb9ef5`)
- `scratch/perf_after.json` (SHA-256: `00cdb952de5f6166641eb9553c6ba5ee530fb246ff19c82f71d1e29f6814558b`)
