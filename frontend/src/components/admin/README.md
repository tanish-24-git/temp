# Admin Components Documentation

This directory contains reusable components for the Admin Dashboard, following the project's existing design patterns (light theme, consistent styling).

---

## Components Overview

### 1. **RuleStatsCards.tsx**
Displays summary statistics for rules in card format.

**Props:**
```typescript
interface RuleStatsCardsProps {
  stats: RuleStats | null;
  loading?: boolean;
}
```

**Usage:**
```tsx
<RuleStatsCards stats={stats} loading={statsLoading} />
```

**Features:**
- 4 stat cards: Total, Active, IRDAI, Critical
- Loading skeleton animation
- Color-coded values (green, purple, red)
- Responsive grid layout (1 column mobile, 4 columns desktop)

---

### 2. **RuleUploadForm.tsx**
File upload form for generating rules from documents.

**Props:**
```typescript
interface RuleUploadFormProps {
  onUpload: (file: File, title: string) => Promise<void>;
  uploading: boolean;
  uploadResult: RuleGenerationResponse | null;
}
```

**Usage:**
```tsx
<RuleUploadForm
  onUpload={handleUpload}
  uploading={uploading}
  uploadResult={uploadResult}
/>
```

**Features:**
- Document title input
- File upload (PDF, DOCX, HTML, MD)
- File size display
- Upload progress indicator (spinner)
- Success/error result display
- Auto-reset form on success

---

### 3. **RuleFilters.tsx**
Filter bar for rules table with category, severity, status, and search.

**Props:**
```typescript
interface RuleFiltersProps {
  categoryFilter: string;
  severityFilter: string;
  activeFilter: boolean | undefined;
  searchQuery: string;
  onCategoryChange: (value: string) => void;
  onSeverityChange: (value: string) => void;
  onActiveChange: (value: boolean | undefined) => void;
  onSearchChange: (value: string) => void;
}
```

**Usage:**
```tsx
<RuleFilters
  categoryFilter={categoryFilter}
  severityFilter={severityFilter}
  activeFilter={activeFilter}
  searchQuery={searchQuery}
  onCategoryChange={setCategoryFilter}
  onSeverityChange={setSeverityFilter}
  onActiveChange={setActiveFilter}
  onSearchChange={setSearchQuery}
/>
```

**Features:**
- 4 filter inputs in responsive grid
- Category: All, IRDAI, Brand, SEO
- Severity: All, Critical, High, Medium, Low
- Status: All, Active, Inactive
- Search: Full-text search in rule text

---

### 4. **RulesTable.tsx**
Main data table for displaying rules with actions.

**Props:**
```typescript
interface RulesTableProps {
  rules: Rule[];
  loading: boolean;
  onEdit: (rule: Rule) => void;
  onDelete: (ruleId: string) => void;
}
```

**Usage:**
```tsx
<RulesTable
  rules={rules}
  loading={loading}
  onEdit={setEditingRule}
  onDelete={handleDeleteRule}
/>
```

**Features:**
- 6 columns: Category, Severity, Rule Text, Points, Status, Actions
- Color-coded badges (matches Submissions page style)
- Truncated text with hover tooltips
- Edit and Delete action buttons
- Loading state
- Empty state message
- Hover row highlighting

**Styling Pattern:**
- Light theme (white bg, gray-50 header)
- Badge colors:
  - **Category**: Purple (IRDAI), Green (Brand), Blue (SEO)
  - **Severity**: Red (Critical), Orange (High), Yellow (Medium), Blue (Low)
  - **Status**: Green (Active), Gray (Inactive)

---

### 5. **Pagination.tsx**
Pagination controls for table navigation.

**Props:**
```typescript
interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}
```

**Usage:**
```tsx
<Pagination
  currentPage={currentPage}
  totalPages={totalPages}
  onPageChange={setCurrentPage}
/>
```

**Features:**
- Previous/Next buttons
- Current page indicator
- Disabled state for boundary pages
- Auto-hide when only 1 page
- Centered layout

---

### 6. **RuleEditModal.tsx**
Modal dialog for editing rule details.

**Props:**
```typescript
interface RuleEditModalProps {
  rule: Rule | null;
  onClose: () => void;
  onSave: (ruleId: string, updates: Partial<Rule>) => Promise<void>;
}
```

**Usage:**
```tsx
<RuleEditModal
  rule={editingRule}
  onClose={() => setEditingRule(null)}
  onSave={handleUpdateRule}
/>
```

**Features:**
- Full-screen overlay with backdrop
- Form fields:
  - Rule Text (textarea)
  - Category (select)
  - Severity (select)
  - Points Deduction (number input with validation)
  - Keywords (comma-separated)
  - Pattern (regex, optional)
  - Active status (checkbox)
