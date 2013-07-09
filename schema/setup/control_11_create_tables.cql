USE @@KEYSPACE@@;

CREATE COLUMNFAMILY groups (
    "groupId" ascii,
    "webhook" text,
    PRIMARY KEY("groupId", "webhook")
    );

CREATE COLUMNFAMILY servers (
    "serverId" ascii,
    "groupId" ascii,
    "state" ascii,
    PRIMARY KEY("serverId", "groupId")
);
