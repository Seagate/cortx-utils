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
 *   indexTimestamp:  Timestamping format of the index, either "year", "month", "day", or "hour"
 *   indexType:       The dociment type of the saved stat (default: 'stat')
 */

var net = require('net'),
   util = require('util'),
   http = require('http');
// this will be instantiated to the logger
var lg;
var debug;
var statsdHost;
var flushInterval;
var elasticHost;
var elasticPort;
var elasticPath;
var elasticIndex;
var elasticIndexTimestamp;
var elasticCountType;
var elasticTimerType;
var elasticUsername;
var elasticPassword;

var elasticStats = {};


var es_bulk_insert = function elasticsearch_bulk_insert(listCounters, listTimers, listTimerData, listGaugeData) {

      var renderKV = function(k, v) {
        if (typeof v == 'number') {
          return '"'+k+'":'+v;
        }
        return '"'+k+'":"'+v+'"';
        /*
        if (k === '@timestamp') {
          var s = new Date(v).toISOString();
          return '"'+k+'":"'+s+'"';
        } else if (k === 'val') {
          return '"'+k+'":'+v;
        } else {
          return '"'+k+'":"'+v+'"';
        }
        */
      };

      var indexDate = new Date();

      //var statsdIndex = elasticIndex + '-' + indexDate.getUTCFullYear()
      var statsdCounterIndex = elasticIndex + '_counter-' + indexDate.getUTCFullYear()
      var statsdTimerIndex = elasticIndex + '_timer-' + indexDate.getUTCFullYear()
      var statsdTimerDataIndex = elasticIndex + '_timerdata-' + indexDate.getUTCFullYear()
      var statsdGaugeDataIndex = elasticIndex + '_gauge-' + indexDate.getUTCFullYear()

      if (elasticIndexTimestamp == 'month' || elasticIndexTimestamp == 'day' || elasticIndexTimestamp == 'hour'){
        var indexMo = indexDate.getUTCMonth() +1;
        if (indexMo < 10) {
            indexMo = '0'+indexMo;
        }
        //statsdIndex += '.' + indexMo;
        statsdCounterIndex += '.' + indexMo;
        statsdTimerIndex += '.' + indexMo;
        statsdTimerDataIndex += '.' + indexMo;
        statsdGaugeDataIndex += '.' + indexMo;
      }

      if (elasticIndexTimestamp == 'day' || elasticIndexTimestamp == 'hour'){
        var indexDt = indexDate.getUTCDate();
        if (indexDt < 10) {
            indexDt = '0'+indexDt;
        }
        //statsdIndex += '.' +  indexDt;
        statsdCounterIndex += '.' + indexDt;
        statsdTimerIndex += '.' + indexDt;
        statsdTimerDataIndex += '.' + indexDt;
        statsdGaugeDataIndex += '.' + indexDt;
      }

      if (elasticIndexTimestamp == 'hour'){
        var indexDt = indexDate.getUTCHours();
        if (indexDt < 10) {
            indexDt = '0'+indexDt;
        }
        //statsdIndex += '.' +  indexDt;
        statsdCounterIndex += '.' + indexDt;
        statsdTimerIndex += '.' + indexDt;
        statsdTimerDataIndex += '.' + indexDt;
        statsdGaugeDataIndex += '.' + indexDt;
      }

      var counterPayload = '';
      for (key in listCounters) {
        counterPayload += '{"index":{"_index":"'+statsdCounterIndex+'","_type":"telementry"}}'+"\n";
        counterPayload += '{';
        innerPayload = '';
          for (statKey in listCounters[key]){
            if (innerPayload) innerPayload += ',';
            innerPayload += renderKV(statKey, listCounters[key][statKey]);
            //innerPayload += '"'+statKey+'":"'+listCounters[key][statKey]+'"';
          }
          counterPayload += innerPayload +'}'+"\n";
      }
      var counterOptionsPost = {
        host: elasticHost,
        port: elasticPort,
        path: elasticPath + statsdCounterIndex + '/' + '/_bulk',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': counterPayload.length
        }
      };

      if(elasticUsername && elasticPassword) {
          timerOptionsPost.auth = elasticUsername + ':' + elasticPassword;
      }

      var counterReq = http.request(counterOptionsPost, function(res) {
          res.on('data', function(d) {
            if (Math.floor(res.statusCode / 100) == 5){
              var errdata = "HTTP " + res.statusCode + ": " + d;
              lg.log('error', errdata);
            }
          });
      }).on('error', function(err) {
          lg.log('error', 'Error with HTTP request, no stats flushed.');
      });

      if (debug) {
        lg.log('ES payload:');
        lg.log(counterPayload);
      }
      counterReq.write(counterPayload);
      counterReq.end();

      var timerPayload = '';
      for (key in listTimers) {
        timerPayload += '{"index":{"_index":"'+statsdTimerIndex+'","_type":"telementry"}}'+"\n";
        timerPayload += '{';
        innerPayload = '';
          for (statKey in listTimers[key]){
            if (innerPayload) innerPayload += ',';
            innerPayload += renderKV(statKey, listTimers[key][statKey]);
            //innerPayload += '"'+statKey+'":"'+listTimers[key][statKey]+'"';
          }
          timerPayload += innerPayload +'}'+"\n";
      }
      var timerOptionsPost = {
        host: elasticHost,
        port: elasticPort,
        path: elasticPath + statsdTimerIndex + '/' + '/_bulk',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': timerPayload.length
        }
      };

      if(elasticUsername && elasticPassword) {
          timerOptionsPost.auth = elasticUsername + ':' + elasticPassword;
      }

      var timerReq = http.request(timerOptionsPost, function(res) {
          res.on('data', function(d) {
            if (Math.floor(res.statusCode / 100) == 5){
              var errdata = "HTTP " + res.statusCode + ": " + d;
              lg.log('error', errdata);
            }
          });
      }).on('error', function(err) {
          lg.log('error', 'Error with HTTP request, no stats flushed.');
      });

      if (debug) {
        lg.log('ES payload:');
        lg.log(timerPayload);
      }
      timerReq.write(timerPayload);
      timerReq.end();

      var timerDataPayload = '';
      for (key in listTimerData) {
        timerDataPayload += '{"index":{"_index":"'+statsdTimerDataIndex+'","_type":"telementry"}}'+"\n";
        timerDataPayload += '{';
        innerPayload = '';
          for (statKey in listTimerData[key]){
            if (innerPayload) innerPayload += ',';
            innerPayload += renderKV(statKey, listTimerData[key][statKey]);
            //innerPayload += '"'+statKey+'":"'+listTimerData[key][statKey]+'"';
          }
          timerDataPayload += innerPayload +'}'+"\n";
      }
      var timerDataOptionsPost = {
        host: elasticHost,
        port: elasticPort,
        path: elasticPath + statsdTimerDataIndex + '/' + '/_bulk',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': timerDataPayload.length
        }
      };

      if(elasticUsername && elasticPassword) {
        timerDataOptionsPost.auth = elasticUsername + ':' + elasticPassword;
      }

      var timerDataReq = http.request(timerDataOptionsPost, function(res) {
          res.on('data', function(d) {
            if (Math.floor(res.statusCode / 100) == 5){
              var errdata = "HTTP " + res.statusCode + ": " + d;
              lg.log('error', errdata);
            }
          });
      }).on('error', function(err) {
          lg.log('error', 'Error with HTTP request, no stats flushed.');
      });

      if (debug) {
        lg.log('ES payload:');
        lg.log(timerDataPayload);
      }
      timerDataReq.write(timerDataPayload);
      timerDataReq.end();

      var gaugePayload = '';
      for (key in listGaugeData) {
        gaugePayload += '{"index":{"_index":"'+statsdGaugeDataIndex+'","_type":"telementry"}}'+"\n";
        gaugePayload += '{';
        innerPayload = '';
          for (statKey in listGaugeData[key]){
            if (innerPayload) innerPayload += ',';
            innerPayload += renderKV(statKey, listGaugeData[key][statKey]);
            //innerPayload += '"'+statKey+'":"'+listGaugeData[key][statKey]+'"';
          }
          gaugePayload += innerPayload +'}'+"\n";
      }
      var gaugeOptionsPost = {
        host: elasticHost,
        port: elasticPort,
        path: elasticPath + statsdGaugeDataIndex + '/' + '/_bulk',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': gaugePayload.length
        }
      };

      if(elasticUsername && elasticPassword) {
        gaugeOptionsPost.auth = elasticUsername + ':' + elasticPassword;
      }

      var gaugeReq = http.request(gaugeOptionsPost, function(res) {
          res.on('data', function(d) {
            if (Math.floor(res.statusCode / 100) == 5){
              var errdata = "HTTP " + res.statusCode + ": " + d;
              lg.log('error', errdata);
            }
          });
      }).on('error', function(err) {
          lg.log('error', 'Error with HTTP request, no stats flushed.');
      });

      if (debug) {
        lg.log('ES payload:');
        lg.log(gaugePayload);
      }
      gaugeReq.write(gaugePayload);
      gaugeReq.end();
}

