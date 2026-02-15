# 🎯 Palace Mental - Quick Reference Cheat Sheet

Quick visual reference for using Palace Mental efficiently.

---

## 🚀 Essential Commands

```bash
# BASIC FLOW
poetry run palace init                                    # First time
poetry run palace ingest                                  # Load code
poetry run palace context src/file.py                     # View context
poetry run palace sleep                                   # Weekly maintenance

# USEFUL VARIANTS
poetry run palace ingest --file-pattern "src/**/*.py"    # Specific pattern
poetry run palace context src/file.py --compact           # One line
poetry run palace context src/file.py -o /tmp/ctx.md      # Save to file
poetry run palace query "MATCH (n) RETURN COUNT(n)"       # Cypher query
poetry run palace stats                                   # Graph statistics
```

---

## 📊 Output Interpretation

### File Context Output

```
## 🏛️ Architectural Context (Palace Mental)
**Seed**: `src/auth.py` | **Activation**: 12.46 | **Risk**: 0.15

### ⚠️ Active Invariants
• [🔴 CRITICAL] `no_eval`                → DO NOT USE eval()
• [🟠 HIGH] `sql_injection_risk`         → Use parameterization

### 🔗 Local Topology
📥 Depends on:    tests/test_auth.py, config/settings.py
📤 Impacts:       api/routes.py, middleware/auth.py
🔗 Related:       utils/crypto.py

### 🧠 Active Concepts
Security Authentication  ██████████ 1.00  (core concept)
Security Tokens          █████████░ 0.92  (very related)
Pattern Middleware       ████████░░ 0.80  (used pattern)

### 📜 Historical Memory
• [2024-01-10] ADR-001: Use JWT
  ↳ Status: accepted | Reason: Stateless

### 🎯 Risk Assessment
🟡 Risk: Medium (0.15)
⚠️  2 active invariants
💡 Review security rules before modifying
```

### Emoji Meanings

| Emoji | Meaning | Action |
|-------|---------|--------|
| 🔴 | CRITICAL | Fix before any change |
| 🟠 | HIGH | Review carefully |
| 🟡 | MEDIUM | Consider in refactoring |
| 🟢 | LOW | Good state |
| 📥 | Depends on | These files will be affected |
| 📤 | Impacts | Changes affect these files |
| ⚠️ | Warning | Pay attention |
| 💡 | Recommendation | Suggested action |

---

## 🧮 Statistics Quick Guide

### Nodes

```
Artifacts:  90  → Codebase size
Concepts:   34  → Semantic richness
Invariants: 2   → Detected problems (0 = ideal)
Decisions:  3   → Decision documentation
```

### Edges

```
EVOKES:      570  → Semantic associations (high = good)
DEPENDS_ON:  165  → Dependency graph
CONSTRAINS:  3    → Active restrictions (low = good)
RELATED_TO:  0    → Learned via Hebbian (grow with use)
```

### Derived Metrics

| Metric | Range | Good | Bad |
|--------|-------|------|-----|
| **Risk Score** | 0.0 - 1.0 | < 0.3 🟢 | > 0.6 🔴 |
| **Activation** | 0 - ∞ | 5-20 | < 5 (isolated) |
| **Hops** | 1, 2, 3... | 2-3 | > 4 (irrelevant) |

---

## 🎯 Use Cases - Recipes

### 1️⃣ Safe Refactoring

```bash
# BEFORE changing code
poetry run palace context src/component.py

# Look for in output:
# • 📤 "Impacts" → List of affected files
# • 🎯 "Risk" → If 🔴, write tests first
# • ⚠️ Invariants → Do not violate detected rules
```

**What to check:**
- High connectivity? → Write integration tests
- CRITICAL invariants? → Must not violate
- High risk score? → Review dependencies first

### 2️⃣ Quick Onboarding

```bash
# New dev needs to understand a module
poetry run palace context src/payment/gateway.py --compact

# Gets:
# • 🧠 Domain concepts
# • 📜 Relevant ADRs (rules of the game)
# • 🔗 Related files
```

**Benefits:**
- See architectural context in seconds
- Understand dependencies immediately
- Know what rules to follow

### 3️⃣ Code Review

```bash
# For each file in the PR
poetry run palace context file.py >> review.md

# Review:
# • 🔴🟠 Invariants → Security
# • 📜 ADRs → Following architectural decisions?
# • 🎯 Risk → Needs additional tests?
```

**Checklist:**
- [ ] No CRITICAL invariants violated
- [ ] Low risk score (< 0.3)
- [ ] Follows architectural decisions
- [ ] Properly handles dependencies

### 4️⃣ Prompt for Claude

```bash
# Prepare context
poetry run palace context src/feature.py -o /tmp/ctx.md
cat /tmp/ctx.md | xclip -selection clipboard

# In Claude:
# [Paste context]
# "Implement X considering the detected invariants"
```

**Example prompt:**
```
[Context from Palace]

I need to add rate limiting to this API endpoint.
Given that:
- Risk score is 0.2 (low)
- Depends on database connection
- Related to authentication concepts

What's the best approach to add rate limiting
without breaking existing authentication logic?
```

### 5️⃣ Detect Problems

