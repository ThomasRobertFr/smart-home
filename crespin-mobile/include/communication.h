#ifndef __COMMUNICATION__
#define __COMMUNICATION__

void send_data(int sockfd, char data[]);
int read_data(int sockfd, char data[], int datasize);
int start_server();
int wait_for_client(int sockfd);

#endif
