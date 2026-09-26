# Build Journal

This journal documents how I built, tested, troubleshot, and refined the Secure AWS Cloud Infrastructure Lab. It covers the implementation process, problems I encountered, how I resolved them, and what I learned along the way.

The final environment is documented in the main project README. This journal focuses on the implementation process and the reasoning behind the changes I made along the way.

---

## 1. Project Setup and Network Foundation

### Choosing the AWS Region and VPC Address Space

I initially created the VPC in `us-east-2` instead of my intended region, `us-east-1`. I deleted it and recreated the environment in the correct region.

My first subnet attempt exposed a more important issue: I did not yet fully understand how the subnet CIDR had to fit inside the VPC CIDR. After receiving an error, I rebuilt the VPC using `10.0.0.0/16`, which gave me an address space from which I could create smaller `/24` subnets.

![VPC subnet CIDR error](../screenshots/networking/vpc-subnetting/vpc-subnet-cidr-error.png)

![Corrected VPC CIDR](../screenshots/networking/vpc-subnetting/vpc-cidr-corrected.png)

### Creating the Subnets

When I began creating the subnets, I initially selected address ranges that overlapped an existing subnet. AWS rejected the configuration.

This helped make the relationship between the VPC address space and its subnet ranges much more concrete: each subnet had to fall inside the VPC CIDR while also occupying a unique, non-overlapping range.

During the initial build, I created one public subnet and two private subnets while working through the network configuration. As the architecture developed, I only needed one of the private subnets for the final lab environment, so the final design uses one public subnet and one private subnet.

![Subnet CIDR overlap error](../screenshots/networking/vpc-subnetting/subnet-cidr-overlap-error.png)

![VPC subnets created](../screenshots/networking/vpc-subnetting/vpc-subnets-created.png)

### Establishing Route Tables and Internet Connectivity

I noticed that AWS had already created a route table with the VPC. I initially treated that table as my public route table and then created a separate private route table.

While reviewing the subnet associations, I realized that the private subnets were not associated with the private route table as intended. I corrected the associations so that the public and private routing paths could be managed separately.

![Initial route table subnet associations](../screenshots/networking/routing/initial-route-table-subnet-associations.png)

![Private route table configuration](../screenshots/networking/routing/private-route-table-configuration.png)

I then created and attached an Internet Gateway to the VPC and configured the public routing path with a default route (`0.0.0.0/0`) targeting the Internet Gateway.

![Internet Gateway created](../screenshots/networking/routing/internet-gateway-created.png)

![Public default route configuration](../screenshots/networking/routing/public-default-route-configuration.png)

![Public route table Internet Gateway route](../screenshots/networking/routing/public-route-table-internet-gateway-route.png)

This part of the build helped me understand that creating subnets alone does not determine whether they are public or private. Their routing configuration, public addressing, and related network controls determine how resources can communicate.

---

## 2. Deploying and Validating the Public EC2 Instance

### Launching the Public Instance

I launched the first EC2 instance into the public subnet using Amazon Linux. I enabled a public IPv4 address and initially restricted SSH access in its security group to my current public IP.

![Public EC2 launch configuration](../screenshots/networking/connectivity/public-ec2-launch-configuration.png)

![Public EC2 launch success](../screenshots/networking/connectivity/public-ec2-launch-success.png)

### Troubleshooting EC2 Instance Connect

My first attempt to connect through browser-based EC2 Instance Connect failed. The connection assistance indicated that the security group was blocking the required connection path.

![EC2 Instance Connect failure](../screenshots/administrative-access/public-ec2-instance-connect-failure.png)

As a temporary troubleshooting test, I broadened the SSH rule and retried the connection. The connection succeeded, confirming that the security-group configuration was the cause rather than a general instance or Internet-connectivity failure.

![EC2 Instance Connect success](../screenshots/administrative-access/public-ec2-instance-connect-success.png)

I did not leave SSH broadly exposed. The temporary rule was used to isolate the cause of the failure and was removed afterward.

### Restricting SSH and Handling a Changing Client IP

After restoring the restricted SSH rule, I tested direct SSH from my Mac. The connection still failed because my public Wi-Fi IP had changed since I originally configured the security group.

