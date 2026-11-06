from pathlib import Path

import torch
from modules.doc_extractor.layout_classifier import build_classifier

MODEL_PATH = Path(__file__).parent / "models" / "document_classifier.pth"


def load_document_model(model_path: Path = MODEL_PATH):
    """
    Load trained MobileNetV3-Small weights.
    Fail immediately if weights are missing or invalid.
    """

    if not model_path.is_file():
        raise FileNotFoundError(
            f"Document classifier weights not found: {model_path}"
        )

    model = build_classifier(pretrained=False)

    try:
        state_dict = torch.load(
            model_path,
            map_location="cpu",
            weights_only=True,
        )

        model.load_state_dict(state_dict, strict=True)

    except Exception as exc:
        raise RuntimeError(
            f"Unable to load document classifier weights: {exc}"
        ) from exc

    model.eval()
    return model
