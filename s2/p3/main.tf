terraform {
  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "~> 0.8.3"
    }
  }
}

provider "libvirt" {
  uri = "qemu:///system"
}

variable "vm_name" {
  type    = string
  default = "web1"
}

# bazna slika se preuzima jednom, a disk VM-a je njen "copy-on-write" potomak
resource "libvirt_volume" "base" {
  name   = "ubuntu-noble-base.qcow2"
  pool   = "default"
  format = "qcow2"
  source = "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"
}

resource "libvirt_volume" "disk" {
  name           = "${var.vm_name}.qcow2"
  pool           = "default"
  base_volume_id = libvirt_volume.base.id
  size           = 10 * 1024 * 1024 * 1024
}

resource "libvirt_cloudinit_disk" "init" {
  name = "${var.vm_name}-init.iso"
  pool = "default"
  user_data = templatefile("${path.module}/cloud-init.tftpl", {
    hostname = var.vm_name
    ssh_key  = trimspace(file(pathexpand("~/.ssh/id_ed25519.pub")))
  })
}

resource "libvirt_domain" "vm" {
  name      = var.vm_name
  memory    = 1024
  vcpu      = 1
  cloudinit = libvirt_cloudinit_disk.init.id

  disk { volume_id = libvirt_volume.disk.id }

  network_interface {
    network_name   = "default"
    wait_for_lease = true
  }

  console {
    type        = "pty"
    target_type = "serial"
    target_port = "0"
  }
}

output "ip" {
  value = libvirt_domain.vm.network_interface[0].addresses[0]
}
