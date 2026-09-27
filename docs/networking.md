# Networking

This document explains the networking architecture of the Secure AWS Cloud Infrastructure Lab, including the VPC, subnet segmentation, routing, internet connectivity, security groups, and administrative access paths.

The final network separates public-facing infrastructure from the private EC2 instance while still allowing controlled administrative access and outbound internet connectivity where needed.

## Network Architecture

The environment is deployed in `us-east-1` inside a custom VPC using the CIDR block:

`10.0.0.0/16`

The final architecture uses two subnets:

| Subnet | CIDR | Purpose |
|---|---|---|
| Public Subnet | `10.0.0.0/24` | Public EC2 instance and NAT Gateway |
| Private Subnet | `10.0.1.0/24` | Private EC2 instance and EC2 Instance Connect Endpoint |

The public and private subnets use separate routing behavior so that the private EC2 instance does not require a public IPv4 address.

![VPC and subnets](../screenshots/networking/vpc-subnetting/vpc-subnets-created.png)

## VPC and Subnetting

The `/16` VPC provides the overall private address space for the environment, while the `/24` subnets divide that space into smaller network segments.

During the initial build, I encountered two CIDR-related configuration errors. I first attempted to create a subnet outside the VPC's address range, then later attempted to create overlapping subnet ranges. AWS rejected both configurations.

![VPC CIDR corrected](../screenshots/networking/vpc-subnetting/vpc-cidr-corrected.png)

![Subnet CIDR overlap](../screenshots/networking/vpc-subnetting/subnet-cidr-overlap-error.png)

Working through these errors helped reinforce two important subnetting rules:

- A subnet CIDR must fall within the address space of its VPC.
- Subnets within the same VPC cannot use overlapping CIDR ranges.

I initially created two private subnets while working through the network configuration. As the architecture developed, I only needed one private subnet for the final lab environment, so the final design uses one public subnet and one private subnet.

## Public and Private Routing

The public and private subnets use different route-table configurations.

### Public Routing

The public subnet has a default route:

`0.0.0.0/0 → Internet Gateway`

The Internet Gateway is attached to the VPC and provides a path between resources with the appropriate public addressing and the internet.

![Public route table](../screenshots/networking/routing/public-route-table-internet-gateway-route.png)

The public EC2 instance was launched with a public IPv4 address. From inside the instance, `ip addr` showed its private address on the network interface, while `curl ifconfig.me` returned the public address visible to the internet.

![Public EC2 network validation](../screenshots/networking/connectivity/public-ec2-network-interface-and-route-validation.png)

This helped me understand that the public IPv4 address is not configured directly on the instance's network interface inside the guest operating system. The instance operates using its private address, while AWS maps the associated public IPv4 address through the VPC's internet connectivity infrastructure.

I also used `nslookup amazon.com` to verify DNS resolution from the instance.

![Public EC2 DNS validation](../screenshots/networking/connectivity/public-ec2-dns-connectivity-validation.png)

### Private Routing

The private EC2 instance was launched without a public IPv4 address.

![Private EC2 instance](../screenshots/networking/connectivity/private-ec2-instance-details.png)

Its subnet uses a private route table with a default route through the NAT Gateway:

`0.0.0.0/0 → NAT Gateway`

The NAT Gateway is located in the public subnet, where it can reach the Internet Gateway.

The resulting outbound path is:

`Private EC2 → Private Route Table → NAT Gateway → Internet Gateway → Internet`

This allows the private EC2 instance to initiate outbound internet connections without assigning a public IPv4 address directly to the instance.

## Route Table Associations

One of the most useful networking lessons from the project was understanding the difference between main route-table behavior and explicit subnet associations.

During the initial configuration, the public subnet was using the VPC's main route table implicitly. I later explicitly associated the intended public route table with the public subnet and organized the private subnet associations around their intended private route tables.

![Initial route table associations](../screenshots/networking/routing/initial-route-table-subnet-associations.png)

![Corrected route table associations](../screenshots/networking/routing/route-table-associations-corrected.png)

During this process, I also noticed an additional route table that I could not initially account for. I reviewed the VPC's route tables, main route table, and subnet associations, but at the time I was not sure why the additional route table was present.

Later, while troubleshooting the private EC2 instance's outbound connectivity, I corrected the NAT Gateway and private routing configuration. After making those corrections, I noticed that the additional route table was no longer present. I had not intentionally deleted it, so I could not conclusively determine why it disappeared. Rather than assuming a cause, I focused on verifying that the final route table associations and routing configuration matched the intended architecture.

![VPC routing after NAT correction](../screenshots/networking/routing/vpc-routing-after-nat-correction.png)

## NAT Gateway and Private Internet Access

The private instance initially could not reach the internet.

While connected to it, I ran:

```bash
curl -I https://amazon.com
```

The request timed out.

![Private EC2 outbound failure](../screenshots/networking/connectivity/private-ec2-outbound-connectivity-failure.png)

