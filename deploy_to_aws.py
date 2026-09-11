#!/usr/bin/env python3
"""
AIM-SHIELD AWS Deployment Automation
Deploys the entire system to AWS with one command
"""

import boto3
import json
import subprocess
import time
import sys
from datetime import datetime

class AWSDeployer:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)
        self.iam = boto3.client('iam')
        self.deployment_info = {
            'timestamp': datetime.now().isoformat(),
            'region': region,
            'resources': {}
        }
    
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    def create_security_group(self, name="aim-shield-sg"):
        """Create security group allowing HTTP, HTTPS, and SSH"""
        try:
            # Check if already exists
            response = self.ec2.describe_security_groups(
                Filters=[{'Name': 'group-name', 'Values': [name]}]
            )
            if response['SecurityGroups']:
                self.log(f"Security group '{name}' already exists")
                return response['SecurityGroups'][0]['GroupId']
        except:
            pass
        
        self.log(f"Creating security group: {name}")
        sg = self.ec2.create_security_group(
            GroupName=name,
            Description='AIM-SHIELD monitoring platform security group'
        )
        sg_id = sg['GroupId']
        
        # Allow SSH
        self.ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTP'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTPS'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 5000,
                    'ToPort': 5000,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Backend API'}]
                }
            ]
        )
        
        self.log(f"✓ Security group created: {sg_id}")
        self.deployment_info['resources']['security_group_id'] = sg_id
        return sg_id
    
    def create_key_pair(self, name="aim-shield-key"):
        """Create EC2 key pair for SSH access"""
        try:
            response = self.ec2.describe_key_pairs(KeyNames=[name])
            if response['KeyPairs']:
                self.log(f"Key pair '{name}' already exists")
                return name
        except:
            pass
        
        self.log(f"Creating key pair: {name}")
        key = self.ec2.create_key_pair(KeyName=name)
        
        # Save key locally
        key_path = f"/tmp/{name}.pem"
        with open(key_path, 'w') as f:
            f.write(key['KeyMaterial'])
        
        # Set proper permissions
        subprocess.run(['chmod', '600', key_path])
        
        self.log(f"✓ Key pair created and saved to: {key_path}")
        self.deployment_info['resources']['key_pair_name'] = name
        self.deployment_info['resources']['key_path'] = key_path
        return name
    
    def get_user_data_script(self):
        """Create EC2 user data script for deployment"""
        return '''#!/bin/bash
set -e

# Update system
sudo yum update -y
sudo yum install -y python3 python3-pip git curl docker

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Clone repository (using HTTPS for simplicity)
cd /home/ec2-user
git clone https://github.com/yourusername/aim-shield.git || true
cd aim-shield || cd AIM-SHIELD || true

# Build Docker image
sudo docker build -f Dockerfile -t aim-shield:latest .

# Run Docker container
sudo docker run -d \\
    --name aim-shield \\
    -p 80:5000 \\
    -e FLASK_ENV=production \\
    aim-shield:latest

# Wait for service to start
sleep 5

# Log success
echo "AIM-SHIELD deployed successfully!"
curl http://localhost/api/health || true
'''
    
    def launch_ec2_instance(self, 
                           instance_type="t3.micro",
                           key_name="aim-shield-key",
                           sg_id=None):
        """Launch EC2 instance for AIM-SHIELD"""
        
        self.log(f"Launching EC2 instance: {instance_type}")
        
        # Get Amazon Linux 2 AMI
        images = self.ec2.describe_images(
            Owners=['amazon'],
            Filters=[
                {'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']},
                {'Name': 'state', 'Values': ['available']}
            ]
        )
        
        if not images['Images']:
            self.log("ERROR: No Amazon Linux 2 AMI found")
            return None
        
        ami_id = sorted(images['Images'], 
                       key=lambda x: x['CreationDate'])[-1]['ImageId']
        self.log(f"Using AMI: {ami_id}")
        
        # Launch instance
        instances = self.ec2.run_instances(
            ImageId=ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType=instance_type,
            KeyName=key_name,
            SecurityGroupIds=[sg_id] if sg_id else [],
            UserData=self.get_user_data_script(),
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': 'aim-shield-demo'},
                        {'Key': 'Project', 'Value': 'AIM-SHIELD'}
                    ]
                }
            ]
        )
        
        instance_id = instances['Instances'][0]['InstanceId']
        self.log(f"✓ Instance launched: {instance_id}")
        self.deployment_info['resources']['instance_id'] = instance_id
        
        # Wait for running state
        self.log("Waiting for instance to start...")
        waiter = self.ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        # Get public IP
        response = self.ec2.describe_instances(InstanceIds=[instance_id])
        public_ip = response['Reservations'][0]['Instances'][0].get('PublicIpAddress')
        
        self.log(f"✓ Instance running at: {public_ip}")
        self.deployment_info['resources']['public_ip'] = public_ip
        self.deployment_info['resources']['instance_url'] = f"http://{public_ip}"
        
        return instance_id, public_ip
    
    def create_rds_database(self, db_name="aimshield"):
        """Create RDS PostgreSQL database (optional - uses SQLite by default)"""
        self.log("Creating RDS PostgreSQL database...")
        
        rds = boto3.client('rds', region_name=self.region)
        
        try:
            rds.create_db_instance(
                DBInstanceIdentifier=db_name,
                DBInstanceClass='db.t3.micro',
                Engine='postgres',
                MasterUsername='admin',
                MasterUserPassword='AimShield2024!',
                AllocatedStorage=20,
                PubliclyAccessible=True,
                SkipFinalSnapshot=True,
                Tags=[
                    {'Key': 'Project', 'Value': 'AIM-SHIELD'}
                ]
            )
            
            self.log(f"✓ RDS instance created: {db_name}")
            self.deployment_info['resources']['rds_instance'] = db_name
        except Exception as e:
            self.log(f"Note: RDS creation skipped ({str(e)})")
    
    def setup_cloudwatch_monitoring(self, instance_id):
        """Setup CloudWatch monitoring for the instance"""
        self.log("Setting up CloudWatch monitoring...")
        
        cloudwatch = boto3.client('cloudwatch', region_name=self.region)
        
        # Create alarm for high CPU
        cloudwatch.put_metric_alarm(
            AlarmName='aim-shield-high-cpu',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=2,
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',
            Period=300,
            Statistic='Average',
            Threshold=80.0,
            ActionsEnabled=True,
            Dimensions=[
                {'Name': 'InstanceId', 'Value': instance_id}
            ]
        )
        
        self.log("✓ CloudWatch alarms configured")
    
    def create_s3_bucket_for_backups(self):
        """Create S3 bucket for database backups"""
        s3 = boto3.client('s3', region_name=self.region)
        bucket_name = f"aim-shield-backups-{datetime.now().strftime('%s')}"
        
        try:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': self.region}
                if self.region != 'us-east-1' else {}
            )
            
            # Enable versioning
            s3.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            self.log(f"✓ S3 backup bucket created: {bucket_name}")
            self.deployment_info['resources']['s3_bucket'] = bucket_name
        except Exception as e:
            self.log(f"Note: S3 bucket creation skipped ({str(e)})")
    
    def deploy(self):
        """Execute full deployment"""
        self.log("=" * 60)
        self.log("AIM-SHIELD AWS Deployment Automation")
        self.log("=" * 60)
        
        try:
            # Verify AWS credentials
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            self.log(f"AWS Account: {identity['Account']}")
            self.log(f"AWS Region: {self.region}")
            
            # Create infrastructure
            sg_id = self.create_security_group()
            key_name = self.create_key_pair()
            instance_id, public_ip = self.launch_ec2_instance(
                key_name=key_name,
                sg_id=sg_id
            )
            
            # Setup monitoring
            self.setup_cloudwatch_monitoring(instance_id)
            
            # Create backups
            self.create_s3_bucket_for_backups()
            
            # Display results
            self.log("=" * 60)
            self.log("✓ DEPLOYMENT COMPLETE!")
            self.log("=" * 60)
            self.print_connection_info(public_ip, key_name)
            
            # Save deployment info
            self.save_deployment_info()
            
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            sys.exit(1)
    
    def print_connection_info(self, public_ip, key_name):
        """Print connection information"""
        key_path = f"/tmp/{key_name}.pem"
        
        print("\n📊 AIM-SHIELD is now running on AWS!")
        print(f"\n🌐 Frontend: http://{public_ip}")
        print(f"🔌 Backend API: http://{public_ip}:5000")
        print(f"\n🔐 SSH Access:")
        print(f"   ssh -i {key_path} ec2-user@{public_ip}")
        print(f"\n💾 Deployment Info: /tmp/aim-shield-deployment.json")
        print(f"\n⏱️  Note: Service takes 2-3 minutes to fully start")
        print(f"\n   Check status: curl http://{public_ip}/api/health")
    
    def save_deployment_info(self):
        """Save deployment information to file"""
        info_path = "/tmp/aim-shield-deployment.json"
        with open(info_path, 'w') as f:
            json.dump(self.deployment_info, f, indent=2)
        self.log(f"Deployment info saved to: {info_path}")


def main():
    deployer = AWSDeployer(region='us-east-1')
    deployer.deploy()


if __name__ == '__main__':
    main()
