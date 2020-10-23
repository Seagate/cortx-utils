/*
 * Filename: md5hash.h
 * Description: MD5 - Data types and declarations for MD5 Hashing algorithm
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

#ifndef _MD5HASH_H_
#define _MD5HASH_H_

#include <openssl/md5.h> /* MD5_CTX, MD5 APIs */
#include <stdbool.h> /* bool */
#include "str.h"  /* str256_t */

#define DIGEST_LENGTH MD5_DIGEST_LENGTH

#define MD5HASH_INIT_EMPTY (struct md5hash) { .is_finalized = false }

struct md5hash {
	MD5_CTX md5ctx;  /* MD5 context */
	unsigned char md5_digest[DIGEST_LENGTH]; /* Buffer to hold the message digest */
	bool is_finalized; /* Holds state of message digest */
};

/** Computes the MD5 checksum (hash) and stores it in the md5hash object context
 *  based on the data buffer passed.
 *
 *  @param[in] input - data buffer whose hash is to be computed.
 *  @param[in] len - length of the data buffer
 *  @param[out] hash - md5hash object where the hash is computed and stored.
 *
 *  @return 0 if successful, a negative "-errno" value in case of failure
 */
int md5hash_compute(const char *input, size_t len, struct md5hash *hash);

/** Maps the MD5 message digest to its equivalent hex string.
 *  NOTE: The caller must first compute the hash in order to get a valid
 *        MD5 message digest.
 *
 * @param[in] hash - md5hash object holding valid MD5 message digest
 * @param[out] hex_str - string which holds the hex string of message digest
 *
 * @return 0 if successful, a negative "-errno" value in case of failure
 */
int md5hash_get_string(struct md5hash *hash, str256_t  *hex_str);

/** Validates the calculated hex string with the requested hex string.
 *
 *  @param[in] calc_str - hex string calculated from md5hash object
 *  @param[in] req_str - hex string requested.
 *
 *  @return 0 if successful, "-ENOENT" value in case of failure
 */
int md5hash_validate(str256_t *calc_str, str256_t *req_str);

#endif /* _MD5HASH_H_ */
