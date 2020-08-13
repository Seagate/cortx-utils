/*
 * Filename: common.h
 * Description: Headers for utils framework.
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

#ifndef _UTILS_COMMON_H
#define _UTILS_COMMON_H

#include <stddef.h>

#define _PUBLIC			__attribute__ ((visibility ("default")))
#define _PRIVATE		__attribute__ ((visibility ("hidden")))

#define likely(__cond)   __builtin_expect(!!(__cond), 1)

#define unlikely(__cond) __builtin_expect(!!(__cond), 0)
#ifndef container_of
#define container_of(ptr, type, member) (type*)((char*)(ptr) - offsetof(type, member))
#endif

#define LIST_FOREACH_SAFE(var, head, field, tvar)                       \
	for ((var) = LIST_FIRST((head));                                \
		(var) && ((tvar) = LIST_NEXT((var), field), 1);         \
		(var) = (tvar))

#endif
