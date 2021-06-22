#!/usr/bin/env python3
import code

src = """
#include <stdio.h>
#include <stdlib.h>

int main()
{
    printf("ok\\n");
    usleep(100000);
    return 1;
}
"""

print(code.run('c', src))
