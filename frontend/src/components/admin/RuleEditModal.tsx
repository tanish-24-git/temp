import React, { useState, useEffect } from 'react';
import { Rule } from '../../lib/types';

interface RuleEditModalProps {
  rule: Rule | null;
  onClose: () => void;
  onSave: (ruleId: string, updates: Partial<Rule>) => Promise<void>;
}

export const RuleEditModal: React.FC<RuleEditModalProps> = ({ rule, onClose, onSave }) => {
  const [formData, setFormData] = useState<Partial<Rule>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (rule) {
      setFormData({
        rule_text: rule.rule_text,
        severity: rule.severity,
        category: rule.category,
        points_deduction: rule.points_deduction,
        is_active: rule.is_active,
        keywords: rule.keywords,
        pattern: rule.pattern,
      });
    }
  }, [rule]);

  if (!rule) return null;

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(rule.id, formData);
      onClose();
    } catch (error) {
      console.error('Failed to save rule:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-semibold text-gray-900">Edit Rule</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Form */}
          <div className="space-y-4">
            {/* Rule Text */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Rule Text
              </label>
              <textarea
                value={formData.rule_text || ''}
                onChange={(e) => setFormData({ ...formData, rule_text: e.target.value })}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Category and Severity */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category
                </label>
                <select
                  value={formData.category || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, category: e.target.value as any })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="irdai">IRDAI</option>
                  <option value="brand">Brand</option>
                  <option value="seo">SEO</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Severity
                </label>
                <select
                  value={formData.severity || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, severity: e.target.value as any })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>

            {/* Points Deduction with Slider */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Points Deduction
              </label>

              {/* Suggested points based on severity */}
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xs text-gray-500">Suggested for {formData.severity}:</span>
                {(['critical', 'high', 'medium', 'low'] as const).map((sev) => (
                  <button
                    key={sev}
                    type="button"
                    onClick={() => {
                      const suggestedPoints = {
                        critical: -20,
                        high: -10,
                        medium: -5,
                        low: -2
                      };
                      setFormData({ ...formData, points_deduction: suggestedPoints[sev], severity: sev });
                    }}
                    className={`px-2 py-1 text-xs rounded-md transition-colors ${formData.severity === sev
                        ? sev === 'critical' ? 'bg-red-100 text-red-800 ring-2 ring-red-400' :
                          sev === 'high' ? 'bg-orange-100 text-orange-800 ring-2 ring-orange-400' :
                            sev === 'medium' ? 'bg-yellow-100 text-yellow-800 ring-2 ring-yellow-400' :
                              'bg-blue-100 text-blue-800 ring-2 ring-blue-400'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                  >
                    {sev.charAt(0).toUpperCase() + sev.slice(1)}
                  </button>
                ))}
              </div>

              {/* Slider */}
              <div className="space-y-2">
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="-50"
                    max="0"
                    step="1"
                    value={formData.points_deduction || 0}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        points_deduction: parseFloat(e.target.value),
                      })
                    }
                    className="flex-1 h-3 rounded-lg appearance-none cursor-pointer"
                    style={{
                      background: `linear-gradient(to right, #ef4444 0%, #f97316 25%, #eab308 50%, #22c55e 75%, #22c55e 100%)`
                    }}
                  />
                  <div className="w-20 text-right">
                    <span className={`text-2xl font-bold ${(formData.points_deduction || 0) <= -20 ? 'text-red-600' :
                        (formData.points_deduction || 0) <= -10 ? 'text-orange-600' :
                          (formData.points_deduction || 0) <= -5 ? 'text-yellow-600' :
                            'text-green-600'
                      }`}>
                      {formData.points_deduction || 0}
                    </span>
                  </div>
                </div>

                {/* Visual scale */}
                <div className="flex justify-between text-xs text-gray-400">
                  <span>-50 (Harsh)</span>
                  <span>-25</span>
                  <span>0 (None)</span>
                </div>

                {/* Impact preview */}
                <div className={`mt-2 p-3 rounded-lg ${(formData.points_deduction || 0) <= -20 ? 'bg-red-50 border border-red-200' :
                    (formData.points_deduction || 0) <= -10 ? 'bg-orange-50 border border-orange-200' :
                      (formData.points_deduction || 0) <= -5 ? 'bg-yellow-50 border border-yellow-200' :
                        'bg-green-50 border border-green-200'
                  }`}>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-700">Impact:</span>
                    <span className={`text-sm font-semibold ${(formData.points_deduction || 0) <= -20 ? 'text-red-700' :
                        (formData.points_deduction || 0) <= -10 ? 'text-orange-700' :
                          (formData.points_deduction || 0) <= -5 ? 'text-yellow-700' :
                            'text-green-700'
                      }`}>
                      {(formData.points_deduction || 0) <= -20 ? 'Severe penalty - strongly discouraged content' :
                        (formData.points_deduction || 0) <= -10 ? 'Significant penalty - likely violation' :
                          (formData.points_deduction || 0) <= -5 ? 'Moderate penalty - needs attention' :
                            'Minor penalty - soft warning'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Keywords */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Keywords (comma-separated)
              </label>
              <input
                type="text"
                value={formData.keywords?.join(', ') || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    keywords: e.target.value.split(',').map((k) => k.trim()),
                  })
                }
                placeholder="misleading, guarantee, returns"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Pattern */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Regex Pattern (optional)
              </label>
              <input
                type="text"
                value={formData.pattern || ''}
                onChange={(e) => setFormData({ ...formData, pattern: e.target.value })}
                placeholder="e.g., (?i)guarantee.*return"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              />
            </div>

            {/* Active Status */}
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active || false}
                onChange={(e) =>
                  setFormData({ ...formData, is_active: e.target.checked })
                }
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
                Active (rule will be used in compliance checks)
              </label>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            <button
              onClick={handleSave}
              disabled={saving}
              className={`flex-1 px-6 py-3 rounded-lg font-medium transition-colors ${saving
                  ? 'bg-blue-400 text-white cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
            <button
              onClick={onClose}
              disabled={saving}
              className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition-colors disabled:cursor-not-allowed"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
