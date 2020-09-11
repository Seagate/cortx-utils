
var counters = function (key, value, ts, bucket, host) {
    bucket.push({
        "ns": host,
        "act": key,
        "val": value,
        "@timestamp": ts
    });
    return 1;
}

var timers = function (key, series, ts, bucket, host) {
    for (keyTimer in series) {
      bucket.push({
		"ns": host,
		"act": key,
		"val": series[keyTimer],
		"@timestamp": ts
	 });
    }
	return series.length;
}

var timer_data = function (key, value, ts, bucket, host) {
    value["@timestamp"] = ts;
    value["ns"]  = host;
    value["act"] = key;
    if (value['histogram']) {
      for (var keyH in value['histogram']) {
        value[keyH] = value['histogram'][keyH];
      }
      delete value['histogram'];
    }
    bucket.push(value);
}

exports.counters   = counters;
exports.timers     = timers;
exports.timer_data = timer_data;
exports.gauges     = counters;
