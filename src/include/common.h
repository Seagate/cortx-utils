/**
 * Filename: common.h
 * Description: Headers for utils framework.
 *
 * Do NOT modify or remove this copyright and confidentiality notice!
 * Copyright (c) 2019, Seagate Technology, LLC.
 * The code contained herein is CONFIDENTIAL to Seagate Technology, LLC.
 * Portions are also trade secret. Any use, duplication, derivation, distribution
 * or disclosure of this code, for any reason, not expressly authorized is
 * prohibited. All other rights are expressly reserved by Seagate Technology, LLC.
 * 
 * Author: Yogesh Lahane <yogesh.lahane@seagate.com>
 *
 */

#ifndef _UTILS_COMMON_H
#define _UTILS_COMMON_H

#define _PUBLIC			__attribute__ ((visibility ("default")))
#define _PRIVATE		__attribute__ ((visibility ("hidden")))

#define likely(__cond)   __builtin_expect(!!(__cond), 1)

#define unlikely(__cond) __builtin_expect(!!(__cond), 0)

#endif
