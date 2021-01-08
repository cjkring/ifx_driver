Add_executable(ifx_driver ifx_driver.c)

target_link_libraries( ifx_driver ComLib_C_Interface)

target_include_directories( ifx_driver PUBLIC ${PROJECT_SOURCE_DIR}/ComLib_C_Interface/include)

message( STATUS "PROJECT_SOURCE_DIRC is " ${PROJECT_SOURCE_DIR} )
