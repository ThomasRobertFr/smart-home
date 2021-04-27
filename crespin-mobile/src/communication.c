#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <arpa/inet.h>

void error(char *msg) {
  perror(msg);
  exit(1);
}

void send_data(int sockfd, char data[]) {
    if (write(sockfd, data, strlen(data)) < 0)
        error(("ERROR writing to socket"));
}

int read_data(int sockfd, char data[], int datasize) {
    int n;
    if ((n = read(sockfd, data, datasize - 1)) < 0)
        error(("ERROR reading from socket"));
    data[n] = '\0';
    return n;
}

int start_server(int portno) {
    int sockfd;
    struct sockaddr_in serv_addr;

    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0)
        error(("ERROR opening socket"));
    if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &(int){ 1 }, sizeof(int)) < 0)
        error("setsockopt(SO_REUSEADDR) failed");

    bzero((char *) &serv_addr, sizeof(serv_addr));

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons(portno);
    if (bind(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0)
       error(("ERROR on binding"));
    listen(sockfd,5);

    return sockfd;
}

int wait_for_client(int sockfd) {
    int newsockfd, clilen;
    struct sockaddr_in cli_addr;

    clilen = sizeof(cli_addr);

    if ((newsockfd = accept(sockfd, (struct sockaddr *) &cli_addr, (socklen_t*) &clilen)) < 0)
        error(("ERROR on accept"));

    return newsockfd;
}

/*
int main(int argc, char *argv[])
{
    int sockfd, newsockfd;

    char data [512];

    sockfd = start_server();

    while (1) {
        printf("waiting for new client...\n");

        newsockfd = wait_for_client(sockfd);
        read_data(newsockfd, data, 512);
        printf("got %s\n", data);

        // sendData(newsockfd, data * 2);
        close(newsockfd);
    }
}
*/

/* A simple client program to interact with the myServer.c program on the Raspberry.
myClient.c
D. Thiebaut
Adapted from http://www.cs.rpi.edu/~moorthy/Courses/os98/Pgms/socket.html
The port number used in 51717.
This code is compiled and run on the Macbook laptop as follows:

    g++ -o myClient myClient.c
    ./myClient


*/

/*


int main(int argc, char *argv[])
{
    int sockfd, portno = 51717, n;
    char serverIp[] = "127.0.0.1";
    struct sockaddr_in serv_addr;
    struct hostent *server;
    char buffer[256];
    int data;

    if (argc < 3) {
      // error(("usage myClient2 hostname port\n"));
      printf("contacting %s on port %d\n", serverIp, portno);
      // exit(0);
    }
    if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
        error(("ERROR opening socket"));

    if ((server = gethostbyname(serverIp)) == NULL)
        error(("ERROR, no such host\n"));

    bzero((char *) &serv_addr, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    bcopy((char *)server->h_addr, (char *)&serv_addr.sin_addr.s_addr, server->h_length);
    serv_addr.sin_port = htons(portno);
    if (connect(sockfd,(struct sockaddr *)&serv_addr,sizeof(serv_addr)) < 0)
        error(("ERROR connecting"));

    for (n = 0; n < 10; n++) {
      sendData(sockfd, n);
      data = getData(sockfd);
      printf("%d ->  %d\n",n, data);
    }
    sendData(sockfd, -2);

    close(sockfd);
    return 0;
}
*/
