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

# snapshot of the temp VM's disk
resource "google_compute_snapshot" "temp_snapshot" {
  name        = "ar-temp-snapshot"
  source_disk = google_compute_instance.temp_vm.boot_disk[0].source
  zone        = var.zone

  depends_on = [google_compute_instance.temp_vm]
}

# image from the snapshot 
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
    apt-get update
    apt-get install -y apache2
    echo "Hello from $(hostname)" > /var/www/html/index.html
    systemctl enable apache2
    systemctl start apache2
  EOT
}

# instance group
resource "google_compute_region_instance_group_manager" "web_mig" {
  name               = "ar-web-mig"
  region             = var.region
  base_instance_name = "web"
  target_size        = 3

  version {
    instance_template = google_compute_instance_template.web_template.self_link
  }

  named_port {
    name = "http"
    port = 80
  }

  # auto-healing using the health check
  auto_healing_policies {
    health_check      = google_compute_health_check.web_hc.id
    initial_delay_sec = 120
  }
  depends_on = [google_compute_instance_template.web_template]
}

# health check 
resource "google_compute_health_check" "web_hc" {
  name                = "ar-web-hc"
  check_interval_sec  = 10
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3

  http_health_check {
    port = 80
  }
}

# backend service for lb
resource "google_compute_backend_service" "web_backend" {
  name      = "ar-web-backend"
  protocol  = "HTTP"
  port_name = "http"

  health_checks = [google_compute_health_check.web_hc.id]

  backend {
    group = google_compute_region_instance_group_manager.web_mig.instance_group
  }
}

# URL map to backend service
resource "google_compute_url_map" "web_url_map" {
  name            = "ar-web-url-map"
  default_service = google_compute_backend_service.web_backend.id
}

resource "google_compute_target_http_proxy" "web_proxy" {
  name    = "ar-web-http-proxy"
  url_map = google_compute_url_map.web_url_map.id
}

resource "google_compute_global_forwarding_rule" "web_fwd" {
  name       = "ar-web-fwd"
  target     = google_compute_target_http_proxy.web_proxy.id
  port_range = "80"
}

# # optional: bucket 
# resource "google_storage_bucket" "my_bucket" {
#   name     = "aropt-terraform-bucket"
#   location = var.region
# }

# Output LB IP
output "load_balancer_ip" {
  value = google_compute_global_forwarding_rule.web_fwd.ip_address
}
