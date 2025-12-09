import React from 'react';
import { SeverityWeights, SEVERITY_PRESETS } from '../../lib/types';

interface Props {
    weights: SeverityWeights;
    onChange: (weights: SeverityWeights) => void;
    disabled?: boolean;
}

const SEVERITY_COLORS = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-blue-500',
};

const SEVERITY_LABELS = {
    critical: 'Critical',
    high: 'High',
    medium: 'Medium',
    low: 'Low',
};

export const SeverityWeightSlider: React.FC<Props> = ({
    weights,
    onChange,
    disabled = false
}) => {
    const handleSliderChange = (severity: keyof SeverityWeights, value: number) => {
        onChange({
            ...weights,
            [severity]: value,
        });
    };

    const applyPreset = (presetName: keyof typeof SEVERITY_PRESETS) => {
        onChange(SEVERITY_PRESETS[presetName]);
    };

    return (
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-lg font-semibold text-gray-900">Severity Weights</h3>
                    <p className="text-sm text-gray-500 mt-1">
                        Adjust how much each severity level affects the score
                    </p>
                </div>

                {/* Presets */}
                <div className="flex gap-2">
                    <button
                        onClick={() => applyPreset('lenient')}
                        disabled={disabled}
                        className="px-3 py-1.5 text-xs font-medium rounded-lg bg-green-50 text-green-700 hover:bg-green-100 transition-colors disabled:opacity-50"
                    >
                        Lenient
                    </button>
                    <button
                        onClick={() => applyPreset('balanced')}
                        disabled={disabled}
                        className="px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors disabled:opacity-50"
                    >
                        Balanced
                    </button>
                    <button
                        onClick={() => applyPreset('strict')}
                        disabled={disabled}
                        className="px-3 py-1.5 text-xs font-medium rounded-lg bg-red-50 text-red-700 hover:bg-red-100 transition-colors disabled:opacity-50"
                    >
                        Strict
                    </button>
                </div>
            </div>

            <div className="space-y-5">
                {(Object.keys(SEVERITY_LABELS) as Array<keyof SeverityWeights>).map((severity) => (
                    <div key={severity} className="flex items-center gap-4">
                        {/* Severity Label */}
                        <div className="w-24 flex items-center gap-2">
                            <span className={`w-3 h-3 rounded-full ${SEVERITY_COLORS[severity]}`}></span>
                            <span className="text-sm font-medium text-gray-700">
                                {SEVERITY_LABELS[severity]}
                            </span>
                        </div>

                        {/* Slider */}
                        <div className="flex-1 relative">
                            <input
                                type="range"
                                min="0"
                                max="3"
                                step="0.1"
                                value={weights[severity]}
                                onChange={(e) => handleSliderChange(severity, parseFloat(e.target.value))}
                                disabled={disabled}
                                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                                style={{
                                    background: `linear-gradient(to right, ${severity === 'critical' ? '#ef4444' :
                                            severity === 'high' ? '#f97316' :
                                                severity === 'medium' ? '#eab308' : '#3b82f6'
                                        } 0%, ${severity === 'critical' ? '#ef4444' :
                                            severity === 'high' ? '#f97316' :
                                                severity === 'medium' ? '#eab308' : '#3b82f6'
                                        } ${(weights[severity] / 3) * 100}%, #e5e7eb ${(weights[severity] / 3) * 100}%, #e5e7eb 100%)`
                                }}
                            />
                            {/* Value markers */}
                            <div className="flex justify-between text-xs text-gray-400 mt-1">
                                <span>0</span>
                                <span>1</span>
                                <span>2</span>
                                <span>3</span>
                            </div>
                        </div>

                        {/* Current Value */}
                        <div className="w-16 text-right">
                            <span className="text-lg font-bold text-gray-900">
                                {weights[severity].toFixed(1)}x
                            </span>
                        </div>
                    </div>
                ))}
            </div>

            {/* Weight Description */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div className="text-sm text-gray-600">
                        <p className="font-medium text-gray-700 mb-1">How weights work:</p>
                        <ul className="list-disc list-inside space-y-1">
                            <li><strong>0.0</strong> = Ignore violations of this severity</li>
                            <li><strong>1.0</strong> = Standard deduction (no multiplier)</li>
                            <li><strong>2.0+</strong> = Harsh penalties (deduction doubled)</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SeverityWeightSlider;
