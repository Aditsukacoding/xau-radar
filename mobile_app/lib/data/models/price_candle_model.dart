class PriceCandleModel {
  final int id;
  final String symbol;
  final String timeframe;
  final DateTime timestamp;
  final double open;
  final double high;
  final double low;
  final double close;
  final double volume;

  PriceCandleModel({
    required this.id,
    required this.symbol,
    required this.timeframe,
    required this.timestamp,
    required this.open,
    required this.high,
    required this.low,
    required this.close,
    required this.volume,
  });

  bool get isBullish => close >= open;

  factory PriceCandleModel.fromJson(Map<String, dynamic> json) {
    return PriceCandleModel(
      id: json['id'] ?? 0,
      symbol: json['symbol'] ?? 'XAUUSD',
      timeframe: json['timeframe'] ?? '1h',
      timestamp: DateTime.tryParse(json['timestamp'] ?? '') ?? DateTime.now(),
      open: (json['open'] as num?)?.toDouble() ?? 0.0,
      high: (json['high'] as num?)?.toDouble() ?? 0.0,
      low: (json['low'] as num?)?.toDouble() ?? 0.0,
      close: (json['close'] as num?)?.toDouble() ?? 0.0,
      volume: (json['volume'] as num?)?.toDouble() ?? 0.0,
    );
  }

  PriceCandleModel copyWith({
    int? id,
    String? symbol,
    String? timeframe,
    DateTime? timestamp,
    double? open,
    double? high,
    double? low,
    double? close,
    double? volume,
  }) {
    return PriceCandleModel(
      id: id ?? this.id,
      symbol: symbol ?? this.symbol,
      timeframe: timeframe ?? this.timeframe,
      timestamp: timestamp ?? this.timestamp,
      open: open ?? this.open,
      high: high ?? this.high,
      low: low ?? this.low,
      close: close ?? this.close,
      volume: volume ?? this.volume,
    );
  }
}
