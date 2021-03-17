#include <stdio.h>
#include <math.h>
#include <time.h>

#ifdef WIN32
#include <winsock2.h>
#include <stdint.h>
#include <ws2tcpip.h>
static char *port = "8080";

typedef int socklen_t;
#else // Linux
#define closesocket close
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h> 
#endif
#include <stdlib.h> 
#include <string.h> 
#include <signal.h>

static int port = 8080;
static int server_fd = -1;
static struct sockaddr_in address; 

int setupServerSocket()
{
    int opt = 0; 

#ifdef WIN32

    WSADATA wsaData;
    if( WSAStartup(MAKEWORD(2,2), &wsaData) < 0 ){
        fprintf(stderr, "Error: WSAstartup failed\n");
        return -1;
    }

    struct addrinfo hints = {0};
    struct addrinfo *res = NULL;
    
    hints.ai_flags = AI_PASSIVE;
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_protocol = IPPROTO_TCP;

    if( getaddrinfo(NULL, "8080", &hints, &res ) < 0  ){
        fprintf(stderr, "getaddrinfo failed\n");
        return -1;
    }

    // Creating socket file descriptor 
    if ((server_fd = socket(res->ai_family, res->ai_socktype, res->ai_protocol)) < 0 ) { 
        fprintf(stderr, "socket failed: %d\n", WSAGetLastError()); 
        return -1;
    } 
       
    // Forcefully attaching socket to the port 8080 
    if (bind(server_fd, res->ai_addr,  res->ai_addrlen) < 0) { 
        fprintf(stderr, "bind failed: %d\n", WSAGetLastError()); 
        return -1;
    } 
    if (listen(server_fd, 3) < 0) { 
        fprintf(stderr, "listen failed %d\n", WSAGetLastError()); 
        return -1;
    } 
    return server_fd;
       
#else 
    signal(SIGPIPE, SIG_IGN);

    // Creating socket file descriptor 
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) { 
        perror("socket failed"); 
        exit(EXIT_FAILURE); 
    } 
    // Forcefully attaching socket to the port 8080 
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEPORT, &opt, sizeof(opt))) { 
        perror("setsockopt failed"); 
        exit(EXIT_FAILURE); 
    } 
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt))) { 
        perror("setsockopt failed"); 
        exit(EXIT_FAILURE); 
    } 
    address.sin_family = AF_INET; 
    address.sin_addr.s_addr = INADDR_ANY; 
    address.sin_port = htons( 8080 ); 

    // Forcefully attaching socket to the port 8080 
    if (bind(server_fd, (struct sockaddr *)&address,  sizeof(address))<0) { 
        perror("bind failed"); 
        exit(EXIT_FAILURE); 
    } 
    if (listen(server_fd, 3) < 0) { 
        perror("listen failed"); 
        exit(EXIT_FAILURE); 
    } 
    return server_fd;
#endif
}
int acceptSocket()
{
#ifdef WIN32
    socklen_t addrlen = sizeof(address);
    int sock;
    if ((sock = accept(server_fd, (struct sockaddr *)&address,  &addrlen)) < 0) { 
        fprintf(stderr, "accept failed %d\n", WSAGetLastError()); 
        return -1;
    } 
    return sock;
#else 
    int sock; 
    struct sockaddr_in address;
    int addrlen = sizeof(address);
    if ((sock = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen))<0) { 
        perror("accept failed"); 
	exit(EXIT_FAILURE); 
    } 
    return sock;
#endif

}
typedef struct reading {
    uint32_t I;
    uint32_t Q;
} reading;

#define SAMPLES_PER_PACKET  256

int notmain(int argc, char const *argv[]) 
{ 
    int server_fd, new_socket, valread; 

    reading readings[SAMPLES_PER_PACKET];
  

    double scale = 2;

    if( argc > 1 ){
        scale = atof(argv[1]);
        fprintf(stderr, "scale set to %f\n", scale);
    }
    server_fd = setupServerSocket();
    // handles only one socket at a time.  Dumps I Q to the socket
#define SECOND_NANOS 1000000000L
#define PADDING_LEN 4
    double update_period = SECOND_NANOS / scale;
    uint8_t padding[PADDING_LEN] = {0xDE,0xAD,0xBE,0xEF};
    
    uint32_t sin_count = 0;
    while( 1 ){
        new_socket = acceptSocket();
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
        if(( send(new_socket, padding, PADDING_LEN, 0) < 0 ) ||
           ( send(new_socket, (char *)&seq_hton, sizeof(int32_t), 0) < 0 ) ||
           ( send(new_socket, (char *)&count_hton, sizeof(int32_t), 0) < 0 ) ||
           ( send(new_socket, (char *)readings, sizeof(int32_t) * 2 * SAMPLES_PER_PACKET, 0) < 0 )){
                fprintf(stderr, "Socket disconnected");
                break;
            }
            seqno++;
            //nanosleep((const struct timespec[]){{0, update_period }}, NULL);
            nanosleep((const struct timespec[]){{1, 0}}, NULL);
        }
    }
    return 0; 
} 
