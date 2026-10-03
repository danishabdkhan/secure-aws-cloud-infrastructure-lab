# Identity and Access

This document explains the identity and access design of the original AWS infrastructure. The design separates administrator access from EC2 workload permissions and uses AWS-managed temporary credentials instead of static access keys.

Identity and access for the generative AI / RAG extension, including its dedicated Bedrock and application roles, are documented separately in [Generative AI Extension](generative-ai.md).

For the implementation and testing process, see the [Build Journal](build-journal.md).

## Access Model

The original infrastructure uses two primary types of identity:

| Identity | Purpose |
|---|---|
| Administrator IAM user | Used to configure and manage AWS resources |
| EC2 assumed-role identity | Used by the EC2 workload to access permitted AWS services |

Keeping these identities separate makes it easier to distinguish actions performed by an administrator from actions performed by an EC2 workload.

## EC2 Workload Identity

The public EC2 instance uses an IAM role to access a private S3 bucket.

The role provides temporary AWS credentials to the instance, so I did not need to configure long-term AWS access keys inside the operating system.

The access model is:

`EC2 Instance → IAM Role → IAM Policy → S3`

This allows permissions to be assigned to the EC2 workload itself rather than storing credentials directly on the instance.

## Least-Privilege S3 Access

I created a custom IAM policy for the EC2 role that allowed the access required to retrieve the test object from the private S3 bucket without granting permission to delete it.

The intended authorization behavior was:

| Action | Expected Result |
|---|---|
| Read/retrieve the permitted S3 object | Allowed |
| Delete the S3 object | Denied |

I validated both conditions from the EC2 instance. The object could be downloaded successfully using the assumed-role identity, while the deletion attempt returned `AccessDenied`.

This demonstrated that the workload had the permission it needed without also receiving unnecessary destructive access.

The auditing of these actions through CloudTrail and Athena is covered in [Auditing](auditing.md).

## Administrative Access

Administrative access to the EC2 instances uses EC2 Instance Connect Endpoint.

The final access path is:

`Administrator → EC2 Instance Connect → EIC Endpoint → EC2 Instance`

This provides an administrative path to the instances without requiring the private EC2 instance to have a public IPv4 address.

Security groups control the permitted network path between the EIC Endpoint and the EC2 instances.

Direct SSH and a bastion-host approach were also tested during development, but the EIC Endpoint is the administrative-access method used in the final design.

For the underlying network path and security-group relationships, see [Networking](networking.md).

## Identity Attribution

Separating administrator and workload identities also improves auditability.

Actions performed through my IAM user can be distinguished from actions performed by the EC2 instance through its assumed IAM role.

For example:

`Administrator action → IAM user identity`

`EC2 action → Assumed-role identity`

This distinction became visible when I queried CloudTrail records with Athena. Administrative security-group activity was attributed to my IAM user, while the S3 requests from EC2 were attributed to the assumed-role identity.

This makes it possible to determine not only what action occurred, but also which type of identity performed it.

## Security Principles

The identity and access design applies several security principles:

- **Least privilege:** The EC2 role receives only the permissions required for its task.
- **Temporary credentials:** The EC2 instance uses credentials provided through its IAM role rather than statically configured access keys.
- **Identity separation:** Administrator activity and workload activity use different identities.
- **Private resource access:** The S3 bucket remains private while authorized access is granted through IAM.
- **Controlled administration:** EC2 Instance Connect Endpoint provides the final administrative-access path to the EC2 instances.
- **Auditability:** CloudTrail records can be used to distinguish administrator actions from assumed-role workload actions.

## Design Summary

The original infrastructure's access model separates human administration from workload authorization.

The administrator identity manages the AWS environment, while the EC2 instance assumes an IAM role for its permitted S3 access. The role allows the required read operation while denying the tested delete operation, and no static AWS access keys are required on the instance.

Administrative EC2 access is handled separately through EC2 Instance Connect Endpoint and security-group controls.

Together, these controls provide a clearer separation between **who manages the infrastructure**, **what the workload is allowed to do**, and **how those actions can later be attributed through auditing**.
