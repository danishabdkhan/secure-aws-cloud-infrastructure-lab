# Threat Detection

This document explains how threat detection is incorporated into the Secure AWS Cloud Infrastructure Lab using Amazon GuardDuty.

GuardDuty adds a threat-detection layer by analyzing AWS data sources and identifying activity that may indicate compromised credentials, suspicious network behavior, unauthorized access, or other security threats.

For the implementation process, see the [Build Journal](https://github.com/danishabdkhan/secure-aws-cloud-infrastructure-lab/blob/main/docs/build-journal.md). The detailed investigation notes for the GuardDuty sample findings are documented below.

## GuardDuty

I enabled GuardDuty and generated AWS-provided sample findings to practice investigating security detections.

The findings used in this project are simulated examples provided by GuardDuty. They do not represent real attacks against the lab environment.

I used the following investigation process:

`Severity → Finding Type → Affected Resource → Evidence → Analysis → Proposed Response`

Rather than treating the findings only as alerts, I examined what activity caused each detection, what the behavior could indicate in a real environment, and how I would respond.

## Finding 1: S3 and IAM Attack Sequence

**Severity:** Critical  
**Finding Type:** AttackSequence  
**Affected Resources:** S3 buckets

The sample finding represented a sequence of suspicious actions associated with a compromised IAM identity.

The activity included discovery of S3 resources followed by actions involving CloudTrail, IAM permissions, S3 public-access configuration, and object deletion.

Taken together, the sequence represented a scenario in which compromised credentials could be used to discover resources, reduce visibility, establish additional access, and affect stored data.

### Proposed Response

For a real finding with similar evidence, my response would include:

- Revoke or rotate the compromised credentials.
- Restore any logging that had been disabled.
- Review and remove unauthorized IAM or S3 policy changes.
- Isolate and investigate the affected S3 resources.
- Check for evidence of data access or exfiltration.
- Recover deleted objects through available versioning or backups.

## Finding 2: Unusual EC2 Network Activity

**Severity:** Medium  
**Finding Type:** Behavior  
**Affected Resource:** EC2 instance

This sample finding represented an unusually large amount of outbound network traffic from an EC2 instance.

The behavior was significant because a large and unexpected outbound transfer can indicate activity such as data exfiltration or a compromised workload communicating with an external system.

### Proposed Response

For a real finding with similar evidence, I would:

- Restrict suspicious outbound communication.
- Inspect running processes and active network connections on the instance.
- Review authentication and system logs for unauthorized access.
- Rotate potentially exposed credentials.
- Correlate the activity with network telemetry to determine the source and volume of the traffic.

The investigation would focus on determining whether the network activity was expected workload behavior or evidence that the instance had been compromised.

## Finding 3: Unusual RDS Login

**Severity:** High  
**Finding Type:** CredentialAccess  
**Affected Resource:** RDS database

This sample finding represented a successful database login that differed from the expected historical behavior.

The unusual connection characteristics could indicate that valid database credentials were being used from an unexpected source or application.

### Proposed Response

For a real finding with similar evidence, I would:

- Rotate or revoke the affected database credentials.
- Restrict unauthorized network access to the database.
- Review database logs around the time of the login.
- Investigate queries and other activity performed during the session.
- Check for unauthorized data access or modification.

The goal would be to contain the access first and then determine what occurred while the credentials were being used.

## Role of GuardDuty

GuardDuty serves a different purpose from the other security controls in the project.

| Control | Purpose |
|---|---|
| IAM | Controls what an identity is authorized to do |
| CloudTrail | Records AWS activity |
| CloudWatch | Monitors metrics and configured conditions |
| GuardDuty | Detects potentially suspicious activity |

These services complement one another.

For example, IAM can restrict permissions, CloudTrail can provide an audit record of API activity, CloudWatch can identify metric conditions, and GuardDuty can surface behavior that may require security investigation.

## Detection vs. Response

GuardDuty provides findings that help identify potentially suspicious behavior, but a finding still requires investigation and response.

My approach was therefore not simply:

`Finding → Threat`

Instead, I treated the process as:

`Finding → Evidence → Context → Analysis → Response`

This distinction is important because a detection is an indication that should be investigated rather than automatic proof that a resource has been compromised.

## Design Summary

GuardDuty adds the threat-detection component to the lab's security architecture.

Using AWS-provided sample findings allowed me to practice interpreting detections across three different scenarios:

- IAM and S3 attack-sequence activity
- Abnormal EC2 network behavior
- Unusual RDS authentication

The exercises helped connect AWS security findings to an investigation process based on severity, affected resources, supporting evidence, analysis, containment, and follow-up investigation.

Combined with IAM, CloudTrail, Athena, and CloudWatch, GuardDuty provides another layer of visibility for identifying and investigating potentially malicious activity.
