# CatLog Offline Model Pack Guide & Licensing Compliance

CatLog uses InsightFace deep learning models (`buffalo_l`) for face detection (SCRFD detector) and 512-dimensional embedding extraction (ArcFace ResNet50).

In air-gapped event environments, slow internet connections, or private institutional deployments, you can prepare and install the model weights completely offline.

---

## 1. InsightFace Model Licensing Notice

> [!IMPORTANT]
> **Non-Commercial License Restriction**:
> The pre-trained ONNX models distributed in InsightFace's model zoo (`buffalo_l.zip`) are provided strictly under InsightFace's non-commercial research and educational license.
> - **Redistribution Policy**: CatLog application release archives **DO NOT bundle the model weights directly** inside the git repository or release zip to honor licensing agreements.
> - **End-User Responsibility**: Users download or provide the weights for their own private use. Commercial deployments must use appropriately licensed or custom-trained facial detection/embedding models.

---

## 2. Model Specifications & Verification Hashes

CatLog strictly verifies the file size and cryptographic SHA-256 hash of all 5 required ONNX models before running inference:

| Model Filename | Role | Exact File Size | SHA-256 Digest |
| :--- | :--- | :--- | :--- |
| `1k3d68.onnx` | 3D Face Alignment | 143,607,619 bytes | `df5c06b8a0c12e422b2ed8947b8869faa4105387f199c477af038aa01f9a45cc` |
| `2d106det.onnx` | 2D 106-Point Landmarks | 5,030,888 bytes | `f001b856447c413801ef5c42091ed0cd516fcd21f2d6b79635b1e733a7109dbf` |
| `det_10g.onnx` | SCRFD 10G Face Detector | 16,923,827 bytes | `5838f7fe053675b1c7a08b633df49e7af5495cee0493c7dcf6697200b85b5b91` |
| `genderage.onnx` | Attribute Classifier | 1,322,532 bytes | `4fde69b1c810857b88c64a335084f1c3fe8f01246c9a191b48c7bb756d6652fb` |
| `w600k_r50.onnx` | ResNet50 ArcFace Embeddings | 174,383,860 bytes | `4c06341c33c2ca1f86781dab0e829f88ad5b64be9fba56e56bc9ebdefc619e43` |
| **Total Model Archive** | **`buffalo_l.zip`** | **288,621,354 bytes (~275 MB)** | — |

---

## 3. Offline Installation Instructions

### Option A: App-Adjacent Folder (Recommended for Portable USB Drives)
Place the 5 extracted `.onnx` files into a `models/buffalo_l/` or `catlog_models/buffalo_l/` folder right next to `CatLog.exe` (or the repository root):

```text
CatLog/
├── CatLog.exe
├── LICENSE
├── README.md
└── models/
    └── buffalo_l/
        ├── 1k3d68.onnx
        ├── 2d106det.onnx
        ├── det_10g.onnx
        ├── genderage.onnx
        └── w600k_r50.onnx
```

### Option B: User Profile Directory
Copy the files into your local user home directory:
- **Windows**: `C:\Users\<YourUsername>\.photosorter\models\buffalo_l\` (or `%USERPROFILE%\.insightface\models\buffalo_l\`)
- **macOS / Linux**: `~/.photosorter/models/buffalo_l/` (or `~/.insightface/models/buffalo_l/`)

---

## 4. Download Sources (Official Mirrors)

If downloading from another internet-connected device:
1. **Official InsightFace Release**:
   `https://github.com/deepinsight/insightface/releases/download/model-zoo/buffalo_l.zip`
2. **Hugging Face Public Mirror**:
   `https://huggingface.co/public-data/insightface-models/resolve/main/buffalo_l.zip`

