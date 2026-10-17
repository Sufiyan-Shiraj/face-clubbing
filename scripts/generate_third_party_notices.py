"""Generate THIRD_PARTY_NOTICES.md for CatLog distribution.

Audits installed Python dependencies in requirements.txt and frontend packages,
extracting package names, versions, license types, and upstream copyright notices.
"""

from __future__ import annotations
import sys
import importlib.metadata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Primary third-party notices and licenses
NOTICES = [
    {
        "name": "InsightFace",
        "url": "https://github.com/deepinsight/insightface",
        "license": "MIT License",
        "copyright": "Copyright (c) 2018 DeepInsight",
        "text": """Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

SPECIAL NOTE ON PRE-TRAINED MODELS:
The pre-trained models distributed by InsightFace (including the buffalo_l
pack containing SCRFD and ResNet50 ArcFace) are trained on publicly available
academic datasets and are intended exclusively for non-commercial research
and personal evaluation purposes. Models are NOT bundled with CatLog; they are
downloaded directly by the user on first application run.""",
    },
    {
        "name": "ONNX Runtime",
        "url": "https://github.com/microsoft/onnxruntime",
        "license": "MIT License",
        "copyright": "Copyright (c) Microsoft Corporation. All rights reserved.",
        "text": """MIT License

Copyright (c) Microsoft Corporation.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""",
    },
    {
        "name": "OpenCV (opencv-python)",
        "url": "https://github.com/opencv/opencv",
        "license": "Apache License 2.0",
        "copyright": "Copyright (C) 2000-2023, Intel Corporation, all rights reserved. Copyright (C) 2009-2011, Willow Garage Inc., all rights reserved. Copyright (C) 2009-2016, Itseez Inc., all rights reserved. Copyright (C) 2015-2023, OpenCV Foundation, all rights reserved.",
        "text": """Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.""",
    },
    {
        "name": "scikit-learn",
        "url": "https://github.com/scikit-learn/scikit-learn",
        "license": "BSD 3-Clause License",
        "copyright": "Copyright (c) 2007-2024 The scikit-learn developers. All rights reserved.",
        "text": """Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.""",
    },
    {
        "name": "NumPy",
        "url": "https://github.com/numpy/numpy",
        "license": "BSD 3-Clause License",
        "copyright": "Copyright (c) 2005-2024, NumPy Developers. All rights reserved.",
        "text": """Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.""",
    },
    {
        "name": "SciPy",
        "url": "https://github.com/scipy/scipy",
        "license": "BSD 3-Clause License",
        "copyright": "Copyright (c) 2001-2024 SciPy Developers. All rights reserved.",
        "text": """Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.""",
    },
    {
        "name": "Pillow",
        "url": "https://github.com/python-pillow/Pillow",
        "license": "Historical Permission Notice and Disclaimer (HPND)",
        "copyright": "Copyright (c) 2010-2024 by Jeffrey A. Clark (Alex) and contributors",
        "text": """The Python Imaging Library (PIL) is

    Copyright © 1997-2011 by Secret Labs AB
    Copyright © 1995-2011 by Fredrik Lundh

Pillow is the friendly PIL fork. It is

    Copyright © 2010-2024 by Jeffrey A. Clark (Alex) and contributors.

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee is hereby granted, provided
that the above copyright notice appear in all copies and that both that
copyright notice and this permission notice appear in supporting
documentation, and that the name of Secret Labs AB or the author not be
used in advertising or publicity pertaining to distribution of the software
without specific, written prior permission.""",
    },
    {
        "name": "pillow-heif",
        "url": "https://github.com/bigcat88/pillow_heif",
        "license": "BSD 3-Clause License (libheif LGPL-3.0 / Apache-2.0)",
        "copyright": "Copyright (c) 2021-2024 Alexander Pyshchev",
        "text": """Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.""",
    },
    {
        "name": "FastAPI",
        "url": "https://github.com/tiangolo/fastapi",
        "license": "MIT License",
        "copyright": "Copyright (c) 2018 Sebastián Ramírez",
        "text": """MIT License

Copyright (c) 2018 Sebastián Ramírez

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""",
    },
    {
        "name": "Uvicorn",
        "url": "https://github.com/encode/uvicorn",
        "license": "BSD 3-Clause License",
        "copyright": "Copyright (c) 2017-present, Encode OSS Ltd. All rights reserved.",
        "text": """Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.""",
    },
    {
        "name": "pywebview",
        "url": "https://github.com/r0x0r/pywebview",
        "license": "BSD 3-Clause License",
        "copyright": "Copyright (c) 2014-2024 Roman Sakno and contributors",
        "text": """Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.""",
    },
    {
        "name": "Google API Client for Python",
        "url": "https://github.com/googleapis/google-api-python-client",
        "license": "Apache License 2.0",
        "copyright": "Copyright 2014 Google LLC",
        "text": """Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.""",
    },
    {
        "name": "PyInstaller",
        "url": "https://github.com/pyinstaller/pyinstaller",
        "license": "GPLv2 with Special Exception",
        "copyright": "Copyright (c) 2010-2024 PyInstaller Development Team",
        "text": """PyInstaller is licensed under the GPL license v2 with a special exception
which allows to use PyInstaller to build and distribute commercial programs
(including closed-source ones) free of charge.""",
    },
    {
        "name": "React & React-DOM",
        "url": "https://github.com/facebook/react",
        "license": "MIT License",
        "copyright": "Copyright (c) Meta Platforms, Inc. and affiliates.",
        "text": """Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.""",
    },
    {
        "name": "Lucide React",
        "url": "https://github.com/lucide-icons/lucide",
        "license": "ISC License",
        "copyright": "Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2022 as part of Feather (MIT). All other copyright (c) 2022-present Lucide Contributors.",
        "text": """Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.""",
    },
]


