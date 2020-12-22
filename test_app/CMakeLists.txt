Add_executable(test_app test_app.c)

target_link_libraries( test_app ComLib_C_Interface m)

target_include_directories( test_app PUBLIC ${PROJECT_SOURCE_DIR}/ComLib_C_Interface/include)

