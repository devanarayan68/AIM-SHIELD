# 🚀 AIM-SHIELD v2 AWS Deployment Guide

**Deploy Your Infrastructure Monitoring Platform to AWS in 30 Minutes**

---

## 📋 Prerequisites

Before starting, ensure you have:
- AWS Account (with billing enabled)
- AWS CLI installed and configured (`aws configure`)
- Docker installed locally
- GitHub account (for CI/CD)
- kubectl installed (for EKS)

Check versions:
```bash
aws --version
docker --version
kubectl version --client
```

---

## 🎯 Deployment Options

### **Option 1: EC2 + Docker (Easiest - 15 min)**
Best for: Demo, MVP, small-scale deployment

### **Option 2: ECS (Elastic Container Service - 20 min)**
Best for: Production, auto-scaling, managed service

### **Option 3: EKS (Kubernetes - 30 min)**
Best for: Enterprise, complex orchestration, multi-region

### **Option 4: Lambda + RDS (Serverless - 25 min)**
Best for: Low-cost, pay-per-use, minimal ops

We'll cover all 4 options. Start with Option 1 for your investor demo.

---

## 🏃 **QUICKEST: Option 1 - EC2 + Docker (15 min)**

### Step 1: Launch EC2 Instance

```bash
# AWS Console → EC2 → Launch Instance
# Or use CLI:

aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=aim-shield-demo}]'
```

**Instance specs for demo:**
- AMI: Ubuntu 22.04 LTS
- Instance Type: t3.medium (2 vCPU, 4GB RAM)
- Storage: 30GB SSD
- Security Group: Allow 22 (SSH), 5000 (Backend), 8080 (Frontend)

### Step 2: Connect & Setup

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@YOUR_INSTANCE_IP

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 3: Deploy AIM-SHIELD

```bash
# Clone or upload your project
cd /home/ubuntu
git clone https://github.com/YOUR_REPO/AIM-SHIELD.git
cd AIM-SHIELD

# Or upload via S3/SCP
scp -i your-key.pem -r ./AIM-SHIELD ubuntu@YOUR_INSTANCE_IP:/home/ubuntu/

# Deploy with Docker Compose
docker-compose up -d

# Check status
docker-compose ps
```

### Step 4: Access Your Demo

**Frontend**: `http://YOUR_INSTANCE_IP:8080`  
**Backend API**: `http://YOUR_INSTANCE_IP:5000`

---

## ☁️ **Option 2 - ECS Deployment (20 min)**

### Step 1: Create ECR Repository

```bash
# Create Elastic Container Registry
aws ecr create-repository --repository-name aim-shield

# Get login command
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag and push image
docker build -t aim-shield:latest .
docker tag aim-shield:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/aim-shield:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/aim-shield:latest
```

### Step 2: Create ECS Cluster

```bash
# Create cluster
aws ecs create-cluster --cluster-name aim-shield-cluster

# Create task definition
aws ecs register-task-definition \
  --family aim-shield-task \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu 256 \
  --memory 512 \
  --container-definitions file://task-definition.json
```

### Step 3: Launch Service

```bash
# Create service
aws ecs create-service \
  --cluster aim-shield-cluster \
  --service-name aim-shield-service \
  --task-definition aim-shield-task:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

## ☸️ **Option 3 - EKS Deployment (30 min)**

### Step 1: Create EKS Cluster

```bash
# Create cluster
aws eks create-cluster \
  --name aim-shield-cluster \
  --version 1.24 \
  --role-arn arn:aws:iam::ACCOUNT_ID:role/eks-service-role \
  --resources-vpc-config subnetIds=subnet-xxx,subnet-yyy,securityGroupIds=sg-zzz

# Update kubeconfig
aws eks update-kubeconfig --name aim-shield-cluster --region us-east-1

# Create node group
aws eks create-nodegroup \
  --cluster-name aim-shield-cluster \
  --nodegroup-name aim-shield-nodes \
  --scaling-config minSize=2,maxSize=10,desiredSize=3 \
  --subnets subnet-xxx subnet-yyy \
  --node-role arn:aws:iam::ACCOUNT_ID:role/NodeInstanceRole
```

### Step 2: Deploy to EKS

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s-deployment.yaml

# Check deployment
kubectl get pods
kubectl get svc

# Get LoadBalancer endpoint
kubectl get svc aim-shield-backend-svc -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

---

## 💾 **Option 4 - RDS + Lambda (Serverless)**

### Step 1: Setup RDS PostgreSQL

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier aim-shield-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 20
```

### Step 2: Update Database Configuration

```python
# backend/config.py
DATABASE_URL = "postgresql://admin:PASSWORD@aim-shield-db.xxxxxxxxx.us-east-1.rds.amazonaws.com:5432/aim_shield"
```

### Step 3: Package & Deploy Lambda

```bash
# Create deployment package
pip install -r requirements.txt -t package/
cp -r backend/ package/
cd package && zip -r ../lambda-deployment.zip . && cd ..

# Upload to Lambda
aws lambda create-function \
  --function-name aim-shield \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-role \
  --handler backend.app_advanced.app \
  --zip-file fileb://lambda-deployment.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables={DATABASE_URL=postgresql://...}
```

---

## 🌍 **Add Custom Domain (All Options)**

### Step 1: Register Domain with Route 53

```bash
aws route53 register-domain \
  --domain-name yourdomain.com \
  --duration-in-years 1 \
  --admin-contact PrivacyProtected=true,Type=ORGANIZATION,ContactDetail=...
```

