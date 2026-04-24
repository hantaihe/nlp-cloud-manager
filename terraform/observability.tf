# Prometheus
data "http" "istio_prometheus" {
  url = "https://raw.githubusercontent.com/istio/istio/release-1.24/samples/addons/prometheus.yaml"
}

data "kubectl_file_documents" "prometheus" {
  content = data.http.istio_prometheus.response_body
}

resource "kubectl_manifest" "prometheus" {
  for_each = data.kubectl_file_documents.prometheus.manifests

  yaml_body        = each.value
  wait             = false
  wait_for_rollout = false

  depends_on = [
    helm_release.istiod,
    kubernetes_namespace.istio_system,
  ]
}

# Kiali
resource "helm_release" "kiali" {
  name       = "kiali-server"
  namespace  = kubernetes_namespace.istio_system.metadata[0].name
  repository = "https://kiali.org/helm-charts"
  chart      = "kiali-server"
  version    = "1.89.3"

  values = [
    yamlencode({
      auth = {
        strategy = "anonymous"
      }
      external_services = {
        prometheus = {
          url = "http://prometheus.${kubernetes_namespace.istio_system.metadata[0].name}:9090"
        }
        istio = {
          root_namespace = kubernetes_namespace.istio_system.metadata[0].name
        }
      }
      server = {
        web_root = "/kiali"
      }
      deployment = {
        ingress = { enabled = false }
        view_only_mode = false
      }
    })
  ]

  depends_on = [
    helm_release.istiod,
    kubectl_manifest.prometheus,
  ]
}
