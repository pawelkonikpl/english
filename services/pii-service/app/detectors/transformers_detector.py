"""PII detector backed by a Hugging Face token-classification model.

Imports torch and transformers at module level; the detector factory imports this
module lazily, so the service runs without them when a non-ML backend is chosen.
"""

import threading
from collections.abc import Mapping

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

from app.detectors.base import PiiCategory, PiiEntity
from app.detectors.span_decoding import TokenPrediction, decode_spans, refine_spans


class TransformersPiiDetector:
    """Detects PII with a token-classification model from the Hugging Face Hub.

    Texts longer than one model window are split into overlapping windows, so no
    part of the text is skipped.
    """

    def __init__(
        self,
        model_id: str,
        label_map: Mapping[str, PiiCategory],
        *,
        revision: str | None = None,
        device: str = "cpu",
        window_tokens: int = 512,
        window_stride: int = 128,
        batch_size: int = 8,
    ) -> None:
        self._label_map = label_map
        self._device = torch.device(device)
        self._window_tokens = window_tokens
        self._window_stride = window_stride
        self._batch_size = batch_size
        # Fast tokenizers are not safe to call from several threads at once, and
        # FastAPI runs sync endpoints in a thread pool.
        self._lock = threading.Lock()

        self._tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
        # safetensors only: never unpickle downloaded weights.
        self._model = AutoModelForTokenClassification.from_pretrained(
            model_id, revision=revision, use_safetensors=True
        )
        self._model.to(self._device).eval()
        self._id_to_tag: dict[int, str] = {
            int(label_id): tag for label_id, tag in self._model.config.id2label.items()
        }

    def detect(self, text: str) -> list[PiiEntity]:
        if not text.strip():
            return []
        with self._lock:
            tokens = self._predict_tokens(text)
        spans = refine_spans(text, decode_spans(tokens))
        return [
            PiiEntity(
                category=self._label_map.get(span.label, PiiCategory.OTHER),
                source_label=span.label,
                start=span.start,
                end=span.end,
                score=span.score,
            )
            for span in spans
        ]

    def _predict_tokens(self, text: str) -> list[TokenPrediction]:
        encoding = self._tokenizer(
            text,
            truncation=True,
            max_length=self._window_tokens,
            stride=self._window_stride,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            padding=True,
            return_tensors="pt",
        )
        input_ids: torch.Tensor = encoding["input_ids"]
        attention_mask: torch.Tensor = encoding["attention_mask"]
        offsets: list[list[list[int]]] = encoding["offset_mapping"].tolist()

        # A token inside the overlap of two windows keeps the prediction from the
        # window where it has more context on both sides, i.e. lies farther from
        # the window edges.
        best_by_offsets: dict[tuple[int, int], tuple[int, TokenPrediction]] = {}
        for first in range(0, input_ids.shape[0], self._batch_size):
            window_slice = slice(first, first + self._batch_size)
            with torch.inference_mode():
                logits = self._model(
                    input_ids=input_ids[window_slice].to(self._device),
                    attention_mask=attention_mask[window_slice].to(self._device),
                ).logits
            scores, tag_ids = logits.float().softmax(dim=-1).max(dim=-1)

            for window_offsets, window_mask, window_scores, window_tag_ids in zip(
                offsets[window_slice],
                attention_mask[window_slice].tolist(),
                scores.tolist(),
                tag_ids.tolist(),
                strict=True,
            ):
                predictions = [
                    TokenPrediction(start=start, end=end, tag=self._id_to_tag[tag_id], score=score)
                    for (start, end), is_token, score, tag_id in zip(
                        window_offsets, window_mask, window_scores, window_tag_ids, strict=True
                    )
                    # Padding and special tokens have no characters behind them, and
                    # whitespace-only tokens tagged O would split a multi-word name.
                    if is_token and end > start and not text[start:end].isspace()
                ]
                last_position = len(predictions) - 1
                for position, prediction in enumerate(predictions):
                    context = min(position, last_position - position)
                    key = (prediction.start, prediction.end)
                    if key not in best_by_offsets or context > best_by_offsets[key][0]:
                        best_by_offsets[key] = (context, prediction)

        return sorted(
            (prediction for _, prediction in best_by_offsets.values()),
            key=lambda token: (token.start, token.end),
        )
