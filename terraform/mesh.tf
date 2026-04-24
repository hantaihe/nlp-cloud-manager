resource "kubectl_manifest" "peer_auth_strict" {
  yaml_body = yamlencode({
    apiVersion = "security.istio.io/v1beta1"
    kind       = "PeerAuthentication"
    metadata = {
      name      = "default-strict"
      namespace = kubernetes_namespace.app.metadata[0].name
    }
    spec = {
      mtls = { mode = "STRICT" }
    }
  })

  depends_on = [
    helm_release.istio_base,
    helm_release.istiod,
    kubernetes_namespace.app,
  ]
}

resource "kubectl_manifest" "destinationrule_backend" {
  for_each = local.backends

  yaml_body = yamlencode({
    apiVersion = "networking.istio.io/v1beta1"
    kind       = "DestinationRule"
    metadata = {
      name      = "backend-${each.key}"
      namespace = kubernetes_namespace.app.metadata[0].name
    }
    spec = {
      host = "backend-${each.key}.${var.namespace}.svc.cluster.local"
      trafficPolicy = {
        tls = { mode = "ISTIO_MUTUAL" }
      }
    }
  })

  depends_on = [helm_release.istiod]
}

resource "kubectl_manifest" "destinationrule_frontend" {
  for_each = local.frontends

  yaml_body = yamlencode({
    apiVersion = "networking.istio.io/v1beta1"
    kind       = "DestinationRule"
    metadata = {
      name      = "frontend-${each.key}"
      namespace = kubernetes_namespace.app.metadata[0].name
    }
    spec = {
      host = "frontend-${each.key}.${var.namespace}.svc.cluster.local"
      trafficPolicy = {
        tls = { mode = "ISTIO_MUTUAL" }
      }
    }
  })

  depends_on = [helm_release.istiod]
}

resource "kubectl_manifest" "gateway" {
  yaml_body = yamlencode({
    apiVersion = "networking.istio.io/v1beta1"
    kind       = "Gateway"
    metadata = {
      name      = "nlp-gateway"
      namespace = kubernetes_namespace.app.metadata[0].name
    }
    spec = {
      selector = { istio = "ingressgateway" }
      servers = [
        {
          port = {
            number   = 80
            name     = "http"
            protocol = "HTTP"
          }
          hosts = [var.ingress_host]
        },
      ]
    }
  })

  depends_on = [helm_release.istio_ingress]
}

resource "kubectl_manifest" "virtualservice" {
  yaml_body = yamlencode({
    apiVersion = "networking.istio.io/v1beta1"
    kind       = "VirtualService"
    metadata = {
      name      = "nlp-routes"
      namespace = kubernetes_namespace.app.metadata[0].name
    }
    spec = {
      hosts    = [var.ingress_host]
      gateways = ["nlp-gateway"]
      http = [
        {
          name  = "backend-base"
          match = [{ uri = { prefix = "/api/" } }, { uri = { exact = "/api" } }]
          route = [{
            destination = {
              host = "backend-base.${var.namespace}.svc.cluster.local"
              port = { number = 3000 }
            }
          }]
        },
        {
          name    = "backend-aws"
          match   = [{ uri = { prefix = "/aws/" } }, { uri = { exact = "/aws" } }]
          rewrite = { uri = "/" }
          route = [{
            destination = {
              host = "backend-aws.${var.namespace}.svc.cluster.local"
              port = { number = 3002 }
            }
          }]
        },
        {
          name    = "backend-azure"
          match   = [{ uri = { prefix = "/azure/" } }, { uri = { exact = "/azure" } }]
          rewrite = { uri = "/" }
          route = [{
            destination = {
              host = "backend-azure.${var.namespace}.svc.cluster.local"
              port = { number = 8001 }
            }
          }]
        },
        {
          name    = "backend-gcp"
          match   = [{ uri = { prefix = "/gcp/" } }, { uri = { exact = "/gcp" } }]
          rewrite = { uri = "/" }
          route = [{
            destination = {
              host = "backend-gcp.${var.namespace}.svc.cluster.local"
              port = { number = 8002 }
            }
          }]
        },
        {
          name    = "backend-chatbot"
          match   = [{ uri = { prefix = "/chatbot/" } }, { uri = { exact = "/chatbot" } }]
          rewrite = { uri = "/" }
          timeout = "3600s"
          route = [{
            destination = {
              host = "backend-chatbot.${var.namespace}.svc.cluster.local"
              port = { number = 8000 }
            }
          }]
        },
        {
          name    = "frontend-aws"
          match   = [{ uri = { prefix = "/services/aws/" } }, { uri = { exact = "/services/aws" } }]
          rewrite = { uri = "/" }
          route = [{
            destination = {
              host = "frontend-aws.${var.namespace}.svc.cluster.local"
              port = { number = 5175 }
            }
          }]
        },
        {
          name    = "frontend-azure"
          match   = [{ uri = { prefix = "/services/azure/" } }, { uri = { exact = "/services/azure" } }]
          rewrite = { uri = "/" }
          route = [{
            destination = {
              host = "frontend-azure.${var.namespace}.svc.cluster.local"
              port = { number = 5176 }
            }
          }]
        },
        {
          name    = "frontend-gcp"
          match   = [{ uri = { prefix = "/services/gcp/" } }, { uri = { exact = "/services/gcp" } }]
          rewrite = { uri = "/" }
          route = [{
            destination = {
              host = "frontend-gcp.${var.namespace}.svc.cluster.local"
              port = { number = 5177 }
            }
          }]
        },
        {
          name  = "frontend-chatbot"
          match = [{ uri = { prefix = "/services/chatbot/" } }, { uri = { exact = "/services/chatbot" } }]
          route = [{
            destination = {
              host = "frontend-chatbot.${var.namespace}.svc.cluster.local"
              port = { number = 3106 }
            }
          }]
        },
        {
          name  = "kiali"
          match = [{ uri = { prefix = "/kiali/" } }, { uri = { exact = "/kiali" } }]
          route = [{
            destination = {
              host = "kiali.${var.istio_namespace}.svc.cluster.local"
              port = { number = 20001 }
            }
          }]
        },
        {
          name  = "frontend-main"
          match = [{ uri = { prefix = "/" } }]
          route = [{
            destination = {
              host = "frontend-main.${var.namespace}.svc.cluster.local"
              port = { number = 3000 }
            }
          }]
        },
      ]
    }
  })

  depends_on = [
    kubectl_manifest.gateway,
    kubectl_manifest.destinationrule_backend,
    kubectl_manifest.destinationrule_frontend,
  ]
}
