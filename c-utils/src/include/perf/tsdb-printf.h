/*
 * Filename:	tsdb-printf.h
 * Description:	This module defines a dummy printf-based TSDB engine.
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

/* This module can be used only for debugging of public TSDB API. It has
 * zero meaning for real-life scenarios.
 */

#ifndef TSDB_PRINTF_H_
#define TSDB_PRINTF_H_
/******************************************************************************/
#include <stdio.h>
#include <stdint.h>

/******************************************************************************/

#ifndef TSDB_FOUT
#define TSDB_FOUT stdout
#endif

#ifndef TSDB_PREFIX
#define TSDB_PREFIX "TSDB::"
#endif

static inline
void tsdb_add(uint64_t id, int n, const uint64_t *value)
{
	int i;

	fprintf(TSDB_FOUT, TSDB_PREFIX "add: ID=%lx", (unsigned long) id);

	for (i = 0; i < n; i++) {
		fprintf(TSDB_FOUT, ", %lx", (unsigned long) value[i]);
	}

	fprintf(TSDB_FOUT, ";\n");
}

static inline
void tsdb_leave(void)
{
	fprintf(TSDB_FOUT, "leave;\n");
}


#define TSDB_ACTION_ID_BASE 0


/******************************************************************************/
#endif /* TSDB_PRINTF_H_ */
