import pytest
import torch
from modules.doc_extractor.layout_classifier import build_classifier
from modules.doc_extractor.model_loader import load_document_model


def test_missing_model_weights_fail_fast(tmp_path):
    missing_path = tmp_path / "missing.pth"

    with pytest.raises(FileNotFoundError):
        load_document_model(missing_path)


def test_corrupt_model_weights_fail_fast(tmp_path):
    corrupt_path = tmp_path / "corrupt.pth"
    corrupt_path.write_text("invalid model weights")

    with pytest.raises(RuntimeError):
        load_document_model(corrupt_path)


def test_valid_model_weights_load_successfully(tmp_path):
    model_path = tmp_path / "valid.pth"

    model = build_classifier(pretrained=False)
    torch.save(model.state_dict(), model_path)

    loaded_model = load_document_model(model_path)

    assert loaded_model.classifier[3].out_features == 4
    assert not loaded_model.training
