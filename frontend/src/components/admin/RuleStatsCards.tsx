import React from 'react';
import { RuleStats } from '../../lib/types';

interface RuleStatsCardsProps {
  stats: RuleStats | null;
  loading?: boolean;
}

export const RuleStatsCards: React.FC<RuleStatsCardsProps> = ({ stats, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg border p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-24 mb-3"></div>
            <div className="h-8 bg-gray-200 rounded w-16"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const cards = [
    {
      label: 'Total Rules',
      value: stats.total_rules,
      color: 'text-gray-900',
    },
    {
      label: 'Active Rules',
      value: stats.active_rules,
      color: 'text-green-600',
    },
    {
      label: 'IRDAI Rules',
      value: stats.by_category.irdai,
      color: 'text-purple-600',
    },
    {
      label: 'Critical Rules',
      value: stats.by_severity.critical,
      color: 'text-red-600',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {cards.map((card, index) => (
        <div key={index} className="bg-white rounded-lg border p-6">
          <div className="text-sm font-medium text-gray-500 mb-2">{card.label}</div>
          <div className={`text-3xl font-bold ${card.color}`}>{card.value}</div>
        </div>
      ))}
    </div>
  );
};
