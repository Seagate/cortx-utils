/**
 * Filename:	tsdb-addb.h
 * Description:	This module defines ADDB-based interfaces for TSDB.
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
 * please email opensource@seagate.com or cortx-questions@seagate.com.*
 */
#ifndef TSDB_ADDB_H_
#define TSDB_ADDB_H_
/******************************************************************************/
#include <stdint.h>

/******************************************************************************/

/* Note: We do not include addb headers directly in order to avoid
 * problems with contamination of the other source files.
 * So that, we just define this constant right here.
 * A corresponding compile-time check will be added into
 * the source file.
 */
#define TSDB_ACTION_ID_BASE 0x0020000

void m0_addb2_add(uint64_t id, int n, const uint64_t *value);
void m0_addb2_global_leave(void);

static inline
void tsdb_add(uint64_t id, int n, const uint64_t *value)
{
	m0_addb2_add(id, n, value);
}

static inline
void tsdb_leave(void)
{
	m0_addb2_global_leave();
}

/******************************************************************************/
#endif /* TSDB_ADDB_H_ */
