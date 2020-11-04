/*
 * Filename: md5hash.c
 * Description: APIs for md5hash.c for computing hash based on the data buffer.
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

#include <string.h>
#include <errno.h>
#include "md5hash.h"
#include "common/log.h"

#define HASH_BLK_SIZE 1024*64
#define HIGHER_NIB(ch) ch >> 4   /* Masking higher nibble */
#define LOWER_NIB(ch) ch & 0x0F  /* Masking lower nibble */

const char hex_tbl[] = "0123456789abcdef";

int md5hash_compute(const char *input, size_t length, struct md5hash *hash)
{
	int rc = 0;

	dassert(hash);
	dassert(input);

	/* MD5 hash is not prior computed */
	dassert(!hash->is_finalized);

	rc = MD5_Init(&hash->md5ctx);
	if (rc < 1) {
		rc = -EINVAL;
		goto out;
	}

	/* Calculates hash for an empty string */
	if (length == 0) {
		rc = MD5_Update(&hash->md5ctx, input, length);
		if (rc < 1) {
			goto update_fail;
		}
	} else {
		while (length > HASH_BLK_SIZE) {
			rc = MD5_Update(&hash->md5ctx, input, HASH_BLK_SIZE);
			if (rc < 1) {
				goto update_fail;
			}
			input += HASH_BLK_SIZE;
			length -= HASH_BLK_SIZE;
		}
		if (length > 0) {
			rc = MD5_Update(&hash->md5ctx, input, length);
			if (rc < 1) {
				goto update_fail;
			}
		}
	}
	rc = MD5_Final(hash->md5_digest, &hash->md5ctx);
	if (rc < 1) {
		rc = -EINVAL;
		goto out;
	}
	/* Success */
	hash->is_finalized = true;
	rc = 0;
	goto out;

update_fail:
	if (rc < 1) {
		log_err("Invalid data buffer");
		rc = -EINVAL;
	}

out:
	log_debug("md5hash hash=%p, length of data buf=%zu", hash, length);
	return rc;
}

int md5hash_get_string(struct md5hash *hash, str256_t  *hex_str)
{
	int i, rc = 0;
	unsigned int ch;
	char hex[DIGEST_LENGTH * 2] = "";

	dassert(hash);
	dassert(hex_str);

	if (!hash->is_finalized) {
		log_err("MD5 hash is not computed");
		rc = -EINVAL;
		goto out;
	}

	/* Convert to unsigned char which can be represented in two hex digits,
	   0x00-0xFF */
	for (i = 0; i < DIGEST_LENGTH; ++i) {
		ch = hash->md5_digest[i] & 255;

		snprintf(hex + i*2, sizeof(hex), "%c", hex_tbl[HIGHER_NIB(ch)]);
		snprintf(hex + i*2 + 1, sizeof(hex), "%c", hex_tbl[LOWER_NIB(ch)]);
	}

	str256_from_cstr((*hex_str), hex, DIGEST_LENGTH * 2);

out:
	log_debug("md5hash hash=%p, hex string=" STR256_F, hash, STR256_P(hex_str));
	return rc;
}

int md5hash_validate(str256_t *calc_str, str256_t *req_str)
{
	int rc = 0;

	dassert(calc_str);
	dassert(req_str);

	rc = str256_cmp(calc_str, req_str);
	if (rc) {
		log_err("Requested hash does not match with the calculated hash");
		rc = -ENOENT;
	}

	log_debug("calculated hash=" STR256_F " and requested hash=" STR256_F,
	          STR256_P(calc_str), STR256_P(req_str));

	return rc;
}