I traced the problem through the NAT Gateway and private routing configuration and found two important issues:

- The private route did not have the correct `0.0.0.0/0` default destination.
- My original NAT Gateway configuration was not attached to the intended public subnet.

I corrected the default route, recreated the NAT Gateway in the public subnet, and updated the private route tables to use the corrected NAT Gateway.

![NAT configuration](../screenshots/networking/routing/vpc-resource-map-nat-configuration.png)

I then reran the same connectivity test from the private EC2 instance.

![Private EC2 outbound success](../screenshots/networking/connectivity/private-ec2-outbound-connectivity-success.png)

The successful response confirmed that the private instance now had outbound internet connectivity through the NAT path while remaining without a public IPv4 address.

## Security Groups

Security groups were used to control which network traffic could reach the EC2 instances.

An important part of the project was learning to reference another security group rather than relying only on individual IP addresses.

While configuring access to the private EC2 instance, I noticed that its inbound SSH rule referenced an old Wi-Fi public IP rather than the public EC2 instance that was supposed to act as the administrative entry point.

![Incorrect private EC2 SSH source](../screenshots/networking/connectivity/private-ec2-incorrect-ssh-source-rule.png)

I corrected the rule to reference the public instance's security group.

![Corrected security group reference](../screenshots/networking/connectivity/private-ec2-security-group-reference-corrected.png)

This allowed the access rule to describe the relationship between the resources instead of depending on a specific client IP address.

I also learned why permanently allowing SSH from `0.0.0.0/0` was not appropriate. I temporarily broadened SSH access while diagnosing an EC2 Instance Connect failure, but removed the broad rule after testing.

## Testing Bastion Access

Before moving to EC2 Instance Connect Endpoint, I tested using the public EC2 instance as a bastion host to reach the private EC2 instance.

The access path was:

`Administrator → Public EC2 → Private EC2`

After correcting the private instance's security group, I successfully connected from the public instance to the private instance.

![Bastion SSH success](../screenshots/networking/connectivity/bastion-to-private-ec2-ssh-success.png)

This demonstrated how a host in a public subnet can provide an administrative path to a resource that has no public IPv4 address.

However, I did not keep the bastion method as the final administrative-access design. It required maintaining a publicly reachable instance as the entry point and, during testing, required handling the SSH private key on that instance.

## EC2 Instance Connect Endpoint

I then implemented EC2 Instance Connect Endpoint as the final administrative-access method.

The endpoint provides a way to reach the EC2 instances without using the bastion path or repeatedly updating SSH rules for my changing public Wi-Fi IP.

My first connection to the private instance through the endpoint failed.

![Private EC2 EIC failure](../screenshots/administrative-access/private-ec2-eic-connection-failure.png)

I traced the failure to the security-group relationship between the endpoint and the private instance. After updating the private instance's inbound rule to allow the security group used by the EIC Endpoint, the connection succeeded.

![EIC Endpoint created](../screenshots/administrative-access/eic-endpoint-created.png)

![Private EC2 EIC success](../screenshots/administrative-access/private-ec2-eic-access-success.png)

I also tested using the same endpoint to reach the public EC2 instance after updating its security-group rule appropriately.

![Public EC2 EIC success](../screenshots/administrative-access/public-ec2-eic-access-success.png)

The final administrative path is therefore based on EC2 Instance Connect Endpoint rather than the bastion method tested earlier.

## Final Traffic Paths

The final network can be summarized through three main traffic paths.

### Public EC2 Outbound Traffic

`Public EC2 → Public Route Table → Internet Gateway → Internet`

### Private EC2 Outbound Traffic

`Private EC2 → Private Route Table → NAT Gateway → Internet Gateway → Internet`

### Administrative Access

`Administrator → EC2 Instance Connect → EIC Endpoint → EC2 Instance`

These paths serve different purposes. The Internet Gateway provides the VPC's internet connectivity path, the NAT Gateway gives the private instance outbound internet access without assigning it a public IPv4 address, and the EIC Endpoint provides the administrative access path used in the final design.

## What I Learned

Building and troubleshooting the network made several concepts much clearer to me:

- VPC and subnet CIDR ranges must be planned so that every subnet fits inside the VPC without overlapping another subnet.
- A subnet's routing behavior depends on the route table associated with it.
- Main route-table associations can be implicit, while explicit associations make the intended design easier to understand.
- An Internet Gateway and a NAT Gateway solve different networking problems.
- A private EC2 instance can initiate internet connections through a NAT Gateway without having its own public IPv4 address.
- Security-group references can define access between AWS resources without relying on fixed client IP addresses.
- A failed connection can result from several layers of configuration, so troubleshooting requires checking the complete path rather than assuming the first visible component is the problem.
- Testing the architecture from inside the EC2 instances was important for verifying that the configuration actually behaved as intended.

The networking portion of this project gave me practical experience moving from individual AWS networking components to understanding how subnetting, routing, gateways, security groups, and administrative access work together as a complete system.
