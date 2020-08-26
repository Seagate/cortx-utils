/*
 * Filename:	tsdb.c
 * Description:	This module implements TSDB frontend interface.
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
 
#include "perf/tsdb.h"

/** TSDB state */
struct tsdb_module {
	/** Engine state.
	 * The state is a readonly properly. It can be set (or cleared)
	 * in a call to ::tsdb_init, and it cannot be changed later.
	 */
	bool is_engine_on;

	/** Runtime state.
	 * This is mutable properly. It can be changed using
	 * ::tsdb_set_rt_state.
	 */
	bool is_rt_on;
};

/** TSDB singleton. */
static struct tsdb_module g_tsdb;

bool tsdb_is_on(void)
{
	return g_tsdb.is_rt_on && g_tsdb.is_engine_on;
}

bool tsdb_is_engine_on(void)
{
	return g_tsdb.is_engine_on;
}

void tsdb_set_rt_state(bool state)
{
	g_tsdb.is_rt_on = state;
}

int tsdb_init(bool engine_state, bool rt_state)
{
	g_tsdb.is_engine_on = engine_state;
	g_tsdb.is_rt_on = rt_state;

	return 0; /* nothing can fail at this moment */
}

void tsdb_fini(void)
{
	g_tsdb.is_rt_on = false;
	g_tsdb.is_engine_on = false;
}

