variable "zone" {
  default = "europe-central2-a"
}

variable "region" {
  default = "europe-central2"
}

variable "vpc_network" {
  default = "default"  
}

variable "subnet" {
  default = "default" 
}

variable "allowed_ips" {
  type        = list(string)
  description = "Allowed IPs for firewall"
  default     = []
}
