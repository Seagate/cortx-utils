/*
 * Filename:         debug.h
 * Description:      Debug related configuration
 *
 * Do NOT modify or remove this copyright and confidentiality notice!
 * Copyright (c) 2019, Seagate Technology, LLC.
 * The code contained herein is CONFIDENTIAL to Seagate Technology, LLC.
 * Portions are also trade secret. Any use, duplication, derivation,
 * distribution or disclosure of this code, for any reason, not expressly
 * authorized is prohibited. All other rights are expressly reserved by
 * Seagate Technology, LLC.
 *
 */

#ifndef _DEBUG_H
#define _DEBUG_H

#include <assert.h>

#ifdef ENABLE_DASSERT
#define dassert assert
#else
#define dassert(...)
#endif /* ENABLE_DASSERT */

#endif /* _DEBUG_H */

