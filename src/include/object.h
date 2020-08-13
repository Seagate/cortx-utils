/*
 * Filename: object.h
 * Description: Contains definitions of obj_id_t
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

#ifndef _UTILS_OBJECT_H
#define _UTILS_OBJECT_H

#include <stdint.h>
#include <inttypes.h>

typedef struct obj_id {
        uint64_t f_hi;
        uint64_t f_lo;
} obj_id_t;


#define OBJ_ID_F "<%" PRIx64 ":%" PRIx64 ">"
#define OBJ_ID_P(_objid) (_objid)->f_hi, (_objid)->f_lo

#endif
