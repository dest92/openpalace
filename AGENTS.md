# 🤖 Palace Mental - Integration Guide for AI Agents

Guide for integrating Palace Mental with AI coding assistants (Claude Code, OpenCode, Cursor, etc.).

---

## 🎯 Purpose

Palace acts as a **context provider** for AI agents, giving them architectural awareness of your codebase. This prevents AI from making mistakes that violate architectural rules or break dependencies.

---

## 🔄 How It Works

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   AI Agent  │ ──────> │   Palace    │ ──────> │  Knowledge  │
│ (Claude/Open)│ Query  │   Context   │  Query  │   Graph     │
└─────────────┘         └─────────────┘         └─────────────┘
                                │
                                ▼
                        ┌─────────────┐
                        │   Structured│
                        │  Context    │
                        └─────────────┘
                                │
                                ▼
                        ┌─────────────┐
                        │  Informed   │
                        │   Response  │
                        └─────────────┘
```

---

## 🚀 Quick Integration

### Method 1: Manual (Recommended for Development)

```bash
# 1. Get context for the file you're working on
poetry run palace context src/auth.py -o /tmp/context.md

# 2. Copy to clipboard
cat /tmp/context.md | xclip -selection clipboard  # Linux
pbcopy < /tmp/context.md  # Mac

# 3. In AI assistant:
#    - Paste context
#    - Ask your question
```

### Method 2: Script-Based (For Automation)

Create `get_context.sh`:
```bash
#!/bin/bash
FILE=$1
poetry run palace context "$FILE" -o /tmp/palace_context.md
cat /tmp/palace_context.md
```

Usage:
```bash
./get_context.sh src/auth.py | pbcopy
```

### Method 3: Direct Integration (For AI Tool Builders)

```python
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.api.context import ContextProvider
from palace.formatters.claude import ClaudeFormatter

def get_architectural_context(file_path: str, repo_root: str = ".") -> str:
    """
    Get architectural context for a file.

    Returns formatted Markdown ready for AI consumption.
    """
    palace_dir = Path(repo_root) / ".palace"

    with Hippocampus(palace_dir) as hippo:
        provider = ContextProvider(hippo)
        ctx = provider.get_context_for_file(file_path)

        # Convert to ContextBundle
        bundle = create_context_bundle(ctx, file_path)

        # Format for AI
        formatter = ClaudeFormatter()
        return formatter.format(bundle)

# Usage
context = get_architectural_context("src/auth.py")
print(context)  # Feed this to AI
```

---

## 📝 Example Prompts with Palace Context

### Scenario 1: Implementing a New Feature

**Without Palace:**
```
"Add OAuth2 authentication to the login system."
```
**AI might:** Break existing auth, miss dependencies, violate patterns

**With Palace:**
```
[Paste Palace context for src/auth/login.py]

"Add OAuth2 authentication to the login system.
Considering:
- Current risk score: 0.15 (low)
- Depends on: database/connection.py
- Related concepts: Authentication, Security
- No active invariants

How should I integrate OAuth2 without breaking
the existing authentication flow?"
```
**AI will:** Consider dependencies, maintain architecture, follow patterns

### Scenario 2: Refactoring

**Without Palace:**
```
"Refactor the database module to use connection pooling."
```
**AI might:** Break dependent code, miss edge cases

**With Palace:**
```
[Paste Palace context for src/database/connection.py]

"I want to add connection pooling.
Current state:
- Impacts: src/auth/login.py, src/api/routes.py
- Risk: High (0.65)
- 2 CRITICAL invariants active

What's the safest approach to add pooling
without breaking the 2 files that depend on this?"
```
**AI will:** Suggest gradual migration, maintain compatibility

### Scenario 3: Code Review

**Without Palace:**
```
"Review this PR for issues."
```
**AI might:** Miss architectural violations

**With Palace:**
```
[Paste Palace context for all changed files]

"Review these changes considering:
- File 1: Risk 0.2, no invariants
- File 2: Risk 0.8, 2 CRITICAL invariants
- File 3: Risk 0.4, 1 HIGH invariant

