#include <stdarg.h>
#include <sysexits.h>   /* EX_* exit codes (EX_OSERR, EX_SOFTWARE) */
#include "lib/uuid.h"              /* m0_node_uuid_string_set */

#include "module/instance.h"       /* m0 */
#include "motr/init.h"             /* m0_init */
#include "lib/uuid.h"              /* m0_node_uuid_string_set */
#include "lib/getopts.h"           /* M0_GETOPTS */
#include "lib/thread.h"            /* LAMBDA */
#include "lib/string.h"            /* m0_strdup */
#include "lib/user_space/types.h"  /* bool */
#include "lib/user_space/trace.h"  /* m0_trace_parse */
#include "lib/misc.h"              /* ARRAY_SIZE */
#include "lib/trace.h"

#include "m0log.h"

/* file for magical symbol file */
const int  m0trace_common1 = 2811;


int test_m0log_setup(void)
{

	m0_trace_init();

	int rc = 0;

        rc = m0_trace_set_immediate_mask("all");
        if (rc) {
                printf("Failed to set mask, rc = %d", rc);
                goto out;
        }
        rc = m0_trace_set_print_context("full");
        if (rc) {
                printf("Failed to set print context, rc = %d", rc);
                goto out;
        }
        rc = m0_trace_set_level("debug");
        if (rc) {
                printf("Failed to set trace level, rc = %d", rc);
                goto out;
        }
        m0_trace_set_mmapped_buffer(true);
out:
        return rc;
}

void test_m0log_common1_setup(const void* p)
{
	int rc = 0;
        rc = m0_trace_magic_sym_extra_addr_add(p);
}

void m0log_fini(void)
{
	m0_trace_fini();
}


void my_funct1(void)
{
        M0_LOG(M0_DEBUG, "\n In my_funct1");
}

#define DEFAULT_M0MOTR_KO_IMG_PATH  "/var/log/motr/m0motr_ko.img"

int decoder (const void* p, char *ifile, char *ofile)
{

	const char *m0motr_ko_path        = DEFAULT_M0MOTR_KO_IMG_PATH;
	enum m0_trace_parse_flags flags   = M0_TRACE_PARSE_DEFAULT_FLAGS;
	FILE       *input_file;
	FILE       *output_file;
	int         rc=0;
	const void *magic_symbols[1];
	static struct m0 instance;

	m0_trace_set_mmapped_buffer(false);
	m0_node_uuid_string_set(NULL);

	rc = m0_init(&instance);
	if (rc != 0)
		return rc;

	const char *input_file_name =  m0_strdup(ifile);
	const char *output_file_name = m0_strdup(ofile);

	input_file = fopen(input_file_name, "r");
	if (input_file == NULL) {
		printf("Failed to open input file '%s'", input_file_name);
		rc = EX_NOINPUT;
		goto out;
	}

	output_file = fopen(output_file_name, "w");
	if (output_file == NULL) {
		printf("Failed to open output file '%s'", output_file_name);
		rc = EX_NOINPUT;
		goto out;
	}

	magic_symbols[0] = p;

	rc = m0_trace_parse(input_file, output_file, m0motr_ko_path, flags,
			magic_symbols, 1);
	if (rc != 0) {
		printf("Error occurred while parsing input trace data");
		rc = EX_SOFTWARE;
	}

out:
	m0_fini();
	fclose(output_file);
	fclose(input_file);

	return rc;
}

