class TradeSetupModel {
  final String action; // BUY, SELL, WAIT
  final String actionLabel; // BUY (LONG) ON PULLBACK, etc.
  final String entryZone;
  final double entryPrice;
  final double stopLoss;
  final double takeProfit1;
  final double takeProfit2;
  final String riskRewardRatio;
  final double riskPips;
  final double rewardTp1Pips;
  final double rewardTp2Pips;
  final String technicalRationale;
  final String invalidationLevel;
  final String? status;
  final String? statusMessage;

  String get safeStatus => status ?? 'ACTIVE';
  String get safeStatusMessage => (statusMessage != null && statusMessage!.isNotEmpty)
      ? statusMessage!
      : 'Setup Konsisten Terkunci';

  TradeSetupModel({
    required this.action,
    required this.actionLabel,
    required this.entryZone,
    required this.entryPrice,
    required this.stopLoss,
    required this.takeProfit1,
    required this.takeProfit2,
    required this.riskRewardRatio,
    required this.riskPips,
    required this.rewardTp1Pips,
    required this.rewardTp2Pips,
    required this.technicalRationale,
    required this.invalidationLevel,
    this.status = 'ACTIVE',
    this.statusMessage = 'Setup Konsisten Terkunci',
  });

  factory TradeSetupModel.fromJson(Map<String, dynamic> json) {
    return TradeSetupModel(
      action: json['action'] ?? 'WAIT',
      actionLabel: json['action_label'] ?? 'WAIT / STANDBY',
      entryZone: json['entry_zone'] ?? '',
      entryPrice: (json['entry_price'] as num?)?.toDouble() ?? 0.0,
      stopLoss: (json['stop_loss'] as num?)?.toDouble() ?? 0.0,
      takeProfit1: (json['take_profit_1'] as num?)?.toDouble() ?? 0.0,
      takeProfit2: (json['take_profit_2'] as num?)?.toDouble() ?? 0.0,
      riskRewardRatio: json['risk_reward_ratio'] ?? '1 : 2.0',
      riskPips: (json['risk_pips'] as num?)?.toDouble() ?? 0.0,
      rewardTp1Pips: (json['reward_tp1_pips'] as num?)?.toDouble() ?? 0.0,
      rewardTp2Pips: (json['reward_tp2_pips'] as num?)?.toDouble() ?? 0.0,
      technicalRationale: json['technical_rationale'] ?? '',
      invalidationLevel: json['invalidation_level'] ?? '',
      status: json['status']?.toString() ?? 'ACTIVE',
      statusMessage: json['status_message']?.toString() ?? 'Setup Konsisten Terkunci',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'action': action,
      'action_label': actionLabel,
      'entry_zone': entryZone,
      'entry_price': entryPrice,
      'stop_loss': stopLoss,
      'take_profit_1': takeProfit1,
      'take_profit_2': takeProfit2,
      'risk_reward_ratio': riskRewardRatio,
      'risk_pips': riskPips,
      'reward_tp1_pips': rewardTp1Pips,
      'reward_tp2_pips': rewardTp2Pips,
      'technical_rationale': technicalRationale,
      'invalidation_level': invalidationLevel,
      'status': status,
      'status_message': statusMessage,
    };
  }
}
