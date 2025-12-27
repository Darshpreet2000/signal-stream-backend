CREATE STREAM IF NOT EXISTS SUMMARY_STREAM (
    conversation_id VARCHAR KEY,
    tenant_id VARCHAR,
    tldr VARCHAR,
    customer_issue VARCHAR,
    agent_response VARCHAR,
    key_points ARRAY<VARCHAR>,
    next_steps ARRAY<VARCHAR>
) WITH (
    KAFKA_TOPIC='support.ai.summary',
    VALUE_FORMAT='JSON'
);

CREATE TABLE IF NOT EXISTS SUMMARY_TABLE AS
    SELECT
        conversation_id,
        LATEST_BY_OFFSET(tenant_id) AS tenant_id,
        LATEST_BY_OFFSET(tldr) AS tldr,
        LATEST_BY_OFFSET(customer_issue) AS customer_issue,
        LATEST_BY_OFFSET(agent_response) AS agent_response,
        LATEST_BY_OFFSET(key_points) AS key_points,
        LATEST_BY_OFFSET(next_steps) AS next_steps
    FROM SUMMARY_STREAM
    GROUP BY conversation_id;
