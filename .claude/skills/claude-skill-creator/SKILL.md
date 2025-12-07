---
name: Claude Skill Creator
description: Expert guide for writing effective Claude skills with best practices for frontmatter, descriptions, progressive disclosure, file organization, MCP tool references, and testing workflows. Use when creating or improving skills, troubleshooting skill loading, or optimizing skill performance.
---

# Claude Skill Creator

Comprehensive guide for authoring high-quality Claude skills that Claude can discover, load, and use effectively.

## Core Principles

### The Context Window is a Public Good

Your skill shares the context window with:
- System prompt
- Conversation history
- Other skills' metadata
- User's actual request

**Loading Model:**
- **Level 1** (Always loaded): `name` and `description` from frontmatter (~100 tokens per skill)
- **Level 2** (When triggered): SKILL.md body (under 5k tokens)
- **Level 3+** (As needed): Referenced files via bash (effectively unlimited)

**Best Practice:** Keep SKILL.md body under 500 lines. Split into separate files when approaching this limit.

---

## ⚠️ CRITICAL: Avoid Over-Engineering

### The #1 Skill Creation Mistake

**Problem:** Creating comprehensive skill structure with 15-20 referenced files, but only implementing 3-4 of them.

**Why this happens:**
- Progressive disclosure pattern encourages creating an index first
- Enthusiasm for completeness leads to ambitious scope
- Time runs out before filling in all referenced files
- Result: Skill with broken links and empty promises

**Impact:**
- Claude follows link to non-existent file → confusion
- User loses trust in skill quality
- Wasted tokens loading an incomplete index
- Maintenance burden (unfinished files linger forever)

### START SMALL - The Right Approach

**When creating a new skill:**

1. **Start with 1-3 files maximum:**
   - SKILL.md (the main file)
   - OPTIONAL: 1-2 detailed reference files

2. **Only create files you IMMEDIATELY populate:**
   - Never create empty placeholder files
   - Never reference files you haven't written yet
   - If you write "See [advanced.md]" → **write advanced.md BEFORE saving SKILL.md**

3. **Add incrementally based on actual need:**
   - Skill works fine with 3 files? Stop there.
   - User needs more depth? Add 1-2 more files.
   - Don't anticipate future needs - address current needs.

4. **Maximum file count guidelines:**
   - Simple skill: 1-3 files
   - Moderate skill: 4-6 files
   - Complex skill: 7-10 files (rare!)
   - **If you find yourself planning 15+ files, you're over-engineering**

### Example: Right-Sized Skills

**✅ GOOD - Focused skill (3 files):**
```
pdf-skill/
├── SKILL.md (main patterns + quick start)
├── forms.md (form filling details)
└── extraction.md (text extraction details)
```

**❌ BAD - Over-engineered skill (20 files, half empty):**
```
pdf-skill/
├── SKILL.md (references 20 files)
├── basics/
│   ├── installation.md (empty)
│   ├── quick-start.md (empty)
│   └── configuration.md (empty)
├── advanced/
│   ├── forms.md (has content)
│   ├── encryption.md (empty)
│   ├── compression.md (empty)
│   └── optimization.md (empty)
└── [12 more empty files]
```

### Gatekeeping Questions

**Before creating any skill, ask:**

1. **Can this be 1 file?** If yes, do that.
2. **If multi-file, can I complete ALL files RIGHT NOW?** If no, reduce scope.
3. **Am I creating placeholders?** If yes, stop.
4. **Would the user actually need this depth?** If uncertain, start smaller.
5. **Am I solving a current problem or anticipating future ones?** Focus on current.

### The Right Process

```
Step 1: Create SKILL.md with minimal scope (1-3 topics)
Step 2: Immediately create any referenced files
Step 3: Test the skill - does it solve the problem?
Step 4: (Optional) Add 1-2 more files only if proven necessary
Step 5: Stop when problem is solved
```

