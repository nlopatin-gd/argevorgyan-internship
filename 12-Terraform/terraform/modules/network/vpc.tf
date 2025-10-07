resource "google_compute_network" "vpc_network" {
  name                    = "artf-vpc-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "ar-tf-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc_network.id
}

resource "google_compute_firewall" "allow_lb" {
  name    = "ar-allow-lb-access"
  network = google_compute_network.vpc_network.id

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  # Allow pub ip and ghc ranges
  source_ranges = concat(
    var.allowed_ips,
    [
      "35.191.0.0/16",
      "130.211.0.0/22"
    ]
  )
}

output "vpc_network" {
  value = google_compute_network.vpc_network.name
}

output "subnet" {
  value = google_compute_subnetwork.subnet.name
}

variable "region" {
  type    = string
  default = "europe-central2"
}

variable "allowed_ips" {
  type        = list(string)
  description = "Allowed IPs for firewall"
  default     = []
}
