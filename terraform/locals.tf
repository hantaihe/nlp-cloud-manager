locals {
  backends = {
    base    = { port = 3000 }
    aws     = { port = 3002 }
    azure   = { port = 8001 }
    gcp     = { port = 8002 }
    chatbot = { port = 8000 }
  }

  frontends = {
    main    = { port = 3000 }
    aws     = { port = 5175 }
    azure   = { port = 5176 }
    gcp     = { port = 5177 }
    chatbot = { port = 3106 }
  }
}
