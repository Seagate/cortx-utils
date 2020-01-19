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

#ifndef _EOS_UTILS_H_
#define _EOS_UTILS_H_

#include <stdint.h>
#include <linux/limits.h>

#define STR256_F "%*.s"
#define STR256_P(__s) ((__s)->s_len), ((__s)->s_str)

/** A string object which has a C string (up to 255 characters)
 * and its length.
 */
struct str256 {
        /** The length of the C string. */
        uint8_t s_len;
        /** A buffer which contains a null-terminated C string. */
        char    s_str[NAME_MAX + 1];
} __attribute__((packed));

typedef struct str256 str256_t;

/* Fills in a str256 string from a C (null-terminated) string.
 * `str_len` is optional (0 makes it use strlen internally).
 * If the "src" cannot fit into "dst" then false is returned.
 * */
int str256_from_cstr(str256_t *dst, const char *src, size_t src_len);

#endif /* _EOS_UTILS_H_ */

