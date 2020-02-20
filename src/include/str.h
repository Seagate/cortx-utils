/*
 * Filename:         utils.h
 * Description:      common structures
 *
 * Do NOT modify or remove this copyright and confidentiality notice!
 * Copyright (c) 2019, Seagate Technology, LLC.
 * The code contained herein is CONFIDENTIAL to Seagate Technology, LLC.
 * Portions are also trade secret. Any use, duplication, derivation,
 * distribution or disclosure of this code, for any reason, not expressly
 * authorized is prohibited. All other rights are expressly reserved by
 * Seagate Technology, LLC.
 *
 */

#ifndef _EOS_STR_H_
#define _EOS_STR_H_

#include <stdint.h>
#include <debug.h>
#include <linux/limits.h>

#define STR256_F "%s"
#define STR256_P(__s) ((__s)->s_str)

/** A string object which has string pointe and its length. */
struct str {
    uint16_t s_len;
    char *s_str;
} __attribute__((packed));

typedef struct str str_t;

/** A string object which has a C string (up to 255 characters)
 * and its length. Note that the order of the fields of str256 cannot be
 * changed as its space optimized.
 */
struct str256 {
	uint8_t s_len;      /* Length of the string. */
	char    s_str[256]; /* Buffer containing null-terminated string. */
} __attribute__((packed));

typedef struct str256 str256_t;

/* Fills in a str256 string from a C (null-terminated) string.
 * `str_len` is optional (0 makes it use strlen internally).
 * If the "src" cannot fit into "dst" then false is returned.
 */
#define str256_from_cstr(dst, src, len) 				\
	do {                                                        	\
		memcpy(dst.s_str, src, len);                           	\
		dst.s_str[len] = '\0';                                 	\
		dst.s_len = len;                                       	\
	} while (0);

/* String Comparison: Evaluates to ZERO if both the strings are same, else non-zero */
#define str256_cmp(str1, str2)                            \
	(((str1)->s_len != (str2)->s_len) || memcmp((str1)->s_str, (str2)->s_str, (str1)->s_len))

/* String Copy: Copy Source String to Destination */
#define str256_cp(dst, src)                             	\
	do {                                                	\
		memcpy((dst)->s_str, (src)->s_str, src.s_len);  \
		(dst)->s_str[(dst)->s_len] = '\0';              \
		(dst)->s_len = (src)->s_len;                    \
	} while (0);

/* str256_isalphanum: Validate if ns_name is alpha numeric */
int str256_isalphanum(const str256_t *name);

#endif /* _EOS_STR_H_ */
