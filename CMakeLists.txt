cmake_minimum_required( VERSION 3.10 )

#set project name
project(ifx_driver VERSION 0.1.0 LANGUAGES C )

#only set things if this is called from the top level, no included through a subdirectory

if(CMAKE_PROJECT_NAME STREQUAL ixf_driver) 

	#set(CMAKE_CXX_EXTENSIONS OFF )

	#support folders in IDES
	set_property( GLOBAL PROPERTY USE_FOLDERS_ON) 

	# Testing only available if this is the main app
	# Note this needs to be done in the main CMakeLists
	# since it calls enable_testing, which must be in the
	# main CMakeLists.
	include(CTest)

	# Docs only available if this is the main app
	find_package(Doxygen)
	if(Doxygen_FOUND)
		add_subdirectory(docs)
	else()
		message(STATUS "Doxygen not found, not building docs")
	endif()
endif()

message( STATUS "CMAKE_PROJECT_NAME is " ${CMAKE_PROJECT_NAME} )


#executables
#add_subdirectory(driver_app)
add_subdirectory(test_app)

#ifx Comm Library
add_subdirectory(ComLib_C_Interface)

# Testing only available if this is the main app
# Emergency override MODERN_CMAKE_BUILD_TESTING provided as well
if((CMAKE_PROJECT_NAME STREQUAL ifx_driver OR MODERN_CMAKE_BUILD_TESTING) AND BUILD_TESTING)
     add_subdirectory(tests)
endif()