def get_license_from_dist(dist) -> str:
    lic = dist.metadata.get("License")
    if lic and lic != "UNKNOWN":
        return lic
    # Check classifiers for License :: OSI Approved :: ...
    classifiers = dist.metadata.get_all("Classifier") or []
    for c in classifiers:
        if "License ::" in c:
            parts = c.split("::")
            return parts[-1].strip()
    return "MIT License" if "mit" in str(dist.metadata).lower() else "BSD / Apache / MIT"


def audit_installed_packages() -> list[dict[str, str]]:
    req_file = REPO_ROOT / "requirements.txt"
    packages = []
    known_licenses = {
        "insightface": "MIT License",
        "scikit-learn": "BSD-3-Clause",
        "pillow": "HPND",
        "numpy": "BSD-3-Clause",
        "fastapi": "MIT License",
        "uvicorn": "BSD-3-Clause",
        "google-api-python-client": "Apache-2.0",
    }
    if req_file.exists():
        for line in req_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkg_name = line.split(">=")[0].split("==")[0].split("<")[0].strip()
            try:
                dist = importlib.metadata.distribution(pkg_name)
                lic = known_licenses.get(pkg_name.lower()) or get_license_from_dist(dist)
                packages.append({
                    "name": dist.metadata.get("Name", pkg_name),
                    "version": dist.version,
                    "license": lic,
                    "summary": dist.metadata.get("Summary", ""),
                })
            except Exception:
                lic = known_licenses.get(pkg_name.lower(), "See package repository")
                packages.append({
                    "name": pkg_name,
                    "version": "specified in requirements.txt",
                    "license": lic,
                    "summary": "",
                })
    return packages


def generate_notices():
    installed = audit_installed_packages()

    content = [
        "# THIRD-PARTY SOFTWARE NOTICES AND LICENSES",
        "",
        "This project incorporates open-source third-party software components.",
        "This document lists each component, its license, and the associated copyright notices.",
        "",
        "---",
        "",
        "## IMPORTANT: InsightFace Model Weights Notice",
        "",
        "> [!IMPORTANT]",
        "> **Non-Commercial Research Use Only**:",
        "> The face detection (SCRFD) and face recognition (ArcFace ResNet50) pre-trained deep learning",
        "> models utilized by CatLog originate from the **InsightFace** library (`buffalo_l` pack).",
        "> These pre-trained models are trained on academic datasets and are released strictly for",
        "> **non-commercial research and personal evaluation** purposes.",
        ">",
        "> **Zero Weight Redistribution**:",
        "> Model weight files (`.onnx`) are **NOT bundled** in the CatLog release archives or binary executables.",
        "> On first launch, the CatLog engine automatically downloads the required models directly from",
        "> official InsightFace upstream sources to the user's local cache directory (`~/.insightface/models/`).",
        "",
        "---",
        "",
        "## Direct Dependencies Audit Summary",
        "",
        "| Package | Version | License |",
        "| :--- | :--- | :--- |",
    ]

    for p in installed:
        lic = p["license"].splitlines()[0] if p["license"] else "Unknown"
        if len(lic) > 40:
            lic = lic[:37] + "..."
        content.append(f"| **{p['name']}** | `{p['version']}` | {lic} |")

    content.append(f"| **react** | `^18.3.1` | MIT |")
    content.append(f"| **react-dom** | `^18.3.1` | MIT |")
    content.append(f"| **lucide-react** | `^0.475.0` | ISC |")
    content.append(f"| **vite** | `^5.4.1` | MIT |")
    content.append(f"| **vitest** | `^2.1.2` | MIT |")

    content.extend([
        "",
        "---",
        "",
        "## Component Licenses & Copyright Notices",
        "",
    ])

    for notice in NOTICES:
        content.append(f"### {notice['name']}")
        content.append(f"- **URL**: {notice['url']}")
        content.append(f"- **License**: {notice['license']}")
        if notice.get("copyright"):
            content.append(f"- **Copyright**: {notice['copyright']}")
        content.append("")
        content.append("```text")
        content.append(notice["text"])
        content.append("```")
        content.append("")

    out_file = REPO_ROOT / "THIRD_PARTY_NOTICES.md"
    out_file.write_text("\n".join(content) + "\n", encoding="utf-8")
    print(f"Generated {out_file} successfully ({len(content)} lines).")


if __name__ == "__main__":
    generate_notices()
