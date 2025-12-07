# MCP Skill Example

A skill that uses Model Context Protocol (MCP) tools.

## Use Case
Salesforce data analysis using MCP server tools for querying and managing records.

## File Structure
```
salesforce-analyst/
├── SKILL.md (main instructions with MCP tool references)
├── soql-guide.md (SOQL query patterns)
├── objects.md (common Salesforce objects reference)
└── examples.md (real-world query examples)
```

## SKILL.md

```markdown
---
name: Salesforce Analyst
description: Query and analyze Salesforce data using SOQL, create/update records, and retrieve object metadata. Use when working with Salesforce cases, accounts, opportunities, or custom objects.
---

# Salesforce Analyst

Analyze Salesforce data using MCP tools for querying, creating, and updating records.

## Prerequisites

Requires the Salesforce MCP server to be configured and running.

## Core Operations

### Querying Data

Use the `pdi-salesforce-sse3:query` tool to run SOQL queries:

```soql
SELECT Id, CaseNumber, Subject, Status, Priority
FROM Case
WHERE Status = 'New'
ORDER BY CreatedDate DESC
LIMIT 10
```

**Important:** Always use fully qualified tool name: `pdi-salesforce-sse3:query`

### Creating Records

Use the `pdi-salesforce-sse3:create` tool to create new records:

```json
{
  "sObjectType": "Case",
  "record": {
    "Subject": "Product inquiry",
    "Description": "Customer question about pricing",
    "Priority": "Medium",
    "Origin": "Web"
  }
}
```

### Updating Records

Use the `pdi-salesforce-sse3:update` tool to update existing records:

```json
{
  "sObjectType": "Case",
  "id": "5003000000D8cuI",
  "record": {
    "Status": "Closed",
    "Resolution": "Customer satisfied with answer"
  }
}
```

## MCP Tools Reference

All tools require the `pdi-salesforce-sse3:` prefix:

| Tool | Purpose | Example |
|------|---------|---------|
| `pdi-salesforce-sse3:query` | Execute SOQL queries | Retrieve cases, accounts, etc. |
| `pdi-salesforce-sse3:create` | Create new records | Create case, contact, opportunity |
| `pdi-salesforce-sse3:update` | Update existing records | Update case status, account info |
| `pdi-salesforce-sse3:retrieve` | Get records by ID | Fetch specific case by ID |
| `pdi-salesforce-sse3:describeSObject` | Get object metadata | Discover fields on Case object |

## Common Workflows

**Case Analysis**: See [examples.md](examples.md#case-analysis)
**Account Management**: See [examples.md](examples.md#account-management)
**SOQL Patterns**: See [soql-guide.md](soql-guide.md)
**Object Reference**: See [objects.md](objects.md)

## Error Handling

If you encounter "tool not found" errors:
1. Verify MCP server is running
2. Check that tool name includes server prefix: `pdi-salesforce-sse3:`
3. Confirm server name matches your MCP configuration

## Best Practices

1. **Always use fully qualified tool names** to avoid conflicts
2. **Test queries with LIMIT** before running on large datasets
3. **Use selective field lists** (not SELECT *) for performance
4. **Check describeSObject** for available fields before querying
```

## soql-guide.md

```markdown
# SOQL Query Patterns

## Contents
- Basic queries
- Filtering and sorting
- Relationship queries
- Aggregations
- Date functions

## Basic Queries

### Select All Cases
```soql
SELECT Id, CaseNumber, Subject, Status
FROM Case
```

### With Filtering
```soql
SELECT Id, CaseNumber, Subject
FROM Case
WHERE Status = 'New' AND Priority = 'High'
```

### With Sorting
```soql
SELECT Id, CaseNumber, CreatedDate
FROM Case
ORDER BY CreatedDate DESC
LIMIT 20
```

## Relationship Queries

### Parent to Child
```soql
SELECT Id, Name, (SELECT Id, Subject FROM Cases)
FROM Account
WHERE Industry = 'Technology'
```

### Child to Parent
```soql
SELECT Id, Subject, Account.Name, Account.Industry
FROM Case
WHERE Account.Industry = 'Retail'
```

## Aggregations

### Count by Status
```soql
SELECT Status, COUNT(Id) total
FROM Case
GROUP BY Status
```

### Average Age by Priority
```soql
SELECT Priority, AVG(Age_Days__c) avg_age
FROM Case
GROUP BY Priority
```

## Date Functions

### Last 7 Days
```soql
SELECT Id, Subject
FROM Case
WHERE CreatedDate = LAST_N_DAYS:7
```

### This Month
```soql
SELECT Id, Subject
FROM Case
WHERE CreatedDate = THIS_MONTH
```

[Guide continues...]
```

## examples.md

```markdown
# Salesforce Analysis Examples

## Case Analysis

### Find High-Priority Open Cases

**Query using MCP tool:**

Tool: `pdi-salesforce-sse3:query`

Parameters:
```json
{
  "soql": "SELECT Id, CaseNumber, Subject, Priority, Status, Owner.Name FROM Case WHERE Status != 'Closed' AND Priority = 'High' ORDER BY CreatedDate DESC LIMIT 25"
}
```

**Expected result:** List of high-priority open cases with owner information

### Analyze Case Resolution Time

**Query:**
```soql
SELECT AVG(Resolution_Time_Hours__c) avg_time, Priority
FROM Case
WHERE Status = 'Closed' AND ClosedDate = LAST_N_DAYS:30
GROUP BY Priority
```

## Account Management

### Find Accounts with Recent Activity

**Query using MCP tool:**

Tool: `pdi-salesforce-sse3:query`

Parameters:
```json
{
  "soql": "SELECT Id, Name, Industry, (SELECT Id, Subject FROM Cases WHERE CreatedDate = THIS_MONTH) FROM Account WHERE LastActivityDate = THIS_MONTH"
}
```

[Examples continue...]
```

## Key Points

- **Fully qualified MCP tool names**: Always use `server:tool` format
- **Clear examples**: Shows exact tool calls with parameters
- **Error guidance**: Explains common issues and solutions
- **Reference structure**: SOQL guide separate from main instructions
- **Progressive disclosure**: Examples file loaded only when needed
- **Tool table**: Quick reference for all available MCP tools
