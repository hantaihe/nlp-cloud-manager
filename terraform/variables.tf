variable "kubeconfig_path" {
  description = "kubeconfig file path"
  type        = string
  default     = "~/.kube/config"
}

variable "kube_context" {
  description = "Kubeconfig context"
  type        = string
  default     = ""
}

variable "namespace" {
  description = "Namespace"
  type        = string
  default     = "nlp-cloud-manager"
}

variable "istio_namespace" {
  description = "Istio namespace"
  type        = string
  default     = "istio-system"
}

variable "istio_version" {
  description = "Istio Helm chart version"
  type        = string
  default     = "1.24.2"
}

variable "ingress_host" {
  description = "Istio ingress Gateway"
  type        = string
  default     = "nlp-cloud-manager.local"
}

variable "image_registry" {
  description = "Image registry prefix"
  type        = string
  default     = "nlp-cloud-manager"
}

variable "image_tag" {
  description = "Image tag"
  type        = string
  default     = "latest"
}

variable "image_pull_policy" {
  description = "imagePullPolicy"
  type        = string
  default     = "IfNotPresent"
}

variable "gateway_service_type" {
  description = "Istio ingress gateway Service type"
  type        = string
  default     = "LoadBalancer"
}

variable "db_username" {
  description = "MySQL username"
  type        = string
  default     = "root"
  sensitive   = true
}

variable "db_password" {
  description = "MySQL password"
  type        = string
  default     = "root"
  sensitive   = true
}

variable "db_root_password" {
  description = "MySQL root password"
  type        = string
  default     = "root"
  sensitive   = true
}

variable "mysql_storage_size" {
  description = "Persistent storage"
  type        = string
  default     = "10Gi"
}

variable "mysql_storage_class" {
  description = "StorageClass PVC"
  type        = string
  default     = null
}
