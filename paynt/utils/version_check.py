import payntbind.info
import stormpy.info

import logging
logger = logging.getLogger(__name__)

# Checks whether stormpy and payntbind use the same Storm as backend
# Note that even if all these checks pass there is still a chance that the version of Storm used are incompatible but this should be rare
def check_stormpy_compatibility():

    incompatibility_found = False

    if payntbind.info.storm_version() != stormpy.info.storm_version():
        logger.warning(f"Storm used by payntbind ({payntbind.info.storm_version()}) and stormpy ({stormpy.info.storm_version()}) are not the same!")
        incompatibility_found = True
    if payntbind.info.storm_from_system() != stormpy.info.storm_from_system():
        logger.warning(f"Storm used by payntbind ({'system' if payntbind.info.storm_from_system() else 'fetched'}) and stormpy ({'system' if stormpy.info.storm_from_system() else 'fetched'}) have different origins!")
        incompatibility_found = True
    if payntbind.info.storm_development_version() != stormpy.info.storm_development_version():
        logger.warning(f"Storm used by payntbind ({'development' if payntbind.info.storm_development_version() else 'stable'}) and stormpy ({'development' if stormpy.info.storm_development_version() else 'stable'}) have different development versions!")
        incompatibility_found = True
    if payntbind.info.storm_origin_info() != stormpy.info.storm_origin_info():
        logger.warning(f"Storm used by payntbind ({payntbind.info.storm_origin_info()}) and stormpy ({stormpy.info.storm_origin_info()}) have different origin information!")
        incompatibility_found = True
    if payntbind.info.storm_directory() != stormpy.info.storm_directory():
        logger.warning(f"Storm used by payntbind is located at {payntbind.info.storm_directory()} while Storm used by stormpy is located at {stormpy.info.storm_directory()}.")
        incompatibility_found = True

    if not incompatibility_found:
        logger.info(f"Storm used by payntbind and stormpy seem to be the same.")
