output "server_ip" {
  description = "Public IPv4 address of the Hushh Tunnel server"
  value       = hcloud_server.hushh.ipv4_address
}

output "server_name" {
  description = "Hetzner server name"
  value       = hcloud_server.hushh.name
}

output "tunnel_url_example" {
  description = "Example tunnel URL format"
  value       = "https://abc123.${var.domain}"
}

output "ssh_command" {
  description = "SSH command to connect to the server"
  value       = "ssh root@${hcloud_server.hushh.ipv4_address}"
}
