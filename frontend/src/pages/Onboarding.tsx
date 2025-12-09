import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { CheckCircle, Sparkles, Building2, Target, ArrowRight, ArrowLeft, Loader2 } from 'lucide-react';

// Industry options
const INDUSTRIES = [
    { value: 'insurance', label: 'Insurance', icon: '🛡️', description: 'IRDAI regulations & guidelines' },
    { value: 'healthcare', label: 'Healthcare', icon: '⚕️', description: 'HIPAA, FDA compliance' },
    { value: 'finance', label: 'Finance & Banking', icon: '💰', description: 'SEBI, RBI regulations' },
    { value: 'ecommerce', label: 'E-Commerce', icon: '🛒', description: 'Consumer protection laws' },
    { value: 'technology', label: 'Technology', icon: '💻', description: 'GDPR, data privacy' },
    { value: 'other', label: 'Other', icon: '🏢', description: 'General compliance' },
];

// Analysis scope options
const ANALYSIS_SCOPES = [
    {
        value: 'regulatory',
        label: 'Regulatory Compliance',
        icon: '⚖️',
        description: 'Industry-specific regulations and legal requirements'
    },
    {
        value: 'brand',
        label: 'Brand Guidelines',
        icon: '🎨',
        description: 'Brand voice, tone, and visual identity standards'
    },
    {
        value: 'seo',
        label: 'SEO Optimization',
        icon: '🔍',
        description: 'Search engine optimization best practices'
    },
    {
        value: 'qualitative',
        label: 'Qualitative Assessment',
        icon: '✨',
        description: 'Consumer-friendly language and readability'
    },
];