- Save and Cancel buttons
- Loading state during save
- Close button (X icon)
- Scrollable for long content

**Validation:**
- Points: -50.00 to 0.00 range
- Keywords: Auto-split by comma
- Form syncs with rule prop changes

---

## Design System

### Color Palette (Light Theme)

**Backgrounds:**
- White: `bg-white`
- Light Gray: `bg-gray-50`
- Border: `border-gray-200` / `border-gray-300`

**Text:**
- Primary: `text-gray-900`
- Secondary: `text-gray-500` / `text-gray-600`
- Placeholder: `text-gray-400`

**Badges:**
```tsx
// Severity
critical: 'bg-red-100 text-red-800'
high:     'bg-orange-100 text-orange-800'
medium:   'bg-yellow-100 text-yellow-800'
low:      'bg-blue-100 text-blue-800'

// Category
irdai:    'bg-purple-100 text-purple-800'
brand:    'bg-green-100 text-green-800'
seo:      'bg-blue-100 text-blue-800'

// Status
active:   'bg-green-100 text-green-800'
inactive: 'bg-gray-100 text-gray-800'
```

**Buttons:**
```tsx
// Primary
'bg-blue-600 text-white hover:bg-blue-700'

// Danger
'text-red-600 hover:text-red-800'

// Disabled
'bg-gray-300 text-gray-500 cursor-not-allowed'
```

### Spacing
- Card padding: `p-6`
- Grid gap: `gap-4`
- Section spacing: `space-y-4` / `space-y-6`

### Typography
- Page title: `text-3xl font-bold text-gray-900`
- Section title: `text-xl font-semibold text-gray-900`
- Label: `text-sm font-medium text-gray-700`
- Body: `text-sm text-gray-900`

---

## Integration Example

**pages/AdminDashboard.tsx:**
```tsx
import {
  RuleStatsCards,
  RuleUploadForm,
  RuleFilters,
  RulesTable,
  Pagination,
  RuleEditModal,
} from '../components/admin';

export default function AdminDashboard() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [stats, setStats] = useState<RuleStats | null>(null);
  // ... more state

  return (
    <div className="space-y-6">
      <RuleStatsCards stats={stats} loading={false} />
      <RuleUploadForm onUpload={handleUpload} uploading={false} uploadResult={null} />
      <RuleFilters {...filterProps} />
      <RulesTable rules={rules} loading={false} onEdit={handleEdit} onDelete={handleDelete} />
      <Pagination currentPage={1} totalPages={5} onPageChange={handlePageChange} />
      <RuleEditModal rule={editingRule} onClose={closeModal} onSave={saveRule} />
    </div>
  );
}
```

---

## Comparison: Before vs After

### Before (Monolithic)
- **Single file**: 780 lines in AdminDashboard.tsx
- **Difficult to maintain**: All logic in one component
- **Hard to test**: Tightly coupled code
- **Dark theme**: Didn't match project style

### After (Modular)
- **7 files**: Main page + 6 reusable components
- **Easy to maintain**: Separation of concerns
- **Easy to test**: Each component isolated
- **Light theme**: Matches Submissions page style
- **Reusable**: Can use components elsewhere
- **Clear props**: Well-defined interfaces

---

## Testing

Each component should be tested independently:

```tsx
// Example: RulesTable.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { RulesTable } from './RulesTable';

test('renders rules correctly', () => {
  const mockRules = [
    { id: '1', category: 'irdai', rule_text: 'Test rule', severity: 'high', ... }
  ];

  render(
    <RulesTable
      rules={mockRules}
      loading={false}
      onEdit={jest.fn()}
      onDelete={jest.fn()}
    />
  );

  expect(screen.getByText('Test rule')).toBeInTheDocument();
});
```

---

## Best Practices

1. **Component Size**: Keep components under 200 lines
2. **Props**: Use TypeScript interfaces for type safety
3. **Callbacks**: Use `(value) => void` pattern for handlers
4. **Loading States**: Always handle loading state
5. **Empty States**: Provide helpful messages
6. **Accessibility**: Use semantic HTML, labels, ARIA attributes
7. **Responsive**: Test on mobile, tablet, desktop
8. **Consistency**: Follow existing component patterns

---

## Future Enhancements

- **Sorting**: Add sort functionality to RulesTable
- **Bulk Actions**: Select multiple rules for bulk operations
- **Export**: Download rules as CSV/JSON
- **Import**: Upload rules from file
- **History**: Show rule change history
- **Preview**: Preview rule before saving