var flush_stats = function elastic_flush(ts, metrics) {
  var statString = '';
  var numStats = 0;
  var key;
  var array_counts     = new Array();
  var array_timers     = new Array();
  var array_timer_data = new Array();
  var array_gauges     = new Array();

  ts = ts*1000;

  ts = new Date(ts).toISOString()

/*
  var gauges = metrics.gauges;
  var pctThreshold = metrics.pctThreshold;
*/

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

  es_bulk_insert(array_counts, array_timers, array_timer_data, array_gauges);

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

  debug = config.debug;
  lg = logger;

  var configEs = config.elasticsearch || { };

  statsdHost            = config.statsd_host      || 'localhost';
  elasticHost           = configEs.host           || 'localhost';
  elasticPort           = configEs.port           || 9200;
  elasticPath           = configEs.path           || '/';
  elasticIndex          = configEs.indexPrefix    || 'statsd';
  elasticIndexTimestamp = configEs.indexTimestamp || 'day';
  elasticCountType      = configEs.countType      || 'counter';
  elasticTimerType      = configEs.timerType      || 'timer';
  elasticTimerDataType  = configEs.timerDataType  || elasticTimerType + '_stats';
  elasticGaugeDataType  = configEs.gaugeDataType  || 'gauge';
  elasticFormatter      = configEs.formatter      || 'default_format';
  elasticUsername       = configEs.username       || undefined;
  elasticPassword       = configEs.password       || undefined;

  fm   = require('./' + elasticFormatter + '.js')
  if (debug) {
    lg.log("debug", "loaded formatter " + elasticFormatter);
  }

  if (fm.init) {
    fm.init(configEs);
  }
  flushInterval         = config.flushInterval;

  elasticStats.last_flush = startup_time;
  elasticStats.last_exception = startup_time;


  events.on('flush', flush_stats);
  events.on('status', elastic_backend_status);

  return true;
};

