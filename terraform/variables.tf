variable "region" {
  type    = string
  default = "ap-south-1"
}


variable "project" {
  type    = string
  default = "platform-v2"
}


variable "kubernetes_version" {
  type    = string
  default = "1.36"
}


variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}
