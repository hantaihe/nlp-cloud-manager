output "namespace" {
  value       = kubernetes_namespace.app.metadata[0].name
  description = "Namespace"
}

output "ingress_host" {
  value       = var.ingress_host
  description = "Istio ingress Gateway"
}

data "kubernetes_service" "istio_ingress" {
  metadata {
    name      = "istio-ingressgateway"
    namespace = kubernetes_namespace.istio_ingress.metadata[0].name
  }

  depends_on = [helm_release.istio_ingress]
}

output "ingress_endpoint" {
  description = "Istio ingress Gateway"
  value = try(
    data.kubernetes_service.istio_ingress.status[0].load_balancer[0].ingress[0].hostname,
    data.kubernetes_service.istio_ingress.status[0].load_balancer[0].ingress[0].ip,
    null,
  )
}
