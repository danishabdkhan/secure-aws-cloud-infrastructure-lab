# Secure AWS Cloud Infrastructure Lab

A hands-on AWS cloud infrastructure, security, and generative AI project focused on network segmentation, least-privilege access, secure administration, auditing, monitoring, threat detection, and retrieval-augmented generation (RAG).

I built and tested the environment in AWS to apply cloud and security concepts beyond certification study, troubleshoot real configuration issues, and validate that the implemented controls behaved as intended. I later extended the environment with Amazon Bedrock to build a RAG assistant that answers questions about the project's architecture, security controls, validation evidence, and troubleshooting history using the project's own documentation.

## Architecture

![Secure AWS Cloud Infrastructure Architecture](architecture/extended-architecture-diagram.png)

The current architecture combines the original secure AWS infrastructure with a generative AI / RAG extension built using Amazon Bedrock.

The infrastructure is deployed in `us-east-1` and uses a custom VPC with separate public and private subnets.

- The **public subnet** contains a public EC2 instance and NAT Gateway.
- The **private subnet** contains a private EC2 instance with no public IPv4 address.
- An **Internet Gateway** provides the public internet path.
- The **NAT Gateway** provides outbound internet connectivity for the private instance.
- **EC2 Instance Connect Endpoint** provides the final administrative-access path.
- **Security groups** restrict traffic between resources.

The RAG extension uses project documentation stored in S3 as a knowledge source for a Bedrock Knowledge Base. A Python/Boto3 client allows a user to ask questions about the project outside the AWS console. Bedrock retrieves relevant information from the project documentation, provides that context to a foundation model, and returns a grounded answer with the source documents used.

The original infrastructure architecture before the generative AI extension is preserved in [`architecture/v1-architecture-diagram.png`](architecture/v1-architecture-diagram.png).

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
| RAG retrieval and generation | Retrieved relevant project documentation and generated grounded answers with source attribution |
| Cross-document reasoning | Answered questions requiring information from multiple project documents |
| Unsupported-information handling | Correctly recognized that no AWS Lambda functions were deployed rather than making up an answer |

## AWS Services Used

`VPC` • `EC2` • `IAM` • `S3` • `CloudTrail` • `Athena` • `CloudWatch` • `GuardDuty` • `Bedrock`

Supporting networking components include Internet Gateway, NAT Gateway, route tables, security groups, and EC2 Instance Connect Endpoint.

## Technical Documentation

More detailed documentation is available in [`docs/`](docs/):

- [Build Journal](docs/build-journal.md) — chronological implementation, troubleshooting, testing, and lessons learned
- [Networking](docs/networking.md) — final network architecture, routing, and administrative-access design
- [Identity and Access](docs/identity-and-access.md) — IAM roles, least privilege, workload identity, and access model
- [Auditing](docs/auditing.md) — CloudTrail, S3 data events, Athena queries, and identity attribution
- [Monitoring](docs/monitoring.md) — EC2 metrics, CloudWatch Agent, and alarms
- [Threat Detection](docs/threat-detection.md) — GuardDuty design and detailed sample-finding investigations
- [Generative AI Extension](docs/generative-ai.md) — Bedrock Knowledge Base, RAG workflow, Python/Boto3 client, least-privilege IAM, evaluation, and limitations

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
- Retrieval-augmented generation (RAG) with Amazon Bedrock
- Semantic retrieval and grounded response generation
- Python/Boto3 integration with AWS services
- Least-privilege IAM for an application client using temporary credentials
- RAG evaluation and unsupported-premise testing

## What I Learned

Building the original environment helped me understand how AWS networking, identity, auditing, monitoring, and threat detection work together rather than viewing each service independently.

The most valuable part of the infrastructure work was troubleshooting configurations and then validating the corrected behavior. Testing routing, IAM authorization, audit records, monitoring data, and security findings gave me a clearer understanding of both how the individual controls work and how they contribute to a broader cloud security architecture.

Extending the project with RAG also gave me hands-on experience connecting generative AI to project-specific information. I learned how documentation can be ingested, converted into embeddings, retrieved based on a user's question, and supplied as context to a foundation model. Building the Python/Boto3 client also helped me understand how an application can interact programmatically with managed AWS AI services while still using least-privilege IAM and temporary credentials.

For the full implementation process and troubleshooting history, see the [Build Journal](docs/build-journal.md).

## Generative AI Extension

I extended the project with Amazon Bedrock to build a retrieval-augmented generation (RAG) assistant that can answer questions about the project based on its own technical documentation.

A foundation model on its own has no knowledge of how this specific project was designed, secured, tested, or troubleshot. The RAG system addresses this by retrieving relevant information from the project's documentation and providing that context to a foundation model before an answer is generated.

Six project documents covering networking, identity and access, auditing, monitoring, threat detection, and the full build process are stored under a dedicated S3 prefix and ingested into a Bedrock Knowledge Base. The documents are parsed, chunked, converted into embeddings, and indexed in a managed vector store for semantic retrieval.

I also built a Python/Boto3 command-line client in [`src/query_knowledge_base.py`](src/query_knowledge_base.py) to use the RAG system outside of the AWS console. A user can enter a question about the project through the client, which sends the query to Bedrock. Bedrock retrieves relevant information from the project documentation, provides that context to a foundation model, and returns a grounded answer along with the source documents used.

The client uses the standard AWS credential provider chain rather than storing credentials in the source code.

### Security

I reviewed the IAM permissions automatically created for the Bedrock Knowledge Base and narrowed its S3 object access from the entire bucket to only the `project-docs/` corpus prefix.

For the Python client, I created a dedicated IAM role with only the permissions required to query the Bedrock Knowledge Base and invoke the managed response-generation workflow. I tested the client using temporary credentials from the assumed role rather than relying on my broader administrative identity or long-lived application credentials.

### Evaluation

I tested the RAG system against several types of questions:

- **Specific retrieval and synthesis:** explained how the EC2 workload's S3 read access and denied delete operation were validated
- **Cross-document synthesis:** combined information from multiple project documents to explain how security controls worked together
- **Troubleshooting retrieval:** recovered project-specific networking problems and their resolutions from the build history
- **Unsupported information:** correctly recognized that no AWS Lambda functions were deployed rather than making up an answer

The tests demonstrated useful semantic retrieval, cross-document synthesis, source attribution, and the ability to recognize information that was not supported by the project documentation. Generated responses still require technical review because retrieval quality and foundation-model output are not guaranteed to be correct.

For the implementation, IAM design, evaluation results, and limitations, see [Generative AI Extension](docs/generative-ai.md).

Curated implementation and validation evidence is available in [`screenshots/bedrock/`](screenshots/bedrock/).
