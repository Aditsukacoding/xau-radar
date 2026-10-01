class NewsArticleModel {
  final int id;
  final String symbol;
  final String title;
  final String source;
  final String? url;
  final String? summary;
  final String sentimentLabel; // POSITIVE, NEGATIVE, NEUTRAL
  final double sentimentScore; // -1.0 to 1.0
  final DateTime publishedAt;

  NewsArticleModel({
    required this.id,
    required this.symbol,
    required this.title,
    required this.source,
    this.url,
    this.summary,
    required this.sentimentLabel,
    required this.sentimentScore,
    required this.publishedAt,
  });

  factory NewsArticleModel.fromJson(Map<String, dynamic> json) {
    return NewsArticleModel(
      id: json['id'] ?? 0,
      symbol: json['symbol'] ?? 'XAUUSD',
      title: json['title'] ?? '',
      source: json['source'] ?? 'Market News',
      url: json['url'],
      summary: json['summary'],
      sentimentLabel: json['sentiment_label'] ?? 'NEUTRAL',
      sentimentScore: (json['sentiment_score'] as num?)?.toDouble() ?? 0.0,
      publishedAt: DateTime.tryParse(json['published_at'] ?? '') ?? DateTime.now(),
    );
  }
}
