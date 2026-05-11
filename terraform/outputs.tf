output "app_url" {
  description = "URL to access the application"
  value       = "http://localhost:5002"
}

output "container_name" {
  description = "Running container name"
  value       = docker_container.app.name
}

output "network_name" {
  description = "Docker network name"
  value       = docker_network.app_network.name
}
