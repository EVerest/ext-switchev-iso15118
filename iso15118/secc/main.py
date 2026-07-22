import asyncio
import logging

from iso15118.secc import SECCHandler
from iso15118.secc.controller.interface import ServiceStatus
from iso15118.secc.controller.simulator import SimEVSEController
from iso15118.secc.secc_settings import Config
from iso15118.shared.cbv2g_exi_codec import Cbv2gEXICodec
from iso15118.shared.exificient_exi_codec import ExificientEXICodec

logger = logging.getLogger(__name__)


async def main():
    """
    Entrypoint function that starts the ISO 15118 code running on
    the SECC (Supply Equipment Communication Controller)
    """
    config = Config()
    config.load_envs()
    config.print_settings()

    # Prefer the native cbv2g codec (no Java required); fall back to the
    # Java-based ExificientEXICodec if the native shared library is missing.
    try:
        exi_codec = Cbv2gEXICodec()
    except Exception as native_err:
        logger.warning("Native Cbv2gEXICodec unavailable (%s); using ExificientEXICodec",
                       native_err)
        exi_codec = ExificientEXICodec()

    sim_evse_controller = SimEVSEController()
    await sim_evse_controller.set_status(ServiceStatus.STARTING)
    await SECCHandler(
        exi_codec=exi_codec,
        evse_controller=sim_evse_controller,
        config=config,
    ).start(config.iface)


def run():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.debug("SECC program terminated manually")


if __name__ == "__main__":
    run()
