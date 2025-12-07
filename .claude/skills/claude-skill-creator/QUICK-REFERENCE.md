# Claude Skill Creation - Quick Reference

## Frontmatter Template

```yaml
---
name: [64 chars max]
description: [1024 chars max - include WHAT and WHEN]
---
```

## Description Formula

```
[What it does] + [Key capabilities] + Use when [specific triggers/scenarios]
```

**Example:**
```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF documents or form automation.
```

## File Structure Patterns

### Single File (Simple)
```
skill-name/
└── SKILL.md
```

### Multi-File (Progressive Disclosure)
```
skill-name/
├── SKILL.md (navigation hub)
├── reference.md (API docs)
├── examples.md (use cases)
└── workflows/
    ├── workflow1.md
    └── workflow2.md
```

### With Code
```
skill-name/
├── SKILL.md
├── guide.md
└── scripts/
    ├── script1.py
    └── script2.sh
```

## SKILL.md Structure

```markdown
# [Skill Name]

## Quick Start
[Minimal example for most common use case]

## Core Workflows
[Brief descriptions or links to detailed files]

## Reference
See [reference.md](reference.md) for complete API documentation

## Examples
See [examples.md](examples.md) for usage examples
```

## Progressive Disclosure

**In SKILL.md:**
```markdown
**Basic usage**: [instructions here]
**Advanced features**: See [advanced.md](advanced.md)
**API reference**: See [reference.md](reference.md)
```

**File loads:** Only when Claude needs them (zero context cost until accessed)

## MCP Tool References

**Always use fully qualified names:**
```markdown
Use the `ServerName:tool_name` tool to [perform action].

Examples:
- `BigQuery:bigquery_schema` - Get table schemas
- `GitHub:create_issue` - Create GitHub issues
- `Salesforce:query` - Run SOQL queries
```

## Common Patterns

### Pattern 1: Reference Files
```markdown
**For [topic]**: See [file.md](file.md)
```

### Pattern 2: Conditional Details
```markdown
## Basic usage
[Simple instructions]

**For advanced scenarios**: See [advanced.md](advanced.md)
```

### Pattern 3: Table of Contents (files > 100 lines)
```markdown
# API Reference

## Contents
- Authentication
- Core methods
- Advanced features
- Error handling

## Authentication
[Details...]
```

## Testing Checklist

- [ ] Description triggers on intended use cases
- [ ] Claude can find and load the skill
- [ ] File references work correctly
- [ ] MCP tools use qualified names
- [ ] SKILL.md under 500 lines
- [ ] Test with realistic scenarios

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Claude doesn't load skill | Check description specificity, verify file location |
| "Tool not found" error | Use fully qualified MCP tool name: `Server:tool` |
| Claude loads wrong content | Reorganize SKILL.md references, make navigation clearer |
| File reference broken | Use forward slashes, verify path relative to SKILL.md |

## Limits

- **name**: 64 characters
- **description**: 1024 characters
- **SKILL.md**: < 500 lines recommended
- **File nesting**: 1 level deep from SKILL.md

## Best Practices at a Glance

✅ **Do:**
- Keep SKILL.md under 500 lines
- Use third person in descriptions
- Include "what" AND "when" in description
- Use `Server:tool` for MCP tools
- Test with real use cases
- Add TOC to long files (>100 lines)

❌ **Don't:**
- Use first person ("I can help")
- Make descriptions generic
- Nest file references deeply
- Skip testing
- Load everything into SKILL.md

## Example Descriptions

✅ **Good:**
- "Generate descriptive commit messages by analyzing git diffs. Use when committing code changes or creating pull requests."
- "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF documents or form automation."

❌ **Weak:**
- "Helps with Git and commits"
- "PDF tool for various tasks"

## File Loading Model

| Level | Loaded | Cost | Content |
|-------|--------|------|---------|
| 1 | Always (startup) | ~100 tokens | Frontmatter only |
| 2 | When triggered | <5k tokens | SKILL.md body |
| 3+ | As needed | 0 until read | Referenced files |

## Quick Commands

List available skills:
```
Ask Claude: "What skills do you have available?"
```

Test skill trigger:
```
Ask Claude a question that should trigger your skill
```

Verify file access:
```
Ask Claude to read a specific file from your skill
```
