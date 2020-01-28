/*
 * Filename:         helpers.h
 * Description:      Helper macros in case of errors

 * Do NOT modify or remove this copyright and confidentiality notice!
 * Copyright (c) 2019, Seagate Technology, LLC.
 * The code contained herein is CONFIDENTIAL to Seagate Technology, LLC.
 * Portions are also trade secret. Any use, duplication, derivation,
 * distribution or disclosure of this code, for any reason, not expressly
 * authorized is prohibited. All other rights are expressly reserved by
 * Seagate Technology, LLC.

  Helper return code macros
*/

#ifndef _COMMON_HELPERS_H
#define _COMMON_HELPERS_H

#define RC_WRAP(__function, ...) ({\
	int __rc = __function(__VA_ARGS__);\
	if (__rc < 0)        \
		return __rc; })

#define RC_WRAP_LABEL(__rc, __label, __function, ...) ({\
	__rc = __function(__VA_ARGS__);\
	if (__rc < 0)        \
		goto __label; })


#define RC_WRAP_SET(__err) (log_trace("set_error: %d (%d)", __err, -__err), __err)

/* Uncomment this define if you want to get detailed trace
 * of RC_WRAP_LABEL calls
 */
// #define ENABLE_RC_WRAP_LABEL_TRACE
#if defined(ENABLE_RC_WRAP_LABEL_TRACE)

#undef RC_WRAP_LABEL

#define RC_WRAP_LABEL(__rc, __label, __function, ...) ({\
	__rc = __function(__VA_ARGS__);\
	log_trace("%s:%d, %s(%s) = %d\n", __FILE__, __LINE__,\
		# __function, #__VA_ARGS__, __rc); \
	if (__rc < 0)        \
		goto __label; })

#endif

#endif // _COMMON_HELPERS_H
