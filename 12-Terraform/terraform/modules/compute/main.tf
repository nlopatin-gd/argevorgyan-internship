# vm with apache for snapshot
resource "google_compute_instance" "temp_vm" {
  name         = "ar-terraform-vm"
  machine_type = "e2-micro"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  network_interface {
    network    = var.vpc_network
    subnetwork = var.subnet
    access_config {}
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    apt-get update
    apt-get install -y apache2
    echo "Hello from $(hostname)" > /var/www/html/index.html
    systemctl enable apache2
    systemctl start apache2
  EOT
}

# snap of disk
resource "google_compute_snapshot" "temp_snapshot" {
  name        = "ar-temp-snapshot"
  source_disk = google_compute_instance.temp_vm.boot_disk[0].source
  zone        = var.zone
}

# image from snap
resource "google_compute_image" "custom_image" {
  name            = "ar-custom-http-image"
  source_snapshot = google_compute_snapshot.temp_snapshot.id
}

# instance template
resource "google_compute_instance_template" "web_template" {
  name         = "ar-web-template"
  machine_type = "e2-micro"

  disk {
    boot         = true
    source_image = google_compute_image.custom_image.self_link
    auto_delete  = true
  }

  network_interface {
    network    = var.vpc_network
    subnetwork = var.subnet
    access_config {}
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    echo "Hello from $(hostname)" > /var/www/html/index.html
    systemctl start apache2
  EOT
}

# Managed instance group with 3 replicas
resource "google_compute_region_instance_group_manager" "web_mig" {
  name               = "ar-web-mig"
  region             = var.region
  base_instance_name = "web"
  target_size        = 3

  version {
    instance_template = google_compute_instance_template.web_template.self_link
  }
}

# health check
resource "google_compute_health_check" "web_hc" {
  name = "ar-web-hc"

  http_health_check {
    port = 80
  }
}

# LB
resource "google_compute_backend_service" "web_backend" {
  name      = "ar-web-backend"
  protocol  = "HTTP"
  port_name = "http"

  backend {
    group = google_compute_region_instance_group_manager.web_mig.instance_group
  }

  health_checks = [google_compute_health_check.web_hc.id]
}

resource "google_compute_url_map" "web_url_map" {
  name            = "ar-web-url-map"
  default_service = google_compute_backend_service.web_backend.id
}

resource "google_compute_target_http_proxy" "web_proxy" {
  name    = "ar-web-http-proxy"
  url_map = google_compute_url_map.web_url_map.id
}

# external ip
resource "google_compute_global_forwarding_rule" "web_fwd" {
  name       = "ar-web-fwd"
  target     = google_compute_target_http_proxy.web_proxy.id
  port_range = "80"
}

#optional: bucket creating and deleting local and remotely 
resource "google_storage_bucket" "my_bucket" {
  name     = "aropt-terraform-bucket"
  location = var.region
  force_destroy = false  
}
# Output LB IP
output "load_balancer_ip" {
  value = google_compute_global_forwarding_rule.web_fwd.ip_address
}

# vars
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
