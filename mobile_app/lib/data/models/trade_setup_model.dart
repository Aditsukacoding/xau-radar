class MtfTimeframeItem {
  final String tf; // M1, M5, M15, M30, H1, H4, D1
  final String trend; // BULLISH, BEARISH, SIDEWAYS
  final double? rsi;
  final double atrPips;
  final double sup;
  final double res;
  final String pa;

  const MtfTimeframeItem({
    required this.tf,
    required this.trend,
    this.rsi,
    this.atrPips = 0.0,
    this.sup = 0.0,
    this.res = 0.0,
    this.pa = '',
  });

  factory MtfTimeframeItem.fromJson(Map<String, dynamic> json) {
    return MtfTimeframeItem(
      tf: json['tf']?.toString() ?? 'M15',
      trend: json['trend']?.toString().toUpperCase() ?? 'SIDEWAYS',
      rsi: (json['rsi'] as num?)?.toDouble(),
      atrPips: (json['atr_pips'] as num?)?.toDouble() ?? 0.0,
      sup: (json['sup'] as num?)?.toDouble() ?? 0.0,
      res: (json['res'] as num?)?.toDouble() ?? 0.0,
      pa: json['pa']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'tf': tf,
        'trend': trend,
        'rsi': rsi,
        'atr_pips': atrPips,
        'sup': sup,
        'res': res,
        'pa': pa,
      };
}

class EntryReasonItem {
  final String title;
  final String tag;
  final String detail;
  final String tone; // bullish, bearish, cyan, gold

  const EntryReasonItem({
    required this.title,
    this.tag = '',
    required this.detail,
    this.tone = 'gold',
  });

  factory EntryReasonItem.fromJson(Map<String, dynamic> json) {
    return EntryReasonItem(
      title: json['title']?.toString() ?? '',
      tag: json['tag']?.toString() ?? '',
      detail: json['detail']?.toString() ?? '',
      tone: json['tone']?.toString().toLowerCase() ?? 'gold',
    );
  }

  Map<String, dynamic> toJson() => {
        'title': title,
        'tag': tag,
        'detail': detail,
        'tone': tone,
      };
}

class CounterSetupModel {
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
  final String riskRewardRatio;
  final int setupQualityScore;
  final String zoneProof;
  final double zoneDistancePips;
  final String triggerCondition;

  const CounterSetupModel({
    required this.action,
    required this.actionLabel,
    this.executionType = 'LIMIT',
    required this.entryZone,
    required this.entryPrice,
    required this.stopLoss,
    required this.takeProfit1,
    required this.takeProfit2,
    required this.takeProfit3,
    required this.riskPips,
    this.rewardTp1Pips = 60.0,
    required this.rewardTp2Pips,
    required this.rewardTp3Pips,
    this.riskRewardRatio = '1 : 3.5',
    this.setupQualityScore = 76,
    this.zoneProof = '',
    this.zoneDistancePips = 0.0,
    this.triggerCondition = '',
  });

  factory CounterSetupModel.fromJson(Map<String, dynamic> json) {
    return CounterSetupModel(
      action: json['action']?.toString().toUpperCase() ?? 'BUY',
      actionLabel: json['action_label']?.toString() ?? 'BUY LIMIT (KEY DEMAND)',
      executionType: json['execution_type']?.toString().toUpperCase() ?? 'LIMIT',
      entryZone: json['entry_zone']?.toString() ?? '',
      entryPrice: (json['entry_price'] as num?)?.toDouble() ?? 0.0,
      stopLoss: (json['stop_loss'] as num?)?.toDouble() ?? 0.0,
      takeProfit1: (json['take_profit_1'] as num?)?.toDouble() ?? 0.0,
      takeProfit2: (json['take_profit_2'] as num?)?.toDouble() ?? 0.0,
      takeProfit3: (json['take_profit_3'] as num?)?.toDouble() ?? 0.0,
      riskPips: (json['risk_pips'] as num?)?.toDouble() ?? 40.0,
      rewardTp1Pips: (json['reward_tp1_pips'] as num?)?.toDouble() ?? 60.0,
      rewardTp2Pips: (json['reward_tp2_pips'] as num?)?.toDouble() ?? 110.0,
      rewardTp3Pips: (json['reward_tp3_pips'] as num?)?.toDouble() ?? 170.0,
      riskRewardRatio: json['risk_reward_ratio']?.toString() ?? '1 : 3.5',
      setupQualityScore: (json['setup_quality_score'] as num?)?.toInt() ?? 76,
      zoneProof: json['zone_proof']?.toString() ?? '',
      zoneDistancePips: (json['zone_distance_pips'] as num?)?.toDouble() ?? 0.0,
      triggerCondition: json['trigger_condition']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'action': action,
        'action_label': actionLabel,
        'execution_type': executionType,
        'entry_zone': entryZone,
        'entry_price': entryPrice,
        'stop_loss': stopLoss,
        'take_profit_1': takeProfit1,
        'take_profit_2': takeProfit2,
        'take_profit_3': takeProfit3,
        'risk_pips': riskPips,
        'reward_tp1_pips': rewardTp1Pips,
        'reward_tp2_pips': rewardTp2Pips,
        'reward_tp3_pips': rewardTp3Pips,
        'risk_reward_ratio': riskRewardRatio,
        'setup_quality_score': setupQualityScore,
        'zone_proof': zoneProof,
        'zone_distance_pips': zoneDistancePips,
        'trigger_condition': triggerCondition,
      };
}

class TradeSetupModel {
  final String action; // BUY, SELL, WAIT
  final String actionLabel; // BUY NOW (SCALP), SELL LIMIT (CONFLUENCE), etc.
  final String executionType; // INSTANT, LIMIT, WAIT
  final String scalpTimeframe; // M1–D1 MTF
  final String sessionName;
  final double atrPips;
  final String mtfAlignment;
  final List<MtfTimeframeItem> mtfOverview;
  final String confluenceNote;
  final int setupQualityScore;
  final String zoneProof;
  final double zoneDistancePips;
  final String entryZone;
  final double entryPrice;
  final double stopLoss;
  final double takeProfit1;
  final double takeProfit2;
  final double takeProfit3;
  final String riskRewardRatio;
  final double riskPips;
  final double rewardTp1Pips;
  final double rewardTp2Pips;
  final double rewardTp3Pips;
  final String lotManagement;
  final List<EntryReasonItem> entryReasons;
  final String technicalRationale;
  final String invalidationLevel;
  final String? status;
  final String? statusMessage;
  final CounterSetupModel? counterSetup;

  String get safeStatus => status ?? 'ACTIVE';
  String get safeStatusMessage => (statusMessage != null && statusMessage!.isNotEmpty)
      ? statusMessage!
      : 'Setup Scalping Aktif';

  TradeSetupModel({
    required this.action,
    required this.actionLabel,
    this.executionType = 'INSTANT',
    this.scalpTimeframe = 'M1–D1 MTF',
    this.sessionName = '',
    this.atrPips = 0.0,
    this.mtfAlignment = '',
    this.mtfOverview = const [],
    this.confluenceNote = '',
    this.setupQualityScore = 78,
    this.zoneProof = '',
    this.zoneDistancePips = 0.0,
    required this.entryZone,
    required this.entryPrice,
    required this.stopLoss,
    required this.takeProfit1,
    required this.takeProfit2,
    this.takeProfit3 = 0.0,
    required this.riskRewardRatio,
    required this.riskPips,
    required this.rewardTp1Pips,
    required this.rewardTp2Pips,
    this.rewardTp3Pips = 0.0,
    this.lotManagement = '40% TP1 +60p (SL→BEP) • 40% TP2 (SL→TP1) • 20% Runner TP3',
    this.entryReasons = const [],
    required this.technicalRationale,
    required this.invalidationLevel,
    this.status = 'ACTIVE',
    this.statusMessage = 'Setup Scalping Aktif',
    this.counterSetup,
  });

  factory TradeSetupModel.fromJson(Map<String, dynamic> json) {
    final entry = (json['entry_price'] as num?)?.toDouble() ?? 0.0;
    final tp1 = (json['take_profit_1'] as num?)?.toDouble() ?? 0.0;
    final tp2 = (json['take_profit_2'] as num?)?.toDouble() ?? 0.0;
    double tp3 = (json['take_profit_3'] as num?)?.toDouble() ?? 0.0;
    double r3Pips = (json['reward_tp3_pips'] as num?)?.toDouble() ?? 0.0;

    if (tp3 <= 0 && tp2 > 0 && entry > 0) {
      final step = (tp2 - tp1).abs();
      final delta = step > 0.5 ? step * 1.2 : 4.5;
      tp3 = (tp2 >= entry)
          ? double.parse((tp2 + delta).toStringAsFixed(2))
          : double.parse((tp2 - delta).toStringAsFixed(2));
      r3Pips = double.parse(((tp3 - entry).abs() * 10.0).toStringAsFixed(1));
    }

    final rawOverview = json['mtf_overview'];
    final List<MtfTimeframeItem> overview = (rawOverview is List)
        ? rawOverview
            .whereType<Map>()
            .map((e) => MtfTimeframeItem.fromJson(Map<String, dynamic>.from(e)))
            .toList()
        : const [];

    final rawReasons = json['entry_reasons'];
    final List<EntryReasonItem> reasons = (rawReasons is List)
        ? rawReasons
            .whereType<Map>()
            .map((e) => EntryReasonItem.fromJson(Map<String, dynamic>.from(e)))
            .where((item) => item.title.isNotEmpty && item.detail.isNotEmpty)
            .toList()
        : const [];

    return TradeSetupModel(
      action: json['action'] ?? 'WAIT',
      actionLabel: json['action_label'] ?? 'WAIT / STANDBY',
      executionType: json['execution_type'] ?? 'INSTANT',
      scalpTimeframe: json['scalp_timeframe'] ?? 'M1–D1 MTF',
      sessionName: json['session_name'] ?? '',
      atrPips: (json['atr_pips'] as num?)?.toDouble() ?? 0.0,
      mtfAlignment: json['mtf_alignment']?.toString() ?? '',
      mtfOverview: overview,
      confluenceNote: json['confluence_note']?.toString() ?? '',
      setupQualityScore: (json['setup_quality_score'] as num?)?.toInt() ?? 78,
      zoneProof: json['zone_proof']?.toString() ?? '',
      zoneDistancePips: (json['zone_distance_pips'] as num?)?.toDouble() ?? 0.0,
      entryZone: json['entry_zone'] ?? '',
      entryPrice: entry,
      stopLoss: (json['stop_loss'] as num?)?.toDouble() ?? 0.0,
      takeProfit1: tp1,
      takeProfit2: tp2,
      takeProfit3: tp3,
      riskRewardRatio: json['risk_reward_ratio'] ?? '1 : 3.0',
      riskPips: (json['risk_pips'] as num?)?.toDouble() ?? 0.0,
      rewardTp1Pips: (json['reward_tp1_pips'] as num?)?.toDouble() ?? 0.0,
      rewardTp2Pips: (json['reward_tp2_pips'] as num?)?.toDouble() ?? 0.0,
      rewardTp3Pips: r3Pips,
      lotManagement: json['lot_management'] ?? '40% TP1 +60p (SL→BEP) • 40% TP2 (SL→TP1) • 20% Runner TP3',
      entryReasons: reasons,
      technicalRationale: json['technical_rationale'] ?? '',
      invalidationLevel: json['invalidation_level'] ?? '',
      status: json['status']?.toString() ?? 'ACTIVE',
      statusMessage: json['status_message']?.toString() ?? 'Setup Scalping Aktif',
      counterSetup: (json['counter_setup'] is Map)
          ? CounterSetupModel.fromJson(Map<String, dynamic>.from(json['counter_setup']))
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'action': action,
      'action_label': actionLabel,
      'execution_type': executionType,
      'scalp_timeframe': scalpTimeframe,
      'session_name': sessionName,
      'atr_pips': atrPips,
      'mtf_alignment': mtfAlignment,
      'mtf_overview': mtfOverview.map((e) => e.toJson()).toList(),
      'confluence_note': confluenceNote,
      'setup_quality_score': setupQualityScore,
      'zone_proof': zoneProof,
      'zone_distance_pips': zoneDistancePips,
      'entry_zone': entryZone,
      'entry_price': entryPrice,
      'stop_loss': stopLoss,
      'take_profit_1': takeProfit1,
      'take_profit_2': takeProfit2,
      'take_profit_3': takeProfit3,
      'risk_reward_ratio': riskRewardRatio,
      'risk_pips': riskPips,
      'reward_tp1_pips': rewardTp1Pips,
      'reward_tp2_pips': rewardTp2Pips,
      'reward_tp3_pips': rewardTp3Pips,
      'lot_management': lotManagement,
      'entry_reasons': entryReasons.map((e) => e.toJson()).toList(),
      'technical_rationale': technicalRationale,
      'invalidation_level': invalidationLevel,
      'status': status,
      'status_message': statusMessage,
      'counter_setup': counterSetup?.toJson(),
    };
  }
}