**NOT:**
```
Step 1: Plan comprehensive skill with 20 topics
Step 2: Create SKILL.md referencing all 20 files
Step 3: Create 4 files, run out of time
Step 4: Ship incomplete skill with broken references
```

---

## Frontmatter Structure

```yaml
---
name: [Skill Name]
description: [One-line description with what AND when]
---
```

### Requirements

- **Required fields:** `name` and `description` (only two fields supported)
- **name:** 64 characters maximum
- **description:** 1024 characters maximum

### Description Best Practices

The description determines when Claude loads your skill. It should include:

1. **What the skill does** (capabilities)
2. **When to use it** (triggers)
3. **Key terminology** (searchable domain terms)

**Style Guidelines:**
- Use third person: "Processes Excel files" not "I can help you"
- Be specific with domain language users would search for
- Avoid generic terms like "helps" or "assists"

**Effective Examples:**

✅ **Good:**
```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF documents or form automation.
```

✅ **Good:**
```yaml
description: Generate descriptive commit messages by analyzing git diffs. Use when committing code changes or creating pull requests.
```

❌ **Weak:**
```yaml
description: Helps with documents and files when needed.
```

---

## SKILL.md Body Structure

### Pattern 1: High-Level Guide with File References

Best for skills with multiple workflows or extensive documentation.

```markdown
# [Skill Name]

## Quick Start
[Concise instructions or code for common use case]

## Workflows
**[Workflow Name]**: See [workflows.md](workflows.md)
**[Another Workflow]**: See [advanced.md](advanced.md)

## Reference
For complete API documentation, see [reference.md](reference.md)
```

### Pattern 2: Domain-Specific Organization

Organize by domain so Claude loads only relevant content.

```markdown
# BigQuery Analysis Skill

## Overview
Query and analyze data in BigQuery datasets.

## Documentation by Domain
**Finance metrics**: See [reference/finance.md](reference/finance.md)
**Sales metrics**: See [reference/sales.md](reference/sales.md)
**Product metrics**: See [reference/product.md](reference/product.md)
```

**File Structure:**
```
bigquery-skill/
├── SKILL.md (overview and navigation)
└── reference/
    ├── finance.md
    ├── sales.md
    └── product.md
```

### Pattern 3: Conditional Details with Progressive Disclosure

```markdown
## Basic Usage
[Simple instructions for common cases]

## Advanced Features
**For complex scenarios**: See [advanced.md](advanced.md)
**For batch operations**: See [batch.md](batch.md)
**For error handling**: See [errors.md](errors.md)
```

---

## File Organization

### Directory Structure Examples

#### Simple Skill (Single File)
```
my-skill/
└── SKILL.md
```

#### Skill with Documentation
```
my-skill/
├── SKILL.md (required - overview and navigation)
├── reference.md (loaded as needed)
├── examples.md (loaded as needed)
└── workflows.md (loaded as needed)
```

#### Skill with Code and Docs
```
pdf-skill/
├── SKILL.md (main instructions)
├── FORMS.md (form-filling guide)
├── reference.md (API reference)
├── examples.md (usage examples)
└── scripts/
    ├── analyze_form.py (executed via bash, not loaded)
    ├── fill_form.py
    └── validate.py
```

**⚠️ CRITICAL:** In all examples above, **every file shown exists and has content**. Never create a structure with empty placeholder files.

### File Types and Their Strengths

| Type | Purpose | Token Cost | When to Use |
|------|---------|------------|-------------|
| **Instructions** (`.md`) | Flexible guidance | Loaded into context | Workflows, concepts, guidance |
| **Code** (`.py`, `.sh`, etc.) | Deterministic operations | Executed, not loaded | Utilities, validation, automation |
| **Resources** (schemas, templates) | Reference materials | Loaded on demand | Data structures, examples, templates |

---

## Progressive Disclosure Patterns

### Filesystem-Based Model

Claude navigates skills like a filesystem, reading files only when needed.

