import torch
import torch.nn as nn
from torchvision import models


DOCUMENT_CLASSES = [
    "invoice",
    "receipt",
    "contract",
    "purchase_order",
]


def build_classifier(pretrained: bool = True):
    """
    Build a MobileNetV3-Small classifier
    with four document categories.
    """

    weights = (
        models.MobileNet_V3_Small_Weights.DEFAULT
        if pretrained
        else None
    )

    model = models.mobilenet_v3_small(weights=weights)

    input_features = model.classifier[3].in_features

    model.classifier[3] = nn.Linear(
        input_features,
        len(DOCUMENT_CLASSES)
    )

    return model


def predict_document(model, image_tensor):
    """
    Predict document class and confidence.
    """

    model.eval()

    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)

        confidence, predicted = torch.max(
            probabilities,
            dim=1
        )

    return {
        "document_type": DOCUMENT_CLASSES[predicted.item()],
        "confidence": round(confidence.item(), 4),
    }