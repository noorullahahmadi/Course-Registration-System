terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

# Connect to local Docker
provider "docker" {
  host = "unix:///var/run/docker.sock"
}

# Docker Network
resource "docker_network" "app_network" {
  name = "course-registration-network"
}

# Docker Volume (persistent database storage)
resource "docker_volume" "db_volume" {
  name = "course-registration-db"
}

# Docker Container
resource "docker_container" "app" {
  name  = "course-registration-app"
  image = "course-registration:latest"

  restart = "unless-stopped"

  ports {
    internal = 5000
    external = 5002
  }

  networks_advanced {
    name = docker_network.app_network.name
  }

  volumes {
    volume_name    = docker_volume.db_volume.name
    container_path = "/app/data"
  }

  env = [
    "FLASK_APP=app.py",
    "FLASK_ENV=production",
    "FLASK_RUN_HOST=0.0.0.0",
  ]
}