**Example workflow:**

1. User asks about revenue metrics
2. Claude reads SKILL.md, sees reference to `reference/finance.md`
3. Claude invokes bash to read just that file
4. Other files (`sales.md`, `product.md`) remain unloaded (zero context tokens)

**In SKILL.md:**
```markdown
# BigQuery Skill

## Quick reference by domain
**Revenue/billing**: [reference/finance.md](reference/finance.md)
**Pipeline/opportunities**: [reference/sales.md](reference/sales.md)
**Usage/features**: [reference/product.md](reference/product.md)
```

### Table of Contents for Long Files

For reference files exceeding 100 lines, include a table of contents at the top.

**Example:**
```markdown
# API Reference

## Contents
- Authentication and setup
- Core methods (create, read, update, delete)
- Advanced features (batch operations, webhooks)
- Error handling patterns
- Code examples

## Authentication and setup
...

## Core methods
...
```

Claude can see the full scope even when previewing, then read the complete file or jump to sections.

---

## MCP Tool References

Always use fully qualified tool names to avoid "tool not found" errors.

**Format:** `ServerName:tool_name`

**Examples:**
```markdown
Use the `BigQuery:bigquery_schema` tool to retrieve table schemas.
Use the `GitHub:create_issue` tool to create issues.
Use the `Salesforce:query` tool to run SOQL queries.
```

**Where:**
- `BigQuery`, `GitHub`, `Salesforce` = MCP server names
- `bigquery_schema`, `create_issue`, `query` = tool names

**Why this matters:** Tool names can conflict across MCP servers. Fully qualified names ensure Claude invokes the correct tool.

---

## Testing and Iteration

### Three-Agent Testing Pattern

Use three Claude instances for rapid iteration:

1. **Claude A** (Skill Author): You describe what the skill should do
2. **Claude B** (Tester): Uses the skill in realistic scenarios
3. **You**: Observe behavior, refine based on what works/doesn't work

**Why this works:**
- Claude A understands agent needs
- You provide domain expertise
- Claude B reveals gaps through real usage
- Iterative refinement based on observed behavior vs assumptions

### Observe How Claude Navigates Skills

As you iterate, watch for:

- **Unexpected exploration paths**: Claude reads files in different order than you anticipated
  - **Fix**: Your structure may not be as intuitive as you thought

- **Missed connections**: Claude fails to follow references to important files
  - **Fix**: Make links more explicit or prominent

- **Overreliance on certain sections**: Claude repeatedly reads the same file
  - **Fix**: Consider moving that content into main SKILL.md

- **Ignored content**: Claude never accesses a bundled file
  - **Fix**: File might be unnecessary or poorly signaled

**Iterate based on these observations** to align skill structure with how Claude naturally explores it.

---

## Common Patterns

### Pattern: Reference Multiple Files from SKILL.md

Keep SKILL.md as a navigation hub:

```markdown
# SKILL.md

**Basic usage**: [Core workflows are in this file]

**Advanced features**: See [advanced.md](advanced.md)
**API reference**: See [reference.md](reference.md)
**Examples**: See [examples.md](examples.md)
```

### Pattern: Conditional Loading

Show basics in SKILL.md, reference details only when needed:

```markdown
## Creating documents
Use the document library to create new files.

## Editing documents
For simple edits, modify XML directly.

**For tracked changes and redlining**: See [REDLINING.md](REDLINING.md)
```

### Pattern: Code + Documentation

Bundle executable scripts separately:

```markdown
## Analyzing PDF forms

Run the analysis script: `python scripts/analyze_form.py <file>`

**For field extraction details**: See [FORMS.md](FORMS.md)
```

**File structure:**
```
pdf-skill/
├── SKILL.md
├── FORMS.md
└── scripts/
    └── analyze_form.py
```

Scripts execute via bash without loading content into context.

---

## Troubleshooting

