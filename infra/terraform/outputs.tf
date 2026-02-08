output "app_url" {
  description = "TokenMeter API URL"
  value       = "https://${fly_app.tokenmeter_api.name}.fly.dev"
}

output "app_hostname" {
  description = "Fly.io hostname"
  value       = "${fly_app.tokenmeter_api.name}.fly.dev"
}
