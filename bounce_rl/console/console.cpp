#include <assert.h>
#include <fcntl.h>
#include <malloc.h>
#include <readline/history.h>
#include <readline/readline.h>
#include <stdbool.h>
#include <stdio.h>
#include <string>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

int main(int argc, char **argv) {
  int fd;
  assert(argc == 2);

  printf("Opening pipe: %s for writes.\n", argv[1]);
  fd = open(argv[1], O_WRONLY);

  if (fd < 0) {
    fprintf(stderr, "Failed to open pipe named: %s\n", argv[1]);
    fprintf(stderr, "Exiting.\n", argv[1]);
    return 1;
  }


  while (true) {
    char *input = readline("$ ");
    add_history(input);

    std::string input_string = input;
    input_string.push_back('\n');
    ssize_t written = write(fd, input_string.c_str(), input_string.size());
    if (written < 0) {
      fprintf(stderr, "Failed to write to command pipe. Exiting.\n");
      return 1;
    }

    free(input);
    input = 0;
  }
}
