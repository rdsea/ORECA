terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.17.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

resource "google_compute_network" "k8s-network" {
  name                    = "k8s-network"
  auto_create_subnetworks = false
}


resource "google_compute_subnetwork" "k8s-nodes" {
  name          = "k8s-nodes"
  network       = google_compute_network.k8s-network.id
  ip_cidr_range = "XXX.XXX.XXX.XXX/24"
}

resource "google_compute_firewall" "allow-tcp-udp-icmp-ipip-k8s-internal" {
  name    = "allow-tcp-udp-icmp-ipip-internal"
  network = google_compute_network.k8s-network.id

  allow {
    protocol = "tcp"
  }

  allow {
    protocol = "udp"
  }

  allow {
    protocol = "ipip"
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["XXX.XXX.XXX.XXX/24"]
}

resource "google_compute_firewall" "allow-tcp-icmp-k8s-external" {
  name    = "allow-tcp-icmp-k8s-external"
  network = google_compute_network.k8s-network.id

  allow {
    protocol = "tcp"
    ports    = ["22", "6443"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["XXX.XXX.XXX.XXX/0"]
}


resource "google_compute_instance" "k8s-controller" {
  name         = "k8s-controller"
  machine_type = var.controller_instance_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 200
    }
  }

  connection {
    type        = "ssh"
    user        = var.ssh_username
    private_key = file(var.private_key_path)
    host        = self.network_interface[0].access_config[0].nat_ip
  }

  network_interface {
    subnetwork = google_compute_subnetwork.k8s-nodes.id
    network_ip = "XXX.XXX.XXX.XXX"
    access_config {}
  }
  can_ip_forward = true

  metadata = {
    ssh-keys = "${var.ssh_username}:${file(var.public_key_path)}"
  }

  tags = ["k8s", "controller"]

  metadata_startup_script = file("./install-kubeadm.sh")

}

resource "google_compute_instance" "k8s-workers" {
  count        = 3
  name         = "k8s-worker-${count.index}"
  machine_type = var.worker_instance_type
  zone         = var.zone

  tags = ["k8s", "worker"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 200
    }
  }

  metadata = {
    ssh-keys = "${var.ssh_username}:${file(var.public_key_path)}"
  }

  network_interface {
    subnetwork = google_compute_subnetwork.k8s-nodes.id
    network_ip = "XXX.XXX.XXX.XXX${count.index}"
    access_config {}
  }

  can_ip_forward = true

  metadata_startup_script = file("./install-kubeadm.sh")

}

resource "null_resource" "k8s-controller-script" {

  connection {
    type        = "ssh"
    user        = var.ssh_username
    private_key = file(var.private_key_path)
    host        = google_compute_instance.k8s-controller.network_interface[0].access_config[0].nat_ip
  }

  provisioner "remote-exec" {
    inline = [
      "sudo kubeadm init --pod-network-cidr=XXX.XXX.XXX.XXX/16 >/tmp/kubeinit.log 2>&1",
      "sudo kubeadm token create --print-join-command >/home/${var.ssh_username}/kubeadm_join.sh",
      "chmod +r /home/${var.ssh_username}/kubeadm_join.sh",
      "mkdir -p /home/${var.ssh_username}/.kube",
      "sudo cp -i /etc/kubernetes/admin.conf /home/${var.ssh_username}/.kube/config",
      "sudo chown $(id -u):$(id -g) /home/${var.ssh_username}/.kube/config",
    ]
  }
  provisioner "local-exec" {
    command = "rm kubeadm_join.sh"
  }

  provisioner "local-exec" {
    command = "scp -i ${var.private_key_path} ${var.ssh_username}@${google_compute_instance.k8s-controller.network_interface[0].access_config[0].nat_ip}:/home/${var.ssh_username}/kubeadm_join.sh ./kubeadm_join.sh"
  }


  depends_on = [google_compute_instance.k8s-controller]
}

resource "null_resource" "k8s-worker-script" {
  count = 3

  connection {
    type        = "ssh"
    user        = var.ssh_username
    private_key = file(var.private_key_path)
    host        = google_compute_instance.k8s-workers[count.index].network_interface[0].access_config[0].nat_ip
  }

  provisioner "file" {
    source      = "kubeadm_join.sh"
    destination = "/var/lib/kubeadm_join.sh"
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /var/lib/kubeadm_join.sh",
      ". /var/lib/kubeadm_join.sh"
    ]
  }


  depends_on = [google_compute_instance.k8s-workers, null_resource.k8s-controller-script]
}