![SSH failure after client IP change](../screenshots/administrative-access/public-ec2-ssh-after-ip-change-failure.png)

I updated the inbound rule to my current public IP and successfully connected directly from the Mac terminal.

![Direct SSH success](../screenshots/administrative-access/public-ec2-direct-ssh-success.png)

This exposed an operational limitation of relying on a changing client public IP for administrative access: the allowlist may need to be updated whenever the client network changes.

### Validating Networking from Linux

Once connected, I validated the instance's networking from inside the guest operating system rather than relying only on the AWS console.

I used `ip addr` and `ip route` to inspect the instance's private interface addressing and default route.

![Network interface and route validation](../screenshots/networking/connectivity/public-ec2-network-interface-and-route-validation.png)

I also tested DNS resolution with `nslookup`, confirming that the instance could resolve external domain names.

![DNS connectivity validation](../screenshots/networking/connectivity/public-ec2-dns-connectivity-validation.png)

One important distinction I learned here is that the public IPv4 address associated with an EC2 instance is not configured as an address directly on the instance's network interface. Inside the guest OS, the instance sees its private address, while AWS networking provides the public IPv4 mapping used for Internet communication.

---

## 3. Building the Private Network Path

### Creating the Private Workload

I created another private route table while developing the private side of the network and launched a second EC2 instance into the private subnet with public IPv4 assignment disabled.

![Private EC2 instance details](../screenshots/networking/connectivity/private-ec2-instance-details.png)

This instance became the workload I used to test private-subnet routing and controlled administrative access.

### Configuring Private Routing and NAT

I created a NAT Gateway to provide outbound Internet access for the private subnet without assigning the private EC2 instance a public IPv4 address.

During this process, I also noticed an additional route table that I could not initially account for. I reviewed the VPC's route tables, main route table, and subnet associations and cleaned up the associations so the intended public and private routing paths were clearer. However, the additional route table remained, and at the time I was not sure why it was there.

![VPC resource map during NAT configuration](../screenshots/networking/routing/vpc-resource-map-nat-configuration.png)

![Corrected route table associations](../screenshots/networking/routing/route-table-associations-corrected.png)

### Configuring Security-Group-Based Access

Before connecting to the private instance, I reviewed its security group and noticed that its SSH rule still referenced one of my previous client public IP addresses.

That did not match the bastion-style path I was about to test. The private instance needed to accept the connection originating through the public EC2 instance rather than directly trusting my old client network.

![Incorrect private EC2 SSH source](../screenshots/networking/connectivity/private-ec2-incorrect-ssh-source-rule.png)

I corrected the rule to reference the public instance's security group.

![Corrected security group reference](../screenshots/networking/connectivity/private-ec2-security-group-reference-corrected.png)

This was an important practical lesson in using security-group relationships between AWS workloads instead of tying internal communication to an unrelated external IP address.

### Testing Bastion-Style Administrative Access

I first tested a bastion-style approach by connecting to the public EC2 instance and then using it as the path into the private EC2 instance.

The SSH connection to the private workload succeeded.

![Bastion to private EC2 SSH success](../screenshots/networking/connectivity/bastion-to-private-ec2-ssh-success.png)

This proved the network and security-group path between the instances, but the test also showed why maintaining a bastion introduces additional credential-management and host-management considerations.

### Diagnosing and Correcting Private Internet Access

While connected to the private EC2 instance, I ran:

`curl -I https://amazon.com`

The request timed out.

![Private EC2 outbound connectivity failure](../screenshots/networking/connectivity/private-ec2-outbound-connectivity-failure.png)

I traced the problem back through the private routing and NAT configuration. The private route was not configured with the correct default destination, and my original NAT Gateway configuration was not attached to the intended public subnet.

I corrected the default route, recreated the NAT Gateway in the public subnet, and updated the private route tables to use the corrected NAT Gateway.

After making these corrections, I also noticed that the additional route table I had encountered earlier was no longer present. I had not intentionally deleted it, so I could not conclusively determine why it disappeared. Rather than assuming a cause, I focused on verifying that the final route table associations and routing configuration matched the intended architecture.

![VPC routing after NAT correction](../screenshots/networking/routing/vpc-routing-after-nat-correction.png)

