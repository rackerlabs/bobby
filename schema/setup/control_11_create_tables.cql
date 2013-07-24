USE @@KEYSPACE@@;

CREATE COLUMNFAMILY groups (
    "groupId" ascii, /* Provided by otter */
    "tenantId" ascii,
    "notification" ascii,
    "notificationPlan" ascii,
    PRIMARY KEY("tenantId", "groupId")
    );

CREATE COLUMNFAMILY servers (
    "tenantId" ascii,
    "serverId" ascii, /* Provided by nova */
    "groupId" ascii,
    "entityId" ascii, /* Provided by MaaS */
    PRIMARY KEY("tenantId", "serverId")
);

CREATE INDEX servers_by_groupId ON servers ("groupId");

CREATE COLUMNFAMILY policies (
    "groupId" ascii,
    "policyId" ascii, /* Provided by otter */
    "alarmTemplate" ascii, /* Provided by otter */
    "checkTemplate" ascii, /* Provided by otter */
    PRIMARY KEY ("groupId", "policyId")
);

CREATE COLUMNFAMILY serverpolicies (
    "serverId" ascii,
    "policyId" ascii,
    "alarmId" ascii,
    "checkId" ascii,
    "state" ascii,
    PRIMARY KEY("policyId", "serverId")
);
