
#include <stdio.h>
#include <string.h>
#include "Protocol.h"
#include "COMPort.h"
#include "EndpointRadarBase.h"
#include "EndpointRadarDoppler.h"
#include "EndpointRadarAdcxmc.h"
#include "EndpointRadarIndustrial.h"

#ifdef WIN32
#include <winsock.h>
#else
#include <sys/socket.h>
#include <sys/time.h>
#endif
extern int setupServerSocket();
extern int acceptSocket();

#define AUTOMATIC_DATA_TRIGER_TIME_US (300000)	// set to 0 to disable automatic trigger mode, defines when the next data is available
/*
 * Doppler Config Callback
 */
void doppler_config_callback(void *context, int32_t protocol_handle, uint8_t endpoint, const Doppler_Configuration_t* doppler_config)
{
	static int config_tried = 0;
	if( config_tried == 0 ){
		config_tried = 1;
		Doppler_Configuration_t config = *doppler_config;
		config.tx_power = 7;
		int32_t res = ep_radar_doppler_set_doppler_configuration( protocol_handle, endpoint, &config);
	    fprintf(stderr,"set doppler config: %s\n", protocol_get_status_code_description(protocol_handle, res ));
	} else {
		fprintf(stderr, "\tfrequency_kHz: %d\n", doppler_config->frequency_kHz );
		fprintf(stderr, "\ttx_power: %d\n", doppler_config->tx_power );
	}
}

/*
 * Device Info Callback
 */
void device_info_callback(void *context, int32_t protocol_handle, uint8_t endpoint, const Device_Info_t* device_info)
{
	if( device_info->data_format == EP_RADAR_BASE_RX_DATA_COMPLEX ){
	      fprintf(stderr, "\tdata_format: DATA_COMPLEX\n");   // I and Q in separate data blocks
	} else if ( device_info->data_format == EP_RADAR_BASE_RX_DATA_COMPLEX_INTERLEAVED ){
	      fprintf(stderr, "\tdata_format: DATA_COMPLEX_INTERLEAVED\n"); // I and Q interleaved
	} else {
	      fprintf(stderr, "\tdata_format: DATA_REAL\n");  // Only I or Q  -- this is an error condition
	} 
	fprintf(stderr, "\tmax_tx_power: %d\n", device_info->max_tx_power );
  
}

/*
 * Frame Format Callback
 */

void frame_format_callback(void *context, int32_t protocol_handle, uint8_t endpoint, const Frame_Format_t* frame_format)
 {
	 if( frame_format->eSignalPart != EP_RADAR_BASE_SIGNAL_I_AND_Q ){
		fprintf(stderr, "Error: radar does not support I and Q\n");
	 }
	fprintf(stderr, "\tnum_samples_per_chirp: %d\n", frame_format->num_samples_per_chirp );
	fprintf(stderr, "\tnum_chirps_per_frame: %d\n", frame_format->num_chirps_per_frame );
 }

/*
 * ADC Configuration Callback
 */

#define ADC_SAMPLE_RATE 1024
#define ADC_RESOLUTION 12

void adc_config_callback( void* context, int32_t protocol_handle, uint8_t endpoint, 
                          const Adc_Xmc_Configuration_t* adc_configuration)
{
	static int config_tried = 0;
	if( config_tried == 0 ){
	    config_tried = 1;
	    Adc_Xmc_Configuration_t config = *adc_configuration;
	    config.samplerate_Hz = ADC_SAMPLE_RATE;
	    config.resolution = ADC_RESOLUTION;
	    int32_t res = ep_radar_adcxmc_set_adc_configuration( protocol_handle, endpoint, &config);
	    fprintf(stderr,"set ADC config: %s\n", protocol_get_status_code_description(protocol_handle, res ));

	} else {
		fprintf(stderr, "\tADC samplerate_Hz: %d\n", adc_configuration->samplerate_Hz );
		fprintf(stderr, "\tADC resolution: %d\n", adc_configuration->resolution );
		fprintf(stderr, "\tADC use_post_calibration: %d\n", adc_configuration->use_post_calibration );
	}
}

/*
 * Chirp Duration Callback
 */

