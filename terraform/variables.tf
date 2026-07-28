variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token with Zone:DNS:Edit permission"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID for hushh.online"
  type        = string
}

variable "domain" {
  description = "Base domain for tunnels"
  type        = string
  default     = "hushh.online"
}

variable "environment" {
  description = "Deployment environment (prod, staging)"
  type        = string
  default     = "prod"
}

variable "server_type" {
  description = "Hetzner server type (cx21=2vCPU/4GB, cx31=2vCPU/8GB)"
  type        = string
  default     = "cx21"
}

variable "location" {
  description = "Hetzner datacenter location (nbg1, fsn1, hel1, ash, hil)"
  type        = string
  default     = "nbg1"
}

variable "ssh_public_key" {
  description = "SSH public key for server access"
  type        = string
}

variable "admin_source_ips" {
  description = "CIDR blocks allowed to SSH into the server"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict in production
}

variable "hushh_secret_key" {
  description = "JWT secret key for the Hushh server"
  type        = string
  sensitive   = true
}

variable "hushh_admin_email" {
  description = "Admin account email"
  type        = string
  default     = "admin@hushh.online"
}

variable "hushh_admin_password" {
  description = "Admin account password"
  type        = string
  sensitive   = true
}
