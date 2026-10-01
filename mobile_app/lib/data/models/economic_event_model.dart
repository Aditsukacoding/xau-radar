class EconomicEventModel {
  final int id;
  final String? externalId;
  final String currency;
  final String eventTitle;
  final String impactLevel;
  final DateTime scheduledAt;
  final String? actualValue;
  final String? forecastValue;
  final String? previousValue;
  final String? unit;
  final String? sentimentImpact;

  EconomicEventModel({
    required this.id,
    this.externalId,
    required this.currency,
    required this.eventTitle,
    required this.impactLevel,
    required this.scheduledAt,
    this.actualValue,
    this.forecastValue,
    this.previousValue,
    this.unit,
    this.sentimentImpact,
  });

  factory EconomicEventModel.fromJson(Map<String, dynamic> json) {
    // Parse scheduled_at — always treat as UTC so WIB conversion is accurate.
    // Backend now emits ISO-8601 with +00:00 suffix; legacy naive strings are
    // also treated as UTC (they were stored as UTC in SQLite).
    DateTime parseUtc(String? raw) {
      if (raw == null || raw.isEmpty) return DateTime.now().toUtc();
      final dt = DateTime.tryParse(raw);
      if (dt == null) return DateTime.now().toUtc();
      // If already has timezone info, convert to UTC
      if (dt.isUtc) return dt;
      // Naive datetime: treat as UTC explicitly
      return DateTime.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.millisecond);
    }

    return EconomicEventModel(
      id: json['id'] ?? 0,
      externalId: json['external_id'],
      currency: json['currency'] ?? 'USD',
      eventTitle: json['event_title'] ?? '',
      impactLevel: json['impact_level'] ?? 'HIGH',
      scheduledAt: parseUtc(json['scheduled_at']),
      actualValue: json['actual_value'],
      forecastValue: json['forecast_value'],
      previousValue: json['previous_value'],
      unit: json['unit'],
      sentimentImpact: json['sentiment_impact'],
    );
  }
}

