import 'trade_setup_model.dart';

class DashboardSummaryModel {
  final String symbol;
  final String instrumentName;
  final double currentPrice;
  final double priceChange24h;
  final double priceChangePct24h;
  final double high24h;
  final double low24h;
  final String bias;
  final int confidenceScore;
  final String biasSummary;
  final TradeSetupModel? tradeSetup;
  final Map<String, dynamic>? upcomingHighImpactEvent;
  final Map<String, dynamic>? latestGeopoliticalHeadline;
  final Map<String, dynamic> technicalSnapshot;
  final String disclaimer;
  final DateTime lastUpdated;

  DashboardSummaryModel({
    required this.symbol,
    required this.instrumentName,
    required this.currentPrice,
    required this.priceChange24h,
    required this.priceChangePct24h,
    required this.high24h,
    required this.low24h,
    required this.bias,
    required this.confidenceScore,
    required this.biasSummary,
    this.tradeSetup,
    this.upcomingHighImpactEvent,
    this.latestGeopoliticalHeadline,
    required this.technicalSnapshot,
    required this.disclaimer,
    required this.lastUpdated,
  });

  factory DashboardSummaryModel.fromJson(Map<String, dynamic> json) {
    return DashboardSummaryModel(
      symbol: json['symbol'] ?? 'XAUUSD',
      instrumentName: json['instrument_name'] ?? 'Gold vs US Dollar',
      currentPrice: (json['current_price'] as num?)?.toDouble() ?? 0.0,
      priceChange24h: (json['price_change_24h'] as num?)?.toDouble() ?? 0.0,
      priceChangePct24h: (json['price_change_pct_24h'] as num?)?.toDouble() ?? 0.0,
      high24h: (json['high_24h'] as num?)?.toDouble() ?? 0.0,
      low24h: (json['low_24h'] as num?)?.toDouble() ?? 0.0,
      bias: json['bias'] ?? 'NEUTRAL',
      confidenceScore: (json['confidence_score'] as num?)?.toInt() ?? 50,
      biasSummary: json['bias_summary'] ?? '',
      tradeSetup: json['trade_setup'] != null ? TradeSetupModel.fromJson(json['trade_setup']) : null,
      upcomingHighImpactEvent: json['upcoming_high_impact_event'],
      latestGeopoliticalHeadline: json['latest_geopolitical_headline'],
      technicalSnapshot: json['technical_snapshot'] ?? {},
      disclaimer: json['disclaimer'] ?? '',
      lastUpdated: DateTime.tryParse(json['last_updated'] ?? '') ?? DateTime.now(),
    );
  }

  DashboardSummaryModel copyWith({
    String? symbol,
    String? instrumentName,
    double? currentPrice,
    double? priceChange24h,
    double? priceChangePct24h,
    double? high24h,
    double? low24h,
    String? bias,
    int? confidenceScore,
    String? biasSummary,
    TradeSetupModel? tradeSetup,
    Map<String, dynamic>? upcomingHighImpactEvent,
    Map<String, dynamic>? latestGeopoliticalHeadline,
    Map<String, dynamic>? technicalSnapshot,
    String? disclaimer,
    DateTime? lastUpdated,
  }) {
    return DashboardSummaryModel(
      symbol: symbol ?? this.symbol,
      instrumentName: instrumentName ?? this.instrumentName,
      currentPrice: currentPrice ?? this.currentPrice,
      priceChange24h: priceChange24h ?? this.priceChange24h,
      priceChangePct24h: priceChangePct24h ?? this.priceChangePct24h,
      high24h: high24h ?? this.high24h,
      low24h: low24h ?? this.low24h,
      bias: bias ?? this.bias,
      confidenceScore: confidenceScore ?? this.confidenceScore,
      biasSummary: biasSummary ?? this.biasSummary,
      tradeSetup: tradeSetup ?? this.tradeSetup,
      upcomingHighImpactEvent: upcomingHighImpactEvent ?? this.upcomingHighImpactEvent,
      latestGeopoliticalHeadline: latestGeopoliticalHeadline ?? this.latestGeopoliticalHeadline,
      technicalSnapshot: technicalSnapshot ?? this.technicalSnapshot,
      disclaimer: disclaimer ?? this.disclaimer,
      lastUpdated: lastUpdated ?? this.lastUpdated,
    );
  }
}
