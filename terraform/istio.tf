resource "kubernetes_namespace" "istio_system" {
  metadata {
    name = var.istio_namespace
    labels = {
      "istio-injection" = "disabled"
    }
  }
}

resource "helm_release" "istio_base" {
  name       = "istio-base"
  namespace  = kubernetes_namespace.istio_system.metadata[0].name
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "base"
  version    = var.istio_version

  set {
    name  = "defaultRevision"
    value = "default"
  }
}

resource "helm_release" "istiod" {
  name       = "istiod"
  namespace  = kubernetes_namespace.istio_system.metadata[0].name
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "istiod"
  version    = var.istio_version

  set {
    name  = "sidecarInjectorWebhook.rewriteAppHTTPProbe"
    value = "true"
  }

  depends_on = [helm_release.istio_base]
}

resource "kubernetes_namespace" "istio_ingress" {
  metadata {
    name = "istio-ingress"
    labels = {
      "istio-injection" = "enabled"
    }
  }

  depends_on = [helm_release.istiod]
}

resource "helm_release" "istio_ingress" {
  name       = "istio-ingressgateway"
  namespace  = kubernetes_namespace.istio_ingress.metadata[0].name
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "gateway"
  version    = var.istio_version

  values = [
    yamlencode({
      service = {
        type = var.gateway_service_type
        ports = [
          { name = "status-port", port = 15021, targetPort = 15021 },
          { name = "http2", port = 80, targetPort = 80 },
          { name = "https", port = 443, targetPort = 443 },
        ]
      }
    })
  ]

  depends_on = [helm_release.istiod]
}
