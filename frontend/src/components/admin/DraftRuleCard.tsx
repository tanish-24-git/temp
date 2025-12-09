import React, { useState } from 'react';
import { DraftRule } from '../../lib/types';
import { api } from '../../lib/api';

// POC: Hard-coded super admin user ID
const SUPER_ADMIN_USER_ID = '11111111-1111-1111-1111-111111111111';

interface DraftRuleCardProps {
    rule: DraftRule;
    onUpdate: (tempId: string, updates: Partial<DraftRule>) => void;
    onApprove: (tempId: string) => void;
    onReject: (tempId: string) => void;
}

const SEVERITY_COLORS = {
    critical: 'bg-red-100 text-red-800 border-red-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-green-100 text-green-800 border-green-200',
};

const CATEGORY_COLORS = {
    irdai: 'bg-blue-100 text-blue-800',
    brand: 'bg-purple-100 text-purple-800',
    seo: 'bg-teal-100 text-teal-800',
};

export const DraftRuleCard: React.FC<DraftRuleCardProps> = ({
    rule,
    onUpdate,
    onApprove,
    onReject,
}) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editedText, setEditedText] = useState(rule.rule_text);
    const [editedSeverity, setEditedSeverity] = useState(rule.severity);
    const [editedCategory, setEditedCategory] = useState(rule.category);
    const [editedPoints, setEditedPoints] = useState(rule.points_deduction);
    const [editedKeywords, setEditedKeywords] = useState(rule.keywords.join(', '));
    const [isRefining, setIsRefining] = useState(false);
    const [refineInstruction, setRefineInstruction] = useState('');
    const [showRefineInput, setShowRefineInput] = useState(false);

    const handleSaveEdit = () => {
        onUpdate(rule.temp_id, {
            rule_text: editedText,
            severity: editedSeverity as DraftRule['severity'],
            category: editedCategory as DraftRule['category'],
            points_deduction: editedPoints,
            keywords: editedKeywords.split(',').map(k => k.trim()).filter(k => k),
        });
        setIsEditing(false);
    };

    const handleRefineWithAI = async () => {
        if (!refineInstruction.trim()) return;

        setIsRefining(true);
        try {
            const response = await api.refineRule(
                {
                    rule_text: editedText || rule.rule_text,
                    refinement_instruction: refineInstruction,
                    category: editedCategory || rule.category,
                    severity: editedSeverity || rule.severity,
                },
                SUPER_ADMIN_USER_ID
            );

            if (response.data.success) {
                setEditedText(response.data.refined_text);
                if (response.data.refined_keywords.length > 0) {
                    setEditedKeywords(response.data.refined_keywords.join(', '));
                }
                setIsEditing(true);
            }
        } catch (error) {
            console.error('Failed to refine rule:', error);
        } finally {
            setIsRefining(false);
            setShowRefineInput(false);
            setRefineInstruction('');
        }
    };

    const isApproved = rule.is_approved;

    return (
        <div
            className={`bg-white rounded-xl border-2 shadow-lg p-6 transition-all duration-300 hover:shadow-xl ${isApproved ? 'border-green-300' : 'border-red-300 opacity-75'
                }`}
        >
            {/* Header with badges */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${CATEGORY_COLORS[rule.category]}`}>
                        {rule.category.toUpperCase()}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${SEVERITY_COLORS[rule.severity]}`}>
                        {rule.severity.toUpperCase()}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-500">
                        Points: {rule.points_deduction}
                    </span>
                    {isApproved ? (
                        <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                            ✓ Approved
                        </span>
                    ) : (
                        <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">
                            ✗ Rejected
                        </span>
                    )}
                </div>
            </div>

            {/* Rule Text */}
            {isEditing ? (
                <div className="space-y-4 mb-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Rule Text</label>
                        <textarea
                            value={editedText}
                            onChange={(e) => setEditedText(e.target.value)}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                            rows={3}
                        />
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                            <select
                                value={editedCategory}
                                onChange={(e) => setEditedCategory(e.target.value as DraftRule['category'])}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="irdai">IRDAI</option>
                                <option value="brand">Brand</option>
                                <option value="seo">SEO</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
                            <select
                                value={editedSeverity}
                                onChange={(e) => setEditedSeverity(e.target.value as DraftRule['severity'])}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="critical">Critical</option>
                                <option value="high">High</option>
                                <option value="medium">Medium</option>
                                <option value="low">Low</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Points</label>
                            <input
                                type="number"
                                value={editedPoints}
                                onChange={(e) => setEditedPoints(Number(e.target.value))}
                                max={0}
                                min={-50}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Keywords (comma-separated)</label>
                        <input
                            type="text"
                            value={editedKeywords}
                            onChange={(e) => setEditedKeywords(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            placeholder="keyword1, keyword2, keyword3"
                        />
                    </div>

                    <div className="flex gap-2">
                        <button
                            onClick={handleSaveEdit}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Save Changes
                        </button>
                        <button
                            onClick={() => {
                                setIsEditing(false);
                                setEditedText(rule.rule_text);
                                setEditedSeverity(rule.severity);
                                setEditedCategory(rule.category);
                                setEditedPoints(rule.points_deduction);
                                setEditedKeywords(rule.keywords.join(', '));
                            }}
                            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            ) : (
                <p className="text-gray-800 mb-4 leading-relaxed">{rule.rule_text}</p>
            )}

            {/* Keywords */}
            {!isEditing && (
                <div className="flex flex-wrap gap-2 mb-4">
                    {rule.keywords.map((keyword, idx) => (
                        <span
                            key={idx}
                            className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
                        >
                            {keyword}
                        </span>
                    ))}
                </div>
            )}

            {/* AI Refine Input */}
            {showRefineInput && (
                <div className="mb-4 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
                    <label className="block text-sm font-medium text-purple-700 mb-2">
                        ✨ How would you like to refine this rule?
                    </label>
                    <input
                        type="text"
                        value={refineInstruction}
                        onChange={(e) => setRefineInstruction(e.target.value)}
                        placeholder="e.g., Make it more specific, add examples, simplify language..."
                        className="w-full px-4 py-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 mb-2"
                    />
                    <div className="flex gap-2">
                        <button
                            onClick={handleRefineWithAI}
                            disabled={isRefining || !refineInstruction.trim()}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${isRefining || !refineInstruction.trim()
                                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                    : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700'
                                }`}
                        >
                            {isRefining ? (
                                <span className="flex items-center">
                                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                    </svg>
                                    Refining...
                                </span>
                            ) : (
                                '✨ Refine with AI'
                            )}
                        </button>
                        <button
                            onClick={() => {
                                setShowRefineInput(false);
                                setRefineInstruction('');
                            }}
                            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <div className="flex gap-2">
                    {!isEditing && (
                        <>
                            <button
                                onClick={() => setIsEditing(true)}
                                className="px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                            >
                                ✏️ Edit
                            </button>
                            <button
                                onClick={() => setShowRefineInput(!showRefineInput)}
                                className="px-3 py-2 text-sm bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors"
                            >
                                ✨ Refine with AI
                            </button>
                        </>
                    )}
                </div>

                <div className="flex gap-2">
                    {isApproved ? (
                        <button
                            onClick={() => onReject(rule.temp_id)}
                            className="px-4 py-2 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors font-medium"
                        >
                            ✗ Reject
                        </button>
                    ) : (
                        <button
                            onClick={() => onApprove(rule.temp_id)}
                            className="px-4 py-2 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors font-medium"
                        >
                            ✓ Approve
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};
