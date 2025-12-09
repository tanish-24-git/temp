import React from 'react';
import { DraftRule, RuleBulkSubmitResponse } from '../../lib/types';
import { DraftRuleCard } from './DraftRuleCard';
import { api } from '../../lib/api';

// POC: Hard-coded super admin user ID
const SUPER_ADMIN_USER_ID = '11111111-1111-1111-1111-111111111111';

interface RulePreviewPanelProps {
    documentTitle: string;
    draftRules: DraftRule[];
    totalExtracted: number;
    errors: string[];
    onRulesChange: (rules: DraftRule[]) => void;
    onSubmitSuccess: (response: RuleBulkSubmitResponse) => void;
    onCancel: () => void;
}

export const RulePreviewPanel: React.FC<RulePreviewPanelProps> = ({
    documentTitle,
    draftRules,
    totalExtracted,
    errors,
    onRulesChange,
    onSubmitSuccess,
    onCancel,
}) => {
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const [submitError, setSubmitError] = React.useState<string | null>(null);

    const approvedCount = draftRules.filter(r => r.is_approved).length;
    const rejectedCount = draftRules.length - approvedCount;

    const handleUpdateRule = (tempId: string, updates: Partial<DraftRule>) => {
        const updatedRules = draftRules.map(rule =>
            rule.temp_id === tempId ? { ...rule, ...updates } : rule
        );
        onRulesChange(updatedRules);
    };

    const handleApprove = (tempId: string) => {
        const updatedRules = draftRules.map(rule =>
            rule.temp_id === tempId ? { ...rule, is_approved: true } : rule
        );
        onRulesChange(updatedRules);
    };

    const handleReject = (tempId: string) => {
        const updatedRules = draftRules.map(rule =>
            rule.temp_id === tempId ? { ...rule, is_approved: false } : rule
        );
        onRulesChange(updatedRules);
    };

    const handleApproveAll = () => {
        const updatedRules = draftRules.map(rule => ({ ...rule, is_approved: true }));
        onRulesChange(updatedRules);
    };

    const handleRejectAll = () => {
        const updatedRules = draftRules.map(rule => ({ ...rule, is_approved: false }));
        onRulesChange(updatedRules);
    };

    const handleSubmit = async () => {
        if (approvedCount === 0) {
            setSubmitError('Please approve at least one rule before submitting.');
            return;
        }

        setIsSubmitting(true);
        setSubmitError(null);

        try {
            const response = await api.bulkSubmitRules(
                {
                    document_title: documentTitle,
                    approved_rules: draftRules.filter(r => r.is_approved),
                },
                SUPER_ADMIN_USER_ID
            );

            onSubmitSuccess(response.data);
        } catch (error: any) {
            setSubmitError(error.response?.data?.detail || 'Failed to save rules');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="bg-gradient-to-br from-blue-50 via-white to-purple-50 rounded-2xl border-2 border-blue-200 shadow-xl p-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                        <span className="text-3xl">📋</span>
                        Review Generated Rules
                    </h2>
                    <p className="text-gray-600 mt-1">
                        Document: <span className="font-semibold text-blue-600">{documentTitle}</span>
                    </p>
                </div>

                <button
                    onClick={onCancel}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                >
                    ✕ Cancel
                </button>
            </div>

            {/* Stats Bar */}
            <div className="grid grid-cols-4 gap-4 mb-6">
                <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm text-center">
                    <p className="text-3xl font-bold text-blue-600">{totalExtracted}</p>
                    <p className="text-sm text-gray-500">Extracted</p>
                </div>
                <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm text-center">
                    <p className="text-3xl font-bold text-purple-600">{draftRules.length}</p>
                    <p className="text-sm text-gray-500">Valid Rules</p>
                </div>
                <div className="bg-white rounded-xl p-4 border border-green-200 shadow-sm text-center">
                    <p className="text-3xl font-bold text-green-600">{approvedCount}</p>
                    <p className="text-sm text-gray-500">Approved</p>
                </div>
                <div className="bg-white rounded-xl p-4 border border-red-200 shadow-sm text-center">
                    <p className="text-3xl font-bold text-red-600">{rejectedCount}</p>
                    <p className="text-sm text-gray-500">Rejected</p>
                </div>
            </div>

            {/* Errors */}
            {errors.length > 0 && (
                <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <h4 className="font-medium text-yellow-800 mb-2">⚠️ Extraction Warnings</h4>
                    <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
                        {errors.slice(0, 5).map((err, idx) => (
                            <li key={idx}>{err}</li>
                        ))}
                        {errors.length > 5 && (
                            <li className="font-medium">...and {errors.length - 5} more</li>
                        )}
                    </ul>
                </div>
            )}

            {/* Bulk Actions */}
            <div className="flex items-center justify-between mb-6 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">
                    Select which rules to save. You can edit any rule before submitting.
                </p>
                <div className="flex gap-2">
                    <button
                        onClick={handleApproveAll}
                        className="px-4 py-2 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors font-medium"
                    >
                        ✓ Approve All
                    </button>
                    <button
                        onClick={handleRejectAll}
                        className="px-4 py-2 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors font-medium"
                    >
                        ✗ Reject All
                    </button>
                </div>
            </div>

            {/* Rules List */}
            <div className="space-y-4 mb-8 max-h-[600px] overflow-y-auto pr-2">
                {draftRules.map((rule) => (
                    <DraftRuleCard
                        key={rule.temp_id}
                        rule={rule}
                        onUpdate={handleUpdateRule}
                        onApprove={handleApprove}
                        onReject={handleReject}
                    />
                ))}
            </div>

            {/* Submit Error */}
            {submitError && (
                <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                    {submitError}
                </div>
            )}

            {/* Submit Section */}
            <div className="flex items-center justify-between pt-6 border-t border-gray-200">
                <p className="text-gray-600">
                    <span className="font-semibold text-green-600">{approvedCount}</span> rules will be saved to the database.
                </p>
                <div className="flex gap-4">
                    <button
                        onClick={onCancel}
                        className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={isSubmitting || approvedCount === 0}
                        className={`px-8 py-3 rounded-lg font-semibold transition-all duration-300 ${isSubmitting || approvedCount === 0
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl'
                            }`}
                    >
                        {isSubmitting ? (
                            <span className="flex items-center">
                                <svg className="animate-spin -ml-1 mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                </svg>
                                Saving Rules...
                            </span>
                        ) : (
                            `Submit ${approvedCount} Approved Rules`
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};
