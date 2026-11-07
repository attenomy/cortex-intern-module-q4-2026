import pytest
from modules.doc_extractor.sroie_adapter import adapt_sroie_entities


def test_adapt_sroie_complete_record():
    record = {
        "document_id": "SROIE-001",
        "entities": {
            "vendor_name": ["ABC STORE"],
            "date": ["25/12/2018"],
            "address": ["Johor Bahru"],
            "total": ["60.30"]
        }
    }
    result = adapt_sroie_entities(record)
    assert result["vendor_name"] == "ABC STORE"
    assert result["net_amount"] == 60.30
    assert result["invoice_number"] is None
    assert result["currency"] is None
    assert result["source"] == "SROIE"
def test_adapt_sroie_does_not_invent_missing_fields():
    result = adapt_sroie_entities({"entities": {"vendor_name": ["ABC"]}})
    assert result["invoice_number"] is None
    assert result["currency"] is None
    assert result["net_amount"] is None
def test_adapt_sroie_amount_with_commas():
    result = adapt_sroie_entities({
        "entities": {"total": ["1,250.75"]}
    })
    assert result["net_amount"] == 1250.75
def test_adapt_sroie_invalid_amount():
    result = adapt_sroie_entities({
        "entities": {"total": ["not-an-amount"]}
    })
    assert result["net_amount"] is None
def test_adapt_sroie_empty_entity_lists():
    result = adapt_sroie_entities({
        "entities": {
            "vendor_name": [],
            "total": []
        }
    })
    assert result["vendor_name"] is None
    assert result["net_amount"] is None
def test_adapt_sroie_rejects_invalid_record():
    with pytest.raises(TypeError):
        adapt_sroie_entities("invalid")
