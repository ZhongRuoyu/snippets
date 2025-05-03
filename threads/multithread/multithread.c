#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <unistd.h>

enum { kThreadsCount = 8 };

static _Atomic int found;
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
static int a;
static int b;
static int c;
static pthread_mutex_t next_mutex = PTHREAD_MUTEX_INITIALIZER;
static int next_a;
static int next_b;

int Find(int a, int b) {
  for (int c = 0; c < 10000; ++c) {
    int x = 10000 * 10000 * a + 10000 * b + c;
    usleep(1);
    if (x == 3141592) {
      return c;
    }
  }

  return -1;
}

void *Work(void *arg) {
  int worker_id = *(int *)arg;

  for (;;) {
    if (atomic_load(&found)) {
      printf("Worker %d: Found already, exiting\n", worker_id);
      break;
    }

    pthread_mutex_lock(&next_mutex);
    int try_a = next_a;
    int try_b = next_b++;
    if (next_b == 10000) {
      next_b = 0;
      next_a++;
      if (next_a >= 10000) {
        printf("Worker %d: Exhausted all possibilities\n", worker_id);
        pthread_mutex_unlock(&next_mutex);
        break;
      }
    }
    pthread_mutex_unlock(&next_mutex);

    int try_c = Find(try_a, try_b);
    if (try_c != -1) {
      atomic_store(&found, 1);
      pthread_mutex_lock(&mutex);
      a = try_a;
      b = try_b;
      c = try_c;
      pthread_mutex_unlock(&mutex);
      printf("Worker %d: Found a = %d, b = %d, c = %d\n", worker_id, try_a,
             try_b, try_c);
      break;
    }

    printf("Worker %d: Not found with a = %d, b = %d\n", worker_id, try_a,
           try_b);
  }

  return NULL;
}

int main(int argc, char **argv) {
  atomic_init(&found, 0);

  int worker_ids[kThreadsCount];
  pthread_t workers[kThreadsCount];
  for (int i = 0; i < kThreadsCount; ++i) {
    worker_ids[i] = i;
    pthread_create(&workers[i], NULL, Work, &worker_ids[i]);
  }
  for (int i = 0; i < kThreadsCount; ++i) {
    pthread_join(workers[i], NULL);
  }

  printf("\n");
  if (atomic_load(&found)) {
    printf("Found a = %d, b = %d, c = %d\n", a, b, c);
  } else {
    printf("Not found\n");
  }
}
