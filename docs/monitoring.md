# Monitoring

This document explains how monitoring is implemented in the Secure AWS Cloud Infrastructure Lab using Amazon CloudWatch, EC2 metrics, the CloudWatch Agent, and CloudWatch alarms.

The monitoring design combines AWS-provided infrastructure metrics with metrics collected from inside the EC2 guest operating system.

For the implementation and testing process, see the [Build Journal](build-journal.md).

## Monitoring Architecture

The monitoring setup has two main sources of metrics:

`EC2 → CloudWatch`

and:

`EC2 Guest OS → CloudWatch Agent → CloudWatch`

Together, these provide visibility into both the AWS infrastructure and the operating system running inside the instance.

## EC2 Metrics

EC2 automatically provides several metrics to CloudWatch without requiring an agent inside the instance.

For this project, I examined metrics including:

- `CPUUtilization`
- `NetworkIn`
- `NetworkOut`

These metrics provide visibility into resource activity from the AWS side of the EC2 instance.

I also generated CPU activity on the public EC2 instance and observed the resulting increase in `CPUUtilization`, validating that changes in instance activity were reflected in CloudWatch.

## Guest OS Metrics

The standard EC2 metrics did not provide all of the operating-system-level information I wanted to monitor.

To extend visibility into the guest OS, I installed and configured the CloudWatch Agent on the public EC2 instance.

The instance's IAM role was given permission for the agent to publish monitoring data to CloudWatch.

The resulting path is:

`EC2 Guest OS → CloudWatch Agent → CloudWatch`

Through the agent, I collected the `mem_used_percent` metric to monitor memory utilization from inside the operating system.

This demonstrates the difference between metrics provided by AWS for the EC2 resource and additional metrics collected from within the guest operating system.

## CloudWatch Alarm

I created a CloudWatch alarm using the `mem_used_percent` metric published by the CloudWatch Agent.

The alarm evaluates the metric against a configured threshold:

`Memory metric → Threshold evaluation → Alarm state`

During testing, I intentionally configured a low threshold so the current memory utilization would place the alarm into the `ALARM` state.

I then increased the threshold above the current utilization and observed the alarm transition back to `OK`.

This validated that the alarm was evaluating the custom guest OS metric and changing state according to the configured condition.

The alarm in this version of the project performs detection only. It does not automatically remediate the condition or trigger an operational response.

## Infrastructure vs. Guest OS Visibility

The project demonstrates two different monitoring perspectives:

| Monitoring Source | Example Visibility |
|---|---|
| EC2 metrics | CPU and network activity |
| CloudWatch Agent | Guest OS memory utilization |

This distinction is useful because monitoring an EC2 workload can require information from both outside and inside the operating system.

AWS-provided EC2 metrics give visibility into supported instance-level behavior, while the CloudWatch Agent can publish additional metrics collected from the guest OS.

## Monitoring Role in the Architecture

Monitoring provides operational visibility into the workload rather than controlling access to it.

Other parts of the project handle different security functions:

- [Identity and Access](identity-and-access.md) controls what identities are permitted to do.
- [Auditing](auditing.md) records AWS activity for later investigation.
- CloudWatch provides visibility into workload behavior and configured metric conditions.
- [Threat Detection](threat-detection.md) examines potentially suspicious activity through GuardDuty.

These layers provide different types of information rather than serving the same purpose.

## Design Summary

The final monitoring model combines built-in EC2 metrics with guest OS telemetry:

`EC2 metrics → CloudWatch`

`Guest OS metrics → CloudWatch Agent → CloudWatch`

`CloudWatch metric → Alarm evaluation → ALARM / OK`

This provides visibility into CPU and network activity from EC2 as well as memory utilization collected from inside the guest operating system.

The CloudWatch alarm adds condition-based detection by evaluating the memory metric against a defined threshold, providing a foundation that could later be extended with notifications or automated remediation.