void chirp_duration_callback(void* context, int32_t protocol_handle, uint8_t endpoint, uint32_t chirp_duration_ns)
{
    fprintf(stderr, "\tchirp_duration_ns: %d\n",chirp_duration_ns );
}

/*
 * LNA status
 */

void lna_status_callback(void* context, int32_t protocol_handle, uint8_t endpoint, uint8_t is_enabled)
{
    fprintf(stderr, "\tlna_enabled: %d\n", is_enabled );
}

int radar_auto_connect(void)
{
	int radar_handle = 0;
	int num_of_ports = 0;
	char comp_port_list[256];
	char* comport;
	const char *delim = ";";

	//----------------------------------------------------------------------------

	num_of_ports = com_get_port_list(comp_port_list, (size_t)256);

	if (num_of_ports == 0)
	{
		return -1;
	}
	else
	{
		comport = strtok(comp_port_list, delim);

		while (num_of_ports > 0)
		{
			num_of_ports--;

			// open COM port
			radar_handle = protocol_connect(comport);

			if (radar_handle >= 0)
			{
				break;
			}

			comport = strtok(NULL, delim);
		}

		return radar_handle;
	}

}

#define PADDING_LEN 4
uint8_t padding[PADDING_LEN] = {0xDE,0xAD,0xBE,0xEF};
int sock = -1;
int seqno = 1;

int first = 1;
struct timeval start_time, end_time;
int getElapsedTime()
{
    if( first ){
		first = 0;
		gettimeofday(&start_time, NULL);
		return 0;
	}
	gettimeofday(&end_time, NULL);
	int32_t seconds = end_time.tv_sec - start_time.tv_sec; //seconds
    int32_t useconds = end_time.tv_usec - start_time.tv_usec; //milliseconds
    int32_t milli_time = ((seconds) * 1000 + useconds/1000.0);
	start_time = end_time;
	return milli_time;
}

// called every time ep_radar_base_get_frame_data method is called to return measured time domain signals
void received_frame_data(void* context,
						int32_t protocol_handle,
		                uint8_t endpoint,
						const Frame_Info_t* frame_info)
{
	int count = frame_info->num_samples_per_chirp;
	int count_hton = htonl(count);
	int seq_hton = htonl(seqno);

	if(( send(sock, padding, PADDING_LEN, 0) < 0 ) ||
	   ( send(sock, (char *)&seq_hton, sizeof(int32_t), 0) < 0 ) ||
       ( send(sock, (char *)&count_hton, sizeof(int32_t), 0) < 0 )){

		   fprintf(stderr, "Socket disconnected\n");
		   sock = -1;
		   return;
	}

	// Print the sampled data which can be found in frame_info->sample_data
	const float *I_data = frame_info->sample_data;
	const float *Q_data = &frame_info->sample_data[count];
	for (uint32_t i = 0; i < count; i++)
	{
		uint32_t I_hton = htonl(I_data[i]*1000 + 100000 );
		uint32_t Q_hton = htonl(Q_data[i]*1000 + 100000 );
       if (( send(sock, (char *)&I_hton, sizeof(int32_t), 0) < 0 ) ||
	       ( send(sock, (char *)&Q_hton, sizeof(int32_t), 0) < 0 )){
			fprintf(stderr, "Socket disconnected\n");
			sock = -1;
			return;
		}
	}
	int elapsed = getElapsedTime();
    fprintf(stderr, "sent %d(%d), %d [%f,%f] ... [%f,%f]\n",seqno++, elapsed, count, I_data[0], Q_data[0], I_data[count-1],Q_data[count-1]);
}

