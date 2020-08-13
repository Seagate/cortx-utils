/*
 * Filename:         helpers.h
 * Description:      Helper macros in case of errors
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