I then repeated the same outbound request from the private instance.

This time it succeeded.

![Private EC2 outbound connectivity success](../screenshots/networking/connectivity/private-ec2-outbound-connectivity-success.png)

The failure-and-retest sequence was one of the most useful networking exercises in the project because it forced me to trace the entire outbound path rather than assuming the architecture was correct because the resources existed.

---

## 4. Moving to EC2 Instance Connect Endpoint

### Evaluating a Managed Administrative Path

After proving that bastion-style access worked, I explored EC2 Instance Connect Endpoint as another way to reach instances without depending on a publicly reachable bastion workflow.

The goal was to simplify administrative access to the private workload while keeping it without a public IPv4 address.

### Troubleshooting Private EC2 Access

I created an EC2 Instance Connect Endpoint and attempted to connect to the private instance.

![EIC Endpoint created](../screenshots/administrative-access/eic-endpoint-created.png)

The initial connection failed.

![Private EC2 EIC connection failure](../screenshots/administrative-access/private-ec2-eic-connection-failure.png)

I reviewed the security-group path and updated the private instance's inbound rule so that it accepted the required traffic from the security group associated with the endpoint.

I then configured the connection through the endpoint:

![EIC Endpoint connection configuration](../screenshots/administrative-access/eic-endpoint-connection-config.png)

The next connection succeeded.

![Private EC2 EIC access success](../screenshots/administrative-access/private-ec2-eic-access-success.png)

This gave me a cleaner administrative path to the private instance without assigning it a public IPv4 address.

### Extending EIC Access to the Public Instance

I also tested whether I could use the existing endpoint to administer the public EC2 instance. After updating its security-group configuration appropriately, I successfully connected to it through EIC as well.

![Public EC2 EIC access success](../screenshots/administrative-access/public-ec2-eic-access-success.png)

At this point, I no longer needed to repeatedly update an allowlist whenever my client public IP changed for these EIC-based connections.

---

## 5. Implementing Least-Privilege Workload Access

### EC2-to-S3 Access with an IAM Role

I created a private S3 bucket and uploaded a test object. I then created a custom IAM policy designed to let the EC2 workload retrieve the object without permitting deletion.

![IAM S3 least-privilege policy](../screenshots/iam-s3/iam-s3-least-privilege-policy.png)

I attached the policy to an IAM role and assigned that role to the **public EC2 instance**.

![IAM role attached to public EC2](../screenshots/iam-s3/public-ec2-iam-role-attached.png)

From the instance, I successfully downloaded the object without configuring static AWS access keys. I then attempted to delete the object and received `AccessDenied`.

![IAM S3 least-privilege validation](../screenshots/iam-s3/iam-s3-least-privilege-validation.png)

This validated both sides of the policy boundary:

- the workload could perform the action it required;
- a destructive action outside that permission set was denied.

It also gave me hands-on experience using temporary role credentials for an EC2 workload instead of placing long-lived IAM-user credentials on the instance.

---

## 6. Building the Audit Trail

### Configuring CloudTrail

I created a CloudTrail trail to record API activity for the project.

![CloudTrail trail configuration](../screenshots/cloudtrail-athena/cloudtrail-trail-configuration.png)

To generate activity worth auditing, I created and deleted a temporary security group and repeated the S3 authorization test from the public EC2 instance.

When I searched CloudTrail Event History for the S3 object operations, I initially found nothing.

![CloudTrail Event History](../screenshots/cloudtrail-athena/cloudtrail-event-history-no-s3-data-events.png)

This led me to distinguish between the management events shown in Event History and the S3 object-level data events I was trying to inspect through the trail's delivered logs.

### Investigating the Delivered Logs

I initially tried to inspect the CloudTrail log objects directly in S3. The large number of JSON log files made it difficult to locate the specific `GetObject` and `DeleteObject` events from my test.

I also experimented with querying an individual object using S3 Select, but that approach produced an error and still would have required working through individual log files.

![S3 Select query error](../screenshots/cloudtrail-athena/cloudtrail-s3-select-query-error.png)

The failed approach helped clarify why a query layer over the logs would be more useful than manually opening raw log objects.

### Exploring Athena

