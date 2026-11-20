class IntermarketQuoteItem {
  final double price;
  final double change;
  final double changePct;
  final String trend;
  final String goldEffect;

  IntermarketQuoteItem({
    required this.price,
    required this.change,
    required this.changePct,
    required this.trend,
    required this.goldEffect,
  });

  factory IntermarketQuoteItem.fromJson(Map<String, dynamic> json) {
    return IntermarketQuoteItem(
      price: (json['price'] as num?)?.toDouble() ?? 0.0,
      change: (json['change'] as num?)?.toDouble() ?? 0.0,
      changePct: (json['change_pct'] as num?)?.toDouble() ?? 0.0,
      trend: json['trend']?.toString() ?? 'FLAT',
      goldEffect: json['gold_effect']?.toString() ?? 'NEUTRAL',
    );
  }
}

class IntermarketSnapshotModel {
  final IntermarketQuoteItem? dxy;
  final IntermarketQuoteItem? us10y;
  final IntermarketQuoteItem? wti;
  final double intermarketScore;
  final String marketRegime;
  final String marketRegimeEvidence;
  final String updatedAtWib;

  IntermarketSnapshotModel({
    this.dxy,
    this.us10y,
    this.wti,
    this.intermarketScore = 0.0,
    this.marketRegime = '',
    this.marketRegimeEvidence = '',
    this.updatedAtWib = '',
  });

  factory IntermarketSnapshotModel.fromJson(Map<String, dynamic> json) {
    return IntermarketSnapshotModel(
      dxy: json['dxy'] is Map ? IntermarketQuoteItem.fromJson(Map<String, dynamic>.from(json['dxy'])) : null,
      us10y: json['us10y'] is Map ? IntermarketQuoteItem.fromJson(Map<String, dynamic>.from(json['us10y'])) : null,
      wti: json['wti'] is Map ? IntermarketQuoteItem.fromJson(Map<String, dynamic>.from(json['wti'])) : null,
      intermarketScore: (json['intermarket_score'] as num?)?.toDouble() ?? 0.0,
      marketRegime: json['market_regime']?.toString() ?? '',
      marketRegimeEvidence: json['market_regime_evidence']?.toString() ?? '',
      updatedAtWib: json['updated_at_wib']?.toString() ?? '',
    );
  }
}

class HistoricalReactionItem {
  final String eventTitle;
  final String impactLevel;
  final String releasedAtWib;
  final String actual;
  final String forecast;
  final String previous;
  final String goldImpact;
  final double move1hPips;
  final double range1hPips;
  final String direction;
  final String verdict;

  HistoricalReactionItem({
    required this.eventTitle,
    required this.impactLevel,
    required this.releasedAtWib,
    required this.actual,
    required this.forecast,
    required this.previous,
    required this.goldImpact,
    required this.move1hPips,
    required this.range1hPips,
    required this.direction,
    required this.verdict,
  });

  factory HistoricalReactionItem.fromJson(Map<String, dynamic> json) {
    return HistoricalReactionItem(
      eventTitle: json['event_title']?.toString() ?? '',
      impactLevel: json['impact_level']?.toString() ?? 'HIGH',
      releasedAtWib: json['released_at_wib']?.toString() ?? '',
      actual: json['actual']?.toString() ?? '-',
      forecast: json['forecast']?.toString() ?? '-',
      previous: json['previous']?.toString() ?? '-',
      goldImpact: json['gold_impact']?.toString() ?? 'NEUTRAL',
      move1hPips: (json['move_1h_pips'] as num?)?.toDouble() ?? 0.0,
      range1hPips: (json['range_1h_pips'] as num?)?.toDouble() ?? 0.0,
      direction: json['direction']?.toString() ?? 'WHIPSAW',
      verdict: json['verdict']?.toString() ?? '',
    );
  }
}

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
  final IntermarketSnapshotModel? intermarketSnapshot;
  final String eventComparisonNote;
  final List<HistoricalReactionItem> historicalReactions;
  final String historicalSummary;
  final double avgHistoricalRangePips;
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
    this.intermarketSnapshot,
    this.eventComparisonNote = '',
    this.historicalReactions = const [],
    this.historicalSummary = '',
    this.avgHistoricalRangePips = 0.0,
    required this.disclaimer,
    required this.analyzedAtWib,
  });

  factory NewsIntelligenceModel.fromJson(Map<String, dynamic> json) {
    final rawIntermarket = json['intermarket_snapshot'];
    final rawHist = json['historical_reactions'];
    return NewsIntelligenceModel(
      symbol: json['symbol'] ?? 'XAUUSD',
      eventTitle: json['event_title'] ?? 'US Non-Farm Payrolls',
      scheduledAtWib: json['scheduled_at_wib'] ?? '',
      scheduledAtUtc: json['scheduled_at_utc'] ?? '',
      consensus: json['consensus'] ?? '-',
      previous: json['previous'] ?? '-',
      marketRegime: json['market_regime'] ?? 'Transisi Makro',
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
      intermarketSnapshot: rawIntermarket is Map
          ? IntermarketSnapshotModel.fromJson(Map<String, dynamic>.from(rawIntermarket))
          : null,
      eventComparisonNote: json['event_comparison_note']?.toString() ?? '',
      historicalReactions: rawHist is List
          ? rawHist
              .whereType<Map>()
              .map((e) => HistoricalReactionItem.fromJson(Map<String, dynamic>.from(e)))
              .toList()
          : const [],
      historicalSummary: json['historical_summary']?.toString() ?? '',
      avgHistoricalRangePips: (json['avg_historical_range_pips'] as num?)?.toDouble() ?? 0.0,
      disclaimer: json['disclaimer'] ?? '',
      analyzedAtWib: json['analyzed_at_wib'] ?? '',
    );
  }
}
