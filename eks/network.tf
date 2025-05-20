resource "aws_vpc" "gc_vpc" {
  cidr_block           = "10.0.0.0/16"
  instance_tenancy     = "default"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name  = "gc-k8s-vpc-${var.instance}"
    owner = var.owner
    team  = var.team
  }
}

resource "aws_internet_gateway" "gc_igw" {
  vpc_id = aws_vpc.gc_vpc.id

  tags = {
    Name  = "gc-k8s-igw-${var.instance}"
    owner = var.owner
    team  = var.team
  }
}

resource "aws_route_table" "gc_rt" {
  vpc_id = aws_vpc.gc_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gc_igw.id
  }
  
  route {
    cidr_block = "10.0.0.0/16"
    gateway_id = "local"
  }

  tags = {
    Name  = "gc-k8s-rtb-${var.instance}"
    owner = var.owner
    team  = var.team
  }
}

resource "aws_subnet" "gc_subnet_a" {
  vpc_id                  = aws_vpc.gc_vpc.id
  cidr_block              = "${var.subnet_a}"
  availability_zone       = "${data.aws_region.current.name}a"
  map_public_ip_on_launch = true

  tags = {
    Name  = "gc-k8s-subnet-a-${var.instance}"
    owner = var.owner
    team  = var.team
  }
}

resource "aws_route_table_association" "gc_subnet_a_assoc" {
  subnet_id      = aws_subnet.gc_subnet_a.id
  route_table_id = aws_route_table.gc_rt.id
}

resource "aws_subnet" "gc_subnet_b" {
  vpc_id                  = aws_vpc.gc_vpc.id
  cidr_block              = var.subnet_b
  availability_zone       = "${data.aws_region.current.name}b"
  map_public_ip_on_launch = true

  tags = {
    Name  = "gc-k8s-subnet-b-${var.instance}"
    owner = var.owner
    team  = var.team
  }
}

resource "aws_route_table_association" "gc_subnet_b_assoc" {
  subnet_id      = aws_subnet.gc_subnet_b.id
  route_table_id = aws_route_table.gc_rt.id
}