int main(int argc, char const *argv[]) 
{
	int res = -1;
	int protocolHandle = -1;
	int endpointRadarBase = -1;
	int endpointRadarDoppler = -1;
	int endpointRadarADC = -1;
	int endpointRadarIndustrial = -1;

	

	// open COM port
	protocolHandle = radar_auto_connect();
	fprintf(stderr, "protocol handle: %d\n", protocolHandle);


	// get endpoint ids
	if (protocolHandle >= 0)
	{
		Endpoint_Info_t info;
		for (int i = 1; i <= protocol_get_num_endpoints(protocolHandle); ++i) {
			if( protocol_get_endpoint_info(protocolHandle, i, &info ) < 0 ){
				fprintf(stderr, "protocol %d: no info\n", i );
			} else {
				fprintf(stderr, "protocol %d: %s\n", i, info.description );
			}
		    if (ep_radar_base_is_compatible_endpoint(protocolHandle, i) == 0) {
				endpointRadarBase = i;
			}
			if (ep_radar_doppler_is_compatible_endpoint(protocolHandle, i) == 0) {
				endpointRadarDoppler = i;
			}
			if (ep_radar_adcxmc_is_compatible_endpoint(protocolHandle, i) == 0) {
				endpointRadarADC = i;
			}
			if (ep_radar_industrial_is_compatible_endpoint(protocolHandle, i) == 0) {
				endpointRadarIndustrial = i;
			}
		}
	}
	fprintf(stderr, "endpoint radar base: %d, ADC base: %d, doppler base %d\n", endpointRadarBase, endpointRadarADC, endpointRadarDoppler);
	if (endpointRadarBase < 0 || endpointRadarADC < 0 || endpointRadarDoppler < 0) {
		fprintf(stderr, "Aborting: missing an endpoint\n");
		 return -1;
	}

	// disable automatic trigger for configuration 
	res = ep_radar_base_set_automatic_frame_trigger(protocolHandle, endpointRadarBase, 0 );
	fprintf(stderr,"disable automatic trigger: %s\n", protocol_get_status_code_description(protocolHandle, res ));

    ep_radar_doppler_set_callback_doppler_configuration( doppler_config_callback, NULL);
	res = ep_radar_doppler_get_doppler_configuration(protocolHandle, endpointRadarDoppler);
	fprintf(stderr,"get doppler config: %s\n", protocol_get_status_code_description(protocolHandle, res ));

    ep_radar_base_set_callback_device_info( device_info_callback, NULL);
	res = ep_radar_base_get_device_info(protocolHandle, endpointRadarBase); 
	fprintf(stderr,"get device info: %s\n", protocol_get_status_code_description(protocolHandle, res ));

    ep_radar_base_set_callback_frame_format( frame_format_callback, NULL);
	res = ep_radar_base_get_frame_format(protocolHandle, endpointRadarBase); 
	fprintf(stderr,"get frame format: %s\n", protocol_get_status_code_description(protocolHandle, res ));
     
    ep_radar_base_set_callback_chirp_duration( chirp_duration_callback, NULL);
	res = ep_radar_base_get_chirp_duration(protocolHandle, endpointRadarBase); 
	fprintf(stderr,"get chirp duration: %s\n", protocol_get_status_code_description(protocolHandle, res ));

    ep_radar_adcxmc_set_callback_adc_configuration(adc_config_callback, NULL);
	res = ep_radar_adcxmc_get_adc_configuration(protocolHandle, endpointRadarADC); 
	fprintf(stderr,"get ADC: %s\n", protocol_get_status_code_description(protocolHandle, res ));

    ep_radar_adcxmc_set_callback_adc_configuration(adc_config_callback, NULL);
	res = ep_radar_adcxmc_get_adc_configuration(protocolHandle, endpointRadarADC); 
	fprintf(stderr,"get ADC: %s\n", protocol_get_status_code_description(protocolHandle, res ));

    ep_radar_industrial_set_callback_bgt_lna_status(lna_status_callback, NULL);
    res = ep_radar_industrial_bgt_lna_is_enable( protocolHandle, endpointRadarIndustrial);
	fprintf(stderr,"get LNA: %s\n", protocol_get_status_code_description(protocolHandle, res ));

	// set automatic trigger
	res = ep_radar_base_set_automatic_frame_trigger(protocolHandle,
													endpointRadarBase,
													AUTOMATIC_DATA_TRIGER_TIME_US);
	fprintf(stderr,"set automatic trigger: %s\n", protocol_get_status_code_description(protocolHandle, res ));

	ep_radar_base_set_callback_data_frame(received_frame_data, NULL);

	setupServerSocket();

    while(1){
	    sock = acceptSocket();
		// register call back functions for adc data
		while (sock > 0) {
			// causes the adc data callback to be iteratively called
			res = ep_radar_base_get_frame_data(protocolHandle, endpointRadarBase, 1);
		}
	}
	return 0;
}
