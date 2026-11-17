#include <pthread.h>
#include <stdlib.h>

/* The Gluon shared-library target leaves these libjava/libzip imports open.
 * iOS paths already use the native Unix representation. */
char *JVM_NativePath(char *path) {
    return path;
}

void *JVM_RawMonitorCreate(void) {
    pthread_mutex_t *monitor = malloc(sizeof(*monitor));
    if (monitor == NULL) return NULL;
    pthread_mutexattr_t attributes;
    if (pthread_mutexattr_init(&attributes) != 0) {
        free(monitor);
        return NULL;
    }
    int status = pthread_mutexattr_settype(&attributes, PTHREAD_MUTEX_RECURSIVE);
    if (status == 0) status = pthread_mutex_init(monitor, &attributes);
    pthread_mutexattr_destroy(&attributes);
    if (status != 0) {
        free(monitor);
        return NULL;
    }
    return monitor;
}

void JVM_RawMonitorDestroy(void *monitor) {
    if (monitor != NULL && pthread_mutex_destroy(monitor) == 0) free(monitor);
}

int JVM_RawMonitorEnter(void *monitor) {
    return monitor != NULL && pthread_mutex_lock(monitor) == 0 ? 0 : -1;
}

void JVM_RawMonitorExit(void *monitor) {
    if (monitor != NULL) pthread_mutex_unlock(monitor);
}
