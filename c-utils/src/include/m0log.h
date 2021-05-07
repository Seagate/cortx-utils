#ifndef TEST_M0LOG_H
#define TEST_M0LOG_H

#include <stdarg.h>
#include <stdio.h>

extern const int m0trace_common1;

int test_m0log_setup(void);
void m0log_fini(void);

void test_m0log_common1_setup(const void* p);

void my_funct1(void);

int decoder (const void* p, char *ifile, char *ofile);

#endif /* TEST_M0LOG_H */
