/*
 * Flush stats to ElasticSearch (http://www.elasticsearch.org/)
 *
 * To enable this backend, include 'elastic' in the backends
 * configuration array:
 *
 *   backends: ['./backends/elastic']
 *  (if the config file is in the statsd folder)
 *
 * A sample configuration can be found in exampleElasticConfig.js
 *
 * This backend supports the following config options:
 *
 *   host:            hostname or IP of ElasticSearch server
 *   port:            port of Elastic Search Server
 *   path:            http path of Elastic Search Server (default: '/')
 *   indexPrefix:     Prefix of the dynamic index to be created (default: 'statsd')
 *   indexTimestamp:  Timestamping format of the index, either "year", "month",
 *                    "day", or "hour"
 *   indexType:       The dociment type of the saved stat (default: 'stat')
 */

var http = require('http');
// this will be instantiated to the logger
var lg;
var debug;
var statsdHost;
var elasticHost;
var elasticPort;
var elasticPath;
var elasticIndex;
var elasticIndexTimestamp;
var elasticCountType;
var elasticTimerDataType;
var elasticTimerType;
var elasticUsername;
var elasticPassword;
var prev_counter_index;
var prev_timer_index;
var prev_timerdata_index;
var prev_gauge_index;

var elasticStats = {};


var es_bulk_insert = function elasticsearch_bulk_insert(listCounters, listTimers,
  listTimerData, listGaugeData) {
  var renderKV = function(k, v) {
  if (typeof v == 'number') {
      return '"'+k+'":'+v;
    }
    return '"'+k+'":"'+v+'"';
  };
  statsdCounterIndex = elasticIndex;
  statsdTimerIndex = elasticIndex;
  statsdTimerDataIndex = elasticIndex;
  statsdGaugeDataIndex = elasticIndex;
  ({ statsdCounterIndex, statsdTimerIndex, statsdTimerDataIndex, statsdGaugeDataIndex }
    = getStatsIndexes(statsdCounterIndex, statsdTimerIndex,
      statsdTimerDataIndex, statsdGaugeDataIndex));

  // Counter
  if (elasticCountType != 'disable') {
    setData(listCounters, statsdCounterIndex, renderKV, prev_counter_index);
  }

  // Timer
  if (elasticTimerType != 'disable') {
    setData(listTimers, statsdTimerIndex, renderKV, prev_timer_index);
  }

  // Timer data
  if (elasticTimerDataType != 'disable') {
    setData(listTimerData, statsdTimerDataIndex, renderKV, prev_timerdata_index);
  }

  // Gauge
  if(elasticGaugeDataType != 'disable') {
    setData(listGaugeData, statsdGaugeDataIndex, renderKV, prev_gauge_index);
  }
}

var flush_stats = function elastic_flush(ts, metrics) {
  var numStats = 0;
  var key;
  var array_counts     = new Array();
  var array_timers     = new Array();
  var array_timer_data = new Array();
  var array_gauges     = new Array();

  ts = ts*1000;

  ts = new Date(ts).toISOString()

  for (key in metrics.counters) {
    numStats += fm.counters(key, metrics.counters[key], ts, array_counts, statsdHost);
  }

  for (key in metrics.timers) {
    numStats += fm.timers(key, metrics.timers[key], ts, array_timers, statsdHost);
  }

  if (array_timers.length > 0) {
    for (key in metrics.timer_data) {
      fm.timer_data(key, metrics.timer_data[key], ts, array_timer_data, statsdHost);
    }
  }

  for (key in metrics.gauges) {
    numStats += fm.gauges(key, metrics.gauges[key], ts, array_gauges, statsdHost);
  }

  if (debug) {
    lg.log('metrics:');
    lg.log( JSON.stringify(metrics) );
  }

  try {
    es_bulk_insert(array_counts, array_timers, array_timer_data, array_gauges);
  }
  catch (e) {
    lg.log("warning","Connection to elasticsearch is failed.");
  }

  if (debug) {
    lg.log("debug", "flushed " + numStats + " stats to ES");
  }
};

var elastic_backend_status = function (writeCb) {
  for (stat in elasticStats) {
    writeCb(null, 'elastic', stat, elasticStats[stat]);
  }
};

exports.init = function elasticsearch_init(startup_time, config, events, logger) {

  lg = logger;

  var configEs = config.elasticsearch || { };

  debug                 = config.debug;
  statsdHost            = config.statsd_host      || 'localhost';
  flushInterval         = config.flushInterval    || 10000;
  elasticHost           = configEs.host           || 'localhost';
  elasticPort           = configEs.port           || 9200;
  elasticPath           = configEs.path           || '/';
  elasticIndex          = configEs.indexPrefix    || 'statsd';
  elasticIndexTimestamp = configEs.indexTimestamp || 'day';
  elasticCountType      = configEs.countType      || 'disable';
  elasticTimerType      = configEs.timerType      || 'disable';
  elasticTimerDataType  = configEs.timerDataType  || 'disable';
  elasticGaugeDataType  = configEs.gaugeDataType  || 'disable';
  elasticFormatter      = configEs.formatter      || 'default_format';
  elasticUsername       = configEs.username       || undefined;
  elasticPassword       = configEs.password       || undefined;
  replication           = configEs.replication    || 1;

  fm   = require('./' + elasticFormatter + '.js')
  if (debug) {
    lg.log("debug", "loaded formatter " + elasticFormatter);
  }

  if (fm.init) {
    fm.init(configEs);
  }

  elasticStats.last_flush = startup_time;
  elasticStats.last_exception = startup_time;

  events.on('flush', flush_stats);
  events.on('status', elastic_backend_status);

  return true;
};

