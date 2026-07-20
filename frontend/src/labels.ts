export const eventLabel = (type: string) => ({
  intrusion: "위험구역 침입",
  ppe_missing: "보호구 미착용",
  conveyor_approach: "컨베이어 접근",
  pinch_risk: "끼임 위험",
  stop_required: "작업중지 권고",
  fall_down: "작업자 낙상",
  emergency_gesture: "비상 제스처",
}[type] || type.replaceAll("_", " "));

export const severityLabel = (severity: string) => ({ low: "낮음", medium: "중간", high: "높음", critical: "매우 높음" }[severity] || severity);
export const statusLabel = (status: string) => ({ entered: "확인 필요", staying: "위험 지속", exited: "구역 이탈", checking: "현장 확인 중", stopped: "작업중지 처리", resolved: "조치 완료", false_positive: "오탐 처리" }[status] || status);
