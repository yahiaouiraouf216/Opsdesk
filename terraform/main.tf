resource "aws_vpc" "opsdesk_vpc" {
  cidr_block = var.vpc_cidr
}

resource "aws_subnet" "opsdesk_subnet" {
  vpc_id                  = aws_vpc.opsdesk_vpc.id
  map_public_ip_on_launch = true
  cidr_block              = var.subnet_cidr
  availability_zone       = var.aws_region
}

resource "aws_internet_gateway" "opsdesk_igw" {
  vpc_id = aws_vpc.opsdesk_vpc.id
}

resource "aws_route_table" "opsdesk_route_table" {
  vpc_id = aws_vpc.opsdesk_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.opsdesk_igw.id
  }
}

resource "aws_route_table_association" "opsdesk_route_table_assoc" {
  subnet_id      = aws_subnet.opsdesk_subnet.id
  route_table_id = aws_route_table.opsdesk_route_table.id
}

resource "aws_security_group" "opsdesk_sg" {
  name        = "opsdesk_sg"
  description = "Security group for OpsDesk"
  vpc_id      = aws_vpc.opsdesk_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_instance" "opsdesk_instance" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.opsdesk_subnet.id
  vpc_security_group_ids = [aws_security_group.opsdesk_sg.id]

  tags = {
    Name = "${var.project_name}-instance"
  }
}