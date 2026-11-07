import torch
from modules.doc_extractor.layout_classifier import (
    DOCUMENT_CLASSES,
    build_classifier,
    predict_document,
)


def test_classifier_has_four_output_classes():
    model = build_classifier(pretrained=False)

    assert model.classifier[3].out_features == 4


def test_prediction_returns_valid_document_type():
    model = build_classifier(pretrained=False)
    image = torch.randn(1, 3, 224, 224)

    result = predict_document(model, image)

    assert result["document_type"] in DOCUMENT_CLASSES
    assert 0 <= result["confidence"] <= 1


def test_prediction_returns_confidence():
    model = build_classifier(pretrained=False)
    image = torch.randn(1, 3, 224, 224)

    result = predict_document(model, image)

    assert isinstance(result["confidence"], float)
