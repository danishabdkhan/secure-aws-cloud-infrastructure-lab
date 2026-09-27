# Secure AWS Cloud Infrastructure Lab

A hands-on AWS cloud infrastructure and security lab focused on network segmentation, least-privilege access, secure administration, auditing, monitoring, and threat detection.

I built and tested the environment in AWS to apply cloud and security concepts beyond certification study, troubleshoot real configuration issues, and validate that the implemented controls behaved as intended.

## Architecture

![Secure AWS Cloud Infrastructure Architecture](architecture/architecture-diagram.png)

The environment is built inside a custom VPC in `us-east-1` with separate public and private subnets.

- The **public subnet** contains a public EC2 instance and NAT Gateway.
- The **private subnet** contains a private EC2 instance with no public IPv4 address.
- An **Internet Gateway** provides the public internet path.
- The **NAT Gateway** provides outbound internet connectivity for the private instance.
- **EC2 Instance Connect Endpoint** provides the final administrative-access path.
- **Security groups** restrict traffic between resources.

## Security and Design Decisions

### Network Segmentation

I separated public and private resources using dedicated subnets and route tables.

The private EC2 instance has no public IPv4 address and reaches the internet outbound through the NAT Gateway rather than receiving direct public internet exposure.

### Secure Administrative Access

I used EC2 Instance Connect Endpoint as the final administrative-access method for the EC2 instances.

During development, I also tested direct SSH and a bastion-host approach before moving to the endpoint-based design.

### Least-Privilege Workload Access

The public EC2 instance uses an IAM role with a custom policy to access a private S3 bucket.

I validated the permissions directly from the instance:

`GetObject → Allowed`

`DeleteObject → AccessDenied`

The workload uses temporary role credentials rather than statically configured AWS access keys.

### Auditing

I configured CloudTrail with S3 data event logging and stored the trail logs in S3.

Using Athena, I queried the audit records and verified:

- Successful `GetObject` activity under the EC2 assumed-role identity
- Denied `DeleteObject` activity under the same workload identity
- Security-group administration under my IAM user identity

This provided a practical way to distinguish administrator activity from workload activity.

### Monitoring

I used CloudWatch to monitor EC2 CPU and network metrics and installed the CloudWatch Agent to collect guest OS memory utilization.

I also created a memory alarm and validated its transition between `ALARM` and `OK` as the configured threshold changed.

### Threat Detection

I enabled GuardDuty and investigated AWS-provided sample findings representing:

- An S3/IAM attack sequence
- Unusual EC2 network activity
- Unusual RDS authentication

The findings were simulated rather than real compromises of the environment. I used them to practice moving from detection to evidence review, analysis, and proposed response actions.

## Key Validations

| Control | Validation |
|---|---|
| Private networking | Private EC2 reached the internet outbound through the NAT Gateway without a public IPv4 address |
| Administrative access | Connected to EC2 through EC2 Instance Connect Endpoint |
| Least privilege | `GetObject` succeeded while `DeleteObject` returned `AccessDenied` |
| Identity attribution | CloudTrail distinguished IAM-user activity from EC2 assumed-role activity |
| Audit investigation | Queried CloudTrail records using Athena |
| Infrastructure monitoring | Observed EC2 CPU and network metrics in CloudWatch |
| Guest OS monitoring | Published memory utilization through the CloudWatch Agent |
| Alerting | Validated CloudWatch alarm state changes |
| Threat detection | Investigated three GuardDuty sample-finding scenarios |

## AWS Services Used

`VPC` • `EC2` • `IAM` • `S3` • `CloudTrail` • `Athena` • `CloudWatch` • `GuardDuty`

Supporting networking components include Internet Gateway, NAT Gateway, route tables, security groups, and EC2 Instance Connect Endpoint.

## Technical Documentation

More detailed documentation is available in [`docs/`](docs/):

- [Build Journal](docs/build-journal.md) — chronological implementation, troubleshooting, testing, and lessons learned
- [Networking](docs/networking.md) — final network architecture, routing, and administrative-access design
- [Identity and Access](docs/identity-and-access.md) — IAM roles, least privilege, workload identity, and access model
- [Auditing](docs/auditing.md) — CloudTrail, S3 data events, Athena queries, and identity attribution
- [Monitoring](docs/monitoring.md) — EC2 metrics, CloudWatch Agent, and alarms
- [Threat Detection](docs/threat-detection.md) — GuardDuty design and detailed sample-finding investigations

Supporting validation evidence is organized by topic in [`screenshots/`](screenshots/).

## Skills Demonstrated

- AWS network architecture and VPC segmentation
- Public and private subnet routing
- Security groups and controlled administrative access
- IAM roles and least-privilege policy design
- Temporary AWS credentials for EC2 workloads
- CloudTrail auditing and S3 data event logging
- SQL-based CloudTrail investigation with Athena
- CloudWatch infrastructure and guest OS monitoring
- CloudWatch Agent configuration and alarms
- GuardDuty finding analysis and incident-response reasoning
- Linux networking and AWS troubleshooting
- Technical documentation and architecture communication

## What I Learned

Building the environment helped me understand how AWS networking, identity, auditing, monitoring, and threat detection work together rather than viewing each service independently.

The most valuable part of the project was troubleshooting configurations and then validating the corrected behavior. Testing routing, IAM authorization, audit records, monitoring data, and security findings gave me a clearer understanding of both how the individual controls work and how they contribute to a broader cloud security architecture.

For the full implementation process and troubleshooting history, see the [Build Journal](docs/build-journal.md).

## In Progress: Generative AI Extension

I am extending this project with Amazon Bedrock to explore generative AI and retrieval-augmented generation (RAG) in an AWS environment. The planned extension will use project documentation and security validation evidence as a knowledge source for an assistant that can answer questions about the architecture, implemented security controls, and observed results.

Planned work includes:

- Integrating Amazon Bedrock with project data stored in Amazon S3
- Building a knowledge base for retrieval-augmented generation
- Testing retrieval and generated responses against project documentation
- Applying least-privilege IAM permissions to the AI components
- Documenting the architecture, implementation, and validation results
