import '../../core/utils/wib_date_time.dart';

class SignalHistoryItemModel {
  final int id;
  final String symbol;
  final String sourceType; // LIVE | AUDIT_14D
  final String action; // BUY | SELL
  final String actionLabel;
  final String executionType;
  final String entryZone;
  final double entryPrice;
  final double stopLoss;
  final double takeProfit1;
  final double takeProfit2;
  final double takeProfit3;
  final double riskPips;
  final double rewardTp1Pips;
  final double rewardTp2Pips;
  final double rewardTp3Pips;
  final int setupQualityScore;
  final String mtfAlignment;
  final String zoneProof;
  final String sessionName;
  final String outcome; // PENDING_LIMIT | ACTIVE | TP1_HIT | TP2_HIT | TP3_HIT | SL_HIT | EXPIRED
  final bool isClosed;
  final DateTime? triggeredAt;
  final DateTime? closedAt;
  final double? hitPrice;
  final double maxFavorablePips;
  final double maxAdversePips;
  final double realizedPips;
  final String outcomeNote;
  final DateTime createdAt;
  final String createdAtWib;
  final String? triggeredAtWib;
  final String? closedAtWib;

  const SignalHistoryItemModel({
    required this.id,
    required this.symbol,
    required this.sourceType,
    required this.action,
    required this.actionLabel,
    required this.executionType,
    required this.entryZone,
    required this.entryPrice,
    required this.stopLoss,
    required this.takeProfit1,
    required this.takeProfit2,
    required this.takeProfit3,
    required this.riskPips,
    required this.rewardTp1Pips,
    required this.rewardTp2Pips,
    required this.rewardTp3Pips,
    required this.setupQualityScore,
    this.mtfAlignment = '',
    this.zoneProof = '',
    this.sessionName = '',
    required this.outcome,
    required this.isClosed,
    this.triggeredAt,
    this.closedAt,
    this.hitPrice,
    this.maxFavorablePips = 0.0,
    this.maxAdversePips = 0.0,
    this.realizedPips = 0.0,
    this.outcomeNote = '',
    required this.createdAt,
    this.createdAtWib = '',
    this.triggeredAtWib,
    this.closedAtWib,
  });

  bool get isWin =>
      outcome == 'TP1_HIT' || outcome == 'TP2_HIT' || outcome == 'TP3_HIT';
  bool get isLoss => outcome == 'SL_HIT';
  bool get isOpen => outcome == 'ACTIVE' || outcome == 'PENDING_LIMIT';
  bool get isExpired => outcome == 'EXPIRED';

  factory SignalHistoryItemModel.fromJson(Map<String, dynamic> json) {
    final created = parseUtcDateTime(json['created_at']?.toString());
    return SignalHistoryItemModel(
      id: (json['id'] as num?)?.toInt() ?? 0,
      symbol: json['symbol']?.toString() ?? 'XAUUSD',
      sourceType: json['source_type']?.toString() ?? 'LIVE',
      action: json['action']?.toString().toUpperCase() ?? 'SELL',
      actionLabel: json['action_label']?.toString() ?? '',
      executionType: json['execution_type']?.toString().toUpperCase() ?? 'LIMIT',
      entryZone: json['entry_zone']?.toString() ?? '',
      entryPrice: (json['entry_price'] as num?)?.toDouble() ?? 0.0,
      stopLoss: (json['stop_loss'] as num?)?.toDouble() ?? 0.0,
      takeProfit1: (json['take_profit_1'] as num?)?.toDouble() ?? 0.0,
      takeProfit2: (json['take_profit_2'] as num?)?.toDouble() ?? 0.0,
      takeProfit3: (json['take_profit_3'] as num?)?.toDouble() ?? 0.0,
      riskPips: (json['risk_pips'] as num?)?.toDouble() ?? 0.0,
      rewardTp1Pips: (json['reward_tp1_pips'] as num?)?.toDouble() ?? 60.0,
      rewardTp2Pips: (json['reward_tp2_pips'] as num?)?.toDouble() ?? 110.0,
      rewardTp3Pips: (json['reward_tp3_pips'] as num?)?.toDouble() ?? 170.0,
      setupQualityScore: (json['setup_quality_score'] as num?)?.toInt() ?? 78,
      mtfAlignment: json['mtf_alignment']?.toString() ?? '',
      zoneProof: json['zone_proof']?.toString() ?? '',
      sessionName: json['session_name']?.toString() ?? '',
      outcome: json['outcome']?.toString().toUpperCase() ?? 'PENDING_LIMIT',
      isClosed: json['is_closed'] == true,
      triggeredAt: json['triggered_at'] != null
          ? parseUtcDateTime(json['triggered_at']?.toString())
          : null,
      closedAt: json['closed_at'] != null
          ? parseUtcDateTime(json['closed_at']?.toString())
          : null,
      hitPrice: (json['hit_price'] as num?)?.toDouble(),
      maxFavorablePips: (json['max_favorable_pips'] as num?)?.toDouble() ?? 0.0,
      maxAdversePips: (json['max_adverse_pips'] as num?)?.toDouble() ?? 0.0,
      realizedPips: (json['realized_pips'] as num?)?.toDouble() ?? 0.0,
      outcomeNote: json['outcome_note']?.toString() ?? '',
      createdAt: created,
      createdAtWib: (json['created_at_wib']?.toString().isNotEmpty == true)
          ? json['created_at_wib'].toString()
          : created.formatWibShort(),
      triggeredAtWib: json['triggered_at_wib']?.toString(),
      closedAtWib: json['closed_at_wib']?.toString(),
    );
  }
}

