# Računarstvo u oblaku 2026/27: primjeri s predavanja

Univerzitet u Zenici, Politehnički fakultet. II ciklus studija, III semestar.
Asistent: ass. Mr. Adin Jahić.

Repozitorij sadrži kod iz bilješki s predavanja (Infrastructure as Code). Svaki primjer iz bilješki je ovdje
prava datoteka, a pokreće se jednom naredbom `make`, pa se na nastavi odmah vidi šta kod radi.

| Sedmica | Tema | Primjeri |
|---|---|---|
| 2 | Uvod u IaC: virtualne mašine kao kod | `s2/p1` Terraform (state, drift), `s2/p2` cloud-init, `s2/p3` Terraform + libvirt VM, `s2/p4` Packer |
| 3 | Konfiguracija i kontejneri kao kod | `s3/p1` Ansible, `s3/p2` role + Vault, `s3/p3` Terraform + Ansible, `s3/p4` Dockerfile + Compose, `s3/p5` Kubernetes |

Bilješke (PDF) uz primjere su u mapi [`docs/`](docs/).

## Šta je potrebno

Sve se pokreće u **Linux okruženju**: Ubuntu 24.04 ili **WSL2** na Windowsu (obaveza iz sillabusa).

| Alat | Potreban za | Napomena |
|---|---|---|
| `git`, `make` | sve | `sudo apt install -y git make` |
| Terraform | `s2/*`, `s3/p3` | HashiCorp apt repozitorij |
| Ansible | `s3/p1`, `s3/p2`, `s3/p3` | `sudo apt install -y ansible` |
| Docker + Compose | `s3/p4`, kind | Docker Desktop (WSL integracija) ili Docker Engine |
| Packer | `s2/p4` | HashiCorp apt repozitorij (niže) |
| libvirt / KVM | `s2/p3`, `s2/p4`, `s3/p3` | samo za primjere s virtualnim mašinama |
| `kubectl`, `kind` | `s3/p5` | samo za pokretanje klastera; dry-run radi i bez njih |

Za većinu primjera **nije potreban račun u oblaku i ništa ne košta**. Nijedan primjer ne koristi plaćene usluge.

### Instalacija: prva skripta `00-setup.sh`

Sve potrebno postavlja jedna skripta (Ubuntu/Debian ili WSL2 Ubuntu). Pokreće se kao običan korisnik, a `sudo` traži sama:

```bash
./00-setup.sh        # ili: make setup
```

Šta radi (idempotentno, može se pokrenuti više puta):

1. provjerava okruženje (Linux, apt, WSL2; ako treba, uključuje `systemd` u `/etc/wsl.conf`),
2. instalira `git`, `make`, `curl`, `ansible`,
3. dodaje HashiCorp repozitorij i instalira **Terraform** i **Packer**,
4. instalira KVM/libvirt, dodaje korisnika u grupe `libvirt`/`kvm`, pokreće `libvirtd` i pravi pool i mrežu `default`,
5. provjerava Docker (sa `INSTALL_DOCKER=1` ga instalira ako ga nema),
6. instalira `kubectl` i `kind`,
7. pravi SSH ključ `~/.ssh/id_ed25519` ako ne postoji (koristi se u VM primjerima),
8. ispisuje provjeru instaliranih alata.

Opcije: `SKIP_LIBVIRT=1` (bez KVM-a), `SKIP_K8S=1` (bez kubectl/kind), `INSTALL_DOCKER=1`.
Nakon prvog pokretanja treba se odjaviti i ponovo prijaviti (WSL: `wsl --shutdown`) da bi članstvo u grupama počelo važiti.
Za rad se koristi isključivo **Terraform** (ne OpenTofu).

### Posebne napomene za WSL2

- libvirt traži **systemd**. U `/etc/wsl.conf` dodati:
  ```ini
  [boot]
  systemd=true
  ```
  pa u PowerShellu `wsl --shutdown` i ponovo otvoriti Ubuntu.
- Za pokretanje VM-ova treba `/dev/kvm` (ugniježđena virtualizacija). Ako ga nema, VM primjeri ostaju na nivou `plan`/`validate`, što je dovoljno za nastavu.
- Pool i mreža u libvirt-u: `virsh -c qemu:///system pool-list` i `net-list` moraju pokazati `default`. Ako ne:
  ```bash
  virsh -c qemu:///system pool-define-as default dir --target /var/lib/libvirt/images
  virsh -c qemu:///system pool-start default
  virsh -c qemu:///system net-start default
  ```

## Početak

**Repozitorij kloniraj unutar Linux fajl sistema (`~/`), ne u `/mnt/c/...`.** Ansible ignoriše `ansible.cfg` u direktoriju
kojem svi mogu pisati (a to je `/mnt/c`), pa Vault i uloge tamo ne rade ispravno.

```bash
cd ~
git clone <URL-OVOG-REPOZITORIJA> RuO-2026-27
cd RuO-2026-27
./00-setup.sh      # instalacija alata (jednom)
make check        # koji alati su instalirani
make help         # popis svih ciljeva
```

## Upotreba make-a

Svaki primjer ima oznaku `s<sedmica>-p<primjer>`. Naredba `make s2-p1` pokreće primjer 1 iz sedmice 2 i
ispisuje svaku naredbu koja se izvršava, pa je jasno šta se radi. Isto radi i `make run EX=s2-p1`.

```bash
make s2-p1                    # pokreni primjer
make s2-p1-clean              # očisti ga (destroy + brisanje statea)
make ANSIBLE_ARGS= s3-p1      # ako sudo ne traži lozinku (bez -K)
```

