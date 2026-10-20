terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

variable "ime" {
  type    = string
  default = "RuO"
}

resource "local_file" "pozdrav" {
  filename        = "${path.module}/pozdrav.txt"
  content         = "Zdravo, ${var.ime}!\n"
  file_permission = "0644"
}

output "putanja" {
  value = local_file.pozdrav.filename
}
