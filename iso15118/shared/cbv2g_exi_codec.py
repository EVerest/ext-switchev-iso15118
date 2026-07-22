# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Pionix GmbH and Contributors to EVerest
"""Python ctypes bindings for libcbv2g_json_wrapper."""

import ctypes
import logging
import os
from pathlib import Path
from typing import Optional

from iso15118.shared.iexi_codec import IEXICodec

logger = logging.getLogger(__name__)


class Cbv2gEXICodec(IEXICodec):
    # Native EXI codec backed by libcbv2g via ctypes.

    # Default buffer sizes
    ENCODE_BUFFER_SIZE = 65536  # 64KB for encoded EXI
    DECODE_BUFFER_SIZE = 262144  # 256KB for decoded JSON

    def __init__(self, library_path: Optional[str] = None):
        """Load libcbv2g_json_wrapper.so and bind the C entry points."""
        self._lib = None
        self._library_path = library_path or self._find_library()

        if self._library_path is None:
            raise RuntimeError(
                "Could not find libcbv2g_json_wrapper.so. "
                "Please build the library first or specify the path."
            )

        self._load_library()
        self._setup_functions()
        logger.info(f"Cbv2gEXICodec initialized with library: {self._library_path}")

    def _find_library(self) -> Optional[str]:
        """Locate libcbv2g_json_wrapper.so in standard or LD_LIBRARY_PATH locations."""
        lib_name = "libcbv2g_json_wrapper.so"

        # Possible search paths
        search_paths = [
            # Relative to this file
            Path(__file__).parent / "cbv2g_wrapper" / "build" / lib_name,
            Path(__file__).parent / "cbv2g_wrapper" / "build" / "lib" / lib_name,
            # Standard locations
            Path("/usr/local/lib") / lib_name,
            Path("/usr/lib") / lib_name,
            # Current directory
            Path.cwd() / lib_name,
            Path.cwd() / "build" / lib_name,
        ]

        # Add LD_LIBRARY_PATH directories
        ld_library_path = os.environ.get("LD_LIBRARY_PATH", "")
        for path in ld_library_path.split(":"):
            if path:
                search_paths.append(Path(path) / lib_name)

        # Search for the library
        for path in search_paths:
            if path.exists():
                return str(path)

        return None

    def _load_library(self) -> None:
        """Load the shared library via ctypes."""
        try:
            self._lib = ctypes.CDLL(self._library_path)
        except OSError as e:
            raise RuntimeError(
                f"Failed to load libcbv2g_json_wrapper.so from {self._library_path}: {e}"
            )

    def _setup_functions(self) -> None:
        """Bind argtypes and restypes for the C entry points."""
        # cbv2g_encode
        self._lib.cbv2g_encode.argtypes = [
            ctypes.c_char_p,  # json_message
            ctypes.c_char_p,  # namespace
            ctypes.POINTER(ctypes.c_uint8),  # output_buffer
            ctypes.c_size_t,  # buffer_size
            ctypes.POINTER(ctypes.c_size_t),  # output_length
        ]
        self._lib.cbv2g_encode.restype = ctypes.c_int

        # cbv2g_decode
        self._lib.cbv2g_decode.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),  # exi_data
            ctypes.c_size_t,  # exi_length
            ctypes.c_char_p,  # namespace
            ctypes.c_char_p,  # output_json
            ctypes.c_size_t,  # buffer_size
        ]
        self._lib.cbv2g_decode.restype = ctypes.c_int

        # cbv2g_get_version
        self._lib.cbv2g_get_version.argtypes = []
        self._lib.cbv2g_get_version.restype = ctypes.c_char_p

        # cbv2g_get_last_error
        self._lib.cbv2g_get_last_error.argtypes = []
        self._lib.cbv2g_get_last_error.restype = ctypes.c_char_p

        # cbv2g_clear_error
        self._lib.cbv2g_clear_error.argtypes = []
        self._lib.cbv2g_clear_error.restype = None

    def encode(self, message: str, namespace: str) -> bytes:
        """Encode a JSON message to EXI bytes for the given V2G namespace."""
        # Create output buffer
        output_buffer = (ctypes.c_uint8 * self.ENCODE_BUFFER_SIZE)()
        output_length = ctypes.c_size_t()

        # Call the C function
        result = self._lib.cbv2g_encode(
            message.encode("utf-8"),
            namespace.encode("utf-8"),
            output_buffer,
            self.ENCODE_BUFFER_SIZE,
            ctypes.byref(output_length),
        )

        if result != 0:
            error_msg = self._lib.cbv2g_get_last_error()
            error_str = error_msg.decode("utf-8") if error_msg else "Unknown error"
            raise Exception(f"EXI encoding failed (code {result}): {error_str}")

        # Return the encoded bytes
        return bytes(output_buffer[: output_length.value])

    def decode(self, stream: bytes, namespace: str) -> str:
        """Decode EXI bytes to a JSON message for the given V2G namespace."""
        # Create input buffer from stream
        exi_data = (ctypes.c_uint8 * len(stream))(*stream)

        # Create output buffer
        output_buffer = ctypes.create_string_buffer(self.DECODE_BUFFER_SIZE)

        # Call the C function
        result = self._lib.cbv2g_decode(
            exi_data,
            len(stream),
            namespace.encode("utf-8"),
            output_buffer,
            self.DECODE_BUFFER_SIZE,
        )

        if result != 0:
            error_msg = self._lib.cbv2g_get_last_error()
            error_str = error_msg.decode("utf-8") if error_msg else "Unknown error"
            raise Exception(f"EXI decoding failed (code {result}): {error_str}")

        # Return the decoded JSON string
        return output_buffer.value.decode("utf-8")

    def get_version(self) -> str:
        """Return the libcbv2g_json_wrapper version string."""
        version = self._lib.cbv2g_get_version()
        return version.decode("utf-8") if version else "unknown"

    def shutdown(self) -> None:
        """No Java gateway to tear down; the native codec has no session-end work."""
