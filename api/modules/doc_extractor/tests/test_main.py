from unittest.mock import patch

import pytest
import torch
from fastapi.testclient import TestClient
from main import app
from modules.doc_extractor.layout_classifier import predict_document


def test_model_loads_during_startup():
    with TestClient(app):
        assert app.state.document_classifier is not None
        assert isinstance(app.state.document_classifier, torch.nn.Module)
def test_loaded_model_performs_inference():
    with TestClient(app):
        model = app.state.document_classifier
        result = predict_document(model, torch.randn(1, 3, 224, 224))
        assert result["document_type"] in {
            "invoice", "receipt", "contract", "purchase_order"
        }
        assert 0 <= result["confidence"] <= 1
def test_startup_fails_when_model_is_missing():
    with patch("main.load_document_model", side_effect=FileNotFoundError("Model missing")):
        with pytest.raises(FileNotFoundError):
            with TestClient(app):
                pass
