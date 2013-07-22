USE @@KEYSPACE@@;

CREATE COLUMNFAMILY groups (
    "groupId" ascii, /* Provided by otter */
    "tenantId" ascii,
    "notification" ascii,
    "notificationPlan" ascii,
    PRIMARY KEY("groupId", "tenantId")
    );

CREATE COLUMNFAMILY servers (
    "serverId" ascii, /* Provided by nova */
    "groupId" ascii,
    "entityId" ascii, /* Provided by MaaS */
    PRIMARY KEY("serverId", "groupId")
);

CREATE COLUMNFAMILY policies (
    "groupId" ascii,
    "policyId" ascii, /* Provided by otter */
    "alarmTemplate" ascii, /* Provided by otter */
    "checkTemplate" ascii, /* Provided by otter */
    PRIMARY KEY ("policyId", "groupId")
);

CREATE COLUMNFAMILY serverpolicies (
    "serverId" ascii,
    "policyId" ascii,
    "alarmId" ascii,
    "checkId" ascii,
    "state" ascii,
    PRIMARY KEY("serverId", "policyId")
);
