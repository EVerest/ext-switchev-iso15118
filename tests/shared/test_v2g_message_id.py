# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Pionix GmbH and Contributors to EVerest
"""Pins the message id that debugV2GMessages reports, per generation."""
# Runnable on its own, because tests/conftest.py does not import at this
# revision and so pytest collects nothing here:
#   PYTHONPATH=. python3 tests/shared/test_v2g_message_id.py
from iso15118.evcc.everest import context as evcc_ctx
from iso15118.shared.comm_session import _v2g_message_id, debugV2GMessages
from iso15118.shared.messages.app_protocol import (
    AppProtocol,
    SupportedAppProtocolReq,
    SupportedAppProtocolRes,
)
from iso15118.shared.messages.enums import Namespace
from iso15118.shared.messages.iso15118_2.body import Body, PowerDeliveryReq
from iso15118.shared.messages.iso15118_2.datatypes import ChargeProgress
from iso15118.shared.messages.iso15118_2.header import MessageHeader
from iso15118.shared.messages.iso15118_2.msgdef import V2GMessage as V2GMessageV2
from iso15118.shared.messages.iso15118_20.common_types import (
    MessageHeader as MessageHeaderV20,
)
from iso15118.shared.messages.iso15118_20.dc import DCCableCheckReq

MOCK_SESSION_ID = "0102030405060708"


class EVCCCommunicationSession:
    """Stands in for the real session: only its class name is read."""


def iso2_message():
    return V2GMessageV2(
        header=MessageHeader(session_id=MOCK_SESSION_ID),
        body=Body(
            power_delivery_req=PowerDeliveryReq(
                charge_progress=ChargeProgress.START, sa_schedule_tuple_id=1
            )
        ),
    )


def iso20_message():
    return DCCableCheckReq(
        header=MessageHeaderV20(session_id=MOCK_SESSION_ID, timestamp=1)
    )


def supported_app_protocol_req():
    return SupportedAppProtocolReq(
        app_protocol=[
            AppProtocol(
                protocol_ns=Namespace.ISO_V2_MSG_DEF,
                major_version=2,
                minor_version=0,
                schema_id=1,
                priority=1,
            )
        ]
    )


def test_iso15118_2_id_is_the_body_message_name():
    assert _v2g_message_id(iso2_message()) == "PowerDeliveryReq"


def test_supported_app_protocol_id_is_the_class_name():
    req = supported_app_protocol_req()
    res = SupportedAppProtocolRes(response_code="OK_SuccessfulNegotiation", schema_id=1)
    assert _v2g_message_id(req) == "SupportedAppProtocolReq"
    assert _v2g_message_id(res) == "SupportedAppProtocolRes"
    # Their __str__ lowercases the first letter, so it is not usable as an id.
    assert str(req) == "supportedAppProtocolReq"


def test_iso15118_20_id_is_the_xsd_spelling():
    # AC/DC -20 messages override __str__ to the underscored XSD name, which is
    # not the class name. A consumer mapping ids must key off this spelling.
    assert _v2g_message_id(iso20_message()) == "DC_CableCheckReq"


def test_message_without_a_name_has_no_id():
    assert _v2g_message_id(object()) == ""


def test_evcc_publishes_the_id_and_tolerates_no_callback():
    published = []
    evcc_ctx.set_publish_callback(lambda name, value: published.append((name, value)))
    try:
        debugV2GMessages(iso2_message(), None, EVCCCommunicationSession())
        assert published == [("v2g_messages", {"id": "PowerDeliveryReq"})]

        evcc_ctx._pub_callback = None
        debugV2GMessages(iso2_message(), None, EVCCCommunicationSession())
    finally:
        evcc_ctx._pub_callback = None


if __name__ == "__main__":
    for case_name, case in sorted(globals().items()):
        if case_name.startswith("test_"):
            case()
            print(f"ok  {case_name}")
