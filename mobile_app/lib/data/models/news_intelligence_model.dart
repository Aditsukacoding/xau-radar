class NewsScenarioModel {
  final String label;
  final String condition;
  final String yieldDxyReaction;
  final String goldReaction;
  final String targetArea;
  final String invalidationLevel;

  NewsScenarioModel({
    required this.label,
    required this.condition,
    required this.yieldDxyReaction,
    required this.goldReaction,
    required this.targetArea,
    required this.invalidationLevel,
  });

  factory NewsScenarioModel.fromJson(Map<String, dynamic> json) {
    return NewsScenarioModel(
      label: json['label'] ?? '',
      condition: json['condition'] ?? '',
      yieldDxyReaction: json['yield_dxy_reaction'] ?? '',
      goldReaction: json['gold_reaction'] ?? '',
      targetArea: json['target_area'] ?? '',
      invalidationLevel: json['invalidation_level'] ?? '',
    );
  }
}

class NewsIntelligenceModel {
  final String symbol;
  final String eventTitle;
  final String scheduledAtWib;
  final String scheduledAtUtc;
  final String consensus;
  final String previous;
  final String marketRegime;
  final String marketRegimeEvidence;
  final String fundamentalSummary;
  final String geopoliticalSummary;
  final String positioningSentiment;
  final String chartConditionH4;
  final String chartConditionM30;
  final String chartConditionM5;
  final List<double> keySupportLevels;
  final List<double> keyResistanceLevels;
  final String invalidationLevel;
  final String bias;
  final String confidenceLevel;
  final List<NewsScenarioModel> scenarios;
  final List<String> catalystsToWatch;
  final List<Map<String, String>> pendingCatalysts;
  final String disclaimer;
  final String analyzedAtWib;

  NewsIntelligenceModel({
    required this.symbol,
    required this.eventTitle,
    required this.scheduledAtWib,
    required this.scheduledAtUtc,
    required this.consensus,
    required this.previous,
    required this.marketRegime,
    required this.marketRegimeEvidence,
    required this.fundamentalSummary,
    required this.geopoliticalSummary,
    required this.positioningSentiment,
    required this.chartConditionH4,
    required this.chartConditionM30,
    required this.chartConditionM5,
    required this.keySupportLevels,
    required this.keyResistanceLevels,
    required this.invalidationLevel,
    required this.bias,
    required this.confidenceLevel,
    required this.scenarios,
    required this.catalystsToWatch,
    required this.pendingCatalysts,
    required this.disclaimer,
    required this.analyzedAtWib,
  });

  factory NewsIntelligenceModel.fromJson(Map<String, dynamic> json) {
    return NewsIntelligenceModel(
      symbol: json['symbol'] ?? 'XAUUSD',
      eventTitle: json['event_title'] ?? 'US Non-Farm Payrolls',
      scheduledAtWib: json['scheduled_at_wib'] ?? '',
      scheduledAtUtc: json['scheduled_at_utc'] ?? '',
      consensus: json['consensus'] ?? '-',
      previous: json['previous'] ?? '-',
      marketRegime: json['market_regime'] ?? 'Energy-Driven Inflation Shock',
      marketRegimeEvidence: json['market_regime_evidence'] ?? '',
      fundamentalSummary: json['fundamental_summary'] ?? '',
      geopoliticalSummary: json['geopolitical_summary'] ?? '',
      positioningSentiment: json['positioning_sentiment'] ?? '',
      chartConditionH4: json['chart_condition_h4'] ?? '',
      chartConditionM30: json['chart_condition_m30'] ?? '',
      chartConditionM5: json['chart_condition_m5'] ?? '',
      keySupportLevels: (json['key_support_levels'] as List<dynamic>?)
              ?.map((e) => (e as num).toDouble())
              .toList() ??
          [],
      keyResistanceLevels: (json['key_resistance_levels'] as List<dynamic>?)
              ?.map((e) => (e as num).toDouble())
              .toList() ??
          [],
      invalidationLevel: json['invalidation_level'] ?? '',
      bias: json['bias'] ?? 'NEUTRAL',
      confidenceLevel: json['confidence_level'] ?? 'Sedang',
      scenarios: (json['scenarios'] as List<dynamic>?)
              ?.map((e) => NewsScenarioModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      catalystsToWatch: (json['catalysts_to_watch'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      pendingCatalysts: (json['pending_catalysts'] as List<dynamic>?)
              ?.map((e) => Map<String, String>.from(e as Map))
              .toList() ??
          [],
      disclaimer: json['disclaimer'] ?? '',
      analyzedAtWib: json['analyzed_at_wib'] ?? '',
    );
  }
}