Focus particularly on File 2 which has
CRITICAL invariants for eval() and SQL injection."
```
**AI will:** Prioritize critical issues, check rule violations

### Scenario 4: Bug Fixing

**Without Palace:**
```
"Fix the bug in the payment module."
```
**AI might:** Not understand context, introduce regressions

**With Palace:**
```
[Paste Palace context for src/payment/gateway.py]

"Bug: Payment fails when user has multiple cards.
Context:
- Depends on: database/connection.py, utils/encryption.py
- Impacts: api/checkout.py
- Concepts: Payment Processing, Transaction Management

The bug happens when processing the second card.
Given the architecture, where should I look first?"
```
**AI will:** Check transaction handling, database connections, encryption

---

## 🎯 Best Practices for AI Prompts

### DO ✅

1. **Always include context before asking**
   ```
   [Palace context for src/module.py]
   [Your question]
   ```

2. **Reference specific invariants**
   ```
   "The context shows a CRITICAL invariant for eval() usage.
   How can I implement this feature WITHOUT using eval()?"
   ```

3. **Consider dependencies**
   ```
   "Given that src/auth.py depends on database/connection.py,
   how should I structure the new feature?"
   ```

4. **Acknowledge risk level**
   ```
   "This file has HIGH risk (0.7). What extra precautions
   should I take before modifying it?"
   ```

5. **Use concepts in your question**
   ```
   "The file evokes 'Authentication' and 'Security' concepts.
   Does my proposed change align with these concepts?"
   ```

### DON'T ❌

1. **Don't ignore invariants**
   ```
   ❌ "Disable the eval() check temporarily"
   ✅ "How can I achieve this without eval()?"
   ```

2. **Don't skip dependencies**
   ```
   ❌ "Just refactor this file in isolation"
   ✅ "Refactor this considering its 3 dependents"
   ```

3. **Don't disregard architecture**
   ```
   ❌ "Add the feature wherever fits"
   ✅ "Where should this fit given the current architecture?"
   ```

---

## 🔧 Integration Examples

### Claude Code (VS Code)

Add to `.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Palace: Get Context",
      "type": "shell",
      "command": "poetry run palace context ${file} -o /tmp/ctx.md && cat /tmp/ctx.md",
      "problemMatcher": []
    },
    {
      "label": "Palace: Compact Context",
      "type": "shell",
      "command": "poetry run palace context ${file} --compact",
      "problemMatcher": []
    }
  ]
}
```

**Workflow:**
1. Open file in VS Code
2. Run `Palace: Get Context` task
3. Copy output
4. Paste in Claude Code + your question

### Cursor IDE

Create `.cursor/rules/palace_context.rule`:
```python
function getPalaceContext(filePath) {
    // Shell out to palace
    const result = shell.exec(`poetry run palace context ${filePath} --compact`);
    return result.stdout;
}

// In your prompt
const context = getPalaceContext(filePath);
return `
${context}

Given this architectural context, please help me with:
${userQuestion}
`;
```

### OpenCode

Similar to Claude Code, use tasks or keybindings:
```json
{
  "key": "ctrl+shift+p",
  "command": "workbench.action.tasks.runTask",
  "args": "Palace: Get Context"
}
```

---

## 📊 Understanding Palace Output

### Key Fields for AI Agents

| Field | AI Usage | Example |
|-------|----------|---------|
| **seed_file** | Current working file | `src/auth.py` |
| **risk_score** | Caution level | 0.8 → Be careful |
| **invariants** | Rules to follow | Don't use eval() |
| **depends_on** | What will break | 3 files affected |
| **impacts** | What depends on this | 5 files need updates |
| **concepts** | Domain context | Authentication, Security |
| **decisions** | ADRs to follow | Use JWT, not sessions |

### Interpreting Risk Scores

```python
if risk_score > 0.7:
    # AI should:
    # - Suggest extensive testing
    # - Recommend gradual approach
    # - Highlight all invariants
    # - Check all dependencies