### Claude Doesn't Use My Skill

**Checklist:**
1. Is the description specific enough to trigger on your use case?
2. Does the description include key terminology users would search for?
3. Is SKILL.md in the correct location (`.claude/skills/<skill-name>/SKILL.md`)?
4. Is the YAML frontmatter properly formatted (three dashes, required fields)?

**Test:** Ask Claude to list available skills. If yours doesn't appear, check file location and YAML syntax.

### Skill Has Errors

**Common causes:**
1. **YAML syntax errors**: Missing closing `---`, incorrect indentation
2. **File path errors**: Use forward slashes (`reference/guide.md`), relative paths from SKILL.md location
3. **Description too long**: Must be under 1024 characters

**Debug:**
1. Verify YAML frontmatter with a YAML validator
2. Check that all referenced files exist
3. Test file paths by having Claude read them directly

### Multiple Skills Conflict

**When:** Two skills have overlapping descriptions/triggers

**Solutions:**
1. Make descriptions more specific
2. Use conditional phrases: "Use when [specific scenario]"
3. Consider merging related skills into one with organized sections

---

## Security Considerations

**Only use skills from trusted sources:**
- Skills you created yourself
- Skills from Anthropic
- Skills from verified, trusted sources

**Why:** Skills provide Claude with new capabilities through instructions and code. A malicious skill can direct Claude to invoke tools or execute code in unintended ways.

**If using untrusted skills:**
1. Thoroughly audit all files
2. Check all code for malicious operations
3. Verify tool invocations match stated purpose
4. Test in isolated environment first

---

## Best Practices Summary

### Do's ✅

- Keep SKILL.md body under 500 lines
- Use third-person descriptions
- Include "what" AND "when" in descriptions
- Use fully qualified MCP tool names (`Server:tool`)
- Reference files progressively (one level deep from SKILL.md)
- Add table of contents to files > 100 lines
- Bundle executable scripts separately
- Test with real usage scenarios
- Observe how Claude navigates your skill

### Don'ts ❌

- Don't make descriptions generic
- Don't use first person ("I can help you")
- Don't exceed 1024 characters in description
- Don't load everything into SKILL.md
- Don't use relative paths that go up directories
- Don't nest references more than one level deep
- Don't skip testing with realistic use cases

---

## Quick Reference

### Skill Creation Checklist

1. **Planning**
   - [ ] Define clear purpose and triggers
   - [ ] Identify key terminology for description
   - [ ] Plan file structure (single file vs multi-file)

2. **Frontmatter**
   - [ ] Name under 64 characters
   - [ ] Description under 1024 characters
   - [ ] Description includes "what" AND "when"
   - [ ] Third-person voice

3. **Body Structure**
   - [ ] SKILL.md under 500 lines
   - [ ] Clear navigation to additional files
   - [ ] MCP tools use fully qualified names
   - [ ] File references one level deep

4. **Testing**
   - [ ] Test with realistic scenarios
   - [ ] Observe Claude's navigation patterns
   - [ ] Verify all file references work
   - [ ] Check that skill loads only when needed

5. **Iteration**
   - [ ] Refine based on actual usage
   - [ ] Update descriptions if triggers miss
   - [ ] Reorganize if Claude explores inefficiently

---

## Examples Gallery

For complete examples and templates, see:
- [examples/simple-skill.md](examples/simple-skill.md) - Single-file skill
- [examples/multi-file-skill.md](examples/multi-file-skill.md) - Skill with documentation
- [examples/code-skill.md](examples/code-skill.md) - Skill with executable scripts
- [examples/mcp-skill.md](examples/mcp-skill.md) - Skill using MCP tools

---

## Additional Resources

- **Official Docs**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/
- **Best Practices**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices
- **API Reference**: https://docs.claude.com/en/api/skills

---

*This skill consolidates official Claude Skills documentation, best practices, and patterns for creating effective skills that Claude can discover and use optimally.*
