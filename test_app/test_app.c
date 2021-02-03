#include <stdio.h>
#include <math.h>
#include <time.h>
//#include <netdb.h> /* getprotobyname */
//#include <netinet/in.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h> 
#include <stdlib.h> 
#include <string.h> 
#include <signal.h>

typedef struct reading {
    uint32_t I;
    uint32_t Q;
} reading;
#define SAMPLES_PER_PACKET  256

#define PORT 8080 
int main(int argc, char const *argv[]) 
{ 
    int server_fd, new_socket, valread; 
    struct sockaddr_in address; 
    int opt = 1; 
    int addrlen = sizeof(address);

    reading readings[SAMPLES_PER_PACKET];
  

    double scale = 2;


    if( argc > 1 ){
        scale = atof(argv[1]);
        fprintf(stderr, "scale set to %f\n", scale);
    }
        

    signal(SIGPIPE, SIG_IGN);

    // Creating socket file descriptor 
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) { 
        perror("socket failed"); 
        exit(EXIT_FAILURE); 
    } 
       
    // Forcefully attaching socket to the port 8080 
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt))) { 
        perror("setsockopt failed"); 
        exit(EXIT_FAILURE); 
    } 
    // Forcefully attaching socket to the port 8080 
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEPORT, &opt, sizeof(opt))) { 
        perror("setsockopt failed"); 
        exit(EXIT_FAILURE); 
    } 
    address.sin_family = AF_INET; 
    address.sin_addr.s_addr = INADDR_ANY; 
    address.sin_port = htons( PORT ); 
       
    // Forcefully attaching socket to the port 8080 
    if (bind(server_fd, (struct sockaddr *)&address,  sizeof(address))<0) { 
        perror("bind failed"); 
        exit(EXIT_FAILURE); 
    } 
    if (listen(server_fd, 3) < 0) { 
        perror("listen failed"); 
        exit(EXIT_FAILURE); 
    } 
    // handles only one socket at a time.  Dumps I Q to the socket
#define SECOND_NANOS 1000000000L
#define PADDING_LEN 4
    double update_period = SECOND_NANOS / scale;
    uint8_t padding[PADDING_LEN] = {0xDE,0xAD,0xBE,0xEF};
    
    uint32_t sin_count = 0;
    while( 1 ){
        if ((new_socket = accept(server_fd, (struct sockaddr *)&address,  
                                 (socklen_t*)&addrlen))<0) { 
            perror("accept failed"); 
            exit(EXIT_FAILURE); 
        } 
        uint32_t seqno = 1;
        while( 1 ){   // socket is connected

        float I, Q;

            for( int count = 0; count < SAMPLES_PER_PACKET; count++ ){
		// base rate is 512 count per sec / 6.28 count per radian = 81 Hz
		double theta = sin_count / 0.5;
                I = sin(theta); // 41 Hz
                Q = cos(2 * theta);
                fprintf(stderr,"%d,%2.2f,%2.2f\n", sin_count, I, Q );
                

                readings[count].I = htonl(I*1000 + 100000);
                readings[count].Q = htonl(Q*1000 + 100000);
                if( ++sin_count > 10000000 )sin_count = 0;
            }
        int count_hton = htonl(SAMPLES_PER_PACKET);
        int seq_hton = htonl(seqno);
        if(( write(new_socket, padding, PADDING_LEN) < 0 ) ||
           ( write(new_socket, &seq_hton, sizeof(int32_t)) < 0 ) ||
           ( write(new_socket, &count_hton, sizeof(int32_t)) < 0 ) ||
           ( write(new_socket, readings, sizeof(int32_t) * 2 * SAMPLES_PER_PACKET) < 0 )){
                perror("Socket disconnected");
                break;
            }
            seqno++;
            //nanosleep((const struct timespec[]){{0, update_period }}, NULL);
            nanosleep((const struct timespec[]){{1, 0}}, NULL);
            
        }
    }
    return 0; 
} 
