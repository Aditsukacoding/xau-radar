import '../../core/utils/wib_date_time.dart';

class TradePostMortemModel {
  final String causeCode;
  final String causeLabel;
  final String severity; // POSITIVE | WARNING | NEUTRAL
  final String diagnosis;
  final String lesson;

  const TradePostMortemModel({
    required this.causeCode,
    required this.causeLabel,
    this.severity = 'NEUTRAL',
    required this.diagnosis,
    required this.lesson,
  });

  factory TradePostMortemModel.fromJson(Map<String, dynamic> json) {
    return TradePostMortemModel(
      causeCode: json['cause_code']?.toString() ?? '',
      causeLabel: json['cause_label']?.toString() ?? '',
      severity: json['severity']?.toString().toUpperCase() ?? 'NEUTRAL',
      diagnosis: json['diagnosis']?.toString() ?? '',
      lesson: json['lesson']?.toString() ?? '',
    );
  }
}

class SelfEvaluationModel {
  final int analyzedTrades;
  final int consecutiveSl;
  final bool inPostSlCooldown;
  final int cooldownRemainingMin;
  final double slBufferMult;
  final bool blockMixedChop;
  final bool useOuterEdgeEntry;
  final List<String> activeAdjustments;
  final List<String> recentLessons;
  final String summary;

  const SelfEvaluationModel({
    this.analyzedTrades = 0,
    this.consecutiveSl = 0,
    this.inPostSlCooldown = false,
    this.cooldownRemainingMin = 0,
    this.slBufferMult = 1.0,
    this.blockMixedChop = false,
    this.useOuterEdgeEntry = false,
    this.activeAdjustments = const [],
    this.recentLessons = const [],
    this.summary = '',
  });

  factory SelfEvaluationModel.fromJson(Map<String, dynamic> json) {
    return SelfEvaluationModel(
      analyzedTrades: (json['analyzed_trades'] as num?)?.toInt() ?? 0,
      consecutiveSl: (json['consecutive_sl'] as num?)?.toInt() ?? 0,
      inPostSlCooldown: json['in_post_sl_cooldown'] == true,
      cooldownRemainingMin: (json['cooldown_remaining_min'] as num?)?.toInt() ?? 0,
      slBufferMult: (json['sl_buffer_mult'] as num?)?.toDouble() ?? 1.0,
      blockMixedChop: json['block_mixed_chop'] == true,
      useOuterEdgeEntry: json['use_outer_edge_entry'] == true,
      activeAdjustments: (json['active_adjustments'] is List)
          ? (json['active_adjustments'] as List).map((e) => e.toString()).toList()
          : const [],
      recentLessons: (json['recent_lessons'] is List)
          ? (json['recent_lessons'] as List).map((e) => e.toString()).toList()
          : const [],
      summary: json['summary']?.toString() ?? '',
    );
  }
}

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
  final TradePostMortemModel? postMortem;
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
    this.postMortem,
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
      postMortem: (json['post_mortem'] is Map)
          ? TradePostMortemModel.fromJson(Map<String, dynamic>.from(json['post_mortem']))
          : null,
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
  final SelfEvaluationModel? selfEvaluation;
  final List<SignalHistoryItemModel> items;
  final String methodologyNote;

  const SignalHistoryResponseModel({
    required this.symbol,
    required this.currentPrice,
    required this.updatedAtWib,
    required this.stats,
    this.selfEvaluation,
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
      selfEvaluation: (json['self_evaluation'] is Map)
          ? SelfEvaluationModel.fromJson(Map<String, dynamic>.from(json['self_evaluation']))
          : null,
      items: items,
      methodologyNote: json['methodology_note']?.toString() ?? '',
    );
  }
}
