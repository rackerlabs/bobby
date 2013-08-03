USE @@KEYSPACE@@;

CREATE COLUMNFAMILY groups (
    "tenantId" ascii,
    "groupId" ascii, /* Provided by otter */
    "notification" ascii,
    "notificationPlan" ascii,
    PRIMARY KEY("tenantId", "groupId")
    );

CREATE COLUMNFAMILY servers (
    "groupId" ascii,
    "serverId" ascii, /* Provided by nova */
    "entityId" ascii, /* Provided by MaaS */
    PRIMARY KEY("groupId", "serverId")
);

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

CREATE INDEX serverpolicies_by_alarmId ON serverpolicies ("alarmId");
