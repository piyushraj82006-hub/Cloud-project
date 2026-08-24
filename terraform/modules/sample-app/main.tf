variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "public_subnet_ids" { type = list(string) }

locals {
  name_prefix = "cloudguard-${var.environment}"
}

# ─── Security Groups ───────────────────────────────────────────────

resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
  description = "Security group for sample app ALB"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-alb-sg"
  }
}

resource "aws_security_group" "ec2" {
  name        = "${local.name_prefix}-ec2-sg"
  description = "Security group for sample app EC2 instances"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-ec2-sg"
  }
}

# ─── IAM Role for EC2 ─────────────────────────────────────────────

resource "aws_iam_role" "ec2" {
  name = "${local.name_prefix}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${local.name_prefix}-ec2-profile"
  role = aws_iam_role.ec2.name
}

# ─── Launch Template ───────────────────────────────────────────────

resource "aws_launch_template" "sample_app" {
  name          = "${local.name_prefix}-sample-app"
  image_id      = data.aws_ami.amazon_linux_2023.id
  instance_type = "t3.micro"
  key_name      = "" # Use SSM instead of SSH

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2.name
  }

  user_data = base64encode(<<-EOF
    #!/bin/bash
    yum update -y
    yum install -y nginx
    cat > /usr/share/nginx/html/health <<'HEALTH'
    OK
    HEALTH
    cat > /usr/share/nginx/html/index.html <<'INDEX'
    <!DOCTYPE html>
    <html>
    <head><title>CloudGuard DR Sample App</title></head>
    <body>
      <h1>CloudGuard DR Sample App</h1>
      <p>This is the system under test for disaster recovery testing.</p>
      <p>Status: <a href="/health">Healthy</a></p>
    </body>
    </html>
    INDEX
    systemctl start nginx
    systemctl enable nginx
  EOF
  )

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name    = "${local.name_prefix}-sample-app"
      "dr-test" = "true"
    }
  }

  tags = {
    Name = "${local.name_prefix}-sample-app-lt"
  }
}

# ─── Auto Scaling Group ────────────────────────────────────────────

resource "aws_autoscaling_group" "sample_app" {
  name                = "${local.name_prefix}-sample-app-asg"
  min_size            = 2
  max_size            = 2
  desired_capacity    = 2
  vpc_zone_identifier = var.public_subnet_ids
  target_group_arns   = [aws_lb_target_group.sample_app.arn]
  health_check_type   = "ELB"

  launch_template {
    id      = aws_launch_template.sample_app.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${local.name_prefix}-sample-app"
    propagate_at_launch = true
  }

  tag {
    key                 = "dr-test"
    value               = "true"
    propagate_at_launch = true
  }
}

# ─── Application Load Balancer ─────────────────────────────────────

resource "aws_lb" "sample_app" {
  name               = "${local.name_prefix}-sample-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  tags = {
    Name = "${local.name_prefix}-sample-alb"
  }
}

resource "aws_lb_target_group" "sample_app" {
  name     = "${local.name_prefix}-sample-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    path                = "/health"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 10
    timeout             = 5
    matcher             = "200"
  }

  tags = {
    Name = "${local.name_prefix}-sample-tg"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.sample_app.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.sample_app.arn
  }
}

# ─── Route 53 Health Check ─────────────────────────────────────────

resource "aws_route53_health_check" "sample_app" {
  fqdn              = aws_lb.sample_app.dns_name
  port               = 80
  type               = "HTTP"
  resource_path      = "/health"
  failure_threshold  = 3
  request_interval   = 10

  tags = {
    Name = "${local.name_prefix}-health-check"
  }
}

# ─── AMI Data Source ──────────────────────────────────────────────

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ─── Outputs ────────────────────────────────────────────────────────

output "instance_ids" {
  value = aws_autoscaling_group.sample_app.instances[*].id
}

output "alb_dns_name" {
  value = aws_lb.sample_app.dns_name
}

output "alb_arn" {
  value = aws_lb.sample_app.arn
}

output "health_check_id" {
  value = aws_route53_health_check.sample_app.id
}
