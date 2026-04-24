data "kubectl_path_documents" "k8s_root" {
  pattern          = "${path.module}/../k8s/*.yaml"
  disable_template = true
}

data "kubectl_path_documents" "k8s_nested" {
  pattern          = "${path.module}/../k8s/*/*.yaml"
  disable_template = true
}

locals {
  k8s_docs_raw = [
    for doc in concat(
      data.kubectl_path_documents.k8s_root.documents,
      data.kubectl_path_documents.k8s_nested.documents,
    ) : doc
    if trimspace(doc) != ""
  ]
  k8s_docs_retargeted = [
    for doc in local.k8s_docs_raw :
    replace(
      replace(
        doc,
        "/image:\\s*nlp-cloud-manager\\/([a-z0-9-]+):[a-z0-9.-]+/",
        "image: ${var.image_registry}/$1:${var.image_tag}"
      ),
      "/namespace:\\s*nlp-cloud-manager/",
      "namespace: ${var.namespace}"
    )
  ]

  k8s_docs_classified = [
    for doc in local.k8s_docs_retargeted : {
      body = doc
      kind = try(yamldecode(doc).kind, "")
      name = try(yamldecode(doc).metadata.name, "")
    }
  ]

  k8s_docs_filtered = [
    for m in local.k8s_docs_classified : m
    if !contains(["Namespace", "Ingress"], m.kind)
  ]
  tier_config = {
    for m in local.k8s_docs_filtered : "${m.kind}/${m.name}" => m.body
    if contains(
      ["ConfigMap", "Secret", "PersistentVolumeClaim", "Service", "ServiceAccount"],
      m.kind
    )
  }

  tier_workload = {
    for m in local.k8s_docs_filtered : "${m.kind}/${m.name}" => m.body
    if contains(["Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"], m.kind)
  }
}

resource "kubectl_manifest" "k8s_config" {
  for_each = local.tier_config

  yaml_body          = each.value
  override_namespace = kubernetes_namespace.app.metadata[0].name
  wait               = false
  wait_for_rollout   = false

  depends_on = [
    kubernetes_namespace.app,
  ]
}

resource "kubectl_manifest" "k8s_workload" {
  for_each = local.tier_workload

  yaml_body          = each.value
  override_namespace = kubernetes_namespace.app.metadata[0].name
  wait             = false
  wait_for_rollout = false

  depends_on = [
    kubectl_manifest.k8s_config,
  ]
}
