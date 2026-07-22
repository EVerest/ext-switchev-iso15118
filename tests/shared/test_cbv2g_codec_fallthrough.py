# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Pionix GmbH and Contributors to EVerest
"""Tests for the native cbv2g EXI codec fall-through to ExificientEXICodec."""

from pathlib import Path
from unittest.mock import patch

import pytest

from iso15118.shared.exi_codec import EXI
from iso15118.shared.exificient_exi_codec import ExificientEXICodec


@pytest.fixture(autouse=True)
def reset_exi_singleton():
    """EXI is a singleton; reset its codec between tests."""
    EXI._instance = None
    yield
    EXI._instance = None


def test_exi_falls_back_to_exificient_when_native_unavailable():
    """Native codec constructor raises -> ExificientEXICodec is used."""
    with patch(
        "iso15118.shared.exi_codec.Cbv2gEXICodec",
        side_effect=RuntimeError(
            "Could not find libcbv2g_json_wrapper.so."
        ),
    ):
        codec = EXI().get_exi_codec()

    assert isinstance(codec, ExificientEXICodec), (  # nosec B101
        "expected ExificientEXICodec fallback when native codec unavailable"
    )


def test_exi_prefers_native_when_available():
    """When Cbv2gEXICodec constructs cleanly, EXI uses it."""

    class _FakeNative:
        def encode(self, message, namespace):  # pragma: no cover - not invoked
            return b""

        def decode(self, stream, namespace):  # pragma: no cover - not invoked
            return ""

        def get_version(self):
            return "1.0.0-fake"

    with patch(
        "iso15118.shared.exi_codec.Cbv2gEXICodec",
        return_value=_FakeNative(),
    ):
        codec = EXI().get_exi_codec()

    assert isinstance(codec, _FakeNative), (  # nosec B101
        "expected the native codec to be selected when it constructs cleanly"
    )


def test_secc_main_imports_both_codecs():
    """Static source check that secc/main.py imports both codecs."""
    main_path = (
        Path(__file__).resolve().parents[2]
        / "iso15118"
        / "secc"
        / "main.py"
    )
    source = main_path.read_text()
    assert (  # nosec B101
        "from iso15118.shared.cbv2g_exi_codec import Cbv2gEXICodec" in source
    ), "secc/main.py must import Cbv2gEXICodec for the runtime fallback"
    assert (  # nosec B101
        "from iso15118.shared.exificient_exi_codec import ExificientEXICodec"
        in source
    ), "secc/main.py must keep the ExificientEXICodec import for the fallback"


def test_explicit_codec_overrides_default():
    """set_exi_codec() takes precedence over the default selection."""

    class _Sentinel:
        def encode(self, message, namespace):  # pragma: no cover
            return b""

        def decode(self, stream, namespace):  # pragma: no cover
            return ""

        def get_version(self):
            return "sentinel"

    sentinel = _Sentinel()
    exi = EXI()
    exi.set_exi_codec(sentinel)
    assert exi.get_exi_codec() is sentinel  # nosec B101
