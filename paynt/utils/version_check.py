from __future__ import annotations

import payntbind.info
import stormpy.info

import logging

logger = logging.getLogger(__name__)


# Checks whether stormpy and payntbind use the same Storm as backend
# Note that even if all these checks pass there is still a chance that the version of Storm used are incompatible but this should be rare
def check_stormpy_compatibility() -> None:

    incompatibility_found = False

    if payntbind.info.storm_version() != stormpy.info.storm_version():
        logger.warning(f"Storm used by payntbind ({payntbind.info.storm_version()}) and stormpy ({stormpy.info.storm_version()}) are not the same!")
        incompatibility_found = True
    if payntbind.info.storm_from_system() != stormpy.info.storm_from_system():
        payntbind_origin = "system" if payntbind.info.storm_from_system() else "fetched"
        stormpy_origin = "system" if stormpy.info.storm_from_system() else "fetched"
        logger.warning(f"Storm used by payntbind ({payntbind_origin}) and stormpy ({stormpy_origin}) have different origins!")
        incompatibility_found = True
    if payntbind.info.storm_development_version() != stormpy.info.storm_development_version():
        payntbind_dev = "development" if payntbind.info.storm_development_version() else "stable"
        stormpy_dev = "development" if stormpy.info.storm_development_version() else "stable"
        logger.warning(f"Storm used by payntbind ({payntbind_dev}) and stormpy ({stormpy_dev}) have different development versions!")
        incompatibility_found = True
    stormpy_storm_repo, _, stormpy_storm_hash = stormpy.info.storm_origin_info()
    if not payntbind.info.storm_from_system() and (payntbind.info.storm_origin_info() != (stormpy_storm_repo, stormpy_storm_hash)):
        logger.warning(
            f"Storm used by payntbind ({payntbind.info.storm_origin_info()}) and stormpy "
            f"({(stormpy_storm_repo, stormpy_storm_hash)}) have different origin information!"
        )
        incompatibility_found = True
    if payntbind.info.storm_from_system() and (payntbind.info.storm_directory() != stormpy.info.storm_directory()):
        logger.warning(
            f"Storm used by payntbind is located at {payntbind.info.storm_directory()} "
            f"while Storm used by stormpy is located at {stormpy.info.storm_directory()}."
        )
        incompatibility_found = True

    if not incompatibility_found:
        logger.info("Storm used by payntbind and stormpy seem to be the same.")
