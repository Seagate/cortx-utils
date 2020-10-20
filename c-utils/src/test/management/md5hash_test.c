/*
 * Filename: md5hash_test.c
 * Description: Unit test cases for md5hash.
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

#include <stdio.h>
#include <string.h>
#include "md5hash.h"
#include "common/log.h"
#include <errno.h>

int test_basic_string()
{
	char input[] = "abcdefghijklmnopqrstuvwxyz";
	struct md5hash hash = MD5HASH_INIT_EMPTY;
	str256_t hex_str, req_str;
	int rc = 0;

	rc = md5hash_compute(input, sizeof(input)-1, &hash);
	if (rc) {
		goto out;
	}

	rc = md5hash_get_string(&hash, &hex_str);
	if (rc) {
		goto out;
	}

	/* MD5 value from RFC 1321
	   https://www.ietf.org/rfc/rfc1321.txt
	*/
	char tmp[] = "c3fcd3d76192e4007dfb496cca67e13b";
	str256_from_cstr(req_str, tmp, sizeof(tmp)-1);

	rc = md5hash_validate(&hex_str, &req_str);

out:
	return rc;
}

int test_empty_string()
{
	char input[] = "12345678901234567890123456789012345678901234567890123456789"
	               "012345678901234567890";
	struct md5hash hash = MD5HASH_INIT_EMPTY;
	str256_t hex_str, req_str;
	int rc = 0;

	rc = md5hash_compute(input, sizeof(input)-1, &hash);
	if (rc) {
		goto out;
	}

	rc = md5hash_get_string(&hash, &hex_str);
	if (rc) {
		goto out;
	}

	char tmp[] = "57edf4a22be3c955ac49da2e2107b67a";
	str256_from_cstr(req_str, tmp, sizeof(tmp)-1);

	rc = md5hash_validate(&hex_str, &req_str);

out:
	return rc;
}

int test_numeral_string()
{
	char input[] = "";
	struct md5hash hash = MD5HASH_INIT_EMPTY;
	str256_t hex_str, req_str;
	int rc = 0;

	rc = md5hash_compute(input, 0, &hash);
	if (rc) {
		goto out;
	}

	rc = md5hash_get_string(&hash, &hex_str);
	if (rc) {
		goto out;
	}

	char tmp[] = "d41d8cd98f00b204e9800998ecf8427e";
	str256_from_cstr(req_str, tmp, sizeof(tmp)-1);

	rc = md5hash_validate(&hex_str, &req_str);

out:
	return rc;
}

int main(int argc, char *argv[])
{
	int test_count = 3;
	int test_failed = 0;
	int rc;

	rc = test_basic_string();
	if (rc) {
		test_failed++;
	}

	rc = test_empty_string();
	if (rc) {
		test_failed++;
	}

	rc = test_numeral_string();
	if (rc) {
		test_failed++;
	}
	/* Test summary */
	printf("Total tests  = %d\n", test_count);
	printf("Tests passed = %d\n", test_count-test_failed);
	printf("Tests failed = %d\n", test_failed);

	return 0;
}
