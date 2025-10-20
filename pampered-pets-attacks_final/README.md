# Attack Tree Analyzer — Pampered Pets (Unit 6)

A small Flask app to parse, analyze, and visualize **attack‑tree** models for the Pampered Pets SME scenario. It supports YAML/JSON/XML, lets you edit leaf probabilities and impacts in the browser, runs a one‑click sensitivity check, and exports updated specs and images.

---

## ✨ Features

- **Load demos** (Pre‑Digital and Post‑Digital trees) or **Upload** your own spec.
- **Browser editing** of leaf inputs with validation (`prob ∈ [0,1]`, `impact ≥ 0`).
- **KPIs**: top‑event probability `P(top)` and **Expected Loss** `E[L]`.
- **Sensitivity analysis** (implemented): multiply one leaf’s **probability** by a factor `m`; value is **clamped to 1.0**. Preview results then **Apply**.
- **Visualization**: renders a PNG of the tree (Graphviz if available, else a fallback layout) to `app/static/outputs/`.
- **Export**: download the **updated YAML** spec and the latest **PNG** image.
- **Format‑agnostic parser**: YAML/JSON/XML normalized to a single internal structure.
- **Tests + Linting**: basic unit tests for parsing/logic; ruff for style.

---

## 🗂 Project layout

```
pampered-pets-attacks_final/
├─ app/
│  ├─ __init__.py        # create_app() factory, Jinja helpers
│  ├─ routes.py          # upload, analyze, sensitivity, downloads
│  ├─ model.py           # parsing + P(top) + E[L] + top contributors
│  ├─ viz.py             # PNG rendering to static/outputs/
│  ├─ templates/         # base.html, index.html, analyze.html
│  └─ static/            # css + generated outputs
├─ data/                 # demo specs: pre_digital.yaml, post_digital.yaml
├─ screenshots/          # figures for the report/README
├─ tests/                # test_parser.py, test_logic.py
├─ requirements.txt
├─ ruff.toml
├─ Makefile
└─ run.py
```

---

## ▶️ Quick start

> Requires **Python 3.10+**.

```bash
# 1) Create & activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

# 2) Install deps
pip install -r requirements.txt

# 3) Run (pick one)
# a) Flask dev server via factory
set FLASK_APP=app:create_app   # (Windows)
flask run --reload
# macOS/Linux:
# export FLASK_APP=app:create_app && flask run --reload

# b) Convenience script
python run.py
```

Open http://localhost:5000 and **Upload** a spec or **Load Pre/Post Demo**.

---

## 🧮 What the app computes

**Node semantics**

- **AND**:  $P_{\text{AND}} = \prod_j P(\text{child}_j)$
- **OR**:   $P_{\text{OR}} = 1 - \prod_j (1 - P(\text{child}_j))$

**Top event**

- Apply the same AND/OR rules from leaves to the **root** to get $P(\text{top})$.

**Expected monetary loss**

- $\mathbb{E}[L] = \sum_{i \in \text{leaves}} p_i \; I_i$

**Sensitivity (as implemented in the app)**

- Pick a **leaf** $k$ and a multiplier $m$. The app uses  
  $p'_k = \min(1,\, m\, p_k)$  
  Then it recomputes $P(\text{top})$ and $\mathbb{E}[L]$. (Impact-side scaling is shown in the UI help for completeness, but the current implementation **modifies probability only**.)

---

## 📄 Spec format (YAML/JSON/XML)

All formats are normalized to:
```yaml
id: <root-id>
label: <root-label>
type: AND|OR|LEAF
children: [child-id, ...]
nodes:
  - { id, label, type, children?, prob?, impact? }
```

**Minimal YAML example**
```yaml
id: root
label: Business loss at Pampered Pets
type: OR
children: [op_risk, cyber]
nodes:
  - { id: op_risk, label: Operational risks, type: AND, children: [power_out, hdd_fail] }
  - { id: cyber,   label: Cyber risks,       type: OR,  children: [fd_ransom, weak_cfg] }
  - { id: power_out, label: Power outage, type: LEAF, prob: 0.30, impact: 8000 }
  - { id: hdd_fail,  label: Old HDD fails, type: LEAF, prob: 0.01, impact: 12000 }
  - { id: fd_ransom, label: Ransomware,   type: LEAF, prob: 0.50, impact: 180000 }
  - { id: weak_cfg,  label: Weak Wi‑Fi,   type: LEAF, prob: 0.60, impact: 60000 }
```

**Validation rules**
- `prob` must be in `[0,1]`; `impact` must be `≥ 0`.
- All `children` must reference existing node `id`s.
- Exactly one node acts as the **root** (`id` in the top‑level fields).

---

## 🧭 Using the UI

1. **Home to Upload & Analyze**: choose `.yaml/.yml/.json/.xml` or click **Load Pre/Post Demo**.
2. **Edit leaves**: update `prob` and `impact` inline, click **Recalculate** to see KPIs.
3. **Sensitivity**: select a leaf + multiplier `m` → **Run Sensitivity** → **Apply** to persist.
4. **Visualization**: the tree PNG is regenerated on analyze; files are saved in `app/static/outputs/`.
5. **Download**: get the **Updated Spec (YAML)** and the **PNG** from the analyze page.

---

## 🧪 Tests & linting

```bash
# Run unit tests
pytest -q

# Lint (ruff)
ruff check .
```

Logic is covered by `tests/test_parser.py` and `tests/test_logic.py`.

---

## 🖼 Screenshots

- `./screenshots/pre-digital-attack-tree.png`
- `./screenshots/post-digital-attack-tree.png`
- `./screenshots/pre-digital-calculation-python-application-ui.png`
- `./screenshots/post-digital-calculation-python-application-ui.png`

---

## 🔎 Notes & assumptions

- **Independence assumption**: leaf events are independent unless modeled otherwise.
- **Graphviz optional**: if not installed, the app falls back to a non‑Graphviz layout.
- **YAML export**: the server serializes in‑memory and streams as `text/yaml`.
- **Data sources**: the demo specs live in `data/pre_digital.yaml` and `data/post_digital.yaml` and can be edited during analysis.

---

## 📦 License

Academic/learning use. Replace with your license if publishing.