function setData(listData, statsdIndex, renderKV, prev_index) {
  var payload = '';
  for (key in listData) {
    payload += '{"index":{"_index":"' + statsdIndex + '","_type":"telementry"}}' + "\n";
    payload += '{';
    innerPayload = '';
    for (statKey in listData[key]) {
      if (innerPayload)
        innerPayload += ',';
      innerPayload += renderKV(statKey, listData[key][statKey]);
    }
    payload += innerPayload + '}' + "\n";
  }

  if (replication == 2) {
    if (prev_index != statsdIndex) {
      try {
        var reqOpts = {
          host: elasticHost,
          port: elasticPort,
          path: elasticPath + statsdIndex,
          method: 'PUT'
        }
        req = http.request(reqOpts, function (res) {
        }).on('error', function (err) {
          lg.log('warning', 'Elasticsearch-Statsd connection failed, No stats flushed.');
        });
        req.end();

        settings_payload = '{ \"index\" : { \"auto_expand_replicas\": \"1-all\" }}'
        settingsOptions = {
          host: elasticHost,
          port: elasticPort,
          path: elasticPath + statsdIndex + "/_settings",
          method: "PUT",
          headers: {'Content-Type': 'application/json'}
        };
        settings_req = http.request(settingsOptions, function(res) {
        }).on('error', function (err) {
          lg.log('warning', 'Elasticsearch-Statsd connection failed, No stats flushed.');
        });
        settings_req.write(settings_payload);
        settings_req.end();

        prev_index = statsdIndex
      } catch (err) {
        lg.log("error", err)
      }
    }
  }

  var optionsPost = {
    host: elasticHost,
    port: elasticPort,
    path: elasticPath + statsdIndex + '/' + '/_bulk',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': payload.length
    }
  };
  if (elasticUsername && elasticPassword) {
    optionsPost.auth = elasticUsername + ':' + elasticPassword;
  }
  var dataReq = http.request(optionsPost, function (res) {
    res.on('data', function (d) {
      if (Math.floor(res.statusCode / 100) == 5) {
        var errdata = "HTTP " + res.statusCode + ": " + d;
        lg.log('error', errdata);
      }
    });
  }).on('error', function (err) {
    lg.log('warning', 'Elasticsearch-Statsd connection failed, No stats flushed.');
  });
  if (debug) {
    lg.log('ES payload:');
    lg.log(payload);
  }
  dataReq.write(payload);
  dataReq.end();
}

function getStatsIndexes(statsdCounterIndex, statsdTimerIndex,
  statsdTimerDataIndex, statsdGaugeDataIndex) {
  var indexDate = new Date();

  statsdCounterIndex += '_counter-' + indexDate.getUTCFullYear()
  statsdTimerIndex += '_timer-' + indexDate.getUTCFullYear()
  statsdTimerDataIndex += '_timerdata-' + indexDate.getUTCFullYear()
  statsdGaugeDataIndex += '_gauge-' + indexDate.getUTCFullYear()
  if (elasticIndexTimestamp == 'month' || elasticIndexTimestamp == 'day'
    || elasticIndexTimestamp == 'hour') {
    var indexMo = indexDate.getUTCMonth() + 1;
    if (indexMo < 10) {
      indexMo = '0' + indexMo;
    }
    statsdCounterIndex += '.' + indexMo;
    statsdTimerIndex += '.' + indexMo;
    statsdTimerDataIndex += '.' + indexMo;
    statsdGaugeDataIndex += '.' + indexMo;
  }
  if (elasticIndexTimestamp == 'day' || elasticIndexTimestamp == 'hour') {
    var indexDt = indexDate.getUTCDate();
    if (indexDt < 10) {
      indexDt = '0' + indexDt;
    }
    statsdCounterIndex += '.' + indexDt;
    statsdTimerIndex += '.' + indexDt;
    statsdTimerDataIndex += '.' + indexDt;
    statsdGaugeDataIndex += '.' + indexDt;
  }
  if (elasticIndexTimestamp == 'hour') {
    var indexDt = indexDate.getUTCHours();
    if (indexDt < 10) {
      indexDt = '0' + indexDt;
    }
    statsdCounterIndex += '.' + indexDt;
    statsdTimerIndex += '.' + indexDt;
    statsdTimerDataIndex += '.' + indexDt;
    statsdGaugeDataIndex += '.' + indexDt;
  }
  return { statsdCounterIndex, statsdTimerIndex, statsdTimerDataIndex, statsdGaugeDataIndex };
}