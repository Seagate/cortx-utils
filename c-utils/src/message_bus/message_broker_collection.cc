#include "message_broker.h"
#include<string.h>
#include<list>
#include<signal.h>
#include<iostream>
#include "log.h"
#include <librdkafka/rdkafka.h>
static volatile sig_atomic_t run = 1;

static void stop(int sig) {
        run = 0;
}
static int is_printable(const char *buf, size_t size) {
        size_t i;

        for (i = 0; i < size; i++)
                if (!isprint((int)buf[i]))
                        return 0;

        return 1;
}

KafkaMessageBroker::KafkaMessageBroker(){}
static void dr_msg_cb(rd_kafka_t *rk, const rd_kafka_message_t *rkmessage, void *opaque) {
        if (rkmessage->err)
                log_err("%% Message delivery failed: %s\n",
                        rd_kafka_err2str(rkmessage->err));
        else
                log_err("%% Message delivered (%zd bytes, "
                        "partition %" PRId32 ")\n",
                        rkmessage->len, rkmessage->partition);

        /* The rkmessage is destroyed automatically by librdkafka */
}
void KafkaMessageBroker::send(std::string producer_id,std::string message_type,std::string method,std::list<std::string> messages)
{
	rd_kafka_t *rk;        /* Producer instance handle */
        rd_kafka_conf_t *conf; /* Temporary configuration object */
        char errstr[512];      /* librdkafka API error reporting buffer */
        const char *brokers;   /* Argument: broker list */
        const char *topic;     /* Argument: topic to produce to */
	std::list<std::string>::iterator s;     //iterator to iterate te list of messages
	int len;
//	RdKafka::ErrorCode err;
	 rd_kafka_resp_err_t err;
	/*
         * Create Kafka client configuration place-holder
         */
	//std::cout<<"producer_id: "<<producer_id<<" " <<"message_type: "<<message_type<<" "<<"method: "<<method;
        conf = rd_kafka_conf_new();
	if (rd_kafka_conf_set(conf, "bootstrap.servers", "192.168.83.120:9092", errstr,
                              sizeof(errstr)) != RD_KAFKA_CONF_OK) {
                log_err("Inside send function%s\n", errstr);
                return;
        }
	
	rd_kafka_conf_set_dr_msg_cb(conf,dr_msg_cb);
	rk = rd_kafka_new(RD_KAFKA_PRODUCER, conf, errstr, sizeof(errstr));
        if (!rk) {
                log_err("%% Failed to create new producer: %s\n",
                        errstr);
                return;
        }

	for(s= messages.begin();s!=messages.end();s++)
	{
	len = (*s).size();
	retry:

		 err = rd_kafka_producev(
                    /* Producer handle */
                    rk,
                    /* Topic name */
                    RD_KAFKA_V_TOPIC(message_type.c_str()),
                    /* Make a copy of the payload. */
                    RD_KAFKA_V_MSGFLAGS(RD_KAFKA_MSG_F_COPY),
                    /* Message value and length */
                    RD_KAFKA_V_VALUE((void*)((*s).c_str()), len),
                    /* Per-Message opaque, provided in
                     * delivery report callback as
                     * msg_opaque. */
                    RD_KAFKA_V_OPAQUE(NULL),
                    /* End sentinel */
                    RD_KAFKA_V_END);
	
		 if (err) {
                        /*
                         * Failed to *enqueue* message for producing.
                         */
                        log_err("%% Failed to produce to topic %s: %s\n", message_type.c_str(),
                                rd_kafka_err2str(err));

                        if (err == RD_KAFKA_RESP_ERR__QUEUE_FULL) {
                                /* If the internal queue is full, wait for
                                 * messages to be delivered and then retry.
                                 * The internal queue represents both
                                 * messages to be sent and messages that have
                                 * been sent or failed, awaiting their
                                 * delivery report callback to be called.
                                 *
                                 * The internal queue is limited by the
                                 * configuration property
                                 * queue.buffering.max.messages */
                                rd_kafka_poll(rk,
                                              1000 /*block for max 1000ms*/);
                                goto retry;
                        }
			} else {
                        log_debug("%% Enqueued message (%zd bytes) "
                                "for topic %s\n",
                                len, message_type.c_str());
                }
	}
	rd_kafka_poll(rk, 0 /*non-blocking*/);
       
	 log_debug("%% Flushing final messages..\n");
        rd_kafka_flush(rk, 10 * 1000 /* wait for max 10 seconds */);

        /* If the output queue is still not empty there is an issue
         * with producing messages to the clusters. */
        if (rd_kafka_outq_len(rk) > 0)
                log_err("%% %d message(s) were not delivered\n",
                        rd_kafka_outq_len(rk));

        /* Destroy the producer instance */
        rd_kafka_destroy(rk);



}