elif risk_score > 0.4:
    # AI should:
    # - Mention key invariants
    # - Note main dependencies
    # - Suggest testing strategy
else:
    # AI should:
    # - Proceed normally
    # - Still check invariants
    # - Note dependencies briefly
```

---

## 🎓 Advanced Usage

### Multi-File Context

```bash
# Get context for multiple files
for file in src/auth/*.py; do
  poetry run palace context $file --compact
done > /tmp/full_context.md

# Feed to AI for module-level questions
```

### Diff-Based Context

```bash
# Get context only for changed files
git diff --name-only HEAD | while read file; do
  echo "## Context for $file"
  poetry run palace context "$file" --compact
done > /tmp/pr_context.md
```

### Historical Decision Awareness

```python
# AI should check ADRs before suggesting changes
if "ADR-001: Use JWT" in context:
    # Don't suggest session-based auth
    # Work within JWT decision
```

---

## 🤖 AI Agent Behavior Guidelines

### When Receiving Palace Context

1. **Always read invariants first**
   - CRITICAL: Must not violate
   - HIGH: Should review
   - MEDIUM: Consider

2. **Check dependencies before suggesting changes**
   - What depends on this file?
   - What does this file depend on?
   - Will changes break anything?

3. **Consider risk score**
   - High risk → Suggest testing, review, gradual approach
   - Low risk → Can proceed more confidently

4. **Respect architectural decisions**
   - Check ADRs section
   - Don't contradict past decisions without mentioning it
   - Suggest updating ADR if architecture should change

5. **Use concepts for domain understanding**
   - If file evokes "Security", prioritize security
   - If "Authentication", consider auth flow
   - Match implementation to concepts

### Example AI Response Pattern

```python
def generate_response(palace_context, user_question):
    # 1. Analyze invariants
    critical = [i for i in palace_context.invariants if i.severity == "CRITICAL"]
    if critical:
        response += "⚠️ CRITICAL constraints:\n"
        for inv in critical:
            response += f"- {inv.rule}\n"

    # 2. Check dependencies
    if palace_context.depends_on:
        response += f"\n📥 Will affect: {', '.join(palace_context.depends_on)}\n"

    # 3. Consider risk
    if palace_context.risk_score > 0.6:
        response += f"\n🔴 HIGH RISK ({palace_context.risk_score:.2f})\n"
        response += "Recommend:\n"
        response += "- Write comprehensive tests\n"
        response += "- Gradual migration\n"
        response += "- Review with team\n"

    # 4. Address question
    response += f"\n💡 Answer:\n{answer_question(user_question)}"

    return response
```

---

## 🧪 Testing AI Integration

### Test Scenario

```bash
# 1. Set up test file
echo "def authenticate(user, password):
    eval(f'auth({user}, {password})')" > /tmp/bad_code.py

# 2. Get context
poetry run palace context /tmp/bad_code.py

# 3. Ask AI
# "Review this code for security issues"
```

**Expected AI Response (with context):**
```
⚠️ CRITICAL: The context shows a CRITICAL invariant:
"no_eval" → DO NOT USE eval()

Your code violates this invariant. eval() is dangerous
because it allows arbitrary code execution.

Alternative: Use parameterized queries or proper auth library.
```

**Without context:**
```
The code looks functional. Consider adding error handling.
```

---

## 📚 Additional Resources

- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup
- [CHEATSHEET.md](CHEATSHEET.md) - Quick reference
- [TUTORIAL.md](TUTORIAL.md) - Complete guide
- [GLOSSARY.md](GLOSSARY.md) - All concepts explained
- [DEMO.md](DEMO.md) - Real execution examples

---

## 🤝 Contributing

To improve Palace integration with your AI agent:

1. Test with your agent
2. Report issues
3. Suggest improvements
4. Submit PRs for better formatters

**GitHub**: https://github.com/dest92/openpalace

---

*"The best AI assistant is one that understands your codebase's architecture"* - Palace Team
