#
# FindCub
#
# This module finds the Cub header files and extracts their version.  It
# sets the following variables.
#
# CUB_INCLUDE_DIR -  Include directory for cub header files.  (All header
#                       files will actually be in the cub subdirectory.)
# CUB_VERSION -      Version of cub in the form "major.minor.patch".
#
# Cub_FOUND - Indicates whether cub has been found
#

find_path(CUB_INCLUDE_DIR
	HINTS
		/usr/include/cuda
		/usr/local/include
		/usr/local/cuda/include
		${CUDA_INCLUDE_DIRS}
	NAMES cub/version.cuh
	DOC "Cub headers"
)
if(CUB_INCLUDE_DIR)
	list(REMOVE_DUPLICATES CUB_INCLUDE_DIR)
endif(CUB_INCLUDE_DIR)

# Find cub version
file(STRINGS ${CUB_INCLUDE_DIR}/cub/version.cuh
	version
	REGEX "#define CUB_VERSION[ \t]+([0-9x]+)"
)
string(REGEX REPLACE
	"#define CUB_VERSION[ \t]+"
	""
	version
	"${version}"
)

string(REGEX MATCH "^[0-9]" major ${version})
string(REGEX REPLACE "^${major}00" "" version "${version}")
string(REGEX MATCH "^[0-9]" minor ${version})
string(REGEX REPLACE "^${minor}0" "" version "${version}")
set(CUB_VERSION "${major}.${minor}.${version}")
set(CUB_MAJOR_VERSION "${major}")
set(CUB_MINOR_VERSION "${minor}")

# Check for required components
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Cub REQUIRED_VARS CUB_INCLUDE_DIR VERSION_VAR CUB_VERSION)

set(CUB_INCLUDE_DIRS ${CUB_INCLUDE_DIR})
mark_as_advanced(CUB_INCLUDE_DIR)