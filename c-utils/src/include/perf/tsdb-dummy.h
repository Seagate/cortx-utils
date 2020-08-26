/*
 * Filename:	tsdb-dummy.h
 * Description:	This module defines a noop implementation of TSDB backend.
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

#ifndef TSDB_DUMMY_H_
#define TSDB_DUMMY_H_
/******************************************************************************/
#include <stdint.h>

/******************************************************************************/

static inline
void tsdb_add(uint64_t id, int n, const uint64_t *value) { }
static inline
void tsdb_leave(void) { }


#define TSDB_ACTION_ID_BASE 0

/******************************************************************************/
#endif /* TSDB_DUMMY_H_ */
