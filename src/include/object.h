/**
 * Filename: object.h
 * Description: Contains definitions of obj_id_t
 *
 * Do NOT modify or remove this copyright and confidentiality notice!
 * Copyright (c) 2019, Seagate Technology, LLC.
 * The code contained herein is CONFIDENTIAL to Seagate Technology, LLC.
 * Portions are also trade secret. Any use, duplication, derivation, distribution
 * or disclosure of this code, for any reason, not expressly authorized is
 * prohibited. All other rights are expressly reserved by Seagate Technology, LLC.
 *
 * Conatins definitions of obj_id_t
 *
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
