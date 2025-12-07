# Compliance Rule Generation Guide

This guide provides comprehensive documentation on generating compliance rules for different business domains using the Compliance Agent system.

---

## Table of Contents

1. [Overview](#overview)
2. [Supported Industries](#supported-industries)
3. [Document Preparation](#document-preparation)
4. [Best Practices](#best-practices)
5. [Rule Categories](#rule-categories)
6. [Industry-Specific Examples](#industry-specific-examples)
7. [Customizing Point Deductions](#customizing-point-deductions)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Compliance Agent uses AI (Ollama LLM) to extract compliance rules from regulatory documents. The system automatically:

- Parses uploaded documents (PDF, DOCX, HTML, Markdown)
- Extracts 5-15 actionable compliance rules per document
- Categorizes rules by type and severity
- Assigns point deductions based on rule importance
- Stores rules in the database for automated content checking

### Workflow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Upload Doc    │ -> │   AI Extraction  │ -> │  Rules Stored   │
│  (PDF/DOCX/MD)  │    │  (Ollama LLM)    │    │  (PostgreSQL)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              v
                    ┌──────────────────┐
                    │  Rule Validation │
                    │  (JSON Schema)   │
                    └──────────────────┘
```

---

## Supported Industries

The system is designed to be **industry-agnostic** and can be configured for various business domains:

| Industry | Common Rule Categories | Typical Regulations |
|----------|----------------------|---------------------|
| **Insurance** | IRDAI, Brand, Legal | IRDAI Guidelines, Consumer Protection |
| **Banking/Finance** | RBI, Compliance, Risk | RBI Circulars, SEBI Guidelines |
| **Healthcare** | HIPAA, Clinical, Safety | HIPAA, FDA Regulations |
| **E-commerce** | Consumer Rights, Privacy | Consumer Protection Act, GDPR |
| **Pharmaceuticals** | CDSCO, Clinical Trials | CDSCO Guidelines, FDA |
| **Real Estate** | RERA, Legal, Marketing | RERA Act, Advertising Standards |
| **Telecom** | TRAI, Privacy, Billing | TRAI Regulations |

---

## Document Preparation

### Supported Formats

| Format | Extension | Best For |
|--------|-----------|----------|
| PDF | `.pdf` | Official regulatory documents, scanned policies |
| Word | `.docx` | Internal compliance manuals, editable guidelines |
| HTML | `.html`, `.htm` | Web-based regulations, online guidelines |
| Markdown | `.md`, `.markdown` | Technical documentation, developer guidelines |

### Document Quality Tips

> [!TIP]
> Higher quality documents produce better rules!

1. **Use clear headings**: Structure documents with clear sections
2. **Avoid scanned images**: OCR-based PDFs may have extraction issues
3. **Include examples**: Documents with examples help AI understand context
4. **Keep it focused**: One regulatory topic per document works best
5. **Limit size**: Documents over 10,000 characters may be truncated

### Optimal Document Structure

```markdown
# Regulation Title

## Section 1: Requirements
- Requirement 1.1
- Requirement 1.2

## Section 2: Prohibitions
- Prohibition 2.1
- Prohibition 2.2

## Section 3: Penalties
- Violation penalties
```

---

## Best Practices

### 1. Document Naming

Use descriptive document titles when uploading:

| ✅ Good | ❌ Bad |
|---------|--------|
| "IRDAI Marketing Guidelines 2024" | "doc1.pdf" |
| "RBI KYC Compliance Requirements" | "rules.docx" |
| "FDA Drug Advertising Standards" | "new file.html" |

### 2. Rule Granularity

> [!IMPORTANT]
> Each rule should be **specific** and **actionable**.

**Good rule**: "All premium amounts must include GST calculations with explicit breakdown"

**Bad rule**: "Follow tax laws"

### 3. Keyword Selection

Keywords help the system identify violations. Choose:

- Domain-specific terms
- Common violation triggers
- Regulatory terminology

**Example for Insurance**:
```json
{
  "keywords": ["premium", "GST", "tax", "deduction", "calculation"]
}
```

### 4. Severity Assignment

| Severity | When to Use | Point Deduction |
|----------|-------------|-----------------|
| **Critical** | Legal risk, regulatory violations | -15 to -20 |
| **High** | Compliance failures, major issues | -10 to -15 |
| **Medium** | Best practice violations | -5 to -10 |
| **Low** | Minor issues, suggestions | -2 to -5 |

### 5. Regular Updates

- Review rules quarterly for regulatory changes
- Deactivate outdated rules (soft delete)
- Upload new regulatory documents as they're released

---

## Rule Categories

### Default Categories

The system comes with three default categories:

#### 1. IRDAI (Insurance Regulatory)
```json
{
  "category": "irdai",
  "description": "Insurance Regulatory and Development Authority rules",
  "examples": [
    "Premium payment disclosure",
    "Policy benefits accuracy",
    "Agent identification requirements"
  ]
}
```

#### 2. Brand (Marketing/Brand Guidelines)
```json
{
  "category": "brand",
  "description": "Brand consistency and marketing guidelines",
  "examples": [
    "Logo usage standards",
    "Terminology consistency",
    "Tagline requirements"
  ]
}
```

#### 3. SEO (Search Engine Optimization)
```json
{
  "category": "seo",
  "description": "Digital content and SEO compliance",
  "examples": [
    "Meta description requirements",
    "Heading structure",
    "Content length guidelines"
  ]
}
```

### Adding Custom Categories

To add new categories, modify `backend/app/models/rule.py`:

```python
# Add to category enum/validation
VALID_CATEGORIES = ['irdai', 'brand', 'seo', 'your_new_category']
```

---

## Industry-Specific Examples

### Insurance Industry (IRDAI)

**Sample Document Title**: "IRDAI Advertising Guidelines 2024"

**Expected Rules**:

```json
[
  {
    "category": "irdai",
    "rule_text": "All insurance advertisements must clearly display the IRDAI registration number",
    "severity": "critical",
    "keywords": ["IRDAI", "registration", "advertisement", "display"],
    "points_deduction": -20
  },
  {
    "category": "irdai",
    "rule_text": "Premium amounts must be quoted with clear GST breakdown",
    "severity": "high",
    "keywords": ["premium", "GST", "tax", "breakdown"],
    "points_deduction": -10
  }
]
```

---

### Banking & Finance (RBI)

**Sample Document Title**: "RBI Customer Communication Guidelines"

**Expected Rules**:

```json
[
  {
    "category": "rbi",
    "rule_text": "All interest rate communications must include annualized percentage rate (APR)",
    "severity": "critical",
    "keywords": ["interest", "APR", "rate", "percentage"],
    "points_deduction": -20
  },
  {
    "category": "rbi",
    "rule_text": "Loan terms must include total repayment amount and duration",
    "severity": "high",
    "keywords": ["loan", "repayment", "EMI", "tenure"],
    "points_deduction": -15
  }
]
```

---

### Healthcare (HIPAA/Medical)

**Sample Document Title**: "Patient Communication Compliance Standards"

**Expected Rules**:

```json
[
  {
    "category": "hipaa",
    "rule_text": "Patient identifiable information (PII) must never be included in public-facing content",
    "severity": "critical",
    "keywords": ["PII", "patient", "identifiable", "HIPAA"],
    "points_deduction": -20
  },
  {
    "category": "medical",
    "rule_text": "Medical claims must include 'consult your doctor' disclaimer",
    "severity": "high",
    "keywords": ["medical", "doctor", "consult", "disclaimer"],
    "points_deduction": -10
  }
]
```

---

### E-commerce (Consumer Protection)

**Sample Document Title**: "E-commerce Advertising Standards"

**Expected Rules**:

```json
[
  {
    "category": "consumer",
    "rule_text": "All product prices must include applicable taxes and delivery charges",
    "severity": "high",
    "keywords": ["price", "tax", "delivery", "charges", "total"],
    "points_deduction": -10
  },
  {
    "category": "consumer",
    "rule_text": "Return and refund policy must be clearly visible before checkout",
    "severity": "medium",
    "keywords": ["return", "refund", "policy", "checkout"],
    "points_deduction": -5
  }
]
```

---

### Real Estate (RERA)

**Sample Document Title**: "RERA Marketing Compliance Guidelines"

**Expected Rules**:

```json
[
  {
    "category": "rera",
    "rule_text": "All property advertisements must display RERA registration number",
    "severity": "critical",
    "keywords": ["RERA", "registration", "property", "advertisement"],
    "points_deduction": -20
  },
  {
    "category": "rera",
    "rule_text": "Possession dates must match registered project timeline",
    "severity": "critical",
    "keywords": ["possession", "date", "timeline", "delivery"],
    "points_deduction": -20
  }
]
```

---

## Customizing Point Deductions

### Via Admin Dashboard

1. Navigate to **Admin Dashboard** (`/admin`)
2. Locate the rule in the **Rules Table**
3. Click **Edit** on the rule
4. Adjust the **Points Deduction** value
5. Click **Save**

### Via API

```bash
curl -X PUT "http://localhost:8000/api/admin/rules/{rule_id}" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 11111111-1111-1111-1111-111111111111" \
  -d '{
    "points_deduction": -15
  }'
```

### Recommended Deduction Ranges

| Severity | Min | Max | Default |
|----------|-----|-----|---------|
| Critical | -20 | -15 | -20 |
| High | -15 | -10 | -10 |
| Medium | -10 | -5 | -5 |
| Low | -5 | -2 | -2 |

---

## Troubleshooting

### Common Issues

#### 1. No Rules Extracted

**Symptoms**: Document uploads but zero rules created

**Solutions**:
- Check document isn't empty or corrupted
- Ensure text is selectable (not scanned image)
- Try a smaller, more focused document

#### 2. Low-Quality Rules

**Symptoms**: Rules are too vague or generic

**Solutions**:
- Use more specific regulatory documents
- Include clear examples in source document
- Add section headings for better parsing

#### 3. Wrong Category Assignment

**Symptoms**: Rules assigned to wrong category

**Solutions**:
- Edit rules manually via dashboard
- Include category context in document title
- Structure document with clear regulatory domain

#### 4. Duplicate Rules

**Symptoms**: Similar rules created multiple times

**Solutions**:
- Use "Delete All" to clear and re-import
- Edit/deactivate duplicate rules manually
- Combine related regulations into single document

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Unsupported file type" | Wrong file extension | Use PDF, DOCX, HTML, or MD |
| "Failed to parse document" | Corrupted file | Re-export from source |
| "LLM extraction failed" | Ollama connection issue | Check Ollama service is running |
| "Invalid JSON response" | LLM output malformed | Retry upload, check document quality |

---

## API Reference

### Generate Rules from Document

```http
POST /api/admin/rules/generate
Content-Type: multipart/form-data
X-User-Id: {super_admin_user_id}

file: [binary]
document_title: "IRDAI Guidelines 2024"
```

### List All Rules

```http
GET /api/admin/rules?page=1&page_size=20&category=irdai&severity=critical
X-User-Id: {super_admin_user_id}
```

### Delete All Rules

```http
DELETE /api/admin/rules
X-User-Id: {super_admin_user_id}
```

---

## Next Steps

1. **Start with a pilot**: Test with one regulatory document
2. **Review generated rules**: Manually verify accuracy
3. **Adjust point deductions**: Tune to your organization's needs
4. **Scale up**: Add more regulatory documents
5. **Monitor**: Track compliance scores over time

---

## Support

For questions or issues:
- Check the [PROJECT_UNDERSTANDING.md](../PROJECT_UNDERSTANDING.md) for system architecture
- Review [PHASE2_SUMMARY.md](../PHASE2_SUMMARY.md) for feature details
- Open an issue in the repository for bugs

---

*Last Updated: December 2025*
