#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
  pid_t pid = fork();
  if (pid == -1) {
    perror("fork");
    exit(EXIT_FAILURE);
  }
  if (pid == 0) {
    // Child process
    char **args = malloc(sizeof(char *) * argc);
    if (args == NULL) {
      perror("malloc");
      exit(EXIT_FAILURE);
    }
    for (int i = 1; i < argc; i++) {
      args[i - 1] = argv[i];
    }
    args[argc - 1] = NULL;
    execvp(args[0], args);
  } else {
    // Parent process
    waitpid(pid, NULL, 0);
  }
  printf("Done\n");
  return 0;
}