const OnboardingWizard: React.FC = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    // Form state
    const [formData, setFormData] = useState({
        industry: '',
        brand_name: '',
        brand_guidelines: '',
        analysis_scope: ['regulatory', 'brand', 'seo'] as string[],
    });

    const totalSteps = 4;

    const handleIndustrySelect = (industry: string) => {
        setFormData({ ...formData, industry });
    };

    const handleScopeToggle = (scope: string) => {
        const currentScopes = formData.analysis_scope;
        if (currentScopes.includes(scope)) {
            setFormData({
                ...formData,
                analysis_scope: currentScopes.filter(s => s !== scope),
            });
        } else {
            setFormData({
                ...formData,
                analysis_scope: [...currentScopes, scope],
            });
        }
    };

    const handleNext = () => {
        if (step < totalSteps) {
            setStep(step + 1);
        }
    };

    const handleBack = () => {
        if (step > 1) {
            setStep(step - 1);
        }
    };

    const handleSubmit = async () => {
        setLoading(true);
        setError(null);

        try {
            // Get user ID from localStorage or use demo user
            const userId = localStorage.getItem('userId') || 'demo-user-id';

            const response = await api.startOnboarding({
                user_id: userId,
                industry: formData.industry,
                brand_name: formData.brand_name,
                brand_guidelines: formData.brand_guidelines,
                analysis_scope: formData.analysis_scope,
                region: 'India',
            });

            setSuccess(true);

            // Show success for 2 seconds, then redirect
            setTimeout(() => {
                navigate('/dashboard');
            }, 2000);
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'Onboarding failed');
        } finally {
            setLoading(false);
        }
    };

    const canProceed = () => {
        switch (step) {
            case 1:
                return formData.industry !== '';
            case 2:
                return formData.brand_name.trim() !== '';
            case 3:
                return formData.analysis_scope.length > 0;
            case 4:
                return true;
            default:
                return false;
        }
    };

    if (success) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-8">
                <div className="bg-white rounded-2xl shadow-2xl p-12 max-w-md text-center animate-fade-in">
                    <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <CheckCircle className="w-12 h-12 text-green-600" />
                    </div>
                    <h2 className="text-3xl font-bold text-gray-900 mb-4">All Set!</h2>
                    <p className="text-gray-600 mb-2">Your compliance rules are ready.</p>
                    <p className="text-sm text-gray-500">Redirecting to dashboard...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="text-center mb-12">
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-100 rounded-full mb-4">
                        <Sparkles className="w-5 h-5 text-indigo-600" />
                        <span className="text-sm font-semibold text-indigo-700">Adaptive Compliance Engine</span>
                    </div>
                    <h1 className="text-4xl font-bold text-gray-900 mb-3">Welcome! Let's Get Started</h1>
                    <p className="text-lg text-gray-600">
                        We'll personalize your compliance analysis in just a few steps
                    </p>
                </div>

                {/* Progress Bar */}
                <div className="mb-12">
                    <div className="flex items-center justify-between mb-2">
                        {[1, 2, 3, 4].map((num) => (
                            <div key={num} className="flex items-center">
                                <div
                                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all ${num < step
                                            ? 'bg-green-500 text-white'
                                            : num === step
                                                ? 'bg-indigo-600 text-white ring-4 ring-indigo-200'
                                                : 'bg-gray-200 text-gray-500'
                                        }`}
                                >
                                    {num < step ? <CheckCircle className="w-5 h-5" /> : num}
                                </div>
                                {num < totalSteps && (
                                    <div
                                        className={`w-24 h-1 mx-2 transition-all ${num < step ? 'bg-green-500' : 'bg-gray-200'
                                            }`}
                                    />
                                )}
                            </div>
                        ))}
                    </div>
                    <div className="flex justify-between text-xs text-gray-500 px-2">
                        <span>Industry</span>
                        <span>Brand</span>
                        <span>Scope</span>
                        <span>Review</span>
                    </div>
                </div>

                {/* Card Container */}
                <div className="bg-white rounded-2xl shadow-xl p-8 sm:p-12">
                    {/* Error Message */}
                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-red-800 text-sm">{error}</p>
                        </div>
                    )}

                    {/* Step 1: Industry Selection */}
                    {step === 1 && (
                        <div className="animate-fade-in">
                            <div className="flex items-center gap-3 mb-6">
                                <Building2 className="w-8 h-8 text-indigo-600" />
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-900">Select Your Industry</h2>
                                    <p className="text-gray-600">We'll find relevant regulations for you</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {INDUSTRIES.map((industry) => (
                                    <button
                                        key={industry.value}
                                        onClick={() => handleIndustrySelect(industry.value)}
                                        className={`p-6 rounded-xl border-2 transition-all text-left hover:shadow-lg ${formData.industry === industry.value
                                                ? 'border-indigo-600 bg-indigo-50 ring-2 ring-indigo-200'
                                                : 'border-gray-200 hover:border-indigo-300'
                                            }`}
                                    >
                                        <div className="flex items-start gap-4">
                                            <span className="text-4xl">{industry.icon}</span>
                                            <div className="flex-1">
                                                <h3 className="font-semibold text-gray-900 mb-1">{industry.label}</h3>
                                                <p className="text-sm text-gray-600">{industry.description}</p>
                                            </div>
                                            {formData.industry === industry.value && (
                                                <CheckCircle className="w-6 h-6 text-indigo-600 flex-shrink-0" />
                                            )}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Step 2: Brand Information */}
                    {step === 2 && (
                        <div className="animate-fade-in">
                            <div className="flex items-center gap-3 mb-6">
                                <Target className="w-8 h-8 text-indigo-600" />
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-900">Tell Us About Your Brand</h2>
                                    <p className="text-gray-600">This helps us tailor the analysis</p>
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                                        Brand Name *
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.brand_name}
                                        onChange={(e) =>
                                            setFormData({ ...formData, brand_name: e.target.value })
                                        }
                                        placeholder="e.g., SecureLife Insurance"
                                        className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 outline-none transition-all"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                                        Brand Guidelines (Optional)
                                    </label>
                                    <textarea
                                        value={formData.brand_guidelines}
                                        onChange={(e) =>
                                            setFormData({ ...formData, brand_guidelines: e.target.value })
                                        }
                                        placeholder="Paste your brand guidelines here, or leave blank..."
                                        rows={6}
                                        className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 outline-none transition-all resize-none"
                                    />
                                    <p className="text-xs text-gray-500 mt-2">
                                        Adding guidelines helps generate more accurate brand compliance rules
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Step 3: Analysis Scope */}
                    {step === 3 && (
                        <div className="animate-fade-in">
                            <div className="flex items-center gap-3 mb-6">
                                <CheckCircle className="w-8 h-8 text-indigo-600" />
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-900">Choose Analysis Scope</h2>
                                    <p className="text-gray-600">Select what you want us to check (at least one)</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {ANALYSIS_SCOPES.map((scope) => (
                                    <button
                                        key={scope.value}
                                        onClick={() => handleScopeToggle(scope.value)}
                                        className={`p-6 rounded-xl border-2 transition-all text-left hover:shadow-lg ${formData.analysis_scope.includes(scope.value)
                                                ? 'border-indigo-600 bg-indigo-50'
                                                : 'border-gray-200 hover:border-indigo-300'
                                            }`}
                                    >
                                        <div className="flex items-start gap-4">
                                            <span className="text-4xl">{scope.icon}</span>
                                            <div className="flex-1">
                                                <h3 className="font-semibold text-gray-900 mb-1">{scope.label}</h3>
                                                <p className="text-sm text-gray-600">{scope.description}</p>
                                            </div>
                                            <div
                                                className={`w-6 h-6 rounded border-2 flex items-center justify-center flex-shrink-0 transition-all ${formData.analysis_scope.includes(scope.value)
                                                        ? 'bg-indigo-600 border-indigo-600'
                                                        : 'border-gray-300'
                                                    }`}
                                            >
                                                {formData.analysis_scope.includes(scope.value) && (
                                                    <CheckCircle className="w-4 h-4 text-white" />
                                                )}
                                            </div>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Step 4: Review & Submit */}
                    {step === 4 && (
                        <div className="animate-fade-in">
                            <div className="flex items-center gap-3 mb-6">
                                <Sparkles className="w-8 h-8 text-indigo-600" />
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-900">Review Your Setup</h2>
                                    <p className="text-gray-600">Ready to generate your compliance rules?</p>
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div className="p-6 bg-gray-50 rounded-lg">
                                    <h3 className="font-semibold text-gray-900 mb-4">Configuration Summary</h3>

                                    <div className="space-y-3">
                                        <div>
                                            <span className="text-sm text-gray-600">Industry:</span>
                                            <p className="font-medium text-gray-900">
                                                {INDUSTRIES.find(i => i.value === formData.industry)?.label}
                                            </p>
                                        </div>

                                        <div>
                                            <span className="text-sm text-gray-600">Brand Name:</span>
                                            <p className="font-medium text-gray-900">{formData.brand_name}</p>
                                        </div>

                                        <div>
                                            <span className="text-sm text-gray-600">Analysis Scope:</span>
                                            <div className="flex flex-wrap gap-2 mt-2">
                                                {formData.analysis_scope.map((scope) => {
                                                    const scopeInfo = ANALYSIS_SCOPES.find(s => s.value === scope);
                                                    return (
                                                        <span
                                                            key={scope}
                                                            className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium"
                                                        >
                                                            {scopeInfo?.icon} {scopeInfo?.label}
                                                        </span>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                                    <p className="text-sm text-blue-800">
                                        <strong>What happens next:</strong> We'll search for industry regulations
                                        and generate 5-7 personalized compliance rules tailored to your business.
                                        This usually takes 30-60 seconds.
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Navigation Buttons */}
                    <div className="flex items-center justify-between mt-12 pt-6 border-t">
                        <button
                            onClick={handleBack}
                            disabled={step === 1}
                            className="flex items-center gap-2 px-6 py-3 text-gray-700 hover:bg-gray-100 rounded-lg font-medium transition-all disabled:opacity-0 disabled:pointer-events-none"
                        >
                            <ArrowLeft className="w-5 h-5" />
                            Back
                        </button>

                        {step < totalSteps ? (
                            <button
                                onClick={handleNext}
                                disabled={!canProceed()}
                                className="flex items-center gap-2 px-8 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
                            >
                                Continue
                                <ArrowRight className="w-5 h-5" />
                            </button>
                        ) : (
                            <button
                                onClick={handleSubmit}
                                disabled={loading}
                                className="flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Generating Rules...
                                    </>
                                ) : (
                                    <>
                                        <Sparkles className="w-5 h-5" />
                                        Complete Setup
                                    </>
                                )}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default OnboardingWizard;
