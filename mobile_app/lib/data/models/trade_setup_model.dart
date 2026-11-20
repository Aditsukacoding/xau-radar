class TradeSetupModel {
  final String action; // BUY, SELL, WAIT
  final String actionLabel; // BUY NOW (SCALP), SELL LIMIT (RALLY), etc.
  final String executionType; // INSTANT, LIMIT, WAIT
  final String scalpTimeframe; // M5 / M15
  final String sessionName;
  final double atrPips;
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
  final String technicalRationale;
  final String invalidationLevel;
  final String? status;
  final String? statusMessage;

  String get safeStatus => status ?? 'ACTIVE';
  String get safeStatusMessage => (statusMessage != null && statusMessage!.isNotEmpty)
      ? statusMessage!
      : 'Setup Scalping Aktif';

  TradeSetupModel({
    required this.action,
    required this.actionLabel,
    this.executionType = 'INSTANT',
    this.scalpTimeframe = 'M5 / M15',
    this.sessionName = '',
    this.atrPips = 0.0,
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
    this.lotManagement = '40% TP1 (SL→BEP) • 40% TP2 (SL→TP1) • 20% Runner TP3',
    required this.technicalRationale,
    required this.invalidationLevel,
    this.status = 'ACTIVE',
    this.statusMessage = 'Setup Scalping Aktif',
  });

  factory TradeSetupModel.fromJson(Map<String, dynamic> json) {
    final entry = (json['entry_price'] as num?)?.toDouble() ?? 0.0;
    final tp1 = (json['take_profit_1'] as num?)?.toDouble() ?? 0.0;
    final tp2 = (json['take_profit_2'] as num?)?.toDouble() ?? 0.0;
    double tp3 = (json['take_profit_3'] as num?)?.toDouble() ?? 0.0;
    double r3Pips = (json['reward_tp3_pips'] as num?)?.toDouble() ?? 0.0;

    // Graceful fallback if reading an older cached payload without TP3
    if (tp3 <= 0 && tp2 > 0 && entry > 0) {
      final step = (tp2 - tp1).abs();
      final delta = step > 0.5 ? step * 1.2 : 4.5;
      tp3 = (tp2 >= entry) ? double.parse((tp2 + delta).toStringAsFixed(2)) : double.parse((tp2 - delta).toStringAsFixed(2));
      r3Pips = double.parse(((tp3 - entry).abs() * 10.0).toStringAsFixed(1));
    }

    return TradeSetupModel(
      action: json['action'] ?? 'WAIT',
      actionLabel: json['action_label'] ?? 'WAIT / STANDBY',
      executionType: json['execution_type'] ?? 'INSTANT',
      scalpTimeframe: json['scalp_timeframe'] ?? 'M5 / M15',
      sessionName: json['session_name'] ?? '',
      atrPips: (json['atr_pips'] as num?)?.toDouble() ?? 0.0,
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
      lotManagement: json['lot_management'] ?? '40% TP1 (SL→BEP) • 40% TP2 (SL→TP1) • 20% Runner TP3',
      technicalRationale: json['technical_rationale'] ?? '',
      invalidationLevel: json['invalidation_level'] ?? '',
      status: json['status']?.toString() ?? 'ACTIVE',
      statusMessage: json['status_message']?.toString() ?? 'Setup Scalping Aktif',
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
      'technical_rationale': technicalRationale,
      'invalidation_level': invalidationLevel,
      'status': status,
      'status_message': statusMessage,
    };
  }
}
