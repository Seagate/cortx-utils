add_executable(perf-manual-test
		perf-manual-test.c
		$<TARGET_OBJECTS:${UTILS_TSDB}>
	)


