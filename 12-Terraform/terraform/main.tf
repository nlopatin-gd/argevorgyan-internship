terraform {
  backend "gcs" {
    bucket = "ar-terraform-bucket"
    prefix = "terraform/state"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.8.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

module "network" {
  source = "./modules/network"
  region = var.region
}

module "compute" {
  source      = "./modules/compute"
  zone        = var.zone
  region      = var.region
  vpc_network = module.network.vpc_network
  subnet      = module.network.subnet
}

output "load_balancer_ip" {
  value       = module.compute.load_balancer_ip
  description = "IP of Load Balancer"
}
