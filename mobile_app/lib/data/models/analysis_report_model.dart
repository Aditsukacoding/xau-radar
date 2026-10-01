import 'trade_setup_model.dart';

class KeyLevelsModel {
  final List<double> support;
  final List<double> resistance;

  KeyLevelsModel({
    required this.support,
    required this.resistance,
  });

  factory KeyLevelsModel.fromJson(Map<String, dynamic>? json) {
    if (json == null) return KeyLevelsModel(support: [], resistance: []);
    return KeyLevelsModel(
      support: (json['support'] as List<dynamic>?)
              ?.map((e) => (e as num).toDouble())
              .toList() ??
          [],
      resistance: (json['resistance'] as List<dynamic>?)
              ?.map((e) => (e as num).toDouble())
              .toList() ??
          [],
    );
  }
}

class AnalysisReportModel {
  final int id;
  final String symbol;
  final String timeframe;
  final String bias; // BULLISH, BEARISH, NEUTRAL
  final int confidenceScore;
  final String summary;
  final String? fundamentalNotes;
  final String? geopoliticalNotes;
  final String? technicalNotes;
  final KeyLevelsModel keyLevels;
  final TradeSetupModel? tradeSetup;
  final List<String> riskFactors;
  final List<String> sources;
  final String disclaimer;
  final DateTime createdAt;

  AnalysisReportModel({
    required this.id,
    required this.symbol,
    required this.timeframe,
    required this.bias,
    required this.confidenceScore,
    required this.summary,
    this.fundamentalNotes,
    this.geopoliticalNotes,
    this.technicalNotes,
    required this.keyLevels,
    this.tradeSetup,
    required this.riskFactors,
    required this.sources,
    required this.disclaimer,
    required this.createdAt,
  });

  factory AnalysisReportModel.fromJson(Map<String, dynamic> json) {
    return AnalysisReportModel(
      id: json['id'] ?? 0,
      symbol: json['symbol'] ?? 'XAUUSD',
      timeframe: json['timeframe'] ?? '1h',
      bias: json['bias'] ?? 'NEUTRAL',
      confidenceScore: (json['confidence_score'] as num?)?.toInt() ?? 50,
      summary: json['summary'] ?? '',
      fundamentalNotes: json['fundamental_notes'],
      geopoliticalNotes: json['geopolitical_notes'],
      technicalNotes: json['technical_notes'],
      keyLevels: KeyLevelsModel.fromJson(json['key_levels']),
      tradeSetup: json['trade_setup'] != null ? TradeSetupModel.fromJson(json['trade_setup']) : null,
      riskFactors: (json['risk_factors'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      sources: (json['sources'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      disclaimer: json['disclaimer'] ?? '',
      createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
    );
  }
}