class SignalHistoryStatsModel {
  final int totalSignals;
  final int closedTrades;
  final int activeOrPending;
  final int wins;
  final int losses;
  final int expired;
  final int tp1Hits;
  final int tp2Hits;
  final int tp3Hits;
  final int slHits;
  final int buyCount;
  final int sellCount;
  final int buyWins;
  final int sellWins;
  final double winRatePct;
  final double netPips;
  final double avgWinPips;
  final double avgLossPips;
  final double profitFactor;

  const SignalHistoryStatsModel({
    this.totalSignals = 0,
    this.closedTrades = 0,
    this.activeOrPending = 0,
    this.wins = 0,
    this.losses = 0,
    this.expired = 0,
    this.tp1Hits = 0,
    this.tp2Hits = 0,
    this.tp3Hits = 0,
    this.slHits = 0,
    this.buyCount = 0,
    this.sellCount = 0,
    this.buyWins = 0,
    this.sellWins = 0,
    this.winRatePct = 0.0,
    this.netPips = 0.0,
    this.avgWinPips = 0.0,
    this.avgLossPips = 0.0,
    this.profitFactor = 0.0,
  });

  factory SignalHistoryStatsModel.fromJson(Map<String, dynamic> json) {
    return SignalHistoryStatsModel(
      totalSignals: (json['total_signals'] as num?)?.toInt() ?? 0,
      closedTrades: (json['closed_trades'] as num?)?.toInt() ?? 0,
      activeOrPending: (json['active_or_pending'] as num?)?.toInt() ?? 0,
      wins: (json['wins'] as num?)?.toInt() ?? 0,
      losses: (json['losses'] as num?)?.toInt() ?? 0,
      expired: (json['expired'] as num?)?.toInt() ?? 0,
      tp1Hits: (json['tp1_hits'] as num?)?.toInt() ?? 0,
      tp2Hits: (json['tp2_hits'] as num?)?.toInt() ?? 0,
      tp3Hits: (json['tp3_hits'] as num?)?.toInt() ?? 0,
      slHits: (json['sl_hits'] as num?)?.toInt() ?? 0,
      buyCount: (json['buy_count'] as num?)?.toInt() ?? 0,
      sellCount: (json['sell_count'] as num?)?.toInt() ?? 0,
      buyWins: (json['buy_wins'] as num?)?.toInt() ?? 0,
      sellWins: (json['sell_wins'] as num?)?.toInt() ?? 0,
      winRatePct: (json['win_rate_pct'] as num?)?.toDouble() ?? 0.0,
      netPips: (json['net_pips'] as num?)?.toDouble() ?? 0.0,
      avgWinPips: (json['avg_win_pips'] as num?)?.toDouble() ?? 0.0,
      avgLossPips: (json['avg_loss_pips'] as num?)?.toDouble() ?? 0.0,
      profitFactor: (json['profit_factor'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class SignalHistoryResponseModel {
  final String symbol;
  final double currentPrice;
  final String updatedAtWib;
  final SignalHistoryStatsModel stats;
  final List<SignalHistoryItemModel> items;
  final String methodologyNote;

  const SignalHistoryResponseModel({
    required this.symbol,
    required this.currentPrice,
    required this.updatedAtWib,
    required this.stats,
    required this.items,
    required this.methodologyNote,
  });

  factory SignalHistoryResponseModel.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'];
    final items = (rawItems is List)
        ? rawItems
            .whereType<Map>()
            .map((e) => SignalHistoryItemModel.fromJson(Map<String, dynamic>.from(e)))
            .toList()
        : const <SignalHistoryItemModel>[];

    return SignalHistoryResponseModel(
      symbol: json['symbol']?.toString() ?? 'XAUUSD',
      currentPrice: (json['current_price'] as num?)?.toDouble() ?? 0.0,
      updatedAtWib: json['updated_at_wib']?.toString() ?? '',
      stats: (json['stats'] is Map)
          ? SignalHistoryStatsModel.fromJson(Map<String, dynamic>.from(json['stats']))
          : const SignalHistoryStatsModel(),
      items: items,
      methodologyNote: json['methodology_note']?.toString() ?? '',
    );
  }
}
