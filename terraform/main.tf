terraform {
  required_version = ">= 1.7"
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

# ── Providers ─────────────────────────────────────────────────────────────────
provider "hcloud" {
  token = var.hcloud_token
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# ── SSH Key ───────────────────────────────────────────────────────────────────
resource "hcloud_ssh_key" "hushh" {
  name       = "${var.environment}-hushh-key"
  public_key = var.ssh_public_key
}

# ── Firewall ──────────────────────────────────────────────────────────────────
resource "hcloud_firewall" "hushh" {
  name = "${var.environment}-hushh-firewall"

  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "22"
    source_ips = var.admin_source_ips
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "80"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "443"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "udp"
    port       = "443"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}

# ── Server VM ─────────────────────────────────────────────────────────────────
resource "hcloud_server" "hushh" {
  name        = "${var.environment}-hushh-server"
  server_type = var.server_type  # "cx21" = 2vCPU 4GB RAM ~$6/mo
  image       = "ubuntu-22.04"
  location    = var.location
  ssh_keys    = [hcloud_ssh_key.hushh.id]
  firewall_ids = [hcloud_firewall.hushh.id]

  user_data = templatefile("${path.module}/cloud-init.yaml.tpl", {
    hushh_secret_key     = var.hushh_secret_key
    hushh_admin_email    = var.hushh_admin_email
    hushh_admin_password = var.hushh_admin_password
    cloudflare_api_token = var.cloudflare_api_token
    domain               = var.domain
  })

  labels = {
    environment = var.environment
    project     = "hushh-tunnel"
  }
}

# ── DNS Records (Cloudflare) ───────────────────────────────────────────────────
resource "cloudflare_record" "apex" {
  zone_id = var.cloudflare_zone_id
  name    = "@"
  value   = hcloud_server.hushh.ipv4_address
  type    = "A"
  proxied = false  # Direct — Caddy handles TLS
  ttl     = 300
}

resource "cloudflare_record" "wildcard" {
  zone_id = var.cloudflare_zone_id
  name    = "*"
  value   = hcloud_server.hushh.ipv4_address
  type    = "A"
  proxied = false
  ttl     = 300
}
