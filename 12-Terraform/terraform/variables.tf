variable "project_id" {
  default = "gd-gcp-internship-devops"
}

variable "region" {
  default = "europe-central2"
}

variable "zone" {
  default = "europe-central2-a"
}

variable "allowed_ips" {
  
  default     = ["0.0.0.0/0"]
}
