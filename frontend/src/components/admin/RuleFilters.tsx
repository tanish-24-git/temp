import React from 'react';

interface RuleFiltersProps {
  categoryFilter: string;
  severityFilter: string;
  activeFilter: boolean | undefined;
  searchQuery: string;
  onCategoryChange: (value: string) => void;
  onSeverityChange: (value: string) => void;
  onActiveChange: (value: boolean | undefined) => void;
  onSearchChange: (value: string) => void;
  hideActiveFilter?: boolean; // Optional prop to hide status filter when tabs handle this
}

export const RuleFilters: React.FC<RuleFiltersProps> = ({
  categoryFilter,
  severityFilter,
  activeFilter,
  searchQuery,
  onCategoryChange,
  onSeverityChange,
  onActiveChange,
  onSearchChange,
  hideActiveFilter = false,
}) => {
  return (
    <div className="bg-white rounded-lg border p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Filter Rules</h2>
      <div className={`grid grid-cols-1 gap-4 ${hideActiveFilter ? 'md:grid-cols-3' : 'md:grid-cols-4'}`}>
        {/* Category Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Category
          </label>
          <select
            value={categoryFilter}
            onChange={(e) => onCategoryChange(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Categories</option>
            <option value="irdai">IRDAI</option>
            <option value="brand">Brand</option>
            <option value="seo">SEO</option>
          </select>
        </div>

        {/* Severity Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Severity
          </label>
          <select
            value={severityFilter}
            onChange={(e) => onSeverityChange(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        {/* Status Filter - Hidden when tabs handle this */}
        {!hideActiveFilter && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={activeFilter === undefined ? '' : activeFilter ? 'true' : 'false'}
              onChange={(e) =>
                onActiveChange(
                  e.target.value === '' ? undefined : e.target.value === 'true'
                )
              }
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Status</option>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </div>
        )}

        {/* Search */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Search
          </label>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search rule text..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>
    </div>
  );
};
