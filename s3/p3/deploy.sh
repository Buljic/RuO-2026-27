#!/bin/bash
set -e
terraform apply -auto-approve                                 # 1. resursi + inventory.ini
ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook site.yml     # 2. konfiguracija
