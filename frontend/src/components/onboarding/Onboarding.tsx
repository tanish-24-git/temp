import React, { useState, useEffect } from 'react';

interface OnboardingProps {
    onComplete: () => void;
}

const ONBOARDING_STEPS = [
    {
        icon: '🚀',
        title: 'Welcome to Compliance Agent',
        description: 'Your AI-powered insurance marketing compliance platform. Let\'s take a quick tour!',
    },
    {
        icon: '📄',
        title: 'Upload Content for Review',
        description: 'Upload your marketing materials in PDF, HTML, Markdown, or DOCX format. Our AI will analyze them for compliance issues.',
    },
    {
        icon: '✨',
        title: 'AI-Powered Rule Generation',
        description: 'Admins can upload regulatory documents to automatically generate compliance rules using AI. Review and refine rules before saving.',
    },
    {
        icon: '📊',
        title: 'Detailed Compliance Reports',
        description: 'Get comprehensive reports with violation details, severity levels, and suggested fixes. Track your compliance score over time.',
    },
];

export const Onboarding: React.FC<OnboardingProps> = ({ onComplete }) => {
    const [currentStep, setCurrentStep] = useState(0);
    const [isVisible, setIsVisible] = useState(true);
    const [dontShowAgain, setDontShowAgain] = useState(false);

    useEffect(() => {
        const hasSeenOnboarding = localStorage.getItem('compliance-agent-onboarding-seen');
        if (hasSeenOnboarding === 'true') {
            setIsVisible(false);
            onComplete();
        }
    }, [onComplete]);

    const handleNext = () => {
        if (currentStep < ONBOARDING_STEPS.length - 1) {
            setCurrentStep(currentStep + 1);
        } else {
            handleComplete();
        }
    };

    const handleSkip = () => {
        handleComplete();
    };

    const handleComplete = () => {
        if (dontShowAgain) {
            localStorage.setItem('compliance-agent-onboarding-seen', 'true');
        }
        setIsVisible(false);
        onComplete();
    };

    if (!isVisible) return null;

    const step = ONBOARDING_STEPS[currentStep];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full mx-4 overflow-hidden animate-fade-in">
                {/* Progress bar */}
                <div className="h-1 bg-gray-100">
                    <div
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-500"
                        style={{ width: `${((currentStep + 1) / ONBOARDING_STEPS.length) * 100}%` }}
                    />
                </div>

                {/* Content */}
                <div className="p-8 text-center">
                    {/* Icon */}
                    <div className="text-6xl mb-6 animate-bounce-slow">{step.icon}</div>

                    {/* Title */}
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">{step.title}</h2>

                    {/* Description */}
                    <p className="text-gray-600 mb-8 leading-relaxed">{step.description}</p>

                    {/* Step indicators */}
                    <div className="flex justify-center gap-2 mb-8">
                        {ONBOARDING_STEPS.map((_, idx) => (
                            <button
                                key={idx}
                                onClick={() => setCurrentStep(idx)}
                                className={`w-3 h-3 rounded-full transition-all duration-300 ${idx === currentStep
                                        ? 'bg-blue-600 w-8'
                                        : idx < currentStep
                                            ? 'bg-blue-400'
                                            : 'bg-gray-300'
                                    }`}
                            />
                        ))}
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-4">
                        <div className="flex gap-4 justify-center">
                            <button
                                onClick={handleSkip}
                                className="px-6 py-3 text-gray-600 hover:text-gray-800 font-medium transition-colors"
                            >
                                Skip Tour
                            </button>
                            <button
                                onClick={handleNext}
                                className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-300 shadow-lg hover:shadow-xl"
                            >
                                {currentStep < ONBOARDING_STEPS.length - 1 ? 'Next' : 'Get Started'}
                            </button>
                        </div>

                        {/* Don't show again */}
                        <label className="flex items-center justify-center gap-2 text-sm text-gray-500 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={dontShowAgain}
                                onChange={(e) => setDontShowAgain(e.target.checked)}
                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            Don't show this again
                        </label>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Onboarding;
