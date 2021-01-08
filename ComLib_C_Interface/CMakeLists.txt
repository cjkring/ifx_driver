Add_library(ComLib_C_Interface STATIC
	src/COMPort_Unix.c
	src/COMPort_Windows.c
	src/EndpointCalibration.c
	src/EndpointRadarAdcxmc.c
	src/EndpointRadarBase.c
	src/EndpointRadarDoppler.c
	src/EndpointRadarErrorCodes.c
	src/EndpointRadarFmcw.c
	src/EndpointRadarIndustrial.c
	src/EndpointTargetDetection.c
	src/Protocol.c )

target_include_directories( ComLib_C_Interface PUBLIC include)
