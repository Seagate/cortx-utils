/*
 * Filename:         utils.h
 * Description:      common structures
 *
 * Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU Affero General Public License for more details.
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 * For any questions about this software or licensing,
 * please email opensource@seagate.com or cortx-questions@seagate.com. 
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