std::list<std::string> KafkaMessageBroker::receive(std::string client_id)
{
	 rd_kafka_t *rk;          /* Consumer instance handle */
        rd_kafka_conf_t *conf;   /* Temporary configuration object */
        rd_kafka_resp_err_t err; /* librdkafka API error code */
        char errstr[512];        /* librdkafka API error reporting buffer */
        const char *brokers;     /* Argument: broker list */
        const char *groupid;     /* Argument: Consumer group id */
        char **topics;           /* Argument: list of topics to subscribe to */
        int topic_cnt;           /* Number of topics to subscribe to */
        rd_kafka_topic_partition_list_t *subscription; /* Subscribed topics */
        int i;
	std::list<std::string> tem;


        groupid   = "";
        //topics    = "";
        topic_cnt = 1;


        /*
         * Create Kafka client configuration place-holder
         */
        conf = rd_kafka_conf_new();

        /* Set bootstrap broker(s) as a comma-separated list of
         * host or host:port (default port 9092).
         * librdkafka will use the bootstrap brokers to acquire the full
         * set of brokers from the cluster. */
        if (rd_kafka_conf_set(conf, "bootstrap.servers", client_id.c_str(), errstr,
                              sizeof(errstr)) != RD_KAFKA_CONF_OK) {
                log_err("%s\n", errstr);
                rd_kafka_conf_destroy(conf);
                return tem;
        }

        /* Set the consumer group id.
         * All consumers sharing the same group id will join the same
         * group, and the subscribed topic' partitions will be assigned
         * according to the partition.assignment.strategy
         * (consumer config property) to the consumers in the group. */
        if (rd_kafka_conf_set(conf, "group.id", groupid, errstr,
                              sizeof(errstr)) != RD_KAFKA_CONF_OK) {
                log_err("%s\n", errstr);
                rd_kafka_conf_destroy(conf);
                return tem;
        }

        /* If there is no previously committed offset for a partition
         * the auto.offset.reset strategy will be used to decide where
         * in the partition to start fetching messages.
         * By setting this to earliest the consumer will read all messages
         * in the partition if there was no previously committed offset. */
        if (rd_kafka_conf_set(conf, "auto.offset.reset", "earliest", errstr,
                              sizeof(errstr)) != RD_KAFKA_CONF_OK) {
                log_err( "%s\n", errstr);
                rd_kafka_conf_destroy(conf);
                return tem;
        }

        /*
         * Create consumer instance.
         *
         * NOTE: rd_kafka_new() takes ownership of the conf object
         *       and the application must not reference it again after
         *       this call.
         */
        rk = rd_kafka_new(RD_KAFKA_CONSUMER, conf, errstr, sizeof(errstr));
        if (!rk) {
                log_err("%% Failed to create new consumer: %s\n",
                        errstr);
                return tem;
        }

        conf = NULL; /* Configuration object is now owned, and freed,
                      * by the rd_kafka_t instance. */


        /* Redirect all messages from per-partition queues to
         * the main queue so that messages can be consumed with one
         * call from all assigned partitions.
         *
         * The alternative is to poll the main queue (for events)
         * and each partition queue separately, which requires setting
         * up a rebalance callback and keeping track of the assignment:
         * but that is more complex and typically not recommended. */
        rd_kafka_poll_set_consumer(rk);


        /* Convert the list of topics to a format suitable for librdkafka */
        subscription = rd_kafka_topic_partition_list_new(topic_cnt);
        for (i = 0; i < topic_cnt; i++)
                rd_kafka_topic_partition_list_add(subscription, topics[i],
                                                  /* the partition is ignored
                                                   * by subscribe() */
                                                  RD_KAFKA_PARTITION_UA);

        /* Subscribe to the list of topics */
        err = rd_kafka_subscribe(rk, subscription);
        if (err) {
                log_err("%% Failed to subscribe to %d topics: %s\n",
                        subscription->cnt, rd_kafka_err2str(err));
                rd_kafka_topic_partition_list_destroy(subscription);
                rd_kafka_destroy(rk);
                return tem;
        }

        log_debug("%% Subscribed to %d topic(s), "
                "waiting for rebalance and messages...\n",
                subscription->cnt);

        rd_kafka_topic_partition_list_destroy(subscription);


        /* Signal handler for clean shutdown */
        signal(SIGINT, stop);

        /* Subscribing to topics will trigger a group rebalance
         * which may take some time to finish, but there is no need
         * for the application to handle this idle period in a special way
         * since a rebalance may happen at any time.
         * Start polling for messages. */

        while (run) {
                rd_kafka_message_t *rkm;

                rkm = rd_kafka_consumer_poll(rk, 100);
                if (!rkm)
                        continue; /* Timeout: no message within 100ms,
                                   *  try again. This short timeout allows
                                   *  checking for `run` at frequent intervals.
                                   */

                /* consumer_poll() will return either a proper message
                 * or a consumer error (rkm->err is set). */
                if (rkm->err) {
                        /* Consumer errors are generally to be considered
                         * informational as the consumer will automatically
                         * try to recover from all types of errors. */
                        log_err("%% Consumer error: %s\n",
                                rd_kafka_message_errstr(rkm));
                        rd_kafka_message_destroy(rkm);
                        continue;
                }

                /* Proper message. */
                log_debug("Message on %s [%" PRId32 "] at offset %" PRId64 ":\n",
                       rd_kafka_topic_name(rkm->rkt), rkm->partition,
                       rkm->offset);

                /* Print the message key. */
                if (rkm->key && is_printable((char *)rkm->key, rkm->key_len))
                        log_debug(" Key: %.*s\n", (int)rkm->key_len,
                               (const char *)rkm->key);
                else if (rkm->key)
                        log_debug(" Key: (%d bytes)\n", (int)rkm->key_len);

                /* Print the message value/payload. */
                if (rkm->payload && is_printable((char *)rkm->payload, rkm->len))
                        log_debug(" Value: %.*s\n", (int)rkm->len,
                               (const char *)rkm->payload);
                else if (rkm->payload)
                        log_debug(" Value: (%d bytes)\n", (int)rkm->len);

                rd_kafka_message_destroy(rkm);
        }


        /* Close the consumer: commit final offsets and leave the group. */
        log_debug("%% Closing consumer\n");
        rd_kafka_consumer_close(rk);


        /* Destroy the consumer */
        rd_kafka_destroy(rk);

        return tem;


}