I went directly to Athena and configured an S3 query-results location. I began exploring manual table creation from the CloudTrail data, but the setup was more cumbersome than necessary for this use case.

I returned to CloudTrail to look for a more direct integration.

### Exploring CloudTrail Lake

I also tried creating a CloudTrail Lake event data store. That attempt returned an error in the console, so I did not use CloudTrail Lake for the final validation workflow.

![CloudTrail Lake event data store error](../screenshots/cloudtrail-athena/cloudtrail-lake-event-data-store-error.png)

Since I could not proceed with CloudTrail Lake, I returned to CloudTrail and Athena and continued looking for a practical way to query the trail logs.

### Validating Authorization with CloudTrail and Athena

I eventually located CloudTrail's option to create an Athena table from the trail logs.

![Create Athena table from CloudTrail](../screenshots/cloudtrail-athena/cloudtrail-create-athena-table.png)

With the table available in Athena, I wrote a SQL query to locate the `GetObject` and `DeleteObject` events from my IAM test.

![Athena CloudTrail S3 audit query](../screenshots/cloudtrail-athena/athena-cloudtrail-s3-audit-query.png)

The results showed the successful `GetObject` under the EC2 assumed-role identity and the denied `DeleteObject` under the same workload identity.

![CloudTrail Athena S3 audit validation](../screenshots/cloudtrail-athena/cloudtrail-athena-s3-audit-validation.png)

This gave me two independent views of the same security control:

1. the EC2 terminal showed that retrieval succeeded and deletion was denied;
2. CloudTrail recorded those API actions and Athena allowed me to query the resulting audit evidence.

### Distinguishing Administrator and Workload Activity

I modified the Athena query to inspect the temporary security-group activity I had generated earlier.

The results showed the successful `CreateSecurityGroup` and `DeleteSecurityGroup` actions under my IAM-user identity.

![Security group audit validation](../screenshots/cloudtrail-athena/cloudtrail-athena-security-group-audit-validation.png)

Comparing these records with the S3 events helped me distinguish **administrator activity performed with my IAM user** from **workload activity performed through an EC2 assumed role**.

---

## 7. Monitoring the Workload

### Validating Native EC2 Metrics

I moved to CloudWatch and examined metrics for the public EC2 instance, including `CPUUtilization`, `NetworkIn`, and `NetworkOut`.

To create a visible CPU event, I connected to the instance and ran:

`timeout 60 md5sum /dev/zero`

![EC2 CPU load test](../screenshots/cloudwatch/ec2-cpu-load-test.png)

When I first refreshed CloudWatch, the expected change was not immediately obvious. After allowing additional time for the EC2 basic-monitoring metric to be published, the graph showed the CPU utilization increase and subsequent return toward baseline.

![CloudWatch CPU utilization spike](../screenshots/cloudwatch/cloudwatch-ec2-cpu-utilization-spike-validation.png)

This taught me not to interpret a monitoring graph as instantaneous. The publication interval of the metric has to be considered when validating a short-lived event.

### Adding Guest OS Metrics with the CloudWatch Agent

The standard EC2 metrics did not provide the guest-level memory metric I wanted to monitor, so I installed the CloudWatch Agent on the public instance.

I added the required CloudWatch Agent permissions to the instance role, installed the agent package, and worked through its configuration.

![CloudWatch Agent installation](../screenshots/cloudwatch/cloudwatch-agent-installation.png)

Once the agent was running, CloudWatch began receiving guest OS telemetry including `mem_used_percent`.

![CloudWatch Agent memory metric](../screenshots/cloudwatch/cloudwatch-agent-memory-metric.png)

This made the distinction between AWS-provided EC2 metrics and additional guest OS telemetry much clearer.

### Creating and Testing a Memory Alarm

I created a CloudWatch alarm against `mem_used_percent`.

For testing, I initially set the threshold to 10%, which was below the instance's normal memory usage.

![CloudWatch memory alarm configuration](../screenshots/cloudwatch/cloudwatch-memory-alarm-configuration.png)

The alarm entered the `ALARM` state as expected.

![CloudWatch memory alarm state](../screenshots/cloudwatch/cloudwatch-memory-alarm-state.png)

I then changed the threshold to 40%, placing the current memory usage below the threshold. After the alarm reevaluated the metric, it transitioned to `OK`.

