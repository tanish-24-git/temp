import React from 'react';
import { Rule } from '../../lib/types';
import { Badge } from '../ui/badge';

interface RulesTableProps {
  rules: Rule[];
  loading: boolean;
  onEdit: (rule: Rule) => void;
  onDelete?: (ruleId: string) => void;
  onRestore?: (ruleId: string) => void;
  showRestoreButton?: boolean;
}

export const RulesTable: React.FC<RulesTableProps> = ({
  rules,
  loading,
  onEdit,
  onDelete,
  onRestore,
  showRestoreButton = false,
}) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'irdai':
        return 'bg-purple-100 text-purple-800';
      case 'brand':
        return 'bg-green-100 text-green-800';
      case 'seo':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="text-center py-12 text-gray-500">Loading rules...</div>
      </div>
    );
  }

  if (rules.length === 0) {
    return (
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="text-center py-12 text-gray-500">
          {showRestoreButton
            ? 'No deactivated rules found.'
            : 'No rules found. Try adjusting your filters or upload a document to generate rules.'}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Severity
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Rule Text
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Points
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rules.map((rule) => (
              <tr key={rule.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <Badge className={getCategoryColor(rule.category)}>
                    {rule.category.toUpperCase()}
                  </Badge>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <Badge className={getSeverityColor(rule.severity)}>
                    {rule.severity}
                  </Badge>
                </td>
                <td className="px-6 py-4">
                  <div className="max-w-md">
                    <div className="text-sm text-gray-900 line-clamp-2" title={rule.rule_text}>
                      {rule.rule_text}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm font-mono text-gray-900">
                    {rule.points_deduction}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <Badge
                    className={
                      rule.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }
                  >
                    {rule.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <button
                    onClick={() => onEdit(rule)}
                    className="text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Edit
                  </button>
                  {showRestoreButton && onRestore ? (
                    <button
                      onClick={() => onRestore(rule.id)}
                      className="text-green-600 hover:text-green-800 font-medium ml-4"
                    >
                      Restore
                    </button>
                  ) : onDelete ? (
                    <button
                      onClick={() => onDelete(rule.id)}
                      className="text-red-600 hover:text-red-800 font-medium ml-4"
                    >
                      Deactivate
                    </button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
