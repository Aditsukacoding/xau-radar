class TechnicalIndicatorsModel {
  final String symbol;
  final String timeframe;
  final double latestPrice;
  final double? rsi14;
  final String? rsiCondition;
  final double? sma20;
  final double? sma50;
  final double? sma200;
  final double? ema9;
  final double? ema21;
  final String trendDirection;
  final List<double> supportLevels;
  final List<double> resistanceLevels;
  final String summary;

  TechnicalIndicatorsModel({
    required this.symbol,
    required this.timeframe,
    required this.latestPrice,
    this.rsi14,
    this.rsiCondition,
    this.sma20,
    this.sma50,
    this.sma200,
    this.ema9,
    this.ema21,
    required this.trendDirection,
    required this.supportLevels,
    required this.resistanceLevels,
    required this.summary,
  });

  factory TechnicalIndicatorsModel.fromJson(Map<String, dynamic> json) {
    return TechnicalIndicatorsModel(
      symbol: json['symbol'] ?? 'XAUUSD',
      timeframe: json['timeframe'] ?? '1h',
      latestPrice: (json['latest_price'] as num?)?.toDouble() ?? 0.0,
      rsi14: (json['rsi_14'] as num?)?.toDouble(),
      rsiCondition: json['rsi_condition'],
      sma20: (json['sma_20'] as num?)?.toDouble(),
      sma50: (json['sma_50'] as num?)?.toDouble(),
      sma200: (json['sma_200'] as num?)?.toDouble(),
      ema9: (json['ema_9'] as num?)?.toDouble(),
      ema21: (json['ema_21'] as num?)?.toDouble(),
      trendDirection: json['trend_direction'] ?? 'NEUTRAL',
      supportLevels: (json['support_levels'] as List<dynamic>?)
              ?.map((e) => (e as num).toDouble())
              .toList() ??
          [],
      resistanceLevels: (json['resistance_levels'] as List<dynamic>?)
              ?.map((e) => (e as num).toDouble())
              .toList() ??
          [],
      summary: json['summary'] ?? '',
    );
  }
}
