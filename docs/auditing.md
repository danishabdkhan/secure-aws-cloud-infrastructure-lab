# Auditing

This document explains how auditing is implemented in the Secure AWS Cloud Infrastructure Lab using AWS CloudTrail, S3, and Amazon Athena.

The auditing design records AWS activity, stores trail logs in S3, and makes those records queryable so actions can be investigated and attributed to the identities that performed them.

For the implementation and troubleshooting process, see the [Build Journal](build-journal.md).

## Audit Architecture

The audit path is:

`AWS Activity → CloudTrail → S3 Log Bucket → Athena`

CloudTrail provides the activity records, the S3 log bucket provides centralized storage for the trail logs, and Athena provides a practical way to query those records using SQL.

This allows the environment to move beyond simply generating logs to actually using them for investigation and validation.

## Management and Data Events

An important distinction in the audit design is the difference between management events and data events.

Management events record operations performed on AWS resources, such as creating or deleting a security group.

S3 object-level operations such as `GetObject` and `DeleteObject` are data events. I configured the CloudTrail trail to record S3 data events so these object-level actions could also be audited.

This distinction matters because the CloudTrail Event History view focuses on management events and did not show the S3 object activity I was trying to investigate.

## Querying CloudTrail with Athena

The CloudTrail logs stored in S3 were made queryable through Athena.

Rather than manually inspecting individual log files, I could use SQL queries to locate specific API actions and examine fields such as:

- Event name
- Identity
- Resource activity
- Error code
- Event time

This made the audit trail much more useful for investigating specific activity.

## Validating Least Privilege

I used the audit data to verify the IAM behavior tested from the public EC2 instance.

The relevant results showed:

| Event | Identity | Result |
|---|---|---|
| `GetObject` | EC2 assumed-role identity | Successful |
| `DeleteObject` | Same assumed-role identity | `AccessDenied` |

The successful `GetObject` showed that the EC2 instance was operating through its IAM role and had the permission required to retrieve the S3 object.

The denied `DeleteObject` showed that the same workload identity did not have permission to perform the destructive action.

CloudTrail did not enforce the permission itself. IAM made the authorization decision, while CloudTrail recorded the resulting activity for later investigation.

For the IAM design behind this test, see [Identity and Access](identity-and-access.md).

## Administrator vs. Workload Activity

I also queried the audit trail for a temporary security group that I created and deleted.

Those actions were attributed to my IAM user rather than the EC2 assumed-role identity.

This demonstrated two different identity patterns in the audit records:

`Infrastructure administration → IAM user`

`EC2 S3 activity → Assumed-role identity`

Being able to distinguish these identities is important because an audit trail should answer more than just **what happened**. It should also help determine **who or what performed the action** and whether it succeeded.

## What the Audit Trail Provides

The final auditing setup provides several useful capabilities:

- Records AWS API activity through CloudTrail.
- Includes S3 object-level activity through data event logging.
- Stores trail logs centrally in S3.
- Makes CloudTrail records queryable through Athena.
- Shows successful and denied API requests.
- Distinguishes administrator activity from EC2 assumed-role activity.
- Provides evidence that IAM controls behaved as intended during testing.

## Design Summary

The auditing design connects AWS activity to a searchable record of what occurred:

`Activity → CloudTrail recording → S3 storage → Athena investigation`

This allowed me to verify that the EC2 workload successfully performed its permitted S3 action, that its unauthorized deletion attempt was denied, and that administrator actions could be distinguished from workload activity by identity.

The result is an audit trail that supports both **security validation** and **investigation**, rather than logs being collected without being examined.
