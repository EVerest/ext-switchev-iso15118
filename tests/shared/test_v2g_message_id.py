# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Pionix GmbH and Contributors to EVerest
"""Pins the message id that debugV2GMessages reports, per generation.

Two different strings are pinned here, and confusing them aborts the consumer:

* ``_v2g_message_id`` returns the id the PROTOCOL uses. For ISO 15118-20 that
  is the underscored XSD spelling (``DC_CableCheckReq``).
* ``debugV2GMessages`` publishes the id EVEREST accepts. Its ``V2gMessageId``
  is a closed enum, so a string outside it makes the consumer's generated
  deserializer raise ``std::out_of_range`` and abort the module.
"""
# Runnable on its own, because tests/conftest.py does not import at this
# revision and so pytest collects nothing here:
#   PYTHONPATH=. python3 tests/shared/test_v2g_message_id.py
import importlib
import inspect
import pkgutil

from iso15118.evcc.everest import context as evcc_ctx
from iso15118.shared import comm_session as comm_session_mod
from iso15118.shared.comm_session import (
    _EVEREST_KNOWN_IDS,
    _EVEREST_UNKNOWN_ID,
    _everest_v2g_message_id,
    _v2g_message_id,
    debugV2GMessages,
)
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
from iso15118.shared.messages.iso15118_20.common_types import (
    V2GMessage as V2GMessageV20,
)
from iso15118.shared.messages.iso15118_20.dc import (
    DCCableCheckReq,
    DCChargeParameterDiscoveryReq,
)

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


class UnknownToEverestReq(DCCableCheckReq):
    """A -20 message everest's V2gMessageId does not contain.

    Stands in for any message a future Josev gains before everest's enum
    catches up. Its id must never reach the consumer as itself.
    """

    def __str__(self):
        return "DC_MessageFromTheFutureReq"


def iso20_charge_parameter_discovery_req():
    # construct() rather than __init__: the message requires one of its
    # energy-transfer-mode fields, and none of them affect the id.
    return DCChargeParameterDiscoveryReq.construct(
        header=MessageHeaderV20(session_id=MOCK_SESSION_ID, timestamp=1)
    )


def unknown_to_everest_message():
    return UnknownToEverestReq(
        header=MessageHeaderV20(session_id=MOCK_SESSION_ID, timestamp=1)
    )


def publish_via_evcc(message):
    """Return the id debugV2GMessages actually publishes for `message`."""
    published = []
    comm_session_mod._warn_unmapped_id.cache_clear()
    evcc_ctx.set_publish_callback(lambda name, value: published.append((name, value)))
    try:
        debugV2GMessages(message, None, EVCCCommunicationSession())
    finally:
        evcc_ctx._pub_callback = None
    if not published:
        return None
    assert len(published) == 1, published
    name, value = published[0]
    assert name == "v2g_messages", name
    return value["id"]


def concrete_v2g20_message_classes():
    """Every concrete ISO 15118-20 message class Josev defines."""
    package = importlib.import_module("iso15118.shared.messages.iso15118_20")
    for module in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"iso15118.shared.messages.iso15118_20.{module.name}")

    seen = set()

    def walk(cls):
        for sub in cls.__subclasses__():
            if sub not in seen:
                seen.add(sub)
                walk(sub)

    walk(V2GMessageV20)
    return [cls for cls in seen if not inspect.isabstract(cls)]


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


def test_iso15118_20_publishes_the_everest_spelling():
    # The exact message that aborted ev_manager with "Provided string
    # DC_ChargeParameterDiscoveryReq could not be converted to enum of type
    # V2gMessageId". The protocol id is right; everest spells it differently.
    message = iso20_charge_parameter_discovery_req()
    assert _v2g_message_id(message) == "DC_ChargeParameterDiscoveryReq"
    assert publish_via_evcc(message) == "DcChargeParameterDiscoveryReq"


def test_unmapped_id_is_never_published_verbatim():
    """The regression guard: an id everest does not know must degrade.

    Publishing the raw name is what aborts the consumer, so this asserts on
    the published value rather than on any log line.
    """
    message = unknown_to_everest_message()
    raw = _v2g_message_id(message)
    assert raw == "DC_MessageFromTheFutureReq"
    assert raw not in _EVEREST_KNOWN_IDS

    published_id = publish_via_evcc(message)
    assert published_id == _EVEREST_UNKNOWN_ID
    assert published_id != raw
    assert published_id in _EVEREST_KNOWN_IDS


def test_every_message_josev_can_send_is_accepted_by_everest():
    """Enumerates the domain instead of sampling it.

    Sampling on SessionStopReq, whose class name and XSD name coincide, is
    what let the -20 spelling difference through in the first place.
    """
    offenders = []
    for cls in concrete_v2g20_message_classes():
        instance = cls.__new__(cls)
        mapped = _everest_v2g_message_id(instance)
        if mapped not in _EVEREST_KNOWN_IDS:
            offenders.append((cls.__name__, cls.__str__(instance), mapped))
    assert not offenders, (
        "these messages would be published as an id everest's V2gMessageId "
        f"enum rejects, aborting the consumer: {offenders}"
    )


if __name__ == "__main__":
    for case_name, case in sorted(globals().items()):
        if case_name.startswith("test_"):
            case()
            print(f"ok  {case_name}")
