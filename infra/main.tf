terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

# ---------------------
# Resource Group
# ---------------------
resource "azurerm_resource_group" "app" {
  name     = "rg-${var.app_name}"
  location = var.location
}

# ---------------------
# Container Registry
# ---------------------
resource "azurerm_container_registry" "acr" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.app.name
  location            = azurerm_resource_group.app.location
  sku                 = "Basic"
  admin_enabled       = true
}

# ---------------------
# Log Analytics (required by Container Apps)
# ---------------------
resource "azurerm_log_analytics_workspace" "logs" {
  name                = "logs-${var.app_name}"
  resource_group_name = azurerm_resource_group.app.name
  location            = azurerm_resource_group.app.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# ---------------------
# Container Apps Environment
# ---------------------
resource "azurerm_container_app_environment" "env" {
  name                       = "cae-${var.app_name}"
  resource_group_name        = azurerm_resource_group.app.name
  location                   = azurerm_resource_group.app.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id
}

# ---------------------
# Container App
# ---------------------
resource "azurerm_container_app" "app" {
  name                         = var.app_name
  resource_group_name          = azurerm_resource_group.app.name
  container_app_environment_id = azurerm_container_app_environment.env.id
  revision_mode                = "Single"

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.acr.admin_password
  }

  registry {
    server               = azurerm_container_registry.acr.login_server
    username             = azurerm_container_registry.acr.admin_username
    password_secret_name = "acr-password"
  }

  ingress {
    external_enabled = true
    target_port      = 8000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 1
    max_replicas = var.max_replicas

    container {
      name   = var.app_name
      image  = "${azurerm_container_registry.acr.login_server}/${var.app_name}:${var.image_tag}"
      cpu    = 0.5
      memory = "1Gi"
    }
  }
}
