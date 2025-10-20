# Pampered Pets Attack Tree Analyzer

This repository contains a small, production‑ready Flask application
designed to analyse attack trees/graphs for an MSc assignment.  An
attack tree is a hierarchical model that expresses how a malicious
outcome (the *top event*) can be achieved by combining simpler
sub‑events.  Each internal node is either an **AND** node (all
children must occur) or an **OR** node (any child can occur); leaf
nodes carry an estimated probability of occurrence and an impact value.

The application accepts attack tree specifications in **YAML**, **JSON**
or **XML** formats, visualises the resulting tree, allows you to edit
leaf probabilities and impacts, computes aggregated metrics, and
provides a simple sensitivity analysis tool.  Two demo scenarios
representing pre‑digital and post‑digital retail environments are
included under `data/`.

## Installation & Running

1. **Clone** the repository and navigate into the project directory:

   ```bash
   git clone <this-repo> pampered-pets-attacks
   cd pampered-pets-attacks
   ```

2. **Install** the dependencies using Python 3.11.  It is
   recommended to do this in a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run** the application.  The Flask development server listens on
   port 5000 by default.  The entrypoint is `run.py` which constructs
   the app via an application factory:

   ```bash
   flask --app run run
   # or equivalently
   python run.py
   ```

4. **Open** your browser and navigate to `http://localhost:5000` to
   upload a specification or load a demo scenario.

## Specification Schema

An attack tree specification is a single object with the following
keys:

| Key      | Type                         | Description                                               |
|---------:|:-----------------------------|:----------------------------------------------------------|
| `id`     | string                       | Identifier of the top event (root).                       |
| `label`  | string                       | Human‑readable label for the root.                        |
| `type`   | `AND` / `OR`                 | Node type for the root.                                   |
| `children` | list of strings             | Identifiers of the root's immediate children.             |
| `nodes`  | sequence of node objects     | Definitions of all other nodes (including leaves).        |

Each node object in the `nodes` array contains at minimum an `id`,
`label` and `type`.  For internal nodes (`AND` or `OR`) a `children`
list must be present.  For leaf nodes (`LEAF`) optional `prob` and
`impact` fields may appear; if absent they default to `null`.  The
internal representation normalises all nodes so that every node has
``id``, ``label``, ``type``, ``children`` (empty for leaves),
``prob`` and ``impact``.

## Aggregation Formulas

### Probability of the top event

The probability of an internal node is derived from its children via
well‑known rules:

* **AND node**: the node occurs only if *all* children occur, so
  \(P_{AND} = \prod_i P_i\).
* **OR node**: the node occurs if *any* child occurs.  Equivalently
  the node does *not* occur only if *none* of the children occur, so
  \(P_{OR} = 1 - \prod_i (1 - P_i)\).

Leaf nodes use the `prob` value supplied by the user.  If any leaf
lacks a probability the tool will prompt for input before displaying
aggregated results.

### Expected Loss

The expected loss is the sum of each leaf's probability multiplied by
its impact:

\[\mathrm{E}[L] = \sum_{\text{leaf}} P_{\text{leaf}} \times \mathrm{impact}_{\text{leaf}}\]

Here `impact` is user‑provided and represents the monetary or utility
loss associated with that leaf event.  Missing values will trigger
validation messages.

### Top Contributors

To identify which leaf nodes drive the greatest expected loss, the
tool computes \(P \times \mathrm{impact}\) for each leaf and returns
the top three values in descending order.

## Sensitivity Analysis

A simple sensitivity helper allows you to explore how the top event
probability and expected loss change when you scale a single leaf's
probability by a user‑specified multiplier.  The modified values are
displayed without altering the underlying model; you may choose to
"Apply" the results to update the leaf permanently.  Multipliers are
clamped so that probabilities never exceed 1.0.

## RTO/RPO and Impact Assumptions

Recovery Time Objective (RTO) and Recovery Point Objective (RPO) are
business continuity metrics that guide how long a service can be down
and how much data loss is tolerable.  In the provided demo scenarios
the **impact** values are left unspecified for you to populate based
on assumed RTO/RPO thresholds: higher impacts correspond to longer
outages or more severe data loss.  For example, relying on manual
spreadsheets may lengthen the time to restore operations compared to a
cloud‑hosted e‑commerce platform.  Similarly, hosted or redirect
payment integrations reduce PCI scope but residual risks such as
SQL injection (OWASP A1) or cross‑site scripting (OWASP A7) still need
consideration.  See the OWASP Top 10 and PCI DSS Self‑Assessment
Questionnaire A for further reading.

## Running Tests and Linting

Unit tests live in the `tests/` directory and cover the core logic
functions.  To run them use:

```bash
pytest -q
```

Linting is enforced via **ruff**.  The configuration in `ruff.toml`
enables common checks for code style and correctness.  Run:

```bash
ruff .
```

Alternatively a `Makefile` is provided with convenient targets:

```bash
make install   # install dependencies
make lint      # run linter
make test      # execute unit tests
make run       # start the development server
```

## Directory Structure

The project is organised as follows:

```
pampered-pets-attacks/
  app/            # Flask application package (routing, logic, visualisation)
  data/           # Demo YAML specifications
  static/         # Static assets (CSS, outputs)
  templates/      # Jinja2 templates
  tests/          # Unit tests for parsing and computation
  docs/screens/   # Placeholder for screenshots (empty)
  run.py          # Application entrypoint
  requirements.txt# Python dependencies with pinned versions
  ruff.toml       # Linter configuration
  README.md       # This document
```

## Notes and References

* **OWASP Top 10** – The Open Web Application Security Project
  maintains a list of the most critical web application risks.  See
  the [2021 Top 10](https://owasp.org/www-project-top-ten/) for
  details on SQL injection, cross‑site scripting and other
  vulnerabilities.
* **PCI DSS SAQ A** – The Payment Card Industry Data Security
  Standard Self‑Assessment Questionnaire A applies to merchants that
  outsource cardholder data functions to third parties.  Hosted
  payment forms reduce PCI scope but do not eliminate all risk.

The attack tree model implemented here is intentionally simple and
lives entirely in memory; it is not intended to handle extremely
large graphs.  Contributions and suggestions to improve the tool are
welcome.