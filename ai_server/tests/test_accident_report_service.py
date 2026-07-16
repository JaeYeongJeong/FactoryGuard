from types import SimpleNamespace

from app.services.vision_llm import accident_report_service


class FakeRagEngine:
    def build_report_basis(self, **_kwargs):
        basis = SimpleNamespace(
            model_dump=lambda: {
                "title": "산업안전보건 기준",
                "source": "safety.pdf",
                "pages": 3,
                "reason": "검색된 근거",
                "corpus": "safety_authority",
                "chunk_id": "chunk-1",
                "parent_id": "parent-1",
            }
        )
        return SimpleNamespace(
            legal_basis=[basis],
            recommended_action=["설비를 정지한다."],
            markdown="# 사고 근거 보고서",
        )


class FailingRagEngine:
    def build_report_basis(self, **_kwargs):
        raise RuntimeError("RAG unavailable")


def test_vision_report_is_combined_with_rag_basis(monkeypatch) -> None:
    monkeypatch.setattr(
        accident_report_service,
        "analyze_accident",
        lambda *_args: "작업자 끼임 위험이 관찰되었습니다.",
    )
    monkeypatch.setattr(
        accident_report_service,
        "get_engine",
        lambda: FakeRagEngine(),
    )

    result = accident_report_service.generate_report_with_legal_basis(
        "unused.jpg",
        event_id="event-001",
    )

    assert result["event_id"] == "event-001"
    assert result["rag_available"] is True
    assert result["legal_basis"][0]["corpus"] == "safety_authority"
    assert result["recommended_action"] == ["설비를 정지한다."]


def test_vision_report_survives_rag_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        accident_report_service,
        "analyze_accident",
        lambda *_args: "Vision 분석 결과",
    )
    monkeypatch.setattr(
        accident_report_service,
        "get_engine",
        lambda: FailingRagEngine(),
    )

    result = accident_report_service.generate_report_with_legal_basis("unused.jpg")

    assert result["report"] == "Vision 분석 결과"
    assert result["rag_available"] is False
    assert result["legal_basis"] == []