![CloudWatch memory alarm validation](../screenshots/cloudwatch/cloudwatch-memory-alarm-validation.png)

This was an intentional threshold test rather than an automatic remediation event. A future improvement would be to connect monitoring to notification or remediation mechanisms.

---

## 8. Threat Detection and Investigation

### Enabling GuardDuty and Generating Sample Findings

For the final security component of the lab, I enabled GuardDuty and generated AWS-provided sample findings.

![GuardDuty sample findings](../screenshots/guardduty/guardduty-sample-findings-dashboard.png)

These were **simulated findings, not real compromises of my environment**. I used them to practice a consistent investigation process:

**severity → finding type → affected resources → observed evidence → analysis → potential response**

### Investigating an S3/IAM Attack Sequence

The first sample I investigated was a **Critical** AttackSequence finding involving example S3 resources and an IAM identity.

![Critical GuardDuty finding](../screenshots/guardduty/guardduty-critical-finding-overview.png)

The sample grouped multiple signals into a sequence containing activities such as resource discovery, changes affecting logging or permissions, and object-level activity.

![GuardDuty attack sequence](../screenshots/guardduty/guardduty-critical-finding-attack-sequence.png)

I treated the sequence as a credential-compromise investigation exercise. Potential response actions I considered included revoking exposed credentials, restoring or verifying audit logging, reviewing unauthorized policy changes, isolating affected storage resources, investigating possible exfiltration, and recovering deleted data from available versions or backups.

### Investigating Unusual EC2 Network Activity

The second sample finding involved an EC2 instance generating an unusually large amount of outbound network traffic.

![GuardDuty EC2 network finding](../screenshots/guardduty/guardduty-ec2-network-finding-overview.png)

I reviewed the network/action details associated with the finding.

![GuardDuty EC2 network action details](../screenshots/guardduty/guardduty-ec2-network-finding-action-details.png)

In a real investigation, I would use this type of finding as a starting point for checking processes, sockets, authentication activity, credentials, and network telemetry to determine whether the behavior represented expected workload traffic, data exfiltration, or a compromised host.

### Investigating Unusual RDS Authentication

The third sample was a **High** severity credential-access finding involving an unusual successful RDS login.

![GuardDuty RDS login finding](../screenshots/guardduty/guardduty-rds-login-finding-overview.png)

I reviewed the authentication/network context associated with the finding.

![GuardDuty RDS login action details](../screenshots/guardduty/guardduty-rds-login-finding-action-details.png)

For a real event of this type, I would investigate the affected database identity, rotate or revoke credentials when appropriate, restrict unauthorized access paths, and correlate the finding timestamp with database logs to determine what actions occurred during the session.

Again, these GuardDuty findings were AWS-generated samples used for investigation practice rather than evidence of actual attacks against this lab.

---

## 9. What I Learned

The most valuable part of this project was not getting every configuration right on the first attempt. It was having to determine **why** something failed and then prove that the correction worked.

Some of the most useful troubleshooting sequences were:

- correcting VPC and subnet CIDR mistakes;
- understanding explicit and implicit route-table associations;
- diagnosing EC2 Instance Connect and SSH access failures;
- replacing an incorrect private-instance SSH source with a security-group relationship;
- tracing a private EC2 outbound failure through its route table and NAT path;
- moving from bastion-style access to EC2 Instance Connect Endpoint;
- validating least privilege through both successful and denied API actions;
- moving from difficult raw CloudTrail log inspection to Athena queries;
- distinguishing IAM-user administrator activity from EC2 assumed-role workload activity;
- understanding the difference between native EC2 metrics and guest OS metrics published by the CloudWatch Agent;
- deliberately testing CloudWatch alarm-state behavior; and
- practicing structured investigation with GuardDuty sample findings.

The project also changed how I approach cloud troubleshooting. A resource existing in the console does not prove that the system works. I learned to validate behavior from multiple layers: route tables and security groups in AWS, commands from inside the instances, authorization results from the workload, audit records in CloudTrail, metrics in CloudWatch, and findings in GuardDuty.

The final result is a working lab, but the troubleshooting process is what gave me the strongest understanding of how the individual AWS services interact.
