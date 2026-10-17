#pragma once
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <unistd.h>
#if defined(__APPLE__) && !defined(TCP_KEEPIDLE)
#define TCP_KEEPIDLE TCP_KEEPALIVE
#endif
// All traffic uses real loopback sockets. Wrappers constrain I/O sizes and
// inject EAGAIN deterministically; select also permits a clean test shutdown.
int zigbee_test_bind(int, const struct sockaddr *, socklen_t);
int zigbee_test_select(int, fd_set *, fd_set *, fd_set *, struct timeval *);
ssize_t zigbee_test_send(int, const void *, size_t, int);
ssize_t zigbee_test_recv(int, void *, size_t, int);
#define bind zigbee_test_bind
#define select zigbee_test_select
#define send zigbee_test_send
#define recv zigbee_test_recv