### Pravilo: prvo plan, apply je opcionalan

Da studenti ne bi trošili resurse, **osnovni cilj svakog primjera samo pokazuje šta bi se desilo**
(`terraform plan`, `packer validate`, `ansible --check --diff`, `compose config`, `kubectl --dry-run`).
Ciljevi koji stvarno mijenjaju sistem imaju sufiks `-apply`, `-build`, `-up` i označeni su kao `[opcionalno]`.
Izuzeci koji se mogu bezbrijetno izvršiti jer rade lokalno i ne koštaju ništa su `s2-p1` i `s3-p4`.

| Cilj | Šta radi | Mijenja sistem? |
|---|---|---|
| `make s2-p1` | Terraform + `local_file`: plan, apply, ponovni apply (idempotentnost), promjena varijable, **drift** i njegovo ispravljanje | piše jednu lokalnu datoteku |
| `make s2-p2` | cloud-init: provjera `user-data` | ne |
| `make s2-p3` | Terraform + libvirt VM: init, validate, **plan** | ne (traži da libvirt radi) |
| `make s2-p3-apply` / `s2-p3-clean` | stvarno kreira / uklanja VM | da (KVM) |
| `make s2-p4` | Packer: init i validate | ne |
| `make s2-p4-build` | gradi sliku (~4 min, ~640 MB) | da (KVM) |
| `make s2-p4-vm` | plan VM-a iz izgrađene slike | ne |
| `make s3-p1` | Ansible: ping, syntax-check, `--check --diff` | ne |
| `make s3-p1-apply` | instalira nginx, dva puta (drugi put `changed=0`) | da |
| `make s3-p2` | role + Vault: šifrovana tajna, `--check` | ne |
| `make s3-p3` | Terraform + Ansible: **plan** i syntax-check | ne |
| `make s3-p3-apply` | kreira VM i konfiguriše je (`deploy.sh`) | da (KVM) |
| `make s3-p4` | Dockerfile + Compose: build, up, brojač posjeta | lokalni kontejneri |
| `make s3-p4-persist` / `s3-p4-clean` | podaci u volumenu / čišćenje | lokalni kontejneri |
| `make s3-p5` | Kubernetes manifest, dry-run | ne |
| `make s3-p5-up` / `s3-p5-heal` / `s3-p5-clean` | kind klaster, samoizlječenje, brisanje | lokalni kontejneri |
| `make safe-all` | sve što ne mijenja sistem | ne |
| `make clean-all` | čisti sve primjere | uklanja |

### Preporučeni tok na nastavi

```bash
make check                 # priprema
make s2-p1                 # state, idempotentnost, drift na jednom fajlu
make s2-p2 && make s2-p3   # cloud-init i plan za VM
make s3-p1                 # Ansible --check
make s3-p2                 # role i Vault
make s3-p4                 # Docker Compose
make s3-p5                 # Kubernetes dry-run
```

Spore korake (preuzimanje Ubuntu slike, `packer build`, `kind create cluster`) pokrenuti prije predavanja.

## Tajne i Git

- `s3/p2/.vault_pass` i `s3/p2/group_vars/web/vault.yml` pravi `make s3-p2-vault` i **nisu u Gitu** (`.gitignore`).
  U repozitoriju je samo `vault.yml.example`. Lozinka iz primjera služi samo za laboratorij.
- Ni `*.tfstate`, `.terraform/`, `tfplan` ni Packer slike (`*.qcow2`) ne idu u Git. Zaključani `.terraform.lock.hcl` **ide**.
- Prije vlastitog projekta zamijeniti sve laboratorijske vrijednosti.

## Rješavanje problema

| Simptom | Rješenje |
|---|---|
| `Permission denied` pri otvaranju diska VM-a | AppArmor: u labu `security_driver = "none"` u `/etc/libvirt/qemu.conf`, zatim `sudo systemctl restart libvirtd` |
| Terraform ne vidi libvirt | `virsh -c qemu:///system list` mora raditi; provjeriti `systemd` u WSL2 i članstvo u grupi `libvirt` |
| Nema `/dev/kvm` | zadržati se na `plan`/`validate`; u `s2/p3/main.tf` bi se u domeni dodalo `type = "qemu"` (sporo) |
| `make: *** missing separator` | koristi se Makefile iz ovog repozitorija (prefiks naredbi je `>`, ne tabulator); GNU make 3.82+ |
| Ansible traži lozinku | `make s3-p1` koristi `-K`; ako sudo ne traži lozinku: `make ANSIBLE_ARGS= s3-p1` |
| Compose: port 8080 zauzet | promijeniti mapiranje u `s3/p4/compose.yaml` |

## Struktura

```
Makefile        # make help
docs/           # bilješke s predavanja (PDF)
s2/p1..p4/      # sedmica 2: Terraform, cloud-init, libvirt VM, Packer
s3/p1..p5/      # sedmica 3: Ansible, role + Vault, Terraform + Ansible, Compose, Kubernetes
```

Status provjere: `make help`, `make check`, `s2-p1` (cijeli tok s driftom), `s2-p2`, `s3-p1` (ping, syntax-check) i
`s3-p2` (Vault) su izvršeni; primjeri koji traže KVM, Packer, Docker daemon ili klaster (`s2-p3`, `s2-p4`, `s3-p3`,
`s3-p4`, `s3-p5`) napisani su prema bilješkama, ali nisu pokretani u razvojnom okruženju. Ako nešto ne radi, prvo ih
pokrenuti u `plan`/`validate` obliku i javiti asistentu.