```bash
# View all problems
poetry run palace query "MATCH (i:Invariant) RETURN i.rule, i.severity"

# Most problematic files
poetry run palace query "MATCH (i:Invariant)-[:CONSTRAINS]->(a:Artifact) \
              RETURN a.path, COUNT(i) as problems \
              ORDER BY problems DESC"

# Files without tests
poetry run palace query "MATCH (a:Artifact) WHERE NOT a.path CONTAINS 'test' \
              AND a.language = 'python' RETURN a.path"
```

---

## 📝 ADR Template

Create in `.palace/decisions/XXX-name.md`:

```markdown
---
date: 2024-02-15
status: accepted  # proposed | accepted | deprecated | superseded
---

# ADR-XXX: Descriptive title

## Context
What problem are we solving?

## Decision
What did we decide?

## Consequences
✅ Positives
⚠️ Negatives / Trade-offs

## Alternatives Rejected
- Option A: Why not
- Option B: Why not
```

**After creating ADR:**
```bash
poetry run palace ingest  # Reload decisions
```

---

## 🔍 Useful Cypher Queries

### List files by concept

```bash
poetry run palace query "MATCH (a:Artifact)-[:EVOKES]->(c:Concept {name: 'Authentication'}) RETURN a.path"
```

### Find circular dependencies

```bash
poetry run palace query "MATCH (a:Artifact)-[:DEPENDS_ON]->(b:Artifact)-[:DEPENDS_ON]->(a) RETURN a.path, b.path"
```

### Files with most dependencies

```bash
poetry run palace query "MATCH (a:Artifact)-[r:DEPENDS_ON]->() RETURN a.path, COUNT(r) as deps ORDER BY deps DESC LIMIT 10"
```

### Most frequent concepts

```bash
poetry run palace query "MATCH (c:Concept)<-[:EVOKES]-(a:Artifact) RETURN c.name, COUNT(a) as freq ORDER BY freq DESC LIMIT 10"
```

### Find security issues

```bash
poetry run palace query "MATCH (i:Invariant) WHERE i.severity = 'CRITICAL' RETURN i.rule, i.severity"
```

---

## ⚡ Troubleshooting

| Problem | Solution |
|---------|----------|
| `palace: command not found` | Use `poetry run palace` or `pip install -e .` |
| Empty context | Run `poetry run palace ingest --force` |
| No concepts detected | `poetry add sentence-transformers` |
| Ingestion very slow | Check `.gitignore` excludes `node_modules/`, etc. |
| Kuzu errors | `rm -rf .palace/ && palace init && palace ingest` |
| Import errors | Run `poetry install` |

---

## 📅 Maintenance Calendar

| Frequency | Command | Purpose |
|-----------|---------|---------|
| **Daily** | `palace context <file>` | Before editing files |
| **Weekly** | `palace sleep` | Consolidate and clean graph |
| **Monthly** | `palace ingest --force` | Complete re-sync |
| **Per PR** | `palace context <changes>` | Informed code review |

---

## 🎨 Visual Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR PROJECT                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  palace init                                                │
│  └── Creates .palace/ (brain.kuzu, vectors.db)             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  palace ingest                                              │
│  └── Scans code → Extracts concepts → Loads ADRs           │
│      └── 90 artifacts, 570 concepts, 3 decisions...        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  palace context src/x.py                                    │
│  └── Spreading Activation → Markdown Context               │
│      └── Invariants, ADRs, Concepts, Risk...               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Use in Claude Code / OpenCode                              │
│  └── Paste context + Your question                          │
│      └── AI responds with architectural context            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  palace sleep (weekly)                                      │
│  └── Decay → Prune → Consolidation → Hebbian               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Risk Score Guide

### 🟢 Low Risk (0.0 - 0.3)
- Safe to modify
- No critical invariants
- Few dependencies
- **Action**: Proceed with normal development

### 🟡 Medium Risk (0.3 - 0.6)
- Some invariants active
- Moderate connectivity
- **Action**: Review invariants, write tests

### 🔴 High Risk (0.6 - 1.0)
- Critical invariants present
- High connectivity
- Possible violations
- **Action**: Extensive testing required, review with team

---

## 💡 Productivity Tips

### Before Editing
```bash
palace context src/feature.py --compact
# Quick sanity check
```

### Before Committing
```bash
for file in $(git diff --name-only); do
  palace context $file | grep -E "CRITICAL|HIGH"
done
# Check for critical issues
```

### Before Refactoring
```bash
palace context src/old_module.py
# Check what depends on it
palace query "MATCH (a)-[:DEPENDS_ON]->(b:Artifact) WHERE b.path = 'src/old_module.py' RETURN a.path"
```

### During Onboarding
```bash
# Map out the architecture
for file in src/**/*.py; do
  palace context $file --compact
done | sort | uniq
```

---

## 🚀 Shortcut

Save this page as a quick reference while using Palace.

**📚 Complete documentation:**
- [GLOSSARY.md](GLOSSARY.md) - Understand all concepts
- [TUTORIAL.md](TUTORIAL.md) - Deep dive tutorial
- [DEMO.md](DEMO.md) - Real execution examples
- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup

---

**🧠 Remember**: Palace is your cognitive memory assistant. Use it before every coding session for maximum benefit!