### Step 2: Create CloudFront Distribution

```bash
# AWS Console → CloudFront → Create Distribution
# Origin: Your load balancer/ALB endpoint
# Caching: Default (for demo)
# HTTPS: Enabled (free with CloudFront)
```

### Step 3: Update Route 53 Records

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.yourdomain.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{
          "Value": "YOUR_ALB_ENDPOINT"
        }]
      }
    }]
  }'
```

---

## 🔐 **Add SSL/TLS Certificate (ACM)**

```bash
# Request certificate
aws acm request-certificate \
  --domain-name yourdomain.com \
  --domain-name "*.yourdomain.com" \
  --validation-method DNS

# Verify and attach to load balancer/CloudFront
```

---

## 📊 **Setup CloudWatch Monitoring**

```bash
# Create custom metrics
aws cloudwatch put-metric-alarm \
  --alarm-name aim-shield-cpu-high \
  --alarm-description "Alert when CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold

# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name AIM-SHIELD \
  --dashboard-body file://dashboard-config.json
```

---

## 📈 **Enable Auto-Scaling**

### For ECS:
```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/aim-shield-cluster/aim-shield-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --policy-name aim-shield-scaling-policy \
  --service-namespace ecs \
  --resource-id service/aim-shield-cluster/aim-shield-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration ...
```

### For EKS:
```bash
# Install Metrics Server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Apply HPA
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aim-shield-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aim-shield-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
EOF
```

---

## 💾 **Backup & Recovery**

### Database Backups (RDS):
```bash
# Automated backups (enabled by default)
aws rds modify-db-instance \
  --db-instance-identifier aim-shield-db \
  --backup-retention-period 7

# Manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier aim-shield-db \
  --db-snapshot-identifier aim-shield-backup-$(date +%Y%m%d)
```

### Application Backup (EC2):
```bash
# Create AMI from instance
aws ec2 create-image \
  --instance-id i-xxxxxxxxx \
  --name aim-shield-backup-$(date +%Y%m%d)
```

---

## 🔄 **Setup CI/CD Pipeline (GitHub Actions → AWS)**

### Step 1: Create IAM User for CI/CD

```bash
aws iam create-user --user-name github-actions
aws iam attach-user-policy \
  --user-name github-actions \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

aws iam create-access-key --user-name github-actions
```

### Step 2: Add to GitHub Secrets

```bash
# GitHub Repo → Settings → Secrets
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=us-east-1
ECR_REGISTRY=xxx.dkr.ecr.us-east-1.amazonaws.com
```

### Step 3: Update CI/CD Workflow

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build & Push to ECR
        run: |
          aws ecr get-login-password --region ${{ env.AWS_REGION }} | \
          docker login --username AWS --password-stdin ${{ env.ECR_REGISTRY }}
          
          docker build -t ${{ env.ECR_REGISTRY }}/aim-shield:latest .
          docker push ${{ env.ECR_REGISTRY }}/aim-shield:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster aim-shield-cluster \
            --service aim-shield-service \
            --force-new-deployment
```

---

## 📊 **Cost Estimation**

| Component | Size | Monthly Cost |
|-----------|------|--------------|
| **EC2** (t3.medium) | 1 instance | $30 |
| **ECS** (Fargate) | 2 tasks | $40 |
| **EKS** (3 nodes) | t3.medium | $80 |
| **RDS** (db.t3.micro) | 20GB storage | $25 |
| **CloudFront** | 1GB/month | $10 |
| **Data Transfer** | 10GB/month | $10 |
| **S3** (backups) | 50GB | $1 |
| **CloudWatch** | Monitoring | $5 |
| **Route 53** | Domain | $12 |
| **Total** (all services) | - | **$213** |

**For demo: EC2 + Docker = ~$30/month** ✅

---

## ✅ **Deployment Checklist**

### Pre-Deployment:
- [ ] AWS account created & billing enabled
- [ ] AWS CLI configured
- [ ] Docker images built and tested
- [ ] Database schema reviewed
- [ ] Environment variables documented

### Deployment:
- [ ] Infrastructure provisioned
- [ ] Application deployed
- [ ] Health checks passing
- [ ] SSL/TLS enabled
- [ ] DNS configured

### Post-Deployment:
- [ ] Monitoring enabled
- [ ] Alarms configured
- [ ] Backups scheduled
- [ ] CI/CD pipeline active
- [ ] Load testing completed

### Security:
- [ ] Security groups configured
- [ ] IAM roles least-privilege
- [ ] Secrets encrypted (Secrets Manager)
- [ ] VPC properly isolated
- [ ] DDoS protection (Shield)

---

## 🚀 **Next Steps**

1. **Choose deployment option** based on scale
2. **Follow steps above** for your chosen option
3. **Test thoroughly** before investor demo
4. **Setup monitoring** to show live metrics
5. **Configure logging** for troubleshooting

---

## 📞 **Troubleshooting**

### Port Access Issues:
```bash
# Check security group
aws ec2 describe-security-groups --group-ids sg-xxx

# Update inbound rules
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxx \
  --protocol tcp \
  --port 5000 \
  --cidr 0.0.0.0/0
```

### Container Issues:
```bash
# View logs
docker logs $(docker ps -q)
kubectl logs pod-name

# SSH into container
docker exec -it container-id bash
```

### Database Connection:
```bash
# Test RDS connection
psql -h endpoint.rds.amazonaws.com -U admin -d aim_shield
```

---

**🎉 Your AIM-SHIELD is now enterprise-ready on AWS!**
